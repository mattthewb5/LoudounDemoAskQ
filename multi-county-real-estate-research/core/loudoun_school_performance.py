"""
Loudoun County School Performance Analysis Module

Provides functions for loading school performance data, finding peer schools,
and creating comparison charts for the Loudoun County real estate app.
"""

import os
import pandas as pd
import plotly.express as px
from math import radians, cos, sin, asin, sqrt
from typing import List, Tuple, Optional

# Data file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'loudoun')
PERFORMANCE_FILE = os.path.join(DATA_DIR, 'school_performance_trends_with_state_avg.csv')
COORDINATES_FILE = os.path.join(DATA_DIR, 'loudoun_school_coordinates.csv')


def load_performance_data() -> pd.DataFrame:
    """
    Load school performance data with state averages.

    Returns:
        DataFrame with columns: School_ID, School_Name, Division_Name, School_Type,
        Year, History_Pass_Rate, Math_Pass_Rate, Reading_Pass_Rate,
        Science_Pass_Rate, Writing_Pass_Rate, Overall_Pass_Rate
    """
    df = pd.read_csv(PERFORMANCE_FILE)

    # Defensive data cleaning: strip whitespace from school names
    # Some source data has trailing spaces (e.g., "Belmont Station Elementary ")
    if 'School_Name' in df.columns:
        df['School_Name'] = df['School_Name'].str.strip()

    return df


def load_school_coordinates() -> pd.DataFrame:
    """
    Load Loudoun school coordinates.

    Returns:
        DataFrame with columns: School_Name, School_Type, Latitude, Longitude
    """
    df = pd.read_csv(COORDINATES_FILE)
    return df


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)

    Returns:
        Distance in miles
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Earth's radius in miles
    r = 3956

    return c * r


