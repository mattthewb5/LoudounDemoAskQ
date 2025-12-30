# Platform Features Guide

## Executive Summary

The Loudoun County Property Intelligence Platform provides **11 distinct feature areas** that synthesize data from 18 sources into investment-grade intelligence. While competitors offer isolated data points—a property value here, a school rating there—this platform connects disparate datasets to reveal insights that answer questions sophisticated buyers actually ask.

The platform supports three primary use cases:

1. **Property Investment Analysis**: Valuation, development pressure, rental yields, and forward-looking appreciation factors
2. **Relocation Decision Support**: Schools, commute, healthcare, and neighborhood character for families making life decisions
3. **Development Opportunity Identification**: Zoning alignment, permit activity, and comprehensive plan analysis for commercial developers

Features work together to provide holistic intelligence. Building permit analysis connects to zoning to explain *why* development pressure exists. Demographics connect to economic indicators to explain *why* an area is affluent. The AI synthesis weaves all features into coherent narratives that read like advice from a knowledgeable local expert.

---

## Core Features

---

## 1. Property Overview & Valuation

### Overview

The Property Valuation section provides triangulated property values from multiple independent sources, sales history from county records (2020-2025), comparable sales analysis with quality scoring, rental value estimates, and 1/3/5-year forecasts. Rather than trusting a single automated valuation, the platform combines ATTOM, RentCast, and local sales data to produce confidence-weighted estimates.

### Value Proposition

Investment decisions require understanding whether a property is fairly priced relative to recent comparable sales and future appreciation potential. This section answers: What is this property worth today from multiple perspectives? What did it sell for historically? What are similar nearby properties selling for? What could it rent for? Where will the value be in 5 years based on market trends?

### Data Sources

- ATTOM Data API (AVM, property details, comparable sales)
- RentCast API (value estimate, rental estimate, HOA data)
- Loudoun County Commissioner of Revenue (sales history 2020-2025, 47K records)

### Key Capabilities

- Property details display (sqft, lot size, year built, property type)
- Sales history table with appreciation calculations between sales
- Current value estimates from multiple sources with confidence scoring
- Comparable sales within configurable radius with quality assessment (Excellent/Good/Fair based on distance, size similarity, recency)
- Rental value estimate with gross yield calculation
- 1/3/5-year value projections based on market trends

### Technical Implementation

The `PropertyValuationOrchestrator` class unifies ATTOM and RentCast clients with local sales data in Parquet format (105x faster than Excel). Comparable sales receive quality scores based on distance (<0.5mi=Excellent), size similarity (within 20%), and recency (<6 months). The forecast engine applies area-specific appreciation rates. Square footage resolution prioritizes MLS data, falling back to ATTOM tax records, then RentCast.

**Key Modules:** `core/property_valuation_orchestrator.py`, `core/attom_client.py`, `core/rentcast_client.py`, `core/loudoun_sales_data.py`, `core/forecast_engine.py`

---

## 2. Building Permits Intelligence

### Overview

The Building Permits section analyzes nearby permit activity to calculate a development pressure score (0-100). It examines total permits, construction values, new construction ratios, and permit type impact to reveal whether a neighborhood is stable, transitioning, or experiencing active development. This is forward-looking intelligence that predicts neighborhood change.

### Value Proposition

Development pressure reveals what will happen to a neighborhood, not what has already happened. A buyer seeking a quiet established neighborhood wants to avoid areas with high new construction activity—the score quantifies this risk. A developer wants to identify areas with momentum where the market is moving. Competitors don't offer this analysis.

### Data Sources

- Loudoun County Department of Building and Development (permit records with construction costs)
- Geocoded permit locations for spatial analysis

### Key Capabilities

- Development pressure score (0-100) with classification (Very High/High/Moderate/Low)
- Total permits within 0.5-mile and 2-mile radii
- Total construction value aggregation
- New construction ratio (percentage of permits that are new buildings vs. renovations)
- Recent activity ratio (past 6 months vs. prior year)
- Trend indicator (increasing/stable/decreasing)
- Top impact permits with details and distance
- Permit type impact weighting (data center=10, warehouse=9, single-family=8, alteration=3, fence=2)

