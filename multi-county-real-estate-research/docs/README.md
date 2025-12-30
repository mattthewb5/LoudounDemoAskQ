# Loudoun County Property Intelligence Platform

## Executive Summary

We integrate official government sources, commercial APIs, and proprietary research that mainstream platforms don't combine—and synthesize them into investment-grade intelligence. While others show property values and school ratings, we reveal development trajectories through permit patterns, assess location quality across traffic, transit, and zoning alignment, and provide forward-looking insights by connecting datasets that don't naturally integrate. It's not just data access—it's the comprehensive synthesis across disparate metrics that answers questions sophisticated buyers actually ask.

The platform serves real estate professionals making investment decisions—developers, commercial brokers, and agents—but the intelligence is equally valuable for families making the most important purchase of their lives. Whether you're analyzing a $50M development site or buying your first home, you get the same hyper-local insights: what's actually happening in the neighborhood, what the county envisions for the future, and whether this location aligns with your needs. This is not a consumer property search tool—it's an intelligence platform that transforms 18 integrated data sources into actionable insights.

This implementation focuses on Loudoun County, Virginia—one of America's wealthiest and fastest-growing counties—with an architecture designed for national scalability. The same integration framework can be replicated for any county with similar data availability.

**Think of it as having a knowledgeable local advisor who's done weeks of research.** We synthesize building permits, school trends, traffic patterns, and economic data into insights you can actually use—not data dumps you have to interpret yourself. The analysis is hyper-local: 1-mile and 3-mile radius demographics, assigned schools with subject-level test scores (reading, math, history, science) compared to county and state averages, and specific road segment traffic volumes.

## What Makes This Different

### The Competitive Moat: Integration + Synthesis

The platform's defensibility comes from integrating sources that competitors don't connect: official government data (Census, BLS, VDOE, VDOT, County GIS), commercial APIs (ATTOM, RentCast), and proprietary research that required manual curation. Examples of proprietary data:

- **Community Amenities**: 64 Loudoun County communities with researched HOA fees, amenities (pools, tennis, clubhouses), and community boundaries—data not available through any API
- **Major Employers**: 18-year historical trends extracted manually from County ACFR documents, revealing structural shifts like Amazon's entry (2020) and AOL's exit (2014)
- **Development Patterns**: Building permit analysis with cost weighting and infrastructure detection that reveals development trajectories competitors miss

It's not just access to individual data sources—it's the synthesis infrastructure that connects them into coherent intelligence.

### Platform Comparison

| Capability | Our Approach | Zillow/Redfin Approach |
|------------|--------------|------------------------|
| **Schools** | 5-year SOL score trends with peer school comparisons within 5-mile radius, Virginia state benchmarks | GreatSchools simplified 1-10 ratings |
| **Zoning** | Development probability scoring (0-100) with comprehensive plan alignment analysis | Basic zoning code lookup |
| **Demographics** | Census block group analysis at 1-mile and 3-mile radii with population-weighted aggregation | County or ZIP code averages |
| **Building Permits** | Development trajectory analysis with construction cost weighting, new construction ratios | Not available |
| **Economic Data** | 18-year major employer trends, industry employment mix, LFPR comparison to state/national | Not available |
| **Traffic Data** | VDOT segment-specific ADT volumes for highways and collectors | Not available |
| **Healthcare** | Hospital star ratings, safety grades, NICU levels, maternity metrics, bed counts, system affiliations | Hospital proximity only |
| **Environmental** | FEMA flood zones, airport noise overlay zones, power line proximity (80 segments with voltage levels) | Flood zone binary (yes/no) |
| **Infrastructure** | Cell tower mapping (110 towers), power transmission infrastructure | Not available |
| **Transit** | Metro Silver Line stations with distance calculations, track proximity | Not available |

### AI Synthesis

The platform uses Claude API to generate property narratives that read like advice from a knowledgeable friend—conversational yet data-driven. Rather than template-based reports, the AI:

- Identifies what genuinely stands out about each property
- Synthesizes insights across all 18 data sources
- Acknowledges trade-offs honestly
- Provides forward-looking development implications

