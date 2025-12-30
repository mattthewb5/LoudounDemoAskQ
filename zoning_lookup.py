#!/usr/bin/env python3
"""
Athens-Clarke County Zoning Lookup
Retrieves zoning and future land use information for properties
"""

import requests
from dataclasses import dataclass
from typing import Optional, List, Tuple
from geopy.geocoders import Nominatim


@dataclass
class ZoningInfo:
    """Container for zoning information"""
    # Property identification
    parcel_number: str
    pin: str
    address: str

    # Current zoning
    current_zoning: str
    current_zoning_description: str
    combined_zoning: str
    split_zoned: bool

    # Future land use
    future_land_use: str
    future_land_use_description: str
    future_changed: bool

    # Property details
    acres: float

    # Nearby parcels context
    nearby_zones: List[str]
    nearby_future_use: List[str]

    # Coordinates
    latitude: float
    longitude: float


@dataclass
class NearbyZoning:
    """Container for nearby zoning analysis"""
    # Current property
    current_parcel: Optional[ZoningInfo]

    # Surrounding parcels
    nearby_parcels: List[ZoningInfo]

    # Analysis flags
    mixed_use_nearby: bool
    residential_only: bool
    commercial_nearby: bool
    industrial_nearby: bool

    # Identified concerns
    potential_concerns: List[str]

    # Summary metrics
    total_nearby_parcels: int
    unique_zones: List[str]
    zone_diversity_score: float  # 0.0 (all same) to 1.0 (all different)


def get_zoning_code_description(code: str) -> str:
    """
    Get human-readable description of zoning code

    Args:
        code: Zoning code (e.g., "RS-8", "C-D", "G")

    Returns:
        Description of the zoning classification
    """
    zoning_descriptions = {
        # Residential - Single Family
        'RS-40': 'Single-Family Residential (40,000 sq ft minimum lot)',
        'RS-25': 'Single-Family Residential (25,000 sq ft minimum lot)',
        'RS-15': 'Single-Family Residential (15,000 sq ft minimum lot)',
        'RS-8': 'Single-Family Residential (8,000 sq ft minimum lot)',
        'RS-5': 'Single-Family Residential (5,000 sq ft minimum lot)',

        # Residential - Multi-Family
        'RM-1': 'Multi-Family Residential (Low Density)',
        'RM-2': 'Multi-Family Residential (Medium Density)',
        'RM-3': 'Multi-Family Residential (High Density)',

        # Commercial
        'C-N': 'Commercial-Neighborhood (Local retail and services)',
        'C-G': 'Commercial-General (Broad range of commercial uses)',
        'C-D': 'Commercial-Downtown (Downtown core commercial)',
        'C-R': 'Commercial-Regional (Large-scale retail)',

        # Mixed Use
        'MU': 'Mixed Use (Residential and commercial)',
        'MU-C': 'Mixed Use-Commercial',
        'MU-R': 'Mixed Use-Residential',

        # Industrial
        'I-N': 'Industrial-Neighborhood (Light industrial)',
        'I-G': 'Industrial-General (Heavy industrial)',

        # Government/Institutional
        'G': 'Government/Institutional',
        'G-I': 'Government-Institutional',

        # Agricultural
        'A-R': 'Agricultural-Residential',

        # Special
        'PUD': 'Planned Unit Development',
        'PRD': 'Planned Residential Development',
    }

    # Try exact match first
    if code in zoning_descriptions:
        return zoning_descriptions[code]

    # Try partial match for variants
    code_upper = code.upper().strip()
    for key, description in zoning_descriptions.items():
        if code_upper.startswith(key):
            return description

    # Default if unknown
    return f"Zoning: {code}"


