# Multi-County Scaling Guide

Complete guide for adding new counties to the real estate research platform.

## Overview

The platform is designed to scale efficiently across multiple counties using:
- **Lazy Loading:** Counties only load when actually used
- **Independent Caching:** Each county cached separately
- **Predictable Memory:** ~50 MB per county (sales + GIS data)
- **Clean Separation:** No cross-county dependencies

## Memory and Performance Scaling

### Per-County Resource Usage

| Component | Memory | First Load | Cached Access |
|-----------|--------|------------|---------------|
| Sales Data | ~30 MB | 2-3 seconds | <0.001s |
| GIS Data (Roads) | ~15 MB | 3-5 seconds | <0.001s |
| GIS Data (Zones) | ~5 MB | 1-2 seconds | <0.001s |
| **Total** | **~50 MB** | **7-11 seconds** | **Instant** |

### Multi-County Projections

| Counties | Total Memory | First Property | Subsequent Properties |
|----------|--------------|----------------|----------------------|
| 1 county | 50 MB | 7-11 seconds | <1 second |
| 3 counties | 150 MB | 7-11 seconds | <1 second |
| 5 counties | 250 MB | 7-11 seconds | <1 second |
| 10 counties | 500 MB | 7-11 seconds | <1 second |

**Key Points:**
- Only loaded counties consume memory (lazy loading)
- First property per county takes 7-11s (one-time cache fill)
- All subsequent properties instant (regardless of number of counties)
- Memory usage is linear and predictable

### Demo Experience Comparison

**Before Optimization:**
- Single county: 90-150 seconds per property
- Demo with 3 properties: 4.5-7.5 minutes
- Multi-county demo: Unusable

**After Optimization:**
- First property: 7-11 seconds (cold cache)
- Subsequent properties: <1 second (warm cache)
- Demo with 3 properties: ~20 seconds total
- Multi-county demo: Excellent UX

## Complete Checklist for Adding a New County

### Phase 1: Data Acquisition

- [ ] **Obtain sales data** from County Assessor/Recorder
  - Excel/CSV format with sales history
  - Minimum fields: Date, Price, Address/Parcel ID, Sale Type
  - Coverage: 3-5 years recommended
  - Sample: ~50k-100k records typical

- [ ] **Obtain GIS data** from County GIS department
  - Road centerlines (shapefile)
  - Zoning districts (shapefile)
  - Special overlay zones (AIOD, flood, historic, etc.)
  - Utilities (power lines, water, sewer)
  - Download from county GIS portal or request directly

- [ ] **Obtain school data** (if available)
  - School boundaries shapefile
  - Performance metrics (test scores, graduation rates)
  - Assignment zones or attendance boundaries

- [ ] **Verify data licenses and usage rights**
  - Public domain or permissive license
  - Commercial use allowed
  - Attribution requirements documented

### Phase 2: Data Preparation

- [ ] **Create county directory structure:**
  ```bash
  mkdir -p data/<county>/sales
  mkdir -p data/<county>/gis
  mkdir -p data/<county>/schools
  mkdir -p data/<county>/utilities
  ```

- [ ] **Prepare sales data:**
  ```bash
  # Place Excel/CSV files in data/<county>/sales/
  # Combine into single file: combined_sales.xlsx
  # Verify columns match expected schema
  ```

- [ ] **Convert sales data to Parquet:**
  ```bash
  python scripts/convert_sales_to_parquet.py --county <county>

  # Verify conversion:
  # - Row count matches source
  # - Column names correct
  # - Date parsing successful
  # - Performance >50x speedup
  ```

- [ ] **Prepare GIS shapefiles:**
  ```bash
  # Extract shapefiles to appropriate subdirectories
  cd data/<county>/gis/
  unzip Road_Centerline.zip -d roads/
  unzip Zoning_Districts.zip -d zoning/

  # Verify CRS (coordinate reference system)
  # Transform to EPSG:4326 if needed
  ```

- [ ] **Document data sources:**
  ```bash
  # Create data/<county>/README.md with:
  # - Data sources and URLs
  # - Update frequency
  # - License/attribution
  # - Last updated date
  # - Contact information
  ```

