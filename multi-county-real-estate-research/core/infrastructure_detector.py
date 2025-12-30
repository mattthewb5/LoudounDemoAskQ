"""
Infrastructure Construction Activity Detection Module

Detects and quantifies infrastructure-related construction activity from
Loudoun County building permits.

This module identifies:
- Data center construction
- Fiber optic installations
- Telecom tower/antenna work
- Telecom equipment installations

OUTPUT STYLE: Quantitative facts only (counts, distances, values)
NO quality claims like "excellent connectivity"

Author: Claude Code
Date: December 2024
"""

import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

import pandas as pd
import os


# Get the directory where this module is located
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_MODULE_DIR), 'data', 'loudoun')


def load_coordinate_corrections() -> Dict[str, tuple]:
    """
    Load manual coordinate corrections for known geocoding errors.

    Returns:
        dict: Address (uppercase) -> (corrected_lat, corrected_lon) mapping
    """
    corrections_path = os.path.join(_DATA_DIR, 'coordinate_corrections.csv')

    try:
        corrections_df = pd.read_csv(corrections_path)

        corrections = {}
        for _, row in corrections_df.iterrows():
            # Normalize address to uppercase for matching
            address = str(row['address']).strip().upper()
            corrections[address] = (float(row['corrected_lat']), float(row['corrected_lon']))

        return corrections
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Warning: Could not load coordinate corrections: {e}")
        return {}


def validate_data_center_coordinates(
    lat: float,
    lon: float,
    structure_type: str,
    address: str
) -> tuple:
    """
    Basic validation for data center coordinates.

    Flags obvious errors like downtown misplacement for large projects.

    Args:
        lat, lon: Coordinates to validate
        structure_type: Structure type from permit
        address: Address string for logging

    Returns:
        tuple: (is_valid: bool, warning_message: str or None)
    """
    # Check for null/invalid coordinates
    if pd.isna(lat) or pd.isna(lon):
        return (False, "Missing coordinates")

    if lat == 0 and lon == 0:
        return (False, "Null island coordinates (0,0)")

    # Check if coordinates are within Loudoun County bounds
    # Loudoun County approximate bounds: 38.8-39.3 N, -77.9--77.3 W
    if not (38.8 <= lat <= 39.3 and -77.9 <= lon <= -77.3):
        return (False, f"Coordinates outside Loudoun County bounds")

    # Flag if data center is geocoded to exact downtown Leesburg coordinates
    if structure_type == "Data Center":
        downtown_lat = 39.1157
        downtown_lon = -77.5636

        # If within 0.01 degrees (~0.7 miles) of downtown, flag as suspicious
        if abs(lat - downtown_lat) < 0.01 and abs(lon - downtown_lon) < 0.01:
            return (True, f"⚠️  Data center geocoded near downtown Leesburg - may be incorrect: {address}")

    return (True, None)


def load_infrastructure_keywords() -> Dict[str, List[str]]:
    """
    Load infrastructure keyword dictionary for permit detection.

    Based on Phase 1 analysis of 15,752 Loudoun County building permits.
    Keywords refined to minimize false positives (e.g., excluding 'switch',
    'cabinet' which match kitchen renovations).

    Returns:
        dict: Categories with keyword lists for pattern matching
    """
    return {
        'datacenter': [
            'data center',
            'datacenter',
            'data centre',
            'data hall',
            'server room',
            'colocation',
            'colo facility',
            'rack installation',
            'rack installations',
            'computer room',
        ],
        'fiber': [
            'fiber optic',
            'fiber cable',
            'fiber installation',
            'fiber conduit',
            'fiber line',
            'fiber run',
            'optical fiber',
            'fios',
            'hdpe conduit',  # Often paired with fiber
        ],
        'telecom_tower': [
            'antenna',
            'antennas',
            'cell tower',
            'cell site',
            'monopole',
            'lattice tower',
            'wireless tower',
            'telecommunications tower',
            'radio tower',
            '5g',
            'rru',
            'rrh',
            'rrus',
            'rrhs',
            't-mobile',
            'at&t',
            'verizon',
        ],
        'telecom_equipment': [
            'telecommunications',
            'telecom equipment',
            'communications cabling',
            'communication equipment',
            'telecom facility',
        ],
    }


