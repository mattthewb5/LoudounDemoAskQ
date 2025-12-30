"""
Loudoun County Property Intelligence Platform
Professional real estate analysis with school data, location quality,
development pressure, and property valuation.

File: loudoun_streamlit_app.py
Location: multi-county-real-estate-research/
DO NOT CONFUSE WITH: NewCo/streamlit_app.py (Athens app - separate)
"""

import streamlit as st
import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import requests

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Loudoun County Property Intelligence",
    page_icon="🏘️",
    layout="wide"
)

# =============================================================================
# DARK MODE THEME SYSTEM
# =============================================================================

# Initialize theme state (default to light mode)
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

# CSS for dark and light modes
DARK_MODE_CSS = """
<style>
    /* Dark mode - base colors */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    /* Section headers - ensure visibility */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #fafafa !important;
    }

    /* Body text and descriptions */
    p, span, label,
    .stMarkdown p, .stMarkdown span,
    .stMarkdown li, .stCaption, .stText {
        color: #e0e0e0 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
    }

    /* Text inputs and number inputs */
    .stTextInput input, .stNumberInput input {
        background-color: #262730;
        color: #fafafa;
        border: 2px solid #888 !important;
        border-radius: 4px !important;
    }

    /* Expanders - header visibility */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        background-color: #262730;
        color: #fafafa !important;
    }
    .streamlit-expanderContent {
        background-color: #1a1d24;
    }

    /* Tables */
    .stTable, .stDataFrame {
        background-color: #1a1d24;
    }
    table {
        color: #fafafa;
    }
    th {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    td {
        background-color: #1a1d24 !important;
        color: #fafafa !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #fafafa !important;
    }
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }

    /* Markdown tables */
    .stMarkdown table {
        background-color: #1a1d24;
    }
    .stMarkdown th {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    .stMarkdown td {
        background-color: #1a1d24 !important;
        color: #e0e0e0 !important;
        border-color: #3a3a4a !important;
    }

    /* Cards and containers */
    .stAlert {
        background-color: #262730;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #6366f1;
    }

    /* Note: Plotly charts should use template="plotly_dark" in Python code
       CSS overrides can break chart rendering - removed */

    /* Folium maps - dark container */
    iframe {
        border: 1px solid #3a3a4a;
        border-radius: 4px;
    }

    /* Selectbox and multiselect - comprehensive targeting */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] [aria-selected="true"],
    .stMultiSelect > div > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #fafafa !important;
    }

    /* Selectbox selected value */
    [data-baseweb="select"] > div:first-child,
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        background-color: #262730 !important;
        color: #fafafa !important;
    }

    /* Selectbox dropdown menu */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div {
        background-color: #262730 !important;
    }
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #3a3a4a !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: #ffffff;
    }
    .stButton > button:hover {
        background-color: #5558e3;
        color: #ffffff;
    }

    /* Toggle label */
    [data-testid="stToggle"] label span {
        color: #fafafa !important;
    }

    /* Captions and small text */
    .stCaption, small, .caption {
        color: #b0b0b0 !important;
    }
</style>
"""

LIGHT_MODE_CSS = """
<style>
    /* Light mode - base colors */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
    }

    /* Section headers */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #1a1a1a !important;
    }

    /* Body text and descriptions */
    p, span, label,
    .stMarkdown p, .stMarkdown span,
    .stMarkdown li, .stCaption, .stText {
        color: #1a1a1a !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Text inputs and number inputs */
    .stTextInput input, .stNumberInput input {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 2px solid #666 !important;
        border-radius: 4px !important;
    }

    /* Expanders - header visibility */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        background-color: #f0f2f6;
        color: #1a1a1a !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff;
    }

    /* Tables */
    .stTable, .stDataFrame {
        background-color: #ffffff;
    }
    table {
        color: #1a1a1a;
    }
    th {
        background-color: #f0f2f6 !important;
        color: #1a1a1a !important;
    }
    td {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #1a1a1a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5a5a5a !important;
    }

    /* Markdown tables */
    .stMarkdown table {
        background-color: #ffffff;
    }
    .stMarkdown th {
        background-color: #f0f2f6 !important;
        color: #1a1a1a !important;
    }
    .stMarkdown td {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border-color: #e0e0e0 !important;
    }

    /* Cards and containers */
    .stAlert {
        background-color: #f0f2f6;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #6366f1;
    }

    /* Note: Plotly charts use default light template - no CSS override needed */

    /* Folium maps - light container */
    iframe {
        border: 1px solid #d0d0d0;
        border-radius: 4px;
    }

    /* Selectbox and multiselect - comprehensive targeting */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] [aria-selected="true"],
    .stMultiSelect > div > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Selectbox selected value */
    [data-baseweb="select"] > div:first-child,
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Selectbox dropdown menu */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #f0f2f6 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: #ffffff;
    }
    .stButton > button:hover {
        background-color: #5558e3;
        color: #ffffff;
    }

    /* Toggle label */
    [data-testid="stToggle"] label span {
        color: #1a1a1a !important;
    }

    /* Captions and small text */
    .stCaption, small, .caption {
        color: #5a5a5a !important;
    }
</style>
"""

# Apply theme CSS
if st.session_state['dark_mode']:
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)

# Core imports
from core.location_quality_analyzer import LocationQualityAnalyzer, get_cached_location_analyzer
from core.loudoun_zoning_analysis import analyze_property_zoning_loudoun
from core.loudoun_utilities_analysis import analyze_power_line_proximity, get_cached_power_line_analyzer
from core.loudoun_metro_analysis import analyze_metro_access
# from core.mls_sqft_lookup import get_mls_sqft  # DISABLED - not on this branch
from core.api_config import get_api_key
from core.loudoun_school_performance import (
    load_performance_data as load_performance_with_state_avg,
    load_school_coordinates,
    find_peer_schools,
    create_performance_chart,
    normalize_school_name,
    match_school_in_performance_data
)
from core.loudoun_places_analysis import analyze_neighborhood
from core.loudoun_traffic_volume import LoudounTrafficVolumeAnalyzer
from core.loudoun_narrative_generator import compile_narrative_data, generate_property_narrative

# Data handling
import pandas as pd

# Property valuation (with error handling for missing API keys)
VALUATION_AVAILABLE = False
ATTOM_CLIENT = None
try:
    from core.property_valuation_orchestrator import PropertyValuationOrchestrator
    from core.attom_client import ATTOMClient
    # Test if API keys are configured
    attom_key = get_api_key('ATTOM_API_KEY')
    if attom_key or get_api_key('RENTCAST_API_KEY'):
        VALUATION_AVAILABLE = True
    if attom_key:
        ATTOM_CLIENT = ATTOMClient(api_key=attom_key)
except Exception:
    pass

# Community lookup
try:
    from core.loudoun_community_lookup import create_property_community_context, CommunityLookup
    from core.community_spatial_lookup import lookup_community
    COMMUNITY_LOOKUP_AVAILABLE = True
    SPATIAL_LOOKUP_AVAILABLE = True
except Exception as e:
    COMMUNITY_LOOKUP_AVAILABLE = False
    SPATIAL_LOOKUP_AVAILABLE = False
    print(f"Community lookup import failed: {e}")

# Demographics (Census data)
DEMOGRAPHICS_AVAILABLE = False
try:
    from core.demographics_calculator import calculate_demographics
    from core.demographics_formatter import display_demographics_section
    DEMOGRAPHICS_AVAILABLE = True
except Exception as e:
    print(f"Demographics import failed: {e}")

# Economic Indicators
ECONOMIC_INDICATORS_AVAILABLE = False
try:
    from core.economic_indicators import (
        get_lfpr_data,
        get_industry_mix_data,
        fetch_bls_data,
        load_major_employers,
        get_employers_by_year,
        get_employer_trends
    )
    ECONOMIC_INDICATORS_AVAILABLE = True
except Exception as e:
    print(f"Economic indicators import failed: {e}")

# Google Maps Geocoding
GOOGLE_MAPS_KEY = None
try:
    GOOGLE_MAPS_KEY = get_api_key('GOOGLE_MAPS_API_KEY')
except Exception:
    pass

# Mapping imports
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# Charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# GIS for school zone lookups
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# Initialize community lookup for spatial integration
if COMMUNITY_LOOKUP_AVAILABLE:
    try:
        _COMMUNITY_LOOKUP_INSTANCE = CommunityLookup()
    except Exception as e:
        print(f"Failed to initialize CommunityLookup: {e}")
        _COMMUNITY_LOOKUP_INSTANCE = None
else:
    _COMMUNITY_LOOKUP_INSTANCE = None


