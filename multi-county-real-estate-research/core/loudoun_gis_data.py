"""
Loudoun County GIS Data - Cached Loading

Provides cached access to GIS shapefiles and data for location analysis.
Uses Streamlit's @cache_resource for persistent caching across reruns.

Data Sources:
- Road Centerline shapefile (Loudoun County GIS)
- Airport Impact Overlay Districts shapefile (Loudoun County Zoning)
- Major Power Lines GeoJSON (Loudoun County Utilities)

Multi-County Pattern:
When adding new counties, create get_cached_<county>_gis_data() functions
following this same pattern. Each county's data is cached independently.
"""

import json
import os
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Suppress geopandas datetime warnings
warnings.filterwarnings('ignore', category=UserWarning)

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    gpd = None

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# =============================================================================
# ROAD FILTERING PATTERNS (from location_quality_analyzer.py)
# =============================================================================

HIGHWAY_PATTERNS = [
    'LEESBURG PIKE',      # Route 7
    'HARRY BYRD',         # Route 7
    'SULLY RD',           # Route 28
    'SULLY ROAD',         # Route 28
    'DULLES ACCESS',      # Route 267
    'DULLES TOLL',        # Route 267
    'GREENWAY',           # Route 267
    'LEE JACKSON',        # Route 50
    'JOHN MOSBY',         # Route 50
    'JAMES MONROE',       # Route 15
    'KING ST',            # Route 15 in Leesburg
]

COLLECTOR_PATTERNS = [
    'LOUDOUN COUNTY',
    'WAXPOOL',
    'BELMONT RIDGE',
    'ASHBURN VILLAGE',
    'PACIFIC',
    'CLAIBORNE',
    'BRADDOCK',
    'STERLING',
    'BATTLEFIELD',
    'RIVER CREEK',
    'CROSSTRAIL',
    'SHREVEPORT',
    'OLD OX',
    'TALL CEDARS',
    'DULLES WEST',
    'RYAN',
    'SHELLHORN',
    'PROSPERITY',
    'EDWARDS FERRY',
]

COLLECTOR_ROAD_GROUPS = [
    ["RIVER CREEK PKWY", "EDWARDS FERRY RD", "EDWARDS FERRY RD NE", "CROSSTRAIL BLVD", "CROSSTRAIL BLVD SE"],
    ["LOUDOUN COUNTY PKWY", "RIVERSIDE PKWY"],
    ["BATTLEFIELD PKWY NE", "BATTLEFIELD PKWY SE"],
    ["N STERLING BLVD", "S STERLING BLVD", "STERLING RD"],
]


# =============================================================================
# DATA PATH RESOLUTION
# =============================================================================

def _get_loudoun_gis_path() -> Optional[str]:
    """
    Find the Loudoun County GIS data directory.

    Returns:
        Path to GIS directory or None if not found
    """
    possible_paths = [
        'data/loudoun/gis',
        'multi-county-real-estate-research/data/loudoun/gis',
        '/home/user/NewCo/multi-county-real-estate-research/data/loudoun/gis',
    ]

    # Also try relative to this module
    module_dir = Path(__file__).parent.parent
    possible_paths.insert(0, str(module_dir / 'data' / 'loudoun' / 'gis'))

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def _get_loudoun_utilities_path() -> Optional[str]:
    """
    Find the Loudoun County utilities data directory.

    Returns:
        Path to utilities directory or None if not found
    """
    possible_paths = [
        'data/loudoun/utilities',
        'multi-county-real-estate-research/data/loudoun/utilities',
        '/home/user/NewCo/multi-county-real-estate-research/data/loudoun/utilities',
    ]

    # Also try relative to this module
    module_dir = Path(__file__).parent.parent
    possible_paths.insert(0, str(module_dir / 'data' / 'loudoun' / 'utilities'))

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


# =============================================================================
# ROAD DATA LOADING
# =============================================================================

