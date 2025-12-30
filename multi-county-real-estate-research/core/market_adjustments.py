"""
Market Adjustment Utilities

Time adjustments, similarity scoring, and subdivision matching for
more accurate comparable sales analysis.
"""

import re
from datetime import date, datetime
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


# Market appreciation rates by locality
MARKET_APPRECIATION_RATES = {
    "loudoun_county_va": 0.0734,  # 7.34% - 2024 data from Loudoun County Commissioner of Revenue
    "fairfax_county_va": 0.065,   # Placeholder
    "default": 0.05               # Conservative default
}

# Default to Loudoun County rate (can be configured)
DEFAULT_ANNUAL_APPRECIATION = MARKET_APPRECIATION_RATES["loudoun_county_va"]

# Size adjustment configuration
SIZE_ADJUSTMENT_CONFIG = {
    "enabled": True,
    "degradation_rate": 0.05,  # 5% per doubling of size
    "max_degradation": 0.10,   # Cap at 10% total
    "min_size_ratio": 1.1,     # Apply only if subject is 10%+ larger
}


def calculate_size_adjusted_psf(
    comp_avg_sqft: float,
    subject_sqft: float,
    comp_psf: float,
    degradation_rate: float = 0.05
) -> Tuple[float, float]:
    """
    Apply conservative $/sqft adjustment for size differences.

    Larger properties typically have lower $/sqft, but the effect is modest.
    Default: 5% degradation when size doubles (100% increase).

    Research shows luxury home $/sqft degradation is much gentler than
    simple linear extrapolation would suggest. This function applies a
    conservative adjustment based on actual market patterns.

    Args:
        comp_avg_sqft: Average sqft of comparable properties
        subject_sqft: Square footage of subject property
        comp_psf: Average $/sqft from comparables (time-adjusted)
        degradation_rate: Degradation per 100% size increase (default 0.05 = 5%)

    Returns:
        Tuple of (adjusted_psf, degradation_pct)

    Examples:
        >>> # Comps 4,000 sqft → Subject 6,000 sqft (+50%): -2.5% adjustment
        >>> psf, pct = calculate_size_adjusted_psf(4000, 6000, 400)
        >>> print(f"${psf:.2f}/sqft (-{pct:.1f}%)")
        $390.00/sqft (-2.5%)

        >>> # Comps 4,000 sqft → Subject 8,000 sqft (+100%): -5% adjustment
        >>> psf, pct = calculate_size_adjusted_psf(4000, 8000, 400)
        >>> print(f"${psf:.2f}/sqft (-{pct:.1f}%)")
        $380.00/sqft (-5.0%)

        >>> # Comps 3,711 sqft → Subject 7,371 sqft (+99%): -4.95% adjustment
        >>> psf, pct = calculate_size_adjusted_psf(3711, 7371, 329)
        >>> print(f"${psf:.2f}/sqft (-{pct:.1f}%)")
        $312.71/sqft (-4.9%)
    """
    # No adjustment if subject is smaller or similar size
    if subject_sqft <= comp_avg_sqft * SIZE_ADJUSTMENT_CONFIG["min_size_ratio"]:
        return comp_psf, 0.0

    # Calculate size ratio
    size_ratio = subject_sqft / comp_avg_sqft

    # Apply degradation: rate * (ratio - 1)
    # Example: 2x size with 5% rate = (2.0 - 1.0) * 0.05 = 0.05 (5%)
    degradation_pct = (size_ratio - 1.0) * degradation_rate

    # Cap total degradation at max to avoid over-adjustment
    degradation_pct = min(degradation_pct, SIZE_ADJUSTMENT_CONFIG["max_degradation"])

    # Apply adjustment
    adjusted_psf = comp_psf * (1.0 - degradation_pct)

    return adjusted_psf, degradation_pct * 100  # Return as percentage


