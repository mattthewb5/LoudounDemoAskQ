# LCSO Crime Dashboard Research Guide

**Purpose:** Find and configure Loudoun County Sheriff's Office Crime Dashboard API endpoint

**Status:** Research Pending
**Phase:** 2 - Crime Data (Week 3)
**Last Updated:** November 2025

---

## Background

**LCSO Crime Dashboard:**
- Launched: August 2025
- Updates: Nightly (per research)
- Purpose: Public crime transparency and safety information
- Coverage: Loudoun County Sheriff's Office jurisdiction

**Why This Matters:**
- Real-time crime data for safety scoring
- Multi-jurisdiction support (Sheriff vs town PD)
- Personal validation possible (developer lives in Loudoun)

---

## Research Checklist

### Step 1: Find the Crime Dashboard

**Primary Sources to Check:**

1. **Loudoun County Sheriff's Office Website**
   - Main site: https://www.loudoun.gov/sheriff
   - Look for: "Crime Dashboard", "Crime Map", "Crime Statistics", "Public Safety Data"
   - Check: Press releases, news section for August 2025 launch announcement

2. **Loudoun GIS Portal**
   - Portal: https://logis.loudoun.gov/
   - Look for: Crime layers, public safety data
   - Check: Same REST services directory we used for zoning
   - Possible endpoint pattern: `.../rest/services/.../Crime/MapServer`

3. **Loudoun County Open Data**
   - Check: https://data.loudoun.gov/ (if exists)
   - Look for: Crime datasets, API documentation
   - Alternative: Search for "Loudoun County open data portal"

4. **Web Search Strategies**
   - "Loudoun County Sheriff Crime Dashboard"
   - "LCSO Crime Map Virginia"
   - "Loudoun County crime data API"
   - "Loudoun County Sheriff crime statistics 2025"

### Step 2: Identify the API Endpoint

**If Dashboard Uses ArcGIS (like zoning):**

Look for REST endpoint pattern:
```
https://logis.loudoun.gov/gis/rest/services/.../Crime/MapServer/[layer]/query
```

**Check for:**
- Layer structure (what layers are available)
- Field names (incident type, date, location, etc.)
- Spatial reference requirements (we needed `inSR=4326` for zoning!)
- Date format and filtering options

**If Dashboard Uses Different Technology:**

Document:
- Base URL
- Authentication requirements (API key, OAuth, public?)
- Query parameters
- Response format (JSON, XML, CSV?)
- Rate limits or usage restrictions

### Step 3: Analyze the Data Structure

**Required Fields:**
- Incident ID (unique identifier)
- Incident Type (ASSAULT, THEFT, etc.)
- Date/Time of incident
- Location (address or coordinates)
- Jurisdiction (Sheriff vs town PD)

**Optional But Useful:**
- Latitude/Longitude (for radius searches)
- Incident description
- Case number
- Disposition/status

**Test Query:**
```
# Example for ArcGIS REST
params = {
    'where': "IncidentDate >= '2024-01-01'",
    'geometry': '-77.5636,39.1156',  # Leesburg coordinates
    'geometryType': 'esriGeometryPoint',
    'distance': 1,  # 1 mile radius
    'units': 'esriSRUnit_StatuteMile',
    'inSR': '4326',  # WGS84 (CRITICAL!)
    'outFields': '*',
    'returnGeometry': 'false',
    'f': 'json'
}
```

### Step 4: Map Field Names

**Create mapping table:**

| Our Code Field | LCSO Field Name | Example Value |
|----------------|-----------------|---------------|
| incident_id | ? | "2024-12345" |
| incident_type | ? | "THEFT" |
| date | ? | "2024-11-15" |
| address | ? | "Main St, Leesburg" |
| lat | ? | 39.1156 |
| lon | ? | -77.5636 |
| jurisdiction | ? | "LCSO" or "Leesburg PD" |

**Common Field Name Patterns:**
- Incident ID: INCIDENT_ID, CASE_NUM, REPORT_ID, OBJECTID
- Type: INCIDENT_TYPE, OFFENSE, CRIME_TYPE, UCR_CODE
- Date: INCIDENT_DATE, REPORT_DATE, OCCURRED_DATE
- Location: ADDRESS, LOCATION, INCIDENT_LOCATION
- Coordinates: LAT/LON, LATITUDE/LONGITUDE, X/Y
- Jurisdiction: AGENCY, JURISDICTION, DEPARTMENT

