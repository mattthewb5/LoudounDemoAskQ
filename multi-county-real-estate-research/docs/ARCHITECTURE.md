# System Architecture

## Executive Summary

The Loudoun County Property Intelligence Platform is built on a modular Python architecture using Streamlit for the web interface. The system follows a data-centric design where a main application (`loudoun_streamlit_app.py`) orchestrates 33 specialized modules in the `/core` directory, each responsible for a specific data source or analysis capability. This separation allows independent development and testing of each data integration while maintaining a unified user experience.

The architecture prioritizes three key qualities:

1. **Performance**: Aggressive caching at multiple levels (session, 7-day TTL, 24-hour TTL, indefinite) reduces API costs and enables sub-5-second response times despite integrating 18 external data sources
2. **Resilience**: Fallback data sources when primary sources fail—if ATTOM is unavailable, RentCast provides backup; if MLS sqft fails, ATTOM tax records provide fallback
3. **Extensibility**: Configuration-driven county-specific implementations that can be replicated for new geographic markets

The platform processes a user-provided address through a pipeline: geocoding to coordinates, parallel data fetching from multiple APIs and GIS services, spatial analysis and scoring algorithms, and finally AI-powered narrative synthesis that combines all data into coherent intelligence.

---

## System Overview

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Rapid prototyping web UI with built-in widgets, dark/light mode |
| **Visualization** | Plotly, Folium | Interactive charts and maps |
| **Spatial Analysis** | GeoPandas, Shapely | GIS operations, point-in-polygon, distance calculations |
| **Data Processing** | Pandas | Data manipulation, aggregation, filtering |
| **File Formats** | Parquet, GeoJSON, CSV, JSON | Optimized storage (Parquet 105x faster than Excel) |
| **API Clients** | Requests | HTTP integrations with external services |
| **AI Integration** | Anthropic Claude API | Narrative synthesis |
| **Caching** | Streamlit @st.cache_data, file-based | Multi-level performance optimization |

### Application Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      loudoun_streamlit_app.py                        │
│                         (Main Application)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Sidebar   │  │   Sections  │  │    State    │  │   Theme    │ │
│  │   Input     │  │   Display   │  │    Mgmt     │  │   Toggle   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       ▼                       ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│  Valuation  │       │  Location   │       │    Narrative    │
│ Orchestrator│       │   Quality   │       │    Generator    │
└──────┬──────┘       └──────┬──────┘       └────────┬────────┘
       │                     │                       │
       ▼                     ▼                       ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│ ATTOM       │       │ County GIS  │       │   Claude API    │
│ RentCast    │       │ FCC, VDOT   │       │                 │
│ Sales Data  │       │ WMATA       │       │                 │
└─────────────┘       └─────────────┘       └─────────────────┘
```

### Data Flow Pipeline

```
1. Address Input
   └─> User enters address in sidebar
       └─> "43422 Cloister Pl, Leesburg, VA 20176"

2. Geocoding
   └─> Google Maps Geocoding API
       └─> (lat: 39.0892, lon: -77.5034)

3. Parallel Data Fetching (concurrent)
   ├─> ATTOM: Property details, AVM, comparable sales
   ├─> RentCast: Value estimate, rent estimate, subdivision
   ├─> Census: Block group demographics for 1mi/3mi radii
   ├─> BLS: Unemployment rate, labor force
   ├─> County GIS: Zoning, flood, AIOD, school zones
   ├─> Schools: Zone boundaries + SOL performance data
   ├─> Permits: Nearby development activity
   ├─> Traffic: VDOT ADT volumes for nearby roads
   ├─> Metro: Distance to Silver Line stations
   └─> Community: HOA amenities lookup

4. Spatial Analysis & Scoring
   ├─> Development Pressure Score (0-100)
   ├─> Development Probability Score (0-100)
   ├─> School Percentiles (vs state)
   ├─> Metro Accessibility Tier
   ├─> Value Triangulation (confidence score)
   └─> Location Quality Factors

5. Display Rendering (progressive disclosure)
   ├─> Metrics (st.metric)
   ├─> Charts (Plotly)
   ├─> Tables (st.dataframe)
   ├─> Maps (Folium)
   └─> Expanders (detailed data)

6. AI Narrative Synthesis
   └─> Compiled data → Claude prompt → 6-section narrative
       └─> Cached for 24 hours
