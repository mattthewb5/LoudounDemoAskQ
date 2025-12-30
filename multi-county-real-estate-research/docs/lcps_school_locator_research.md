# LCPS School Locator Research

**Last Updated:** November 2025
**Phase:** 3 - School Data
**Status:** Research needed

## Overview

From Prompt 1 research (loudoun_county_data_sources.md):
- LCPS (Loudoun County Public Schools) serves entire county
- 98 schools total (much larger than Athens' ~30)
- School locator tool for finding assigned schools
- No jurisdiction complexity (unlike zoning/crime)

## Research Tasks

### Task 1: Find the School Locator

1. Go to https://www.lcps.org
2. Look for "School Locator", "Boundary Finder", "School Assignment"
3. Document the URL

Expected patterns:
- https://www.lcps.org/boundary-finder
- https://www.lcps.org/school-locator
- https://boundaries.lcps.org

### Task 2: Determine API Access

Check if the school locator has:
- Public API endpoint
- Developer documentation
- GIS-based lookup (ArcGIS REST API)
- Input format (address vs lat/lon)

Common patterns for school district APIs:
- ArcGIS REST service (most common)
- Custom API with address lookup
- Third-party service (SchoolDigger, etc.)
- Direct database query tool

### Task 3: Test the Tool

Test with known addresses:
1. Ashburn area (eastern Loudoun)
2. Leesburg area (central Loudoun)
3. Purcellville area (western Loudoun)

Document:
- What schools are assigned
- How data is returned (HTML, JSON, etc.)
- Whether API is available or just web interface

### Task 4: School Performance Data

Research Virginia School Quality Profiles:
1. Go to https://schoolquality.virginia.gov
2. Look for API or data downloads
3. Document available metrics:
   - Test scores
   - Enrollment
   - Student-teacher ratios
   - Demographics
   - Ratings

### Task 5: Data Format Analysis

Document:
- School ID format
- School names (full vs abbreviated)
- Address formats
- Contact information available
- Performance metrics available

## Expected Findings

Document here once research is complete:

**LCPS School Locator URL:**
[URL]

**API Type:**
- [ ] ArcGIS REST API
- [ ] Custom API with documentation
- [ ] Web interface only (scraping required)
- [ ] Third-party service

**Input Format:**
- [ ] Address (street address)
- [ ] Coordinates (lat/lon)
- [ ] Both

**Output Format:**
- [ ] JSON
- [ ] XML
- [ ] HTML
- [ ] Other

**School Levels Returned:**
- [ ] Elementary
- [ ] Middle
- [ ] High
- [ ] Other (special programs, etc.)

**Virginia School Quality Profiles:**
- URL: [URL]
- API available: Yes/No
- Metrics available: [List]

## Implementation Plan

Based on findings:

1. Update `school_api_endpoint` in config
2. Implement API query in `_query_school_api()`
3. Parse response format
4. Map to School dataclass
5. Test with multiple addresses
6. Add Virginia performance data

## Comparison to Athens

**Athens (Clarke County Schools):**
- Uses CSV street index
- ~30 schools
- Manual data file

**Loudoun (LCPS):**
- API-based (expected)
- 98 schools (3x larger)
- Real-time lookup

**Advantages of API:**
- Always current
- No manual data updates
- More accurate boundaries

## TODO

- [ ] Find LCPS School Locator tool
- [ ] Determine API availability
- [ ] Test with known addresses
- [ ] Document data format
- [ ] Research Virginia School Quality Profiles
- [ ] Update config with findings
- [ ] Implement API integration
