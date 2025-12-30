# Community & Neighborhood Data Investigation

**Date**: December 23, 2025
**Branch**: `claude/community-neighborhood-data-qLule`
**Status**: Implementation Complete

---

## Executive Summary

Investigation and implementation of expanded community/neighborhood data coverage for the Loudoun platform. **Successfully expanded from 17 to 64 communities** with GIS boundary data for spatial matching.

### What Was Built

| Component | Status | Description |
|-----------|--------|-------------|
| GIS Boundary Extraction | ✅ Complete | 64 community polygons from County subdivisions |
| Spatial Lookup Module | ✅ Complete | Point-in-polygon matching for property locations |
| HOA Amenity Scraper | ✅ Complete | Public page scraper for pools, tennis, etc. |

---

## Current State

### communities.json (17 communities)

| # | Community | Type |
|---|-----------|------|
| 1 | River Creek | gated_golf |
| 2 | Brambleton | master_planned |
| 3 | Broadlands | master_planned |
| 4 | Ashburn Village | master_planned |
| 5 | Stone Ridge | master_planned |
| 6 | South Riding | master_planned |
| 7 | Lansdowne on the Potomac | master_planned |
| 8 | Cascades | master_planned |
| 9 | Ashburn Farm | master_planned |
| 10 | One Loudoun | mixed_use |
| 11 | Willowsford | master_planned_rural |
| 12 | Belmont Country Club | gated_golf |
| 13 | Belmont Greene | condo_townhome |
| 14 | Potomac Station | master_planned |
| 15 | Loudoun Valley Estates | master_planned |
| 16 | Farmwell Hunt | master_planned |
| 17 | Kirkpatrick Farms | master_planned |

### Matching Logic

```
RentCast API → subdivision name → fnmatch(pattern) → community data
```

- File: `core/loudoun_community_lookup.py`
- Uses wildcard patterns (e.g., `"BRAMBLETON*"`)
- Supports exclusion patterns to avoid false matches

---

## Coverage Analysis

| Metric | Count |
|--------|-------|
| Current communities | 17 |
| Loudoun.gov HOA list | 71 |
| Overlap (in both) | 16 |
| Unique to us (River Creek) | 1 |
| **Available to add** | **55** |
| Potential total | 72 |

### Already Planned (_todo section)

1. CountrySide ✓
2. Dulles Farms ✓
3. Kincora ✓
4. Loudoun Valley II
5. Loudoun Valley III
6. Moorefield Station ✓
7. Potomac Green ✓
8. Raspberry Falls ✓
9. Sugarland Run ✓

### Additional Communities Available (46)

Alexander's Chase, Amberleigh, Ashburn Village - Four Seasons, Ashburn Village - Lakeshore, Autumn Oaks, Beacon Hill, Beauregard Estates, Belle Terra, Broad Run Farms, Cabin Branch Forest, Calvert's Glen, Cardinal Glen, Carisbrooke, Cascades Park, Church Mills, Connemara Woods, Courts and Ridges of Ashburn, Exeter, Great Falls Forest, Greenfield Crossing, Greenway Farms, Highlands of Round Hill, Lakes at Red Rock, Lansdowne Woods, Lexington 7, Loudoun Crossing, Mayfair, One Loudoun - Midtown, Parkside at Ashburn, Potomac Crossing, Residences at Dulles Parkway Center, Richland Forest, Rivercrest, Seneca Chase, Seneca Ridge, Sterling, Sycamore Hill, Tavistock Farms, The Regency, The Reserve at Rokeby Farm, Vantage Pointe, Village of Waxpool, Waterford View Estates, Westerley, Windermere

---

## Subdivision GIS Data

| Status | Details |
|--------|---------|
| In repository | ✅ YES |
| Source file | `data/loudoun/subdivisions/Subdivisions.shp` |
| Records | 4,753 subdivision plats |
| Unique names | 3,176 |

### Community Boundary Extraction

Dissolved individual subdivision plats into 64 community polygons:

| Output | Path |
|--------|------|
| GeoJSON boundaries | `data/loudoun/gis/community_boundaries.geojson` |
| Pattern mapping | `data/loudoun/config/community_gis_patterns.json` |
| Size | 30.8 MB |

**Coverage**: 64 of 74 target communities (86%)

**Not found in GIS**: Lakes at Red Rock, Calvert's Glen, Carisbrooke, Church Mills, Loudoun Valley III

---

## Spatial Lookup Module

**File**: `core/community_spatial_lookup.py`

Point-in-polygon matching for property coordinates:

```python
from core.community_spatial_lookup import lookup_community

result = lookup_community(38.9753, -77.5328)
# Returns: {"name": "Brambleton", "match_type": "spatial", "confidence": "high"}
```

**Features**:
- Direct spatial match (high confidence)
- Nearest community fallback within 2 miles (medium confidence)
- Cached instance for Streamlit performance

---

## HOA Amenity Scraper

**File**: `scrapers/hoa_amenity_scraper.py`

Extracts amenity data from public HOA marketing pages:

| Amenity Type | Detection Method |
|--------------|------------------|
| Pools | Count patterns, keyword search |
| Tennis courts | Count patterns |
| Clubhouse | Keyword search |
| Fitness center | Keyword search |
| Trails | Mile count patterns |
| Playgrounds | Count patterns |
| Basketball/Pickleball | Keyword search |
| Dog park | Keyword search |

**Test Results** (Potomac Station):
- Pages scraped: 3
- Detected: pool, tennis, clubhouse, trails, playground, basketball, pickleball

**Limitations**:
- Many HOA sites require authentication (Cascades, South Riding, Stone Ridge)
- Some sites block automated requests (403 errors)
- Best targets: Public marketing pages, not member portals

---

## Remaining Work

### Integration Tasks
1. Wire spatial lookup into Streamlit app property display
2. Add community boundary display to map visualization
3. Run amenity scraper on accessible sites and merge with communities.json

### Communities Still Needing Data
5 communities not found in GIS data may need manual boundary definition or alternate source

---

## Key Files

| File | Purpose |
|------|---------|
| `data/loudoun/config/communities.json` | Community definitions & patterns (17 communities) |
| `data/loudoun/config/community_gis_patterns.json` | GIS pattern mapping (64 communities) |
| `data/loudoun/gis/community_boundaries.geojson` | Community boundary polygons |
| `core/loudoun_community_lookup.py` | Pattern-based matching logic |
| `core/community_spatial_lookup.py` | **NEW** - Spatial point-in-polygon matching |
| `scrapers/hoa_amenity_scraper.py` | **NEW** - HOA website amenity extraction |
| `core/property_valuation_orchestrator.py` | Gets subdivision from RentCast |
| `loudoun_streamlit_app.py:1747` | `display_community_section()` |

---

## Data Sources

- [Loudoun County GeoHub](https://geohub-loudoungis.opendata.arcgis.com/)
- [WebLogis Open Data Layers](https://logis.loudoun.gov/loudoun/opendata_layers.html)
- [Loudoun County HOA List](https://www.loudoun.gov/)