## Key Features Overview

1. **Property Overview & Valuation**: Triangulated property values from ATTOM and RentCast with comparable sales analysis, sales history (2020-2025), and 1/3/5-year forecasts based on market trends.

2. **Building Permits Intelligence**: Development pressure scoring that analyzes nearby permit activity, construction costs, and new construction ratios to reveal neighborhood development trajectories.

3. **Zoning & Development Probability**: Current zoning with 2019 Comprehensive Plan alignment scoring—quantifying the gap between what exists and what the county envisions over 20 years.

4. **School Performance Analysis**: Assigned schools with 5-year test score trends across subjects (reading, math, history, science), Virginia state average comparisons, and peer school benchmarking based on geographic proximity.

5. **Neighborhood Intelligence**: 64 communities with proprietary HOA research including fees, amenities (pools, tennis, clubhouses), and community character profiles.

6. **Area Demographics**: Census ACS 5-year estimates at block group level, aggregated within 1-mile and 3-mile radii with population-weighted calculations.

7. **Location Quality Analysis**: Comprehensive environmental assessment including FEMA flood zones, Dulles Airport noise overlay zones, and power transmission line proximity showing 80 segments with voltage levels. Cell tower mapping (110 towers from FCC and County GIS) for infrastructure awareness.

8. **Transportation & Accessibility**: VDOT traffic volumes for specific road segments, Metro Silver Line access (4 Loudoun stations), and highway/collector proximity analysis.

9. **Healthcare Access**: Hospital analysis including CMS star ratings, Leapfrog safety grades, bed counts, health system affiliations, and maternity services detail (NICU levels, C-section rates, annual birth volumes). Urgent care and 24-hour pharmacy locations with drive times.

10. **Economic Indicators**: Labor force participation rates, industry employment breakdown across 13 sectors, unemployment tracking, and 18-year major employer trends revealing structural economic shifts.

11. **AI-Powered Synthesis**: Claude-generated narratives that weave all data sources into coherent analysis with six focused sections covering standout features, schools, daily reality, investment implications, and ideal buyer profiles.

*See [FEATURES.md](FEATURES.md) for detailed documentation of each feature.*

### How Features Connect

The platform's power comes from synthesis, not isolated data points:

- **Development Story**: Building permit patterns (200+ permits within 1 mile) + zoning analysis (Suburban Mixed-Use planned but Single-Family existing) = development pressure score of 73/100, revealing this quiet neighborhood faces significant redevelopment risk over 20 years

- **Economic Context**: Demographics showing median income $160K + Economic Indicators revealing 29.6% professional/scientific employment = explains why test scores are high and why home values appreciate faster than county average

- **Investment Intelligence**: Property valuation showing $2.1M estimate + School trends showing 8-point math improvement + Zoning showing upzone potential = reveals this property has appreciation tailwinds beyond the market average

**This cross-feature synthesis represents a significant opportunity for platform development.** The "Ask a Question" conversational interface can leverage these connections to answer complex queries like "Show me properties in good school districts with development upside" or "Where are tech workers moving, and what does that mean for schools?"

## Quick Start

### Prerequisites

- Python 3.9+
- Streamlit
- Required API keys (see Configuration)

### Installation

```bash
cd multi-county-real-estate-research
pip install -r requirements.txt
```

### Configuration

Create API key configuration at `~/.config/newco/api_keys.json`:

```json
{
  "GOOGLE_MAPS_API_KEY": "your-google-maps-key",
  "ATTOM_API_KEY": "your-attom-key",
  "RENTCAST_API_KEY": "your-rentcast-key",
  "ANTHROPIC_API_KEY": "your-anthropic-key",
  "CENSUS_API_KEY": "your-census-key",
  "BLS_API_KEY": "your-bls-key"
}
```

### Running the Application

```bash
streamlit run loudoun_streamlit_app.py
```

### Test Property

Use this address to verify the installation:
```
43422 Cloister Pl, Leesburg, VA 20176
```

## Project Structure