def get_future_land_use_description(land_use: str) -> str:
    """
    Get human-readable description of future land use

    Args:
        land_use: Future land use designation

    Returns:
        Description of planned future use
    """
    future_use_descriptions = {
        'Single-Family Residential': 'Planned for detached single-family homes',
        'Multi-Family Residential': 'Planned for apartments or condos',
        'Mixed Residential': 'Planned for variety of housing types',
        'Neighborhood Commercial': 'Planned for local shops and services',
        'General Commercial': 'Planned for broader commercial development',
        'Downtown Commercial': 'Planned for downtown-style development',
        'Office': 'Planned for office buildings',
        'Industrial': 'Planned for industrial/manufacturing uses',
        'Government': 'Planned for public/institutional uses',
        'Parks and Recreation': 'Planned for parks, trails, recreation',
        'Conservation': 'Planned for environmental conservation',
        'Mixed Use': 'Planned for combination of residential and commercial',
    }

    # Try exact match
    if land_use in future_use_descriptions:
        return future_use_descriptions[land_use]

    # Try case-insensitive partial match
    land_use_lower = land_use.lower()
    for key, description in future_use_descriptions.items():
        if key.lower() in land_use_lower or land_use_lower in key.lower():
            return description

    # Default
    return f"Planned for: {land_use}"


def _is_residential(zoning_code: str) -> bool:
    """
    Check if a zoning code is residential

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if residential, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Residential patterns
    residential_prefixes = ['RS-', 'RM-', 'R-', 'A-R', 'PRD']

    for prefix in residential_prefixes:
        if code_upper.startswith(prefix):
            return True

    return False


def _is_commercial_or_mixed(zoning_code: str) -> bool:
    """
    Check if a zoning code is commercial or mixed use

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if commercial/mixed, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Commercial and mixed use patterns
    commercial_prefixes = ['C-', 'MU-', 'MU']

    for prefix in commercial_prefixes:
        if code_upper.startswith(prefix):
            return True

    # Exact matches for mixed use
    if code_upper in ['MU', 'MIXED USE']:
        return True

    return False


def _is_industrial(zoning_code: str) -> bool:
    """
    Check if a zoning code is industrial

    Args:
        zoning_code: Zoning code to check

    Returns:
        True if industrial, False otherwise
    """
    if not zoning_code:
        return False

    code_upper = zoning_code.upper().strip()

    # Industrial patterns
    industrial_prefixes = ['I-', 'IN-', 'IND-']

    for prefix in industrial_prefixes:
        if code_upper.startswith(prefix):
            return True

    return False


def _identify_concerns(current_zoning: Optional[ZoningInfo], nearby_parcels: List[ZoningInfo]) -> List[str]:
    """
    Identify potential zoning concerns

    Args:
        current_zoning: The current property's zoning info
        nearby_parcels: List of nearby parcel zoning info

    Returns:
        List of concern strings
    """
    concerns = []

    if not current_zoning:
        return concerns

    current_code = current_zoning.current_zoning
    current_is_residential = _is_residential(current_code)

    # Check for residential next to commercial
    if current_is_residential:
        commercial_nearby = [p for p in nearby_parcels if _is_commercial_or_mixed(p.current_zoning)]
        if commercial_nearby:
            concerns.append(f"Residential property has {len(commercial_nearby)} commercial/mixed-use parcel(s) nearby")

    # Check for residential next to industrial
    if current_is_residential:
        industrial_nearby = [p for p in nearby_parcels if _is_industrial(p.current_zoning)]
        if industrial_nearby:
            concerns.append(f"Residential property has {len(industrial_nearby)} industrial parcel(s) nearby - potential noise/traffic concerns")

    # Check for future land use changes
    if current_zoning.future_changed:
        concerns.append(f"Future land use plan has been updated - area may be in transition")

    # Check if future land use differs significantly from current zoning
    if current_is_residential and current_zoning.future_land_use:
        future_lower = current_zoning.future_land_use.lower()
        if 'commercial' in future_lower or 'mixed' in future_lower:
            concerns.append(f"Future land use ({current_zoning.future_land_use}) differs from current residential zoning - possible redevelopment area")

    # Check for split zoning
    if current_zoning.split_zoned:
        concerns.append("Property has split zoning - different regulations apply to different parts")

    # Check for very diverse nearby zoning (might indicate transitional area)
    unique_zones = set(p.current_zoning for p in nearby_parcels if p.current_zoning)
    if len(unique_zones) >= 5:
        concerns.append(f"High zoning diversity nearby ({len(unique_zones)} different zones) - may indicate transitional neighborhood")

    return concerns


