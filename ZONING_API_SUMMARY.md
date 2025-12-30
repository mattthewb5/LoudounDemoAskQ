# Athens-Clarke County Zoning API Summary

## Test Results

✅ **Both APIs Working Successfully**

Tested with: 150 Hancock Avenue, Athens, GA (33.9519, -83.3774)

---

## 1. Parcel Zoning Types API

**Endpoint:** `https://enigma.accgov.com/server/rest/services/Parcel_Zoning_Types/FeatureServer/0/query`

### Key Fields Available:

| Field Name | Type | Description |
|------------|------|-------------|
| `PARCEL_NO` | String | Parcel identifier |
| `PIN` | String | Property Identification Number |
| `CurrentZn` | String | **Current zoning code** (e.g., "G", "RS-8", "C-D") |
| `CombinedZn` | String | Combined zoning designation |
| `Acres` | Double | Property size in acres |
| `SplitZoned` | String | Indicates if property has split zoning |
| `RGProperty` | String | Related to RG properties |
| `created_date` | Date | When record was created |
| `last_edited_date` | Date | Last update timestamp |

### Sample Response:
```json
{
  "PARCEL_NO": "171    001L",
  "PIN": "171001L",
  "CurrentZn": "G",
  "CombinedZn": "G",
  "Acres": 14.08478691,
  "SplitZoned": " "
}
```

**Test Result:** 5 parcels found within 100m of test location

---

## 2. Future Land Use API

**Endpoint:** `https://enigma.accgov.com/server/rest/services/FutureLandUse/FeatureServer/0/query`

### Key Fields Available:

| Field Name | Type | Description |
|------------|------|-------------|
| `PARCEL_NO` | String | Parcel identifier |
| `Updated_FL` | String | **Future land use designation** (e.g., "Government", "Single-Family Residential") |
| `ACRES` | Double | Property size in acres |
| `Split` | String | Indicates split future land use |
| `Change` | String | Indicates if changed from original plan |
| `DATE_CHANG` | String | Date of change |
| `PROJECT_NO` | String | Related project number |

### Sample Response:
```json
{
  "PARCEL_NO": "171    001I",
  "Updated_FL": "Government",
  "ACRES": 3.73633856,
  "Split": " ",
  "Change": "Yes"
}
```

**Test Result:** 5 parcels found within 100m of test location

---

## API Usage Notes

### Required Parameters:
- `geometry`: Longitude,Latitude format (e.g., "-83.3774,33.9519")
- `geometryType`: "esriGeometryPoint"
- `inSR`: "4326" (WGS84 coordinate system - **required for lat/lon input**)
- `spatialRel`: "esriSpatialRelIntersects"
- `outFields`: "*" (all fields)
- `f`: "json"

### Optional Parameters:
- `distance`: Search radius (default: 100)
- `units`: Distance units (e.g., "esriSRUnit_Meter")
- `returnGeometry`: "true" to get polygon boundaries

### Response Format:
- Spatial Reference: WKID 102667 / EPSG:2240 (Georgia West State Plane)
- Geometry Type: Polygon (property boundaries)
- Features: Array of matching parcels

---

## Common Zoning Codes in Athens-Clarke County

Based on Athens-Clarke County Unified Development Code:

### Residential Zones:
- **RS-40**: Single-family residential, 40,000 sq ft minimum
- **RS-25**: Single-family residential, 25,000 sq ft minimum
- **RS-15**: Single-family residential, 15,000 sq ft minimum
- **RS-8**: Single-family residential, 8,000 sq ft minimum
- **RS-5**: Single-family residential, 5,000 sq ft minimum
- **RM-1**: Multi-family residential, low density
- **RM-2**: Multi-family residential, medium density
- **RM-3**: Multi-family residential, high density

### Commercial Zones:
- **C-N**: Commercial-Neighborhood
- **C-G**: Commercial-General
- **C-D**: Commercial-Downtown
- **C-R**: Commercial-Regional

### Other Zones:
- **G**: Government/Institutional
- **MU**: Mixed Use
- **I-N**: Industrial-Neighborhood
- **I-G**: Industrial-General
- **A-R**: Agricultural-Residential

---

## Integration Possibilities

### What We Can Add to the Tool:

1. **Current Zoning Classification**
   - Show property's current zoning code
   - Explain what uses are allowed
   - Note density/size restrictions

2. **Future Land Use**
   - Show planned future development type
   - Flag if different from current zoning
   - Indicate potential for rezoning

3. **Property Size**
   - Display acreage
   - Compare to zoning minimums
   - Note if undersized/oversized for zone

4. **Development Potential**
   - Flag vacant/underdeveloped parcels
   - Show if property could be subdivided
   - Indicate redevelopment likelihood

5. **Neighborhood Context**
   - Show nearby parcel zones
   - Identify if in transition area
   - Flag mixed-use corridors

---

## Next Steps

1. Create `zoning_lookup.py` module with:
   - Function to get zoning for an address
   - Zoning code explanations
   - Future land use interpretation

2. Create `ZoningInfo` data class similar to SchoolInfo and CrimeAnalysis

3. Integrate with `unified_ai_assistant.py`

4. Add zoning section to Streamlit UI

5. Update AI prompts to include zoning context