### Phase 3: Code Implementation

#### A. Sales Data Module

- [ ] **Create sales data class** (`core/<county>_sales_data.py`):
  ```python
  """
  <County Name> Sales Data Lookup Module

  Provides efficient lookup of property sales history from <County Name>
  official records.

  Data Source: <County> Assessor/Recorder
  Coverage: YYYY-MM-DD to present
  Records: ~XX,000 sales transactions
  """

  import os
  import re
  from datetime import datetime
  from typing import Dict, List, Optional
  from collections import defaultdict

  import pandas as pd

  # Define arms-length transaction codes for this county
  ARMS_LENGTH_CODES = {
      # County-specific codes
  }

  class <County>SalesData:
      """
      Efficient lookup of <County Name> property sales history.

      Usage:
          sales_data = <County>SalesData()
          history = sales_data.get_sales_history("PARID-123-456")
      """

      def __init__(self, data_path: Optional[str] = None):
          if data_path is None:
              base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
              data_path = os.path.join(base_dir, 'data', '<county>', 'sales', 'combined_sales.parquet')

          self.data_path = data_path
          self.df = None
          self.sales_index: Dict[str, List[Dict]] = defaultdict(list)
          self.data_loaded = False
          self.load_error: Optional[str] = None

          self._load_data()

      def _load_data(self) -> None:
          """Load and index sales data from Parquet file."""
          # Implementation following Loudoun pattern
          pass

      def get_sales_history(self, parcel_id: str, max_records: int = 3) -> Dict:
          """Get sales history for a property."""
          # Implementation following Loudoun pattern
          pass

  # Streamlit caching
  try:
      import streamlit as st

      @st.cache_resource
      def get_cached_<county>_sales_data() -> '<County>SalesData':
          """Get cached <County>SalesData instance."""
          return <County>SalesData()

  except ImportError:
      def get_cached_<county>_sales_data() -> '<County>SalesData':
          """Non-cached version for use outside Streamlit."""
          return <County>SalesData()
  ```

- [ ] **Test sales data loading:**
  ```bash
  python -m core.<county>_sales_data

  # Verify:
  # - Parquet loads successfully
  # - Index builds correctly
  # - Sample lookups work
  # - Performance <5 seconds
  ```

#### B. GIS Data Module

- [ ] **Create GIS data module** (`core/<county>_gis_data.py`):
  ```python
  """
  <County Name> GIS Data - Cached Loading

  Provides cached access to GIS shapefiles and data for location analysis.

  Data Sources:
  - Road Centerline shapefile
  - Zoning districts shapefile
  - Special overlay zones
  """

  import os
  import geopandas as gpd
  from typing import Optional, Tuple

  # Define highway/collector patterns for this county
  HIGHWAY_PATTERNS = [
      # County-specific patterns
  ]

  COLLECTOR_PATTERNS = [
      # County-specific patterns
  ]

  def _load_roads_internal() -> Tuple[Optional[gpd.GeoDataFrame], ...]:
      """Load and process road data."""
      # Implementation following Loudoun pattern
      pass

  def _load_zoning_internal() -> Optional[gpd.GeoDataFrame]:
      """Load zoning district data."""
      # Implementation
      pass

  # Streamlit caching
  try:
      import streamlit as st

      @st.cache_resource
      def get_cached_<county>_roads():
          """Get cached road data."""
          return _load_roads_internal()

      @st.cache_resource
      def get_cached_<county>_zoning():
          """Get cached zoning data."""
          return _load_zoning_internal()

  except ImportError:
      # Non-cached fallbacks
      pass
  ```

- [ ] **Test GIS data loading:**
  ```bash
  python -c "from core.<county>_gis_data import _load_roads_internal; roads = _load_roads_internal(); print(f'Loaded {len(roads[0])} road segments')"

  # Verify:
  # - Shapefiles load without errors
  # - CRS transformation works
  # - Highway/collector filtering correct
  # - Performance <10 seconds
  ```