def detect_infrastructure_type(description: str, structure_type: str) -> List[str]:
    """
    Detect infrastructure categories from permit description and structure type.

    Uses a two-tier approach:
    1. PRIMARY: Structure Type field (most reliable for data centers)
    2. SECONDARY: Keyword matching in description

    Args:
        description: Permit description text (can be None or empty)
        structure_type: Structure type field from permit (can be None or empty)

    Returns:
        list: Infrastructure categories detected (e.g., ['datacenter', 'fiber'])
              Empty list if no infrastructure found
    """
    categories = []

    # PRIMARY DETECTION: Structure Type field (most reliable)
    # Handle NaN/float values
    if structure_type is not None and not (isinstance(structure_type, float) and pd.isna(structure_type)):
        if str(structure_type).strip() == 'Data Center':
            categories.append('datacenter')

    # SECONDARY DETECTION: Keyword matching
    # Handle NaN/float values (pandas NaN is float type)
    if description is None or (isinstance(description, float) and pd.isna(description)):
        desc_lower = ''
    else:
        desc_lower = str(description).lower()

    if not desc_lower:
        return categories

    keywords = load_infrastructure_keywords()

    for category, keyword_list in keywords.items():
        # Skip datacenter keywords if already detected via Structure Type
        if category == 'datacenter' and 'datacenter' in categories:
            continue

        for keyword in keyword_list:
            if keyword.lower() in desc_lower:
                if category not in categories:
                    categories.append(category)
                break  # Found match for this category, move to next

    return categories


def tag_permit(permit_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tag a permit with infrastructure type boolean flags.

    Wraps detect_infrastructure_type() and returns a dict with boolean flags
    suitable for adding as new columns to the permit dataframe.

    Args:
        permit_row: Permit data (dict or Series) with 'Permit Description'
                    and 'Structure Type' keys

    Returns:
        dict: Boolean flags for each infrastructure type:
            - is_datacenter: Data center construction
            - is_fiber: Fiber optic installation
            - is_telecom_tower: Cell tower/antenna work
            - is_telecom_equipment: Telecom equipment installation
            - is_infrastructure: True if ANY of the above is True
            - infrastructure_categories: Comma-separated list of categories
    """
    # Extract fields (handle both dict and pandas Series)
    description = permit_row.get('Permit Description', '') or ''
    structure_type = permit_row.get('Structure Type', '') or ''

    # Get categories
    categories = detect_infrastructure_type(description, structure_type)

    return {
        'is_datacenter': 'datacenter' in categories,
        'is_fiber': 'fiber' in categories,
        'is_telecom_tower': 'telecom_tower' in categories,
        'is_telecom_equipment': 'telecom_equipment' in categories,
        'is_infrastructure': len(categories) > 0,
        'infrastructure_categories': ','.join(categories) if categories else '',
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Uses the Haversine formula for accuracy.

    Args:
        lat1, lon1: Coordinates of first point (degrees)
        lat2, lon2: Coordinates of second point (degrees)

    Returns:
        float: Distance in miles
    """
    # Earth's radius in miles
    R = 3958.8

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def find_nearby_infrastructure(
    lat: float,
    lon: float,
    permits_df: pd.DataFrame,
    radius_miles: float = 3.0,
    months_back: int = 12
) -> Dict[str, Any]:
    """
    Find infrastructure construction projects near a location.

    Args:
        lat: Target latitude
        lon: Target longitude
        permits_df: DataFrame with permit data (must have Latitude, Longitude,
                    Permit Issue Date, Permit Description, Structure Type,
                    Estimated Construction Cost, Address columns)
        radius_miles: Search radius in miles (default 3.0)
        months_back: How many months back to search (default 12)

    Returns:
        dict: Infrastructure construction activity summary with counts, lists,
              and nearest projects by type. All values are factual (counts,
              distances, dollar values) - no quality claims.
    """
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=months_back * 30)

    # Make a copy to avoid modifying original
    df = permits_df.copy()

    # Parse dates if needed
    if df['Permit Issue Date'].dtype == 'object':
        df['Permit Issue Date'] = pd.to_datetime(df['Permit Issue Date'], errors='coerce')

    # Filter by date using .loc to avoid reindex issues
    df = df.loc[df['Permit Issue Date'] >= cutoff_date]

    # Filter rows with valid coordinates
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df.loc[(df['Latitude'] != 0) & (df['Longitude'] != 0)]

    if len(df) == 0:
        return _empty_infrastructure_result()

    # Load coordinate corrections for known geocoding errors
    corrections = load_coordinate_corrections()

    # Apply corrections where available
    def get_corrected_coords(row):
        """Get corrected coordinates if available, otherwise return original."""
        address_key = str(row.get('Address', '')).strip().upper()
        if address_key in corrections:
            return corrections[address_key]
        return (row['Latitude'], row['Longitude'])

    # Create corrected coordinate columns
    corrected = df.apply(lambda row: get_corrected_coords(row), axis=1)
    df['Corrected_Latitude'] = corrected.apply(lambda x: x[0])
    df['Corrected_Longitude'] = corrected.apply(lambda x: x[1])

    # Calculate distances using corrected coordinates
    df['distance_miles'] = df.apply(
        lambda row: haversine_distance(lat, lon, row['Corrected_Latitude'], row['Corrected_Longitude']),
        axis=1
    )

    # Filter by radius using .loc to avoid reindex issues
    df = df.loc[df['distance_miles'] <= radius_miles]

    if len(df) == 0:
        return _empty_infrastructure_result()

    # Tag permits with infrastructure types (only if not already tagged)
    if 'is_infrastructure' not in df.columns:
        tags = df.apply(lambda row: tag_permit(row.to_dict()), axis=1)
        tags_df = pd.DataFrame(tags.tolist())
        df = pd.concat([df.reset_index(drop=True), tags_df.reset_index(drop=True)], axis=1)

    # Filter to only infrastructure permits using .loc to avoid reindex issues
    infra_df = df.loc[df['is_infrastructure'] == True].copy()

    if len(infra_df) == 0:
        return _empty_infrastructure_result()

    # Build result
    result = {
        'search_lat': lat,
        'search_lon': lon,
        'radius_miles': radius_miles,
        'months_back': months_back,
        'total_infrastructure_count': len(infra_df),
        'total_construction_value': _safe_sum(infra_df['Estimated Construction Cost']),
    }

    # Process each infrastructure type
    for infra_type in ['datacenter', 'fiber', 'telecom_tower', 'telecom_equipment']:
        flag_col = f'is_{infra_type}'
        type_df = infra_df.loc[infra_df[flag_col] == True].copy()

        count = len(type_df)
        result[f'{infra_type}_count'] = count

        if count > 0:
            # Sort by distance
            type_df = type_df.sort_values('distance_miles')

            # Get project list (top 10 nearest)
            projects = []
            for _, row in type_df.head(10).iterrows():
                projects.append({
                    'address': row.get('Address', 'Unknown'),
                    'distance_miles': round(row['distance_miles'], 2),
                    'date': str(row['Permit Issue Date'].date()) if pd.notna(row['Permit Issue Date']) else 'Unknown',
                    'value': _safe_int(row.get('Estimated Construction Cost', 0)),
                    'description': _truncate(row.get('Permit Description', ''), 100),
                })
            result[f'{infra_type}_projects'] = projects

            # Get nearest
            nearest = type_df.iloc[0]
            result[f'nearest_{infra_type}'] = {
                'address': nearest.get('Address', 'Unknown'),
                'distance_miles': round(nearest['distance_miles'], 2),
                'value': _safe_int(nearest.get('Estimated Construction Cost', 0)),
                'date': str(nearest['Permit Issue Date'].date()) if pd.notna(nearest['Permit Issue Date']) else 'Unknown',
            }

            # Total value for this type
            result[f'{infra_type}_total_value'] = _safe_sum(type_df['Estimated Construction Cost'])
        else:
            result[f'{infra_type}_projects'] = []
            result[f'nearest_{infra_type}'] = None
            result[f'{infra_type}_total_value'] = 0

    return result


