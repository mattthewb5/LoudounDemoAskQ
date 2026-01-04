"""
School Assignment Lookup for Loudoun County

Provides functions to find assigned LCPS schools for a property location.
Uses official school zone boundary files from Loudoun County Public Schools.
Designed for AI tool integration.

Data source: Loudoun County Public Schools Zone Files (GeoJSON)
Zone files: data/loudoun/schools/{elementary,middle,high}_zones.geojson
"""

from pathlib import Path
from typing import Dict, Any, Optional

# Try to import geopandas - graceful fallback if unavailable
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    gpd = None
    Point = None


# Data paths
_MODULE_DIR = Path(__file__).parent.parent
_SCHOOLS_DIR = _MODULE_DIR / 'data' / 'loudoun' / 'schools'


# School code to name mapping for Loudoun County
SCHOOL_CODES = {
    # Elementary
    'ALD': 'Aldie Elementary', 'ALG': 'Algonkian Elementary', 'ARC': 'Arcola Elementary',
    'ASH': 'Ashburn Elementary', 'BAL': "Ball's Bluff Elementary", 'BAN': 'Banneker Elementary',
    'BST': 'Belmont Station Elementary', 'BUF': 'Buffalo Trail Elementary',
    'CAT': 'Catoctin Elementary', 'CCE': "Creighton's Corner Elementary",
    'CED': 'Cedar Lane Elementary', 'CRE': 'Cardinal Ridge Elementary',
    'CSP': 'Cool Spring Elementary', 'CTY': 'Countryside Elementary',
    'DIS': 'Discovery Elementary', 'DOM': 'Dominion Trail Elementary',
    'EME': 'Emerick Elementary', 'ETE': 'Elaine Thompson Elementary',
    'EVE': 'Evergreen Mill Elementary', 'FDE': 'Frederick Douglass Elementary',
    'FHR': 'Frances Hazel Reid Elementary', 'FOR': 'Forest Grove Elementary',
    'GPE': 'Goshen Post Elementary', 'GUI': 'Guilford Elementary',
    'HAM': 'Hamilton Elementary', 'HLS': 'Hillside Elementary',
    'HRZ': 'Horizon Elementary', 'HUT': 'Hutchison Farm Elementary',
    'KWC': 'Kenneth Culbert Elementary', 'LEE': 'Leesburg Elementary',
    'LEG': 'Legacy Elementary', 'LIB': 'Liberty Elementary',
    'LIN': 'Lincoln Elementary', 'LIT': 'Little River Elementary',
    'LOV': 'Lovettsville Elementary', 'LOW': 'Lowes Island Elementary',
    'LUC': 'Lucketts Elementary', 'MEA': 'Meadowland Elementary',
    'MIL': 'Mill Run Elementary', 'MSE': 'Moorefield Station Elementary',
    'MTE': "Madison's Trust Elementary", 'MTV': 'Mountain View Elementary',
    'NLE': 'Newton-Lee Elementary', 'PMK': 'Potowmack Elementary',
    'PNB': 'Pinebrook Elementary', 'RHL': 'Round Hill Elementary',
    'RLC': 'Rosa Lee Carter Elementary', 'RRD': 'Rolling Ridge Elementary',
    'SAN': 'Sanders Corner Elementary', 'SEL': 'Seldens Landing Elementary',
    'STE': 'Sterling Elementary', 'STU': 'Steuart Weller Elementary',
    'SUG': 'Sugarland Elementary', 'SUL': 'Sully Elementary',
    'SYC': 'Sycolin Creek Elementary', 'TOL': 'John Tolbert Elementary',
    'WAT': 'Waterford Elementary', 'WES': 'Waxpool Elementary',
    'HENHOV': 'Hovatter Elementary',
    # Middle
    'BAM': 'Brambleton Middle', 'BEM': 'Belmont Ridge Middle',
    'BRM': 'Blue Ridge Middle', 'ERM': 'Eagle Ridge Middle',
    'FWS': 'Farmwell Station Middle', 'HPM': 'Harper Park Middle',
    'HRM': 'Harmony Middle', 'JLS': 'J. Lupton Simpson Middle',
    'JML': 'J. Michael Lunsford Middle', 'MMS': 'Mercer Middle',
    'RBM': 'River Bend Middle', 'SHM': "Smart's Mill Middle",
    'SMM': 'Stone Hill Middle', 'SRM': 'Sterling Middle',
    'STM': 'Seneca Ridge Middle', 'TMS': 'Trailside Middle',
    'WMS': 'Willard Middle',
    # High
    'BRH': 'Briar Woods High', 'BWH': 'Broad Run High',
    'DMH': 'Dominion High', 'FHS': 'Freedom High',
    'HTH': 'Heritage High', 'IHS': 'Independence High',
    'JCH': 'John Champe High', 'LCH': 'Loudoun County High',
    'LRH': 'Lightridge High', 'LVH': 'Loudoun Valley High',
    'PFH': 'Park View High', 'PVH': 'Potomac Falls High',
    'RRH': 'Rock Ridge High', 'RVH': 'Riverside High',
    'SBH': 'Stone Bridge High', 'THS': 'Tuscarora High',
    'WHS': 'Woodgrove High'
}