#### C. Location Analyzer

- [ ] **Update LocationQualityAnalyzer** to support new county:
  ```python
  # In location_quality_analyzer.py

  def __init__(self, county: str = 'loudoun', preloaded_data: Optional[Dict] = None):
      self.county = county.lower()

      if preloaded_data:
          # Use preloaded cached data
          self.roads_data = preloaded_data.get('roads')
          self.zoning_data = preloaded_data.get('zoning')
      else:
          # Load based on county
          if self.county == 'loudoun':
              from core.loudoun_gis_data import _load_roads_internal
              self.roads_data = _load_roads_internal()
          elif self.county == '<county>':
              from core.<county>_gis_data import _load_roads_internal
              self.roads_data = _load_roads_internal()
  ```

- [ ] **Create cached analyzer factory:**
  ```python
  @st.cache_resource
  def get_cached_<county>_location_analyzer():
      """Get cached location analyzer for <County>."""
      from core.<county>_gis_data import get_cached_<county>_roads

      roads_data = get_cached_<county>_roads()
      return LocationQualityAnalyzer(
          county='<county>',
          preloaded_data={'roads': roads_data}
      )
  ```

#### D. County Configuration

- [ ] **Create county config** (`config/<county>.py`):
  ```python
  """
  Configuration for <County Name>, <State>
  """

  from config.base_config import BaseCountyConfig

  class <County>Config(BaseCountyConfig):
      # County identification
      COUNTY_NAME = "<County Name>"
      STATE = "<State Abbreviation>"
      STATE_FULL = "<State Full Name>"

      # Data paths
      SALES_DATA_PATH = "data/<county>/sales/combined_sales.parquet"
      GIS_DATA_PATH = "data/<county>/gis"

      # API configuration
      ATTOM_COUNTY_CODE = "<code>"  # From ATTOM API docs

      # School data
      HAS_SCHOOL_DATA = True/False
      SCHOOL_DISTRICT_NAME = "<District Name>"

      # GIS layers available
      HAS_ROAD_DATA = True
      HAS_ZONING_DATA = True
      HAS_SCHOOL_BOUNDARIES = True/False
      HAS_UTILITY_DATA = True/False

      # Performance tuning
      SALES_CACHE_TTL = 3600  # seconds
      GIS_CACHE_TTL = 86400   # seconds
  ```

#### E. Orchestrator Integration

- [ ] **Update PropertyValuationOrchestrator:**
  ```python
  def _get_sales_data(self):
      """Load sales data based on county."""
      if self.config.COUNTY_NAME.lower() == 'loudoun':
          from core.loudoun_sales_data import get_cached_loudoun_sales_data
          return get_cached_loudoun_sales_data()
      elif self.config.COUNTY_NAME.lower() == '<county>':
          from core.<county>_sales_data import get_cached_<county>_sales_data
          return get_cached_<county>_sales_data()
  ```

### Phase 4: Testing

- [ ] **Unit tests for sales data:**
  ```bash
  # Test parcel ID normalization
  # Test sales lookup
  # Test date filtering
  # Test arms-length filtering
  # Test caching behavior
  ```

- [ ] **Unit tests for GIS data:**
  ```bash
  # Test shapefile loading
  # Test CRS transformation
  # Test highway/collector identification
  # Test proximity calculations
  # Test caching behavior
  ```

- [ ] **Integration tests:**
  ```bash
  # Test full property analysis workflow
  # Test with multiple properties
  # Test cache performance
  # Test memory usage
  ```

- [ ] **Manual Streamlit testing:**
  ```bash
  # Start Streamlit app
  # Test first property (cold cache)
  # Test second property (warm cache)
  # Verify all sections display
  # Check browser console for errors
  ```

### Phase 5: Documentation

- [ ] **Create county data README** (`data/<county>/README.md`)
- [ ] **Create sales data README** (`data/<county>/sales/README.md`)
- [ ] **Create GIS data README** (`data/<county>/gis/README.md`)
- [ ] **Update main README** with county information
- [ ] **Document API keys/credentials** required (if any)
- [ ] **Create troubleshooting guide** for common issues