```

### Caching Architecture

The platform uses multi-level caching to balance freshness with performance:

| Cache Level | Mechanism | TTL | Use Case |
|-------------|-----------|-----|----------|
| **Session** | `@st.cache_data` (no TTL) | Session lifetime | GIS queries, static file loads |
| **7-Day** | `@st.cache_data(ttl=86400*7)` | 7 days | Census data, BLS data, RentCast property records |
| **24-Hour** | File-based JSON cache | 24 hours | Claude narratives (expensive to regenerate) |
| **Indefinite** | Static files | Manual update | Major employers, road context, community amenities |
| **Resource** | `@st.cache_resource` | App lifetime | Parquet DataFrames, GeoDataFrames |

```python
# Example: 7-day cached Census API call
@st.cache_data(ttl=86400*7)  # 604800 seconds = 7 days
def fetch_census_economic_data() -> Dict[str, Dict[str, Any]]:
    """Fetch LFPR and industry mix - cached 7 days since data is annual."""
    ...

# Example: Resource caching for expensive DataFrame loads
@st.cache_resource
def get_cached_loudoun_sales_data():
    """Load 47K sales records - cached for app lifetime."""
    return pd.read_parquet('data/loudoun/sales/combined_sales.parquet')
```

---

## Module Structure

The `/core` directory contains 33 specialized modules. Below are the key modules organized by function.

### API Client Modules

#### api_config.py

- **Purpose:** Centralized API key management and configuration
- **Key Functions:**
  - `get_api_key(key_name)` — Retrieves API key from JSON config file
  - `get_config_path()` — Returns path to config directory
- **Dependencies:** None (base module)
- **Data Sources:** Reads from `~/.config/newco/api_keys.json`
- **Caching:** None (reads config on demand)

#### attom_client.py

- **Purpose:** ATTOM Data API integration for property data and comparable sales
- **Key Functions:**
  - `get_property_detail(address)` — Property characteristics (beds, baths, sqft, year built)
  - `get_avm(address)` — Automated Valuation Model estimate
  - `get_comparable_sales(address, radius, months)` — Nearby sales within radius
  - `get_sales_history(address)` — Historical sales for specific property
- **Dependencies:** `api_config.py`
- **Data Sources:** ATTOM REST API (api.gateway.attomdata.com)
- **Caching:** Session-based to reduce per-call costs

#### rentcast_client.py

- **Purpose:** RentCast API integration for rental estimates and property data
- **Key Functions:**
  - `get_rent_estimate(address)` — Monthly rent estimate with range
  - `get_value_estimate(address)` — Property value estimate
  - `get_property_records(address)` — Subdivision, HOA, property details
- **Dependencies:** `api_config.py`
- **Data Sources:** RentCast REST API (api.rentcast.io)
- **Caching:** 7-day TTL file-based cache (`cache/rentcast/`)

#### census_api.py

- **Purpose:** Census Bureau ACS and BLS LAUS API integration
- **Key Functions:**
  - `CensusClient.get_block_group_data(variables, state, county)` — ACS 5-year estimates
  - `BLSClient.get_county_unemployment(state, county)` — Current unemployment rate
  - `BLSClient.get_series_data(series_ids)` — Time series data
- **Dependencies:** `api_config.py`
- **Data Sources:** Census API (api.census.gov), BLS API v2 (api.bls.gov)
- **Caching:** 7-day TTL via `@st.cache_data(ttl=86400*7)`

### Analysis Modules

#### demographics_calculator.py

- **Purpose:** Calculate population-weighted demographics within radius
- **Key Functions:**
  - `calculate_demographics(lat, lon, address)` — 1-mile and 3-mile radius analysis
  - `fetch_block_group_centroids(state, county)` — Get centroids from TIGERweb
  - `haversine_distance(lat1, lon1, lat2, lon2)` — Distance calculation
- **Dependencies:** `census_api.py`
- **Data Sources:** Census ACS, TIGERweb block group centroids
- **Caching:** 7-day TTL for Census data

#### economic_indicators.py

- **Purpose:** Economic context: LFPR, industry mix, unemployment, major employers
- **Key Functions:**
  - `get_lfpr_data()` — Labor force participation with VA/USA comparison
  - `get_industry_mix_data()` — Sector employment percentages
  - `fetch_bls_data()` — Current unemployment from BLS LAUS
  - `load_major_employers()` — ACFR employer data (18 years)
  - `get_employer_trends()` — Summary of employer changes over time
- **Dependencies:** `census_api.py`
- **Data Sources:** Census DP03, BLS LAUS, `data/loudoun/major_employers.json`
- **Caching:** 7-day TTL for API data; `@st.cache_data` for static JSON

#### loudoun_school_performance.py

- **Purpose:** School assignment and performance trend analysis
- **Key Functions:**
  - `load_performance_data()` — SOL scores with state averages
  - `load_school_coordinates()` — School lat/lon for peer matching
  - `find_peer_schools(school, type, lat, lon, n)` — Nearest n peer schools
  - `normalize_school_name(name)` — Handle name variations
  - `haversine(lat1, lon1, lat2, lon2)` — Distance calculation
- **Dependencies:** None (uses static CSV files)
- **Data Sources:** `data/loudoun/school_performance_trends_with_state_avg.csv`
- **Caching:** Session-based for file loads

#### loudoun_zoning_analysis.py

- **Purpose:** Zoning analysis with comprehensive plan alignment scoring
- **Key Functions:**
  - `analyze_property_zoning_loudoun(lat, lon)` — Full zoning analysis
  - `get_place_type_loudoun(lat, lon)` — Comprehensive plan designation
  - `detect_jurisdiction(lat, lon)` — Town vs county detection
  - `get_current_zoning(lat, lon)` — Current zoning code
  - `calculate_development_probability(zoning, place_type)` — Gap score
- **Dependencies:** None (direct GIS queries)
- **Data Sources:** Loudoun County GIS layers (Zoning, Planning, CountyBoundary)
- **Caching:** Session-based for GIS queries

#### development_pressure_analyzer.py

- **Purpose:** Building permit analysis for development pressure scoring
- **Key Functions:**
  - `DevelopmentPressureAnalyzer.__init__(permits_csv)` — Load permits
  - `analyze_pressure(lat, lon, radius)` — Development pressure score
  - `haversine_distance(lat1, lon1, lat2, lon2)` — Distance calculation
- **Dependencies:** Pandas
- **Data Sources:** `data/loudoun/building_permits/` (geocoded CSV)
- **Caching:** Permit data loaded once per session

#### loudoun_traffic_volume.py

- **Purpose:** VDOT traffic volume lookups for ADT data
- **Key Functions:**
  - `LoudounTrafficVolumeAnalyzer.get_traffic_volume(road_name, lat, lon)` — ADT for road
  - `format_adt(value)` — Human-readable format (e.g., "45,000")
  - `point_to_line_distance(point, line_coords)` — Distance to road segment
- **Dependencies:** None (uses static GeoJSON)
- **Data Sources:** `data/loudoun/gis/traffic/vdot_traffic_volume.geojson`
- **Caching:** Data loaded once per session

#### loudoun_metro_analysis.py

- **Purpose:** Silver Line Metro proximity and accessibility tier analysis
- **Key Functions:**
  - `analyze_metro_access(lat, lon)` — Distance to all stations + tier
  - `get_nearest_station(lat, lon)` — Closest Metro station
  - `get_accessibility_tier(distance_miles)` — Classification
- **Dependencies:** None
- **Data Sources:** Hardcoded station coordinates (WMATA verified)
- **Caching:** None needed (fast calculation)

#### location_quality_analyzer.py

- **Purpose:** Multi-factor location quality analysis
- **Key Functions:**
  - `LocationQualityAnalyzer.analyze(lat, lon, address)` — Full analysis
  - `check_flood_zone(lat, lon)` — FEMA flood zone status
  - `check_aiod(lat, lon)` — Airport Impact Overlay District
  - `find_nearest_highways(lat, lon)` — Highway proximity
- **Dependencies:** GeoPandas, Shapely
- **Data Sources:** County GIS (AIOD, FEMAFlood), road shapefiles
- **Caching:** Session-based for shapefile loads

#### loudoun_utilities_analysis.py

- **Purpose:** Power line proximity analysis
- **Key Functions:**
  - `analyze_power_lines(lat, lon)` — Distance to nearest power line
  - `point_to_linestring_distance(point, coords)` — Minimum distance
  - `get_visual_impact_score(distance, voltage)` — 1-5 impact score
- **Dependencies:** None
- **Data Sources:** `data/loudoun/utilities/Major_Power_Lines.geojson`
- **Caching:** GeoJSON loaded once per session

#### loudoun_narrative_generator.py

- **Purpose:** AI-powered property narrative synthesis
- **Key Functions:**
  - `compile_narrative_data(address, coords, ...)` — Gather all data
  - `generate_property_narrative(compiled_data)` — Claude API call
  - `_get_cached_narrative(cache_key)` — Check file cache
  - `_save_narrative_to_cache(cache_key, narrative)` — Save to file cache
- **Dependencies:** Most other analysis modules, Anthropic API
- **Data Sources:** All platform data sources + Claude API
- **Caching:** 24-hour TTL file-based cache (`cache/narratives/`)

### Orchestration Modules

#### property_valuation_orchestrator.py

- **Purpose:** Unified property valuation interface
- **Key Functions:**
  - `PropertyValuationOrchestrator.analyze_property(address, lat, lon, sqft)` — Complete valuation
  - `_triangulate_values()` — Combine ATTOM, RentCast, tax assessment
  - `_get_sales_data()` — Lazy-load Parquet sales data
- **Dependencies:** `attom_client.py`, `rentcast_client.py`, `comparable_analyzer.py`, `forecast_engine.py`, `loudoun_sales_data.py`
- **Data Sources:** ATTOM, RentCast, County sales (Parquet)
- **Caching:** Orchestrates cached clients

#### loudoun_community_lookup.py

- **Purpose:** Community/HOA identification and amenity lookup
- **Key Functions:**
  - `CommunityLookup.get_community_for_subdivision(subdivision)` — Pattern matching
  - `normalize_subdivision_name(name)` — Handle variations
  - `_build_pattern_cache()` — Pre-compile patterns
- **Dependencies:** None
- **Data Sources:** `data/loudoun/config/communities.json`
- **Caching:** Pattern cache built on init

---

## Data Processing Pipeline

### Stage 1: Geocoding

```python
# Address → Coordinates via Google Maps
def geocode_address(address: str) -> Tuple[float, float]:
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": address, "key": API_KEY}
    )
    location = response.json()["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]
```

Fallback: If Google fails, ATTOM address lookup provides coordinates.

### Stage 2: Parallel Data Fetching

Multiple data sources are fetched concurrently for performance:

```python
import concurrent.futures

def fetch_all_data(lat, lon, address):
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_census_data, lat, lon): "census",
            executor.submit(fetch_zoning, lat, lon): "zoning",
            executor.submit(fetch_schools, lat, lon): "schools",
            executor.submit(fetch_permits, lat, lon): "permits",
            # ... more sources
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            results[key] = future.result()

        return results
