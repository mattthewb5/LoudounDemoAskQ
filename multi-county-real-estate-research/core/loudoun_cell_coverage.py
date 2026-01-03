"""
Cell Tower Coverage Analysis for Loudoun County

Provides functions to analyze cell tower proximity and coverage
for property locations. Designed for AI tool integration.

Data source: Loudoun County GIS enhanced with FCC carrier data.
Contains 110 towers with coordinates, heights, and attribution levels.
"""

import math
import os
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional


# Data paths - relative to this module's location
_MODULE_DIR = Path(__file__).parent.parent
_DATA_DIR = _MODULE_DIR / 'data' / 'loudoun'
_CELL_TOWERS_DIR = _DATA_DIR / 'Cell-Towers'
_CACHE_DIR = _DATA_DIR / 'cache'


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def load_cell_towers() -> pd.DataFrame:
    """
    Load cell tower data for Loudoun County with file-based caching.

    Data source: Loudoun County GIS enhanced with FCC carrier data.
    Contains 110 towers with coordinates, heights, and attribution levels.

    Returns:
        DataFrame with columns: tower_id, tower_name, structure_type, height_ft,
        latitude, longitude, entity_name, carrier_category, attribution_level, etc.
    """
    cache_file = _CACHE_DIR / 'cell_towers_cache.pkl'

    # Check cache (7 day TTL)
    if cache_file.exists():
        try:
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < 86400 * 7:  # 7 day cache
                return pd.read_pickle(cache_file)
        except Exception:
            pass  # Fall through to load from CSV

    # Load from CSV
    towers_path = _CELL_TOWERS_DIR / 'loudoun_towers_enhanced.csv'
    try:
        df = pd.read_csv(towers_path)
        # Validate required columns
        required_cols = ['latitude', 'longitude', 'tower_name', 'attribution_level']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return pd.DataFrame()
        # Clean coordinates
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])

        # Cache result
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_pickle(cache_file)
        except Exception:
            pass  # Caching is optional

        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_nearby_cell_towers(lat: float, lon: float, towers_df: pd.DataFrame, radius_miles: float = 2.0) -> pd.DataFrame:
    """
    Get cell towers within a specified radius of a property.

    Args:
        lat: Property latitude
        lon: Property longitude
        towers_df: DataFrame from load_cell_towers()
        radius_miles: Search radius in miles (default 2.0)

    Returns:
        DataFrame with nearby towers sorted by distance, with distance_mi column added.
    """
    if towers_df.empty:
        return pd.DataFrame()

    # Calculate distance to each tower
    towers_df = towers_df.copy()
    towers_df['distance_mi'] = towers_df.apply(
        lambda row: haversine_distance(lat, lon, row['latitude'], row['longitude']),
        axis=1
    )

    # Filter to radius and sort by distance
    nearby = towers_df[towers_df['distance_mi'] <= radius_miles].copy()
    nearby = nearby.sort_values('distance_mi')

    return nearby


def analyze_cell_tower_coverage(lat: float, lon: float, towers_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Analyze cell tower coverage for a property location.

    Args:
        lat: Property latitude
        lon: Property longitude
        towers_df: Optional pre-loaded tower DataFrame

    Returns:
        Dict with coverage analysis including:
        - available: bool
        - towers_within_1mi: int
        - towers_within_2mi: int
        - fcc_matched_count: int
        - local_only_count: int
        - carriers_detected: list of carrier names
        - closest_tower: dict with tower details
        - nearby_towers: DataFrame of towers within 2mi
    """
    if towers_df is None:
        towers_df = load_cell_towers()

    if towers_df.empty:
        return {'available': False, 'error': 'Cell tower data not available'}

    # Get nearby towers at different radii
    towers_1mi = get_nearby_cell_towers(lat, lon, towers_df, radius_miles=1.0)
    towers_2mi = get_nearby_cell_towers(lat, lon, towers_df, radius_miles=2.0)

    # Count by attribution level
    fcc_matched = len(towers_2mi[towers_2mi['attribution_level'].str.contains('FCC Matched', na=False)])
    local_only = len(towers_2mi[towers_2mi['attribution_level'] == 'Local Only'])

    # Get unique carriers
    carriers = towers_2mi[towers_2mi['carrier_category'].notna()]['carrier_category'].unique().tolist()

    # Find closest tower
    closest_tower = None
    if not towers_2mi.empty:
        closest = towers_2mi.iloc[0]
        # Handle missing tower name - use street address as fallback
        tower_name = closest.get('tower_name')
        if pd.isna(tower_name) or str(tower_name).strip() == '':
            address = closest.get('address', 'Unknown')
            tower_name = str(address).split(',')[0].strip() if address else 'Unknown'
        closest_tower = {
            'name': tower_name,
            'distance_mi': closest['distance_mi'],
            'height_ft': closest.get('height_ft'),
            'structure_type': closest.get('structure_type'),
            'entity_name': closest.get('entity_name'),
            'attribution_level': closest.get('attribution_level')
        }

    return {
        'available': True,
        'towers_within_1mi': len(towers_1mi),
        'towers_within_2mi': len(towers_2mi),
        'fcc_matched_count': fcc_matched,
        'local_only_count': local_only,
        'carriers_detected': carriers,
        'closest_tower': closest_tower,
        'nearby_towers': towers_2mi
    }


# Convenience function for AI tool use
def get_cell_coverage_summary(lat: float, lon: float) -> str:
    """
    Get a plain-text summary of cell tower coverage for a location.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Human-readable summary string
    """
    result = analyze_cell_tower_coverage(lat, lon)

    if not result.get('available'):
        return "Cell tower coverage data is not available for this location."

    summary_parts = []
    summary_parts.append(f"Cell tower coverage analysis:")
    summary_parts.append(f"- {result['towers_within_2mi']} towers within 2 miles")
    summary_parts.append(f"- {result['towers_within_1mi']} towers within 1 mile")

    if result['closest_tower']:
        ct = result['closest_tower']
        summary_parts.append(f"- Nearest tower: {ct['name']} at {ct['distance_mi']:.2f} miles")
        if ct.get('height_ft'):
            summary_parts.append(f"  Height: {ct['height_ft']:.0f} ft")

    if result['carriers_detected']:
        summary_parts.append(f"- Carriers detected: {', '.join(result['carriers_detected'])}")

    return "\n".join(summary_parts)
