# FCC Cell Tower Data Investigation Report

**Date:** 2025-12-22
**Status:** Investigation Complete
**Type:** READ-ONLY (No Code Changes)

---

## Executive Summary

**CRITICAL FINDING:** The uploaded FCC data does **NOT** contain carrier/entity names. The carrier information (Verizon, AT&T, T-Mobile, etc.) is stored in a separate FCC file called `EN.dat` (Entity data), which was not uploaded.

---

## Files Analyzed

### 1. VA_Sort_CellTowers_22dec25.csv (FCC RA.dat - Virginia)

| Attribute | Value |
|-----------|-------|
| Rows | 4,176 |
| Columns | 49 |
| File Size | 1.1 MB |
| Format | CSV (comma-delimited) |

**Key Column Mapping:**

| Column | Field Name | Description | Sample Values |
|--------|------------|-------------|---------------|
| Column 1 | Record Type | Always "RA" | RA |
| Column 2 | Action Type | Registration type | REG |
| **Column 3** | **System ID** | **JOIN KEY to CO.dat** | A0001896 |
| Column 4 | Registration Number | 7-digit FCC ID | 1001761 |
| Column 5 | Application ID | Application number | 97278 |
| Column 6-9 | Status Codes | Various status flags | NE, M, A, T |
| Column 10-15 | Dates | Various dates | 8/26/1996 |
| Column 16 | Registration Status | A=Active, C=Cancelled | A |
| Column 18-21 | Contact Name | First/MI/Last/Suffix | (parsed name) |
| **Column 22** | **Contact Title** | NOT carrier name! | VP, President, Agent |
| Column 24 | Location Description | Address/location | 6 MI W OF I 295... |
| Column 25 | City | City name | RICHMOND |
| Column 26 | State | Always VA | VA |
| Column 27 | FIPS County | County code | 51041 |
| Column 28 | Zip Code | 5-digit zip | 23831 |
| Column 29 | Ground Elevation | Feet above sea level | 87 |
| Column 30 | Structure Height AGL | Height above ground | 46.6 |
| Column 31 | Overall Height AGL | Total height above ground | 91 |
| Column 32 | Overall Height AMSL | Height above mean sea level | 137.6 |
| **Column 33** | **Structure Type** | Type of structure | TOWER, BLDG, etc. |
| Column 34 | FAA Determination Date | FAA review date | 3/12/1996 |
| Column 35 | FAA Study Number | FAA case number | 96-AEA-0134-OE |

**⚠️ IMPORTANT:** Column 22 contains **contact person titles** (VP, President, Agent), NOT carrier/company names!

---

### 2. CO.dat (FCC Coordinate Data)

| Attribute | Value |
|-----------|-------|
| Rows | 199,982 |
| Columns | 18 |
| File Size | 16 MB |
| Format | Pipe-delimited (|) |

**Key Column Mapping:**

| Column | Field Name | Description | Sample Values |
|--------|------------|-------------|---------------|
| 0 | Record Type | Always "CO" | CO |
| 1 | Action Type | Registration type | REG |
| **2** | **System ID** | **JOIN KEY to RA.dat** | A0997592 |
| 3 | Registration Number | 7-digit FCC ID | 1298230 |
| 4 | Coordinate ID | Internal ID | 2697749 |
| 5 | Coordinate Type | T=Tower | T |
| **6** | **Latitude Degrees** | Degrees N | 36 |
| **7** | **Latitude Minutes** | Minutes | 36 |
| **8** | **Latitude Seconds** | Seconds | 48.5 |
| 9 | Lat Direction | N or S | N |
| 10 | Lat Total Seconds | Computed | 131808.5 |
| **11** | **Longitude Degrees** | Degrees W | 79 |
| **12** | **Longitude Minutes** | Minutes | 55 |
| **13** | **Longitude Seconds** | Seconds | 3.6 |
| 14 | Lon Direction | W or E | W |
| 15 | Lon Total Seconds | Computed | 287703.6 |

**Join Verification:**
- All 4,176 Virginia towers in RA.dat have matching coordinates in CO.dat
- Join on: RA.dat Column 3 = CO.dat Column 2 (System ID)

**Coordinate Conversion Formula:**
```
Latitude = degrees + minutes/60 + seconds/3600
Longitude = -(degrees + minutes/60 + seconds/3600)  # Negative for Western hemisphere
```

---

### 3. Loudoun_Telecom_Towers.shp (County GIS)

| Attribute | Value |
|-----------|-------|
| Total Towers | 110 |
| CRS | NAD83 / Virginia State Plane North |
| Geometry | Point |

**Field Mapping:**

| Field | Description | Sample Values |
|-------|-------------|---------------|
| OBJECTID | Unique ID | 1, 2, 3... |
| TE_SITE_NA | Site Name | Emergency Comm Center, Ryan, Leesburg #3 |
| TE_TYPE | Structure Type | Monopole, Lattice |
| **TE_FCC** | **FCC Registration #** | 1016113 (can join to FCC data!) |
| TE_GE | Ground Elevation | 381, 288, 343 |
| TE_AGL | Height Above Ground | 120, 150, 162 |
| TE_LOC | Location/Address | 16632 Courage Ct, Leesburg |
| TE_STATUS | Status | Built |
| TE_ZIP | Zip Code | 20175, 20147 |
| TE_TOWN | Town | LEESBURG, ASHBURN, STERLING |