# =============================================================================
# DATA PATHS
# =============================================================================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'loudoun')
SCHOOLS_DIR = os.path.join(DATA_DIR, 'schools')
PERMITS_DIR = os.path.join(DATA_DIR, 'building_permits')
GIS_DIR = os.path.join(DATA_DIR, 'gis')
CELL_TOWERS_DIR = os.path.join(DATA_DIR, 'Cell-Towers')
HEALTHCARE_DIR = os.path.join(DATA_DIR, 'healthcare')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    import math
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def format_sale_date(date_str: str) -> str:
    """Convert '2020-04-28' → 'Apr 28, 2020'"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str or "—"


def format_sale_price(price) -> str:
    """Convert 1299000 → '$1,299,000'"""
    if price is None:
        return "N/A"
    try:
        return f"${int(price):,}"
    except:
        return "N/A"


def clean_verification_code(code: str) -> str:
    """Convert '1:MARKET SALE' → 'Market Sale'"""
    try:
        if not code:
            return "—"
        if ':' in code:
            code = code.split(':', 1)[1]
        return code.strip().title()
    except:
        return code or "—"


def format_time_since_sale(date_str: str) -> str:
    """Convert date to human-readable 'X years ago' format"""
    try:
        sale_date = datetime.strptime(date_str, '%Y-%m-%d')
        days = (datetime.now() - sale_date).days

        years = days / 365.25
        if years >= 1:
            return f"{years:.1f} years ago"

        months = days / 30.44  # Average month length
        if months >= 1:
            return f"{int(months)} months ago"

        return f"{days} days ago"
    except:
        return "—"


@st.cache_data
def load_permits_data() -> pd.DataFrame:
    """Load and cache building permits data."""
    permits_path = os.path.join(PERMITS_DIR, 'loudoun_permits_with_infrastructure.csv')
    try:
        df = pd.read_csv(permits_path, encoding='latin-1')
        # Clean coordinates
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Error loading permits: {e}")
        return pd.DataFrame()


@st.cache_data
def load_school_performance() -> pd.DataFrame:
    """Load school performance data for Loudoun County."""
    perf_path = os.path.join(SCHOOLS_DIR, 'school_performance_trends.csv')
    try:
        df = pd.read_csv(perf_path)
        # Filter for Loudoun County
        loudoun = df[df['Division_Name'] == 'Loudoun County'].copy()
        return loudoun
    except Exception as e:
        st.error(f"Error loading school data: {e}")
        return pd.DataFrame()


@st.cache_data
def load_school_metadata() -> pd.DataFrame:
    """Load school metadata for Loudoun County."""
    meta_path = os.path.join(SCHOOLS_DIR, 'school_metadata.csv')
    try:
        df = pd.read_csv(meta_path)
        loudoun = df[df['Division_Name'] == 'Loudoun County'].copy()
        return loudoun
    except Exception as e:
        return pd.DataFrame()


@st.cache_data
def load_road_context() -> Dict:
    """Load road context data with travel times."""
    context_path = os.path.join(DATA_DIR, 'config', 'road_context.json')
    try:
        with open(context_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def normalize_road_name(name: str) -> str:
    """Normalize road names for matching with road_context.json keys.

    Handles variations like:
    - "TO SULLY RD NB (VA-28N)" -> "SULLY RD"
    - "TO SULLY RD NB" -> "SULLY RD"
    - "Leesburg Pike" -> "LEESBURG PIKE"
    - "SULLY ROAD" -> "SULLY RD"
    """
    if not name:
        return ""

    name = str(name).upper().strip()

    # Remove route numbers in parentheses (we'll handle separately)
    name = re.sub(r'\s*\([^)]*\)', '', name)

    # Remove "TO" prefix (appears in GIS data)
    name = re.sub(r'^TO\s+', '', name)

    # Remove directional suffixes (NB, SB, EB, WB)
    name = re.sub(r'\s+(NB|SB|EB|WB)$', '', name)

    # Normalize common variations
    name = re.sub(r'\bROAD\b', 'RD', name)
    name = re.sub(r'\bHIGHWAY\b', 'HWY', name)
    name = re.sub(r'\bPARKWAY\b', 'PKWY', name)
    name = re.sub(r'\bBOULEVARD\b', 'BLVD', name)

    return name.strip()


def extract_route_number(name: str) -> Optional[str]:
    """Extract route number from highway name if present.

    Examples:
    - "TO SULLY RD NB (VA-28N)" -> "Route 28"
    - "LEESBURG PIKE (US-7)" -> "Route 7"
    - "DULLES TOLL RD (VA-267)" -> "Route 267"

    Returns None if no route number found.
    """
    if not name:
        return None

    # Look for pattern like (VA-28N), (US-7), (VA-267), (SR-28)
    match = re.search(r'\((?:VA-|US-|SR-)?(\d+)(?:N|S|E|W)?\)', str(name))
    if match:
        return f"Route {match.group(1)}"
    return None


def expand_road_name(name: str) -> str:
    """Expand common road abbreviations to full words with proper casing.

    Examples:
    - "SULLY RD" -> "Sully Road"
    - "LEESBURG PIKE" -> "Leesburg Pike"
    - "LOUDOUN COUNTY PKWY" -> "Loudoun County Parkway"
    - "DULLES TOLL RD" -> "Dulles Toll Road"
    """
    if not name:
        return ""

    # Convert to title case first
    name = str(name).title()

    # Expand common abbreviations (must match whole words)
    expansions = {
        r'\bRd\b': 'Road',
        r'\bPkwy\b': 'Parkway',
        r'\bBlvd\b': 'Boulevard',
        r'\bHwy\b': 'Highway',
        r'\bSt\b': 'Street',
        r'\bAve\b': 'Avenue',
        r'\bDr\b': 'Drive',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPl\b': 'Place',
        r'\bTer\b': 'Terrace',
        r'\bCir\b': 'Circle',
    }

    for abbrev, full in expansions.items():
        name = re.sub(abbrev, full, name)

    return name


@st.cache_data
def load_cell_towers() -> pd.DataFrame:
    """
    Load and cache cell tower data for Loudoun County.

    Data source: Loudoun County GIS enhanced with FCC carrier data.
    Contains 110 towers with coordinates, heights, and attribution levels.

    Returns:
        DataFrame with columns: tower_id, tower_name, structure_type, height_ft,
        latitude, longitude, entity_name, carrier_category, attribution_level, etc.
    """
    towers_path = os.path.join(CELL_TOWERS_DIR, 'loudoun_towers_enhanced.csv')
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
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
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


def analyze_cell_tower_coverage(lat: float, lon: float, towers_df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Analyze cell tower coverage for a property location.

    Args:
        lat: Property latitude
        lon: Property longitude
        towers_df: Optional pre-loaded tower DataFrame

    Returns:
        Dict with coverage analysis including nearby towers, carrier info, and metrics.
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


@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_parks_data() -> Dict[str, Any]:
    """
    Load parks data from static JSON file.

    The parks.json file contains pre-fetched data from Google Places API
    covering parks and playgrounds across Loudoun County.

    Returns:
        dict: Parks data with 'available', 'parks' list, 'metadata', and 'total_parks'
    """
    try:
        parks_file = os.path.join(DATA_DIR, 'config', 'parks.json')

        if not os.path.exists(parks_file):
            return {"available": False, "error": "Parks data file not found"}

        with open(parks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "available": True,
            "parks": data.get("parks", []),
            "metadata": data.get("_metadata", {}),
            "total_parks": len(data.get("parks", []))
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_nearest_parks(lat: float, lon: float, parks_data: Dict[str, Any],
                      limit: int = 5, max_distance: float = 10.0) -> Dict[str, Any]:
    """
    Get nearest parks to a property location.

    Uses haversine formula to calculate straight-line distances from the property
    to all parks in the database, then returns the nearest ones.

    Args:
        lat: Property latitude
        lon: Property longitude
        parks_data: Output from load_parks_data()
        limit: Maximum parks to return (default 5)
        max_distance: Maximum distance in miles to consider (default 10)

    Returns:
        dict: {
            'available': bool,
            'nearest_park': dict or None (closest park with distance),
            'nearby_parks': list (up to 'limit' parks sorted by distance),
            'count_within_5mi': int (parks within 5 miles)
        }
    """
    if not parks_data.get("available"):
        return {"available": False}

    parks = parks_data.get("parks", [])

    if not parks:
        return {"available": False, "error": "No parks in database"}

    # Calculate distances to all parks
    results = []
    for park in parks:
        distance = haversine_distance(
            lat, lon,
            park['latitude'],
            park['longitude']
        )

        if distance <= max_distance:
            results.append({
                **park,
                'distance_miles': round(distance, 2)
            })

    # Sort by distance (nearest first)
    results.sort(key=lambda x: x['distance_miles'])

    # Count parks within 5 miles
    count_5mi = sum(1 for p in results if p['distance_miles'] <= 5.0)

    return {
        "available": True,
        "nearest_park": results[0] if results else None,
        "nearby_parks": results[:limit],
        "count_within_5mi": count_5mi,
        "total_found": len(results)
    }


@st.cache_data
def check_flood_zone(lat: float, lon: float) -> Dict[str, Any]:
    """
    Check if property is in a FEMA flood zone using Loudoun County GIS.

    Uses the official Loudoun County GIS FEMA Flood layer API to determine
    flood zone status. Returns plain English descriptions for homeowner clarity.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        Dictionary with flood zone status and details:
        - in_flood_zone: True/False/None (None on error)
        - zone_type: 'AE', 'A', 'FLOODWAY', or None
        - zone_description: Raw description from API
        - insurance_required: True/False/None
        - success: True/False
        - error: Error message if any
    """
    ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/FEMAFlood/MapServer/5/query"

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',  # WGS84
        'outFields': 'COL_DESCRIPTION_DETAIL',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if not features:
            # Not in flood zone - good news!
            return {
                'in_flood_zone': False,
                'zone_type': None,
                'zone_description': None,
                'insurance_required': False,
                'source': 'FEMA FIRM via Loudoun County GIS',
                'success': True,
                'error': None
            }

        # Parse zone type from response
        zone_raw = features[0]['attributes'].get('COL_DESCRIPTION_DETAIL', '')

        # Determine zone type for plain English display
        if 'FLOODWAY' in zone_raw.upper():
            zone_type = 'FLOODWAY'
        elif 'ZONE AE' in zone_raw.upper():
            zone_type = 'AE'
        elif 'ZONE A' in zone_raw.upper():
            zone_type = 'A'
        else:
            zone_type = zone_raw  # Fallback to raw value

        return {
            'in_flood_zone': True,
            'zone_type': zone_type,
            'zone_description': zone_raw,
            'insurance_required': True,
            'source': 'FEMA FIRM via Loudoun County GIS',
            'success': True,
            'error': None
        }

    except requests.Timeout:
        return {
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'source': None,
            'success': False,
            'error': 'Flood zone data temporarily unavailable (timeout)'
        }
    except requests.RequestException as e:
        return {
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'source': None,
            'success': False,
            'error': f'Flood zone service error: {str(e)}'
        }


def find_assigned_schools(lat: float, lon: float) -> Dict[str, str]:
    """Find assigned schools for a location using zone geojson files."""
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
        'RBM': 'River Bend Middle', 'SHM': 'Smart\'s Mill Middle',
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

    assignments = {
        'elementary': None,
        'middle': None,
        'high': None
    }

    if not GEOPANDAS_AVAILABLE:
        # Fallback: return placeholder
        return {
            'elementary': 'Evergreen Mill Elementary',
            'middle': 'J. Lupton Simpson Middle',
            'high': 'Tuscarora High'
        }

    point = Point(lon, lat)

    # Zone files with their school code columns
    zone_config = {
        'elementary': ('elementary_zones.geojson', 'ES_SCH_CODE'),
        'middle': ('middle_zones.geojson', 'MS_SCH_CODE'),
        'high': ('high_zones.geojson', 'HS_SCH_CODE')
    }

    for level, (filename, code_col) in zone_config.items():
        filepath = os.path.join(SCHOOLS_DIR, filename)
        try:
            zones_gdf = gpd.read_file(filepath)
            # Find zone containing the point
            for idx, zone in zones_gdf.iterrows():
                if zone.geometry.contains(point):
                    # Extract school code and map to name
                    school_code = zone.get(code_col)
                    if school_code:
                        school_name = SCHOOL_CODES.get(school_code, f"School {school_code}")
                        assignments[level] = school_name
                    break
        except Exception:
            continue

    # Fallbacks if zone lookup fails
    if not assignments['elementary']:
        assignments['elementary'] = 'Evergreen Mill Elementary'
    if not assignments['middle']:
        assignments['middle'] = 'J. Lupton Simpson Middle'
    if not assignments['high']:
        assignments['high'] = 'Tuscarora High'

    return assignments


def get_school_performance(school_name: str, performance_df: pd.DataFrame) -> Dict[str, Any]:
    """Get performance data for a specific school."""
    if performance_df.empty:
        return {}

    # Find matching school
    matches = performance_df[performance_df['School_Name'].str.contains(school_name.split()[0], case=False, na=False)]

    if matches.empty:
        return {}

    # Get most recent year
    latest = matches.sort_values('Year', ascending=False).iloc[0]

    return {
        'reading': latest.get('Reading_Pass_Rate', 0),
        'math': latest.get('Math_Pass_Rate', 0),
        'science': latest.get('Science_Pass_Rate', 0),
        'overall': latest.get('Overall_Pass_Rate', 0)
    }


# =============================================================================
# SECTION: SCHOOLS
# =============================================================================

def display_schools_section(lat: float, lon: float):
    """Display school assignments and performance."""
    st.markdown("## 🏫 School Assignments")

    # Get assigned schools
    assignments = find_assigned_schools(lat, lon)
    performance_df = load_school_performance()

    # Display assigned schools
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Elementary School", assignments['elementary'] or "N/A")
        if assignments['elementary']:
            perf = get_school_performance(assignments['elementary'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    with col2:
        st.metric("Middle School", assignments['middle'] or "N/A")
        if assignments['middle']:
            perf = get_school_performance(assignments['middle'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    with col3:
        st.metric("High School", assignments['high'] or "N/A")
        if assignments['high']:
            perf = get_school_performance(assignments['high'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    # Performance charts
    if PLOTLY_AVAILABLE and not performance_df.empty:
        st.markdown("### School Performance Trends")

        tab1, tab2 = st.tabs(["Reading Proficiency", "Math Proficiency"])

        with tab1:
            # Get trend data for assigned schools
            chart_data = []
            for level, school in assignments.items():
                if school:
                    # Use match function to get exact school name from performance data
                    matched_name = match_school_in_performance_data(school, performance_df)
                    if matched_name:
                        school_data = performance_df[
                            performance_df['School_Name'] == matched_name
                        ]
                        for _, row in school_data.iterrows():
                            chart_data.append({
                                'School': school,
                                'Year': row['Year'],
                                'Reading Pass Rate': row.get('Reading_Pass_Rate', 0)
                            })

            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                fig = px.line(chart_df, x='Year', y='Reading Pass Rate', color='School',
                             title='Reading Proficiency Trends',
                             markers=True)
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("School performance trend data not available for assigned schools.")

        with tab2:
            chart_data = []
            for level, school in assignments.items():
                if school:
                    # Use match function to get exact school name from performance data
                    matched_name = match_school_in_performance_data(school, performance_df)
                    if matched_name:
                        school_data = performance_df[
                            performance_df['School_Name'] == matched_name
                        ]
                        for _, row in school_data.iterrows():
                            chart_data.append({
                                'School': school,
                                'Year': row['Year'],
                                'Math Pass Rate': row.get('Math_Pass_Rate', 0)
                            })

            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                fig = px.line(chart_df, x='Year', y='Math Pass Rate', color='School',
                             title='Math Proficiency Trends',
                             markers=True)
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("School performance trend data not available for assigned schools.")

    # School Performance Comparison with State Average and Peer Schools
    if PLOTLY_AVAILABLE:
        with st.expander("📊 School Performance vs State & Peers", expanded=False):
            st.markdown("Compare assigned schools to Virginia state averages and nearest peer schools in Loudoun County.")

            try:
                # Load enhanced performance data with state averages
                perf_with_state_df = load_performance_with_state_avg()
                coords_df = load_school_coordinates()

                # Create school level tabs
                elem_tab, middle_tab, high_tab = st.tabs([
                    "📚 Elementary School",
                    "🎓 Middle School",
                    "🏫 High School"
                ])

                # Elementary School Tab
                with elem_tab:
                    if assignments.get('elementary'):
                        elem_school = assignments['elementary']
                        # Find 2 nearest peer elementary schools
                        elem_peers = find_peer_schools(
                            elem_school,
                            'Elem',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if elem_peers:
                            st.caption(f"Comparing to: {elem_peers[0][0]} ({elem_peers[0][1]:.1f} mi), {elem_peers[1][0]} ({elem_peers[1][1]:.1f} mi)" if len(elem_peers) >= 2 else f"Comparing to: {elem_peers[0][0]} ({elem_peers[0][1]:.1f} mi)")

                        # Subject tabs for elementary
                        e_math, e_read, e_hist, e_sci, e_overall = st.tabs([
                            "Math", "Reading", "History", "Science", "Overall"
                        ])

                        with e_math:
                            fig = create_performance_chart(elem_school, elem_peers, "Math", "Math_Pass_Rate", "Elem", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No math data available")

                        with e_read:
                            fig = create_performance_chart(elem_school, elem_peers, "Reading", "Reading_Pass_Rate", "Elem", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No reading data available")

                        with e_hist:
                            fig = create_performance_chart(elem_school, elem_peers, "History", "History_Pass_Rate", "Elem", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No history data available")

                        with e_sci:
                            fig = create_performance_chart(elem_school, elem_peers, "Science", "Science_Pass_Rate", "Elem", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No science data available")

                        with e_overall:
                            fig = create_performance_chart(elem_school, elem_peers, "Overall", "Overall_Pass_Rate", "Elem", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No overall data available")
                    else:
                        st.info("No elementary school assigned to this property")

                # Middle School Tab
                with middle_tab:
                    if assignments.get('middle'):
                        mid_school = assignments['middle']
                        mid_peers = find_peer_schools(
                            mid_school,
                            'Middle',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if mid_peers:
                            st.caption(f"Comparing to: {mid_peers[0][0]} ({mid_peers[0][1]:.1f} mi), {mid_peers[1][0]} ({mid_peers[1][1]:.1f} mi)" if len(mid_peers) >= 2 else f"Comparing to: {mid_peers[0][0]} ({mid_peers[0][1]:.1f} mi)")

                        m_math, m_read, m_hist, m_sci, m_overall = st.tabs([
                            "Math", "Reading", "History", "Science", "Overall"
                        ])

                        with m_math:
                            fig = create_performance_chart(mid_school, mid_peers, "Math", "Math_Pass_Rate", "Middle", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No math data available")

                        with m_read:
                            fig = create_performance_chart(mid_school, mid_peers, "Reading", "Reading_Pass_Rate", "Middle", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No reading data available")

                        with m_hist:
                            fig = create_performance_chart(mid_school, mid_peers, "History", "History_Pass_Rate", "Middle", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No history data available")

                        with m_sci:
                            fig = create_performance_chart(mid_school, mid_peers, "Science", "Science_Pass_Rate", "Middle", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No science data available")

                        with m_overall:
                            fig = create_performance_chart(mid_school, mid_peers, "Overall", "Overall_Pass_Rate", "Middle", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No overall data available")
                    else:
                        st.info("No middle school assigned to this property")

                # High School Tab
                with high_tab:
                    if assignments.get('high'):
                        high_school = assignments['high']
                        high_peers = find_peer_schools(
                            high_school,
                            'High',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if high_peers:
                            st.caption(f"Comparing to: {high_peers[0][0]} ({high_peers[0][1]:.1f} mi), {high_peers[1][0]} ({high_peers[1][1]:.1f} mi)" if len(high_peers) >= 2 else f"Comparing to: {high_peers[0][0]} ({high_peers[0][1]:.1f} mi)")

                        h_math, h_read, h_hist, h_sci, h_overall = st.tabs([
                            "Math", "Reading", "History", "Science", "Overall"
                        ])

                        with h_math:
                            fig = create_performance_chart(high_school, high_peers, "Math", "Math_Pass_Rate", "High", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No math data available")

                        with h_read:
                            fig = create_performance_chart(high_school, high_peers, "Reading", "Reading_Pass_Rate", "High", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No reading data available")

                        with h_hist:
                            fig = create_performance_chart(high_school, high_peers, "History", "History_Pass_Rate", "High", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No history data available")

                        with h_sci:
                            fig = create_performance_chart(high_school, high_peers, "Science", "Science_Pass_Rate", "High", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No science data available")

                        with h_overall:
                            fig = create_performance_chart(high_school, high_peers, "Overall", "Overall_Pass_Rate", "High", perf_with_state_df)
                            if fig:
                                st.plotly_chart(fig, width='stretch')
                            else:
                                st.info("No overall data available")
                    else:
                        st.info("No high school assigned to this property")

            except Exception as e:
                st.error(f"Error loading school comparison data: {str(e)}")

    st.markdown("---")


# =============================================================================
# SECTION: LOCATION QUALITY
# =============================================================================

def analyze_location_quality(lat: float, lon: float, address: str) -> Dict[str, Any]:
    """Analyze location quality using GIS data (cached for performance)."""
    try:
        # Use cached analyzer for better performance across property analyses
        analyzer = get_cached_location_analyzer()
        return analyzer.analyze_location(lat, lon, address)
    except Exception as e:
        return {'error': str(e)}


def display_location_section(location_data: Dict[str, Any], power_lines: Dict[str, Any] = None, metro_data: Dict[str, Any] = None, flood_data: Dict[str, Any] = None, parks_data: Dict[str, Any] = None, lat: float = None, lon: float = None):
    """Display location quality summary including flood zone, parks, and other features."""
    st.markdown("## 📍 Location Quality")

    if power_lines is None:
        power_lines = {}
    if metro_data is None:
        metro_data = {}
    if flood_data is None:
        flood_data = {}
    if parks_data is None:
        parks_data = {}

    # Initialize traffic analyzer for ADT data
    traffic_analyzer = None
    try:
        traffic_analyzer = LoudounTrafficVolumeAnalyzer()
    except Exception:
        pass  # Traffic data optional

    if 'error' in location_data:
        st.warning(f"Location analysis unavailable: {location_data['error']}")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Key Location Features:**")

        highlights = []

        # Road classification
        road_class = location_data.get('road_classification', {})
        if isinstance(road_class, dict):
            classification = road_class.get('classification', 'Unknown')
            traffic = road_class.get('traffic_level', 'Unknown')
            highlights.append(f"🛣️ **Road Type:** {classification} ({traffic} traffic)")

        # Highway access with ADT
        hw = location_data.get('highway_proximity', {})
        hw_name = None
        hw_dist = 0
        hw_adt = None
        hw_vdot_route = None
        if isinstance(hw, dict) and hw.get('nearest_highway'):
            hw_name = hw.get('nearest_highway', 'Unknown')
            hw_dist = hw.get('distance_miles', 0)
            hw_level = hw.get('proximity_level', '')
            # Color indicator based on proximity
            if hw_dist < 0.5:
                hw_icon = "🔴"  # Very close - noise concern
            elif hw_dist < 1.0:
                hw_icon = "🟡"  # Close
            else:
                hw_icon = "🟢"  # Good distance

            # Get ADT from traffic analyzer
            if traffic_analyzer and lat and lon:
                hw_traffic = traffic_analyzer.get_traffic_volume(hw_name, lat, lon)
                if hw_traffic:
                    hw_adt = hw_traffic.get('adt')
                    hw_vdot_route = hw_traffic.get('vdot_route')

            # Build display string with optional ADT
            hw_display = f"🚗 **Highway Access:** {hw_icon} {hw_name} ({hw_dist:.1f} mi)"
            if hw_adt:
                hw_display += f" • {traffic_analyzer.format_adt(hw_adt)}"
            highlights.append(hw_display)

        # Collector Roads (major local roads) with ADT
        coll = location_data.get('collector_proximity', {})
        coll_name = None
        coll_dist = 0
        coll_adt = None
        coll_vdot_route = None
        if isinstance(coll, dict) and coll.get('nearest_collector'):
            coll_name = coll.get('nearest_collector', 'Unknown')
            coll_dist = coll.get('distance_miles', 0)
            # Color indicator based on proximity (collectors are local, so different thresholds)
            if coll_dist < 0.3:
                coll_icon = "🔴"  # Very close - traffic concern
            elif coll_dist < 0.75:
                coll_icon = "🟡"  # Close
            else:
                coll_icon = "🟢"  # Good distance

            # Get ADT from traffic analyzer
            if traffic_analyzer and lat and lon:
                coll_traffic = traffic_analyzer.get_traffic_volume(coll_name, lat, lon)
                if coll_traffic:
                    coll_adt = coll_traffic.get('adt')
                    coll_vdot_route = coll_traffic.get('vdot_route')

            # Build display string with optional ADT
            coll_display = f"🛤️ **Major Road:** {coll_icon} {coll_name} ({coll_dist:.1f} mi)"
            if coll_adt:
                coll_display += f" • {traffic_analyzer.format_adt(coll_adt)}"
            highlights.append(coll_display)

        # Airport zone - Plain English display (lead with severity, not zone codes)
        aiod = location_data.get('aiod_status', {})
        if isinstance(aiod, dict):
            if aiod.get('in_aiod'):
                zone = aiod.get('zone', 'Unknown')
                airport = aiod.get('airport', 'Dulles')
                # Translate zone codes to plain English severity
                if 'Ldn 65' in zone or 'LDN65' in zone.upper():
                    severity = "High Aircraft Noise Zone"
                elif 'Ldn 60' in zone or 'LDN60' in zone.upper():
                    if 'Buffer' in zone or 'BUFFER' in zone.upper():
                        severity = "Aircraft Noise Buffer Zone"
                    else:
                        severity = "Moderate Aircraft Noise Zone"
                else:
                    severity = "Aircraft Noise Buffer Zone"
                highlights.append(f"🔔 **{severity}** - Disclosure required ({airport})")
            else:
                highlights.append("✅ **No Aircraft Noise Disclosure** - Outside disclosure zones")

            dulles_dist = aiod.get('distance_to_dulles_miles', 0)
            if dulles_dist:
                highlights.append(f"🛫 **Dulles Airport:** {dulles_dist:.1f} miles")

        # Flood Zone - Plain English display (lead with impact, not zone codes)
        if flood_data and flood_data.get('success'):
            if flood_data.get('in_flood_zone'):
                zone_type = flood_data.get('zone_type', 'Unknown')
                if zone_type == 'FLOODWAY':
                    highlights.append("⚠️ **Flood Insurance Required - Building Restricted** - Property in floodway")
                else:
                    highlights.append("🔔 **Flood Insurance Required** - Property in mapped flood risk area")
            else:
                highlights.append("✅ **No Flood Insurance Required** - Not in mapped flood zone")
        elif flood_data and not flood_data.get('success'):
            # API error - show neutral status
            highlights.append("⚪ **Flood Zone:** Data unavailable")

        # Parks proximity - show nearest park
        if parks_data and parks_data.get('available') and parks_data.get('nearest_park'):
            nearest = parks_data['nearest_park']
            dist = nearest['distance_miles']
            name = nearest['name']

            if dist < 0.5:
                highlights.append(f"🌳 **Parks:** {name} ({dist:.1f} mi) - Walking distance")
            elif dist <= 5.0:
                highlights.append(f"🌳 **Parks:** {name} ({dist:.1f} mi)")
            else:
                highlights.append(f"🌳 **Parks:** Nearest park {dist:.1f} miles away")
        elif parks_data and parks_data.get('available'):
            highlights.append("🌳 **Parks:** Limited park access (>10 mi)")

        # Metro Access
        if metro_data and metro_data.get('available'):
            prox = metro_data.get('proximity', {})
            tier = metro_data.get('tier', {})
            station = prox.get('nearest_station', 'Unknown')
            distance = prox.get('distance_miles', 0)
            tier_name = tier.get('tier', 'Unknown')
            tier_icon = tier.get('icon', '⚪')
            highlights.append(f"🚇 **Metro Access:** {tier_icon} {station} ({distance:.1f} mi) - {tier_name}")

        # Power Infrastructure - conditional display based on impact
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)
            nearest_built = power_lines.get('nearest_built_line')
            nearest_approved = power_lines.get('nearest_approved_line')

            # Determine which line is nearest (built or approved)
            nearest_line = None
            nearest_status = None
            if nearest_built and nearest_approved:
                if nearest_built['distance_miles'] <= nearest_approved['distance_miles']:
                    nearest_line = nearest_built
                    nearest_status = "Built"
                else:
                    nearest_line = nearest_approved
                    nearest_status = "Approved"
            elif nearest_built:
                nearest_line = nearest_built
                nearest_status = "Built"
            elif nearest_approved:
                nearest_line = nearest_approved
                nearest_status = "Approved"

            # For LOW/MODERATE impact (scores 1-3): Add to highlights list (inline)
            if impact_score <= 3:
                if impact_score == 3:
                    if nearest_line:
                        voltage = nearest_line['voltage']
                        dist = nearest_line['distance_miles']
                        highlights.append(f"⚡ **Power Lines:** 🟡 Moderate ({impact_score}/5) - {voltage}kV at {dist:.1f} mi")
                elif impact_score == 2:
                    if nearest_line:
                        voltage = nearest_line['voltage']
                        dist = nearest_line['distance_miles']
                        highlights.append(f"⚡ **Power Lines:** 🟢 Low Impact ({impact_score}/5) - {voltage}kV at {dist:.1f} mi")
                else:  # score 1
                    highlights.append("✅ **Power Lines:** No major lines within 1 mile")

                # Future line if different from nearest (still inline)
                if nearest_approved and nearest_status == "Built":
                    voltage = nearest_approved['voltage']
                    dist = nearest_approved['distance_miles']
                    highlights.append(f"🔮 **Future Power Line:** {voltage}kV approved at {dist:.1f} mi")

        # Render all highlights together
        for h in highlights:
            st.markdown(h)

        # Road Access Details expander (show if we have highway or collector data)
        show_road_expander = hw_name or coll_name
        if show_road_expander:
            with st.expander("ℹ️ Road Access Details"):
                # Load road context for travel times
                road_context = load_road_context()
                roads_data = road_context.get('roads', {})
                destinations = road_context.get('destinations', {})

                if hw_name:
                    # Look up highway in road context (try exact match, then normalized)
                    hw_context = roads_data.get(hw_name)
                    if not hw_context:
                        hw_context = roads_data.get(hw_name.upper())
                    if not hw_context:
                        normalized_hw = normalize_road_name(hw_name)
                        hw_context = roads_data.get(normalized_hw)
                    else:
                        normalized_hw = hw_name.upper()

                    # Display expanded road name if we matched via normalization
                    if hw_context:
                        display_hw_name = expand_road_name(normalized_hw)
                    else:
                        display_hw_name = hw_name

                    # Build final display with route number first if available
                    if hw_context and hw_context.get('route_number'):
                        final_display = f"{hw_context['route_number']} ({display_hw_name})"
                    elif hw_vdot_route and hw_vdot_route != hw_name:
                        final_display = f"{display_hw_name} ({hw_vdot_route})"
                    else:
                        final_display = display_hw_name

                    st.markdown(f"**Highway: {final_display}**")

                    # Add toll info if available
                    if hw_context:
                        if hw_context.get('toll'):
                            st.markdown("- Toll: **Yes** (paid)")
                        else:
                            st.markdown("- Toll: No")

                        # Travel times
                        travel_times = hw_context.get('travel_times', {})
                        if travel_times:
                            route_label = hw_context.get('route_number', 'this highway')
                            st.markdown(f"- **Travel Times** (via {route_label}):")
                            for dest_key, times in travel_times.items():
                                if 'error' not in times:
                                    dest_name = destinations.get(dest_key, {}).get('name', dest_key.title())
                                    rush = times.get('rush_min', 0)
                                    typical = times.get('offpeak_min', 0)
                                    min_time = min(rush, typical)
                                    max_time = max(rush, typical)
                                    st.markdown(f"  - {dest_name}: ~{min_time}-{max_time} min")

                if coll_name:
                    # Look up collector in road context (try exact match, then normalized)
                    coll_context = roads_data.get(coll_name)
                    if not coll_context:
                        coll_context = roads_data.get(coll_name.upper())
                    if not coll_context:
                        normalized_coll = normalize_road_name(coll_name)
                        coll_context = roads_data.get(normalized_coll)
                    else:
                        normalized_coll = coll_name.upper()

                    # Only show Major Road section if we have travel time data
                    if coll_context and coll_context.get('travel_times'):
                        if hw_name:
                            st.markdown("---")

                        # Display expanded road name if we matched via normalization
                        if coll_context:
                            display_coll_name = expand_road_name(normalized_coll)
                        else:
                            display_coll_name = coll_name

                        # Build final display with route number first if available
                        if coll_context and coll_context.get('route_number'):
                            final_display = f"{coll_context['route_number']} ({display_coll_name})"
                        elif coll_vdot_route and coll_vdot_route != coll_name:
                            final_display = f"{display_coll_name} ({coll_vdot_route})"
                        else:
                            final_display = display_coll_name

                        st.markdown(f"**Major Road: {final_display}**")

                        # Add travel times for collectors
                        travel_times = coll_context.get('travel_times', {})
                        if travel_times:
                            route_label = coll_context.get('route_number', 'this road')
                            st.markdown(f"- **Travel Times** (via {route_label}):")
                            for dest_key, times in travel_times.items():
                                if 'error' not in times:
                                    dest_name = destinations.get(dest_key, {}).get('name', dest_key.title())
                                    rush = times.get('rush_min', 0)
                                    typical = times.get('offpeak_min', 0)
                                    min_time = min(rush, typical)
                                    max_time = max(rush, typical)
                                    st.markdown(f"  - {dest_name}: ~{min_time}-{max_time} min")

                st.markdown("---")
                st.caption("Data: VDOT Traffic Volume, Google Distance Matrix")

        # Aircraft Noise Information (expandable) - Plain English display
        if isinstance(aiod, dict):
            with st.expander("✈️ Aircraft Noise Information"):
                if aiod.get('in_aiod'):
                    # Inside a noise disclosure zone
                    zone = aiod.get('zone', 'Unknown')
                    zone_code = aiod.get('zone_code', zone)
                    airport = aiod.get('airport', 'Dulles International')
                    construction_req = aiod.get('construction_requirements', 'None specified')

                    # Determine severity level for plain English display
                    if 'Ldn 65' in zone or 'LDN65' in str(zone_code).upper():
                        severity = "high aircraft noise area"
                        st.markdown(f"""