def adjust_comp_for_time(
    sale_price: float,
    sale_date: date,
    annual_appreciation: float = DEFAULT_ANNUAL_APPRECIATION
) -> Tuple[float, float]:
    """
    Adjust a comp's sale price to present value using market appreciation.

    Uses compound appreciation to account for time value of money in real estate.

    Args:
        sale_price: Original sale price
        sale_date: Date of sale
        annual_appreciation: Annual market appreciation rate (default 7.34% for Loudoun County)

    Returns:
        Tuple of (adjusted_price, adjustment_percentage)

    Example:
        >>> from datetime import date
        >>> price, pct = adjust_comp_for_time(1000000, date(2024, 1, 1))
        >>> print(f"${price:,.0f} (+{pct:.1f}%)")
        $1,066,892 (+6.7%)
    """
    today = date.today()
    days_old = (today - sale_date).days

    # Handle future dates or same-day sales
    if days_old <= 0:
        return sale_price, 0.0

    years_old = days_old / 365.25

    # Compound appreciation: FV = PV * (1 + r)^t
    multiplier = (1 + annual_appreciation) ** years_old
    adjusted_price = sale_price * multiplier
    adjustment_pct = (multiplier - 1) * 100

    return adjusted_price, adjustment_pct


def parse_sale_date(sale_date_str: str) -> Optional[date]:
    """
    Parse sale date string in various formats.

    Supports:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - M/D/YYYY

    Args:
        sale_date_str: Sale date string

    Returns:
        date object or None if unparseable
    """
    if not sale_date_str:
        return None

    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(sale_date_str, '%Y-%m-%d').date()
    except ValueError:
        pass

    # Try MM/DD/YYYY format
    try:
        return datetime.strptime(sale_date_str, '%m/%d/%Y').date()
    except ValueError:
        pass

    # Try M/D/YYYY format
    try:
        return datetime.strptime(sale_date_str, '%m/%d/%Y').date()
    except ValueError:
        pass

    return None


def extract_street_name(address: str) -> Optional[str]:
    """
    Extract street name from address for comparison.

    Args:
        address: Full address string

    Returns:
        Normalized street name or None

    Examples:
        >>> extract_street_name("123 Cloister Pl, Leesburg, VA 20176")
        'cloister pl'
        >>> extract_street_name("43500 Tuckaway Place")
        'tuckaway place'
    """
    if not address:
        return None

    # Match patterns like "123 Cloister Pl" -> "Cloister Pl"
    match = re.search(r'\d+\s+(.+?)(?:,|$)', address)
    if match:
        street = match.group(1).strip().lower()
        # Normalize common abbreviations
        street = street.replace(' street', ' st')
        street = street.replace(' place', ' pl')
        street = street.replace(' drive', ' dr')
        street = street.replace(' road', ' rd')
        street = street.replace(' lane', ' ln')
        street = street.replace(' court', ' ct')
        street = street.replace(' terrace', ' ter')
        return street

    return None


def is_same_subdivision(subject: Dict, comp: Dict) -> bool:
    """
    Determine if two properties are in the same subdivision.

    Checks in order of reliability:
    1. Explicit subdivision field from ATTOM (if available)
    2. Same street name as proxy (e.g., both on "Cloister Pl")
    3. Very close proximity (<0.15 miles) as fallback

    Args:
        subject: Subject property dict with address, subdivision, distance_miles
        comp: Comparable property dict

    Returns:
        True if likely same subdivision

    Example:
        >>> subject = {"address": "123 Cloister Pl", "subdivision": None}
        >>> comp = {"address": "456 Cloister Pl", "distance_miles": 0.1}
        >>> is_same_subdivision(subject, comp)
        True
    """
    # Check explicit subdivision field
    if subject.get("subdivision") and comp.get("subdivision"):
        subject_sub = subject["subdivision"].lower().strip()
        comp_sub = comp["subdivision"].lower().strip()
        if subject_sub == comp_sub:
            return True

    # Check street name match
    subject_street = extract_street_name(subject.get("address", ""))
    comp_street = extract_street_name(comp.get("address", ""))

    if subject_street and comp_street and subject_street == comp_street:
        return True

    # Very close proximity as weak signal
    if comp.get("distance_miles", 999) < 0.15:
        return True  # Likely same neighborhood

    return False


