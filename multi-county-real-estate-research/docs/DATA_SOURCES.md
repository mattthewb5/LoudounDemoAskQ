# Data Sources Catalog

## Executive Summary

The Loudoun County Property Intelligence Platform integrates **18 unique data sources** across three categories: 10 government sources (FREE), 4 commercial APIs (PAID), and 4 proprietary research datasets (curated). This multi-source integration creates a competitive moat that mainstream platforms cannot replicate—each integration requires understanding data formats, API quirks, update schedules, and domain-specific interpretation.

The emphasis on official government sources ensures defensible accuracy. When an investor asks "Can you prove this school really improved 8 points in math over 5 years?", we point to Virginia Department of Education SOL data. When a developer asks about development pressure, we reference actual building permits from the County Commissioner of Revenue with construction costs. This is not opinion—it's auditable government data synthesized into investment-grade intelligence.

The synthesis across these disparate sources—connecting building permits to zoning, demographics to economics, traffic to location quality—answers questions that no single data source can address.

---

## Government Sources (FREE) — 10 Sources

### 1. U.S. Census Bureau - American Community Survey (ACS)

- **Provider:** U.S. Census Bureau
- **Purpose:** Comprehensive demographic data including population, income, education levels, employment characteristics, and housing. Powers the Demographics section with hyper-local 1-mile and 3-mile radius analysis that competitors can't match.
- **Update Frequency:** Annual (5-year rolling estimates released each December)
- **Caching Strategy:** 7-day TTL via `@st.cache_data(ttl=86400*7)`
- **Coverage:** Block group level for Loudoun County (FIPS 51107)
- **Integration Method:** REST API (data.census.gov)
- **Cost:** FREE (API key increases rate limits)
- **Key Data Points:**
  - Total population and median age
  - Median household income and income distribution
  - Educational attainment (bachelor's+, graduate degrees)
  - Labor force participation rate (LFPR)
  - Homeownership rate
  - Average household size
  - Employment status breakdown
- **Module:** `core/census_api.py`, `core/demographics_calculator.py`

---

### 2. Bureau of Labor Statistics - LAUS

- **Provider:** Bureau of Labor Statistics
- **Purpose:** Current unemployment rate and labor force statistics at county level. Provides year-over-year trajectory analysis (improving/stable/worsening) that reveals economic momentum.
- **Update Frequency:** Monthly (released ~3 weeks after reference month)
- **Caching Strategy:** 7-day TTL via `@st.cache_data(ttl=86400*7)`
- **Coverage:** Loudoun County (LAUS series LAUCN511070000000003)
- **Integration Method:** REST API v2 (api.bls.gov)
- **Cost:** FREE (API key increases daily requests from 25 to 500)
- **Key Data Points:**
  - Current unemployment rate
  - Total civilian labor force
  - Number employed/unemployed
  - Year-over-year change percentage
  - Direction indicator (improving/stable/worsening)
- **Module:** `core/census_api.py`, `core/economic_indicators.py`

---

### 3. Virginia Department of Education - SOL Scores

- **Provider:** Virginia Department of Education (VDOE)
- **Purpose:** School performance metrics including Standards of Learning (SOL) pass rates by subject, enabling 5-year trend analysis and peer school comparisons. Critical for families and investors assessing school quality.
- **Update Frequency:** Annual (released after school year ends, typically fall)
- **Caching Strategy:** Static CSV files updated annually
- **Coverage:** All 98 Loudoun County Public Schools (LCPS)
- **Integration Method:** Bulk CSV download, pre-processed
- **Cost:** FREE
- **Key Data Points:**
  - Reading pass rate (by year)
  - Math pass rate (by year)
  - Science pass rate (by year)
  - History pass rate (by year)
  - Writing pass rate (by year)
  - Overall pass rate (by year)
  - Virginia state averages for benchmarking
  - School coordinates for peer matching
- **Files:** `data/loudoun/school_performance_trends_with_state_avg.csv`, `data/loudoun/loudoun_school_coordinates.csv`
- **Module:** `core/loudoun_school_performance.py`

---

### 4. Virginia Department of Transportation - Traffic Volume

- **Provider:** Virginia Department of Transportation (VDOT)
- **Purpose:** Bidirectional Average Daily Traffic (ADT) counts for highways and collectors. Critical for assessing noise impact, location quality, and accessibility. Competitors don't integrate official traffic data.
- **Update Frequency:** Annual
- **Caching Strategy:** Static GeoJSON with road-to-VDOT route mapping
- **Coverage:** All state-maintained roads in Loudoun County
- **Integration Method:** Pre-extracted GeoJSON from VDOT open data
- **Cost:** FREE
- **Key Data Points:**
  - ADT (Average Daily Traffic) by road segment
  - VDOT route identifiers
  - Road classification (highway, collector, local)
  - Coordinate-based segment matching
- **Files:** `data/loudoun/gis/traffic/vdot_traffic_volume.geojson`, `data/loudoun/config/vdot_road_mapping.json`
- **Module:** `core/loudoun_traffic_volume.py`

---

### 5. Loudoun County GIS - Multiple Layers

- **Provider:** Loudoun County GIS (LOGIS)
- **Purpose:** Authoritative spatial data for zoning, school zones, flood zones, airport overlay districts, parcels, and planning designations. The foundation for spatial analysis across the platform.
- **Update Frequency:** Continuous (GIS layers updated as records change)
- **Caching Strategy:** Session-based caching via Streamlit
- **Coverage:** All of Loudoun County including 7 incorporated towns
- **Integration Method:** ArcGIS REST API (esriGeometryPoint queries)
- **Cost:** FREE
- **Key Data Points:**
  - Current zoning classification (Layer 3: Zoning)
  - 2019 Comprehensive Plan Place Types (Layer 10: Planning)
  - Policy Areas (Layer 8: Planning)
  - School attendance zone boundaries (elementary, middle, high)
  - FEMA flood zones (Layer 5: FEMAFlood)
  - Airport Impact Overlay Districts (AIOD)
  - Town boundaries (Layer 1: CountyBoundary)
  - Parcel information
- **Endpoints:**
  - `logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3`
  - `logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer/10`
  - `logis.loudoun.gov/gis/rest/services/COL/FEMAFlood/MapServer/5`
  - `logis.loudoun.gov/gis/rest/services/COL/CountyBoundary/MapServer/1`
- **Module:** `core/loudoun_zoning_analysis.py`, `core/location_quality_analyzer.py`

---

### 6. Loudoun County Building Permits

- **Provider:** Loudoun County Department of Building and Development
- **Purpose:** Building permit activity for development pressure analysis. Tracks new construction, renovations, and demolitions with estimated costs. Reveals development trajectories that predict neighborhood change.
- **Update Frequency:** Monthly bulk export
- **Caching Strategy:** Static CSV file with geocoded coordinates
- **Coverage:** All permits in unincorporated Loudoun County
- **Integration Method:** Pre-processed CSV with geocoded addresses
- **Cost:** FREE
- **Key Data Points:**
  - Permit type (building, electrical, mechanical)
  - Work class (new construction, addition, alteration, demolition)
  - Estimated construction cost
  - Permit issue date
  - Geocoded address with lat/lon
  - Permit description
- **Files:** `data/loudoun/building_permits/`
- **Module:** `core/development_pressure_analyzer.py`

---

### 7. Census TIGERweb - Block Group Centroids

- **Provider:** U.S. Census Bureau TIGERweb
- **Purpose:** Geographic centroids of Census block groups for radius-based demographic calculations. Enables the 1-mile and 3-mile radius analysis that provides hyper-local insights.
- **Update Frequency:** Annual (with decennial Census updates)
- **Caching Strategy:** Session-based caching
- **Coverage:** All block groups in Loudoun County
- **Integration Method:** ArcGIS REST API (tigerweb.geo.census.gov)
- **Cost:** FREE
- **Key Data Points:**
  - Block group GEOID
  - Centroid latitude/longitude
  - Land area (AREALAND)
  - State/County FIPS codes
- **Module:** `core/demographics_calculator.py`

---

### 8. FCC Antenna Structure Registration (ASR) Database

- **Provider:** Federal Communications Commission
- **Purpose:** Cell tower locations with carrier attribution where available. Part of Location Quality Analysis—cell tower proximity affects property values and cell signal availability.
- **Update Frequency:** Continuous (FCC database updates)
- **Caching Strategy:** Static CSV files extracted from FCC
- **Coverage:** All registered antenna structures in Virginia, filtered to Loudoun County (110 towers)
- **Integration Method:** Pre-extracted CSV with enhanced carrier attribution
- **Cost:** FREE
- **Key Data Points:**
  - Tower ID and name
  - Structure type (monopole, lattice, guyed)
  - Height (feet and meters)
  - Latitude/longitude coordinates
  - FCC registration number
  - Entity name (limited availability - FCC database contains entity records for only ~28% of registered towers)
  - Status (built, approved)
- **Files:** `data/loudoun/Cell-Towers/loudoun_towers_enhanced.csv`, `data/loudoun/Cell-Towers/fcc_virginia_towers_active.csv`
- **Module:** `core/location_quality_analyzer.py`

---

### 9. WMATA - Metro Silver Line

- **Provider:** Washington Metropolitan Area Transit Authority (WMATA)
- **Purpose:** Metro Silver Line station locations and track alignment. Enables Metro accessibility tier analysis (Walk-to-Metro, Bike-to-Metro, Metro-Accessible, Metro-Available, Metro-Distant).
- **Update Frequency:** Static (updated when new stations open)
- **Caching Strategy:** Static shapefile data
- **Coverage:** 4 Loudoun County Metro stations (Ashburn, Loudoun Gateway, Innovation Center, Dulles Airport)
- **Integration Method:** Pre-extracted shapefiles from Loudoun County GIS
- **Cost:** FREE
- **Key Data Points:**
  - Station names and locations
  - Track alignment geometry
  - Opening dates (November 2022)
  - Distance calculations to properties
- **Files:** `data/loudoun/transit/Metrorail_Stations.shp`, `data/loudoun/transit/Loudoun_Metrorail_Track.shp`
- **Module:** `core/loudoun_metro_analysis.py`, `core/location_quality_analyzer.py`

---

### 10. Loudoun County ACFR - Major Employers

- **Provider:** Loudoun County Annual Comprehensive Financial Report
- **Purpose:** Top 10 employers in Loudoun County with employee counts. 18-year historical analysis (2008-2025) reveals structural economic shifts—Amazon's entry, AOL's exit, LCPS growth.
- **Update Frequency:** Annual (manually extracted from ACFR PDF documents)
- **Caching Strategy:** Static JSON with `@st.cache_data`
- **Coverage:** Loudoun County top employers
- **Integration Method:** Pre-curated JSON data file (manual extraction)
- **Cost:** FREE (labor-intensive curation)
- **Key Data Points:**
  - Employer name and rank (1-10)
  - Employee count or range
  - Percentage of total employment
  - Year-over-year trends
  - Summary statistics (LCPS 43% growth, Amazon entered 2020, AOL exited 2014)
- **Files:** `data/loudoun/major_employers.json`
- **Module:** `core/economic_indicators.py`

---

## Commercial APIs (PAID) — 4 Sources

### 11. ATTOM Data API

- **Provider:** ATTOM Data Solutions
- **Purpose:** Property characteristics, tax assessments, Automated Valuation Model (AVM), and comparable sales data. One leg of the triangulated property valuation approach.
- **Update Frequency:** Real-time API
- **Caching Strategy:** Session-based caching to reduce API calls
- **Coverage:** National (Loudoun County fully covered)
- **Integration Method:** REST API
- **Cost:** PAID (subscription-based, per-call pricing)
- **Key Data Points:**
  - Property details (beds, baths, sqft, year built, lot size)
  - Tax assessment history
  - AVM current value estimate with confidence scoring
  - Comparable sales within configurable radius
  - Last sale price and date
  - Property type classification
  - Subdivision/neighborhood name
  - APN (Assessor's Parcel Number)
- **Module:** `core/attom_client.py`

---

### 12. RentCast API

- **Provider:** RentCast
- **Purpose:** Rental estimates, property value estimates, and property records including subdivision and HOA data. Provides independent valuation for triangulation and rental yield calculations.
- **Update Frequency:** Real-time API
- **Caching Strategy:** 7-day TTL for property records (file-based cache)
- **Coverage:** National
- **Integration Method:** REST API
- **Cost:** PAID (subscription-based)
- **Key Data Points:**
  - Estimated monthly rent with range
  - Property value estimate with range
  - Property characteristics
  - Subdivision name
  - HOA fee amount
  - Property type
- **Module:** `core/rentcast_client.py`

---

### 13. Google Maps Platform

- **Provider:** Google
- **Purpose:** Address geocoding (address to lat/lon), distance matrix calculations for travel times, and places data for parks and amenities. Foundation for all spatial analysis.
- **Update Frequency:** Real-time API
- **Caching Strategy:** Session-based caching for geocoding results
- **Coverage:** Global
- **Integration Method:** REST API
- **Cost:** PAID (usage-based pricing with free tier)
- **Key Data Points:**
  - Geocoded coordinates from addresses
  - Travel time estimates to destinations
  - Nearby parks and recreation facilities
  - Place ratings and types
  - Formatted address verification
- **Module:** `core/api_config.py`, `core/loudoun_places_analysis.py`

---

### 14. Claude API (Anthropic)

- **Provider:** Anthropic
- **Purpose:** AI-powered narrative generation that synthesizes all data sources into coherent property analysis. Produces investment-grade narratives with local context that template-based reports cannot match.
- **Update Frequency:** Real-time API
- **Caching Strategy:** 24-hour TTL for generated narratives (file-based cache)
- **Coverage:** N/A (text generation)
- **Integration Method:** REST API
- **Cost:** PAID (usage-based token pricing)
- **Key Data Points (Generated):**
  - What Stands Out (distinctive features)
  - Schools Reality (assignment context with percentile rankings)
  - Daily Reality (commute, traffic, convenience)
  - Worth Knowing (important but non-obvious context)
  - Investment Lens (development activity, market position)
  - Bottom Line (ideal buyer profile synthesis)
- **Module:** `core/loudoun_narrative_generator.py`

---

## Proprietary Research (CURATED) — 4 Sources

### 15. Community Amenities Data

- **Provider:** Manual research from HOA websites and community documents
- **Purpose:** 64 Loudoun County communities with HOA fees, amenities, and community characteristics. This proprietary research is not available through any API and provides competitive differentiation.
- **Update Frequency:** Periodic manual updates
- **Caching Strategy:** Static JSON file
- **Coverage:** 64 major Loudoun County communities
- **Integration Method:** Pre-curated data with pattern matching for subdivision-to-community linkage
- **Cost:** FREE (labor-intensive research)
- **Key Data Points:**
  - Community display name
  - HOA monthly/annual fees
  - Amenities (pools, tennis courts, clubhouses, playgrounds, trails)
  - Community type (master-planned, townhouse, single-family)
  - Subdivision pattern matching rules
- **Files:** `data/loudoun/communities/HOA_Amenity_Data_Collection.xlsx`, `data/loudoun/config/communities.json`
- **Module:** `core/loudoun_community_lookup.py`

---

### 16. Road Context Data

- **Provider:** Manual research combining VDOT data with Google Distance Matrix
- **Purpose:** Pre-computed travel times from major roads to key destinations (Tysons, DC, Dulles) during rush hour and off-peak. Enables commute analysis without real-time API calls.
- **Update Frequency:** Periodic manual updates
- **Caching Strategy:** Static JSON file
- **Coverage:** Major highways and collectors in Loudoun County
- **Integration Method:** Pre-curated JSON data
- **Cost:** FREE (Google API costs for initial computation amortized)
- **Key Data Points:**
  - Road name and segment
  - Travel time to Tysons (rush hour and off-peak)
  - Travel time to DC (rush hour and off-peak)
  - Travel time to Dulles Airport
  - Traffic pattern characteristics
- **Files:** `data/loudoun/config/road_context.json`
- **Module:** `core/location_quality_analyzer.py`

---

### 17. Comparable Sales Processing

- **Provider:** Loudoun County Commissioner of Revenue (processed)
- **Purpose:** 47,000 county sales records (2020-2025) converted to Parquet format for 105x performance improvement. Enables rapid comparable sales analysis without ATTOM API dependency.
- **Update Frequency:** Quarterly bulk export and processing
- **Caching Strategy:** Static Parquet file with Streamlit `@st.cache_resource`
- **Coverage:** All recorded sales in Loudoun County (2020-2025)
- **Integration Method:** Parquet file with indexed columns for spatial queries
- **Cost:** FREE (processing time invested)
- **Key Data Points:**
  - Sale price and date
  - Property address with geocoding
  - Square footage
  - Lot size
  - Year built
  - Property type
  - Subdivision name
  - Verification code (sale type)
- **Files:** `data/loudoun/sales/combined_sales.parquet`
- **Module:** `core/loudoun_sales_data.py`, `core/property_valuation_orchestrator.py`

---

### 18. Healthcare Facilities Data

- **Provider:** CMS Hospital Compare, manual research
- **Purpose:** Hospital proximity with Leapfrog safety ratings, maternity services, urgent care centers, and 24-hour pharmacy locations. Family-oriented analysis for relocation decisions.
- **Update Frequency:** Annual (CMS data), periodic manual updates
- **Caching Strategy:** Static files
- **Coverage:** Hospitals and healthcare facilities serving Loudoun County
- **Integration Method:** Pre-processed GeoJSON and JSON files
- **Cost:** FREE
- **Key Data Points:**
  - Hospital name and location
  - Leapfrog safety grade
  - Maternity services availability
  - Level of NICU care
  - Urgent care center locations
  - 24-hour pharmacy locations
  - Distance calculations to properties
- **Files:** `data/loudoun/healthcare/CMS_Hospital_28dec25.csv`, `data/loudoun/healthcare/Loudoun_Hospitals_and_Urgent_Care.geojson`, `data/loudoun/healthcare/maternity_hospitals.json`
- **Module:** `core/location_quality_analyzer.py`

---

## Data Quality & Validation

### Triangulation Approach

For critical metrics like property valuation, the platform triangulates multiple sources:

1. **ATTOM AVM** — Statistical model based on comparable sales
2. **RentCast Value Estimate** — Independent valuation model
3. **Tax Assessment × 1.1** — County's assessed market value adjusted
4. **Comparable Sales Analysis** — Recent sales within radius from county data

The "triangulated estimate" weights these sources by confidence, providing more reliable values than any single source.

### Fallback Strategies

| Data Type | Primary Source | Fallback 1 | Fallback 2 |
|-----------|----------------|------------|------------|
| Property Sqft | MLS (web search) | ATTOM tax records | RentCast |
| Property Value | ATTOM AVM | RentCast AVM | Tax assessment × 1.1 |
| School Assignment | GIS zone boundaries | Hardcoded defaults | Manual lookup |
| Geocoding | Google Maps | ATTOM address lookup | — |
| Subdivision Name | RentCast | ATTOM | County records |

### Data Accuracy Notes

- **School Data:** SOL scores are official VDOE data. School zone boundaries from LCPS may lag redistricting by 1-2 months after boundary changes.
- **Zoning Data:** County GIS is authoritative for unincorporated areas. Town zoning (Leesburg, Purcellville) uses town-specific GIS layers; other towns use county fallback with conservative scoring.
- **Traffic Data:** VDOT ADT counts are annual snapshots. Daily and seasonal variation not reflected—actual traffic varies by time of day and season.
- **Flood Zones:** FEMA FIRM data via County GIS. Properties on zone boundaries should verify with official elevation certificates.
- **Cell Towers:** FCC ASR database provides registered structures. Some carriers may have additional equipment not separately registered.

---

## API Rate Limits & Caching Summary

| Source | Rate Limit | Cache TTL | Rationale |
|--------|------------|-----------|-----------|
| Census API | 500/day with key | 7 days | Data changes annually |
| BLS API | 500/day with key | 7 days | Data changes monthly |
| ATTOM API | Subscription tier | Session | Reduce per-call costs |
| RentCast API | Subscription tier | 7 days | Property data relatively stable |
| Loudoun GIS | No limit | Session | Real-time accuracy needed |
| Google Maps | 25,000/day | Session | Reduce API costs |
| Claude API | Token-based | 24 hours | Narrative regeneration expensive |
| Static files | N/A | Indefinite | Updated manually when needed |

---

## Total Data Sources Summary

| Category | Count | Sources |
|----------|-------|---------|
| **Government APIs** | 10 | Census ACS, BLS LAUS, VDOE SOL, VDOT Traffic, County GIS, Building Permits, TIGERweb, FCC ASR, WMATA Metro, ACFR Employers |
| **Commercial APIs** | 4 | ATTOM, RentCast, Google Maps, Claude |
| **Proprietary Research** | 4 | Community Amenities, Road Context, Comparable Sales, Healthcare Facilities |
| **TOTAL** | **18** | Comprehensive integration across disparate sources |

---

*Last Updated: December 2025*