def _load_roads_internal() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """
    Load and process road data from shapefile.

    Returns:
        Tuple of (all_roads, highways, collectors) GeoDataFrames
        Returns (None, None, None) if loading fails
    """
    if not HAS_GEOPANDAS:
        print("Warning: geopandas not available for road loading")
        return None, None, None

    gis_path = _get_loudoun_gis_path()
    if not gis_path:
        print("Warning: GIS data path not found")
        return None, None, None

    roads_dir = os.path.join(gis_path, 'roads')
    if not os.path.exists(roads_dir):
        print(f"Warning: Roads directory not found: {roads_dir}")
        return None, None, None

    # Find shapefile
    roads_shp = None
    for f in os.listdir(roads_dir):
        if f.endswith('.shp'):
            roads_shp = os.path.join(roads_dir, f)
            break

    if not roads_shp:
        print(f"Warning: No shapefile found in {roads_dir}")
        return None, None, None

    try:
        print(f"Loading roads from: {roads_shp}")
        all_roads = gpd.read_file(roads_shp)

        # Convert to WGS84 (EPSG:4326) for lat/lon operations
        if all_roads.crs and all_roads.crs.to_epsg() != 4326:
            print(f"Converting roads from {all_roads.crs} to EPSG:4326...")
            all_roads = all_roads.to_crs('EPSG:4326')

        # Filter for highways
        highway_pattern = '|'.join(HIGHWAY_PATTERNS)
        highways = all_roads[
            all_roads['ST_FULLNAM'].str.contains(highway_pattern, case=False, na=False)
        ].copy()
        print(f"Found {len(highways)} highway segments")

        # Filter for collectors
        collector_pattern = '|'.join(COLLECTOR_PATTERNS)
        pattern_matches = all_roads['ST_FULLNAM'].str.contains(collector_pattern, case=False, na=False)

        all_group_names = [name for group in COLLECTOR_ROAD_GROUPS for name in group]
        exact_matches = all_roads['ST_FULLNAM'].isin(all_group_names)

        is_collector_class = all_roads['CE_RD_CLAS'] == 'COLLECTOR(6)'

        collectors = all_roads[(pattern_matches | exact_matches) & is_collector_class].copy()
        print(f"Found {len(collectors)} collector segments")

        return all_roads, highways, collectors

    except Exception as e:
        print(f"Error loading roads: {e}")
        return None, None, None


# =============================================================================
# AIOD DATA LOADING
# =============================================================================

def _load_aiod_internal() -> Optional[Any]:
    """
    Load AIOD zones from shapefile.

    Returns:
        AIOD GeoDataFrame or None if loading fails
    """
    if not HAS_GEOPANDAS:
        print("Warning: geopandas not available for AIOD loading")
        return None

    gis_path = _get_loudoun_gis_path()
    if not gis_path:
        print("Warning: GIS data path not found")
        return None

    aiod_dir = os.path.join(gis_path, 'aiod')
    if not os.path.exists(aiod_dir):
        print(f"Warning: AIOD directory not found: {aiod_dir}")
        return None

    # Find shapefile
    aiod_shp = None
    for f in os.listdir(aiod_dir):
        if f.endswith('.shp'):
            aiod_shp = os.path.join(aiod_dir, f)
            break

    if not aiod_shp:
        print(f"Warning: No shapefile found in {aiod_dir}")
        return None

    try:
        print(f"Loading AIOD zones from: {aiod_shp}")
        aiod_zones = gpd.read_file(aiod_shp)

        # Convert to WGS84
        if aiod_zones.crs and aiod_zones.crs.to_epsg() != 4326:
            print(f"Converting AIOD from {aiod_zones.crs} to EPSG:4326...")
            aiod_zones = aiod_zones.to_crs('EPSG:4326')

        print(f"Found {len(aiod_zones)} AIOD zones")
        return aiod_zones

    except Exception as e:
        print(f"Error loading AIOD: {e}")
        return None


# =============================================================================
# POWER LINES DATA LOADING
# =============================================================================

def _load_power_lines_internal() -> List[Dict]:
    """
    Load power lines from GeoJSON file.

    Returns:
        List of power line dicts with coordinates and properties
    """
    utilities_path = _get_loudoun_utilities_path()
    if not utilities_path:
        print("Warning: Utilities data path not found")
        return []

    geojson_path = os.path.join(utilities_path, 'Major_Power_Lines.geojson')
    if not os.path.exists(geojson_path):
        print(f"Warning: Power lines file not found: {geojson_path}")
        return []

    try:
        print(f"Loading power lines from: {geojson_path}")
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        power_lines = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})

            if geom.get('type') != 'LineString':
                continue

            power_lines.append({
                'id': props.get('OBJECTID'),
                'voltage': props.get('MA_VOLTAGE', 0),
                'status': props.get('MA_STATUS', 'Unknown'),
                'voltage_class': props.get('MA_CLASS', ''),
                'updated': props.get('MA_UPD_DATE', ''),
                'coordinates': geom.get('coordinates', [])
            })

        print(f"Loaded {len(power_lines)} power lines")
        return power_lines

    except Exception as e:
        print(f"Error loading power lines: {e}")
        return []


# =============================================================================
# CACHED DATA ACCESS FUNCTIONS
# =============================================================================

