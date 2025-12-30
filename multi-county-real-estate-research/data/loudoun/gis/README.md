# Loudoun County GIS Data

Geographic Information System (GIS) data for location quality analysis.

## Overview

**Data Layers:** Roads, Airport Impact Overlay Districts (AIOD), Power Lines
**Format:** Shapefiles (.shp) and GeoJSON (.json)
**Coordinate System:** EPSG:4326 (WGS84) for compatibility
**Source:** Loudoun County GIS Department
**Caching:** Streamlit @cache_resource for instant subsequent access

## Data Layers

### 1. Road Centerline (Loudoun_Street_Centerline.zip)

**Purpose:** Highway proximity analysis, major collector identification
**Format:** Shapefile (extracted to `roads/` subdirectory)
**Size:** 7.8 MB compressed
**Features:** ~25,000+ road segments county-wide

**Key Attributes:**
- `NAME` - Street name
- `TYPE` - Road classification
- Geometry - LineString coordinates

**Highway Patterns Identified:**
- Route 7: Leesburg Pike, Harry Byrd Highway
- Route 28: Sully Road
- Route 267: Dulles Access Road, Dulles Toll Road, Greenway
- Route 50: Lee Jackson Memorial Highway, John Mosby Highway
- Route 15: James Monroe Highway, King Street

**Major Collectors:**
- Loudoun County Parkway
- Waxpool Road
- Belmont Ridge Road
- Ashburn Village Boulevard
- Battlefield Parkway
- Sterling Boulevard
- River Creek Parkway
- And 10+ others

### 2. Airport Impact Overlay Districts (Loudoun_Airport_Impact_Overlay_Districts.zip)

**Purpose:** Airport noise/safety zone identification
**Format:** Shapefile (extracted to `aiod/` subdirectory)
**Size:** 111 KB compressed
**Features:** 3 overlay districts

**Districts:**
1. **AIOD-1** - Highest impact (close to Leesburg Executive Airport)
2. **AIOD-2** - Moderate impact
3. **AIOD-3** - Lower impact (outer safety zones)

**Key Attributes:**
- `ZONE` - District designation (AIOD-1, AIOD-2, AIOD-3)
- `DESCRIPTION` - Impact level and restrictions
- Geometry - Polygon boundaries

**Use Cases:**
- Property disclosure requirements
- Building height restrictions
- Noise impact assessment
- Buyer awareness and transparency

### 3. Major Power Lines (major_power_lines.json)

**Purpose:** High-voltage transmission line proximity analysis
**Format:** GeoJSON
**Size:** 50 KB
**Features:** 80 transmission line segments

**Attributes:**
- `voltage` - Transmission voltage (kV)
- `operator` - Utility company
- `type` - Line classification
- Geometry - LineString coordinates

**Impact Levels:**
- **Very High:** <100 feet from property
- **High:** 100-300 feet
- **Moderate:** 300-500 feet
- **Low:** 500-1000 feet
- **None:** >1000 feet

## Performance Metrics

### Before Optimization (Per-Property Loading)

| Layer | Load Time | Format | Issue |
|-------|-----------|--------|-------|
| Roads | 3-5 seconds | Shapefile | Repeated file I/O |
| AIOD | 1-2 seconds | Shapefile | Repeated coordinate transforms |
| Power Lines | 0.2 seconds | GeoJSON | Repeated JSON parsing |
| **Total** | **4-8 seconds** | Mixed | Inefficient for multi-property demos |

### After Optimization (Streamlit Caching)

| Layer | First Load | Cached Access | Speedup |
|-------|------------|---------------|---------|
| Roads | 3-5 seconds | ~0 seconds | Instant |
| AIOD | 1-2 seconds | ~0 seconds | Instant |
| Power Lines | 0.2 seconds | ~0 seconds | Instant |
| **Total** | **4-8 seconds** | **~0 seconds** | **∞** (instant) |

### Combined Impact (Sales + GIS)

**First Property Analysis:**
- Sales data: 2.83s
- GIS data: 4-8s
- Total: 7-11 seconds

**Subsequent Properties:**
- Sales data: ~0s (cached)
- GIS data: ~0s (cached)
- Total: <1 second

**Demo Experience:**
- Before: 90-150s per property (unusable for demos)
- After: 7-11s first property, instant thereafter (excellent UX)
- Improvement: 97% reduction in wait time

## Caching Architecture

