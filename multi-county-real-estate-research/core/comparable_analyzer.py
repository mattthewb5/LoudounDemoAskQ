"""
Comparable Sales Analyzer
Analyzes comparable sales data to estimate property values.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from statistics import mean, median, stdev
import math
from core.market_adjustments import (
    adjust_comp_for_time,
    score_comp_similarity,
    is_same_subdivision,
    parse_sale_date,
    calculate_size_adjusted_psf,
    DEFAULT_ANNUAL_APPRECIATION,
    SIZE_ADJUSTMENT_CONFIG
)


@dataclass
class PriceAnalysis:
    """Analysis results from comparable sales."""
    comparable_count: int
    avg_sale_price: float
    median_sale_price: float
    price_std_dev: Optional[float]
    avg_price_per_sqft: Optional[float]
    median_price_per_sqft: Optional[float]
    price_per_sqft_std_dev: Optional[float]
    recent_sales_count: int
    nearby_sales_count: int
    confidence_score: float


class ComparableAnalyzer:
    """Analyzes comparable sales to estimate property values."""

    def __init__(self):
        pass

    def analyze_comparables(self, comparables: List, target_sqft: Optional[int] = None) -> PriceAnalysis:
        """
        Analyze comparable sales data.

        Args:
            comparables: List of ComparableSale objects
            target_sqft: Square footage of target property (if known)

        Returns:
            PriceAnalysis object with statistics
        """
        if not comparables:
            return PriceAnalysis(
                comparable_count=0,
                avg_sale_price=0,
                median_sale_price=0,
                price_std_dev=None,
                avg_price_per_sqft=None,
                median_price_per_sqft=None,
                price_per_sqft_std_dev=None,
                recent_sales_count=0,
                nearby_sales_count=0,
                confidence_score=0.0
            )

        # Extract sale prices
        sale_prices = [comp.sale_price for comp in comparables]

        # Calculate basic price statistics
        avg_price = mean(sale_prices)
        median_price = median(sale_prices)
        std_dev = stdev(sale_prices) if len(sale_prices) > 1 else None

        # Extract price per sqft (if available)
        price_per_sqft_values = [
            comp.price_per_sqft for comp in comparables
            if comp.price_per_sqft is not None
        ]

        avg_price_per_sqft = mean(price_per_sqft_values) if price_per_sqft_values else None
        median_price_per_sqft = median(price_per_sqft_values) if price_per_sqft_values else None
        price_per_sqft_std = stdev(price_per_sqft_values) if len(price_per_sqft_values) > 1 else None

        # Count recent sales (within 0.25 miles)
        nearby_count = sum(1 for comp in comparables if comp.distance_miles <= 0.25)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            len(comparables),
            len(price_per_sqft_values),
            nearby_count,
            std_dev,
            avg_price
        )

        return PriceAnalysis(
            comparable_count=len(comparables),
            avg_sale_price=avg_price,
            median_sale_price=median_price,
            price_std_dev=std_dev,
            avg_price_per_sqft=avg_price_per_sqft,
            median_price_per_sqft=median_price_per_sqft,
            price_per_sqft_std_dev=price_per_sqft_std,
            recent_sales_count=len(comparables),
            nearby_sales_count=nearby_count,
            confidence_score=confidence
        )

    def _calculate_confidence(
        self,
        comp_count: int,
        price_per_sqft_count: int,
        nearby_count: int,
        std_dev: Optional[float],
        avg_price: float
    ) -> float:
        """
        Calculate confidence score (0-100) based on data quality.

        Factors:
        - Number of comparables (more is better)
        - Price per sqft availability (better for accuracy)
        - Proximity of comparables (closer is better)
        - Price variance (lower is better)
        """
        confidence = 0.0

        # Factor 1: Number of comparables (max 30 points)
        if comp_count >= 10:
            confidence += 30
        elif comp_count >= 5:
            confidence += 20
        elif comp_count >= 3:
            confidence += 10
        else:
            confidence += comp_count * 3

        # Factor 2: Price per sqft data (max 25 points)
        if price_per_sqft_count >= 5:
            confidence += 25
        else:
            confidence += price_per_sqft_count * 5

        # Factor 3: Nearby sales (max 25 points)
        if nearby_count >= 5:
            confidence += 25
        elif nearby_count >= 3:
            confidence += 20
        else:
            confidence += nearby_count * 5

        # Factor 4: Price consistency (max 20 points)
        if std_dev and avg_price > 0:
            coefficient_of_variation = (std_dev / avg_price) * 100
            if coefficient_of_variation < 10:
                confidence += 20
            elif coefficient_of_variation < 20:
                confidence += 15
            elif coefficient_of_variation < 30:
                confidence += 10
            else:
                confidence += 5
        else:
            confidence += 10  # Neutral if we can't calculate

        return min(confidence, 100.0)

    def calculate_size_weighted_estimate(
        self,
        comparables: List,
        target_sqft: int
    ) -> Optional[float]:
        """
        Calculate property value estimate using size-weighted comparables.

        Comparables more similar in size to the target are weighted more heavily.

        Args:
            comparables: List of ComparableSale objects
            target_sqft: Target property square footage

        Returns:
            Size-weighted price estimate or None if insufficient data
        """
        # Filter for comparables with sqft data
        valid_comps = [c for c in comparables if c.sqft and c.sqft > 0 and c.price_per_sqft]

        if not valid_comps:
            return None

        # Calculate weights based on size similarity
        weights = []
        for comp in valid_comps:
            # Calculate size difference percentage
            size_diff = abs(comp.sqft - target_sqft) / target_sqft
            # Weight decreases as size difference increases
            # exp(-size_diff) gives us a weight between 0 and 1
            # Properties with <10% size difference get ~90% weight
            # Properties with 50% size difference get ~60% weight
            weight = math.exp(-size_diff)
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average price per sqft
        weighted_ppf = sum(
            comp.price_per_sqft * weight
            for comp, weight in zip(valid_comps, normalized_weights)
        )

        # Apply to target sqft
        return weighted_ppf * target_sqft

    def apply_market_adjustments(
        self,
        comparables: List,
        subject_property: Dict,
        annual_appreciation: float = DEFAULT_ANNUAL_APPRECIATION
    ) -> List:
        """
        Apply time adjustments and similarity scoring to all comparables.

        This enriches each comp with:
        - Time-adjusted sale price
        - Time-adjusted price per sqft
        - Similarity score

        Args:
            comparables: List of ComparableSale objects
            subject_property: Dict with subject property data (sqft, year_built, address, subdivision)
            annual_appreciation: Annual appreciation rate (default: Loudoun County 7.34%)

        Returns:
            List of ComparableSale objects with adjustments applied
        """
        adjusted_comps = []

        for comp in comparables:
            # Parse sale date
            sale_date = parse_sale_date(comp.sale_date)

            if sale_date:
                # Apply time adjustment
                adjusted_price, time_adj_pct = adjust_comp_for_time(
                    comp.sale_price,
                    sale_date,
                    annual_appreciation
                )

                # Update comp with adjusted values
                comp.adjusted_sale_price = int(adjusted_price)
                comp.time_adjustment_pct = round(time_adj_pct, 1)

                # Calculate adjusted price per sqft
                if comp.sqft and comp.sqft > 0:
                    comp.adjusted_price_per_sqft = round(adjusted_price / comp.sqft, 2)
            else:
                # No date available - use original price
                comp.adjusted_sale_price = comp.sale_price
                comp.time_adjustment_pct = 0.0
                comp.adjusted_price_per_sqft = comp.price_per_sqft

            # Calculate similarity score
            comp_dict = {
                "sqft": comp.sqft,
                "year_built": comp.year_built,
                "address": comp.address,
                "subdivision": comp.subdivision,
                "distance_miles": comp.distance_miles,
                "sale_date": comp.sale_date
            }

            comp.similarity_score = round(score_comp_similarity(subject_property, comp_dict), 1)

            adjusted_comps.append(comp)

        # Sort by similarity score (highest first)
        adjusted_comps.sort(key=lambda c: c.similarity_score or 0, reverse=True)

        return adjusted_comps

    def calculate_similarity_weighted_estimate(
        self,
        comparables: List,
        target_sqft: int,
        top_n: int = 5
    ) -> Optional[Dict]:
        """
        Calculate property value using similarity-weighted, time-adjusted comparables
        with conservative size adjustment.

        Args:
            comparables: List of ComparableSale objects (should already have adjustments applied)
            target_sqft: Target property square footage
            top_n: Number of top comparables to use (default: 5)

        Returns:
            Dict with estimated_value, weighted_psf, size_adjusted_psf, and methodology details
        """
        # Filter for comps with valid data
        valid_comps = [c for c in comparables
                      if c.sqft and c.sqft > 0
                      and c.adjusted_price_per_sqft
                      and c.similarity_score is not None]

        if not valid_comps:
            return None

        # Use top N most similar comps
        top_comps = valid_comps[:top_n]

        if not top_comps:
            return None

        # Calculate weighted average $/sqft using similarity scores as weights
        total_weight = sum(c.similarity_score for c in top_comps)

        if total_weight == 0:
            return None

        weighted_psf = sum(
            c.adjusted_price_per_sqft * c.similarity_score
            for c in top_comps
        ) / total_weight

        # Calculate average sqft of comps for size adjustment
        comp_avg_sqft = sum(c.sqft for c in top_comps) / len(top_comps)

        # Apply size adjustment if enabled
        size_adjusted_psf = weighted_psf
        size_adjustment_pct = 0.0

        if SIZE_ADJUSTMENT_CONFIG["enabled"]:
            size_adjusted_psf, size_adjustment_pct = calculate_size_adjusted_psf(
                comp_avg_sqft=comp_avg_sqft,
                subject_sqft=target_sqft,
                comp_psf=weighted_psf,
                degradation_rate=SIZE_ADJUSTMENT_CONFIG["degradation_rate"]
            )

        # Calculate final estimated value using size-adjusted $/sqft
        estimated_value = size_adjusted_psf * target_sqft

        return {
            "estimated_value": int(estimated_value),
            "base_weighted_psf": round(weighted_psf, 2),
            "size_adjusted_psf": round(size_adjusted_psf, 2),
            "size_adjustment_pct": round(size_adjustment_pct, 2),
            "comp_avg_sqft": int(comp_avg_sqft),
            "subject_sqft": target_sqft,
            "size_ratio": round(target_sqft / comp_avg_sqft, 2),
            "comps_used": top_comps,
            "methodology": "Similarity-weighted, time-adjusted, size-adjusted comparables",
            "top_comp_count": len(top_comps)
        }

    def estimate_value(
        self,
        analysis: PriceAnalysis,
        target_sqft: Optional[int] = None,
        api_estimate: Optional[int] = None,
        comparables: Optional[List] = None,
        similarity_weighted_result: Optional[Dict] = None
    ) -> Dict:
        """
        Estimate property value based on analysis.

        Args:
            analysis: PriceAnalysis object
            target_sqft: Target property square footage
            api_estimate: Value estimate from API (RentCast, etc.)
            comparables: List of ComparableSale objects for size-weighted estimation
            similarity_weighted_result: Result from calculate_similarity_weighted_estimate()

        Returns:
            Dictionary with value estimate and confidence interval
        """
        estimates = []
        weights = []

        # Method 1: Similarity-weighted, time & size adjusted estimate (HIGHEST PRIORITY)
        similarity_weighted_estimate = None
        if similarity_weighted_result:
            similarity_weighted_estimate = similarity_weighted_result['estimated_value']
            estimates.append(similarity_weighted_estimate)
            # Use 85% weight when we have high-quality similarity-weighted results
            # This trusts the time-adjusted, size-adjusted, similarity-scored methodology
            weights.append(0.85)

        # Method 2: Size-weighted estimate (if not using similarity-weighted)
        size_weighted_estimate = None
        if comparables and target_sqft and not similarity_weighted_result:
            size_weighted_estimate = self.calculate_size_weighted_estimate(comparables, target_sqft)
            if size_weighted_estimate:
                estimates.append(size_weighted_estimate)
                weights.append(0.5)  # High weight for size-adjusted estimate

        # Method 3: Median comparable sale price (lower weight when similarity-weighted available)
        if analysis.comparable_count > 0:
            estimates.append(analysis.median_sale_price)
            # Reduce median weight from 20% to 5% when similarity-weighted is available
            # Median is too sensitive to outliers and small samples
            weights.append(0.05 if similarity_weighted_estimate else 0.3)

        # Method 4: Price per sqft (if available and not using similarity/size-weighted)
        if analysis.median_price_per_sqft and target_sqft and not (similarity_weighted_estimate or size_weighted_estimate):
            ppf_estimate = analysis.median_price_per_sqft * target_sqft
            estimates.append(ppf_estimate)
            weights.append(0.4)

        # Method 5: API estimate (lower weight when similarity-weighted available)
        if api_estimate:
            estimates.append(api_estimate)
            # Reduce API weight from 30% to 10% when similarity-weighted is available
            # API estimates don't account for property-specific features or recent sales
            weights.append(0.10 if similarity_weighted_estimate else 0.3)

        # Calculate weighted average
        if not estimates:
            return {
                'estimate': None,
                'confidence_low': None,
                'confidence_high': None,
                'confidence_score': 0.0,
                'method': 'insufficient_data'
            }

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted estimate
        weighted_estimate = sum(e * w for e, w in zip(estimates, normalized_weights))

        # Calculate confidence interval based on std dev
        if analysis.price_std_dev:
            # Use standard error for confidence interval
            margin = 1.96 * (analysis.price_std_dev / math.sqrt(analysis.comparable_count))
            confidence_low = weighted_estimate - margin
            confidence_high = weighted_estimate + margin
        else:
            # Use 10% margin if no std dev
            margin = weighted_estimate * 0.10
            confidence_low = weighted_estimate - margin
            confidence_high = weighted_estimate + margin

        # Determine method used
        if similarity_weighted_estimate:
            method = 'similarity_weighted_time_adjusted'
        elif size_weighted_estimate:
            method = 'size_weighted'
        else:
            method = 'weighted_average'

        return {
            'estimate': int(weighted_estimate),
            'confidence_low': int(confidence_low),
            'confidence_high': int(confidence_high),
            'confidence_score': analysis.confidence_score,
            'method': method,
            'components': {
                'similarity_weighted_estimate': int(similarity_weighted_estimate) if similarity_weighted_estimate else None,
                'size_weighted_estimate': int(size_weighted_estimate) if size_weighted_estimate else None,
                'comparable_median': analysis.median_sale_price if analysis.comparable_count > 0 else None,
                'price_per_sqft_estimate': int(analysis.median_price_per_sqft * target_sqft) if analysis.median_price_per_sqft and target_sqft else None,
                'api_estimate': api_estimate
            }
        }

    def format_analysis_report(self, analysis: PriceAnalysis) -> str:
        """Format analysis report for display."""
        lines = [
            "",
            "=" * 70,
            "COMPARABLE SALES ANALYSIS",
            "=" * 70,
            f"Number of Comparables: {analysis.comparable_count}",
            f"Nearby Sales (< 0.25 mi): {analysis.nearby_sales_count}",
            "",
            "Price Statistics:",
            f"  Average Sale Price: ${analysis.avg_sale_price:,.0f}" if analysis.avg_sale_price else "  Average Sale Price: N/A",
            f"  Median Sale Price: ${analysis.median_sale_price:,.0f}" if analysis.median_sale_price else "  Median Sale Price: N/A",
            f"  Price Std Dev: ${analysis.price_std_dev:,.0f}" if analysis.price_std_dev else "  Price Std Dev: N/A",
        ]

        if analysis.avg_price_per_sqft:
            lines.extend([
                "",
                "Price per Square Foot:",
                f"  Average: ${analysis.avg_price_per_sqft:,.2f}/sqft",
                f"  Median: ${analysis.median_price_per_sqft:,.2f}/sqft" if analysis.median_price_per_sqft else "",
                f"  Std Dev: ${analysis.price_per_sqft_std_dev:,.2f}/sqft" if analysis.price_per_sqft_std_dev else "",
            ])

        lines.extend([
            "",
            f"Confidence Score: {analysis.confidence_score:.1f}/100",
            "=" * 70
        ])

        return "\n".join(lines)

    def get_top_comparables(self, comparables: List, n: int = 3) -> List:
        """
        Get the N most relevant comparable sales.

        Args:
            comparables: List of ComparableSale objects
            n: Number of top comparables to return

        Returns:
            List of top N comparable sales
        """
        if not comparables:
            return []

        # Sort by distance first
        sorted_comps = sorted(comparables, key=lambda x: x.distance_miles)

        return sorted_comps[:n]


if __name__ == '__main__':
    # Test with sample data
    from attom_client import ComparableSale

    # Create sample comparable sales
    sample_comps = [
        ComparableSale(
            address="123 Main St",
            city="Leesburg",
            state="VA",
            zipcode="20176",
            sale_price=950000,
            sale_date="2024-06-15",
            bedrooms=4,
            bathrooms=3.5,
            sqft=2500,
            year_built=2010,
            distance_miles=0.1
        ),
        ComparableSale(
            address="456 Oak Ave",
            city="Leesburg",
            state="VA",
            zipcode="20176",
            sale_price=1100000,
            sale_date="2024-08-20",
            bedrooms=4,
            bathrooms=4.0,
            sqft=2800,
            year_built=2012,
            distance_miles=0.2
        ),
        ComparableSale(
            address="789 Pine Dr",
            city="Leesburg",
            state="VA",
            zipcode="20176",
            sale_price=875000,
            sale_date="2024-05-10",
            bedrooms=3,
            bathrooms=3.0,
            sqft=2200,
            year_built=2008,
            distance_miles=0.3
        )
    ]

    analyzer = ComparableAnalyzer()

    # Analyze comparables
    analysis = analyzer.analyze_comparables(sample_comps, target_sqft=2600)
    print(analyzer.format_analysis_report(analysis))

    # Estimate value
    estimate = analyzer.estimate_value(analysis, target_sqft=2600, api_estimate=1450000)
    print("\nVALUE ESTIMATE:")
    print(f"  Estimated Value: ${estimate['estimate']:,}")
    print(f"  Confidence Interval: ${estimate['confidence_low']:,} - ${estimate['confidence_high']:,}")
    print(f"  Confidence Score: {estimate['confidence_score']:.1f}/100")