def calculate_development_probability(current_zoning: str, future_land_use: str) -> int:
    """
    Calculate development probability score based on zoning/future land use mismatch.

    Args:
        current_zoning: Current zoning code (e.g., "RS-8", "C-G")
        future_land_use: Future land use designation

    Returns:
        Score from 0-100 indicating development probability
    """
    score = 0

    if not current_zoning or not future_land_use:
        return 0

    current_upper = current_zoning.upper().strip()
    future_lower = future_land_use.lower().strip()

    # 1. Mismatch between current and future (up to 40 points)
    # Check if future is higher intensity than current
    current_is_residential = _is_residential(current_zoning)
    future_is_commercial = 'commercial' in future_lower or 'mixed' in future_lower
    future_is_multifamily = 'multi' in future_lower
    future_is_industrial = 'industrial' in future_lower

    if current_is_residential:
        if future_is_commercial or future_is_industrial:
            score += 40  # Major intensity increase
        elif future_is_multifamily and current_upper.startswith('RS-'):
            score += 30  # Residential densification
        elif 'mixed' in future_lower:
            score += 35  # Mixed use transition

    # 2. Current zoning restrictiveness (up to 30 points)
    # More restrictive = harder to change = lower development pressure
    restrictiveness_points = 0

    if current_upper.startswith('RS-40'):
        restrictiveness_points = 5  # Very large lots, harder to change
    elif current_upper.startswith('RS-25'):
        restrictiveness_points = 8
    elif current_upper.startswith('RS-15'):
        restrictiveness_points = 12
    elif current_upper.startswith('RS-8'):
        restrictiveness_points = 18
    elif current_upper.startswith('RS-5'):
        restrictiveness_points = 22  # Small lots, easier to redevelop
    elif current_upper.startswith('RM-'):
        restrictiveness_points = 25  # Already multi-family
    elif current_upper.startswith('C-') or current_upper.startswith('MU'):
        restrictiveness_points = 30  # Already commercial/mixed

    score += restrictiveness_points

    # 3. Future designation type (up to 30 points)
    # Commercial/mixed use = higher development pressure
    future_points = 0

    if 'downtown' in future_lower:
        future_points = 30  # Highest pressure
    elif 'regional' in future_lower or 'general commercial' in future_lower:
        future_points = 25
    elif 'mixed use' in future_lower or 'mixed-use' in future_lower:
        future_points = 22
    elif 'neighborhood commercial' in future_lower:
        future_points = 18
    elif 'office' in future_lower:
        future_points = 15
    elif 'multi-family' in future_lower or 'multifamily' in future_lower:
        future_points = 12
    elif 'industrial' in future_lower:
        future_points = 20
    elif 'single-family' in future_lower or 'single family' in future_lower:
        future_points = 5  # Low pressure if staying residential
    elif 'conservation' in future_lower or 'parks' in future_lower:
        future_points = 2  # Very low pressure

    score += future_points

    # Cap at 100
    return min(score, 100)


def classify_risk_level(score: int) -> str:
    """
    Classify development risk based on score.

    Args:
        score: Development probability score (0-100)

    Returns:
        Risk level string: "Low", "Moderate", "High", or "Very High"
    """
    if score <= 25:
        return "Low"
    elif score <= 50:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Very High"


