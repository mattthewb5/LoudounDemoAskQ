# Guide: Adding a New County

**For:** Developers expanding multi-county tool
**Time Estimate:** 2-4 weeks per county
**Difficulty:** Medium (with good data sources)

---

## Prerequisites

Before adding a county, ensure you have:

- [ ] **Data sources researched** (see Loudoun County research as template)
- [ ] **API endpoints documented** (schools, crime, zoning)
- [ ] **Test addresses identified** (3-5 known addresses for validation)
- [ ] **Local knowledge** (ideal but not required)

---

## Step 1: Research Data Sources

### Research Checklist

Create a document similar to `loudoun_county_data_sources.md`:

- [ ] **School Data**
  - School district boundary finder/locator tool
  - State school performance portal (like GA GOSA, VA School Quality Profiles)
  - API or GIS layer availability
  - Boundary update frequency

- [ ] **Crime Data**
  - County/city open data portal
  - Police department crime dashboard
  - FBI Crime Data Explorer coverage
  - Data format (API, downloadable, dashboard only)

- [ ] **Zoning Data**
  - County GIS portal
  - ArcGIS REST API endpoints
  - Parcel data availability
  - Comprehensive plan/future land use

- [ ] **Special Considerations**
  - Incorporated towns/cities?
  - Multi-jurisdictional complexity?
  - Unique local issues (data centers, airports, universities)

### Research Template

```markdown
# [County Name], [State] - Data Sources Research

## Executive Summary
- School data: [Available/Limited/Not Available]
- Crime data: [Available/Limited/Not Available]
- Zoning data: [Available/Limited/Not Available]
- Complexity: [Low/Medium/High]

## School Data Sources
[URLs, formats, APIs]

## Crime Data Sources
[URLs, formats, APIs]

## Zoning Data Sources
[URLs, formats, APIs]

## Implementation Difficulty
[Easy/Medium/Hard with justification]
```

---

## Step 2: Create County Configuration

### A. Create Config File

Create `config/new_county.py`:

```python
"""
Configuration for [County Name], [State]

Data Sources:
- Schools: [URL]
- Crime: [URL]
- Zoning: [URL]

Last Updated: [Date]
"""

from typing import Optional
from .base_config import (
    BaseCountyConfig,
    SchoolInfo,
    CrimeAnalysis,
    ZoningInfo,
    NearbyZoning
)


class NewCountyConfig(BaseCountyConfig):
    """Configuration for [County Name], [State]"""

    def get_county_name(self) -> str:
        return "[County Name] County"

    def get_state(self) -> str:
        return "[STATE]"  # Two-letter abbreviation

    def get_schools(self, address: str) -> Optional[SchoolInfo]:
        """
        Get school assignments for an address

        Data Source: [School district URL]
        """
        # TODO: Implement
        # 1. Geocode address
        # 2. Query school district boundary API
        # 3. Fetch school performance data
        # 4. Return SchoolInfo object
        pass

    def get_crime(
        self,
        address: str,
        radius_miles: float = 0.5,
        months_back: int = 12
    ) -> Optional[CrimeAnalysis]:
        """
        Get crime statistics for an address

        Data Source: [Crime data URL]
        """
        # TODO: Implement
        # 1. Geocode address
        # 2. Query crime data API with radius
        # 3. Calculate safety score
        # 4. Analyze trends
        # 5. Return CrimeAnalysis object
        pass

    def get_zoning(self, address: str) -> Optional[ZoningInfo]:
        """
        Get zoning information for an address

        Data Source: [GIS portal URL]
        """
        # TODO: Implement
        # 1. Geocode address
        # 2. Query GIS parcel layer
        # 3. Extract zoning info
        # 4. Return ZoningInfo object
        pass

    def get_nearby_zoning(
        self,
        address: str,
        radius_meters: int = 250
    ) -> Optional[NearbyZoning]:
        """
        Get nearby zoning analysis

        Data Source: [GIS portal URL]
        """
        # TODO: Implement
        # 1. Geocode address
        # 2. Query nearby parcels
        # 3. Analyze zoning patterns
        # 4. Detect concerns
        # 5. Return NearbyZoning object
        pass

    # Optional: Override these if applicable

    def has_incorporated_areas(self) -> bool:
        """Override if county has towns/cities"""
        return False  # Change to True if applicable

    def get_incorporated_areas(self) -> list:
        """Override if has_incorporated_areas() is True"""
        return []  # ["Town 1", "Town 2", ...]

    def get_ai_context(self) -> str:
        """Add county-specific context for AI"""
        return """
        [County Name] context:
        - [Notable feature 1]
        - [Notable feature 2]
        - [Local considerations]
        """

    def get_data_sources(self) -> dict:
        """Document data sources"""
        return {
            'schools': '[School district URL]',
            'crime': '[Crime data URL]',
            'zoning': '[GIS portal URL]'
        }
```