### Phase 6: Deployment

- [ ] **Verify all dependencies installed:**
  ```bash
  pip install -r requirements.txt
  # Ensure geopandas, pandas, streamlit, etc.
  ```

- [ ] **Set environment variables:**
  ```bash
  export ANTHROPIC_API_KEY='...'
  export ATTOM_API_KEY='...'
  # County-specific keys if needed
  ```

- [ ] **Test in production-like environment:**
  ```bash
  # Clean cache
  rm -rf ~/.streamlit/cache

  # Start app
  streamlit run <county>_streamlit_app.py

  # Test with real users
  ```

- [ ] **Monitor performance:**
  ```bash
  # Check memory usage
  # Monitor load times
  # Verify cache hit rates
  # Check for errors/warnings
  ```

- [ ] **Create backup procedures:**
  ```bash
  # Backup Parquet files
  # Backup shapefiles
  # Document recovery process
  ```

## County-Specific Considerations

### Urban vs. Rural Counties

**Urban (e.g., Loudoun, Fairfax):**
- More sales data (100k+ records)
- Complex road networks
- Multiple school districts
- Higher GIS data volume
- Longer first load (10-15s)
- More memory usage (60-80 MB)

**Rural (e.g., Clarke, Shenandoah):**
- Fewer sales (10k-30k records)
- Simpler road networks
- Single school district
- Smaller GIS files
- Faster first load (5-8s)
- Less memory (30-40 MB)

**Optimization Tips:**
- Rural: Can load all data eagerly
- Urban: Keep lazy loading pattern
- Both: Use same caching strategy

### State-Specific Data Formats

**Virginia:**
- PARID format: 12 digits
- State Plane CRS: EPSG:2283
- Sales codes: State-defined

**Other States:**
- Research state-specific formats
- Adjust PARID normalization
- Update CRS transformation
- Map sale verification codes

### Data Availability

**High Availability (Public Portals):**
- California, Texas, Virginia
- Easy to acquire and refresh
- Well-documented schemas

**Medium Availability (On Request):**
- Many Midwestern states
- Requires formal request
- May have fees

**Low Availability (Limited Access):**
- Some Southern/Eastern states
- May require legal agreements
- Alternative data sources needed

## Performance Testing Procedures

### Memory Profiling

```python
import tracemalloc
import gc

# Start tracing
tracemalloc.start()

# Load county data
from core.<county>_sales_data import get_cached_<county>_sales_data
sales_data = get_cached_<county>_sales_data()

# Get memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.2f} MB")
print(f"Peak: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

### Load Time Profiling

```python
import time

# Test cold load
start = time.time()
from core.<county>_sales_data import LoudounSalesData
sales = LoudounSalesData()
cold_load_time = time.time() - start

# Test warm load (cached)
start = time.time()
from core.<county>_sales_data import get_cached_<county>_sales_data
sales_cached = get_cached_<county>_sales_data()
# Second call
sales_cached = get_cached_<county>_sales_data()
warm_load_time = time.time() - start

print(f"Cold load: {cold_load_time:.2f}s")
print(f"Warm load: {warm_load_time:.4f}s")
print(f"Speedup: {cold_load_time / warm_load_time:.0f}x")
```

### Cache Hit Rate Monitoring

```python
# In Streamlit app
import streamlit as st

# Track cache stats
if 'cache_hits' not in st.session_state:
    st.session_state.cache_hits = 0
    st.session_state.cache_misses = 0

# On data access
if data_loaded_from_cache:
    st.session_state.cache_hits += 1
else:
    st.session_state.cache_misses += 1