if HAS_STREAMLIT:
    @st.cache_resource
    def get_cached_loudoun_roads() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
        """
        Get cached Loudoun County road data.

        Uses Streamlit's @cache_resource for persistent caching.
        First call loads from shapefile (~3-5 seconds).
        Subsequent calls return cached data instantly.

        Returns:
            Tuple of (all_roads, highways, collectors) GeoDataFrames
        """
        print("Loading Loudoun County road data (shapefile + CRS transform)...")
        result = _load_roads_internal()
        print("✓ Road data loaded and cached")
        return result

    @st.cache_resource
    def get_cached_loudoun_aiod() -> Optional[Any]:
        """
        Get cached Loudoun County AIOD zone data.

        Uses Streamlit's @cache_resource for persistent caching.
        First call loads from shapefile (~1-2 seconds).
        Subsequent calls return cached data instantly.

        Returns:
            AIOD GeoDataFrame
        """
        print("Loading Loudoun County AIOD zones (shapefile + CRS transform)...")
        result = _load_aiod_internal()
        print("✓ AIOD data loaded and cached")
        return result

    @st.cache_resource
    def get_cached_loudoun_power_lines() -> List[Dict]:
        """
        Get cached Loudoun County power line data.

        Uses Streamlit's @cache_resource for persistent caching.
        First call loads from GeoJSON (~0.2 seconds).
        Subsequent calls return cached data instantly.

        Returns:
            List of power line dicts
        """
        print("Loading Loudoun County power lines (GeoJSON)...")
        result = _load_power_lines_internal()
        print("✓ Power line data loaded and cached")
        return result

else:
    # Non-Streamlit fallback - simple module-level caching
    _cached_roads = None
    _cached_aiod = None
    _cached_power_lines = None

    def get_cached_loudoun_roads() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
        """Get cached road data (non-Streamlit fallback)."""
        global _cached_roads
        if _cached_roads is None:
            print("Loading Loudoun County road data...")
            _cached_roads = _load_roads_internal()
            print("✓ Road data loaded")
        return _cached_roads

    def get_cached_loudoun_aiod() -> Optional[Any]:
        """Get cached AIOD data (non-Streamlit fallback)."""
        global _cached_aiod
        if _cached_aiod is None:
            print("Loading Loudoun County AIOD zones...")
            _cached_aiod = _load_aiod_internal()
            print("✓ AIOD data loaded")
        return _cached_aiod

    def get_cached_loudoun_power_lines() -> List[Dict]:
        """Get cached power line data (non-Streamlit fallback)."""
        global _cached_power_lines
        if _cached_power_lines is None:
            print("Loading Loudoun County power lines...")
            _cached_power_lines = _load_power_lines_internal()
            print("✓ Power line data loaded")
        return _cached_power_lines


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_all_loudoun_gis_data() -> Dict[str, Any]:
    """
    Load all Loudoun County GIS data at once.

    Useful for pre-loading all data at app startup.

    Returns:
        Dict with keys: 'all_roads', 'highways', 'collectors', 'aiod_zones', 'power_lines'
    """
    all_roads, highways, collectors = get_cached_loudoun_roads()
    aiod_zones = get_cached_loudoun_aiod()
    power_lines = get_cached_loudoun_power_lines()

    return {
        'all_roads': all_roads,
        'highways': highways,
        'collectors': collectors,
        'aiod_zones': aiod_zones,
        'power_lines': power_lines,
    }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    import time

    print("=" * 60)
    print("LOUDOUN GIS DATA CACHING TEST")
    print("=" * 60)

    # Test 1: First load (cold)
    print("\n1. First load (cold)...")
    start = time.time()
    all_roads, highways, collectors = get_cached_loudoun_roads()
    roads_time = time.time() - start

    start = time.time()
    aiod_zones = get_cached_loudoun_aiod()
    aiod_time = time.time() - start

    start = time.time()
    power_lines = get_cached_loudoun_power_lines()
    power_time = time.time() - start

    print(f"\n   Roads: {roads_time:.2f}s")
    print(f"   AIOD: {aiod_time:.2f}s")
    print(f"   Power lines: {power_time:.2f}s")
    print(f"   Total: {roads_time + aiod_time + power_time:.2f}s")

    if highways is not None:
        print(f"\n   Highway segments: {len(highways)}")
    if collectors is not None:
        print(f"   Collector segments: {len(collectors)}")
    if aiod_zones is not None:
        print(f"   AIOD zones: {len(aiod_zones)}")
    print(f"   Power lines: {len(power_lines)}")

    # Test 2: Second load (cached - will only work in Streamlit context)
    print("\n2. Second load (should be cached if in Streamlit)...")
    start = time.time()
    all_roads2, highways2, collectors2 = get_cached_loudoun_roads()
    roads_time2 = time.time() - start

    start = time.time()
    aiod_zones2 = get_cached_loudoun_aiod()
    aiod_time2 = time.time() - start

    start = time.time()
    power_lines2 = get_cached_loudoun_power_lines()
    power_time2 = time.time() - start

    print(f"\n   Roads: {roads_time2:.4f}s")
    print(f"   AIOD: {aiod_time2:.4f}s")
    print(f"   Power lines: {power_time2:.4f}s")
    print(f"   Total: {roads_time2 + aiod_time2 + power_time2:.4f}s")

    if roads_time2 < 0.01:
        print("\n   ✓ Cache hit confirmed (non-Streamlit fallback)")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