### Streamlit @cache_resource Pattern

```python
@st.cache_resource
def get_cached_loudoun_roads():
    """
    Load roads once per Streamlit session.
    Subsequent properties use cached data.
    """
    return _load_roads_internal()

@st.cache_resource
def get_cached_loudoun_aiod():
    """Load AIOD zones once per session."""
    return _load_aiod_internal()

@st.cache_resource
def get_cached_loudoun_power_lines():
    """Load power lines once per session."""
    return _load_power_lines_internal()
```

### Why @cache_resource (not @cache_data)?

- **Resource:** GeoDataFrames, large objects, external data
- **Data:** Simple function outputs, serializable results
- **Benefit:** No serialization overhead, true object reuse
- **Lifecycle:** Persists until server restart or manual clear

### Analyzer Factory Pattern

```python
@st.cache_resource
def get_cached_location_analyzer():
    """
    Pre-loads all GIS data and creates analyzer instance.
    All properties share the same analyzer with cached data.
    """
    roads_data = get_cached_loudoun_roads()
    aiod_data = get_cached_loudoun_aiod()

    return LocationQualityAnalyzer(
        preloaded_data={'roads': roads_data, 'aiod': aiod_data}
    )
```

### Memory Efficiency

**Per-County Memory Usage:**
- Roads: ~15 MB (in-memory GeoDataFrame)
- AIOD: ~5 MB (polygon geometries)
- Power Lines: ~1 MB (line strings)
- **Total:** ~20 MB per county

**Multi-County Scaling:**
- 5 counties: ~100 MB (well within typical limits)
- Lazy loading: Only loaded counties consume memory
- Clean separation: Independent cache per county

## File Structure

```
gis/
├── README.md                                      # This file
├── Loudoun_Street_Centerline.zip                 # Raw shapefile (compressed)
├── Loudoun_Airport_Impact_Overlay_Districts.zip  # Raw shapefile (compressed)
├── roads/                                        # Extracted road shapefile
│   ├── Loudoun_Street_Centerline.shp
│   ├── Loudoun_Street_Centerline.shx
│   ├── Loudoun_Street_Centerline.dbf
│   ├── Loudoun_Street_Centerline.prj
│   └── ...
├── aiod/                                         # Extracted AIOD shapefile
│   ├── Loudoun_Airport_Impact_Overlay_Districts.shp
│   ├── Loudoun_Airport_Impact_Overlay_Districts.shx
│   ├── Loudoun_Airport_Impact_Overlay_Districts.dbf
│   ├── Loudoun_Airport_Impact_Overlay_Districts.prj
│   └── ...
├── traffic/                                      # Traffic count data
├── zoning/                                       # Zoning overlay data
└── flood/                                        # Flood zone data
```

## Usage

### In Streamlit App (Recommended)

```python
from core.loudoun_gis_data import (
    get_cached_loudoun_roads,
    get_cached_loudoun_aiod,
    get_cached_loudoun_power_lines
)

# Load data once per session (cached)
all_roads, highways, collectors = get_cached_loudoun_roads()
aiod_zones = get_cached_loudoun_aiod()
power_lines = get_cached_loudoun_power_lines()

# Use in analysis (instant for all properties)
from core.location_quality_analyzer import get_cached_location_analyzer

analyzer = get_cached_location_analyzer()
result = analyzer.analyze_location(latitude=39.0, longitude=-77.5)
```

### In Scripts (Non-Streamlit)

```python
from core.loudoun_gis_data import (
    _load_roads_internal,
    _load_aiod_internal,
    _load_power_lines_internal
)

# Direct loading (no caching)
all_roads, highways, collectors = _load_roads_internal()
aiod_zones = _load_aiod_internal()
power_lines = _load_power_lines_internal()
```

### Highway Proximity Check

```python
from core.location_quality_analyzer import LocationQualityAnalyzer

# Create analyzer with preloaded data (cached)
roads_data = get_cached_loudoun_roads()
analyzer = LocationQualityAnalyzer(
    preloaded_data={'roads': roads_data}
)

# Check highway proximity
result = analyzer.analyze_location(39.015, -77.475)

if result['near_highway']:
    print(f"Highway: {result['nearest_highway_name']}")
    print(f"Distance: {result['highway_distance_miles']:.2f} miles")
```

### AIOD Zone Check