def generate_development_interpretation(
    current_zoning: str,
    future_land_use: str,
    score: int,
    risk_level: str
) -> str:
    """
    Generate user-friendly interpretation of development probability.

    Args:
        current_zoning: Current zoning code
        future_land_use: Future land use designation
        score: Development probability score
        risk_level: Risk level classification

    Returns:
        Markdown-formatted interpretation text
    """
    if not current_zoning or not future_land_use:
        return "Unable to analyze development probability - missing zoning or future land use data."

    current_is_residential = _is_residential(current_zoning)
    future_lower = future_land_use.lower()

    interpretation = []

    # Main assessment
    if risk_level == "Low":
        interpretation.append(
            "**Assessment:** The current zoning aligns well with the future land use plan. "
            "Significant redevelopment pressure is unlikely in the near term."
        )
        interpretation.append("")
        interpretation.append(
            "**What this means:** The neighborhood character is likely to remain stable. "
            "Any changes would be minor and consistent with current development patterns."
        )
        timeline = "No significant changes expected in the foreseeable future"
        certainty = "High confidence"

    elif risk_level == "Moderate":
        interpretation.append(
            "**Assessment:** There is some mismatch between current zoning and future plans. "
            "Development pressure exists but isn't imminent."
        )
        interpretation.append("")
        if current_is_residential and ('commercial' in future_lower or 'mixed' in future_lower):
            interpretation.append(
                "**What could happen:** Individual properties may seek rezoning for higher-density "
                "or mixed-use development over time. This typically happens gradually, "
                "often starting with corner lots or properties on major roads."
            )
        else:
            interpretation.append(
                "**What could happen:** Some evolution of the neighborhood is possible, "
                "but changes would likely be incremental and take years to materialize."
            )
        timeline = "Possible changes within 5-15 years"
        certainty = "Moderate confidence"

    elif risk_level == "High":
        interpretation.append(
            "**Assessment:** Significant mismatch between current zoning and future land use. "
            "The area is positioned for potential redevelopment."
        )
        interpretation.append("")
        if current_is_residential:
            interpretation.append(
                "**What could happen:** As properties change hands, new owners may pursue rezoning "
                "for higher-intensity uses. You might see proposals for apartments, townhomes, "
                "or commercial development in the coming years."
            )
        else:
            interpretation.append(
                "**What could happen:** The area is likely to see increased development activity. "
                "New construction or major renovations are probable."
            )
        timeline = "Changes possible within 3-10 years"
        certainty = "Moderate confidence"

    else:  # Very High
        interpretation.append(
            "**Assessment:** Strong development pressure exists. The future land use plan "
            "envisions significant change from current conditions."
        )
        interpretation.append("")
        interpretation.append(
            "**What could happen:** This area is a prime target for redevelopment. "
            "Expect active rezoning requests, development proposals, and potentially "
            "significant changes to neighborhood character. Property values may fluctuate "
            "based on development speculation."
        )
        timeline = "Changes likely within 2-5 years"
        certainty = "High confidence in change, timing uncertain"

    interpretation.append("")
    interpretation.append(f"**Timeline estimate:** {timeline}")
    interpretation.append("")
    interpretation.append(f"**Certainty level:** {certainty}")

    # Add context about what the numbers mean
    interpretation.append("")
    interpretation.append(
        f"*This analysis compares the current {current_zoning} zoning against the "
        f"'{future_land_use}' future land use designation from the comprehensive plan.*"
    )

    return "\n".join(interpretation)


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address to lat/lon coordinates

    Args:
        address: Street address

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    try:
        geolocator = Nominatim(user_agent="athens_home_buyer_research")

        # Add Athens, GA if not present
        if 'athens' not in address.lower():
            address = f"{address}, Athens, GA"

        location = geolocator.geocode(address, timeout=10)

        if location:
            return (location.latitude, location.longitude)
        else:
            return None

    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def query_zoning_api(latitude: float, longitude: float, distance_meters: int = 100) -> Optional[dict]:
    """
    Query the Parcel Zoning Types API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        distance_meters: Search radius in meters (default 100)

    Returns:
        API response dict or None if error
    """
    url = "https://enigma.accgov.com/server/rest/services/Parcel_Zoning_Types/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': distance_meters,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',  # We don't need polygon geometry
        'f': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Zoning API error: {e}")
        return None