```

### Stage 3: Spatial Analysis

Point-in-polygon for zone lookups:

```python
from shapely.geometry import Point
import geopandas as gpd

def get_school_assignment(lat, lon, zone_file):
    point = Point(lon, lat)  # GeoJSON uses lon, lat order
    zones = gpd.read_file(zone_file)

    for idx, zone in zones.iterrows():
        if zone.geometry.contains(point):
            return zone['school_name']

    return None
```

Radius-based aggregation for demographics:

```python
def get_block_groups_in_radius(lat, lon, radius_miles, centroids):
    nearby = []
    for _, centroid in centroids.iterrows():
        distance = haversine(lat, lon, centroid['lat'], centroid['lon'])
        if distance <= radius_miles:
            nearby.append(centroid['geoid'])
    return nearby
```

### Stage 4: Scoring Algorithms

Development Pressure Score (0-100):

```python
def calculate_development_pressure(permits, lat, lon, radius=2.0):
    nearby = filter_by_radius(permits, lat, lon, radius)

    # Components
    total_permits = len(nearby)
    total_value = nearby['construction_cost'].sum()
    new_construction_ratio = len(nearby[nearby['type'] == 'NEW']) / total_permits

    # Impact-weighted score
    impact_score = sum(
        IMPACT_SCORES.get(p['work_class'].lower(), 1)
        for p in nearby
    )

    # Normalize to 0-100
    score = min(100, (impact_score / 50) * 100)
    return score