def normalize_school_name(name):
    """
    Normalize school names for consistent matching across data sources.

    Handles:
        - Case differences (uppercase)
        - Punctuation (removes periods, commas)
        - School type suffixes (Elementary, Middle, High, ES, MS, HS)
        - Middle initials (removes single-letter words)

    Examples:
        "Steuart W. Weller Elementary" → "STEUART WELLER"
        "Belmont Ridge Middle" → "BELMONT RIDGE"
        "John F. Kennedy High" → "JOHN KENNEDY"

    Args:
        name: School name string (can be None/NaN)

    Returns:
        Normalized uppercase name without type suffixes or middle initials
    """
    if pd.isna(name) or name is None:
        return ""

    # Convert to uppercase and strip whitespace
    name = str(name).upper().strip()

    # Remove periods and commas
    name = name.replace('.', '').replace(',', '')

    # Remove common school type suffixes (check longest first to avoid partial matches)
    suffixes = [
        ' ELEMENTARY SCHOOL',
        ' MIDDLE SCHOOL',
        ' HIGH SCHOOL',
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
            break  # Only remove one suffix

    # Remove single-letter words (middle initials like "W", "J", etc.)
    words = name.split()
    words = [w for w in words if len(w) > 1]
    name = ' '.join(words)

    return name


def get_school_coordinates(school_name: str, coords_df: pd.DataFrame) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for a school by name.

    Args:
        school_name: Name of the school to find
        coords_df: DataFrame with school coordinates

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    if coords_df is None or coords_df.empty:
        return None

    normalized_target = normalize_school_name(school_name)

    for _, row in coords_df.iterrows():
        normalized_row = normalize_school_name(row['School_Name'])

        # Check for exact match after normalization
        if normalized_target == normalized_row:
            return (row['Latitude'], row['Longitude'])

        # Check if one contains the other (for partial matches)
        if normalized_target in normalized_row or normalized_row in normalized_target:
            return (row['Latitude'], row['Longitude'])

        # Check first word match (school name prefix)
        target_words = normalized_target.split()
        row_words = normalized_row.split()
        if target_words and row_words and target_words[0] == row_words[0]:
            # Additional check: at least 2 matching words
            matching = sum(1 for w in target_words if w in row_words)
            if matching >= 2:
                return (row['Latitude'], row['Longitude'])

    return None


def find_peer_schools(
    school_name: str,
    school_type: str,
    subject_lat: float,
    subject_lon: float,
    coords_df: pd.DataFrame,
    n: int = 2
) -> List[Tuple[str, float]]:
    """
    Find n nearest peer schools of same type.

    Args:
        school_name: Subject school name (to exclude)
        school_type: 'Elem', 'Middle', or 'High'
        subject_lat, subject_lon: Subject property coordinates
        coords_df: DataFrame with school coordinates
        n: Number of peers to find (default 2)

    Returns:
        List of tuples: [(school_name, distance_miles), ...]
    """
    if coords_df is None or coords_df.empty:
        return []

    # Map school type to coordinates file format
    type_mapping = {
        'Elem': 'Elem',
        'Elementary': 'Elem',
        'Middle': 'Middle',
        'High': 'High'
    }
    target_type = type_mapping.get(school_type, school_type)

    # Filter to same school type
    same_type = coords_df[coords_df['School_Type'] == target_type].copy()

    if same_type.empty:
        return []

    # Calculate distance from subject property to each school
    distances = []
    normalized_subject = normalize_school_name(school_name)

    for _, row in same_type.iterrows():
        normalized_row = normalize_school_name(row['School_Name'])

        # Skip if this is the subject school
        if normalized_subject == normalized_row:
            continue
        if normalized_subject in normalized_row or normalized_row in normalized_subject:
            continue

        # Calculate distance from subject PROPERTY (not subject school)
        dist = haversine(subject_lat, subject_lon, row['Latitude'], row['Longitude'])
        distances.append((row['School_Name'], dist))

    # Sort by distance
    distances.sort(key=lambda x: x[1])

    # Return top n
    return distances[:n]


def match_school_in_performance_data(school_name: str, perf_df: pd.DataFrame) -> Optional[str]:
    """
    Find matching school name in performance data using priority matching.

    Priority Matching Strategy:
    ---------------------------
    1. LITERAL EXACT MATCH (case-insensitive)
       - Handles collision cases where schools share normalized names
       - Example: "Riverside High" vs "Riverside Elementary" both normalize to "RIVERSIDE"
       - Without this check, wrong school could be returned

    2. NORMALIZED EXACT MATCH
       - Handles middle initial variations
       - Example: "Steuart Weller Elementary" matches "Steuart W. Weller Elementary"
       - Both normalize to "STEUART WELLER"

    3. NORMALIZED PARTIAL MATCH
       - Fallback for unusual name variations
       - Example: "Sugarland ES" matches "Sugarland Elementary"
       - One normalized name contains the other

    Why Priority Matters:
    ---------------------
    Without priority #1 (literal exact), normalized matching alone would create
    false positives. For example, searching for "Riverside High" would incorrectly
    match "Riverside Elementary" since both normalize to "RIVERSIDE". The literal
    exact match catches the correct school before normalization is attempted.

    Args:
        school_name: School name to search for (from boundary assignment data)
        perf_df: Performance DataFrame containing VADOE school data

    Returns:
        Exact school name from performance data, or None if no match found

    Examples:
        >>> match_school_in_performance_data("Riverside High", perf_df)
        "Riverside High"  # Literal exact match (Priority 1)

        >>> match_school_in_performance_data("Steuart Weller Elementary", perf_df)
        "Steuart W. Weller Elementary"  # Normalized exact match (Priority 2)
    """
    # Get unique school names from Loudoun County
    loudoun_schools = perf_df[perf_df['Division_Name'] == 'Loudoun County']['School_Name'].unique()

    # Priority 1: Literal exact match (case-insensitive)
    # Catches: "Riverside High" exactly (not "Riverside Elementary")
    target_lower = school_name.strip().lower()
    for perf_name in loudoun_schools:
        if perf_name.strip().lower() == target_lower:
            return perf_name

    # Priority 2 & 3: Normalized matching
    # Catches: middle initials, name variations
    normalized_target = normalize_school_name(school_name)

    for perf_name in loudoun_schools:
        normalized_perf = normalize_school_name(perf_name)

        # Priority 2: Normalized exact match
        # Example: "STEUART WELLER" == "STEUART WELLER"
        if normalized_target == normalized_perf:
            return perf_name

        # Priority 3: Normalized partial match
        # Example: "SUGARLAND" in "SUGARLAND ELEMENTARY"
        if normalized_target in normalized_perf or normalized_perf in normalized_target:
            return perf_name

    return None


def create_performance_chart(
    subject_school: str,
    peer_schools: List[Tuple[str, float]],
    metric_name: str,
    metric_col: str,
    school_type: str,
    perf_df: pd.DataFrame
) -> Optional[px.line]:
    """
    Create line chart comparing school performance.

    Args:
        subject_school: Name of subject property school
        peer_schools: List of (school_name, distance) tuples
        metric_name: Display name (e.g., "Math")
        metric_col: Column name in data (e.g., "Math_Pass_Rate")
        school_type: 'Elem', 'Middle', or 'High'
        perf_df: Performance DataFrame

    Returns:
        Plotly figure object, or None if no data
    """
    chart_data = []

    # Map school type
    type_mapping = {
        'Elem': 'Elem',
        'Elementary': 'Elem',
        'Middle': 'Middle',
        'High': 'High'
    }
    target_type = type_mapping.get(school_type, school_type)

    # 1. Get subject school data
    subject_match = match_school_in_performance_data(subject_school, perf_df)
    if subject_match:
        subject_data = perf_df[
            (perf_df['School_Name'] == subject_match) &
            (perf_df['Division_Name'] == 'Loudoun County')
        ]
        for _, row in subject_data.iterrows():
            if pd.notna(row.get(metric_col)):
                chart_data.append({
                    'Year': row['Year'],
                    'Pass_Rate': row[metric_col],
                    'School': subject_school
                })

    # 2. Get Virginia State Average data
    state_data = perf_df[
        (perf_df['School_ID'] == 999999) &
        (perf_df['School_Type'] == target_type)
    ]
    for _, row in state_data.iterrows():
        if pd.notna(row.get(metric_col)):
            chart_data.append({
                'Year': row['Year'],
                'Pass_Rate': row[metric_col],
                'School': 'Virginia State Average'
            })

    # 3. Get peer school data
    for peer_name, peer_dist in peer_schools:
        peer_match = match_school_in_performance_data(peer_name, perf_df)
        if peer_match:
            peer_data = perf_df[
                (perf_df['School_Name'] == peer_match) &
                (perf_df['Division_Name'] == 'Loudoun County')
            ]
            display_name = f"{peer_name} ({peer_dist:.1f} mi)"
            for _, row in peer_data.iterrows():
                if pd.notna(row.get(metric_col)):
                    chart_data.append({
                        'Year': row['Year'],
                        'Pass_Rate': row[metric_col],
                        'School': display_name
                    })

    if not chart_data:
        return None

    # Create DataFrame for plotting
    chart_df = pd.DataFrame(chart_data)

    # Sort by Year to ensure chronological x-axis order
    # (Plotly displays categorical x-axis in order of first appearance)
    chart_df = chart_df.sort_values('Year')

    # Create chart using px.line matching existing pattern
    fig = px.line(
        chart_df,
        x='Year',
        y='Pass_Rate',
        color='School',
        title=f'{metric_name} Pass Rate Trends',
        markers=True
    )

    # Apply styling to match app
    fig.update_layout(
        yaxis_range=[0, 100],
        yaxis_title='Pass Rate (%)',
        xaxis_title='School Year',
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        height=400
    )

    # Custom line styling
    for trace in fig.data:
        if 'Virginia State Average' in trace.name:
            # State average: dashed gray line
            trace.line.dash = 'dash'
            trace.line.color = '#7f7f7f'
            trace.line.width = 2
        elif trace.name == subject_school:
            # Subject school: thick solid blue
            trace.line.dash = 'solid'
            trace.line.color = '#1f77b4'
            trace.line.width = 3
        elif ' mi)' in trace.name:
            # Peer schools: dotted, alternating colors
            trace.line.dash = 'dot'
            trace.line.width = 2
            # Use different colors for peer schools
            if peer_schools and trace.name.startswith(peer_schools[0][0][:10]):
                trace.line.color = '#ff7f0e'  # Orange
            else:
                trace.line.color = '#2ca02c'  # Green

    return fig