def query_future_land_use_api(latitude: float, longitude: float, distance_meters: int = 100) -> Optional[dict]:
    """
    Query the Future Land Use API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        distance_meters: Search radius in meters (default 100)

    Returns:
        API response dict or None if error
    """
    url = "https://enigma.accgov.com/server/rest/services/FutureLandUse/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': distance_meters,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',  # We don't need polygon geometry
        'f': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Future Land Use API error: {e}")
        return None


def get_zoning_info(address: str) -> Optional[ZoningInfo]:
    """
    Get comprehensive zoning information for an address

    Args:
        address: Street address in Athens-Clarke County

    Returns:
        ZoningInfo object or None if address not found
    """
    # Step 1: Geocode the address
    coords = geocode_address(address)
    if not coords:
        print(f"Could not geocode address: {address}")
        return None

    latitude, longitude = coords
    print(f"Geocoded to: ({latitude}, {longitude})")

    # Step 2: Query zoning API
    print(f"🔍 Querying zoning API for coordinates ({latitude}, {longitude})...")
    zoning_data = query_zoning_api(latitude, longitude, distance_meters=50)
    if not zoning_data or not zoning_data.get('features'):
        print("❌ No zoning data found")
        return None
    print(f"✓ Got {len(zoning_data.get('features', []))} zoning records")

    # Step 3: Query future land use API
    print(f"🔍 Querying future land use API...")
    future_data = query_future_land_use_api(latitude, longitude, distance_meters=50)
    if future_data and future_data.get('features'):
        print(f"✓ Got {len(future_data.get('features', []))} future land use records")
    else:
        print("⚠️ No future land use data found")

    # Step 4: Find the closest parcel (usually the first one)
    primary_parcel = zoning_data['features'][0]['attributes']

    # Extract zoning info
    current_zoning = primary_parcel.get('CurrentZn', '').strip()
    combined_zoning = primary_parcel.get('CombinedZn', '').strip()
    parcel_number = primary_parcel.get('PARCEL_NO', '').strip()
    pin = primary_parcel.get('PIN', '').strip()
    acres = primary_parcel.get('Acres', 0.0)
    split_zoned = primary_parcel.get('SplitZoned', '').strip() != ''

    # Get description
    current_zoning_description = get_zoning_code_description(current_zoning)

    # Extract future land use
    future_land_use = ''
    future_land_use_description = ''
    future_changed = False

    if future_data and future_data.get('features'):
        future_parcel = future_data['features'][0]['attributes']
        future_land_use = future_parcel.get('Updated_FL', '').strip()
        future_changed = future_parcel.get('Change', '').strip().lower() == 'yes'
        future_land_use_description = get_future_land_use_description(future_land_use)

    # Get nearby parcels for context
    nearby_zones = []
    nearby_future_use = []

    # Collect nearby zoning codes (excluding the primary parcel)
    for feature in zoning_data['features'][1:]:
        zone = feature['attributes'].get('CurrentZn', '').strip()
        if zone and zone not in nearby_zones:
            nearby_zones.append(zone)

    # Collect nearby future land use
    if future_data and future_data.get('features'):
        for feature in future_data['features'][1:]:
            use = feature['attributes'].get('Updated_FL', '').strip()
            if use and use not in nearby_future_use:
                nearby_future_use.append(use)

    # Create ZoningInfo object
    zoning_info = ZoningInfo(
        parcel_number=parcel_number,
        pin=pin,
        address=address,
        current_zoning=current_zoning,
        current_zoning_description=current_zoning_description,
        combined_zoning=combined_zoning,
        split_zoned=split_zoned,
        future_land_use=future_land_use,
        future_land_use_description=future_land_use_description,
        future_changed=future_changed,
        acres=acres,
        nearby_zones=nearby_zones[:5],  # Limit to 5 nearest
        nearby_future_use=nearby_future_use[:5],
        latitude=latitude,
        longitude=longitude
    )

    return zoning_info