def _empty_infrastructure_result() -> Dict[str, Any]:
    """Return empty result structure when no infrastructure found."""
    return {
        'total_infrastructure_count': 0,
        'total_construction_value': 0,
        'datacenter_count': 0,
        'datacenter_projects': [],
        'nearest_datacenter': None,
        'datacenter_total_value': 0,
        'fiber_count': 0,
        'fiber_projects': [],
        'nearest_fiber': None,
        'fiber_total_value': 0,
        'telecom_tower_count': 0,
        'telecom_tower_projects': [],
        'nearest_telecom_tower': None,
        'telecom_tower_total_value': 0,
        'telecom_equipment_count': 0,
        'telecom_equipment_projects': [],
        'nearest_telecom_equipment': None,
        'telecom_equipment_total_value': 0,
    }


def _safe_sum(series: pd.Series) -> int:
    """Safely sum a series, handling NaN values."""
    return int(pd.to_numeric(series, errors='coerce').fillna(0).sum())


def _safe_int(value: Any) -> int:
    """Safely convert value to int."""
    try:
        return int(float(value)) if pd.notna(value) else 0
    except (ValueError, TypeError):
        return 0


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max length with ellipsis."""
    if not text:
        return ''
    text = str(text)
    return text[:max_len] + '...' if len(text) > max_len else text


def calculate_infrastructure_trends(
    permits_df: pd.DataFrame,
    area_lat: float,
    area_lon: float,
    radius_miles: float = 3.0
) -> Dict[str, Any]:
    """
    Calculate year-over-year infrastructure construction trends.

    Compares current year vs previous year for each infrastructure type
    within a given radius of a location.

    Args:
        permits_df: DataFrame with permit data
        area_lat, area_lon: Center point coordinates
        radius_miles: Search radius (default 3 miles)

    Returns:
        dict: YoY trends by infrastructure type with counts and percentage changes
    """
    # Make a copy to avoid modifying original
    df = permits_df.copy()

    # Parse dates if needed
    if df['Permit Issue Date'].dtype == 'object':
        df['Permit Issue Date'] = pd.to_datetime(df['Permit Issue Date'], errors='coerce')

    # Filter rows with valid coordinates
    df = df.dropna(subset=['Latitude', 'Longitude'])
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]

    if len(df) == 0:
        return _empty_trends_result()

    # Load coordinate corrections
    corrections = load_coordinate_corrections()

    # Apply corrections
    def get_corrected_coords(row):
        address_key = str(row.get('Address', '')).strip().upper()
        if address_key in corrections:
            return corrections[address_key]
        return (row['Latitude'], row['Longitude'])

    corrected = df.apply(lambda row: get_corrected_coords(row), axis=1)
    df['Corrected_Latitude'] = corrected.apply(lambda x: x[0])
    df['Corrected_Longitude'] = corrected.apply(lambda x: x[1])

    # Calculate distances using corrected coordinates
    df['distance_miles'] = df.apply(
        lambda row: haversine_distance(area_lat, area_lon,
                                       row['Corrected_Latitude'],
                                       row['Corrected_Longitude']),
        axis=1
    )

    # Filter by radius
    nearby = df.loc[df['distance_miles'] <= radius_miles].copy()

    if len(nearby) == 0:
        return _empty_trends_result()

    # Tag permits with infrastructure types (only if not already tagged)
    if 'is_infrastructure' not in nearby.columns:
        tags = nearby.apply(lambda row: tag_permit(row.to_dict()), axis=1)
        tags_df = pd.DataFrame(tags.tolist())
        nearby = pd.concat([nearby.reset_index(drop=True), tags_df.reset_index(drop=True)], axis=1)

    # Extract year from permit date
    nearby['year'] = nearby['Permit Issue Date'].dt.year

    # Filter to infrastructure permits only using .loc to avoid reindex issues
    nearby = nearby.loc[nearby['is_infrastructure'] == True]

    if len(nearby) == 0:
        return _empty_trends_result()

    # Get unique years and determine comparison years
    available_years = sorted(nearby['year'].dropna().unique())

    # Use most recent two years for comparison
    if len(available_years) >= 2:
        current_year = int(available_years[-1])
        previous_year = int(available_years[-2])
    elif len(available_years) == 1:
        current_year = int(available_years[0])
        previous_year = current_year - 1
    else:
        return _empty_trends_result()

    # Split by year using .loc to avoid reindex issues
    df_current = nearby.loc[nearby['year'] == current_year]
    df_previous = nearby.loc[nearby['year'] == previous_year]

    # Calculate counts and trends for each type
    results = {
        'current_year': current_year,
        'previous_year': previous_year,
        'radius_miles': radius_miles,
    }

    for infra_type in ['datacenter', 'fiber', 'telecom_tower', 'telecom_equipment']:
        flag_col = f'is_{infra_type}'

        count_current = len(df_current.loc[df_current[flag_col] == True])
        count_previous = len(df_previous.loc[df_previous[flag_col] == True])

        results[f'{infra_type}_{current_year}'] = count_current
        results[f'{infra_type}_{previous_year}'] = count_previous
        results[f'{infra_type}_trend'] = _calculate_trend(count_current, count_previous)

    # Calculate total infrastructure
    total_current = len(df_current)
    total_previous = len(df_previous)

    results[f'total_{current_year}'] = total_current
    results[f'total_{previous_year}'] = total_previous
    results['total_trend'] = _calculate_trend(total_current, total_previous)

    return results


def _calculate_trend(current: int, previous: int) -> str:
    """Calculate trend string from two values."""
    if previous > 0:
        pct_change = ((current - previous) / previous) * 100
        if pct_change > 0:
            return f'+{pct_change:.0f}%'
        elif pct_change < 0:
            return f'{pct_change:.0f}%'
        else:
            return '0%'
    elif current > 0:
        return 'NEW'
    else:
        return 'N/A'


def _empty_trends_result() -> Dict[str, Any]:
    """Return empty trends result structure."""
    return {
        'current_year': None,
        'previous_year': None,
        'radius_miles': 0,
        'datacenter_trend': 'N/A',
        'fiber_trend': 'N/A',
        'telecom_tower_trend': 'N/A',
        'telecom_equipment_trend': 'N/A',
        'total_trend': 'N/A',
    }