### B. Import in `config/__init__.py`

Add to `config/__init__.py`:

```python
from .base_config import BaseCountyConfig, SchoolInfo, CrimeAnalysis, ZoningInfo
from .athens_clarke import AthensConfig
from .loudoun import LoudounConfig
from .new_county import NewCountyConfig  # Add this line
```

---

## Step 3: Implement get_schools()

### A. Geocode Address

```python
from geopy.geocoders import Nominatim

def geocode_address(self, address: str) -> tuple:
    """Convert address to lat/lon"""
    geolocator = Nominatim(user_agent="real-estate-tool")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    raise ValueError(f"Could not geocode address: {address}")
```

### B. Query School Boundary API

Research the school district's API:
- Is it a web tool that returns JSON?
- Is it a GIS layer (ArcGIS REST API)?
- Is it a downloadable file?

Example for ArcGIS REST API:

```python
import requests

def query_school_zones(self, lat: float, lon: float) -> dict:
    """Query school zone GIS layer"""
    url = "https://gis.schooldistrict.org/arcgis/rest/services/Schools/MapServer/0/query"
    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }
    response = requests.get(url, params=params)
    return response.json()
```

### C. Fetch School Performance Data

Query state school performance portal:

```python
def get_school_performance(self, school_name: str) -> dict:
    """Get school performance from state portal"""
    # Example for Virginia School Quality Profiles
    url = f"https://schoolquality.virginia.gov/api/schools/{school_name}"
    response = requests.get(url)
    return response.json()
```

### D. Return SchoolInfo Object

```python
def get_schools(self, address: str) -> Optional[SchoolInfo]:
    """Complete implementation"""
    try:
        # 1. Geocode
        lat, lon = self.geocode_address(address)

        # 2. Query school zones
        zones = self.query_school_zones(lat, lon)
        elementary = zones['elementary']
        middle = zones['middle']
        high = zones['high']

        # 3. Get performance data
        elem_data = self.get_school_performance(elementary)
        mid_data = self.get_school_performance(middle)
        high_data = self.get_school_performance(high)

        # 4. Return structured data
        return SchoolInfo(
            elementary=elementary,
            middle=middle,
            high=high,
            elementary_data=elem_data,
            middle_data=mid_data,
            high_data=high_data
        )

    except Exception as e:
        print(f"Error getting schools: {e}")
        return None
```

---

## Step 4: Implement get_crime()

### A. Query Crime Data API

Research crime data access:
- Open data portal with API?
- Crime dashboard with export?
- FBI Crime Data Explorer only?

Example for open data portal:

```python
def query_crime_data(self, lat: float, lon: float, radius_miles: float, months_back: int) -> list:
    """Query crime incidents near location"""
    url = "https://data.county.gov/api/crimes"
    params = {
        'latitude': lat,
        'longitude': lon,
        'radius': radius_miles,
        'months': months_back
    }
    response = requests.get(url, params=params)
    return response.json()['incidents']
```

### B. Calculate Safety Score

Reuse safety score calculation from Athens:

