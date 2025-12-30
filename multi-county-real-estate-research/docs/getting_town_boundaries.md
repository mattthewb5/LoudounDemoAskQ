# Getting Real Town Boundary Data for Loudoun County

**Last Updated:** November 2025
**Status:** TODO - Need to download from Loudoun GIS
**Priority:** Medium (placeholder works for now, real data needed before production)

## Why We Need This

Loudoun County has 7 incorporated towns with separate zoning ordinances:
1. Leesburg (county seat, largest town)
2. Purcellville (western Loudoun)
3. Middleburg (horse country)
4. Hamilton
5. Lovettsville
6. Round Hill
7. Hillsboro

The jurisdiction detector needs official town boundaries to determine if an address is in a town (town zoning) or unincorporated county (county zoning).

## Current Status

**Placeholder data exists:** `data/loudoun/town_boundaries.geojson`
- Contains rough approximations for Leesburg and Purcellville
- Good enough for testing infrastructure
- NOT accurate for production use

## Data Source

**Official Source:** Loudoun County GIS Portal
**URL:** https://logis.loudoun.gov/

## How to Get Real Boundaries

### Step 1: Access Loudoun County GIS

1. Go to https://logis.loudoun.gov/
2. Look for "Interactive Map" or "GIS Portal"
3. Search for layers:
   - "Municipal Boundaries"
   - "Town Limits"
   - "Incorporated Towns"
   - "Jurisdiction Boundaries"

### Step 2: Download GeoJSON

**Option A: Direct Download (If Available)**
- Look for download/export option
- Select GeoJSON format
- Download all town boundaries

**Option B: REST API Query**

Loudoun County likely has ArcGIS REST services.

Example endpoint structure:
```
https://gis.loudoun.gov/arcgis/rest/services/[service]/MapServer/[layer]/query

Query parameters:
?where=1=1
&outFields=*
&f=geojson
&returnGeometry=true
```

This returns all features in GeoJSON format.

**Option C: Manual Export from Map**

1. Use the interactive map
2. Select each town boundary
3. Export to GeoJSON
4. Combine into single file

### Step 3: Verify Downloaded Data

After downloading, verify the GeoJSON has:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Leesburg",  // Or "NAME", "Town", check field names
        // ... other properties
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[...]]]
      }
    },
    // ... 6 more towns
  ]
}
```

### Step 4: Test with Known Addresses

After replacing placeholder with real data:

**Test addresses in each town:**
- Downtown Leesburg (should return Town of Leesburg)
- Downtown Purcellville (should return Town of Purcellville)
- Ashburn Shopping Plaza (should return unincorporated county)
- Sterling area (should return unincorporated county)

**Test boundary edges:**
- Addresses right at town boundaries
- Verify no addresses are misclassified

## What the Final GeoJSON Should Include

**All 7 incorporated towns:**
1. ✓ Leesburg (partial placeholder)
2. ✓ Purcellville (partial placeholder)
3. ✗ Middleburg (TODO)
4. ✗ Hamilton (TODO)
5. ✗ Lovettsville (TODO)
6. ✗ Round Hill (TODO)
7. ✗ Hillsboro (TODO)

**Required properties for each town:**
- `name` or `NAME` field
- Valid polygon geometry
- Coordinate system: WGS84 (EPSG:4326)

## Notes

- **Accuracy matters:** Wrong jurisdiction = wrong zoning authority
- **Coordinate system:** Must be WGS84 (lat/lon) for our detector
- **Property names:** Check if GIS uses "name", "NAME", "Town", etc.
- **Attribution:** Document source and date in metadata

## When to Do This

**Timeline:**
- **Now (Week 1):** Placeholder is fine for building infrastructure
- **Week 2:** Get real data before testing actual zoning lookup
- **Before Production:** Must have real boundaries

**Priority:** Medium
- Not blocking current development
- Needed before Phase 1 (Zoning) completion
- Critical for accuracy but infrastructure works without it

## TODO Checklist

- [ ] Access Loudoun County GIS portal
- [ ] Find municipal boundaries layer
- [ ] Download GeoJSON for all 7 towns
- [ ] Replace placeholder file
- [ ] Test with known Leesburg addresses
- [ ] Test with Ashburn addresses (unincorporated)
- [ ] Test boundary edges
- [ ] Document source and date
- [ ] Commit real boundaries to repo