```

### Stage 5: AI Narrative Generation

```python
def generate_narrative(compiled_data):
    system_prompt = """You are a local real estate expert...
    Return ONLY a JSON object with these 6 sections:
    {
        "what_stands_out": "...",
        "schools_reality": "...",
        "daily_reality": "...",
        "worth_knowing": "...",
        "investment_lens": "...",
        "bottom_line": "..."
    }
    """

    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": json.dumps(compiled_data)}]
    )

    return json.loads(response.content[0].text)
```

---

## Configuration Architecture

### County-Specific Configuration

The platform is designed for multi-county expansion:

```
config/
├── base_config.py      # Abstract base class defining interface
└── loudoun.py          # Loudoun County implementation
```

Each county implementation provides:
- GIS endpoint URLs
- School zone boundary file paths
- Zoning code translations
- AI context prompts
- Local data file locations

### Adding New Counties

1. Research data sources (schools, zoning, permits, etc.)
2. Create `config/{county}.py` implementing `BaseCountyConfig`
3. Add county data files to `data/{county}/`
4. Create county-specific modules (e.g., `{county}_zoning_analysis.py`)
5. Update main app with county selector

See [adding_a_county.md](adding_a_county.md) for detailed guide.

### Feature Flags

Feature availability is controlled by import-time checks:

```python
# Economic Indicators availability
ECONOMIC_INDICATORS_AVAILABLE = False
try:
    from core.economic_indicators import (
        get_lfpr_data,
        get_industry_mix_data,
        load_major_employers,
        fetch_bls_data
    )
    ECONOMIC_INDICATORS_AVAILABLE = True