def get_nearby_zoning(address: str, radius_meters: int = 250) -> Optional[NearbyZoning]:
    """
    Get comprehensive nearby zoning analysis for an address

    Args:
        address: Street address in Athens-Clarke County
        radius_meters: Search radius in meters (default: 250)

    Returns:
        NearbyZoning object with detailed analysis or None if address not found
    """
    # Step 1: Get the current parcel's zoning
    print(f"📍 Getting current parcel zoning for: {address}")
    current_parcel = get_zoning_info(address)
    if not current_parcel:
        print(f"❌ Could not get zoning for address: {address}")
        return None
    print(f"✓ Got current parcel: {current_parcel.current_zoning}")

    # Step 2: Query for nearby parcels with wider radius
    latitude, longitude = current_parcel.latitude, current_parcel.longitude
    print(f"🔍 Querying nearby parcels within {radius_meters}m radius...")

    zoning_data = query_zoning_api(latitude, longitude, distance_meters=radius_meters)
    future_data = query_future_land_use_api(latitude, longitude, distance_meters=radius_meters)

    if not zoning_data or not zoning_data.get('features'):
        print("❌ No nearby zoning data found")
        return None
    print(f"✓ Found {len(zoning_data.get('features', []))} nearby parcels")

    # Step 3: Build ZoningInfo objects for all nearby parcels
    print(f"📊 Building nearby parcel analysis...")
    nearby_parcels = []

    for feature in zoning_data['features']:
        attrs = feature['attributes']

        # Skip the current parcel (match by PIN or parcel number)
        pin = attrs.get('PIN', '') or ''
        pin = pin.strip() if pin else ''
        if pin and pin == current_parcel.pin:
            continue

        parcel_number = attrs.get('PARCEL_NO', '') or ''
        parcel_number = parcel_number.strip() if parcel_number else ''
        if parcel_number and parcel_number == current_parcel.parcel_number:
            continue

        # Extract zoning info (handle None values)
        current_zoning = attrs.get('CurrentZn', '') or ''
        current_zoning = current_zoning.strip() if current_zoning else ''

        combined_zoning = attrs.get('CombinedZn', '') or ''
        combined_zoning = combined_zoning.strip() if combined_zoning else ''

        acres = attrs.get('Acres', 0.0) or 0.0

        split_zoned_value = attrs.get('SplitZoned', '') or ''
        split_zoned = str(split_zoned_value).strip() != ''

        # Get description
        current_zoning_description = get_zoning_code_description(current_zoning)

        # Try to find matching future land use
        future_land_use = ''
        future_land_use_description = ''
        future_changed = False

        if future_data and future_data.get('features'):
            for future_feature in future_data['features']:
                future_attrs = future_feature['attributes']
                if future_attrs.get('PARCEL_NO', '').strip() == parcel_number:
                    future_land_use = future_attrs.get('Updated_FL', '') or ''
                    future_land_use = future_land_use.strip() if future_land_use else ''
                    change_value = future_attrs.get('Change', '') or ''
                    future_changed = str(change_value).strip().lower() == 'yes'
                    future_land_use_description = get_future_land_use_description(future_land_use)
                    break

        # Create ZoningInfo for this nearby parcel
        nearby_info = ZoningInfo(
            parcel_number=parcel_number,
            pin=pin,
            address=f"Near {address}",
            current_zoning=current_zoning,
            current_zoning_description=current_zoning_description,
            combined_zoning=combined_zoning,
            split_zoned=split_zoned,
            future_land_use=future_land_use,
            future_land_use_description=future_land_use_description,
            future_changed=future_changed,
            acres=acres,
            nearby_zones=[],  # Not needed for nearby parcels
            nearby_future_use=[],
            latitude=latitude,
            longitude=longitude
        )

        nearby_parcels.append(nearby_info)

    # Step 4: Analyze the zoning patterns
    total_nearby = len(nearby_parcels)
    unique_zones = list(set(p.current_zoning for p in nearby_parcels if p.current_zoning))

    # Calculate diversity score
    if total_nearby > 0:
        zone_diversity_score = len(unique_zones) / total_nearby
    else:
        zone_diversity_score = 0.0

    # Check for different use types
    mixed_use_nearby = any(_is_commercial_or_mixed(p.current_zoning) for p in nearby_parcels)
    residential_only = all(_is_residential(p.current_zoning) for p in nearby_parcels) if nearby_parcels else False
    commercial_nearby = any(_is_commercial_or_mixed(p.current_zoning) for p in nearby_parcels)
    industrial_nearby = any(_is_industrial(p.current_zoning) for p in nearby_parcels)

    # Identify potential concerns
    potential_concerns = _identify_concerns(current_parcel, nearby_parcels)

    # Step 5: Create NearbyZoning object
    nearby_zoning = NearbyZoning(
        current_parcel=current_parcel,
        nearby_parcels=nearby_parcels,
        mixed_use_nearby=mixed_use_nearby,
        residential_only=residential_only,
        commercial_nearby=commercial_nearby,
        industrial_nearby=industrial_nearby,
        potential_concerns=potential_concerns,
        total_nearby_parcels=total_nearby,
        unique_zones=unique_zones,
        zone_diversity_score=zone_diversity_score
    )

    print(f"✓ Nearby zoning analysis complete: {total_nearby} parcels, {len(unique_zones)} unique zones, {len(potential_concerns)} concerns")
    return nearby_zoning