```python
# Check if property is in airport overlay district
result = analyzer.analyze_location(39.015, -77.475)

if result['in_aiod']:
    print(f"Zone: {result['aiod_zone']}")
    print(f"Impact: {result['aiod_description']}")
```

### Power Line Analysis

```python
from core.loudoun_utilities_analysis import get_cached_power_line_analyzer

# Get cached analyzer
power_analyzer = get_cached_power_line_analyzer()

# Analyze proximity
result = power_analyzer.analyze_proximity(39.015, -77.475)

print(f"Impact: {result['impact_level']}")
print(f"Distance: {result['distance_feet']:.0f} feet")
print(f"Nearest line: {result['nearest_line_voltage']} kV")
```

## Data Update Procedures

### When to Update

- **Frequency:** Annually or when major infrastructure changes
- **Triggers:** New highways, road realignments, airport zone changes
- **Source:** Loudoun County GIS data portal

### Update Steps

#### 1. Download New Data

```bash
# Visit Loudoun County GIS portal
# https://data-loudoun.opendata.arcgis.com/

# Download new shapefiles:
# - Road_Centerline.zip
# - Airport_Impact_Overlay_Districts.zip
```

#### 2. Replace Files

```bash
cd data/loudoun/gis

# Backup old files
mv Loudoun_Street_Centerline.zip Loudoun_Street_Centerline.zip.old
mv Loudoun_Airport_Impact_Overlay_Districts.zip AIOD.zip.old

# Copy new files
cp ~/Downloads/Road_Centerline.zip Loudoun_Street_Centerline.zip
cp ~/Downloads/AIOD.zip Loudoun_Airport_Impact_Overlay_Districts.zip
```

#### 3. Extract Shapefiles

```bash
# Extract roads
unzip -o Loudoun_Street_Centerline.zip -d roads/

# Extract AIOD
unzip -o Loudoun_Airport_Impact_Overlay_Districts.zip -d aiod/
```

#### 4. Test Loading

```python
# Test in Python
from core.loudoun_gis_data import _load_roads_internal, _load_aiod_internal

all_roads, highways, collectors = _load_roads_internal()
print(f"Roads: {len(all_roads)} segments")
print(f"Highways: {len(highways)} segments")
print(f"Collectors: {len(collectors)} segments")

aiod = _load_aiod_internal()
print(f"AIOD zones: {len(aiod)}")
```

#### 5. Clear Streamlit Cache

```bash
# Restart Streamlit app to clear cache
# Or use in-app cache clearing:
st.cache_resource.clear()
```

#### 6. Verify in Application

```bash
# Test with known properties:
# - Highway property: 44750 Maynard Sq (near Route 28)
# - AIOD property: Property near Leesburg Executive Airport
# - Power line property: Check impact levels
```

## Troubleshooting

### Problem: "GIS data not found"

**Solution:**
```bash
# Check file existence
ls -lh data/loudoun/gis/roads/
ls -lh data/loudoun/gis/aiod/

# If missing, extract from zip files
unzip -o Loudoun_Street_Centerline.zip -d roads/
unzip -o Loudoun_Airport_Impact_Overlay_Districts.zip -d aiod/
```

### Problem: "geopandas not installed"

**Solution:**
```bash
# Install geopandas and dependencies
pip install geopandas

# Or use conda (recommended for GIS libraries)
conda install geopandas

# Verify installation
python -c "import geopandas; print(geopandas.__version__)"
```

### Problem: Slow loading (>10 seconds)

**Possible causes:**
1. Shapefile corruption
2. Large file sizes (>50 MB)
3. Not using cached version

**Solution:**
```python
# Verify caching is active
from core.loudoun_gis_data import get_cached_loudoun_roads

# First call: should see "Loading Loudoun County road data..."
roads = get_cached_loudoun_roads()

# Second call: should be instant (no loading message)
roads = get_cached_loudoun_roads()
```

### Problem: Coordinate transformation errors

**Cause:** Shapefile projection mismatch

**Solution:**
```python
import geopandas as gpd

# Check shapefile CRS
roads = gpd.read_file('data/loudoun/gis/roads/Loudoun_Street_Centerline.shp')
print(f"Original CRS: {roads.crs}")

# Transform to EPSG:4326 (WGS84)
roads = roads.to_crs(epsg=4326)
print(f"New CRS: {roads.crs}")
```

### Problem: Highway/collector not detected

