"""
Loudoun County School Percentile & Context Utility

Provides narrative-ready school context including percentile rankings,
trajectory analysis, and pre-computed narrative helpers for AI-generated
property analysis narratives.

Usage:
    from core.loudoun_school_percentiles import get_school_context

    context = get_school_context("Seldens Landing Elementary")
    print(f"County: {context['county']['percentile']}th percentile")
    print(f"State: {context['state']['percentile']}th percentile")
    print(f"Trajectory: {context['trajectory']['direction']}")
"""

import os
import pandas as pd
import warnings
from typing import Dict, Optional, Any, Tuple


# Data file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'loudoun')
PERFORMANCE_FILE = os.path.join(DATA_DIR, 'schools', 'school_performance_trends.csv')
METADATA_FILE = os.path.join(DATA_DIR, 'schools', 'school_metadata.csv')

# Cache for loaded data
_performance_df: Optional[pd.DataFrame] = None
_metadata_df: Optional[pd.DataFrame] = None


def _load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and cache school performance and metadata DataFrames."""
    global _performance_df, _metadata_df

    if _performance_df is None:
        _performance_df = pd.read_csv(PERFORMANCE_FILE)

    if _metadata_df is None:
        _metadata_df = pd.read_csv(METADATA_FILE)

    return _performance_df, _metadata_df


def normalize_school_name(name: str) -> str:
    """
    Normalize school name for consistent matching.

    Handles variations like:
        "Seldens Landing ES" -> "SELDENS LANDING"
        "Seldens Landing Elementary" -> "SELDENS LANDING"
        "Seldens Landing Elementary School" -> "SELDENS LANDING"
    """
    if pd.isna(name) or name is None:
        return ""

    # Convert to uppercase and strip
    name = str(name).upper().strip()

    # Remove periods and commas
    name = name.replace('.', '').replace(',', '')

    # Remove common school type suffixes (check longest first)
    suffixes = [
        ' ELEMENTARY SCHOOL',
        ' MIDDLE SCHOOL',
        ' HIGH SCHOOL',
        ' CHARTER ACADEMY',
        ' ELEMENTARY',
        ' MIDDLE',
        ' HIGH',
        ' ES',
        ' MS',
        ' HS'
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break

    return name


def _find_school_in_data(
    school_name: str,
    perf_df: pd.DataFrame,
    school_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Find a school in the performance data by name.

    Returns dict with matched school_name (as in data), school_type, and school_id.
    """
    normalized_target = normalize_school_name(school_name)

    # Filter to Loudoun County
    loudoun = perf_df[perf_df['Division_Name'] == 'Loudoun County'].copy()

    # Get unique schools
    unique_schools = loudoun.drop_duplicates(['School_ID', 'School_Name', 'School_Type'])

    for _, row in unique_schools.iterrows():
        normalized_row = normalize_school_name(row['School_Name'])

        # Check for exact match after normalization
        if normalized_target == normalized_row:
            # If school_type specified, verify it matches
            if school_type:
                row_type = _normalize_school_type(row['School_Type'])
                if row_type != _normalize_school_type(school_type):
                    continue
            return {
                'school_name': row['School_Name'],
                'school_type': row['School_Type'],
                'school_id': row['School_ID']
            }

        # Check if one contains the other (for partial matches)
        if normalized_target in normalized_row or normalized_row in normalized_target:
            if school_type:
                row_type = _normalize_school_type(row['School_Type'])
                if row_type != _normalize_school_type(school_type):
                    continue
            return {
                'school_name': row['School_Name'],
                'school_type': row['School_Type'],
                'school_id': row['School_ID']
            }

        # Check first word match
        target_words = normalized_target.split()
        row_words = normalized_row.split()
        if target_words and row_words and target_words[0] == row_words[0]:
            # Additional check: at least first word matches and it's substantial
            if len(target_words[0]) > 3:
                if school_type:
                    row_type = _normalize_school_type(row['School_Type'])
                    if row_type != _normalize_school_type(school_type):
                        continue
                return {
                    'school_name': row['School_Name'],
                    'school_type': row['School_Type'],
                    'school_id': row['School_ID']
                }

    return None