### Step 5: Test with Real Data

**Test Locations (unincorporated = LCSO jurisdiction):**

1. **Ashburn** (39.0437, -77.4875) - Eastern Loudoun, unincorporated
2. **Sterling** (39.0061, -77.4286) - Northern Loudoun, unincorporated
3. **South Riding** (38.9201, -77.5061) - Central Loudoun, unincorporated

**Test Date Ranges:**
- Last 30 days
- Last 90 days (our default)
- Last 365 days

**Verify:**
- Results are returned
- Incident counts seem reasonable
- Types make sense (not all "OTHER")
- Dates are within requested range
- Coordinates fall within Loudoun County

---

## Alternative Approaches

### If No Public API Available

**Option A: Web Scraping**
- If dashboard is web-only, may need to scrape HTML
- NOT IDEAL but possible
- Check robots.txt and terms of service
- Consider requesting official API access

**Option B: Manual Lookup Documentation**
- Document how to manually check crime data
- Provide links to dashboard for users
- Note: "Crime data lookup requires manual verification"

**Option C: Contact LCSO**
- Email: sheriff@loudoun.gov
- Request: API access for public crime data
- Purpose: Real estate safety research tool
- Mention: Using GIS data already, want to add crime layer

**Option D: Use Alternative Source**
- CrimeReports.com (some agencies use this)
- SpotCrime.com (aggregates from multiple sources)
- Note: Less official, may be incomplete

### If Town Police Data Not Available

**Fallback Strategy:**
- Use LCSO data for all jurisdictions
- Note: "Town police data may not be included"
- Document: Which towns have their own PD
- Future: Contact each town PD individually

**Loudoun Towns with Police Departments:**
- Leesburg: Yes, has own PD
- Purcellville: Yes, has own PD
- Others: Likely contract with LCSO (verify)

---

## Expected Configuration

**Once endpoint is found, update `config/loudoun.py`:**

```python
# ===== CRIME & SAFETY =====
crime_data_source="api",
crime_api_endpoint="https://[ACTUAL_ENDPOINT_HERE]",  # From research
crime_data_file_path=None,

# ===== FEATURE FLAGS =====
has_crime_data=True,  # ✅ Phase 2 complete
```

**Field mappings in `core/crime_analysis.py` (line 320+):**

```python
# Add LCSO-specific field names to detection
# Similar to how we added ZO_ZONE, ZD_ZONE_DESC for zoning
```

---

## Validation Plan

**Once API is configured:**

1. **Run integration tests:**
   ```bash
   python tests/test_crime.py
   ```

2. **Test with known areas:**
   - Compare results to local knowledge
   - Verify safety scores make sense
   - Check incident types are categorized correctly

3. **Personal validation:**
   - Test local area (developer lives in Leesburg)
   - Verify incident counts match perception
   - Check jurisdiction detection (town vs county)

4. **Create findings document:**
   - Similar to `docs/loudoun_gis_findings.md`
   - Document API structure, field names, test results
   - Note any quirks or special requirements

---

## Success Criteria

- ✅ Found LCSO Crime Dashboard
- ✅ Identified API endpoint (or confirmed no public API)
- ✅ Tested query returns data
- ✅ Mapped field names
- ✅ Updated configuration
- ✅ Integration tests passing
- ✅ Real data validated against local knowledge

---

## Notes

**Remember from Zoning Integration:**
- Spatial reference (`inSR=4326`) was CRITICAL
- Field names were county-specific (ZO_ZONE vs ZONING)
- Test with multiple locations to verify
- Document quirks immediately

**Questions to Answer:**
- Does LCSO dashboard include all of Loudoun County?
- Are incorporated towns included or separate?
- What date range is available?
- Are addresses exact or approximate (privacy)?
- Is real-time data available or just nightly updates?

---

## Timeline Estimate

**If API exists and is public:** 2-4 hours
- 1 hour: Find and explore endpoint
- 1 hour: Map fields and test queries
- 1 hour: Update code and test
- 1 hour: Validation and documentation

**If no public API:** TBD
- Depends on alternative approach chosen
- May require LCSO contact and approval
- Could delay Phase 2 completion

---

## Next Steps

1. Start research (begin with LCSO website)
2. Document findings as you go
3. Once endpoint found, update this document
4. Test thoroughly before marking complete
5. Create completion document (like `PHASE_1_COMPLETE.md`)