**Debugging:**
```python
from core.loudoun_gis_data import HIGHWAY_PATTERNS, COLLECTOR_PATTERNS

# Check if road name matches patterns
road_name = "LEESBURG PIKE"

highway_match = any(pattern in road_name for pattern in HIGHWAY_PATTERNS)
collector_match = any(pattern in road_name for pattern in COLLECTOR_PATTERNS)

print(f"Highway: {highway_match}")
print(f"Collector: {collector_match}")
```

**Solution:** Add missing patterns to `loudoun_gis_data.py`:
```python
HIGHWAY_PATTERNS = [
    # ... existing patterns
    'NEW HIGHWAY NAME',  # Add new pattern
]
```

## Technical Details

### Why Shapefiles?

**Advantages:**
- Industry standard for GIS data
- Wide tool support (QGIS, ArcGIS, etc.)
- Efficient spatial indexing
- Attribute data included

**Disadvantages:**
- Multiple files (.shp, .shx, .dbf, .prj)
- Larger than GeoJSON for simple data
- Requires specialized libraries

### Why GeoJSON for Power Lines?

**Advantages:**
- Single file (easier to manage)
- Human-readable JSON format
- No geopandas dependency (uses standard `json` module)
- Smaller file size for simple line data

**Trade-offs:**
- Less efficient for complex geometries
- No built-in spatial indexing
- Manual coordinate handling

### Coordinate System (EPSG:4326)

**Why WGS84?**
- Compatible with GPS coordinates (latitude/longitude)
- ATTOM API returns EPSG:4326 coordinates
- Google Maps uses WGS84
- No transformation needed for distance calculations

**When to Transform:**
- Source shapefiles may use different projections
- Loudoun County data often in State Plane Virginia North (EPSG:2283)
- Always transform to EPSG:4326 for consistency

### Distance Calculations

```python
from shapely.geometry import Point
from shapely.ops import nearest_points

# Property location
property_point = Point(-77.475, 39.015)  # (lon, lat)

# Find nearest highway
nearest_highway = highways.geometry.distance(property_point).min()

# Convert to miles (approximate at this latitude)
distance_miles = nearest_highway * 69  # degrees to miles at ~39° latitude
```

**Note:** For precise distances, use geodesic calculations:
```python
from geopy.distance import geodesic

point1 = (39.015, -77.475)  # (lat, lon)
point2 = (39.020, -77.480)
distance_miles = geodesic(point1, point2).miles
```

## Multi-County Pattern

### Scalability Design

Each county has independent GIS data loaders:

```python
# Loudoun County
get_cached_loudoun_roads()
get_cached_loudoun_aiod()
get_cached_loudoun_power_lines()

# Future: Other counties
get_cached_athens_roads()
get_cached_fairfax_roads()
# etc.
```

### Memory Management

- **Lazy Loading:** County data only loads when needed
- **Independent Caching:** Each county cached separately
- **Clean Separation:** No cross-county dependencies
- **Predictable Memory:** ~20 MB per county

### Adding New Counties

1. Create `data/<county>/gis/` directory
2. Add shapefiles for roads, zoning, etc.
3. Create `<county>_gis_data.py` module:
   ```python
   @st.cache_resource
   def get_cached_<county>_roads():
       return _load_<county>_roads_internal()
   ```
4. Update analyzers to accept county parameter
5. Document in county-specific README

See `docs/MULTI_COUNTY_SCALING.md` for complete guide.

## Best Practices

### Do's
- ✓ Use cached functions in Streamlit apps
- ✓ Extract shapefiles before use (don't read from .zip)
- ✓ Transform to EPSG:4326 for consistency
- ✓ Test with known properties after data updates
- ✓ Document custom highway/collector patterns

### Don'ts
- ✗ Load shapefiles on every property analysis
- ✗ Mix coordinate systems without transformation
- ✗ Modify source shapefiles directly (keep originals)
- ✗ Forget to clear cache after data updates
- ✗ Hardcode file paths (use path resolution functions)

## Version History

- **v2.0** (2025-12-19): Streamlit caching, factory pattern, ~33x speedup
- **v1.0** (2024): Original per-property loading implementation

## Support

**Data Questions:** Loudoun County GIS Department
**Technical Issues:** See `docs/PERFORMANCE_OPTIMIZATION.md`
**Code Updates:** See `core/loudoun_gis_data.py`

---

Last Updated: 2025-12-19
Maintained by: Development Team
Data Source: Loudoun County GIS Department