# Display in sidebar
hit_rate = st.session_state.cache_hits / (st.session_state.cache_hits + st.session_state.cache_misses)
st.sidebar.metric("Cache Hit Rate", f"{hit_rate:.1%}")
```

## Common Pitfalls and Solutions

### Pitfall 1: Hardcoded Paths

**Problem:**
```python
# Bad - won't work across environments
df = pd.read_parquet('/Users/matt/data/loudoun/sales/combined_sales.parquet')
```

**Solution:**
```python
# Good - relative to module location
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, 'data', 'loudoun', 'sales', 'combined_sales.parquet')
```

### Pitfall 2: Forgetting to Clear Cache

**Problem:** Data updates don't appear in app

**Solution:**
```python
# Add cache clear button in Streamlit
if st.button("Clear Cache"):
    st.cache_resource.clear()
    st.experimental_rerun()
```

### Pitfall 3: Loading Data on Every Call

**Problem:**
```python
# Bad - loads on every function call
def analyze_property(address):
    sales_data = LoudounSalesData()  # Loads every time!
    return sales_data.get_sales_history(address)
```

**Solution:**
```python
# Good - use cached version
def analyze_property(address):
    sales_data = get_cached_loudoun_sales_data()  # Cached!
    return sales_data.get_sales_history(address)
```

### Pitfall 4: Mixed Coordinate Systems

**Problem:** Distance calculations wrong due to CRS mismatch

**Solution:**
```python
# Always transform to consistent CRS (EPSG:4326)
roads = gpd.read_file('roads.shp')
if roads.crs != 'EPSG:4326':
    roads = roads.to_crs(epsg=4326)
```

### Pitfall 5: No Error Handling

**Problem:** App crashes on missing data

**Solution:**
```python
def _load_data(self):
    try:
        if not os.path.exists(self.data_path):
            self.load_error = f"File not found: {self.data_path}"
            return

        self.df = pd.read_parquet(self.data_path)
        # ... rest of loading
        self.data_loaded = True

    except Exception as e:
        self.load_error = f"Error loading: {str(e)}"
```

## Maintenance Procedures

### Quarterly Data Refresh

1. Download updated sales data from county
2. Convert to Parquet: `python scripts/convert_sales_to_parquet.py --county <county> --force`
3. Test loading: `python -m core.<county>_sales_data`
4. Clear Streamlit cache
5. Verify in app with known properties
6. Update README with new date range

### Annual GIS Update

1. Check county GIS portal for updates
2. Download new shapefiles
3. Replace old files (keep backups)
4. Extract shapefiles
5. Test loading
6. Clear Streamlit cache
7. Verify highway/collector patterns still work
8. Update documentation

### Monitoring Checklist

- [ ] Memory usage stays within limits (<500 MB total)
- [ ] First load times <15 seconds
- [ ] Cached loads <1 second
- [ ] No error logs in production
- [ ] Data coverage remains current (within 3 months)
- [ ] Cache hit rate >90% for multi-property demos

## Success Metrics

### Technical Metrics

- **Load Time:** First property <15s, subsequent <1s
- **Memory Usage:** <100 MB per county
- **Cache Hit Rate:** >90% after first property
- **Error Rate:** <1% of property lookups
- **Data Freshness:** Updates within 3 months

### User Experience Metrics

- **Demo Completion:** >90% of demos complete successfully
- **User Satisfaction:** Perceived as "fast" and "responsive"
- **Feature Usage:** All data sections display correctly
- **Error Recovery:** Users can retry failed lookups

## Support and Resources

### Internal Resources

- **Code Examples:** See `core/loudoun_sales_data.py` (reference implementation)
- **Testing Scripts:** `scripts/convert_sales_to_parquet.py`, `scripts/test_parquet_loading.py`
- **Documentation:** `data/loudoun/*/README.md` files

### External Resources

- **GeoPandas Docs:** https://geopandas.org/
- **Parquet Format:** https://parquet.apache.org/
- **Streamlit Caching:** https://docs.streamlit.io/library/advanced-features/caching
- **Shapely Geometry:** https://shapely.readthedocs.io/

### Getting Help

1. Check county-specific README files
2. Review `docs/PERFORMANCE_OPTIMIZATION.md`
3. Search commit history for similar implementations
4. Test with reference county (Loudoun) first
5. Profile memory and performance systematically

## Version History

- **v1.0** (2025-12-19): Initial multi-county scaling guide

---

Last Updated: 2025-12-19
