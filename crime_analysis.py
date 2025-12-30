#!/usr/bin/env python3
"""
Crime analysis module for home buyers
Provides categorized crime data, statistics, trends, and safety scoring
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
from crime_lookup import get_crimes_near_address, CrimeIncident


# Crime categorization mapping
CRIME_CATEGORIES = {
    'violent': [
        'Assault: Aggravated',
        'Assault: Simple',
        'Assault: Intimidation',
        'Robbery',
        'Homicide: Murder/Nonnegligent Manslaughter',
        'Homicide: Negligent Manslaughter',
        'Kidnapping / Abduction',
        'Sexual Assault: Rape',
        'Sexual Assault: Sodomy',
        'Sexual Assault: Fondling',
        'Sexual Assault: With An Object',
        'Human Trafficking',
    ],
    'property': [
        'Burglary / Breaking and Entering',
        'Larceny: All Other',
        'Larceny: From MV',
        'Larceny: From Bldg',
        'Larceny: Shoplifting',
        'Larceny: Pocket-Picking',
        'Larceny: Purse-Snatching',
        'Larceny: Affixed MV Parts/Accessories',
        'Motor Vehicle Theft',
        'Arson',
        'Destruction / Damage / Vandalism',
        'Stolen Property Offenses',
        'Fraud: False Pretenses',
        'Fraud: Credit Card/Auto. Teller Machine',
        'Fraud: Impersonation',
        'Counterfeiting / Forgery',
        'Embezzlement',
        'Extortion / Blackmail',
    ],
    'traffic': [
        'Driving Under the Influence',
    ],
    'other': [
        'Drug/Narcotic: Violation',
        'Drug/Narcotic: Equipment',
        'Weapon Law Violations',
        'Liquor Law Violations',
        'Drunkenness',
        'Disorderly Conduct',
        'Trespass of Real Property',
        'Family Offenses, Nonviolent',
        'Prostitution',
        'Prostitution: Assist/Promoting',
        'Trafficking - Commercial Sex Acts',
    ]
}


@dataclass
class CrimeStatistics:
    """Statistics for crime data"""
    total_crimes: int
    violent_count: int
    property_count: int
    traffic_count: int
    other_count: int
    violent_percentage: float
    property_percentage: float
    traffic_percentage: float
    other_percentage: float
    crimes_per_month: float
    most_common_crime: str
    most_common_count: int


@dataclass
class TrendAnalysis:
    """Trend analysis comparing two time periods"""
    recent_count: int  # Last 6 months
    previous_count: int  # Previous 6 months
    change_count: int  # Difference
    change_percentage: float  # Percentage change
    trend: str  # "increasing", "decreasing", or "stable"
    trend_description: str  # Human-readable description


@dataclass
class SafetyScore:
    """Safety score with transparent calculation"""
    score: int  # 1-5, where 5 is safest
    level: str  # "Very Safe", "Safe", "Moderate", "Concerning", "High Risk"
    explanation: str  # Why this score was given
    factors: Dict[str, float]  # Individual factor scores


@dataclass
class ComparisonData:
    """Comparison to Athens-Clarke County average"""
    area_crime_count: int
    athens_average: float
    difference_count: float
    difference_percentage: float
    comparison_text: str  # "X% more/less than Athens average"
    relative_ranking: str  # "High activity area", "Above average", "Below average", "Low activity area"


@dataclass
class CrimeAnalysis:
    """Complete crime analysis for a location"""
    address: str
    radius_miles: float
    time_period_months: int
    crimes: List[CrimeIncident]
    statistics: CrimeStatistics
    trends: TrendAnalysis
    safety_score: SafetyScore
    category_breakdown: Dict[str, List[CrimeIncident]]
    comparison: Optional[ComparisonData] = None


def categorize_crime(crime_type: str) -> str:
    """
    Categorize a crime type into violent, property, traffic, or other

    Args:
        crime_type: Crime description from database

    Returns:
        Category name: 'violent', 'property', 'traffic', or 'other'
    """
    for category, crime_types in CRIME_CATEGORIES.items():
        if crime_type in crime_types:
            return category
    return 'other'  # Default if not found


def calculate_statistics(crimes: List[CrimeIncident], months: int) -> CrimeStatistics:
    """
    Calculate comprehensive crime statistics

    Args:
        crimes: List of crime incidents
        months: Time period in months

    Returns:
        CrimeStatistics object
    """
    total = len(crimes)

    if total == 0:
        return CrimeStatistics(
            total_crimes=0,
            violent_count=0,
            property_count=0,
            traffic_count=0,
            other_count=0,
            violent_percentage=0.0,
            property_percentage=0.0,
            traffic_percentage=0.0,
            other_percentage=0.0,
            crimes_per_month=0.0,
            most_common_crime="None",
            most_common_count=0
        )

    # Count by category
    category_counts = {'violent': 0, 'property': 0, 'traffic': 0, 'other': 0}
    crime_type_counts = defaultdict(int)

    for crime in crimes:
        category = categorize_crime(crime.crime_type)
        category_counts[category] += 1
        crime_type_counts[crime.crime_type] += 1

    # Find most common crime type
    most_common = max(crime_type_counts.items(), key=lambda x: x[1])

    return CrimeStatistics(
        total_crimes=total,
        violent_count=category_counts['violent'],
        property_count=category_counts['property'],
        traffic_count=category_counts['traffic'],
        other_count=category_counts['other'],
        violent_percentage=round(category_counts['violent'] / total * 100, 1),
        property_percentage=round(category_counts['property'] / total * 100, 1),
        traffic_percentage=round(category_counts['traffic'] / total * 100, 1),
        other_percentage=round(category_counts['other'] / total * 100, 1),
        crimes_per_month=round(total / months, 1),
        most_common_crime=most_common[0],
        most_common_count=most_common[1]
    )


def analyze_trends(crimes: List[CrimeIncident]) -> TrendAnalysis:
    """
    Analyze crime trends by comparing recent to previous 6 months

    Args:
        crimes: List of crime incidents

    Returns:
        TrendAnalysis object
    """
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    twelve_months_ago = now - timedelta(days=360)

    # Split into recent (last 6 months) and previous (6-12 months ago)
    recent_crimes = [c for c in crimes if c.date >= six_months_ago]
    previous_crimes = [c for c in crimes if twelve_months_ago <= c.date < six_months_ago]

    recent_count = len(recent_crimes)
    previous_count = len(previous_crimes)
    change_count = recent_count - previous_count

    # Calculate percentage change
    if previous_count > 0:
        change_percentage = round((change_count / previous_count) * 100, 1)
    else:
        change_percentage = 0.0 if recent_count == 0 else 100.0

    # Determine trend
    if abs(change_percentage) < 10:
        trend = "stable"
        trend_description = f"Crime is relatively stable ({change_percentage:+.1f}% change)"
    elif change_percentage > 0:
        trend = "increasing"
        trend_description = f"Crime is increasing ({change_percentage:+.1f}% increase)"
    else:
        trend = "decreasing"
        trend_description = f"Crime is decreasing ({change_percentage:+.1f}% decrease)"

    return TrendAnalysis(
        recent_count=recent_count,
        previous_count=previous_count,
        change_count=change_count,
        change_percentage=change_percentage,
        trend=trend,
        trend_description=trend_description
    )


def calculate_safety_score(statistics: CrimeStatistics, trends: TrendAnalysis,
                          radius_miles: float) -> SafetyScore:
    """
    Calculate a transparent safety score (1-100, where 100 is safest)

    Scoring Logic:
    - Start with base score of 100
    - Deduct for crime density (crimes per month per 0.5 sq miles)
    - Deduct for violent crime percentage
    - Deduct for increasing crime trends / bonus for decreasing
    - Designed to scale across U.S. cities with varying crime levels
    - Clamp to 1-100 range

    Args:
        statistics: Crime statistics
        trends: Trend analysis
        radius_miles: Search radius

    Returns:
        SafetyScore object with score and explanation
    """
    base_score = 100
    factors = {}
    explanations = []

    # Factor 1: Crime density (crimes per month, normalized to 0.5 mile radius)
    # Adjust for radius (normalize to 0.5 miles)
    area_factor = (radius_miles / 0.5) ** 2
    normalized_crimes_per_month = statistics.crimes_per_month / area_factor

    # Crime density deductions (designed for U.S. scale)
    if normalized_crimes_per_month >= 75:
        crime_density_deduction = 50
        explanations.append(f"Extreme crime density ({normalized_crimes_per_month:.1f} crimes/month)")
    elif normalized_crimes_per_month >= 50:
        crime_density_deduction = 40
        explanations.append(f"Very high crime density ({normalized_crimes_per_month:.1f} crimes/month)")
    elif normalized_crimes_per_month >= 30:
        crime_density_deduction = 30
        explanations.append(f"High crime density ({normalized_crimes_per_month:.1f} crimes/month)")
    elif normalized_crimes_per_month >= 15:
        crime_density_deduction = 20
        explanations.append(f"Moderate crime density ({normalized_crimes_per_month:.1f} crimes/month)")
    elif normalized_crimes_per_month >= 5:
        crime_density_deduction = 10
        explanations.append(f"Low crime density ({normalized_crimes_per_month:.1f} crimes/month)")
    else:
        crime_density_deduction = 0
        explanations.append(f"Very low crime density ({normalized_crimes_per_month:.1f} crimes/month)")

    factors['crime_density'] = -crime_density_deduction

    # Factor 2: Violent crime percentage
    if statistics.violent_percentage >= 30:
        violent_deduction = 25
        explanations.append(f"Very high violent crime rate ({statistics.violent_percentage:.1f}%)")
    elif statistics.violent_percentage >= 20:
        violent_deduction = 20
        explanations.append(f"High violent crime rate ({statistics.violent_percentage:.1f}%)")
    elif statistics.violent_percentage >= 15:
        violent_deduction = 15
        explanations.append(f"Concerning violent crime rate ({statistics.violent_percentage:.1f}%)")
    elif statistics.violent_percentage >= 10:
        violent_deduction = 10
        explanations.append(f"Moderate violent crime rate ({statistics.violent_percentage:.1f}%)")
    elif statistics.violent_percentage >= 5:
        violent_deduction = 5
        explanations.append(f"Low violent crime rate ({statistics.violent_percentage:.1f}%)")
    else:
        violent_deduction = 0
        explanations.append(f"Very low violent crime rate ({statistics.violent_percentage:.1f}%)")

    factors['violent_crime'] = -violent_deduction

    # Factor 3: Crime trends
    if trends.trend == "increasing" and trends.change_percentage >= 50:
        trend_adjustment = -15
        explanations.append(f"Crime is rapidly increasing ({trends.change_percentage:+.1f}%)")
    elif trends.trend == "increasing" and trends.change_percentage >= 20:
        trend_adjustment = -10
        explanations.append(f"Crime is significantly increasing ({trends.change_percentage:+.1f}%)")
    elif trends.trend == "increasing":
        trend_adjustment = -5
        explanations.append(f"Crime is slightly increasing ({trends.change_percentage:+.1f}%)")
    elif trends.trend == "decreasing" and trends.change_percentage <= -20:
        trend_adjustment = 5  # Bonus for significant decrease
        explanations.append(f"Crime is significantly decreasing ({trends.change_percentage:+.1f}%) ✓")
    elif trends.trend == "decreasing":
        trend_adjustment = 3  # Bonus for decrease
        explanations.append(f"Crime is decreasing ({trends.change_percentage:+.1f}%) ✓")
    else:
        trend_adjustment = 0
        explanations.append(f"Crime is stable ({trends.change_percentage:+.1f}%)")

    factors['trend'] = trend_adjustment

    # Calculate final score
    final_score = base_score + factors['crime_density'] + factors['violent_crime'] + factors['trend']
    final_score = max(1, min(100, round(final_score)))  # Clamp to 1-100

    # Determine level (for 1-100 scale)
    if final_score >= 80:
        level = "Very Safe"
    elif final_score >= 60:
        level = "Safe"
    elif final_score >= 40:
        level = "Moderate"
    elif final_score >= 20:
        level = "Concerning"
    else:
        level = "High Risk"
    explanation = " | ".join(explanations)

    return SafetyScore(
        score=final_score,
        level=level,
        explanation=explanation,
        factors=factors
    )


def analyze_crime_near_address(address: str, radius_miles: float = 0.5,
                               months_back: int = 12) -> Optional[CrimeAnalysis]:
    """
    Comprehensive crime analysis for a specific address

    Args:
        address: Street address in Athens-Clarke County
        radius_miles: Search radius in miles (default: 0.5)
        months_back: How many months of history (default: 12 = 1 year)
                     Can specify up to 60 months (5 years) for longer trends

    Returns:
        CrimeAnalysis object with complete analysis, or None if error
    """
    # Get crime data
    crimes = get_crimes_near_address(address, radius_miles, months_back)

    if crimes is None:
        return None

    # Calculate statistics
    statistics = calculate_statistics(crimes, months_back)

    # Analyze trends
    trends = analyze_trends(crimes)

    # Calculate safety score
    safety_score = calculate_safety_score(statistics, trends, radius_miles)

    # Group crimes by category
    category_breakdown = {
        'violent': [],
        'property': [],
        'traffic': [],
        'other': []
    }

    for crime in crimes:
        category = categorize_crime(crime.crime_type)
        category_breakdown[category].append(crime)

    # Calculate comparison to Athens average
    comparison = None
    try:
        from athens_baseline import get_athens_crime_baseline

        baseline = get_athens_crime_baseline(months_back=months_back)
        if baseline:
            area_count = statistics.total_crimes
            athens_avg = baseline.crimes_per_half_mile_circle

            # Adjust average if radius is different from 0.5 miles
            if radius_miles != 0.5:
                # Scale by area: (r1/r2)^2
                scale_factor = (radius_miles / 0.5) ** 2
                athens_avg = athens_avg * scale_factor

            difference = area_count - athens_avg
            if athens_avg > 0:
                diff_pct = round((difference / athens_avg) * 100, 1)
            else:
                diff_pct = 0.0

            # Generate comparison text
            if diff_pct > 0:
                comparison_text = f"{abs(diff_pct):.0f}% more crime than Athens average"
            elif diff_pct < 0:
                comparison_text = f"{abs(diff_pct):.0f}% less crime than Athens average"
            else:
                comparison_text = "Similar to Athens average"

            # Determine relative ranking
            if diff_pct >= 150:
                ranking = "Very high activity area"
            elif diff_pct >= 50:
                ranking = "High activity area"
            elif diff_pct >= 10:
                ranking = "Above average"
            elif diff_pct >= -10:
                ranking = "Average"
            elif diff_pct >= -40:
                ranking = "Below average"
            else:
                ranking = "Low activity area"

            comparison = ComparisonData(
                area_crime_count=area_count,
                athens_average=round(athens_avg, 1),
                difference_count=round(difference, 1),
                difference_percentage=diff_pct,
                comparison_text=comparison_text,
                relative_ranking=ranking
            )

    except Exception as e:
        print(f"⚠️  Could not calculate comparison: {e}")
        comparison = None

    return CrimeAnalysis(
        address=address,
        radius_miles=radius_miles,
        time_period_months=months_back,
        crimes=crimes,
        statistics=statistics,
        trends=trends,
        safety_score=safety_score,
        category_breakdown=category_breakdown,
        comparison=comparison
    )


def format_analysis_report(analysis: CrimeAnalysis) -> str:
    """
    Format a comprehensive crime analysis report

    Args:
        analysis: CrimeAnalysis object

    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"COMPREHENSIVE CRIME ANALYSIS")
    lines.append("=" * 80)
    lines.append(f"Address: {analysis.address}")
    lines.append(f"Search Radius: {analysis.radius_miles} miles")
    lines.append(f"Time Period: {analysis.time_period_months} months ({analysis.time_period_months // 12} years)")
    lines.append("")

    # Safety Score
    lines.append("=" * 80)
    lines.append("SAFETY SCORE")
    lines.append("=" * 80)
    # Visual bar for 1-100 scale (show 20 segments, each representing 5 points)
    filled_segments = analysis.safety_score.score // 5
    score_bar = "█" * filled_segments + "░" * (20 - filled_segments)
    lines.append(f"Score: {analysis.safety_score.score}/100  [{score_bar}]")
    lines.append(f"Level: {analysis.safety_score.level}")
    lines.append(f"\nFactors:")
    lines.append(f"  {analysis.safety_score.explanation}")
    lines.append("")

    # Overall Statistics
    lines.append("=" * 80)
    lines.append("OVERALL STATISTICS")
    lines.append("=" * 80)
    stats = analysis.statistics
    lines.append(f"Total Crimes: {stats.total_crimes}")
    lines.append(f"Crimes per Month: {stats.crimes_per_month:.1f}")
    lines.append(f"Most Common: {stats.most_common_crime} ({stats.most_common_count} incidents)")
    lines.append("")

    # Category Breakdown
    lines.append("CRIME CATEGORIES:")
    lines.append(f"  🔴 Violent Crimes:   {stats.violent_count:4d} ({stats.violent_percentage:5.1f}%)")
    lines.append(f"  🟠 Property Crimes:  {stats.property_count:4d} ({stats.property_percentage:5.1f}%)")
    lines.append(f"  🟡 Traffic Offenses: {stats.traffic_count:4d} ({stats.traffic_percentage:5.1f}%)")
    lines.append(f"  🟢 Other:            {stats.other_count:4d} ({stats.other_percentage:5.1f}%)")
    lines.append("")

    # Comparison to Athens Average
    if analysis.comparison:
        lines.append("=" * 80)
        lines.append("COMPARISON TO ATHENS-CLARKE COUNTY AVERAGE")
        lines.append("=" * 80)
        comp = analysis.comparison
        lines.append(f"This Area:      {comp.area_crime_count} crimes")
        lines.append(f"Athens Average: {comp.athens_average:.1f} crimes (for {analysis.radius_miles}-mile radius)")
        lines.append(f"Difference:     {comp.difference_count:+.1f} crimes ({comp.difference_percentage:+.0f}%)")
        lines.append(f"Assessment:     {comp.relative_ranking}")
        lines.append(f"                ({comp.comparison_text})")
        lines.append("")

    # Trend Analysis
    lines.append("=" * 80)
    lines.append("TREND ANALYSIS (Last 6 months vs. Previous 6 months)")
    lines.append("=" * 80)
    trend = analysis.trends
    lines.append(f"Recent (last 6 months):    {trend.recent_count} crimes")
    lines.append(f"Previous (6-12 months ago): {trend.previous_count} crimes")
    lines.append(f"Change: {trend.change_count:+d} crimes ({trend.change_percentage:+.1f}%)")
    lines.append(f"Trend: {trend.trend_description}")
    lines.append("")

    # Top crimes by category
    lines.append("=" * 80)
    lines.append("TOP CRIMES BY CATEGORY")
    lines.append("=" * 80)

    for category in ['violent', 'property', 'traffic', 'other']:
        category_crimes = analysis.category_breakdown[category]
        if category_crimes:
            crime_counts = defaultdict(int)
            for crime in category_crimes:
                crime_counts[crime.crime_type] += 1

            lines.append(f"\n{category.upper()} ({len(category_crimes)} total):")
            top_crimes = sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            for crime_type, count in top_crimes:
                lines.append(f"  • {crime_type}: {count}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("SCORING METHODOLOGY")
    lines.append("=" * 80)
    lines.append("Safety Score (1-100, 100 = safest):")
    lines.append("  • Starts at 100 (perfect score)")
    lines.append("  • Crime density: 0 to -50 points (based on crimes/month)")
    lines.append("  • Violent crime %: 0 to -25 points (based on % of crimes that are violent)")
    lines.append("  • Crime trends: -15 to +5 points (increasing = penalty, decreasing = bonus)")
    lines.append("  • Designed to scale across U.S. cities with varying crime levels")
    lines.append("")
    lines.append("Score Breakdown:")
    for factor, value in analysis.safety_score.factors.items():
        lines.append(f"  • {factor}: {value:+.0f} points")
    lines.append("")
    lines.append("=" * 80)
    lines.append("⚠️  DATA NOTES:")
    lines.append("   • Data from Athens-Clarke County Police Department")
    lines.append("   • Crime locations may be approximate for privacy")
    lines.append("   • Safety score is informational only - visit neighborhoods in person")
    lines.append("   • Crime statistics should be one of many factors in decision-making")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """Test crime analysis with standard addresses"""
    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    print("=" * 80)
    print("COMPREHENSIVE CRIME ANALYSIS TEST")
    print("=" * 80)
    print()

    for address in test_addresses:
        print(f"\n\n{'#' * 80}")
        print(f"# ANALYZING: {address}")
        print(f"{'#' * 80}\n")

        try:
            # Test with default: 12 months (1 year)
            analysis = analyze_crime_near_address(address, radius_miles=0.5, months_back=12)

            if analysis:
                report = format_analysis_report(analysis)
                print(report)
            else:
                print(f"❌ Failed to analyze {address}")

        except Exception as e:
            print(f"❌ Error analyzing {address}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
