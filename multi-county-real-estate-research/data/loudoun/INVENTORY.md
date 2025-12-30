# Loudoun County Data Inventory

**Branch:** claude/loudoun-master-consolidated-01EBYMb1Xo8yTKJFUDZoGhnk
**Last Updated:** 2025-12-01
**Total Files:** 13
**Total Size:** 6.4 MB

## Directory Structure

### Schools Data (data/loudoun/schools/)

| File | Size | Description |
|------|------|-------------|
| elementary_zones.geojson | 2.2 MB | Elementary school attendance boundaries |
| middle_zones.geojson | 1.2 MB | Middle school attendance boundaries |
| high_zones.geojson | 1.2 MB | High school attendance boundaries |
| school_sites.geojson | 24 KB | School location points |
| school_metadata.csv | 111 KB | School information (name, address, type) |
| school_accreditation.csv | 660 KB | Virginia accreditation status |
| school_performance_trends.csv | 767 KB | 5-year SOL test trends |

**Source:** claude/loudoun-county-dev-01HFQXNpLjo6hBgdrcQB7SbZ

### Building Permits (data/loudoun/building_permits/)

| File | Size | Description |
|------|------|-------------|
| loudoun_permits_2024_2025_FINAL.csv | 175 KB | 846 permits, geocoded addresses |
| loudoun_permits_2024_2025_geocoded.csv | 143 KB | Alternative geocoded format |

**Coverage:** August 2024 - January 2025
**Source:** claude/initial-setup-01UxcJ3EEcoL5sEJUuyguSEd

### Base Files (data/loudoun/)

| File | Size | Description |
|------|------|-------------|
| README.md | 2.6 KB | Directory overview |
| town_boundaries.geojson | 1.6 KB | Town boundary polygons (Leesburg, Purcellville, etc.) |
| HANDOFF_TO_CLAUDE_CODE.md | 11 KB | Integration documentation |
| README_PROCESSED_DATA.md | 6 KB | Data processing notes |

## Code Files

### Core Module (core/)

| File | Size | Description |
|------|------|-------------|
| loudoun_zoning_analysis.py | 45 KB | Zoning analysis with Place Types + Town support |

**Features:**
- Place Types API integration (2019 Comprehensive Plan)
- Policy Areas detection
- Multi-jurisdiction support (County, Leesburg, Purcellville)
- Development probability scoring

**Source:** claude/add-place-types-query-01EBYMb1Xo8yTKJFUDZoGhnk

### Configuration (config/)

| File | Size | Description |
|------|------|-------------|
| loudoun.py | 7 KB | County configuration and API endpoints |

## Data Sources

### Schools
- Loudoun County Public Schools GIS
- Virginia Department of Education (VDOE)
- School accreditation and performance data

### Building Permits
- Loudoun County Building Permits Portal
- Monthly issued permit reports (PDF/Excel)
- Geocoded via Google Maps API

### Zoning/Planning
- LOGIS (Loudoun GIS) REST Services
- 2019 Comprehensive Plan Place Types
- Town-specific zoning maps

## Athens Files

**Status:** ✅ NO ATHENS FILES MODIFIED

All Athens data, code, and UI files remain unchanged:
- data/athens/ - Untouched
- streamlit_app.py - Untouched
- core/school_performance.py - Untouched
- All Clarke County files - Untouched