**⚠️ NOTE:** No carrier/owner field in county data either!

---

## Critical Gap: Missing Carrier/Entity Data

### What We Have
- Tower locations (from CO.dat + shapefile)
- Tower heights (from RA.dat + shapefile)
- Registration numbers (for cross-referencing)
- Structure types (TOWER, MONOPOLE, etc.)
- Contact person names/titles (but NOT company names)

### What We're Missing
**EN.dat (Entity File)** - Contains:
- Entity name (Verizon Wireless, AT&T, Crown Castle, etc.)
- Entity type (licensee, owner, contact)
- Link to registration number

Without EN.dat, we cannot determine:
- Which carrier owns each tower
- Tower ownership history
- Tenant/colocation information

---

## Recommended Column Names for VA_Sort_CellTowers

```python
RA_COLUMN_NAMES = {
    'Column 1': 'record_type',
    'Column 2': 'action_type',
    'Column 3': 'system_id',         # JOIN KEY
    'Column 4': 'registration_num',
    'Column 5': 'application_id',
    'Column 6': 'status_code_1',
    'Column 7': 'status_code_2',
    'Column 8': 'fcc_region',
    'Column 9': 'tower_use_code',
    'Column 10': 'date_action',
    'Column 11': 'date_received',
    'Column 12': 'date_granted',
    'Column 13': 'date_constructed',
    'Column 14': 'date_dismantled',
    'Column 15': 'date_effective',
    'Column 16': 'registration_status',
    'Column 17': 'unused_1',
    'Column 18': 'contact_first_name',
    'Column 19': 'contact_mi',
    'Column 20': 'contact_last_name',
    'Column 21': 'contact_suffix',
    'Column 22': 'contact_title',     # NOT carrier name!
    'Column 23': 'signatory_flag',
    'Column 24': 'location_description',
    'Column 25': 'city',
    'Column 26': 'state',
    'Column 27': 'fips_county',
    'Column 28': 'zip_code',
    'Column 29': 'ground_elevation_ft',
    'Column 30': 'structure_height_agl_ft',
    'Column 31': 'overall_height_agl_ft',
    'Column 32': 'overall_height_amsl_ft',
    'Column 33': 'structure_type',
    'Column 34': 'faa_determination_date',
    'Column 35': 'faa_study_number',
    'Column 36': 'faa_circular',
    'Column 37': 'lighting_code',
    'Column 38': 'lighting_marks',
    'Column 39': 'lighting_intensity',
    'Column 40': 'unused_2',
    'Column 41': 'nepa_flag',
    'Column 42': 'nepa_category_flag',
    'Column 43': 'notification_date',
    'Column 44-49': 'reserved'
}
```

---

## Next Steps

### Option A: Request EN.dat File
1. User uploads EN.dat from FCC ASR data
2. Join EN.dat with RA.dat on registration number
3. Extract carrier/entity names
4. Create complete tower dataset

### Option B: Proceed Without Carrier Names
1. Merge RA.dat with CO.dat (coordinates)
2. Filter to Loudoun County (FIPS 51107)
3. Cross-reference with county shapefile
4. Create dataset with heights, locations, but NO carrier info

### Option C: Alternative Data Source
1. Use OpenCellID or similar crowd-sourced data
2. May have carrier information
3. Less authoritative than FCC data

---

## Sample Data Join (VA Towers with Coordinates)

```python
# Example of joining the data we have
import pandas as pd

# Load data
ra = pd.read_csv('VA_Sort_CellTowers_22dec25.csv', dtype=str)
co = pd.read_csv('CO.dat', sep='|', header=None, dtype=str)

# Join on system_id
merged = ra.merge(co, left_on='Column 3', right_on=2, how='left')

# Convert coordinates to decimal
merged['latitude'] = merged[6].astype(float) + merged[7].astype(float)/60 + merged[8].astype(float)/3600
merged['longitude'] = -(merged[11].astype(float) + merged[12].astype(float)/60 + merged[13].astype(float)/3600)

# Filter to Loudoun County (FIPS 51107)
loudoun = merged[merged['Column 27'] == '51107']
print(f"Loudoun County towers: {len(loudoun)}")
```

---

## Summary

| Data Source | Rows | Has Coordinates | Has Carrier Name | Has Heights |
|-------------|------|-----------------|------------------|-------------|
| VA_Sort_CellTowers (RA.dat) | 4,176 | ❌ | ❌ | ✓ |
| CO.dat | 199,982 | ✓ | ❌ | ❌ |
| Loudoun Shapefile | 110 | ✓ | ❌ | ✓ |

**Bottom Line:** We can identify tower locations and heights, but cannot determine carrier ownership without the EN.dat file.

---

## Athens Protection Verification

- `streamlit_app.py`: NOT examined or modified
- `clarke_*`, `athens_*`, `accpd_*`, `gosa_*`: NOT examined or modified
- Only examined data files in `/data/loudoun/Cell-Towers/`
