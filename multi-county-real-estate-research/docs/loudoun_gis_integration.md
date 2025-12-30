# Loudoun County GIS Integration

**Last Updated:** November 2025
**Phase:** 1 - Zoning
**Status:** In Progress

## Overview

Loudoun County provides comprehensive GIS data through ArcGIS REST services at https://logis.loudoun.gov/

We need to integrate with the zoning layer to get zoning codes and future land use information.

## Finding the Zoning Layer

### Step 1: Explore GIS Services

1. Go to https://logis.loudoun.gov/
2. Look for "GIS Services" or "REST Services" link
3. Find the zoning/land use service

Typical structure:
```
https://gis.loudoun.gov/arcgis/rest/services/[folder]/[service]/MapServer
```

### Step 2: Identify Zoning Layer

Look for layers named:
- "Zoning"
- "Zoning Districts"
- "Land Use"
- "Zoning Overlay"

Example endpoint:
```
https://gis.loudoun.gov/arcgis/rest/services/Planning/Zoning/MapServer/0
```

### Step 3: Test the Endpoint

Use the query interface to test:
```
https://gis.loudoun.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query
```

Parameters:
- `geometry`: -77.5636,39.1156 (lon, lat)
- `geometryType`: esriGeometryPoint
- `spatialRel`: esriSpatialRelIntersects
- `outFields`: *
- `returnGeometry`: false
- `f`: json

### Step 4: Identify Field Names

Check response for field names:
- Zoning code: ZONING, ZONE, ZONE_CODE?
- Description: ZONE_DESC, DESCRIPTION?
- Overlay: OVERLAY, OVERLAY_ZONE?
- Future land use: FLU, FUTURE_LAND_USE?

## Configuration

Once you find the endpoint and field names, update `config/loudoun.py`:

```python
zoning_api_endpoint="https://gis.loudoun.gov/arcgis/rest/services/.../MapServer/[layer]/query"
```

## Testing

After configuration:

```python
from config import get_county_config
from core.zoning_lookup import ZoningLookup

config = get_county_config("loudoun")
lookup = ZoningLookup(config)

# Test Ashburn (unincorporated)
result = lookup.get_zoning("Ashburn, VA", 39.0437, -77.4875)
print(f"Zoning: {result.zoning_code}")
print(f"Description: {result.zoning_description}")
```

## Common Issues

**Issue:** 401 Unauthorized
**Fix:** API may require authentication token

**Issue:** No features returned
**Fix:** Check coordinate order (lon, lat not lat, lon)

**Issue:** Wrong layer
**Fix:** Try different layer numbers (0, 1, 2, etc.)

## TODO

- [ ] Find Loudoun County GIS REST services URL
- [ ] Identify zoning layer endpoint
- [ ] Test query with known addresses
- [ ] Document field names
- [ ] Update config/loudoun.py with real endpoint
- [ ] Test integration end-to-end