def format_zoning_report(zoning_info: ZoningInfo) -> str:
    """
    Format zoning information as a readable text report

    Args:
        zoning_info: ZoningInfo object

    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("ZONING INFORMATION")
    report.append("=" * 80)
    report.append("")

    report.append(f"Address: {zoning_info.address}")
    report.append(f"Parcel: {zoning_info.parcel_number}")
    report.append(f"PIN: {zoning_info.pin}")
    report.append("")

    report.append("CURRENT ZONING:")
    report.append(f"  Code: {zoning_info.current_zoning}")
    report.append(f"  Description: {zoning_info.current_zoning_description}")
    if zoning_info.split_zoned:
        report.append("  ⚠️  Property has split zoning")
    if zoning_info.combined_zoning and zoning_info.combined_zoning != zoning_info.current_zoning:
        report.append(f"  Combined: {zoning_info.combined_zoning}")
    report.append("")

    report.append("FUTURE LAND USE:")
    report.append(f"  Designation: {zoning_info.future_land_use}")
    report.append(f"  Description: {zoning_info.future_land_use_description}")
    if zoning_info.future_changed:
        report.append("  📝 Future land use plan has been updated/changed")
    report.append("")

    report.append("PROPERTY SIZE:")
    report.append(f"  {zoning_info.acres:.2f} acres ({int(zoning_info.acres * 43560)} square feet)")
    report.append("")

    if zoning_info.nearby_zones:
        report.append("NEARBY ZONING:")
        for zone in zoning_info.nearby_zones:
            description = get_zoning_code_description(zone)
            report.append(f"  • {zone}: {description}")
        report.append("")

    if zoning_info.nearby_future_use:
        report.append("NEARBY FUTURE LAND USE:")
        for use in zoning_info.nearby_future_use:
            report.append(f"  • {use}")
        report.append("")

    report.append(f"Coordinates: ({zoning_info.latitude:.4f}, {zoning_info.longitude:.4f})")
    report.append("")

    return "\n".join(report)


def format_nearby_zoning_report(nearby_zoning: NearbyZoning) -> str:
    """
    Format nearby zoning analysis as a readable text report

    Args:
        nearby_zoning: NearbyZoning object

    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 80)
    report.append("NEARBY ZONING ANALYSIS")
    report.append("=" * 80)
    report.append("")

    if nearby_zoning.current_parcel:
        current = nearby_zoning.current_parcel
        report.append(f"Address: {current.address}")
        report.append(f"Current Zoning: {current.current_zoning} - {current.current_zoning_description}")
        report.append("")

    # Summary statistics
    report.append("NEIGHBORHOOD ZONING SUMMARY:")
    report.append(f"  Total Nearby Parcels: {nearby_zoning.total_nearby_parcels}")
    report.append(f"  Unique Zoning Types: {len(nearby_zoning.unique_zones)}")
    report.append(f"  Zone Diversity Score: {nearby_zoning.zone_diversity_score:.2f} (0.0=uniform, 1.0=all different)")
    report.append("")

    # Zoning pattern flags
    report.append("ZONING PATTERNS:")
    if nearby_zoning.residential_only:
        report.append("  ✓ Residential Only - All nearby parcels are residential")
    if nearby_zoning.commercial_nearby:
        report.append("  ⚠️  Commercial/Mixed Use Nearby")
    if nearby_zoning.industrial_nearby:
        report.append("  ⚠️  Industrial Zoning Nearby")
    if nearby_zoning.mixed_use_nearby:
        report.append("  • Mixed Use Development Nearby")
    report.append("")

    # Unique zones breakdown
    if nearby_zoning.unique_zones:
        report.append("NEARBY ZONING TYPES:")
        for zone in sorted(nearby_zoning.unique_zones):
            description = get_zoning_code_description(zone)
            count = sum(1 for p in nearby_zoning.nearby_parcels if p.current_zoning == zone)
            report.append(f"  • {zone}: {description} ({count} parcels)")
        report.append("")

    # Potential concerns
    if nearby_zoning.potential_concerns:
        report.append("⚠️  POTENTIAL CONCERNS:")
        for i, concern in enumerate(nearby_zoning.potential_concerns, 1):
            report.append(f"  {i}. {concern}")
        report.append("")
    else:
        report.append("✓ No significant zoning concerns identified")
        report.append("")

    # Detailed nearby parcel list (limit to first 10)
    if nearby_zoning.nearby_parcels:
        report.append("NEARBY PARCELS (showing up to 10):")
        for i, parcel in enumerate(nearby_zoning.nearby_parcels[:10], 1):
            report.append(f"  {i}. Parcel {parcel.parcel_number}")
            report.append(f"     Zoning: {parcel.current_zoning} - {parcel.current_zoning_description}")
            report.append(f"     Size: {parcel.acres:.2f} acres")
            if parcel.future_land_use:
                report.append(f"     Future: {parcel.future_land_use}")
        report.append("")

    return "\n".join(report)