def _normalize_school_type(school_type: str) -> str:
    """Normalize school type to standard form."""
    if pd.isna(school_type):
        return ""

    school_type = str(school_type).upper().strip()

    type_mapping = {
        'ELEM': 'Elem',
        'ELEMENTARY': 'Elem',
        'MIDDLE': 'Middle',
        'HIGH': 'High',
        'COMBINED': 'Combined'
    }

    for key, value in type_mapping.items():
        if key in school_type:
            return value

    return school_type


def _get_percentile_bucket(percentile: float) -> str:
    """Map percentile to bucket."""
    if percentile >= 90:
        return "top_10"
    elif percentile >= 75:
        return "top_25"
    elif percentile >= 25:
        return "middle"
    else:
        return "bottom_25"


def _get_county_descriptor(bucket: str) -> str:
    """Get narrative descriptor for county percentile."""
    descriptors = {
        "top_10": "among the best in Loudoun",
        "top_25": "strong for Loudoun",
        "middle": "solid",
        "bottom_25": "below average for Loudoun"
    }
    return descriptors.get(bucket, "solid")


def _get_state_descriptor(bucket: str, percentile: float) -> str:
    """Get narrative descriptor for state percentile."""
    if bucket == "top_10":
        return "top tier statewide"
    elif bucket == "top_25":
        return "well above state average"
    elif bucket == "middle":
        if percentile >= 50:
            return "above average for Virginia"
        else:
            return "around state average"
    else:
        return "below state average"


def _get_trajectory_descriptor(direction: str, delta: float) -> str:
    """Get narrative descriptor for trajectory."""
    if direction == "improving":
        if delta >= 15:
            return "on a strong upward trajectory"
        else:
            return "on an upward trajectory"
    elif direction == "declining":
        if delta <= -15:
            return "showing significant decline"
        else:
            return "showing some decline"
    else:
        return "maintaining stable performance"


def _calculate_percentile(value: float, all_values: pd.Series) -> Tuple[float, int, int]:
    """
    Calculate percentile rank of a value within a series.

    Returns: (percentile, rank, total)
    """
    all_values = all_values.dropna()
    total = len(all_values)

    if total == 0:
        return (0.0, 0, 0)

    # Count how many values are less than or equal to this value
    rank_from_bottom = (all_values <= value).sum()

    # Percentile = (rank from bottom / total) * 100
    percentile = (rank_from_bottom / total) * 100

    # Rank from top (1 = best)
    rank_from_top = total - rank_from_bottom + 1

    return (round(percentile, 1), rank_from_top, total)