```
multi-county-real-estate-research/
├── loudoun_streamlit_app.py          # Main Streamlit application
├── core/                              # Data analysis modules (33 total)
│   ├── api_config.py                 # API key management
│   ├── attom_client.py               # ATTOM property data API
│   ├── rentcast_client.py            # RentCast rental/value API
│   ├── census_api.py                 # Census Bureau + BLS APIs
│   ├── demographics_calculator.py    # Population-weighted radius analysis
│   ├── demographics_formatter.py     # Demographics display formatting
│   ├── economic_indicators.py        # LFPR, industry mix, employers
│   ├── loudoun_school_performance.py # School SOL trends and peer analysis
│   ├── loudoun_school_percentiles.py # School percentile calculations
│   ├── loudoun_zoning_analysis.py    # Zoning and development probability
│   ├── loudoun_traffic_volume.py     # VDOT traffic data integration
│   ├── loudoun_metro_analysis.py     # Silver Line Metro proximity
│   ├── development_pressure_analyzer.py # Permit-based pressure scoring
│   ├── loudoun_narrative_generator.py   # AI synthesis with Claude
│   ├── location_quality_analyzer.py     # Environmental factors analysis
│   ├── loudoun_utilities_analysis.py    # Power line proximity
│   ├── loudoun_community_lookup.py      # Community/HOA matching
│   ├── community_spatial_lookup.py      # GIS-based community detection
│   ├── property_valuation_orchestrator.py # Unified valuation interface
│   ├── comparable_analyzer.py           # Comparable sales analysis
│   ├── forecast_engine.py               # Value projection models
│   ├── loudoun_sales_data.py            # County sales data (Parquet)
│   ├── infrastructure_detector.py       # Infrastructure proximity
│   ├── loudoun_gis_data.py              # GIS data loaders
│   ├── loudoun_places_analysis.py       # Google Places integration
│   ├── loudoun_valuation_context.py     # Valuation narrative context
│   ├── mls_sqft_lookup.py               # MLS square footage lookup
│   ├── school_lookup.py                 # Generic school lookup
│   ├── zoning_lookup.py                 # Generic zoning lookup
│   ├── jurisdiction_detector.py         # Town/county jurisdiction
│   ├── crime_analysis.py                # Crime analysis (placeholder)
│   └── market_adjustments.py            # Market adjustment factors
├── data/loudoun/                      # County-specific data files
│   ├── Cell-Towers/                  # FCC tower data (110 towers)
│   ├── building_permits/             # Geocoded permit data
│   ├── communities/                  # HOA amenity research (64 communities)
│   ├── config/                       # Road context, communities.json
│   ├── gis/                          # GIS extracts (traffic, zoning, etc.)
│   ├── healthcare/                   # CMS hospitals, maternity, urgent care
│   ├── sales/                        # County sales data (47K records, Parquet)
│   ├── schools/                      # School zone boundaries, coordinates
│   ├── subdivisions/                 # Subdivision boundaries
│   ├── transit/                      # Metro Silver Line stations/track
│   ├── utilities/                    # Power lines GeoJSON
│   └── major_employers.json          # ACFR employer data (2008-2025)
├── config/                            # County configuration classes
├── docs/                              # Documentation
└── requirements.txt                   # Python dependencies
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Rapid prototyping web UI with dark/light mode |
| **Visualization** | Plotly, Folium | Interactive charts and maps |
| **Spatial Analysis** | GeoPandas, Shapely | GIS operations and zone lookups |
| **Data Processing** | Pandas | Data manipulation and aggregation |
| **AI Integration** | Claude API (Anthropic) | Narrative synthesis |
| **External APIs** | ATTOM, RentCast, Census, BLS, Google Maps | Property data, demographics, geocoding |
| **GIS Data** | Loudoun County ArcGIS REST services | Zoning, flood, AIOD, school zones |

## Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, module structure, data flow, caching strategies | Engineers, CTOs |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Catalog of all 18 data integrations with update frequencies | Investors, Operations |
| [FEATURES.md](FEATURES.md) | User-facing capabilities with value propositions | Investors, Customers |
| [adding_a_county.md](adding_a_county.md) | Guide for geographic expansion | Engineers |

---

*Last Updated: December 2025*