```python
def calculate_safety_score(self, incidents: list, area_sq_miles: float) -> dict:
    """Calculate safety score (0-100)"""
    # Normalize by area and population
    crime_density = len(incidents) / area_sq_miles

    # Calculate score (lower is better)
    if crime_density < 10:
        score = 90
    elif crime_density < 50:
        score = 70
    elif crime_density < 100:
        score = 50
    else:
        score = 30

    return {
        'score': score,
        'level': self.get_safety_level(score)
    }

def get_safety_level(self, score: int) -> str:
    """Get safety level description"""
    if score >= 80:
        return "Very Safe"
    elif score >= 60:
        return "Moderate"
    else:
        return "Concerning"
```

### C. Analyze Trends

Compare recent vs. previous period:

```python
def analyze_trends(self, incidents: list, months_back: int) -> dict:
    """Analyze crime trends"""
    cutoff_date = datetime.now() - timedelta(days=months_back * 30 / 2)

    recent = [i for i in incidents if i['date'] >= cutoff_date]
    previous = [i for i in incidents if i['date'] < cutoff_date]

    change = ((len(recent) - len(previous)) / len(previous) * 100) if previous else 0

    return {
        'recent_count': len(recent),
        'previous_count': len(previous),
        'change_percentage': change,
        'trend': 'increasing' if change > 5 else 'decreasing' if change < -5 else 'stable'
    }
```

---

## Step 5: Implement get_zoning()

### A. Query GIS Parcel Layer

Example for ArcGIS REST API:

```python
def query_parcel_zoning(self, lat: float, lon: float) -> dict:
    """Query parcel zoning from GIS"""
    url = "https://gis.county.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query"
    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['features']:
        attrs = data['features'][0]['attributes']
        return {
            'current_zoning': attrs['ZONING'],
            'zoning_description': attrs['ZONING_DESC'],
            'future_land_use': attrs.get('FUTURE_LU'),
            'acres': attrs.get('ACRES', 0)
        }
    return None
```

### B. Query Nearby Parcels

```python
def query_nearby_parcels(self, lat: float, lon: float, radius_meters: int) -> list:
    """Query parcels within radius"""
    # Create buffer geometry
    buffer_geometry = self.create_buffer(lat, lon, radius_meters)

    url = "https://gis.county.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query"
    params = {
        'geometry': buffer_geometry,
        'geometryType': 'esriGeometryPolygon',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': 'ZONING',
        'returnGeometry': 'false',
        'f': 'json'
    }
    response = requests.get(url, params=params)
    return response.json()['features']
```

---

## Step 6: Add County to UI

### A. Update streamlit_app.py

Add county to selector:

```python
# At top of streamlit_app.py
from config import athens_clarke, loudoun, new_county

# County selector
county = st.sidebar.selectbox(
    "Select County:",
    [
        "Athens-Clarke County, GA",
        "Loudoun County, VA",
        "[County Name], [STATE]"  # Add this line
    ]
)

# Load config
configs = {
    "Athens-Clarke County, GA": athens_clarke.AthensConfig(),
    "Loudoun County, VA": loudoun.LoudounConfig(),
    "[County Name], [STATE]": new_county.NewCountyConfig()  # Add this line
}
config = configs[county]
```

---

## Step 7: Test Thoroughly

### A. Unit Tests

Create `tests/test_new_county.py`:

```python
import pytest
from config.new_county import NewCountyConfig


def test_county_name():
    config = NewCountyConfig()
    assert config.get_county_name() == "[County Name] County"
    assert config.get_state() == "[STATE]"


def test_get_schools():
    config = NewCountyConfig()
    schools = config.get_schools("123 Main St, City, STATE ZIP")
    assert schools is not None
    assert schools.elementary is not None
    assert schools.middle is not None
    assert schools.high is not None


def test_get_crime():
    config = NewCountyConfig()
    crime = config.get_crime("123 Main St, City, STATE ZIP")
    assert crime is not None
    assert crime.safety_score is not None


def test_get_zoning():
    config = NewCountyConfig()
    zoning = config.get_zoning("123 Main St, City, STATE ZIP")
    assert zoning is not None
    assert zoning.current_zoning is not None
```