def get_school_context(school_name: str, school_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get narrative-ready context for a school.

    Args:
        school_name: Name of the school (will be normalized)
        school_type: Optional - "Elementary", "Middle", "High" (inferred if not provided)

    Returns:
        Dictionary with school metrics, percentiles, trajectory, and narrative helpers.
        Returns None if school not found.
    """
    try:
        perf_df, meta_df = _load_data()
    except Exception as e:
        warnings.warn(f"Failed to load school data: {e}")
        return None

    # Find the school
    school_match = _find_school_in_data(school_name, perf_df, school_type)

    if not school_match:
        warnings.warn(f"School not found: {school_name}")
        return None

    matched_name = school_match['school_name']
    matched_type = school_match['school_type']
    matched_id = school_match['school_id']

    # Normalize school type for comparisons
    normalized_type = _normalize_school_type(matched_type)

    # Get this school's data
    school_data = perf_df[
        (perf_df['School_ID'] == matched_id) &
        (perf_df['Division_Name'] == 'Loudoun County')
    ].sort_values('Year')

    if school_data.empty:
        warnings.warn(f"No performance data found for: {matched_name}")
        return None

    # Get latest year data
    latest_year = school_data['Year'].max()
    latest_data = school_data[school_data['Year'] == latest_year].iloc[0]

    # Build metrics
    metrics = {
        "overall_pass_rate": latest_data.get('Overall_Pass_Rate'),
        "math_pass_rate": latest_data.get('Math_Pass_Rate'),
        "reading_pass_rate": latest_data.get('Reading_Pass_Rate'),
        "science_pass_rate": latest_data.get('Science_Pass_Rate') if pd.notna(latest_data.get('Science_Pass_Rate')) else None,
        "history_pass_rate": latest_data.get('History_Pass_Rate') if pd.notna(latest_data.get('History_Pass_Rate')) else None,
        "year": latest_year
    }

    # Clean up None values for NaN
    for key in metrics:
        if pd.isna(metrics[key]):
            metrics[key] = None

    overall_rate = metrics['overall_pass_rate']

    # ===== COUNTY PERCENTILES =====
    # Get all Loudoun schools of same type for latest year
    loudoun_same_type = perf_df[
        (perf_df['Division_Name'] == 'Loudoun County') &
        (perf_df['School_Type'] == matched_type) &
        (perf_df['Year'] == latest_year)
    ]

    county_percentile, county_rank, county_total = _calculate_percentile(
        overall_rate,
        loudoun_same_type['Overall_Pass_Rate']
    )
    county_bucket = _get_percentile_bucket(county_percentile)

    county = {
        "percentile": int(round(county_percentile)),
        "rank": county_rank,
        "total": county_total,
        "bucket": county_bucket
    }

    # ===== STATE PERCENTILES =====
    # Get all VA schools of same type for latest year
    state_same_type = perf_df[
        (perf_df['School_Type'] == matched_type) &
        (perf_df['Year'] == latest_year)
    ]

    state_percentile, state_rank, state_total = _calculate_percentile(
        overall_rate,
        state_same_type['Overall_Pass_Rate']
    )
    state_bucket = _get_percentile_bucket(state_percentile)

    state = {
        "percentile": int(round(state_percentile)),
        "rank": state_rank,
        "total": state_total,
        "bucket": state_bucket
    }

    # ===== TRAJECTORY =====
    years_data = school_data[['Year', 'Overall_Pass_Rate']].dropna()
    years_available = len(years_data)

    if years_available >= 2:
        earliest = years_data.iloc[0]
        latest = years_data.iloc[-1]

        start_value = earliest['Overall_Pass_Rate']
        end_value = latest['Overall_Pass_Rate']
        delta = end_value - start_value

        # Determine direction based on thresholds
        if delta >= 5:
            direction = "improving"
        elif delta <= -5:
            direction = "declining"
        else:
            direction = "stable"

        trajectory = {
            "direction": direction,
            "delta": round(delta, 1),
            "start_year": earliest['Year'],
            "start_value": round(start_value, 1),
            "end_year": latest['Year'],
            "end_value": round(end_value, 1),
            "years_available": years_available
        }
    else:
        trajectory = {
            "direction": "insufficient_data",
            "delta": 0,
            "start_year": None,
            "start_value": None,
            "end_year": latest_year,
            "end_value": overall_rate,
            "years_available": years_available
        }

    # ===== NARRATIVE HELPERS =====
    county_descriptor = _get_county_descriptor(county_bucket)
    state_descriptor = _get_state_descriptor(state_bucket, state_percentile)
    trajectory_descriptor = _get_trajectory_descriptor(
        trajectory['direction'],
        trajectory['delta']
    )

    # Special flag: mid-pack for Loudoun but strong for Virginia
    # True when county is middle or bottom_25, but state is middle or better
    loudoun_context = (
        county_bucket in ["middle", "bottom_25"] and
        state_bucket in ["top_10", "top_25", "middle"] and
        state_percentile >= 50  # At least above state median
    )

    narrative = {
        "county_descriptor": county_descriptor,
        "state_descriptor": state_descriptor,
        "trajectory_descriptor": trajectory_descriptor,
        "loudoun_context": loudoun_context
    }

    # ===== BUILD RESULT =====
    result = {
        "school_name": matched_name,
        "school_type": _format_school_type(matched_type),
        "division": "Loudoun County",
        "metrics": metrics,
        "county": county,
        "state": state,
        "trajectory": trajectory,
        "narrative": narrative
    }

    return result


def _format_school_type(school_type: str) -> str:
    """Format school type for display."""
    type_mapping = {
        'Elem': 'Elementary',
        'Middle': 'Middle',
        'High': 'High',
        'Combined': 'Combined'
    }
    return type_mapping.get(school_type, school_type)


def get_school_comparison_narrative(school_name: str, school_type: Optional[str] = None) -> Optional[str]:
    """
    Generate a one-sentence narrative about the school's standing.

    Example outputs:
    - "Seldens Landing Elementary ranks among the best in Loudoun (top 10%) and is top tier statewide."
    - "Sugarland Elementary is solid for Loudoun but still above average for Virginia, on an upward trajectory."
    """
    context = get_school_context(school_name, school_type)

    if not context:
        return None

    school = context['school_name']
    county_desc = context['narrative']['county_descriptor']
    state_desc = context['narrative']['state_descriptor']
    trajectory_desc = context['narrative']['trajectory_descriptor']
    loudoun_context = context['narrative']['loudoun_context']

    # Build narrative
    if loudoun_context:
        # Special case: average for Loudoun but strong for Virginia
        narrative = f"{school} is {county_desc} but still {state_desc}, {trajectory_desc}."
    else:
        if context['county']['bucket'] == context['state']['bucket']:
            # Same bucket - combine
            narrative = f"{school} is {county_desc} and {state_desc}, {trajectory_desc}."
        else:
            # Different buckets - show both
            narrative = f"{school} ranks {county_desc} (top {100 - context['county']['percentile']}%) and is {state_desc}, {trajectory_desc}."

    return narrative


# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_school_percentiles():
    """Test the school percentile functions with sample schools."""
    print("=" * 70)
    print("SCHOOL PERCENTILE UTILITY TEST")
    print("=" * 70)

    # Load data to find good test cases
    perf_df, _ = _load_data()
    loudoun = perf_df[
        (perf_df['Division_Name'] == 'Loudoun County') &
        (perf_df['Year'] == '2024-2025')
    ]

    # Find schools at different percentiles
    elem = loudoun[loudoun['School_Type'] == 'Elem'].sort_values('Overall_Pass_Rate', ascending=False)

    if len(elem) > 0:
        # Top elementary
        top_school = elem.iloc[0]['School_Name']
        # Middle elementary (around 50th percentile)
        mid_idx = len(elem) // 2
        mid_school = elem.iloc[mid_idx]['School_Name']
        # Lower elementary (bottom quartile)
        low_idx = int(len(elem) * 0.8)  # 80th from top = 20th percentile
        low_school = elem.iloc[low_idx]['School_Name']

        test_schools = [
            (top_school, "Top performer"),
            (mid_school, "Mid-pack"),
            (low_school, "Lower performer")
        ]
    else:
        # Fallback test schools
        test_schools = [
            ("Seldens Landing Elementary", "Test 1"),
            ("Sugarland Elementary", "Test 2"),
            ("Sterling Elementary", "Test 3")
        ]

    for school_name, description in test_schools:
        print(f"\n{'='*70}")
        print(f"TEST: {description}")
        print(f"School: {school_name}")
        print("-" * 70)

        context = get_school_context(school_name)

        if context:
            print(f"Matched: {context['school_name']} ({context['school_type']})")
            print(f"\nMetrics ({context['metrics']['year']}):")
            print(f"  Overall Pass Rate: {context['metrics']['overall_pass_rate']}%")
            print(f"  Math: {context['metrics']['math_pass_rate']}%")
            print(f"  Reading: {context['metrics']['reading_pass_rate']}%")

            print(f"\nCounty Standing (Loudoun {context['school_type']} schools):")
            print(f"  Percentile: {context['county']['percentile']}th")
            print(f"  Rank: {context['county']['rank']} of {context['county']['total']}")
            print(f"  Bucket: {context['county']['bucket']}")
            print(f"  Descriptor: \"{context['narrative']['county_descriptor']}\"")

            print(f"\nState Standing (VA {context['school_type']} schools):")
            print(f"  Percentile: {context['state']['percentile']}th")
            print(f"  Rank: {context['state']['rank']} of {context['state']['total']}")
            print(f"  Bucket: {context['state']['bucket']}")
            print(f"  Descriptor: \"{context['narrative']['state_descriptor']}\"")

            print(f"\nTrajectory:")
            print(f"  Direction: {context['trajectory']['direction']}")
            print(f"  Change: {context['trajectory']['delta']:+.1f} points")
            print(f"  Period: {context['trajectory']['start_year']} -> {context['trajectory']['end_year']}")
            print(f"  Values: {context['trajectory']['start_value']}% -> {context['trajectory']['end_value']}%")
            print(f"  Descriptor: \"{context['narrative']['trajectory_descriptor']}\"")

            print(f"\nLoudoun Context Flag: {context['narrative']['loudoun_context']}")

            # Generate narrative
            narrative = get_school_comparison_narrative(school_name)
            print(f"\nGenerated Narrative:")
            print(f"  \"{narrative}\"")
        else:
            print("  School not found!")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_school_percentiles()
