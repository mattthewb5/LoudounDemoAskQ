# Loudoun County, Virginia - Data Files

**Purpose:** Store Loudoun-specific static data that can't be fetched via API

## Incorporated Town Boundaries

File: `town_boundaries.geojson`

Loudoun County has 7 incorporated towns with separate zoning jurisdictions:
1. Leesburg (county seat)
2. Purcellville
3. Hamilton
4. Hillsboro
5. Lovettsville
6. Middleburg
7. Round Hill

**Why needed:** To detect if an address is within an incorporated town boundary, which affects zoning lookup.

**Data source:** Loudoun County GIS portal
- URL: https://logis.loudoun.gov/
- Layer: Incorporated town boundaries
- Format: GeoJSON for easy Python parsing

## Zoning Code Lookup Tables

Directory: `zoning_codes/`

Each incorporated town has its own zoning ordinance. These JSON files map zoning codes to descriptions:

- `leesburg.json` - Town of Leesburg zoning codes
- `purcellville.json` - Town of Purcellville zoning codes
- `hamilton.json` - Town of Hamilton zoning codes
- `hillsboro.json` - Town of Hillsboro zoning codes
- `lovettsville.json` - Town of Lovettsville zoning codes
- `middleburg.json` - Town of Middleburg zoning codes
- `round_hill.json` - Town of Round Hill zoning codes

**Format:**
```json
{
  "R-1": {
    "description": "Residential - Single Family",
    "min_lot_size": "1 acre",
    "permitted_uses": ["single family residential", "agriculture"]
  },
  "C-1": {
    "description": "Commercial - Downtown",
    "permitted_uses": ["retail", "office", "restaurant"]
  }
}
```

## School Performance Cache (optional)

File: `school_performance_cache.json`

Cache of Virginia School Quality Profiles data to reduce API calls during development/testing.

**Status:** Not yet implemented - all data fetched live from VDOE

## Data Maintenance

**Update Frequency:**
- Town boundaries: Rarely change (check annually)
- Zoning codes: Check for updates when towns revise ordinances
- School performance: Updated annually by VDOE (August/September)

**How to Update:**
1. Check Loudoun County GIS portal for updated boundaries
2. Check each town's website for zoning ordinance updates
3. Re-export GeoJSON/JSON files as needed

## API vs Static Data Decision

**Use API when:**
- Data changes frequently (daily/weekly)
- Data source has reliable API
- Fresh data is critical

**Use static files when:**
- Data rarely changes
- No API available
- Need offline capability
- Want to reduce API load

**Loudoun Decision:**
- Schools: API (LCPS School Locator, VDOE)
- Crime: API (LCSO Dashboard, GeoHub)
- Zoning: API for county, static files for towns (no town APIs)
- Town boundaries: Static file (rarely change)