except Exception as e:
    print(f"Economic indicators import failed: {e}")

# Later in display code:
if ECONOMIC_INDICATORS_AVAILABLE:
    display_economic_indicators_section()
```

This pattern allows graceful degradation when modules or API keys are unavailable.

---

## Key Technical Decisions

### Why Streamlit?

- **Rapid Development**: Built-in UI components eliminate frontend development time
- **Python Native**: Data scientists work in familiar environment, no JavaScript
- **Interactive Widgets**: Metrics, charts, tables, forms with minimal code
- **Session State**: Easy state management for user interactions
- **Hot Reload**: Instant updates during development
- **Demo Speed**: Investor demos ready in days, not weeks

### Why Aggressive Caching?

External API costs and latency without caching:
- Census API: FREE but slow (~2-3 seconds per call)
- ATTOM: PAID per call (~$0.05-0.15)
- Claude: PAID per token (~$0.01 per narrative)
- GIS: FREE but network latency

7-day cache for stable data (Census, BLS) achieves:
- 80-90% reduction in API costs
- Page load from 15s to 3s (cached)
- Avoids rate limit exhaustion

### Why Progressive Disclosure UI?

18 data sources produce overwhelming information. Progressive disclosure:
- Shows key metrics immediately (st.metric)
- Hides details in expanders (st.expander)
- Organizes by user intent (valuation, schools, location)
- Professional appearance for investor demos

### Why Local GIS Extracts?

Live GIS API queries have disadvantages:
- Network dependency (fails if county server down)
- Latency per query (100-300ms each)
- Rate limiting concerns
- Version drift between queries

Local extracts (GeoJSON, Shapefile) provide:
- Offline reliability
- Sub-10ms query time
- Consistent data version
- Full control over updates

### Why Parquet for Sales Data?

Original Excel format (47K records):
- Load time: ~3 seconds
- Memory: ~150MB

Parquet format:
- Load time: ~0.03 seconds (105x faster)
- Memory: ~40MB
- Columnar filtering (read only needed columns)

---

## Performance Characteristics

### Typical Response Times

| Operation | Uncached | Cached | Notes |
|-----------|----------|--------|-------|
| Geocoding | 200ms | 200ms | Not cached (Google) |
| Census fetch | 2-3s | <10ms | 7-day TTL |
| GIS point queries | 100-300ms | 100-300ms | Session cache |
| ATTOM property | 500ms | 500ms | Session cache |
| Comparable sales | 1-2s | 1-2s | Depends on count |
| Sales data load | 3s (Excel) | 30ms (Parquet) | @st.cache_resource |
| Full page (uncached) | 8-15s | — | Parallel fetching helps |
| Full page (cached) | 2-4s | — | Most data cached |
| AI narrative (uncached) | 3-5s | <10ms | 24-hour file cache |

### Memory Usage

- Streamlit session baseline: ~50-100MB
- Loaded DataFrames: ~20-50MB (permits, schools, sales)
- GeoPandas files: ~10-30MB per GeoJSON
- Peak usage: ~200-300MB per session

---

*Last Updated: December 2025*