# Test functions
def test_zoning_lookup():
    """Test the basic zoning lookup with sample addresses"""
    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "1398 W Hancock Avenue, Athens, GA 30606",
        "220 College Station Road, Athens, GA 30602",
    ]

    for address in test_addresses:
        print("\n" + "=" * 80)
        print(f"Testing: {address}")
        print("=" * 80)

        zoning_info = get_zoning_info(address)

        if zoning_info:
            print(format_zoning_report(zoning_info))
        else:
            print(f"❌ Could not retrieve zoning information for: {address}")


def test_nearby_zoning_analysis():
    """Test the nearby zoning analysis feature"""
    print("\n" + "=" * 80)
    print("TESTING NEARBY ZONING ANALYSIS")
    print("=" * 80)
    print()

    test_address = "1398 W Hancock Avenue, Athens, GA 30606"
    print(f"Analyzing nearby zoning for: {test_address}")
    print(f"Search radius: 250 meters")
    print()

    nearby_zoning = get_nearby_zoning(test_address, radius_meters=250)

    if nearby_zoning:
        print(format_nearby_zoning_report(nearby_zoning))
    else:
        print(f"❌ Could not retrieve nearby zoning analysis for: {test_address}")


if __name__ == "__main__":
    # Run basic test
    test_zoning_lookup()

    print("\n\n")

    # Run nearby zoning analysis test
    test_nearby_zoning_analysis()