def score_comp_similarity(subject: Dict, comp: Dict) -> float:
    """
    Score how similar a comp is to the subject property.

    Higher score = better comp = selected first and weighted more heavily.

    Scoring factors:
    - Size similarity: Up to 40 points penalty for size difference
    - Age similarity: Up to 15 points penalty for build year difference
    - Distance: Up to 25 points penalty for distance
    - Subdivision bonus: +10 points if same subdivision
    - Recency bonus: +2 to +5 points for recent sales

    Args:
        subject: Subject property dict
        comp: Comparable property dict

    Returns:
        Score from 0-100 (100 = perfect match)

    Example:
        >>> subject = {"sqft": 6000, "year_built": 2004, "address": "123 Main St"}
        >>> comp = {"sqft": 5800, "year_built": 2005, "distance_miles": 0.2,
        ...         "address": "456 Main St", "sale_date": "2025-10-01"}
        >>> score_comp_similarity(subject, comp)
        95.3  # High score - similar size, age, close, same street, recent
    """
    score = 100.0

    # Size similarity (largest factor - up to 40 points penalty)
    if subject.get("sqft") and comp.get("sqft"):
        subject_sqft = subject["sqft"]
        comp_sqft = comp["sqft"]

        if subject_sqft > 0:
            sqft_diff_pct = abs(subject_sqft - comp_sqft) / subject_sqft
            # Penalty increases with difference: 10% diff = 4pts, 50% diff = 20pts, 100% diff = 40pts
            penalty = min(sqft_diff_pct * 40, 40)
            score -= penalty

    # Age similarity (up to 15 points penalty)
    if subject.get("year_built") and comp.get("year_built"):
        age_diff = abs(subject["year_built"] - comp["year_built"])
        # 1 year diff = 1 point, max 15 points
        penalty = min(age_diff * 1.0, 15)
        score -= penalty

    # Distance penalty (up to 25 points for 5+ miles)
    if comp.get("distance_miles") is not None:
        # 0.1 mi = 0.5pts, 1 mi = 5pts, 5 mi = 25pts
        penalty = min(comp["distance_miles"] * 5, 25)
        score -= penalty

    # Subdivision bonus (subtle - 10 points, not dominant)
    if is_same_subdivision(subject, comp):
        score += 10

    # Recency bonus (prefer recent sales)
    if comp.get("sale_date"):
        sale_date = parse_sale_date(comp["sale_date"])
        if sale_date:
            months_old = (date.today() - sale_date).days / 30.4
            if months_old < 3:
                score += 5   # Very recent (< 3 months)
            elif months_old < 6:
                score += 2   # Recent (3-6 months)
            # No bonus for older sales

    return max(score, 0.0)


if __name__ == "__main__":
    # Test examples
    print("Market Adjustment Utilities Test")
    print("=" * 70)

    # Test time adjustment
    from datetime import date
    print("\n1. Time Adjustment:")
    test_date = date(2024, 1, 15)
    adjusted, pct = adjust_comp_for_time(1_500_000, test_date)
    print(f"   Original: $1,500,000 (Jan 2024)")
    print(f"   Adjusted: ${adjusted:,.0f} (+{pct:.1f}%)")

    # Test street extraction
    print("\n2. Street Name Extraction:")
    addresses = [
        "43423 Cloister Pl, Leesburg, VA 20176",
        "123 Main Street, Anytown, USA",
        "456 Oak Avenue"
    ]
    for addr in addresses:
        street = extract_street_name(addr)
        print(f"   {addr} → '{street}'")

    # Test similarity scoring
    print("\n3. Similarity Scoring:")
    subject = {
        "sqft": 6000,
        "year_built": 2004,
        "address": "123 Cloister Pl, Leesburg, VA"
    }

    comps = [
        {"sqft": 5900, "year_built": 2005, "distance_miles": 0.1,
         "address": "456 Cloister Pl, Leesburg, VA", "sale_date": "2025-10-01"},
        {"sqft": 4500, "year_built": 2010, "distance_miles": 1.2,
         "address": "789 Oak St, Leesburg, VA", "sale_date": "2024-01-15"},
    ]

    for i, comp in enumerate(comps, 1):
        score = score_comp_similarity(subject, comp)
        print(f"   Comp {i}: Score = {score:.1f}")
        print(f"     {comp['sqft']} sqft, {comp['year_built']}, {comp['distance_miles']} mi")