### Technical Implementation

The `DevelopmentPressureAnalyzer` class loads geocoded permit CSV, filters by configurable radius using haversine distance, and calculates composite scores. Impact scores weight different permit types—data centers and warehouses have highest impact (reflecting Loudoun's role in "Data Center Alley"), deck and fence permits have lowest. The analyzer includes infrastructure detection for significant nearby projects.

**Key Modules:** `core/development_pressure_analyzer.py`, `core/infrastructure_detector.py`

---

## 3. Zoning & Development Probability

### Overview

The Zoning section displays current zoning classification, the 2019 Comprehensive Plan designation (what the county envisions for the next 20 years), and a Development Probability Score (0-100) that quantifies the gap between current zoning and the county's long-term vision. This is the only platform that connects zoning to comprehensive plan alignment.

### Value Proposition

Zoning determines what can be built today. But the comprehensive plan reveals what the county *wants* built over the next two decades. When there's a gap—restrictive current zoning but high-density comprehensive plan designation—there's development pressure that will eventually manifest. This section quantifies that gap and explains implications for neighborhood stability in plain English.

### Data Sources

- Loudoun County GIS (current zoning Layer 3, comprehensive plan Layers 8 and 10)
- Manual zoning code translations for plain-English display
- Town-specific zoning layers for incorporated areas (Leesburg, Purcellville)

### Key Capabilities

- Current zoning code with plain-English translation (e.g., "R-2: Single-Family Residential, 2 units/acre")
- Comprehensive plan Place Type designation (e.g., "Suburban Mixed Use", "Rural")
- Policy Area classification (Suburban, Transition, Rural)
- Development Probability Score (0-100) with risk classification
- Score breakdown (restrictiveness component, pressure component, building activity modifier)
- Intensity alignment analysis (how current zoning compares to plan vision)
- Dynamic three-paragraph narrative explaining what the score means, why it scores this way, and realistic change scenarios with timelines
- Comparative context (what other Loudoun areas score 80+ vs. 20-)

### Technical Implementation

The `loudoun_zoning_analysis.py` module queries multiple Loudoun County GIS layers and handles jurisdiction detection for 7 incorporated towns (Leesburg, Purcellville, Middleburg, Hamilton, Hillsboro, Lovettsville, Round Hill). The development probability algorithm compares current zoning intensity to comprehensive plan intensity, scoring the "gap" that creates rezoning pressure. Scores are scaled by alignment—if current zoning already matches the plan, pressure is reduced. Town properties receive conservative scoring with appropriate disclosures.

**Key Modules:** `core/loudoun_zoning_analysis.py`, `core/jurisdiction_detector.py`

---

## 4. School Performance Analysis

### Overview

The Schools section identifies assigned schools (elementary, middle, high) based on official GIS attendance zone boundaries, displays current SOL pass rates by subject, shows 5-year performance trends, and enables comparison to Virginia state averages and nearby peer schools within 5 miles.

### Value Proposition

School quality is the #1 driver of property values in suburban markets. This section goes far beyond simplified 1-10 ratings to show actual SOL pass rates, 5-year trends (is the school improving or declining?), and how it compares to peer schools within 5 miles. Parents can see if their assigned elementary school outperforms the next-closest option. Investors can identify undervalued properties in improving school zones.

### Data Sources

- Loudoun County GIS (school attendance zone boundaries)
- Virginia Department of Education (SOL pass rates by subject, 5-year history)
- School coordinates for peer matching

### Key Capabilities

- Assigned school identification (elementary, middle, high) from official zone boundaries
- Current pass rates by subject (Reading, Math, Science, History, Writing)
- 5-year test score trends across subjects (reading, math, history, science, writing) by school
- Virginia state average comparison benchmarks
- Peer school comparison (2 nearest schools of same type within 5 miles)
- Subject-by-subject analysis with tabs
- Growth rate calculations showing improvement/decline

### Technical Implementation

School assignments use GeoPandas to query GeoJSON attendance zone boundaries with point-in-polygon operations. Performance data from VDOE is stored in pre-processed CSV with state averages. The `find_peer_schools()` function uses haversine distance from property coordinates to school coordinates to identify the 2 nearest peers of each type. School name normalization handles variations (e.g., "Steuart W. Weller Elementary" matches "WELLER ES").

**Key Modules:** `core/loudoun_school_performance.py`, `core/loudoun_school_percentiles.py`, `core/school_lookup.py`

---

## 5. Neighborhood Intelligence

### Overview

The Neighborhood Intelligence section identifies the community/subdivision where the property is located and provides proprietary HOA research including fees, amenities (pools, tennis courts, clubhouses, playgrounds, trails), and community character. This data required manual research of 64 Loudoun County communities and is not available through any API.

### Value Proposition

Community amenities significantly affect property values and lifestyle. A master-planned community with multiple pools, tennis courts, and a clubhouse commands premium pricing over communities without amenities. HOA fees are a recurring cost that affects affordability calculations. This proprietary research provides insights competitors cannot offer because the data doesn't exist in any purchasable database.

### Data Sources

- Proprietary HOA research (64 communities manually researched)
- RentCast API (subdivision name, HOA fee amount)
- ATTOM Data (subdivision identification)
- Community boundary data for spatial matching

### Key Capabilities

- Community/subdivision identification using pattern matching
- HOA monthly and annual fee amounts
- Community amenities list (pools, tennis, clubhouses, playgrounds, walking trails, fitness centers)
- Community type classification (master-planned, townhouse-only, single-family)
- Subdivision-to-community linkage (e.g., "BRAMBLETON SEC 42" → "Brambleton" community)

### Technical Implementation

The `CommunityLookup` class uses pattern matching to link subdivisions (from tax records and sales data) to master communities. For example, "BRAMBLETON SEC 42", "BRAMBLETON SECTION 12", and "BRAMBLETON TOWN CTR" all map to the "Brambleton" community. Amenity data is stored in a curated JSON configuration file. The `community_spatial_lookup.py` module provides GIS-based matching when subdivision names are unavailable.

**Key Modules:** `core/loudoun_community_lookup.py`, `core/community_spatial_lookup.py`

---

## 6. Area Demographics

### Overview

The Demographics section displays Census ACS 5-year estimates for the population within 1-mile and 3-mile radii of the property. Data includes population, median age, income distribution, educational attainment, homeownership rate, and employment characteristics—all calculated using population-weighted aggregation from Census block groups, not ZIP code averages.

### Value Proposition

Demographics reveal the character of a neighborhood in ways that property photos cannot. A buyer relocating for work wants to know if the area has families with school-age children. An investor wants to understand income levels to gauge rental demand and ability to pay. This section provides authoritative Census data at hyper-local radii—block group granularity is approximately 40x more precise than ZIP code averages used by competitors.

### Data Sources

- U.S. Census Bureau American Community Survey 5-Year Estimates
- Census TIGERweb (block group centroids for radius calculations)

### Key Capabilities

- Side-by-side 1-mile and 3-mile radius comparison
- Total population and median age
- Median household income with comparison to county average
- Income distribution charts
- Educational attainment (bachelor's+, graduate degrees)
- Homeownership rate
- Age distribution visualization
- Employment status breakdown
- Labor force participation

### Technical Implementation

The `demographics_calculator.py` module fetches block group centroids from TIGERweb, determines which block groups fall within each radius using haversine distance, fetches Census variables for those block groups (handling the 50-variable limit by batching requests), and performs population-weighted aggregation. The `demographics_formatter.py` module handles display formatting and comparison calculations.

**Key Modules:** `core/demographics_calculator.py`, `core/demographics_formatter.py`, `core/census_api.py`

---

## 7. Location Quality Analysis

### Overview

The Location Quality section provides comprehensive environmental and infrastructure analysis including FEMA flood zones with insurance implications, airport noise overlay districts (AIOD) with disclosure requirements, power line proximity (80 segments with voltage levels), and cell tower locations (110 towers with FCC carrier attribution). Each factor is presented with plain-English explanations of practical impact.

### Value Proposition

Location factors affect both livability and resale. A property in an airport noise zone requires seller disclosure—a potential deal-breaker for some buyers. A property in a FEMA flood zone requires insurance that can cost thousands annually. Power lines within view affect value. This section surfaces these factors proactively with clear explanations of financial and lifestyle implications—information buyers discover too late in the process when working with traditional agents.

### Data Sources

- Loudoun County GIS (Airport Impact Overlay Districts, FEMA Flood layers)
- Loudoun County power transmission line GIS data (80 segments, 138kV-500kV)
- FCC Antenna Structure Registration database (110 towers in Loudoun)
- Google Places API (parks data)

### Key Capabilities

- FEMA flood zone status with insurance requirement explanations (Zone AE, Zone X, etc.)
- Airport Impact Overlay District detection with noise disclosure levels (Ldn 65, Ldn 60)
- Power line proximity with voltage levels and visual impact scoring (1-5)
- Cell tower proximity with tower type, height, and carrier attribution where available
- Parks and recreation proximity
- Road classification and traffic level assessment
- Data center corridor proximity (Route 28 Ashburn area)

### Technical Implementation

The `LocationQualityAnalyzer` class queries multiple GIS layers in parallel for efficiency. Airport zones translate technical Ldn codes to plain-English severity levels. Flood zone responses include detailed explanations of insurance requirements and development restrictions. The `loudoun_utilities_analysis.py` module calculates minimum distance to power line segments using point-to-linestring geometry. Cell tower data uses enhanced CSV with FCC registration matching for carrier attribution.

**Key Modules:** `core/location_quality_analyzer.py`, `core/loudoun_utilities_analysis.py`

---

## 8. Transportation & Accessibility

### Overview

The Transportation section displays proximity to highways and major collectors with official VDOT traffic volumes (ADT), Metro Silver Line accessibility tier (Walk-to-Metro through Metro-Distant), and highway/collector proximity analysis. This multi-modal accessibility assessment uses official government data competitors don't integrate.

### Value Proposition

Commute time is a primary driver of home selection. This section answers: How close is the nearest highway? What's the actual traffic volume on nearby roads (a proxy for noise and congestion)? How far to the nearest Metro station? What's the realistic accessibility tier for daily transit commuting? Official VDOT traffic data and WMATA Metro station locations provide answers competitors can't offer.

### Data Sources

- VDOT Bidirectional Traffic Volume (ADT by road segment)
- WMATA Metro Silver Line (4 Loudoun stations + track alignment)
- Loudoun County GIS (road classifications)
- Pre-computed road context (travel times to key destinations)

### Key Capabilities

- Highway proximity with specific ADT display (e.g., "Route 7: 45,000 vehicles/day")
- Major collector proximity with ADT
- Metro accessibility tier classification:
  - Walk-to-Metro (<0.5 miles)
  - Bike-to-Metro (<1.5 miles)
  - Metro-Accessible (<5 miles)
  - Metro-Available (<10 miles)
  - Metro-Distant (>10 miles)
- Nearest Metro station with distance (Ashburn, Loudoun Gateway, Innovation Center, Dulles Airport)
- Travel time estimates to destinations (Tysons, DC, Dulles Airport)
- Road classification (residential, collector, arterial)

### Technical Implementation

The `LoudounTrafficVolumeAnalyzer` loads VDOT GeoJSON data and matches road names using normalization functions that handle variations (e.g., "LEESBURG PIKE" vs "HARRY BYRD HWY" for Route 7). ADT values are retrieved for the nearest road segment using coordinate matching. The `loudoun_metro_analysis.py` module calculates distances to all 4 Loudoun Metro stations and classifies accessibility tiers. Travel times are pre-computed in `road_context.json` to avoid real-time API calls.

**Key Modules:** `core/loudoun_traffic_volume.py`, `core/loudoun_metro_analysis.py`, `core/location_quality_analyzer.py`

---

## 9. Healthcare Access

### Overview

The Healthcare Access section analyzes proximity to hospitals, urgent care centers, and pharmacies with a focus on family-oriented factors. It includes Leapfrog safety ratings for hospitals, maternity services availability with NICU levels, and 24-hour pharmacy locations—critical for families with young children or planning to have children.

### Value Proposition

Healthcare access matters for families making relocation decisions. Parents want to know: Where is the nearest hospital with a good safety rating? Does it have maternity services? What level of NICU is available if there are complications? Where is the closest 24-hour pharmacy for late-night emergencies? This family-oriented analysis goes beyond simple proximity to provide actionable healthcare intelligence.

### Data Sources

- CMS Hospital Compare database (hospital quality metrics)
- Leapfrog Hospital Safety Grades
- Maternity services research (NICU levels, delivery capabilities)
- Loudoun Hospitals and Urgent Care GeoJSON
- Pharmacy location data

### Key Capabilities

- Hospital analysis with CMS star ratings (1-5 scale)
- Leapfrog safety grades and consecutive A-grade tracking
- Bed counts (acute care, ICU) and health system affiliations
- NICU levels (I-IV) for neonatal care capability assessment
- Maternity services detail: annual birth volumes, C-section rates, VBAC availability
- Urgent care center locations with distance calculations
- 24-hour pharmacy identification

### Technical Implementation

Healthcare data is pre-processed from CMS Hospital Compare exports and stored in GeoJSON and JSON formats. Distance calculations use haversine formula. The maternity hospitals JSON includes detailed NICU level information and delivery statistics. Integration with the location quality analyzer provides seamless display alongside other environmental factors.

**Key Modules:** `core/location_quality_analyzer.py`
**Data Files:** `data/loudoun/healthcare/`

---

## 10. Economic Indicators

### Overview

The Economic Indicators section synthesizes county-level economic data from the U.S. Census Bureau, Bureau of Labor Statistics, and Loudoun County Annual Comprehensive Financial Reports to provide forward-looking context on employment trends, workforce composition, and major employer dynamics. This reveals economic shifts that affect property values—like tech company market entries or public sector employment growth over 18 years.

### Value Proposition

Economic stability affects property values and investment risk. An area with low unemployment, high labor force participation, and diverse industry mix is more resilient to economic downturns. The 18-year major employers history (2008-2025) reveals structural shifts that explain neighborhood evolution—Amazon's entry in 2020, AOL's exit in 2014, LCPS's 43% workforce growth. This longitudinal perspective provides investment context competitors can't match.

### Data Sources

- Census ACS DP03 Profile (LFPR, industry employment mix)
- Bureau of Labor Statistics LAUS (unemployment rate, labor force)
- Loudoun County ACFR (major employers, manually extracted 2008-2025)

### Key Capabilities

- Labor Force Participation Rate with comparison to Virginia and national averages
- Unemployment rate with year-over-year change and direction indicator (improving/stable/worsening)
- Industry employment mix horizontal bar chart (top 6 sectors or all 13)
- Major employers by year (2008-2025) with employee counts/ranges
- Employer trend summaries (LCPS growth, Amazon entry, AOL exit)
- Data sources transparency with update dates

### Technical Implementation

The `economic_indicators.py` module combines Census ACS profile data (DP03 table) with BLS LAUS time series. Major employers data is stored in `data/loudoun/major_employers.json`, manually extracted from annual ACFR PDF documents—a labor-intensive curation that provides unique longitudinal value. Industry employment charts use Plotly with `uniformtext` settings to prevent label shrinking. Employer DataFrames are pre-created at page load for instant tab switching.

**Key Modules:** `core/economic_indicators.py`, `core/census_api.py`

---

## 11. AI-Powered Synthesis

### Overview

The AI Synthesis section uses Claude API to generate property narratives that synthesize all collected data into coherent, insight-dense prose. The narrative identifies what genuinely stands out about the property, acknowledges trade-offs honestly, and provides the local context that template-based reports miss. It reads like advice from a knowledgeable friend—conversational yet grounded in data.

### Value Proposition

Raw data is overwhelming. Even with 11 feature sections, users need synthesis to understand what matters most. The AI narrative answers: What should I actually pay attention to about this property? What are the genuine trade-offs? Who is this property ideal for? Unlike template-based reports that produce generic text regardless of data, the AI synthesis adapts to each property's unique characteristics.

### Data Sources

- All other platform data sources (compiled and passed to Claude)
- Claude API for narrative generation

### Key Capabilities

Six-section narrative structure:

1. **What Stands Out**: Opening hook with the 1-2 most distinctive features
2. **Schools Reality**: School assignment context with percentile rankings and peer comparisons
3. **Daily Reality**: Commute patterns, traffic, and neighborhood convenience factors
4. **Worth Knowing**: Important but non-obvious context that affects decisions
5. **Investment Lens**: Development activity at 2-mile and 5-mile radii, market position, growth indicators
6. **Bottom Line**: Synthesis of ideal buyer profile—who this property is perfect for

### Technical Implementation

The `compile_narrative_data()` function gathers analysis results from all modules into a structured dictionary. This is passed to Claude with a detailed system prompt that instructs the AI to be direct, factual, and grounded in provided data—no generic real estate fluff or superlatives without data backing. Narratives are cached for 24 hours in file-based cache (`/cache/narratives/`) to reduce API costs and improve response time. The system prompt explicitly prohibits correlating demographics with school performance.

**Key Modules:** `core/loudoun_narrative_generator.py`

---

## Competitive Advantages

### What Competitors DON'T Have

| Capability | Available Here | Zillow | Redfin | CoStar |
|------------|----------------|--------|--------|--------|
| Building permits development trajectories | Yes | No | No | Limited |
| Zoning + comprehensive plan alignment | Yes | No | No | Limited |
| 5-year school SOL trends with peer comparison | Yes | No | No | No |
| Official VDOT traffic volumes | Yes | No | No | No |
| 18-year major employer history | Yes | No | No | No |
| 64-community proprietary HOA research | Yes | No | No | No |
| Census block group radius demographics | Yes | No | No | Limited |
| Cell tower proximity with FCC data | Yes | No | No | No |
| AI narrative synthesis | Yes | No | No | No |

### Why Official Government Data Matters

1. **Defensibility**: When an investor challenges a claim, we cite official government sources
2. **Accuracy**: Government data collected for regulatory purposes, not marketing
3. **Granularity**: Census block groups ~40x smaller than ZIP codes
4. **Completeness**: 100% capture of permits, sales, and recorded transactions
5. **Auditability**: Data trails back to specific government publications and APIs

### AI Synthesis vs Template Reports

Traditional property reports use template-based text generation: "This lovely home features..." Our AI synthesis is fundamentally different:

- **Adaptive**: Analyzes actual data to identify what genuinely stands out
- **Honest**: Acknowledges trade-offs that template reports ignore
- **Contextual**: Provides local context (e.g., "Data Center Alley" development pressure)
- **Grounded**: Every claim backed by provided data—no invented superlatives
- **Forward-Looking**: Development implications, not just historical comps

### Forward-Looking vs Backward-Looking

| Approach | Our Platform | Competitors |
|----------|--------------|-------------|
| **Development** | Predicts neighborhood change via permit analysis + zoning alignment | Shows what was built |
| **Schools** | 5-year trend trajectory reveals improving/declining schools | Static current rating |
| **Economics** | 18-year employer history reveals structural shifts | Current employment only |
| **Zoning** | 20-year comprehensive plan vision | Current zoning code only |
| **Value** | Appreciation forecast based on area trends | Historical comp average |

---

## Feature Integration Examples

### How Features Connect

**Building Permits + Zoning**: The development pressure score combines building permit analysis (what's being built) with zoning alignment analysis (what the county wants built). High permit activity in areas where current zoning misaligns with comprehensive plan creates the highest pressure scores—revealing where neighborhood transformation is most likely.

**Demographics + Economic Indicators**: The demographics section shows who lives in an area now (income, education, age distribution), while economic indicators explain why (major employers, industry mix, labor force participation). Together they reveal economic stability and growth trajectory.

**Transportation + Location Quality**: Traffic volumes from VDOT combine with Metro accessibility tiers and road context travel times to provide complete accessibility intelligence—not just "near Route 7" but "0.8 miles from Route 7 with 45,000 ADT and 35-minute rush hour drive to Tysons."

**AI Synthesis Weaving**: The narrative generator receives data from all 10 analytical features and synthesizes them into coherent prose. For example, combining school performance trends with development pressure to note: "The assigned elementary school improved 8 points in math over 5 years, but nearby permit activity suggests the neighborhood may transition over the next decade."

---

*Last Updated: December 2025*