This property is in a **{severity}** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Frequent aircraft noise expected during arrivals and departures
- Seller must disclose noise impact to buyers
- New residential construction requires sound-reducing features

**Technical Reference:**
- Zone: Ldn 65+ (elevated noise contour)
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                    elif 'Ldn 60' in zone or 'LDN60' in str(zone_code).upper():
                        if 'Buffer' in zone or 'BUFFER' in str(zone_code).upper():
                            # Buffer zone
                            st.markdown(f"""
This property is in an **aircraft noise buffer zone** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Occasional overflight noise possible
- Seller must disclose proximity to airport
- No special construction requirements

**Technical Reference:**
- Zone: 1-Mile Buffer
- Building Requirements: None required
- Disclosure: Required at sale
""")
                        else:
                            # Moderate zone (Ldn 60-65)
                            st.markdown(f"""
This property is in a **moderate aircraft noise area** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Periodic aircraft noise during busy flight times
- Seller must disclose noise impact to buyers
- Sound-reducing construction recommended for new buildings

**Technical Reference:**
- Zone: Ldn 60-65 (moderate noise contour)
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                    else:
                        # Fallback for buffer or unknown zones
                        st.markdown(f"""
This property is in an **aircraft noise buffer zone** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Occasional overflight noise possible
- Seller must disclose proximity to airport
- No special construction requirements

**Technical Reference:**
- Zone: Buffer area
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                else:
                    # Outside all noise disclosure zones
                    dulles_dist = aiod.get('distance_to_dulles_miles', 0)

                    st.markdown(f"""
This property is **not in an aircraft noise disclosure zone**.
No noise-related disclosures required at sale.

**What This Means:**
- No aircraft noise restrictions or disclosures required
- No special construction requirements
- Full flexibility for property development

**Distance to Dulles Airport:** {dulles_dist:.1f} miles
""")

                st.caption("📊 Source: Loudoun County Airport Impact Overlay Districts (Jan 2023)")

        # Flood Zone Details (expandable) - Plain English display
        if flood_data and flood_data.get('success'):
            if flood_data.get('in_flood_zone'):
                zone_type = flood_data.get('zone_type', 'Unknown')

                if zone_type == 'FLOODWAY':
                    with st.expander("⚠️ Flood Insurance Required - Building Restricted"):
                        st.markdown("""
This property is in a regulatory floodway, which is reserved for the
passage of floodwaters. This designation has both financial and
development implications.

**Financial Impact:**
- Flood insurance required by mortgage lenders
- Costs vary based on property specifics and risk level

**Development Restrictions:**
- New dwellings/enclosed structures not permitted
- Cannot place fill material or obstruct flood flow
- Area must remain open for floodwater passage
- Only open-space uses allowed (yards, parking, gardens)

**What This Means:**
The floodway is the river channel plus adjacent land needed to carry
floodwaters. Strict building limitations apply to prevent obstructing
flood flow.

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                elif zone_type == 'AE':
                    with st.expander("🔔 Flood Insurance Required"):
                        st.markdown("""
This property is located in a mapped flood risk area where mortgage
lenders typically require flood insurance.

**What This Means:**
- Federally-backed mortgage lenders require flood insurance in this zone
- Insurance costs vary based on property elevation, value, and other factors
- 1% annual chance of flooding (26% over 30-year mortgage)

**Technical Details:**
- FEMA Zone: AE (detailed flood studies completed)
- Base flood elevations determined for this area

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                elif zone_type == 'A':
                    with st.expander("🔔 Flood Insurance Required"):
                        st.markdown("""
This property is located in a mapped flood risk area where mortgage
lenders typically require flood insurance.

**What This Means:**
- Federally-backed mortgage lenders require flood insurance in this zone
- Insurance costs vary based on property elevation, value, and other factors
- 1% annual chance of flooding (26% over 30-year mortgage)

**Technical Details:**
- FEMA Zone: A (approximate analysis)
- Base flood elevations not yet determined

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                else:
                    # Fallback for any other zone type
                    with st.expander("🔔 Flood Zone Information"):
                        st.markdown(f"""
This property is located in a mapped flood risk area ({zone_type}).
Mortgage lenders may require flood insurance.

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

            else:
                # Outside all flood zones
                with st.expander("✅ Flood Zone Information"):
                    st.markdown("""
This property is not located in a FEMA-designated flood risk area.
Mortgage lenders do not require flood insurance.

**What This Means:**
- Flood insurance optional but may be advisable
- Approximately 25% of flood claims come from outside mapped zones
- Consider coverage if near streams, ponds, or low-lying areas

💡 Learn more about optional flood insurance at [FloodSmart.gov](https://www.floodsmart.gov)
""")
                    st.caption("📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

        # Parks & Recreation (expandable)
        if parks_data and parks_data.get('available'):
            with st.expander("🌳 Parks & Recreation"):
                nearby = parks_data.get('nearby_parks', [])
                count_5mi = parks_data.get('count_within_5mi', 0)

                if nearby:
                    nearest = nearby[0]
                    dist = nearest['distance_miles']

                    # Summary statement based on distance
                    if dist < 0.5:
                        st.markdown(f"**{count_5mi} parks within 5 miles**, with {nearest['name']} "
                                  f"just {dist:.1f} miles away - **walking distance**.")
                    elif dist <= 2.0:
                        st.markdown(f"**{count_5mi} parks within 5 miles**, with {nearest['name']} "
                                  f"{dist:.1f} miles away - **short drive**.")
                    else:
                        st.markdown(f"**{count_5mi} parks within 5 miles**. Nearest is {nearest['name']} "
                                  f"at {dist:.1f} miles.")

                    st.markdown("")
                    st.markdown("**Nearest Parks:**")

                    # List up to 5 nearest parks
                    for park in nearby[:5]:
                        # Format park types for display
                        park_types = park.get('types', [])
                        type_labels = []
                        if 'park' in park_types:
                            type_labels.append('Park')
                        if 'playground' in park_types:
                            type_labels.append('Playground')
                        type_str = ", ".join(type_labels) if type_labels else "Recreation"

                        st.markdown(f"• **{park['name']}** - {park['distance_miles']:.1f} mi ({type_str})")

                    st.markdown("")
                    st.caption("📊 Source: Google Places (Dec 2025)")
                else:
                    st.markdown("No parks found within 10 miles of this property.")
                    st.markdown("")
                    st.caption("📊 Source: Google Places (Dec 2025)")

        # Metro Access Details (expandable)
        if metro_data and metro_data.get('available'):
            prox = metro_data.get('proximity', {})
            tier = metro_data.get('tier', {})
            drive_time = metro_data.get('drive_time', {})
            narrative = metro_data.get('narrative', '')

            with st.expander("🚇 Silver Line Metro Access Details"):
                # Metrics row
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Nearest Station", prox.get('nearest_station', 'N/A'))
                with m_col2:
                    st.metric("Distance", f"{prox.get('distance_miles', 0):.1f} mi")
                with m_col3:
                    st.metric("Drive Time", drive_time.get('display', 'N/A'))

                # Tier badge
                tier_icon = tier.get('icon', '⚪')
                tier_name = tier.get('tier', 'Unknown')
                tier_desc = tier.get('tier_description', '')
                st.markdown(f"**Accessibility:** {tier_icon} {tier_name} - {tier_desc}")

                # Narrative
                if narrative:
                    st.markdown(f"_{narrative}_")

                # All stations
                st.markdown("**All Silver Line Stations in Loudoun:**")
                for station in prox.get('all_stations', []):
                    st.markdown(f"• {station['name']}: {station['distance_miles']:.1f} miles")

                st.markdown("---")
                st.caption("The Silver Line connects Loudoun County to Tysons Corner, Arlington, and downtown Washington DC. Walk-to-Metro properties typically command 10-20% premium valuations.")

        # For HIGH impact (scores 4-5): Show separate prominent section AFTER highlights
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)

            if impact_score >= 4:
                nearest_built = power_lines.get('nearest_built_line')
                nearest_approved = power_lines.get('nearest_approved_line')
                lines_within_mile = power_lines.get('lines_within_one_mile', 0)

                # Determine nearest line
                nearest_line = None
                nearest_status = None
                if nearest_built and nearest_approved:
                    if nearest_built['distance_miles'] <= nearest_approved['distance_miles']:
                        nearest_line = nearest_built
                        nearest_status = "Built"
                    else:
                        nearest_line = nearest_approved
                        nearest_status = "Approved"
                elif nearest_built:
                    nearest_line = nearest_built
                    nearest_status = "Built"
                elif nearest_approved:
                    nearest_line = nearest_approved
                    nearest_status = "Approved"

                st.markdown("**⚡ Power Infrastructure/Major Power Lines:**")

                if impact_score == 5:
                    st.error(f"🔴 Very High Impact ({impact_score}/5)")
                else:
                    st.error(f"🔴 High Impact ({impact_score}/5)")

                if nearest_line:
                    voltage = nearest_line['voltage']
                    dist = nearest_line['distance_miles']
                    st.markdown(f"Nearest line: {voltage}kV at {dist:.2f} miles ({nearest_status})")

                if lines_within_mile > 0:
                    st.markdown(f"{lines_within_mile} line(s) within 1 mile")

                # Additional future line if exists and wasn't nearest
                if nearest_approved and nearest_status == "Built":
                    voltage = nearest_approved['voltage']
                    dist = nearest_approved['distance_miles']
                    st.markdown(f"🔮 Additional future line: {voltage}kV approved at {dist:.2f} mi")

    with col2:
        # Quality score (computed from factors)
        quality_score = 8.0  # Base score

        # Adjust based on road type
        road_class = location_data.get('road_classification', {})
        if isinstance(road_class, dict):
            traffic = road_class.get('traffic_level', '')
            if traffic == 'Very Low':
                quality_score += 1.0
            elif traffic == 'High':
                quality_score -= 1.0

        # Adjust for airport zone
        aiod = location_data.get('aiod_status', {})
        if isinstance(aiod, dict) and aiod.get('in_aiod'):
            quality_score -= 0.5

        # Adjust for power line proximity
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)
            if impact_score >= 5:
                quality_score -= 1.5  # Very High impact
            elif impact_score >= 4:
                quality_score -= 1.0  # High impact
            elif impact_score >= 3:
                quality_score -= 0.5  # Moderate impact

        quality_score = min(10.0, max(1.0, quality_score))

        st.metric(
            "Location Score",
            f"{quality_score:.1f}/10",
            help="Based on road type, traffic levels, airport proximity, and power infrastructure"
        )

    st.markdown("---")


# =============================================================================
# SECTION: NEIGHBORHOOD AMENITIES
# =============================================================================

def display_neighborhood_section(neighborhood_data: Dict[str, Any]):
    """Display neighborhood amenities analysis."""
    st.markdown("## 🏪 Discover Your Neighborhood")

    if not neighborhood_data or not neighborhood_data.get('available'):
        error = neighborhood_data.get('error', 'Unknown error') if neighborhood_data else 'Data not available'
        st.warning(f"Neighborhood analysis unavailable: {error}")
        return

    amenities = neighborhood_data.get('amenities', {})
    convenience = neighborhood_data.get('convenience', {})
    narrative = neighborhood_data.get('narrative', '')

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score = convenience.get('score', 0)
        rating = convenience.get('rating', 'Unknown')
        # Color indicator based on rating
        if rating == 'Excellent':
            color_indicator = "🟢"
        elif rating == 'Good':
            color_indicator = "🟡"
        elif rating == 'Fair':
            color_indicator = "🟠"
        else:
            color_indicator = "🔴"
        st.metric(
            "Convenience Score",
            f"{score}/10",
            help="Based on nearby dining, grocery, and shopping options"
        )
        st.markdown(f"{color_indicator} **{rating}**")

    with col2:
        dining = amenities.get('dining', {})
        dining_count = dining.get('count', 0)
        st.metric("Dining Nearby", f"{dining_count} places")

    with col3:
        grocery = amenities.get('grocery', {})
        grocery_nearest = grocery.get('nearest_distance')
        if grocery_nearest is not None:
            st.metric("Nearest Grocery", f"{grocery_nearest:.1f} mi")
        else:
            st.metric("Nearest Grocery", "N/A")

    with col4:
        walkable = amenities.get('summary', {}).get('walkable_count', 0)
        st.metric("Walkable Places", f"{walkable}", help="Places within 0.5 miles")

    # Category tabs
    dining_tab, grocery_tab, shopping_tab = st.tabs(["🍽️ Dining", "🛒 Grocery", "🛍️ Shopping"])

    with dining_tab:
        dining_places = amenities.get('dining', {}).get('places', [])
        if dining_places:
            for place in dining_places[:5]:  # Show top 5
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                price_str = "$" * place.get('price_level', 0) if place.get('price_level') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str} {price_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No restaurants found within 1 mile")

    with grocery_tab:
        grocery_places = amenities.get('grocery', {}).get('places', [])
        if grocery_places:
            for place in grocery_places[:5]:
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No grocery stores found within 1.5 miles")

    with shopping_tab:
        shopping_places = amenities.get('shopping', {}).get('places', [])
        if shopping_places:
            for place in shopping_places[:5]:
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No shopping centers found within 2 miles")

    # Expandable narrative
    if narrative:
        with st.expander("📝 Neighborhood Summary"):
            st.markdown(narrative)

            # Show highlights if available
            highlights = convenience.get('highlights', [])
            if highlights:
                st.markdown("**Key Highlights:**")
                for h in highlights:
                    st.markdown(f"• {h}")

    # Cache status (subtle footer)
    summary = amenities.get('summary', {})
    if summary.get('served_from_cache'):
        st.caption("📦 Data from cache (updated within 7 days)")
    else:
        api_calls = summary.get('api_calls_made', 0)
        if api_calls > 0:
            st.caption(f"🔄 Fresh data ({api_calls} API calls)")

    st.markdown("---")


# =============================================================================
# SECTION: COMMUNITY & HOA
# =============================================================================

def display_community_section(valuation_data: Dict[str, Any], lat: float = None, lon: float = None):
    """Display community/HOA information based on subdivision lookup and optional spatial coordinates."""
    if not COMMUNITY_LOOKUP_AVAILABLE:
        return

    # Get subdivision and hoa_fee from valuation data
    subdivision = valuation_data.get('subdivision') if valuation_data else None
    hoa_fee = valuation_data.get('hoa_fee') if valuation_data else None

    # Skip if no subdivision data available
    if not subdivision:
        return

    # 3-TIER COMMUNITY MATCHING STRATEGY
    community_ctx = None
    match_method = None

    # TIER 1 & 2: Try spatial lookup first (64 communities via GIS)
    if SPATIAL_LOOKUP_AVAILABLE and lat and lon and _COMMUNITY_LOOKUP_INSTANCE:
        try:
            spatial_result = lookup_community(lat, lon)

            if spatial_result:
                display_name = spatial_result.get('name')

                # Try to find rich data for this community
                community_key = _COMMUNITY_LOOKUP_INSTANCE.get_community_key_by_display_name(display_name)

                if community_key:
                    # TIER 1: Spatial + Rich Data (17 communities)
                    summary = _COMMUNITY_LOOKUP_INSTANCE.get_community_summary(community_key)
                    community_ctx = {
                        'community_found': True,
                        'community_key': community_key,
                        'display_name': summary['display_name'],
                        'location': summary.get('location'),
                        'hoa_website': summary.get('hoa_website'),
                        'management_company': summary.get('management_company'),
                        'monthly_fee': hoa_fee or summary.get('monthly_fee'),
                        'fee_source': 'API' if hoa_fee else summary.get('fee_source', 'Community Data'),
                        'fee_year': summary.get('fee_year'),
                        'fee_includes': summary.get('fee_includes', []),
                        'amenities': summary.get('amenities_list', []),
                        'amenities_detail': summary.get('amenities_detail', {}),
                        'total_homes': summary.get('total_homes'),
                        'total_acres': spatial_result.get('area_acres') or summary.get('total_acres'),
                        'gated': summary.get('gated', False),
                        'schools': summary.get('schools', {}),
                        'match_method': 'spatial',
                        'spatial_confidence': spatial_result.get('confidence', 'high'),
                        'data_quality': 'complete'
                    }
                else:
                    # TIER 2: Spatial Only (47 communities - waiting for VA data)
                    community_ctx = {
                        'community_found': True,
                        'display_name': display_name,
                        'total_acres': spatial_result.get('area_acres'),
                        'match_method': 'spatial',
                        'spatial_confidence': spatial_result.get('confidence', 'high'),
                        'data_quality': 'gis_only',
                        'pending_message': 'Community identified via GIS boundaries. Amenity details coming soon.'
                    }
        except Exception as e:
            print(f"Spatial lookup failed: {e}")
            # Continue to pattern fallback

    # TIER 3: Fall back to pattern matching (17 communities via fnmatch)
    if not community_ctx or not community_ctx.get('community_found'):
        pattern_ctx = create_property_community_context(subdivision, hoa_fee)
        if pattern_ctx.get('community_found'):
            community_ctx = pattern_ctx
            community_ctx['match_method'] = 'pattern'
            community_ctx['data_quality'] = 'complete'
        elif not community_ctx:
            # No match from any method
            community_ctx = {'community_found': False}

    # Section header
    st.markdown("## 🏘️ Community & Amenities")

    if community_ctx.get('community_found'):
        # Community found - display full details
        display_name = community_ctx.get('display_name', 'Unknown')
        monthly_fee = community_ctx.get('monthly_fee')
        fee_source = community_ctx.get('fee_source', '')
        hoa_website = community_ctx.get('hoa_website')
        amenities = community_ctx.get('amenities', [])
        is_gated = community_ctx.get('gated', False)

        # Community name header
        gated_badge = " 🔒" if is_gated else ""
        st.markdown(f"### {display_name}{gated_badge}")

        # Metrics row
        col1, col2, col3 = st.columns(3)

        with col1:
            if monthly_fee:
                st.metric("Monthly HOA Fee", f"${monthly_fee:,.0f}")
                if fee_source:
                    st.caption(f"Source: {fee_source}")
            else:
                st.metric("Monthly HOA Fee", "Contact HOA")

        with col2:
            total_homes = community_ctx.get('total_homes')
            if total_homes:
                st.metric("Community Size", f"{total_homes:,} homes")
            else:
                st.metric("Community Size", "—")

        with col3:
            if is_gated:
                st.metric("Access", "Gated Community")
            else:
                st.metric("Access", "Open Community")

        # Amenities
        if amenities:
            st.markdown("#### Amenities")
            # Display amenities in columns for better layout
            amenity_cols = st.columns(2)
            for i, amenity in enumerate(amenities):
                with amenity_cols[i % 2]:
                    st.markdown(f"• {amenity}")

        # HOA website link
        if hoa_website:
            st.markdown(f"🔗 [Visit HOA Website]({hoa_website})")

        # Fee notes if available
        fee_includes = community_ctx.get('fee_includes', [])
        if fee_includes:
            with st.expander("What's included in HOA fees"):
                for item in fee_includes:
                    st.markdown(f"• {item}")

    else:
        # Community not found - graceful fallback
        subdivision_display = community_ctx.get('display_name') or subdivision
        st.markdown(f"### {subdivision_display}")

        col1, col2 = st.columns(2)

        with col1:
            if hoa_fee:
                st.metric("Monthly HOA Fee", f"${hoa_fee:,.0f}")
                st.caption("Source: RentCast API")
            else:
                st.metric("Monthly HOA Fee", "Unknown")

        with col2:
            st.metric("Community Data", "Not Available")

        st.info("ℹ️ Community details not available for this subdivision. "
                "HOA fee shown is from property records.")

    st.markdown("---")


# =============================================================================
# SECTION: DEVELOPMENT & INFRASTRUCTURE
# =============================================================================

def display_cell_towers_section(lat: float, lon: float):
    """
    Display cell tower information for a property location.

    Shows nearby towers with basic infrastructure details.
    """
    st.markdown("## 📡 Cell Tower Coverage")

    # Get tower analysis
    tower_data = analyze_cell_tower_coverage(lat, lon)

    if not tower_data.get('available'):
        st.info("Cell tower data not available for this location.")
        return

    towers_2mi = tower_data.get('towers_within_2mi', 0)

    # Single metric - towers within 2 miles
    st.metric("Cell Towers Within 2 Miles", towers_2mi)

    # Structure type descriptions for clarity
    def get_structure_description(structure_type: str) -> str:
        descriptions = {
            'Trans-Mount': 'Trans-Mount (on power line tower)',
            'Monopole': 'Monopole (single-pole tower)',
            'Roof Top': 'Roof Top (building-mounted)',
            'Lattice': 'Lattice (steel framework tower)',
            'Water Tank': 'Water Tank (attached to tank)',
            'Guyed': 'Guyed (cable-supported tower)',
            'Silo': 'Silo (concealed in silo)',
        }
        return descriptions.get(structure_type, structure_type)

    # Closest tower info
    closest = tower_data.get('closest_tower')
    if closest:
        st.markdown("### Nearest Tower")
        dist_ft = closest['distance_mi'] * 5280
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{closest.get('name', 'Unknown')}**")
            st.markdown(f"Distance: **{closest['distance_mi']:.2f} mi** ({dist_ft:,.0f} ft)")
        with col2:
            if closest.get('height_ft'):
                st.markdown(f"Height: {closest['height_ft']:.0f} ft")
            if closest.get('structure_type'):
                st.markdown(f"Type: {get_structure_description(closest['structure_type'])}")

    # Nearby towers table
    nearby_towers = tower_data.get('nearby_towers')
    if nearby_towers is not None and not nearby_towers.empty:
        with st.expander(f"View All Nearby Towers ({len(nearby_towers)} within 2 mi)", expanded=False):
            # Prepare display dataframe - simplified columns
            display_df = nearby_towers[['tower_name', 'distance_mi', 'structure_type', 'height_ft', 'address']].copy()

            # Handle missing tower names - use street address as fallback
            display_df['tower_name'] = display_df.apply(
                lambda row: str(row['address']).split(',')[0].strip()
                if pd.isna(row['tower_name']) or str(row['tower_name']).strip() == ''
                else row['tower_name'],
                axis=1
            )

            display_df.columns = ['Tower Name', 'Distance (mi)', 'Type', 'Height (ft)', 'Address']
            display_df['Distance (mi)'] = display_df['Distance (mi)'].apply(lambda x: f"{x:.2f}")
            display_df['Height (ft)'] = display_df['Height (ft)'].apply(lambda x: f"{x:.0f}" if pd.notna(x) and x > 0 else "—")

            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )

    # Simple factual statement
    st.caption(f"📶 {towers_2mi} cell towers within 2 miles of this property.")


def analyze_development(lat: float, lon: float, radius_miles: float = 2.0) -> Dict[str, Any]:
    """Analyze development pressure and nearby permits."""
    permits_df = load_permits_data()

    if permits_df.empty:
        return {'error': 'Could not load permits data'}

    # Calculate distances
    permits_df['distance'] = permits_df.apply(
        lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']),
        axis=1
    )

    # Filter to radius
    nearby = permits_df[permits_df['distance'] <= radius_miles].copy()

    # Calculate metrics
    total_value = nearby['Estimated Construction Cost'].sum()
    datacenter_count = len(nearby[nearby['is_datacenter'] == True])
    fiber_count = len(nearby[nearby['is_fiber'] == True])
    infra_count = len(nearby[nearby['is_infrastructure'] == True])

    # Recent permits (last 6 months)
    try:
        nearby['issue_date'] = pd.to_datetime(nearby['Permit Issue Date'], errors='coerce')
        six_months_ago = datetime.now() - pd.Timedelta(days=180)
        recent = nearby[nearby['issue_date'] >= six_months_ago]
        recent_count = len(recent)
    except:
        recent_count = 0

    return {
        'nearby_permits': nearby,
        'total_permits': len(nearby),
        'total_value': total_value,
        'datacenter_count': datacenter_count,
        'fiber_count': fiber_count,
        'infrastructure_count': infra_count,
        'recent_count': recent_count
    }


def get_marker_radius(value: float, is_datacenter: bool) -> int:
    """Scale marker radius by permit value."""
    if is_datacenter or value >= 10_000_000:  # Data centers or >$10M
        return 12
    elif value >= 5_000_000:  # $5M-$10M
        return 9
    elif value >= 1_000_000:  # $1M-$5M
        return 6
    else:
        return 4  # Fallback


def create_development_map(lat: float, lon: float, nearby_permits: pd.DataFrame) -> folium.Map:
    """Create Folium map with development activity and overlay layers."""
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles=None)
    folium.TileLayer('cartodbpositron', control=False).add_to(m)

    # Property marker
    folium.Marker(
        [lat, lon],
        popup="<b>Your Property</b>",
        icon=folium.Icon(color='blue', icon='home', prefix='fa'),
        tooltip="Subject Property"
    ).add_to(m)

    # 2-mile radius circle
    folium.Circle(
        [lat, lon],
        radius=3218,  # 2 miles in meters
        color='#3388ff',
        fill=False,
        weight=2,
        opacity=0.5,
        tooltip="2-mile radius"
    ).add_to(m)

    # === PERMIT MARKERS (Option 3: Data centers + >$1M) ===
    permits_layer = folium.FeatureGroup(name='🏗️ Major Development (>$1M)')

    value_col = 'Estimated Construction Cost'
    df = nearby_permits.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)

    # Filter: data centers OR value >= $1M
    significant_permits = df[
        (df['is_datacenter'] == True) |
        (df[value_col] >= 1_000_000)
    ]

    for _, permit in significant_permits.iterrows():
        # Color by type
        if permit.get('is_datacenter'):
            color = 'red'
        elif permit.get('is_fiber'):
            color = 'orange'
        elif permit.get('is_infrastructure'):
            color = 'purple'
        else:
            color = 'green'

        cost = permit.get(value_col, 0)
        desc = str(permit.get('Permit Description', 'N/A'))[:100]

        # Value-scaled radius
        radius = get_marker_radius(cost, permit.get('is_datacenter', False))

        popup_html = f"""
        <b>{permit.get('Address', 'N/A')}</b><br>
        <b>Cost:</b> ${cost:,.0f}<br>
        <b>Type:</b> {permit.get('Permit Work Class', 'N/A')}<br>
        <b>Description:</b> {desc}...
        """

        folium.CircleMarker(
            location=[permit['Latitude'], permit['Longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(permits_layer)

    permits_layer.add_to(m)

    # === POWER LINES LAYER ===
    power_layer = folium.FeatureGroup(name='⚡ Power Lines')

    try:
        power_lines_path = os.path.join(DATA_DIR, 'utilities', 'Major_Power_Lines.geojson')
        with open(power_lines_path) as f:
            power_data = json.load(f)

        for feature in power_data['features']:
            coords = feature['geometry']['coordinates']
            # GeoJSON is [lon, lat], Folium wants [lat, lon]
            line_coords = [[c[1], c[0]] for c in coords]

            voltage = feature['properties'].get('MA_VOLTAGE', 'Unknown')

            folium.PolyLine(
                line_coords,
                weight=2,
                color='#FFA500',
                opacity=0.7,
                popup=f"Transmission Line: {voltage}kV",
            ).add_to(power_layer)
    except Exception as e:
        pass  # Silently skip if power lines data unavailable

    power_layer.add_to(m)

    # === METRO STATIONS LAYER ===
    metro_layer = folium.FeatureGroup(name='🚇 Metro Stations')

    metro_stations = [
        {"name": "Ashburn", "lat": 39.0057, "lon": -77.4910},
        {"name": "Loudoun Gateway", "lat": 38.9556, "lon": -77.4377},
        {"name": "Innovation Center", "lat": 38.9614, "lon": -77.4143},
        {"name": "Dulles Airport", "lat": 38.9531, "lon": -77.4483},
    ]

    for station in metro_stations:
        folium.Marker(
            [station['lat'], station['lon']],
            popup=f"🚇 {station['name']} Station (Silver Line)",
            icon=folium.Icon(color='darkblue', icon='train', prefix='fa'),
            tooltip=f"{station['name']} Metro"
        ).add_to(metro_layer)

    # Metro track line (simplified connection)
    track_coords = [[s['lat'], s['lon']] for s in metro_stations]
    folium.PolyLine(
        track_coords,
        weight=4,
        color='#003DA5',
        opacity=0.8,
        dash_array='10',
        popup='Silver Line Metro',
        tooltip='Silver Line'
    ).add_to(metro_layer)

    metro_layer.add_to(m)

    # === SCHOOLS LAYER ===
    school_layer = folium.FeatureGroup(name='🏫 Schools')

    try:
        schools_path = os.path.join(DATA_DIR, 'loudoun_school_coordinates.csv')
        schools_df = pd.read_csv(schools_path)

        for _, school in schools_df.iterrows():
            slat = school.get('Latitude', 0)
            slon = school.get('Longitude', 0)
            name = school.get('School_Name', 'School')
            school_type = school.get('School_Type', '')

            # Only show schools within 2.5 mile radius
            if haversine_distance(lat, lon, slat, slon) <= 2.5:
                # Color by school type, all use graduation-cap icon
                if 'Elem' in str(school_type):
                    icon_color = 'green'
                elif 'Middle' in str(school_type):
                    icon_color = 'orange'
                elif 'High' in str(school_type):
                    icon_color = 'red'
                else:
                    icon_color = 'gray'

                folium.Marker(
                    [slat, slon],
                    popup=f"🏫 {name}",
                    icon=folium.Icon(color=icon_color, icon='graduation-cap', prefix='fa'),
                    tooltip=name
                ).add_to(school_layer)
    except Exception as e:
        pass  # Silently skip if schools data unavailable

    school_layer.add_to(m)

    # === MASTER-PLANNED COMMUNITIES LAYER ===
    communities_layer = folium.FeatureGroup(name='🏘️ Master-Planned Communities')

    try:
        from core.loudoun_community_lookup import CommunityLookup
        lookup = CommunityLookup()

        for comm_key in lookup.list_communities():
            comm_data = lookup.get_community_by_key(comm_key)
            summary = lookup.get_community_summary(comm_key)

            if comm_data and 'latitude' in comm_data and 'longitude' in comm_data:
                clat = comm_data['latitude']
                clon = comm_data['longitude']
                name = summary.get('display_name', comm_key) if summary else comm_key
                homes = summary.get('total_homes', 0) if summary else 0
                gated = summary.get('gated', False) if summary else False
                hoa = summary.get('monthly_fee', 0) if summary else 0

                # Calculate distance to property
                dist = haversine_distance(lat, lon, clat, clon)

                # Build popup
                popup_parts = [f"<b>🏘️ {name}</b>"]
                if homes:
                    popup_parts.append(f"<br>{homes:,} homes")
                if gated:
                    popup_parts.append(" • Gated")
                if hoa:
                    popup_parts.append(f"<br>HOA: ${hoa:.0f}/mo")
                popup_parts.append(f"<br><i>{dist:.1f} mi from property</i>")
                popup_html = "".join(popup_parts)

                folium.Marker(
                    [clat, clon],
                    popup=folium.Popup(popup_html, max_width=200),
                    icon=folium.Icon(color='cadetblue', icon='home', prefix='fa'),
                    tooltip=f"{name} ({dist:.1f} mi)"
                ).add_to(communities_layer)
    except Exception:
        pass  # Silently skip if community data unavailable

    communities_layer.add_to(m)

    # === CELL TOWERS LAYER ===
    # Only show major towers (>= 150 ft) to reduce visual clutter
    towers_layer = folium.FeatureGroup(name='📡 Cell Towers')

    try:
        towers_df = load_cell_towers()
        if not towers_df.empty:
            for _, tower in towers_df.iterrows():
                tlat = tower.get('latitude', 0)
                tlon = tower.get('longitude', 0)
                height = tower.get('height_ft', 0)

                # Filter: only major towers (>= 150 ft) within 3 mile radius
                if height and height >= 150 and haversine_distance(lat, lon, tlat, tlon) <= 3.0:
                    tower_name = tower.get('tower_name', 'Unknown Tower')
                    structure = tower.get('structure_type', 'Unknown')
                    dist = haversine_distance(lat, lon, tlat, tlon)

                    # Build popup HTML - simplified
                    popup_parts = [f"<b>📡 {tower_name}</b>"]
                    popup_parts.append(f"<br>Type: {structure}")
                    popup_parts.append(f"<br>Height: {height:.0f} ft")
                    popup_parts.append(f"<br><b>{dist:.2f} mi from property</b>")
                    popup_html = "".join(popup_parts)

                    folium.Marker(
                        [tlat, tlon],
                        popup=folium.Popup(popup_html, max_width=250),
                        icon=folium.Icon(color='blue', icon='signal', prefix='fa'),
                        tooltip=f"{tower_name} ({dist:.2f} mi)"
                    ).add_to(towers_layer)
    except Exception:
        pass  # Silently skip if cell tower data unavailable

    towers_layer.add_to(m)

    # === HOSPITALS LAYER ===
    hospitals_layer = folium.FeatureGroup(name='🏥 Hospitals')

    # CMS-rated hospitals (hardcoded for reliability - these rarely change)
    cms_hospitals = [
        {
            "name": "Inova Loudoun Hospital",
            "lat": 39.073917871721612,
            "lon": -77.478042919767631,
            "cms_rating": 5,
            "phone": "(703) 858-6600",
            "address": "44045 Riverside Pkwy, Leesburg, VA 20176"
        },
        {
            "name": "StoneSprings Hospital Center",
            "lat": 38.9404382,
            "lon": -77.5424483,
            "cms_rating": 3,
            "phone": "(571) 349-4000",
            "address": "24440 Stone Springs Blvd, Dulles, VA 20166"
        }
    ]

    for hospital in cms_hospitals:
        stars = '⭐' * hospital['cms_rating']
        popup_html = f"""
        <b>🏥 {hospital['name']}</b><br>
        <b>CMS Rating:</b> {stars}<br>
        <b>Phone:</b> {hospital['phone']}<br>
        {hospital['address']}
        """
        folium.Marker(
            [hospital['lat'], hospital['lon']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color='orange', icon='plus-sign', prefix='glyphicon'),
            tooltip=f"{hospital['name']} ({stars})"
        ).add_to(hospitals_layer)

    hospitals_layer.add_to(m)

    # === LAYER CONTROL ===
    folium.LayerControl(collapsed=False).add_to(m)

    # === LEGEND ===
    legend_html = '''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
         background: white; padding: 10px; border-radius: 5px; border: 2px solid gray;
         font-size: 12px; font-family: Arial, sans-serif;">
        <b>Development Activity</b><br>
        <i style="background:red; width:12px; height:12px; border-radius:50%; display:inline-block;"></i> Data Center<br>
        <i style="background:orange; width:10px; height:10px; border-radius:50%; display:inline-block;"></i> Fiber/Telecom<br>
        <i style="background:purple; width:8px; height:8px; border-radius:50%; display:inline-block;"></i> Infrastructure<br>
        <i style="background:green; width:6px; height:6px; border-radius:50%; display:inline-block;"></i> Commercial >$1M<br>
        <hr style="margin: 5px 0;">
        <b>Schools</b><br>
        <i class="fa fa-graduation-cap" style="color:#72AF26;"></i> Elementary<br>
        <i class="fa fa-graduation-cap" style="color:#F69730;"></i> Middle<br>
        <i class="fa fa-graduation-cap" style="color:#D63E2A;"></i> High<br>
        <hr style="margin: 5px 0;">
        <i class="fa fa-home" style="color:#436978;"></i> Master-Planned Community<br>
        <span style="color:#FFA500;">━━</span> Power Lines<br>
        <span style="color:#003DA5;">┅┅</span> Silver Line Metro<br>
        <hr style="margin: 5px 0;">
        <i class="fa fa-signal" style="color:#0066CC;"></i> Cell Towers (150+ ft)<br>
        <i class="fa fa-plus-square" style="color:#F69730;"></i> Hospitals (CMS Rated)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# =============================================================================
# MATERNITY CARE / HEALTHCARE FUNCTIONS
# =============================================================================

def load_maternity_hospitals() -> Dict[str, Any]:
    """Load maternity hospitals data from JSON file."""
    json_path = os.path.join(HEALTHCARE_DIR, 'maternity_hospitals.json')
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'hospitals': [], 'error': 'Maternity hospitals data file not found'}
    except json.JSONDecodeError:
        return {'hospitals': [], 'error': 'Invalid JSON in maternity hospitals file'}


def get_nicu_level_description(level: str) -> str:
    """Get plain-English description for NICU level."""
    descriptions = {
        'I': 'Basic nursery for healthy full-term babies',
        'II': 'Special care for babies 32+ weeks with moderate issues',
        'III': 'Full NICU for premature/seriously ill babies',
        'IV': 'Regional center with surgery & highest-risk care'
    }
    return descriptions.get(level, 'Unknown')


def get_csection_status(rate: float) -> Tuple[str, str]:
    """
    Return color and status for C-section rate.
    Leapfrog standard: 23.6% or less
    """
    if rate <= 0.236:
        return 'green', 'Meets Standard'
    elif rate <= 0.28:
        return 'orange', 'Slightly Above'
    else:
        return 'red', 'Above Standard'


def format_star_rating(rating: int) -> str:
    """Format CMS star rating as emoji stars."""
    if not rating or rating < 1:
        return 'N/A'
    return '⭐' * rating


def load_healthcare_facilities() -> List[Dict[str, Any]]:
    """
    Load hospitals and urgent care facilities from GeoJSON file.

    Returns list of facilities with parsed properties and coordinates.
    """
    geojson_path = os.path.join(HEALTHCARE_DIR, 'Loudoun_Hospitals_and_Urgent_Care (1).geojson')
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        facilities = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])

            facilities.append({
                'name': props.get('FACILITY_NAME', 'Unknown'),
                'type': props.get('FACILITY', 'U'),  # H=Hospital, U=Urgent Care
                'address': props.get('Address', ''),
                'longitude': coords[0],
                'latitude': coords[1],
                'phone': props.get('Phone', ''),
                'cms_rating': props.get('CMS_Rating'),
                'hospital_type': props.get('Hospital_Type', ''),
                'beds': props.get('Beds'),
                'health_system': props.get('Health_System', ''),
                'emergency_services': props.get('Emergency_Services', False)
            })
        return facilities
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def display_hospitals_subsection(facilities: List[Dict[str, Any]], lat: float, lon: float):
    """Display hospitals and emergency centers subsection."""
    st.markdown("### 🏥 Hospitals & Medical Facilities")

    # Filter to hospitals only (type='H')
    hospitals = [f for f in facilities if f.get('type') == 'H']

    if not hospitals:
        st.info("No hospital data available.")
        return

    # Calculate distances
    for h in hospitals:
        h['distance_miles'] = haversine_distance(lat, lon, h['latitude'], h['longitude'])

    # Separate CMS-rated hospitals from others
    cms_rated = [h for h in hospitals if h.get('cms_rating')]
    other_facilities = [h for h in hospitals if not h.get('cms_rating')]

    # Sort each group by distance
    cms_rated_sorted = sorted(cms_rated, key=lambda x: x['distance_miles'])
    other_sorted = sorted(other_facilities, key=lambda x: x['distance_miles'])

    # Display CMS-rated hospitals first with enhanced format
    if cms_rated_sorted:
        st.markdown("**Acute Care Hospitals** (CMS Rated)")
        for h in cms_rated_sorted:
            dist = h['distance_miles']
            name = h['name']
            cms_rating = h.get('cms_rating', 0)
            phone = h.get('phone', '')
            stars = '⭐' * cms_rating if cms_rating else 'N/A'

            # Format: Name — distance | stars | phone
            display_line = f"**{name}** — {dist:.1f} mi | {stars}"
            if phone:
                display_line += f" | {phone}"
            st.markdown(display_line)

            # Second line: Health system, beds, emergency services
            details_parts = []
            if h.get('health_system'):
                details_parts.append(h['health_system'])
            if h.get('beds'):
                details_parts.append(f"{h['beds']} beds")
            if h.get('emergency_services'):
                details_parts.append("Emergency Services")
            if details_parts:
                st.markdown(" • ".join(details_parts))

            st.caption(h['address'])
        st.markdown("---")

    # Display other facilities (ERs, rehab, behavioral, etc.)
    if other_sorted:
        st.markdown(f"**Emergency & Other Medical Facilities** ({len(other_sorted)})")

        # Show nearest facility directly
        nearest = other_sorted[0]
        st.markdown(f"**{nearest['name']}** — {nearest['distance_miles']:.1f} mi")
        st.caption(nearest['address'])

        # Put remaining in expander
        if len(other_sorted) > 1:
            remaining = other_sorted[1:]
            with st.expander(f"View all {len(remaining)} other facilities"):
                for h in remaining:
                    st.markdown(f"**{h['name']}** — {h['distance_miles']:.1f} mi")
                    st.caption(h['address'])
        st.markdown("---")


def display_urgent_care_subsection(facilities: List[Dict[str, Any]], lat: float, lon: float):
    """Display urgent care centers subsection."""
    st.markdown("### 🩺 Urgent Care Centers")

    # Filter to urgent care only (type='U')
    urgent_care = [f for f in facilities if f.get('type') == 'U']

    if not urgent_care:
        st.info("No urgent care data available.")
        return

    # Calculate distances
    for uc in urgent_care:
        uc['distance_miles'] = haversine_distance(lat, lon, uc['latitude'], uc['longitude'])

    urgent_care_sorted = sorted(urgent_care, key=lambda x: x['distance_miles'])

    # Show count and nearest 2
    nearest_2 = urgent_care_sorted[:2]

    st.markdown(f"**{len(urgent_care)} urgent care centers** in Loudoun County")
    st.markdown(f"*Showing {len(nearest_2)} nearest:*")

    for uc in nearest_2:
        dist = uc['distance_miles']
        name = uc['name']
        address = uc['address']
        st.markdown(f"• **{name}** — {dist:.1f} mi")
        st.caption(f"  {address}")

    # Expandable list for all
    if len(urgent_care_sorted) > 2:
        remaining_count = len(urgent_care_sorted) - 2
        with st.expander(f"View all {remaining_count} other urgent care centers"):
            for uc in urgent_care_sorted[2:]:
                dist = uc['distance_miles']
                st.markdown(f"• **{uc['name']}** — {dist:.1f} mi ({uc['address']})")


def display_pharmacies_subsection(pharmacies: list):
    """Display nearby pharmacies from Google Places API."""
    st.markdown("### 💊 Pharmacies")

    if not pharmacies:
        st.info("No pharmacies found within 5 miles")
        return

    # Show count
    st.markdown(f"**{len(pharmacies)} pharmacies** within 5 miles")

    # Highlight 24-hour pharmacies if any
    pharmacies_24hr = [p for p in pharmacies if p.get('is_24_hour')]
    if pharmacies_24hr:
        st.markdown("**🌙 24-Hour Pharmacies:**")
        for p in pharmacies_24hr[:3]:
            rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
            st.markdown(f"• **{p['name']}** — {p['distance_miles']:.1f} mi {rating}")
            st.caption(p['address'])

    # Show 2 nearest (excluding 24-hour already shown)
    shown_names = {p['name'] for p in pharmacies_24hr[:3]}
    regular = [p for p in pharmacies if p['name'] not in shown_names][:2]
    if regular:
        if pharmacies_24hr:
            st.markdown("**Other Nearby Pharmacies:**")
        else:
            st.markdown("**Nearest Pharmacies:**")
        for p in regular:
            rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
            st.markdown(f"• **{p['name']}** — {p['distance_miles']:.1f} mi {rating}")
            st.caption(p['address'])

    # Expander for remaining pharmacies
    total_shown = min(3, len(pharmacies_24hr)) + len(regular)
    if len(pharmacies) > total_shown:
        remaining = len(pharmacies) - total_shown
        with st.expander(f"View all {remaining} other pharmacies"):
            for p in pharmacies[total_shown:]:
                rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
                st.markdown(f"• {p['name']} — {p['distance_miles']:.1f} mi {rating}")


def display_economic_indicators_section():
    """Display Economic Indicators section with LFPR, industry mix, and major employers."""
    import plotly.graph_objects as go
    import pandas as pd

    st.markdown("---")
    st.subheader("💼 Economic Indicators")

    # =========================================================================
    # SUMMARY METRICS (Always Visible)
    # =========================================================================

    lfpr_data = get_lfpr_data()
    bls_data = fetch_bls_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        lfpr = lfpr_data.get("loudoun")
        delta = f"+{lfpr_data.get('loudoun_vs_usa')} vs USA" if lfpr_data.get('loudoun_vs_usa') else None
        st.metric(
            label="Labor Force Participation",
            value=f"{lfpr:.1f}%" if lfpr else "N/A",
            delta=delta
        )

    with col2:
        unemp = bls_data.get("unemployment_rate", {})
        unemp_value = unemp.get("value")
        unemp_date = unemp.get("date", "")

        st.metric(
            label="Unemployment Rate",
            value=f"{unemp_value:.1f}%" if unemp_value else "N/A"
        )
        if unemp_date:
            st.caption(f"As of {unemp_date}")

    with col3:
        lf = bls_data.get("labor_force", {})
        lf_value = lf.get("value")
        yoy = lf.get("yoy_change")
        delta_str = None
        if yoy is not None:
            delta_str = f"+{yoy:.1f}% YoY" if yoy > 0 else f"{yoy:.1f}% YoY"
        st.metric(
            label="Labor Force",
            value=f"{lf_value:,.0f}" if lf_value else "N/A",
            delta=delta_str
        )

    st.caption("Sources: Census ACS 5-Year (LFPR) | BLS LAUS (Unemployment, Labor Force)")

    # =========================================================================
    # INDUSTRY EMPLOYMENT MIX (Expander)
    # =========================================================================

    with st.expander("📊 Industry Employment Mix"):
        industry_data = get_industry_mix_data()
        all_industries = industry_data.get("industries", [])
        industries = all_industries[:6]  # Top 6 sectors for chart

        # Use tabs instead of toggle to prevent expander collapse
        tab_chart, tab_table = st.tabs(["Top 6 Sectors", "All 13 Sectors"])

        with tab_chart:
            if industries:
                # Prepare data for grouped horizontal bar chart
                sectors = [ind["sector"] for ind in industries]
                loudoun_vals = [ind["loudoun"] or 0 for ind in industries]
                va_vals = [ind["virginia"] or 0 for ind in industries]
                usa_vals = [ind["usa"] or 0 for ind in industries]

                # Reverse for horizontal bars (top sector at top)
                sectors.reverse()
                loudoun_vals.reverse()
                va_vals.reverse()
                usa_vals.reverse()

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=loudoun_vals,
                    name='Loudoun',
                    orientation='h',
                    marker_color='#1f77b4',
                    text=[f"{v:.1f}%" for v in loudoun_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=va_vals,
                    name='Virginia',
                    orientation='h',
                    marker_color='#ff7f0e',
                    text=[f"{v:.1f}%" for v in va_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=usa_vals,
                    name='USA',
                    orientation='h',
                    marker_color='#2ca02c',
                    text=[f"{v:.1f}%" for v in usa_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.update_layout(
                    barmode='group',
                    height=350,
                    margin=dict(l=180, r=60, t=40, b=40),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5
                    ),
                    xaxis_title="% of Employment",
                    yaxis=dict(tickfont=dict(size=13)),
                    uniformtext=dict(mode='hide', minsize=14)
                )

                st.plotly_chart(fig, width='stretch')

        with tab_table:
            if all_industries:
                df = pd.DataFrame(all_industries)
                df.columns = ["Sector", "Loudoun %", "Virginia %", "USA %"]
                # Format percentages
                df["Loudoun %"] = df["Loudoun %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                df["Virginia %"] = df["Virginia %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                df["USA %"] = df["USA %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                st.dataframe(df, width='stretch', hide_index=True)

        st.caption(f"Source: {industry_data.get('source', 'Census ACS')}")

    # =========================================================================
    # MAJOR EMPLOYERS (Expander)
    # =========================================================================

    # PRE-LOAD employer data BEFORE expander for instant opening
    all_employers_data = load_major_employers()

    def format_employer_df(employers_list):
        """Format employer list into display DataFrame."""
        formatted = []
        for emp in employers_list:
            employees = emp.get("employees")
            employees_range = emp.get("employees_range", "")
            formatted.append({
                "Rank": emp.get("rank", 0),
                "Employer": emp.get("name", ""),
                "Employees": f"{employees:,}" if employees else employees_range,
                "% of Total": f"{emp.get('pct', 0):.2f}%",
                "Industry": _infer_employer_industry(emp.get("name", ""))
            })
        return pd.DataFrame(formatted)

    # PRE-CREATE all year DataFrames BEFORE expander for instant tab switching
    employer_year_dfs = {}
    for year in range(2008, 2026):
        year_data = all_employers_data.get("employers_by_year", {}).get(str(year), {})
        employers_list = year_data.get("employers", [])
        if employers_list:
            employer_year_dfs[year] = format_employer_df(employers_list)

    with st.expander("🏢 Major Employers"):
        # Trend highlights
        trends = get_employer_trends()
        lcps = trends.get("lcps_growth", {})

        st.info(
            f"📈 **Key Trends (2008-2025):** "
            f"Loudoun County Public Schools +{lcps.get('pct_change', 0):.0f}% ({lcps.get('start_employees', 0):,} → {lcps.get('end_employees', 0):,}) | "
            f"Amazon entered top 10 in 2020 | "
            f"Verizon declined #3 → #8"
        )

        # Year tabs
        tab_years = ["2025", "2024", "2023", "2022", "2021"]
        tabs = st.tabs(tab_years + ["Earlier"])

        for i, tab in enumerate(tabs[:-1]):  # All except "Earlier"
            year = int(tab_years[i])
            with tab:
                if year in employer_year_dfs:
                    st.dataframe(employer_year_dfs[year], width='stretch', hide_index=True)
                else:
                    st.write("Data not available for this year.")

        # "Earlier" tab with dropdown
        with tabs[-1]:
            earlier_year = st.selectbox(
                "Select year",
                range(2020, 2007, -1),
                key="earlier_year_select"
            )
            if earlier_year in employer_year_dfs:
                st.dataframe(employer_year_dfs[earlier_year], width='stretch', hide_index=True)
            else:
                st.info(f"No employer data available for {earlier_year}")

        st.caption("Source: Loudoun County Annual Comprehensive Financial Reports (ACFR)")

    # =========================================================================
    # DATA SOURCES & METHODOLOGY (Expander)
    # =========================================================================

    with st.expander("📋 Data Sources & Methodology"):
        st.markdown("""
**Labor Force Participation Rate (LFPR)**
- Source: Census Bureau American Community Survey (ACS) 5-Year Estimates (2019-2023)
- Definition: Percentage of population 16+ that is in the labor force (employed or actively seeking work)
- Note: 5-Year estimates provide more stable data with lower margin of error than 1-Year estimates

**Unemployment Rate & Labor Force**
- Source: Bureau of Labor Statistics (BLS) Local Area Unemployment Statistics (LAUS)
- Frequency: Monthly (most recent available)
- Note: County-level data is not seasonally adjusted. Year-over-year comparisons are more reliable than month-over-month.

**Industry Employment Mix**
- Source: Census Bureau ACS 5-Year Estimates
- Shows percentage of employed residents by industry sector

**Major Employers**
- Source: Loudoun County Annual Comprehensive Financial Report (ACFR)
- Updated annually (fiscal year ending June 30)
- Employee counts may be ranges; percentages based on total county employment
        """)


def _infer_employer_industry(employer_name: str) -> str:
    """Infer industry category from employer name."""
    name_lower = employer_name.lower()

    if "school" in name_lower or "lcps" in name_lower:
        return "Education"
    elif "county of loudoun" in name_lower:
        return "Government"
    elif "homeland security" in name_lower or "postal" in name_lower:
        return "Federal Government"
    elif "hospital" in name_lower or "inova" in name_lower or "health" in name_lower:
        return "Healthcare"
    elif "amazon" in name_lower:
        return "Technology/Logistics"
    elif "verizon" in name_lower:
        return "Telecommunications"
    elif "united airlines" in name_lower or "swissport" in name_lower:
        return "Aviation/Transportation"
    elif "northrop" in name_lower or "raytheon" in name_lower or "rtx" in name_lower or "orbital" in name_lower:
        return "Defense/Aerospace"
    elif "walmart" in name_lower:
        return "Retail"
    elif "dean" in name_lower or "dynalectric" in name_lower:
        return "Construction/Engineering"
    else:
        return "Other"


def display_medical_access_section(lat: float, lon: float):
    """
    Display comprehensive medical access information.

    Parent section containing:
    - Hospitals & Emergency Centers (from GeoJSON)
    - Urgent Care Centers (from GeoJSON)
    - Pharmacies (Google Places API)
    - Maternity Care (existing detailed component)
    """
    st.markdown("## 🏥 Medical Access")

    # Load facilities from GeoJSON
    facilities = load_healthcare_facilities()

    # Load maternity data for count
    maternity_data = load_maternity_hospitals()
    maternity_hospitals = maternity_data.get('hospitals', []) if 'error' not in maternity_data else []

    # Search for pharmacies using Google Places API
    from core.loudoun_places_analysis import search_nearby_places, PLACE_CATEGORIES
    pharmacy_config = PLACE_CATEGORIES.get('pharmacy', {})
    pharmacies, _ = search_nearby_places(
        (lat, lon),
        'pharmacy',
        pharmacy_config.get('radius_miles', 5.0)
    )

    # Count by type
    hospitals = [f for f in facilities if f.get('type') == 'H']
    urgent_care = [f for f in facilities if f.get('type') == 'U']

    # Summary metrics (4 columns)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Hospitals/ER", len(hospitals))
    with col2:
        st.metric("Urgent Care", len(urgent_care))
    with col3:
        st.metric("Pharmacies", len(pharmacies))
    with col4:
        st.metric("Maternity Hospitals", len(maternity_hospitals))

    st.markdown("---")

    # Subsection: Hospitals & Emergency
    display_hospitals_subsection(facilities, lat, lon)

    # Subsection: Urgent Care
    display_urgent_care_subsection(facilities, lat, lon)

    # Subsection: Pharmacies
    display_pharmacies_subsection(pharmacies)

    # Subsection: Maternity Care (existing component)
    st.markdown("### 🍼 Maternity & Birthing Hospitals")
    _display_maternity_content(lat, lon)

    # Healthcare access quality note
    st.success("✅ **Excellent Healthcare Access** — Loudoun County ranks in the top 10% nationally for primary care physician availability, with approximately 1 physician per 1,350 residents.")

    st.caption("Data: Loudoun County GIS, Leapfrog Group, CMS Hospital Compare, Google Places API")


def _display_maternity_content(lat: float, lon: float):
    """
    Internal function for maternity content display.
    Called from within display_medical_access_section.
    """
    # Load data
    data = load_maternity_hospitals()

    if 'error' in data:
        st.info(f"Maternity hospital data not available: {data['error']}")
        return

    hospitals = data.get('hospitals', [])
    if not hospitals:
        st.info("No maternity hospital data available.")
        return

    # Calculate distances and sort
    for hospital in hospitals:
        coords = hospital.get('coordinates', {})
        h_lat = coords.get('latitude', 0)
        h_lon = coords.get('longitude', 0)
        hospital['distance_miles'] = haversine_distance(lat, lon, h_lat, h_lon)

    hospitals_sorted = sorted(hospitals, key=lambda x: x['distance_miles'])

    # Summary at top
    loudoun_hospitals = [h for h in hospitals_sorted if h.get('in_loudoun_county')]
    nearby_hospitals = [h for h in hospitals_sorted if not h.get('in_loudoun_county')]

    st.markdown(f"""
**{len(loudoun_hospitals)} birthing hospitals in Loudoun County** and **{len(nearby_hospitals)} nearby in Fairfax County**.
All hospitals shown have labor & delivery units, NICUs, and are rated by CMS and Leapfrog for safety.
    """)

    # Display each hospital
    for hospital in hospitals_sorted:
        maternity = hospital.get('maternity', {})
        quality = hospital.get('quality', {})

        distance = hospital['distance_miles']
        name = hospital.get('name', 'Unknown Hospital')
        county_badge = "📍 Loudoun" if hospital.get('in_loudoun_county') else "📍 Fairfax"

        stars = format_star_rating(quality.get('cms_overall_rating'))
        safety_grade = quality.get('leapfrog_safety_grade', 'N/A')

        with st.expander(f"**{name}** — {distance:.1f} mi | {stars} | Safety: {safety_grade}", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Distance", f"{distance:.1f} mi")
                st.caption(county_badge)

            with col2:
                cms_rating = quality.get('cms_overall_rating')
                st.metric("CMS Rating", format_star_rating(cms_rating))
                if quality.get('leapfrog_top_hospital'):
                    st.caption("🏆 Top Hospital")

            with col3:
                st.metric("Safety Grade", safety_grade)
                consecutive = quality.get('leapfrog_consecutive_a_grades')
                if consecutive:
                    st.caption(f"{consecutive} consecutive A's")

            with col4:
                nicu_level = maternity.get('nicu_level', 'N/A')
                st.metric("NICU Level", nicu_level)
                st.caption(get_nicu_level_description(nicu_level))

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Delivery Statistics**")
                births = maternity.get('live_births_annual', 0)
                st.markdown(f"• Births/year: **{births:,}**")

                csection_rate = maternity.get('c_section_rate', 0)
                csection_pct = csection_rate * 100
                color, status = get_csection_status(csection_rate)

                if color == 'green':
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** ✅")
                elif color == 'orange':
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** ⚠️")
                else:
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** 🔴")

                st.caption(f"Leapfrog standard: ≤23.6%")

                episiotomy_rate = maternity.get('episiotomy_rate', 0)
                st.markdown(f"• Episiotomy rate: **{episiotomy_rate * 100:.1f}%**")

            with col2:
                st.markdown("**Key Services**")

                if maternity.get('midwives_available'):
                    st.markdown("✅ Certified Nurse-Midwives")
                else:
                    st.markdown("❌ No midwives on staff")

                if maternity.get('vbac_offered'):
                    st.markdown("✅ VBAC (vaginal birth after C-section)")
                else:
                    st.markdown("❌ VBAC not offered")

                lactation = maternity.get('lactation_services', '')
                if lactation == 'hospital_and_outpatient':
                    st.markdown("✅ Lactation support (hospital & outpatient)")
                elif lactation == 'hospital_only':
                    st.markdown("✅ Lactation support (hospital only)")
                else:
                    st.markdown("❌ No lactation services listed")

                if maternity.get('doulas_allowed'):
                    st.markdown("✅ Doulas welcome")

            with col3:
                st.markdown("**Hospital Info**")
                st.markdown(f"• {hospital.get('health_system', 'N/A')}")
                st.markdown(f"• {hospital.get('address', '')}")
                st.markdown(f"• {hospital.get('city', '')}, {hospital.get('state', '')} {hospital.get('zip', '')}")

                if quality.get('magnet_status'):
                    st.markdown("🏅 **Magnet® Recognized** (nursing excellence)")

                if maternity.get('birthing_friendly_cms'):
                    st.markdown("👶 **CMS Birthing-Friendly** designated")

            top_years = quality.get('leapfrog_top_hospital_years', [])
            if top_years:
                years_str = ', '.join(str(y) for y in top_years)
                st.caption(f"🏆 Leapfrog Top Hospital: {years_str}")

    # NICU Level reference
    with st.expander("ℹ️ Understanding NICU Levels", expanded=False):
        st.markdown("""
| Level | Description | Capabilities |
|-------|-------------|--------------|
| **I** | Well-baby nursery | Healthy, full-term babies (35+ weeks) |
| **II** | Special care nursery | Babies 32+ weeks, moderate issues, expected quick recovery |
| **III** | Full NICU | Babies under 32 weeks or 3.3 lbs, serious illness, subspecialty care |
| **IV** | Regional NICU | All Level III + complex surgery, ECMO, regional referral center |

*Inova Fairfax Hospital has Northern Virginia's only Level IV NICU for the highest-risk cases.*
        """)

    # C-section rate context
    with st.expander("ℹ️ Understanding C-Section Rates", expanded=False):
        st.markdown("""
**What the C-section rate measures:**
The rate shown is for first-time mothers with a single baby in head-down position at full term
(NTSV: Nulliparous, Term, Singleton, Vertex). This is the standard comparison metric.

**Leapfrog standard: 23.6% or less**
- ✅ **Green** = Meets or exceeds the standard
- ⚠️ **Yellow** = Slightly above (23.7% - 28%)
- 🔴 **Red** = Significantly above standard (>28%)

Lower rates generally indicate fewer unnecessary C-sections, but individual medical circumstances vary.
        """)


def display_development_section(lat: float, lon: float):
    """Display development and infrastructure section."""
    st.markdown("## 📊 Neighborhood Development & Infrastructure")

    dev_data = analyze_development(lat, lon)

    if 'error' in dev_data:
        st.warning(f"Development analysis unavailable: {dev_data['error']}")
        return

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Permits (2 mi)", f"{dev_data['total_permits']:,}")

    with col2:
        value_millions = dev_data['total_value'] / 1_000_000
        st.metric("Construction Value", f"${value_millions:.1f}M")

    with col3:
        st.metric("Recent (6 mo)", f"{dev_data['recent_count']:,}")

    with col4:
        st.metric("Tech Infrastructure", f"{dev_data['infrastructure_count']:,}")

    # Map
    if FOLIUM_AVAILABLE and not dev_data['nearby_permits'].empty:
        st.markdown("### Development Activity Map")

        # Legend
        st.markdown("""
        <small>🔴 Data Center | 🟠 Fiber/Telecom | 🟣 Infrastructure | 🟢 Other Construction</small>
        """, unsafe_allow_html=True)

        m = create_development_map(lat, lon, dev_data['nearby_permits'])
        st_folium(m, width=None, height=450, returned_objects=[])

    # Loudoun's Data Center Economy
    if dev_data['datacenter_count'] > 0 or dev_data['fiber_count'] > 0:
        st.markdown("---")
        st.markdown("### 💡 Loudoun's Data Center Economy")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"""
            This property is located in the world's largest data center market.

            **Tech Infrastructure Within 2 Miles:**
            - 🏢 Data Center Projects: **{dev_data['datacenter_count']}**
            - 📡 Fiber/Telecom Projects: **{dev_data['fiber_count']}**
            - 💰 Total Tech Investment: **${dev_data['total_value']/1e6:.1f}M**

            **Why This Matters:**
            - Robust fiber connectivity infrastructure
            - Stable tech sector employment nearby
            - Property values supported by commercial investment
            - World-class internet infrastructure
            """)

        with col2:
            # Simple pie chart of permit types
            if PLOTLY_AVAILABLE:
                nearby = dev_data['nearby_permits']
                infra = len(nearby[nearby['is_infrastructure'] == True])
                other = len(nearby) - infra

                if infra > 0:
                    fig = go.Figure(data=[go.Pie(
                        labels=['Tech Infrastructure', 'Other'],
                        values=[infra, other],
                        hole=0.4,
                        marker_colors=['#6366f1', '#22c55e']
                    )])
                    fig.update_layout(
                        showlegend=True,
                        height=250,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig, width='stretch')

    st.markdown("---")


# =============================================================================
# SECTION: ZONING
# =============================================================================

def display_zoning_section(address: str, lat: float, lon: float):
    """Display zoning information with plain English translations and integrated features."""
    st.markdown("## 🏗️ Zoning & Land Use")

    try:
        # Get full zoning analysis
        zoning_result = analyze_property_zoning_loudoun(lat, lon)

        if not zoning_result:
            st.error("Unable to load zoning information")
            return

        # Extract components
        jurisdiction = zoning_result.get('jurisdiction', 'LOUDOUN')
        town_name = zoning_result.get('town_name')
        current_zoning = zoning_result.get('current_zoning', {})
        place_type = zoning_result.get('place_type', {})
        dev_prob = zoning_result.get('development_probability', {})

        # Get plain English translations
        zoning_code = current_zoning.get('zoning', 'N/A')
        place_type_code = place_type.get('place_type_code', '')

        # Import translation functions
        from core.loudoun_zoning_analysis import (
            get_plain_english_zoning,
            get_plain_english_placetype,
            characterize_building_permits,
            generate_zoning_narrative,
            generate_permit_narrative
        )
        from core.loudoun_community_lookup import CommunityLookup

        zoning_translation = get_plain_english_zoning(zoning_code)
        place_translation = get_plain_english_placetype(place_type_code)

        # Show jurisdiction if in a town
        if town_name:
            st.info(f"📍 This property is in the **Town of {town_name}** (incorporated)")

        # INLINE SUMMARY - Clean and scannable
        plain_zoning = zoning_translation.get('plain_english', zoning_code)
        character = place_translation.get('character', 'Residential area')
        st.markdown(f"📍 **Zoning:** {plain_zoning} • **Character:** {character}")

        # MAIN EXPANDER: What This Means
        with st.expander("📋 What This Means", expanded=False):

            # === ZONING FOR THIS PROPERTY ===
            st.markdown("### Zoning for This Property")

            # Generate flowing prose narrative
            zoning_narrative = generate_zoning_narrative(
                zoning_data=zoning_translation,
                place_data=place_translation,
                community_data=None  # Community data handled in separate section
            )
            st.markdown(zoning_narrative)

            # === RECENT CONSTRUCTION ACTIVITY ===
            st.markdown("### Recent Construction Activity")
            permits = characterize_building_permits(lat, lon, radius_miles=2)

            if permits and permits.get('success'):
                # Generate flowing prose narrative with breakdowns and comparisons
                permit_narrative = generate_permit_narrative(
                    permit_data=permits,
                    activity_level=permits.get('recent_activity', 'Unknown'),
                    property_community=permits.get('property_community')
                )
                st.markdown(permit_narrative)
            else:
                st.info("No recent building permit data available for this area.")

            # === NEARBY COMMUNITIES ===
            st.markdown("### Nearby Communities")

            try:
                from math import radians, sin, cos, sqrt, atan2

                def calculate_distance(lat1, lon1, lat2, lon2):
                    """Calculate distance between two points using Haversine formula."""
                    R = 3959  # Earth's radius in miles
                    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    return R * c

                # Load communities with coordinates
                lookup = CommunityLookup()

                # Calculate distances to all communities
                nearby_communities = []

                for comm_key in lookup.list_communities():
                    # Get raw community data (has coordinates)
                    comm_data = lookup.get_community_by_key(comm_key)
                    summary = lookup.get_community_summary(comm_key)

                    if comm_data and summary and 'latitude' in comm_data and 'longitude' in comm_data:
                        # Calculate distance from current property
                        dist = calculate_distance(
                            lat, lon,
                            comm_data['latitude'],
                            comm_data['longitude']
                        )

                        nearby_communities.append({
                            'key': comm_key,
                            'name': summary.get('display_name', comm_key),
                            'distance': dist,
                            'homes': summary.get('total_homes'),
                            'hoa': summary.get('monthly_fee'),
                            'gated': summary.get('gated', False),
                            'amenities': summary.get('amenities_list', []),
                            'location': summary.get('location', '')
                        })

                # Sort by distance (closest first)
                nearby_communities.sort(key=lambda x: x['distance'])

                # Check if property is WITHIN a community (distance < 0.5 miles)
                current_community = None
                if nearby_communities and nearby_communities[0]['distance'] < 0.5:
                    current_community = nearby_communities[0]
                    nearby_communities = nearby_communities[1:]

                # Display current community if detected
                if current_community:
                    st.success(f"📍 **This property is in {current_community['name']}**")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if current_community['homes']:
                            st.metric("Community Size", f"{current_community['homes']:,} homes")
                    with col2:
                        if current_community['gated']:
                            st.metric("Access", "🔒 Gated")
                        else:
                            st.metric("Access", "Open")
                    with col3:
                        if current_community['hoa']:
                            st.metric("HOA Fee", f"${current_community['hoa']:.0f}/mo")

                    if current_community['amenities']:
                        st.markdown("**Amenities:** " + " • ".join(current_community['amenities'][:5]))

                    st.markdown("---")

                # Display nearby communities (within 5 miles)
                communities_within_5mi = [c for c in nearby_communities if c['distance'] <= 5.0]

                if communities_within_5mi:
                    st.markdown(f"**Other Nearby Communities** ({len(communities_within_5mi)} within 5 miles):")

                    for comm in communities_within_5mi[:10]:
                        # Format distance
                        if comm['distance'] < 0.1:
                            dist_str = f"{comm['distance']*5280:.0f} ft"
                        else:
                            dist_str = f"{comm['distance']:.1f} mi"

                        # Build detail parts
                        details = []
                        if comm['homes']:
                            details.append(f"{comm['homes']:,} homes" if comm['homes'] >= 1000 else f"{comm['homes']} homes")
                        if comm['gated']:
                            details.append("Gated")
                        if comm['hoa']:
                            details.append(f"${comm['hoa']:.0f}/mo")
                        if comm['amenities']:
                            notable = [a for a in comm['amenities']
                                      if any(kw in a.lower() for kw in ['pool', 'golf', 'trail', 'fitness'])]
                            if notable:
                                details.append(notable[0])

                        if details:
                            st.markdown(f"• **{comm['name']}** - {dist_str} ({' • '.join(details[:3])})")
                        else:
                            st.markdown(f"• **{comm['name']}** - {dist_str}")

                    if len(communities_within_5mi) > 10:
                        st.caption(f"+ {len(communities_within_5mi) - 10} more communities within 5 miles")

                elif not current_community:
                    st.info("No major communities found within 5 miles.")
                    if nearby_communities:
                        st.markdown("**Nearest Communities:**")
                        for comm in nearby_communities[:3]:
                            st.markdown(f"• **{comm['name']}** - {comm['distance']:.1f} mi ({comm['location']})")

            except FileNotFoundError:
                st.caption("💡 Community data not available")
            except Exception as e:
                st.caption(f"⚠️ Unable to load community data")

            # Technical Reference (small text)
            st.markdown("---")
            st.caption(f"**Technical Reference:** Zoning: {zoning_code}")
            if current_zoning.get('zoning_description'):
                st.caption(current_zoning['zoning_description'])

            if place_type_code:
                place_full = place_type.get('place_type', '')
                st.caption(f"Place Type: {place_type_code} ({place_full})")

            st.caption("Source: Loudoun County GIS, December 2025")

        # Development Probability (existing functionality - keep as is)
        if dev_prob.get('score') is not None:
            with st.expander("🔮 Development Probability", expanded=False):
                score = dev_prob['score']
                risk_level = dev_prob.get('risk_level', 'Unknown')

                # Display score with color
                if score < 25:
                    color = "🟢"
                elif score < 50:
                    color = "🟡"
                elif score < 75:
                    color = "🟠"
                else:
                    color = "🔴"

                st.markdown(f"{color} **Development Score:** {score}/100 ({risk_level})")

                # Show current status
                st.markdown("**Current Status:**")
                st.markdown(f"• Zoned: {plain_zoning} ({zoning_code})")
                st.markdown(f"• Place Type: {place_translation.get('plain_english', place_type.get('place_type', 'Unknown'))}")

                # Score breakdown table
                component_scores = dev_prob.get('component_scores', {})
                component_reasons = dev_prob.get('component_reasons', {})

                if component_scores:
                    st.markdown("**Score Breakdown:**")

                    # Create breakdown data
                    breakdown_data = {
                        'Component': [
                            'Zoning vs. Plan Mismatch',
                            'Current Zoning Restrictiveness',
                            'Comprehensive Plan Pressure',
                            '**TOTAL**'
                        ],
                        'Score': [
                            f"{component_scores.get('mismatch', 0)}/40",
                            f"{component_scores.get('restrictiveness', 0)}/30",
                            f"{component_scores.get('pressure', 0)}/30",
                            f"**{score}/100**"
                        ],
                        'Reason': [
                            component_reasons.get('mismatch', ''),
                            component_reasons.get('restrictiveness', ''),
                            component_reasons.get('pressure', ''),
                            f"**{risk_level}**"
                        ]
                    }

                    # Display as dataframe
                    breakdown_df = pd.DataFrame(breakdown_data)
                    st.dataframe(
                        breakdown_df,
                        width='stretch',
                        hide_index=True
                    )

                # Educational explanation of components
                with st.expander("📚 Understanding the Score Components"):
                    st.markdown("""
The development probability score combines three factors to assess whether this
property might face redevelopment pressure in the next 10-20 years:

**1. Zoning vs. Plan Mismatch (0-40 points)**

Measures how different today's zoning is from the county's long-term vision in
the 2019 Comprehensive Plan.

- **High score** (30-40 pts): Large gap between current zoning and planned
  intensity. Example: A property zoned for 1 home per acre (R-1) in an area the
  county plans for mixed-use development would score high because there's
  significant potential for rezoning to match the comprehensive plan.

- **Low score** (0-10 pts): Current zoning already matches or exceeds what
  the comprehensive plan envisions. No policy-driven pressure for change.

**2. Current Zoning Restrictiveness (0-30 points, scaled by alignment)**

Measures how difficult it is to increase density under current zoning rules.

- **"Restrictive" means**: Hard to subdivide, limited building types allowed,
  strict density caps. Most restrictive zones are Agricultural/Rural (AR-1, AR-2)
  where subdividing a 20-40 acre parcel is difficult. Least restrictive are
  already-dense zones like Town Center (PD-TC) or built-out master-planned
  communities (PRN, PDH).

- **The scaling**: If current zoning already matches the comprehensive plan,
  restrictiveness is reduced by 80-85% (divided by 6) because it doesn't matter
  how restrictive the zoning is if there's no policy pushing for change.

**3. Comprehensive Plan Pressure (0-30 points, scaled by alignment)**

Measures how aggressively the county's 2019 Comprehensive Plan calls for
development in this area.

- **High pressure** (30 pts raw): Urban Transit Center, Urban/Suburban Mixed Use
  designations - the county's long-term vision actively wants dense, mixed-use
  development in these areas.

- **Moderate pressure** (10 pts raw): Suburban Neighborhood - county wants to
  maintain existing residential character with only minor evolution.

- **Low pressure** (5 pts raw): Rural preservation areas, incorporated town
  boundaries (administrative only), or transition areas where the county expects
  minimal change.

- **The scaling**: Like restrictiveness, pressure is scaled by alignment. If a
  property is already at Urban Mixed Use intensity (example: Ashburn Station
  area), the pressure score is reduced by 80-85% because the development the
  plan calls for has already happened.
""")

                # Dynamic narrative based on score and intensity_diff
                intensity_diff = dev_prob.get('intensity_diff', 0)
                place_type_name = place_type.get('place_type', 'Unknown')

                # Generate dynamic three-paragraph narrative
                # Paragraph 1: What the score means
                if score >= 80:
                    para1 = f"This property has very high redevelopment pressure ({score}/100). A score this high indicates significant potential for neighborhood change - the county's comprehensive plan envisions substantially more density or different land use than currently exists, creating policy-driven pressure for rezoning and redevelopment over the next 10-20 years."
                elif score >= 60:
                    para1 = f"This property has high redevelopment pressure ({score}/100). This indicates notable potential for change - there's a meaningful gap between current zoning and the county's long-term vision, suggesting redevelopment pressure could build over the next 15-20 years as the area evolves toward the comprehensive plan designation."
                elif score >= 40:
                    para1 = f"This property has moderate redevelopment pressure ({score}/100). This suggests some potential for gradual evolution - while there's minor misalignment between current zoning and the comprehensive plan, major change would likely unfold slowly over 20+ years if it occurs at all."
                elif score >= 20:
                    para1 = f"This property has low redevelopment pressure ({score}/100). A score this low indicates strong neighborhood stability - the county's comprehensive plan generally aligns with existing zoning, suggesting minimal policy-driven pressure for change over the next 10-20 years."
                else:
                    para1 = f"This property has very low redevelopment pressure ({score}/100). A score this low indicates very strong neighborhood stability - current zoning closely matches or exceeds what the county's comprehensive plan envisions, meaning there's essentially no policy-driven pressure for redevelopment."

                # Paragraph 2: Why it scores this way
                if intensity_diff >= 2:
                    para2 = f"This property is zoned **{plain_zoning}** ({zoning_code}) but the county's 2019 Comprehensive Plan designates this area as **{place_type_name}** - a significant intensity gap. This mismatch means the county's long-term vision calls for substantially more density or different use than currently allowed. When current zoning restricts what the comprehensive plan envisions, it creates pressure for future rezoning to align with county policy."
                elif intensity_diff == 1:
                    para2 = f"This property is zoned **{plain_zoning}** ({zoning_code}) and the county's 2019 Comprehensive Plan designates this area as **{place_type_name}** - a minor intensity difference. While there's slight misalignment, the current zoning is relatively close to the county's long-term vision. The modest scoring reflects this near-alignment, with component scores partially scaled to reflect the minor gap."
                elif intensity_diff == 0:
                    para2 = f"This property is zoned **{plain_zoning}** ({zoning_code}) and the county's 2019 Comprehensive Plan designates this area as **{place_type_name}** - a good match in intensity. The scoring reflects this strong alignment between what exists today and what the county plans for the future. When current zoning matches the comprehensive plan, there's minimal policy pressure for change, which is why the restrictiveness and pressure components are scaled down."
                else:  # intensity_diff < 0
                    para2 = f"This property is zoned **{plain_zoning}** ({zoning_code}) and the county's 2019 Comprehensive Plan designates this area as **{place_type_name}**. Notably, current zoning actually allows more intensity than the comprehensive plan designates - the area is already at or above the county's long-term vision. The scoring heavily scales down restrictiveness and pressure components because the development the plan envisions has already occurred."

                # Paragraph 3: What could trigger change
                if score >= 80:
                    para3 = "**Realistic change scenarios:** The combination of restrictive current zoning and high-intensity comprehensive plan designation creates conditions where property owners, developers, or the county itself may pursue rezoning within 5-15 years. For change to occur: (1) property owner or developer would petition for rezoning to match the comprehensive plan, (2) county planning staff would likely support since it aligns with policy, (3) public hearings would be required but plan alignment strengthens the case. Timeline: 5-15 years for initial rezonings, 10-20+ years for widespread transformation."
                elif score >= 60:
                    para3 = "**Realistic change scenarios:** The notable gap between current zoning and comprehensive plan creates moderate conditions for future rezoning requests. For change to occur: (1) economic conditions would need to favor the more intensive use, (2) individual property owners or developers would petition for rezoning, (3) county review would consider comprehensive plan alignment favorably but community input would be significant. Timeline: 10-20 years for isolated rezonings, 20-30+ years for any widespread change."
                elif score >= 40:
                    para3 = "**Realistic change scenarios:** The minor misalignment creates modest potential for gradual evolution. For change to occur: (1) sustained growth pressure would need to build over many years, (2) individual property-by-property rezonings might occur opportunistically, (3) comprehensive plan amendments could shift the designation if area character evolves differently than planned. Timeline: 15-25 years minimum for any noticeable change, 30+ years for significant transformation if it happens at all."
                elif score >= 20:
                    para3 = "**Realistic change scenarios:** The strong alignment between current zoning and comprehensive plan means change would require the county to first amend its comprehensive plan through a multi-year public process, then rezone properties through additional hearings. In areas where current zoning matches county policy, plan amendments face higher scrutiny and often strong community opposition. Timeline: 20-30+ years if change occurs at all, with significant public process required before any rezoning."
                else:
                    para3 = "**Realistic change scenarios:** The very strong alignment (or over-development relative to the plan) means major change is highly unlikely. For any significant change: the county would first need to amend its comprehensive plan through a multi-year public process with extensive community input, then individual properties would need rezoning through separate hearings. In established communities or already-developed areas, comprehensive plan amendments are rare and typically face strong opposition. Timeline: 25-35+ years minimum if major change occurs at all, more likely the area remains stable indefinitely."

                # Display the narrative
                st.markdown("---")
                st.markdown("#### Analysis")
                st.markdown(para1)
                st.markdown(para2)
                st.markdown(para3)

                # Comparative context
                st.markdown("---")
                st.markdown("#### 📊 Comparative Context")

                comparative_text = f"""
**High-Scoring Areas in Loudoun County (75-100 points):**

Areas with significant redevelopment pressure typically have restrictive current
zoning combined with high-intensity comprehensive plan designations:

- Single-family residential (R-1, R-2, R-4) near Ashburn, Dulles Airport, or
  Loudoun Gateway Metro stations in areas designated for Transit-Oriented Development
  or Urban Mixed Use

- Agricultural parcels (AR-1, AR-2) along the Route 7 corridor east of Leesburg
  designated for Suburban Mixed Use

- Low-density residential near planned town centers or activity centers where the
  comprehensive plan calls for mixed-use development

**Low-Scoring Areas in Loudoun County (0-25 points):**

Areas with minimal redevelopment pressure typically have current zoning that matches
or exceeds the comprehensive plan:

- Established master-planned communities (PRN, PDH zones) like River Creek,
  Lansdowne, Brambleton - built to their approved plans with no further density increases planned

- Already-developed urban areas like Ashburn Station, One Loudoun, Loudoun Station -
  at or above the intensity the comprehensive plan designates

- Rural preservation areas (AR-1, AR-2) in western Loudoun where the comprehensive
  plan also designates Rural or Transition Large Lot

**This Property:**

With a score of {score}/100, this property falls in the **{risk_level.upper()}** category,
placing it in the {"most stable 15-20%" if score < 20 else "more stable half" if score < 40 else "moderate stability range" if score < 60 else "areas with notable redevelopment potential" if score < 80 else "highest redevelopment pressure areas"} of Loudoun County.
"""
                st.markdown(comparative_text)

                # Score adjustment note for Tier 2 towns
                if current_zoning.get('score_adjustment'):
                    st.caption(f"⚠️ {current_zoning['score_adjustment']}")

    except Exception as e:
        st.warning(f"Zoning analysis error: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

    st.markdown("---")


# =============================================================================
# SECTION: PROPERTY VALUATION
# =============================================================================

def display_valuation_section(address: str, lat: float, lon: float, sqft_result: dict):
    """Display property valuation section with MLS square footage."""
    st.markdown("## 💰 Property Value Analysis")

    if not VALUATION_AVAILABLE:
        st.info("""
        **Property valuation features require API configuration.**

        Configure ATTOM and RentCast API keys to enable:
        - Current market value estimates
        - Comparable sales analysis
        - Rental value estimates
        - 1/3/5 year forecasts

        API keys location: `/home/claude/.config/newco/api_keys.json`
        """)
        return

    try:
        # Resolve square footage: MLS first, then ATTOM fallback
        sqft = None
        sqft_source = None
        sqft_source_details = None

        # Check MLS result
        if sqft_result and sqft_result.get('mls_sqft'):
            sqft = sqft_result['mls_sqft']
            sources = sqft_result.get('sources_found', [])
            if sources:
                sqft_source = 'MLS'
                sqft_source_details = ', '.join(sources[:3])  # Show up to 3 sources
            else:
                sqft_source = 'MLS'
                sqft_source_details = 'web search'

        with st.spinner("Fetching property valuation data..."):
            orchestrator = PropertyValuationOrchestrator()

            # Get lot size, year built, property type, and ATTOM sqft fallback
            lot_size_acres = None
            attom_sqft = None
            year_built = None
            property_type = None
            if ATTOM_CLIENT:
                try:
                    property_data = ATTOM_CLIENT.get_property_detail(address)
                    if property_data:
                        if property_data.lot_size:
                            lot_size_acres = property_data.lot_size
                        if property_data.sqft:
                            attom_sqft = property_data.sqft
                        if property_data.year_built:
                            year_built = property_data.year_built
                        if property_data.property_type:
                            property_type = property_data.property_type
                except Exception:
                    pass

            # Use ATTOM sqft as fallback if MLS failed
            if not sqft and attom_sqft:
                sqft = attom_sqft
                sqft_source = 'Tax Records'
                sqft_source_details = 'may exclude finished basement'

            # Run valuation with resolved sqft
            val_data = orchestrator.analyze_property(address, lat, lon, sqft)

        # Property Details (sqft and lot size)
        st.markdown("### Property Details")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if sqft:
                if sqft_source == 'MLS':
                    st.metric("📐 Property Size", f"{sqft:,} sqft")
                    st.caption(f"from {sqft_source_details}")
                else:
                    st.metric("📐 Property Size", f"{sqft:,} sqft")
                    st.caption(f"Tax Records - {sqft_source_details}")
            else:
                st.metric("📐 Property Size", "Unavailable")
                st.caption("Could not determine square footage")

        with col2:
            if lot_size_acres:
                st.metric("🌳 Lot Size", f"{lot_size_acres:.2f} acres")

        with col3:
            if year_built:
                st.metric("🏠 Year Built", str(year_built))
            else:
                st.metric("🏠 Year Built", "N/A")

        with col4:
            if property_type:
                st.metric("🏘️ Property Type", property_type)
            else:
                st.metric("🏘️ Property Type", "N/A")

        # === Sales History Section ===
        st.markdown("### 📊 Sales History")

        sales_history = val_data.get('sales_history', {})

        if sales_history.get('error'):
            st.warning(f"⚠️ Could not load sales history: {sales_history['error']}")

        elif sales_history.get('found'):
            sales = sales_history.get('sales', [])

            if not sales:
                st.info("No recorded sales found in county records (2020-2025).")
            else:
                # Build display table (excluding owner names)
                display_data = []
                for sale in sales:
                    date_str = format_sale_date(sale.get('sale_date', ''))
                    time_since = format_time_since_sale(sale.get('sale_date', ''))
                    price_str = format_sale_price(sale.get('sale_price'))
                    type_str = clean_verification_code(sale.get('verification_code', ''))

                    display_data.append({
                        'Sale Date': date_str,
                        'Time Since Sale': time_since,
                        'Price': price_str,
                        'Transaction Type': type_str
                    })

                # Show table
                df = pd.DataFrame(display_data)
                st.dataframe(df, width='stretch', hide_index=True)

                # Appreciation calculation (if multiple sales with prices)
                if len(sales) > 1 and sales[0].get('sale_price') and sales[-1].get('sale_price'):
                    oldest = sales[-1]  # Last in list (oldest chronologically)
                    newest = sales[0]   # First in list (newest chronologically)

                    old_price = oldest['sale_price']
                    new_price = newest['sale_price']
                    appreciation_pct = ((new_price - old_price) / old_price) * 100

                    st.info(f"💡 Appreciation: {format_sale_price(old_price)} ({format_sale_date(oldest.get('sale_date', ''))}) → {format_sale_price(new_price)} ({format_sale_date(newest.get('sale_date', ''))}) = **{appreciation_pct:+.1f}%**")

                # Current Estimated Value comparison (if available)
                current_avm = val_data.get('current_value', {}).get('attom_estimate')
                if current_avm and sales[0].get('sale_price'):
                    latest_sale = sales[0]
                    sale_price = latest_sale['sale_price']
                    avm_vs_sale = ((current_avm - sale_price) / sale_price) * 100
                    st.info(f"📈 Current Estimated Value: {format_sale_price(current_avm)} ({avm_vs_sale:+.1f}% vs. last sale)")

                # Source attribution
                data_range = sales_history.get('data_range', '2020-2025')
                source = sales_history.get('source', 'Loudoun County Commissioner of Revenue')
                st.caption(f"**Source:** {source} • Showing sales from {data_range}")

        else:
            st.info("No recorded sales found in county records (2020-2025).")

        # Current value
        cv = val_data.get('current_value', {})

        st.markdown("### Current Value Estimates")

        # Only show ATTOM column if ATTOM is enabled and has data
        attom_val = cv.get('attom_estimate', 0) if ATTOM_CLIENT else 0
        rentcast_val = cv.get('rentcast_estimate', 0)
        triangulated = cv.get('triangulated_estimate', 0)
        confidence = cv.get('confidence_score', 0)

        if attom_val:
            # Show all 4 columns when ATTOM is available
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ATTOM Estimate", f"${attom_val:,.0f}")
            with col2:
                st.metric("RentCast Estimate", f"${rentcast_val:,.0f}" if rentcast_val else "N/A")
            with col3:
                st.metric("Triangulated Value", f"${triangulated:,.0f}" if triangulated else "N/A")
            with col4:
                st.metric("Confidence", f"{confidence:.1f}/10" if confidence else "N/A")
        else:
            # Show only 3 columns when ATTOM is disabled/unavailable
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RentCast Estimate", f"${rentcast_val:,.0f}" if rentcast_val else "N/A")
            with col2:
                st.metric("Triangulated Value", f"${triangulated:,.0f}" if triangulated else "N/A")
            with col3:
                st.metric("Confidence", f"{confidence:.1f}/10" if confidence else "N/A")

        # Forecast
        fc = val_data.get('forecast', {})
        if fc:
            st.markdown("### Property Valuation Projection")
            col1, col2, col3 = st.columns(3)

            with col1:
                y1 = fc.get('1_year', {})
                st.metric(
                    "1-Year Forecast",
                    f"${y1.get('value', 0):,.0f}",
                    delta=f"{y1.get('change_pct', 0):+.1f}%"
                )

            with col2:
                y3 = fc.get('3_year', {})
                st.metric(
                    "3-Year Forecast",
                    f"${y3.get('value', 0):,.0f}",
                    delta=f"{y3.get('change_pct', 0):+.1f}%"
                )

            with col3:
                y5 = fc.get('5_year', {})
                st.metric(
                    "5-Year Forecast",
                    f"${y5.get('value', 0):,.0f}",
                    delta=f"{y5.get('change_pct', 0):+.1f}%"
                )

        # Rental analysis
        ra = val_data.get('rental_analysis', {})
        if ra:
            st.markdown("### Investment Analysis")
            col1, col2, col3 = st.columns(3)

            with col1:
                rent = ra.get('estimated_rent_monthly', 0)
                st.metric("Est. Monthly Rent", f"${rent:,.0f}" if rent else "N/A")

            with col2:
                gross_yield = ra.get('gross_yield_pct', 0)
                st.metric("Gross Yield", f"{gross_yield:.1f}%" if gross_yield else "N/A")

            with col3:
                cash_flow = ra.get('cash_flow_potential', 'N/A')
                st.metric("Cash Flow", cash_flow)

        # Comparable sales - Professional table with quality assessment
        comps = val_data.get('comparable_sales', [])
        subject_sqft = sqft or 0  # Subject property sqft for similarity calculation

        if comps:
            with st.expander(f"📋 Comparable Sales ({len(comps)} properties)", expanded=True):
                # Calculate quality scores and build display data
                display_data = []
                for comp in comps:
                    # Quality score calculation
                    quality_scores = []

                    # Distance score: <0.5mi=3, <1mi=2, <2mi=1, >2mi=0
                    dist = comp.get('distance_miles', 99)
                    if dist < 0.5:
                        dist_score = 3
                    elif dist < 1.0:
                        dist_score = 2
                    elif dist < 2.0:
                        dist_score = 1
                    else:
                        dist_score = 0
                    quality_scores.append(dist_score)

                    # Sqft similarity: within 20%=3, 20-40%=2, >40%=1
                    comp_sqft = comp.get('sqft', 0)
                    if subject_sqft > 0 and comp_sqft > 0:
                        sqft_diff_pct = abs(comp_sqft - subject_sqft) / subject_sqft * 100
                        if sqft_diff_pct <= 20:
                            sqft_score = 3
                        elif sqft_diff_pct <= 40:
                            sqft_score = 2
                        else:
                            sqft_score = 1
                    else:
                        sqft_score = 1  # Unknown = fair
                    quality_scores.append(sqft_score)

                    # Sale recency: <6mo=3, 6-12mo=2, >12mo=1
                    sale_date_str = comp.get('sale_date', '')
                    if sale_date_str:
                        try:
                            # Try common date formats
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                                try:
                                    sale_date = datetime.strptime(sale_date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                sale_date = None

                            if sale_date:
                                months_ago = (datetime.now() - sale_date).days / 30
                                if months_ago <= 6:
                                    recency_score = 3
                                elif months_ago <= 12:
                                    recency_score = 2
                                else:
                                    recency_score = 1
                            else:
                                recency_score = 1
                        except Exception:
                            recency_score = 1
                    else:
                        recency_score = 1
                    quality_scores.append(recency_score)

                    # Calculate overall quality (average, then map to label)
                    avg_score = sum(quality_scores) / len(quality_scores)
                    if avg_score >= 2.5:
                        quality_label = "Excellent"
                    elif avg_score >= 1.8:
                        quality_label = "Good"
                    else:
                        quality_label = "Fair"

                    # Format sale date for display (MMM YYYY)
                    display_date = sale_date_str
                    if sale_date_str:
                        try:
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                                try:
                                    parsed = datetime.strptime(sale_date_str, fmt)
                                    display_date = parsed.strftime('%b %Y')
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass

                    # Format beds/baths
                    beds = comp.get('bedrooms')
                    baths = comp.get('bathrooms')
                    if beds and baths:
                        beds_baths = f"{beds}bd/{baths}ba"
                    elif beds:
                        beds_baths = f"{beds}bd"
                    elif baths:
                        beds_baths = f"{baths}ba"
                    else:
                        beds_baths = "—"

                    display_data.append({
                        'Address': comp.get('address', 'N/A'),
                        'Subdivision': comp.get('subdivision') or '—',
                        'Price': f"${comp.get('sale_price', 0):,.0f}",
                        'Sale Date': display_date or '—',
                        'Sqft': f"{comp_sqft:,}" if comp_sqft else '—',
                        '$/Sqft': f"${comp.get('price_per_sqft', 0):,.0f}" if comp.get('price_per_sqft') else '—',
                        'Year': comp.get('year_built') or '—',
                        'Beds/Baths': beds_baths,
                        'Distance': f"{dist:.2f} mi",
                        'Quality': quality_label,
                        '_sort_score': avg_score  # Hidden sort column
                    })

                # Sort by quality (best first)
                display_data.sort(key=lambda x: x['_sort_score'], reverse=True)

                # Remove sort column before display
                for row in display_data:
                    del row['_sort_score']

                # Create DataFrame and display
                df = pd.DataFrame(display_data)

                # Style the quality column with colors
                def style_quality(val):
                    if val == 'Excellent':
                        return 'background-color: #d4edda; color: #155724'
                    elif val == 'Good':
                        return 'background-color: #fff3cd; color: #856404'
                    else:
                        return 'background-color: #f8d7da; color: #721c24'

                # Apply styling and display
                styled_df = df.style.applymap(style_quality, subset=['Quality'])
                st.dataframe(
                    styled_df,
                    width='stretch',
                    hide_index=True,
                    height=min(400, 50 + len(display_data) * 35)  # Dynamic height
                )

                # Quality score legend
                st.caption("**Quality Score:** Based on distance (<0.5mi best), size similarity (within 20% best), and sale recency (<6 months best)")
                st.caption("*Comparable property square footage from tax records. May exclude finished basements. All comps measured consistently for fair comparison.*")

    except Exception as e:
        st.error(f"Valuation error: {e}")

    st.markdown("---")


# =============================================================================
# SECTION: AI ANALYSIS
# =============================================================================

def _generate_power_line_narrative(power_lines: Dict[str, Any]) -> str:
    """
    Generate power infrastructure narrative in direct coffee-chat style.

    No hedging, no weasel words. State facts clearly with specific numbers.
    Acknowledge concerns honestly without dismissing or exaggerating.
    """
    if not power_lines or 'error' in power_lines:
        return ""

    impact_score = power_lines.get('visual_impact_score', 1)
    impact_level = power_lines.get('visual_impact_level', 'None')
    nearest_built = power_lines.get('nearest_built_line')
    nearest_approved = power_lines.get('nearest_approved_line')
    lines_within_mile = power_lines.get('lines_within_one_mile', 0)

    # No impact - brief mention
    if impact_score == 1:
        narrative = "Power infrastructure: Standard residential electrical service. No major transmission lines within a mile."
        if nearest_approved:
            voltage = nearest_approved['voltage']
            dist = nearest_approved['distance_miles']
            narrative += f" Note: A {voltage}kV line is approved at {dist:.1f} miles - not yet built."
        return narrative

    # Get key details
    if not nearest_built:
        return ""

    voltage = nearest_built['voltage']
    dist = nearest_built['distance_miles']
    feet = int(dist * 5280)

    # Very High impact (score 5) - 500kV very close or 230kV extremely close
    if impact_score == 5:
        if voltage >= 500:
            narrative = f"Let's talk about the big one: there's a {voltage}kV ultra-high-voltage transmission line {dist:.2f} miles away - that's about {feet:,} feet. This is serious regional grid infrastructure, not your standard power line. You'll see it from the property. The EMF concerns are real in buyers' minds, even if utilities maintain safety standards. Trade-off to consider. Some buyers walk away, some don't care. Know what you're getting."
        else:
            narrative = f"Power infrastructure: {voltage}kV transmission line sits {dist:.2f} miles out ({feet:,} feet). That's close. At this distance, the towers and lines are visible. Some buyers factor this into their decision, some don't. Be aware of it."

    # High impact (score 4)
    elif impact_score == 4:
        narrative = f"Power infrastructure context: {voltage}kV transmission line at {dist:.2f} miles ({feet:,} feet). Close enough that you might notice it, especially in winter when trees are bare. Part of Loudoun's electrical grid supporting residential and commercial development. Worth a drive-by to see the actual visual impact from the property."

    # Moderate impact (score 3)
    elif impact_score == 3:
        narrative = f"Power infrastructure: {voltage}kV line sits {dist:.2f} miles out. You probably won't see it day-to-day from the house. It's part of Loudoun's electrical grid serving residential and commercial development. At this distance, most buyers don't think twice about it."

    # Low impact (score 2)
    else:
        narrative = f"Power infrastructure: {voltage}kV transmission line at {dist:.1f} miles. Far enough that it's not a visual or practical concern for most buyers."

    # Add context about multiple lines if relevant
    if lines_within_mile > 1:
        narrative += f" There are {lines_within_mile} transmission lines within a mile of this property - this is part of a developed infrastructure corridor."

    # Add future line info (differentiator!)
    if nearest_approved:
        app_voltage = nearest_approved['voltage']
        app_dist = nearest_approved['distance_miles']
        narrative += f"\n\nHeads-up on future infrastructure: There's an approved {app_voltage}kV line planned {app_dist:.2f} miles from this property. Construction timeline unknown, but it's officially in the pipeline. Won't be there when you move in, but it's coming. If you're thinking 10+ years, factor that in."

    # Data center corridor context for high voltage lines in Ashburn area
    if voltage >= 230 and lines_within_mile >= 2:
        narrative += " This infrastructure is part of the electrical backbone supporting Loudoun's position as a global data center hub - the reason the county has world-class fiber infrastructure and stable tech employment."

    return narrative


def display_ai_analysis(
    address: str,
    coords: Tuple[float, float],
    schools_info: Optional[Dict[str, str]] = None,
    valuation_result: Optional[Dict[str, Any]] = None,
    development_2mi: Optional[Dict[str, Any]] = None,
    development_5mi: Optional[Dict[str, Any]] = None,
    demographics: Optional[Dict[str, Any]] = None
):
    """
    Display AI-powered property analysis narrative using Claude API.

    Args:
        address: Full property address
        coords: (latitude, longitude) tuple
        schools_info: Dict with school assignments {elementary, middle, high}
        valuation_result: Dict from property_valuation_orchestrator.analyze_property()
        development_2mi: Dict from analyze_development() with 2mi radius
        development_5mi: Dict from analyze_development() with 5mi radius
        demographics: Dict from calculate_demographics() with Census data
    """
    st.markdown("## 🤖 AI Property Analysis")

    # Session state key for retry functionality
    narrative_key = f"narrative_{address}"

    def generate_narrative():
        """Generate narrative using Claude API."""
        try:
            # Compile all available data
            compiled_data = compile_narrative_data(
                address=address,
                coords=coords,
                sqft=None,  # Intentionally None - not solving basement problem for demo
                schools_info=schools_info,
                valuation_result=valuation_result,
                development_2mi=development_2mi,
                development_5mi=development_5mi,
                demographics=demographics
            )

            # Generate narrative via Claude API
            narrative_result = generate_property_narrative(compiled_data, use_cache=True)
            return narrative_result

        except Exception as e:
            return {'error': str(e)}

    # Check if we need to generate or have cached result
    if narrative_key not in st.session_state or st.session_state.get(f"{narrative_key}_retry"):
        with st.spinner("Generating AI analysis..."):
            result = generate_narrative()
            st.session_state[narrative_key] = result
            st.session_state[f"{narrative_key}_retry"] = False

    result = st.session_state.get(narrative_key, {})

    # Handle errors gracefully
    if 'error' in result or not result.get('sections'):
        error_msg = result.get('error', 'Unknown error')
        metadata = result.get('metadata', {})
        api_error = metadata.get('error', '')

        st.warning("AI narrative temporarily unavailable. Please try again.")

        # Show error details in expander for debugging
        with st.expander("Error Details"):
            if api_error:
                st.text(f"API Error: {api_error}")
            if error_msg and error_msg != api_error:
                st.text(f"Error: {error_msg}")

        # Retry button
        if st.button("🔄 Retry Narrative Generation", key="retry_narrative"):
            st.session_state[f"{narrative_key}_retry"] = True
            st.rerun()

        return

    # Extract sections
    sections = result.get('sections', {})
    metadata = result.get('metadata', {})

    # Helper to escape dollar signs (prevents LaTeX math mode interpretation)
    def escape_dollars(text: str) -> str:
        """Escape dollar signs to prevent Streamlit LaTeX interpretation."""
        return text.replace('$', '\\$') if text else text

    # Display the 6 narrative sections with proper formatting
    section_config = [
        ('what_stands_out', 'What Stands Out'),
        ('schools_reality', 'Schools'),
        ('daily_reality', 'The Daily Reality'),
        ('worth_knowing', 'Worth Knowing'),
        ('investment_lens', 'Development & Investment'),
        ('bottom_line', 'Bottom Line')
    ]

    for key, title in section_config:
        content = sections.get(key, '')
        if content:
            # Escape dollar signs before markdown rendering
            escaped_content = escape_dollars(content)
            st.markdown(f"**{title}:** {escaped_content}")
            st.markdown("")  # Add spacing between sections

    # Metadata footer (subtle)
    if metadata.get('cached'):
        st.caption("📦 Analysis from cache")
    else:
        st.caption("🤖 AI-generated analysis")

    st.markdown("---")


# =============================================================================
# SECTION: FOOTER
# =============================================================================

def display_footer():
    """Display data sources and footer."""
    st.markdown("## 📊 Data Sources")

    # Dynamic valuation source based on ATTOM availability
    valuation_source = "ATTOM Data Solutions, RentCast API" if ATTOM_CLIENT else "RentCast API"

    st.markdown(f"""
| Category | Source |
|----------|--------|
| Property Valuation | {valuation_source} |
| Area Demographics | U.S. Census Bureau - American Community Survey 2019-2023 |
| Monthly Unemployment | Bureau of Labor Statistics - Local Area Unemployment Statistics |
| Labor Force Participation | U.S. Census Bureau - ACS 5-Year Estimates |
| Industry Employment | U.S. Census Bureau - ACS 5-Year Estimates |
| Major Employers | Loudoun County ACFR (2008-2025) |
| Schools | Loudoun County Public Schools (LCPS) Boundaries |
| School Performance | Virginia Department of Education - SOL 5-Year Trends |
| Building Permits | Loudoun County Permit Portal (Apr 2024 - Present) |
| Traffic Volume | VDOT Bidirectional Traffic Volume Database |
| Metro Access | WMATA Silver Line Stations / Loudoun County GeoHub |
| Power Infrastructure | Loudoun County Major Power Lines (GIS) |
| Cell Towers | Loudoun County Telecom Towers (GIS) + FCC Registration Database |
| Medical Facilities | Loudoun County GIS, CMS Hospital Compare, Leapfrog Group |
| Pharmacies | Google Places API |
| Neighborhood Amenities | Google Places API (Real-time) |
| Travel Times | Google Distance Matrix API |
| Parks & Recreation | Google Places API |
| GIS Data | Loudoun County Official Shapefiles |
| Road Network | Loudoun Street Centerline GIS |
| Zoning | Loudoun County Zoning Districts (GIS) |
| Airport Zones | Airport Impact Overlay Districts (Jan 2023) |
| Flood Zones | FEMA Flood Insurance Rate Map (via Loudoun GIS) |
| Community Data | NewCo Private Research, RentCast API |

**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}

---

*Loudoun County Property Intelligence Platform*
*Professional Real Estate Analysis*
""")


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def analyze_property(address: str, lat: float, lon: float):
    """Main property analysis orchestrator."""

    # Progress tracking
    progress = st.progress(0)
    status = st.empty()

    # Collect all data
    data = {}

    try:
        # Schools (15%)
        status.text("⏳ Fetching school assignments...")
        progress.progress(15)
        # Pre-compute school assignments for AI narrative
        data['schools'] = find_assigned_schools(lat, lon)

        # Location (30%)
        status.text("⏳ Analyzing location quality...")
        progress.progress(30)
        data['location'] = analyze_location_quality(lat, lon, address)

        # Power Lines (40%)
        status.text("⏳ Checking power infrastructure...")
        progress.progress(40)
        data['power_lines'] = analyze_power_line_proximity(lat, lon)

        # Cell Towers (42%)
        status.text("⏳ Analyzing cell tower coverage...")
        progress.progress(42)
        data['cell_towers'] = analyze_cell_tower_coverage(lat, lon)

        # Metro Access (45%)
        status.text("⏳ Analyzing Metro access...")
        progress.progress(45)
        data['metro'] = analyze_metro_access((lat, lon))

        # Flood Zone Check (47%)
        status.text("⏳ Checking flood zone status...")
        progress.progress(47)
        data['flood_zone'] = check_flood_zone(lat, lon)

        # Parks Proximity (48%)
        status.text("⏳ Finding nearby parks...")
        progress.progress(48)
        parks_static_data = load_parks_data()
        data['parks'] = get_nearest_parks(lat, lon, parks_static_data)

        # Neighborhood Amenities (50%)
        status.text("⏳ Discovering neighborhood amenities...")
        progress.progress(50)
        data['neighborhood'] = analyze_neighborhood((lat, lon))

        # Development - Dual Radius (60%)
        status.text("⏳ Analyzing development activity (2mi + 5mi)...")
        progress.progress(55)
        data['development_2mi'] = analyze_development(lat, lon, radius_miles=2.0)
        progress.progress(60)
        data['development_5mi'] = analyze_development(lat, lon, radius_miles=5.0)

        # Square Footage - DISABLED for demo
        # MLS web search unreliable (DuckDuckGo: bot detection, Brave: wrong results)
        # Using tax assessor data for consistency - will show as "Tax Records"
        # Future: Direct MLS API integration (Bridge/Zillow) post-demo
        status.text("⏳ Loading property details...")
        progress.progress(70)
        sqft_result = None  # Disabled - use ATTOM/tax records fallback
        data['sqft'] = sqft_result

        # Zoning (75%)
        status.text("⏳ Checking zoning...")
        progress.progress(75)
        # Get zoning data and store in data dict for AI Summary
        data['zoning'] = analyze_property_zoning_loudoun(lat, lon)

        # Valuation (85%)
        data['valuation'] = None
        if VALUATION_AVAILABLE:
            status.text("⏳ Fetching valuations...")
            progress.progress(85)
            # Pre-compute valuation for AI narrative
            try:
                orchestrator = PropertyValuationOrchestrator()
                data['valuation'] = orchestrator.analyze_property(address, lat, lon, None)
            except Exception as val_err:
                # Valuation failure shouldn't block the whole analysis
                data['valuation'] = None

        # Complete
        progress.progress(100)
        status.text("✓ Analysis complete!")

        # Clear progress indicators
        progress.empty()
        status.empty()

        # Display all sections
        st.success(f"✓ Analysis complete for: **{address}**")
        st.markdown("---")

        # Schools (uses pre-computed assignments)
        display_schools_section(lat, lon)

        # Location Quality
        display_location_section(data['location'], data.get('power_lines', {}), data.get('metro', {}), data.get('flood_zone', {}), data.get('parks', {}), lat, lon)

        # Cell Tower Coverage
        display_cell_towers_section(lat, lon)

        # Neighborhood Amenities
        display_neighborhood_section(data.get('neighborhood', {}))

        # Community & HOA Information
        display_community_section(data.get('valuation', {}), lat, lon)

        # Area Demographics (Census data)
        demographics_data = None
        if DEMOGRAPHICS_AVAILABLE:
            st.markdown("## 📈 Area Demographics")
            demographics_data = calculate_demographics(lat, lon, address)
            display_demographics_section(demographics_data, st)

        # Economic Indicators (LFPR, Industry Mix, Major Employers)
        if ECONOMIC_INDICATORS_AVAILABLE:
            display_economic_indicators_section()

        # Medical Access (Hospitals, Urgent Care, Maternity)
        display_medical_access_section(lat, lon)

        # Development & Infrastructure (uses 2mi data from display_development_section)
        display_development_section(lat, lon)

        # Zoning
        display_zoning_section(address, lat, lon)

        # Valuation (now includes MLS sqft lookup)
        display_valuation_section(address, lat, lon, sqft_result)

        # AI Analysis - pass all pre-computed data including demographics
        display_ai_analysis(
            address=address,
            coords=(lat, lon),
            schools_info=data.get('schools'),
            valuation_result=data.get('valuation'),
            development_2mi=data.get('development_2mi'),
            development_5mi=data.get('development_5mi'),
            demographics=demographics_data
        )

        # Footer
        display_footer()

    except Exception as e:
        st.error(f"Analysis failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


def geocode_address(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address using Google Maps Geocoding API.

    Args:
        address: Full address string
        api_key: Google Maps API key

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    if not address or not api_key:
        return None

    try:
        # Google Maps Geocoding API endpoint
        url = "https://maps.googleapis.com/maps/api/geocode/json"

        params = {
            'address': address,
            'key': api_key
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']

            # Validate coordinates are in Virginia/Maryland area (rough bounds)
            if 37.0 <= lat <= 40.0 and -80.0 <= lng <= -75.0:
                return (lat, lng)
            else:
                st.warning(f"Address geocoded outside expected area: {lat}, {lng}")
                return None
        else:
            st.warning(f"Geocoding failed: {data.get('status', 'Unknown error')}")
            return None

    except requests.exceptions.Timeout:
        st.error("Geocoding request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Geocoding error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected geocoding error: {str(e)}")
        return None


def main():
    """Main entry point."""

    # Header with dark mode toggle in top-right
    header_col, toggle_col = st.columns([6, 1])
    with header_col:
        st.title("🏘️ Loudoun County Property Intelligence")
    with toggle_col:
        # Small toggle for dark/light mode
        dark_mode = st.toggle("🌙", value=st.session_state['dark_mode'], help="Toggle dark/light mode")
        if dark_mode != st.session_state['dark_mode']:
            st.session_state['dark_mode'] = dark_mode
            st.rerun()
    st.markdown("### Professional Real Estate Analysis")
    st.markdown("---")

    # Initialize session state
    if 'analyzed' not in st.session_state:
        st.session_state['analyzed'] = False

    # Input section
    address = st.text_input(
        "Enter a Loudoun County address:",
        placeholder="e.g., 43500 Tuckaway Pl, Leesburg, VA 20176",
        help="Enter the complete property address including city, state, and ZIP"
    )

    # Auto-geocode address when available
    geocoded_coords = None
    if address and GOOGLE_MAPS_KEY:
        geocoded_coords = geocode_address(address, GOOGLE_MAPS_KEY)
        if geocoded_coords:
            st.success(f"✓ Address geocoded: {geocoded_coords[0]:.6f}, {geocoded_coords[1]:.6f}")

    # Set coordinates from geocoding or use defaults
    if geocoded_coords:
        lat, lon = geocoded_coords
    else:
        lat, lon = 39.112665, -77.495668  # Default to River Creek

    # Analyze button
    if st.button("🔍 Analyze Property", type="primary", width='stretch'):
        # Clear previous analysis to ensure fresh results
        st.session_state['analyzed'] = False

        if address:
            # Store new analysis parameters
            st.session_state['analyzed'] = True
            st.session_state['address'] = address
            st.session_state['lat'] = lat
            st.session_state['lon'] = lon
        else:
            st.warning("Please enter an address to analyze.")

    # Run analysis if triggered AND inputs still match (prevents stale results)
    if st.session_state.get('analyzed'):
        # Check if current inputs match what was analyzed
        stored_lat = st.session_state.get('lat')
        stored_lon = st.session_state.get('lon')

        # Only show results if coordinates match (user hasn't changed them)
        if lat == stored_lat and lon == stored_lon:
            analyze_property(
                st.session_state['address'],
                st.session_state['lat'],
                st.session_state['lon']
            )
        else:
            # Coordinates changed - clear stale results and prompt re-analysis
            st.session_state['analyzed'] = False
            st.info("📍 Coordinates have changed. Click 'Analyze Property' to analyze the new location.")


if __name__ == "__main__":
    main()