### B. Integration Tests

Test with real addresses:

```python
def test_real_address_integration():
    """Test with known ground truth address"""
    config = NewCountyConfig()

    # Use address you can validate
    address = "123 Real St, City, STATE ZIP"

    # Get all data
    schools = config.get_schools(address)
    crime = config.get_crime(address)
    zoning = config.get_zoning(address)

    # Validate against known truth
    assert schools.elementary == "Expected Elementary School"
    # etc.
```

### C. Manual Testing

1. Run app: `streamlit run streamlit_app.py`
2. Select new county from dropdown
3. Test 5-10 addresses you can validate
4. Verify all three data types load correctly
5. Check AI analysis generates properly

---

## Step 8: Document

### A. Update README.md

Add county to supported counties list:

```markdown
### [County Name], [STATE]
- [x] School lookup ([School district name])
- [x] Crime analysis ([Crime data source])
- [x] Zoning lookup ([GIS portal name])
- **Status:** ✅ Production-ready
```

### B. Create County Notes

Create `docs/new_county_notes.md`:

```markdown
# [County Name], [State] - Implementation Notes

## Data Sources
- Schools: [URL]
- Crime: [URL]
- Zoning: [URL]

## Special Handling
[Any county-specific quirks]

## Test Addresses
- Address 1 (suburban)
- Address 2 (urban)
- Address 3 (rural)

## Known Issues
[Any limitations or gotchas]
```

---

## Checklist: County Complete

Before considering county "done":

- [ ] All three data types implemented (schools, crime, zoning)
- [ ] Unit tests written and passing
- [ ] Integration tests with real addresses passing
- [ ] Manual testing complete (5+ addresses)
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] County added to UI selector
- [ ] AI context customized (optional but recommended)
- [ ] Data sources documented
- [ ] Known issues documented

---

## Common Pitfalls

### 1. Geocoding Issues

**Problem:** Address doesn't geocode
**Solution:** Try multiple geocoding services, handle fuzzy matches

### 2. API Rate Limiting

**Problem:** Too many requests, getting blocked
**Solution:** Implement caching, rate limiting, retry logic

### 3. Data Format Changes

**Problem:** API changes response format
**Solution:** Defensive programming (hasattr, try-except), version pinning

### 4. Multi-Jurisdiction Complexity

**Problem:** County has incorporated towns
**Solution:** Implement jurisdiction detection, handle towns separately

### 5. Missing Data

**Problem:** Some addresses have no school/crime/zoning data
**Solution:** Graceful fallbacks, clear error messages to user

---

## Estimated Timeline

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Research** | Data source investigation | 1-3 days |
| **Schools** | Implement get_schools() | 2-4 days |
| **Crime** | Implement get_crime() | 2-4 days |
| **Zoning** | Implement get_zoning() | 2-4 days |
| **Testing** | Unit + integration tests | 2-3 days |
| **Documentation** | Update docs, add notes | 1-2 days |
| **Polish** | Error handling, AI context | 1-2 days |

**Total:** 2-4 weeks depending on data source complexity

---

## Questions During Implementation?

Common questions and answers:

**Q: What if there's no API, only a web tool?**
A: You may need to reverse-engineer the web tool's network requests or use web scraping (be careful about ToS)

**Q: What if crime data isn't available?**
A: Fall back to FBI Crime Data Explorer (national database) or state-level data

**Q: What if school boundaries change frequently?**
A: Add disclaimer in UI, document update frequency in config

**Q: What if zoning has town-specific rules?**
A: Override `has_incorporated_areas()` and `detect_jurisdiction()` methods

---

**Good luck adding your county!** Follow this guide step-by-step and you'll have a working implementation in 2-4 weeks.
