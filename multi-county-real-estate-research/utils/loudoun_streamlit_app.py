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

# Core imports
from core.location_quality_analyzer import LocationQualityAnalyzer
from core.loudoun_zoning_analysis import analyze_property_zoning_loudoun
from core.loudoun_utilities_analysis import analyze_power_line_proximity
from core.mls_sqft_lookup import get_mls_sqft
from core.api_config import get_api_key

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


# =============================================================================
# DATA PATHS
# =============================================================================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'loudoun')
SCHOOLS_DIR = os.path.join(DATA_DIR, 'schools')
PERMITS_DIR = os.path.join(DATA_DIR, 'building_permits')
GIS_DIR = os.path.join(DATA_DIR, 'gis')


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
                st.caption(f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%")

    with col2:
        st.metric("Middle School", assignments['middle'] or "N/A")
        if assignments['middle']:
            perf = get_school_performance(assignments['middle'], performance_df)
            if perf:
                st.caption(f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%")

    with col3:
        st.metric("High School", assignments['high'] or "N/A")
        if assignments['high']:
            perf = get_school_performance(assignments['high'], performance_df)
            if perf:
                st.caption(f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%")

    # Performance charts
    if PLOTLY_AVAILABLE and not performance_df.empty:
        st.markdown("### School Performance Trends")

        tab1, tab2 = st.tabs(["Reading Proficiency", "Math Proficiency"])

        with tab1:
            # Get trend data for assigned schools
            chart_data = []
            for level, school in assignments.items():
                if school:
                    school_data = performance_df[
                        performance_df['School_Name'].str.contains(school.split()[0], case=False, na=False)
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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("School performance trend data not available for assigned schools.")

        with tab2:
            chart_data = []
            for level, school in assignments.items():
                if school:
                    school_data = performance_df[
                        performance_df['School_Name'].str.contains(school.split()[0], case=False, na=False)
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
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("School performance trend data not available for assigned schools.")

    st.markdown("---")


# =============================================================================
# SECTION: LOCATION QUALITY
# =============================================================================

def analyze_location_quality(lat: float, lon: float, address: str) -> Dict[str, Any]:
    """Analyze location quality using GIS data."""
    try:
        analyzer = LocationQualityAnalyzer(gis_data_path=GIS_DIR)
        return analyzer.analyze_location(lat, lon, address)
    except Exception as e:
        return {'error': str(e)}


def display_location_section(location_data: Dict[str, Any], power_lines: Dict[str, Any] = None):
    """Display location quality summary."""
    st.markdown("## 📍 Location Quality")

    if power_lines is None:
        power_lines = {}

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

        # Highway access
        hw = location_data.get('nearest_highway', {})
        if isinstance(hw, dict) and hw.get('name'):
            highlights.append(f"🚗 **Highway Access:** {hw.get('name')} ({hw.get('distance_mi', 0):.1f} mi)")

        # Airport zone
        aiod = location_data.get('aiod_status', {})
        if isinstance(aiod, dict):
            if aiod.get('in_aiod'):
                zone = aiod.get('zone', 'Unknown')
                highlights.append(f"✈️ **Airport Zone:** {zone} - noise disclosure required")
            else:
                highlights.append("✅ **Airport Impact:** Outside noise overlay zones")

            dulles_dist = aiod.get('distance_to_dulles_miles', 0)
            if dulles_dist:
                highlights.append(f"🛫 **Dulles Airport:** {dulles_dist:.1f} miles")

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
# SECTION: DEVELOPMENT & INFRASTRUCTURE
# =============================================================================

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


def create_development_map(lat: float, lon: float, nearby_permits: pd.DataFrame) -> folium.Map:
    """Create Folium map with development activity."""
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles='cartodbpositron')

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

    # Permit markers (limit for performance)
    sample = nearby_permits.head(200)

    for _, permit in sample.iterrows():
        # Color by type
        if permit.get('is_datacenter'):
            color = 'red'
            icon_name = 'server'
        elif permit.get('is_fiber'):
            color = 'orange'
            icon_name = 'wifi'
        elif permit.get('is_infrastructure'):
            color = 'purple'
            icon_name = 'bolt'
        else:
            color = 'green'
            icon_name = 'building'

        cost = permit.get('Estimated Construction Cost', 0)
        desc = str(permit.get('Permit Description', 'N/A'))[:100]

        popup_html = f"""
        <b>{permit.get('Address', 'N/A')}</b><br>
        <b>Cost:</b> ${cost:,.0f}<br>
        <b>Type:</b> {permit.get('Permit Work Class', 'N/A')}<br>
        <b>Description:</b> {desc}...
        """

        folium.CircleMarker(
            location=[permit['Latitude'], permit['Longitude']],
            radius=6,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(m)

    return m


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
                    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


# =============================================================================
# SECTION: ZONING
# =============================================================================

def display_zoning_section(address: str, lat: float, lon: float):
    """Display zoning information with Place Types and development probability."""
    st.markdown("## 🏗️ Zoning & Land Use")

    try:
        # Get full zoning analysis (note: function only takes lat, lon)
        zoning_result = analyze_property_zoning_loudoun(lat, lon)

        if not zoning_result:
            st.warning("Unable to retrieve zoning data for this location.")
            return

        # Extract components
        jurisdiction = zoning_result.get('jurisdiction', 'LOUDOUN')
        town_name = zoning_result.get('town_name')
        current_zoning = zoning_result.get('current_zoning', {})
        place_type = zoning_result.get('place_type', {})
        dev_prob = zoning_result.get('development_probability', {})

        # Show jurisdiction if in a town
        if town_name:
            st.info(f"📍 This property is in the **Town of {town_name}** (incorporated)")

        # Row 1: Current Zoning and Place Type
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Current Zoning")
            if current_zoning.get('success'):
                zoning_code = current_zoning.get('zoning', 'N/A')
                zoning_desc = current_zoning.get('zoning_description', '')
                st.metric("Zoning District", zoning_code)
                if zoning_desc:
                    st.caption(zoning_desc)
            else:
                st.warning(f"Zoning data unavailable: {current_zoning.get('error', 'Unknown error')}")

        with col2:
            st.markdown("### Planned Place Type")
            if place_type.get('success'):
                place_name = place_type.get('place_type', 'N/A')
                policy_area = place_type.get('policy_area', '')
                st.metric("Place Type", place_name)
                if policy_area:
                    st.caption(f"Policy Area: {policy_area}")
            else:
                st.warning(f"Place type unavailable: {place_type.get('error', 'Unknown error')}")

        # Row 2: Development Probability Analysis
        if dev_prob.get('score') is not None:
            st.markdown("### 🔮 Development Probability Analysis")

            score = dev_prob['score']
            risk_level = dev_prob.get('risk_level', 'Unknown')

            # Color-coded risk indicator
            if risk_level == "Very High":
                risk_color = "🔴"
                delta_color = "inverse"
            elif risk_level == "High":
                risk_color = "🟠"
                delta_color = "inverse"
            elif risk_level == "Moderate":
                risk_color = "🟡"
                delta_color = "off"
            else:
                risk_color = "🟢"
                delta_color = "normal"

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                st.metric(
                    f"{risk_color} Development Score",
                    f"{score}/100"
                )

            with col2:
                st.metric(
                    "Risk Level",
                    risk_level
                )

            with col3:
                # Show basic facts only - full narrative goes in AI Summary section
                zoning_code = current_zoning.get('zoning', 'Unknown')
                place_name = place_type.get('place_type', 'Unknown') if place_type.get('success') else 'Unknown'
                st.markdown(f"**Current Status:**")
                st.markdown(f"- Zoned: {zoning_code}")
                st.markdown(f"- Place Type: {place_name}")
                st.caption("*See AI Property Analysis Summary below for detailed development analysis*")

            # Score adjustment note for Tier 2 towns
            if current_zoning.get('score_adjustment'):
                st.caption(f"⚠️ {current_zoning['score_adjustment']}")

        # Zoning Details Expander
        if current_zoning.get('success'):
            with st.expander("📋 Zoning Details"):
                # Allowed uses
                allowed_uses = current_zoning.get('allowed_uses', [])
                if allowed_uses:
                    st.markdown("**Permitted Uses:**")
                    for use in allowed_uses[:5]:
                        st.markdown(f"- {use}")

                # Lot requirements
                lot_requirements = current_zoning.get('lot_requirements', {})
                if lot_requirements:
                    st.markdown("**Lot Requirements:**")
                    st.markdown(f"- Min Lot Size: {lot_requirements.get('min_lot_size', 'N/A')}")
                    st.markdown(f"- Setbacks: {lot_requirements.get('setbacks', 'N/A')}")
                    st.markdown(f"- Max Height: {lot_requirements.get('max_height', 'N/A')}")

                # Special notes
                if current_zoning.get('note'):
                    st.info(current_zoning['note'])

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

            # Get lot size and ATTOM sqft fallback
            lot_size_acres = None
            attom_sqft = None
            if ATTOM_CLIENT:
                try:
                    property_data = ATTOM_CLIENT.get_property_detail(address)
                    if property_data:
                        if property_data.lot_size:
                            lot_size_acres = property_data.lot_size
                        if property_data.sqft:
                            attom_sqft = property_data.sqft
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

        # Current value
        cv = val_data.get('current_value', {})

        st.markdown("### Current Value Estimates")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            attom_val = cv.get('attom_estimate', 0)
            st.metric("ATTOM Estimate", f"${attom_val:,.0f}" if attom_val else "N/A")

        with col2:
            rentcast_val = cv.get('rentcast_estimate', 0)
            st.metric("RentCast Estimate", f"${rentcast_val:,.0f}" if rentcast_val else "N/A")

        with col3:
            triangulated = cv.get('triangulated_estimate', 0)
            st.metric("Triangulated Value", f"${triangulated:,.0f}" if triangulated else "N/A")

        with col4:
            confidence = cv.get('confidence_score', 0)
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
                    use_container_width=True,
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


def display_ai_analysis(address: str, data: Dict[str, Any]):
    """Display AI-powered property analysis narrative."""
    st.markdown("## 🤖 Property Analysis Summary")

    # Generate narrative from collected data
    location = data.get('location', {})

    # Road classification narrative
    road_class = location.get('road_classification', {})
    road_narrative = ""
    if isinstance(road_class, dict):
        classification = road_class.get('classification', 'residential street')
        traffic = road_class.get('traffic_level', 'moderate')
        road_narrative = f"The property is located on a {classification.lower()} with {traffic.lower()} traffic levels."

    # Airport narrative
    aiod = location.get('aiod_status', {})
    airport_narrative = ""
    if isinstance(aiod, dict):
        if aiod.get('in_aiod'):
            airport_narrative = f"The property falls within the {aiod.get('zone', 'airport')} zone, which may require noise disclosure."
        else:
            dulles_dist = aiod.get('distance_to_dulles_miles', 0)
            airport_narrative = f"Located {dulles_dist:.1f} miles from Dulles International Airport, outside any noise overlay zones."

    # Power infrastructure narrative (coffee chat style - direct, no hedging)
    power_lines = data.get('power_lines', {})
    power_narrative = _generate_power_line_narrative(power_lines)

    st.markdown(f"""
    ### Location Assessment

    {road_narrative} {airport_narrative}

    This Loudoun County location benefits from:
    - Access to major employment centers in the Dulles Technology Corridor
    - Proximity to world-class data center infrastructure
    - Strong public school system (LCPS)
    - Easy access to Washington D.C. metro area
    """)

    # Power infrastructure section (if relevant)
    if power_narrative:
        st.markdown("### Power Infrastructure")
        st.markdown(power_narrative)

    # Development & Growth Analysis - Rich permit-based narrative
    zoning_data = data.get('zoning', {})
    dev_prob = zoning_data.get('development_probability', {})
    interpretation = dev_prob.get('interpretation', '')

    # Only show if we have the rich narrative (>200 chars indicates full version)
    if interpretation and len(interpretation) > 200:
        st.markdown("### Development & Growth Analysis")
        st.markdown(interpretation)  # Full narrative, no truncation
        st.markdown("---")

    st.markdown("""
    ### Market Context

    Loudoun County consistently ranks among Virginia's most desirable residential markets,
    driven by high-paying tech sector jobs, excellent schools, and proximity to Washington D.C.
    The county's position as the world's largest data center market provides unique economic stability.

    ### Investment Considerations

    - **Appreciation Potential:** Loudoun's job growth and limited land supply support long-term appreciation
    - **Rental Demand:** Strong demand from tech workers and government contractors
    - **Infrastructure:** World-class fiber connectivity throughout the county
    """)

    st.markdown("---")


# =============================================================================
# SECTION: FOOTER
# =============================================================================

def display_footer():
    """Display data sources and footer."""
    st.markdown("## 📊 Data Sources")

    st.markdown(f"""
    | Category | Source |
    |----------|--------|
    | Property Valuation | ATTOM Data Solutions, RentCast API |
    | Schools | Loudoun County Public Schools (LCPS), Virginia DOE |
    | Building Permits | Loudoun County (Apr 2024 - Present) |
    | GIS Data | Loudoun County Official Shapefiles |
    | Road Network | Loudoun Street Centerline GIS |
    | Airport Zones | Airport Impact Overlay Districts |

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
        # Schools (20%)
        status.text("⏳ Fetching school assignments...")
        progress.progress(20)

        # Location (40%)
        status.text("⏳ Analyzing location quality...")
        progress.progress(40)
        data['location'] = analyze_location_quality(lat, lon, address)

        # Power Lines (50%)
        status.text("⏳ Checking power infrastructure...")
        progress.progress(50)
        data['power_lines'] = analyze_power_line_proximity(lat, lon)

        # Development (60%)
        status.text("⏳ Analyzing development activity...")
        progress.progress(60)

        # Square Footage - DISABLED for demo
        # MLS web search unreliable (DuckDuckGo: bot detection, Brave: wrong results)
        # Using tax assessor data for consistency - will show as "Tax Records"
        # Future: Direct MLS API integration (Bridge/Zillow) post-demo
        status.text("⏳ Loading property details...")
        progress.progress(70)
        sqft_result = None  # Disabled - use ATTOM/tax records fallback
        data['sqft'] = sqft_result

        # Zoning (80%)
        status.text("⏳ Checking zoning...")
        progress.progress(80)
        # Get zoning data and store in data dict for AI Summary
        data['zoning'] = analyze_property_zoning_loudoun(lat, lon)

        # Valuation (90%)
        if VALUATION_AVAILABLE:
            status.text("⏳ Fetching valuations...")
            progress.progress(90)

        # Complete
        progress.progress(100)
        status.text("✓ Analysis complete!")

        # Clear progress indicators
        progress.empty()
        status.empty()

        # Display all sections
        st.success(f"✓ Analysis complete for: **{address}**")
        st.markdown("---")

        # Schools
        display_schools_section(lat, lon)

        # Location Quality
        display_location_section(data['location'], data.get('power_lines', {}))

        # Development & Infrastructure
        display_development_section(lat, lon)

        # Zoning
        display_zoning_section(address, lat, lon)

        # Valuation (now includes MLS sqft lookup)
        display_valuation_section(address, lat, lon, sqft_result)

        # AI Analysis
        display_ai_analysis(address, data)

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

    # Header
    st.title("🏘️ Loudoun County Property Intelligence")
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

    # Coordinates - auto-populated from geocoding or manual entry
    with st.expander("📍 Advanced: Manual Coordinates"):
        if geocoded_coords:
            st.caption("Coordinates auto-detected from address. Override below if needed.")
            default_lat, default_lon = geocoded_coords
        else:
            if address and not GOOGLE_MAPS_KEY:
                st.caption("⚠️ Google Maps API key not configured. Enter coordinates manually.")
            else:
                st.caption("Enter coordinates manually or provide an address for auto-detection.")
            default_lat, default_lon = 39.112665, -77.495668  # Default to River Creek

        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            lat = st.number_input("Latitude", value=default_lat, format="%.6f")
        with coord_col2:
            lon = st.number_input("Longitude", value=default_lon, format="%.6f")

    # Analyze button
    if st.button("🔍 Analyze Property", type="primary", use_container_width=True):
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