# Zone file configuration
_ZONE_CONFIG = {
    'elementary': ('elementary_zones.geojson', 'ES_SCH_CODE'),
    'middle': ('middle_zones.geojson', 'MS_SCH_CODE'),
    'high': ('high_zones.geojson', 'HS_SCH_CODE')
}


def find_assigned_schools(lat: float, lon: float) -> Dict[str, Any]:
    """
    Find assigned schools for a location using LCPS zone boundary files.

    Uses official school zone GeoJSON files to determine which elementary,
    middle, and high school serve a given property location.

    Args:
        lat: Property latitude (WGS84)
        lon: Property longitude (WGS84)

    Returns:
        Dict with:
        - available: bool
        - elementary: dict with 'name' (or None if not found)
        - middle: dict with 'name' (or None if not found)
        - high: dict with 'name' (or None if not found)
        - summary: text summary
        - data_source: source attribution
    """
    if not GEOPANDAS_AVAILABLE:
        return {
            'available': False,
            'elementary': None,
            'middle': None,
            'high': None,
            'summary': 'School zone lookup unavailable (geopandas not installed).',
            'data_source': None,
            'error': 'geopandas not available'
        }

    point = Point(lon, lat)

    assignments = {
        'elementary': None,
        'middle': None,
        'high': None
    }

    for level, (filename, code_col) in _ZONE_CONFIG.items():
        filepath = _SCHOOLS_DIR / filename
        try:
            if not filepath.exists():
                continue

            zones_gdf = gpd.read_file(filepath)

            # Find zone containing the point
            for idx, zone in zones_gdf.iterrows():
                if zone.geometry.contains(point):
                    school_code = zone.get(code_col)
                    if school_code:
                        school_name = SCHOOL_CODES.get(school_code, f"School {school_code}")
                        assignments[level] = {'name': school_name, 'code': school_code}
                    break
        except Exception:
            continue

    # Build result
    available = any(v is not None for v in assignments.values())

    # Generate summary
    if available:
        parts = ["Assigned schools:"]
        if assignments['elementary']:
            parts.append(f"Elementary: {assignments['elementary']['name']}")
        if assignments['middle']:
            parts.append(f"Middle: {assignments['middle']['name']}")
        if assignments['high']:
            parts.append(f"High: {assignments['high']['name']}")
        summary = " | ".join(parts)
    else:
        summary = "Could not determine school assignments for this location."

    return {
        'available': available,
        'elementary': assignments['elementary'],
        'middle': assignments['middle'],
        'high': assignments['high'],
        'summary': summary,
        'data_source': 'Loudoun County Public Schools Zone Files'
    }


def get_school_assignment_summary(lat: float, lon: float) -> str:
    """
    Get a plain-text summary of school assignments for a location.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Human-readable summary string
    """
    result = find_assigned_schools(lat, lon)
    return result.get('summary', 'School assignment information unavailable.')


def get_assigned_school_names(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """
    Get just the school names for a location (simpler interface).

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Dict with 'elementary', 'middle', 'high' keys, values are school names or None
    """
    result = find_assigned_schools(lat, lon)

    return {
        'elementary': result['elementary']['name'] if result.get('elementary') else None,
        'middle': result['middle']['name'] if result.get('middle') else None,
        'high': result['high']['name'] if result.get('high') else None
    }
