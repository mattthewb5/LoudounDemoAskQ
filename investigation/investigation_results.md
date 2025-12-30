# Economic Data Investigation Results
## Loudoun County Real Estate Intelligence Platform

**Investigation Date:** December 29, 2025
**Branch:** `claude/add-offering-memorandum-YVwlC`
**Status:** ✅ All Tasks Completed Successfully

---

## Executive Summary

All three economic data sources have been successfully tested and validated:

| Feature | Data Source | Status | Complexity |
|---------|-------------|--------|------------|
| Major Employers | CAFR PDF (Table O) | ✅ Working | Low - PDF extraction |
| Labor Force Participation | Census ACS DP03 | ✅ Working | Low - Single API call |
| Industry Employment Mix | Census ACS DP03 | ✅ Working | Low - Single API call |

**Recommendation:** All three features can be integrated into the existing platform with minimal refactoring.

---

## Task 1: Major Employers Compilation

### Feasibility: ✅ CONFIRMED

#### Data Source
- **Primary:** Loudoun County ACFR (Annual Comprehensive Financial Report)
- **Table:** "Table O - Principal Employers" (formerly Table N pre-2021)
- **URL Pattern:** `https://www.loudoun.gov/DocumentCenter/View/{ID}/`

#### Extraction Method
- PDFs are **machine-readable** (not scanned images)
- PyPDF2 successfully extracts text
- No OCR required

#### Data Quality Notes
- Employment often given as **ranges** (e.g., "2,500-5,000") not exact counts
- Only LCPS and County of Loudoun report exact employee counts
- Each ACFR compares current year to 9 years prior

#### Sample Output (FY2025)

| Rank | Employer | Employees | % of Total | Industry |
|------|----------|-----------|------------|----------|
| 1 | Loudoun County Public Schools | 13,281 | 6.71% | Education |
| 2 | County of Loudoun | 5,059 | 2.56% | Government |
| 3 | U.S. Department of Homeland Security | 2,500-5,000 | 1.89% | Federal Gov |
| 4 | Northrop Grumman | 2,500-5,000 | 1.89% | Aerospace/Defense |
| 5 | United Airlines | 2,500-5,000 | 1.89% | Aviation |
| 6 | Amazon | 2,500-5,000 | 1.89% | Tech/E-commerce |
| 7 | Inova Health System | 2,500-5,000 | 1.89% | Healthcare |
| 8 | Verizon | 1,000-2,500 | 0.88% | Telecom |
| 9 | Dynalectric | 1,000-2,500 | 0.88% | Construction |
| 10 | Walmart | 1,000-2,500 | 0.88% | Retail |

**Top 10 represent 21.36% of total county employment**

#### Historical CAFRs Available
- FY2001-FY2013: Archive at `/DocumentCenter/Index/3215`
- FY2014-FY2025: Individual PDFs available (see `major_employers_historical.json`)

#### Key Trends Identified
- **LCPS growth:** 10,098 (2011) → 13,281 (2025) = +31.5%
- **County gov growth:** 3,303 (2011) → 5,059 (2025) = +53.2%
- **New entrants:** Amazon, Dynalectric, Walmart
- **Departed:** AOL, M.C. Dean, Swissport, USPS
- **Declining:** Verizon (rank 3 → 8)

#### Files Created
- `major_employers_fy2025.json` - Current year structured data
- `major_employers_historical.json` - Multi-year compilation

---

## Task 2: Labor Force Participation Rate

### Feasibility: ✅ CONFIRMED

#### Data Sources Compared

| Source | Recency | LFPR Available? | Geographic Level |
|--------|---------|-----------------|------------------|
| BLS LAUS | Monthly | ❌ Must calculate | County, State |
| Census ACS 5-Year | ~2 years lag | ✅ Pre-calculated | All geographies |

#### BLS LAUS API Results

**Endpoint:** `https://api.bls.gov/publicAPI/v2/timeseries/data/`

```
Series IDs for Loudoun County (FIPS 51107):
- LAUCN511070000000006 = Labor Force
- LAUCN511070000000005 = Employment
- LAUCN511070000000003 = Unemployment Rate
```

**Latest Data (December 2024):**
- Labor Force: 253,982
- Employment: 248,432
- Unemployment: 5,550 (2.2%)

**Limitation:** BLS does NOT publish county-level LFPR. Would need to:
1. Get Labor Force from BLS
2. Get Population 16+ from Census
3. Calculate: `LFPR = (Labor Force / Pop 16+) × 100`

#### Census ACS DP03 API Results

**Endpoint:** `https://api.census.gov/data/2023/acs/acs5/profile`

**Variable:** `DP03_0002PE` = Labor Force Participation Rate (pre-calculated!)

#### LFPR Comparison (Census ACS 5-Year 2023)

| Geography | LFPR | Difference from USA |
|-----------|------|---------------------|
| **Loudoun County** | **74.1%** | **+10.6 pts** |
| Virginia | 65.6% | +2.1 pts |
| United States | 63.5% | baseline |

**Key Insight:** Loudoun's LFPR is 10.6 percentage points above the national average, indicating an exceptionally engaged workforce.

#### Recommendation
**Use Census ACS DP03** for LFPR because:
1. Pre-calculated (no additional computation)
2. Consistent methodology across geographies
3. Allows easy comparison to state/national
4. Already integrated in existing Census API infrastructure

**Use BLS LAUS** for:
1. Monthly unemployment rate updates
2. Labor force trends over time
3. More current data (1-2 month lag vs 2-year for ACS)

#### Files Created
- `test_bls_laus_api.py` - Working BLS API script
- `bls_loudoun_response.json` - Full BLS response
- `test_census_dp03_api.py` - Working Census API script
- `census_dp03_results.json` - Full Census response

---

## Task 3: Industry Employment Mix

### Feasibility: ✅ CONFIRMED

#### Data Source
- Census ACS 5-Year DP03 Profile
- Variables: `DP03_0033PE` through `DP03_0045PE`

#### Loudoun County Industry Mix (2023)

| Sector | % | Visual |
|--------|---|--------|
| Professional, scientific, management, admin | **29.6%** | ████████████████████████████████████ |
| Educational services, health care, social | 16.8% | ████████████████████ |
| Public administration | 8.0% | █████████ |
| Finance, insurance, real estate | 7.9% | █████████ |
| Retail trade | 7.4% | ████████ |
| Arts, entertainment, accommodation, food | 6.7% | ███████ |
| Construction | 5.0% | █████ |
| Other services | 4.7% | █████ |
| Manufacturing | 4.4% | █████ |
| Transportation, warehousing, utilities | 4.1% | ████ |
| Information (Tech/Data Centers) | 3.7% | ████ |
| Wholesale trade | 1.2% | █ |
| Agriculture, forestry, fishing, mining | 0.6% | - |

#### Key Sector Comparisons

| Sector | Loudoun | Virginia | USA | Loudoun vs USA |
|--------|---------|----------|-----|----------------|
| Professional/Scientific/Management | **29.6%** | 16.6% | 12.4% | **+17.2 pts** |
| Information (Tech/Data Centers) | **3.7%** | 1.8% | 1.9% | **+1.8 pts (1.9x)** |
| Public Administration | 8.0% | 8.9% | 4.7% | +3.3 pts |
| Education/Healthcare | 16.8% | 22.2% | 23.4% | -6.6 pts |

#### Key Insights

1. **Professional Services Dominance:** Loudoun's 29.6% vs national 12.4% reflects the concentration of government contractors, tech companies, and professional services firms.

2. **Information Sector:** At 3.7%, Loudoun is 1.9x the national average, reflecting data center presence (though this may undercount since many data center workers are classified under "Professional Services").

3. **Lower Healthcare/Education:** Despite LCPS being the #1 employer, the education/healthcare sector is 6.6 points below national average, suggesting the professional services sector overshadows it proportionally.

#### Ready for Pie Chart

The data is formatted for direct use in visualization:

```json
{
  "industry_mix": [
    {"sector": "Professional & Technical Services", "percentage": 29.6},
    {"sector": "Education & Healthcare", "percentage": 16.8},
    {"sector": "Public Administration", "percentage": 8.0},
    ...
  ]
}
```

---

## Integration Recommendations

### Estimated Complexity

| Feature | New Files | Existing File Changes | API Calls | Effort |
|---------|-----------|----------------------|-----------|--------|
| Major Employers | 1 JSON data file | `loudoun_streamlit_app.py` UI | 0 (static) | Low |
| LFPR | None | Add to `census_api.py` | +1 | Very Low |
| Industry Mix | None | Add to `census_api.py` | +1 | Very Low |

### Suggested Implementation Approach

#### 1. Major Employers
```python
# Option A: Static JSON file (simplest)
# Load from investigation/major_employers_fy2025.json

# Option B: PDF parsing module (dynamic)
# Add cafr_parser.py to core/
# Annually update when new CAFR released
```

#### 2. LFPR Integration
```python
# Add to existing census_api.py
DP03_LFPR_VARS = {
    "DP03_0001E": "pop_16_plus",
    "DP03_0002PE": "labor_force_participation_rate"
}

def get_lfpr(county_fips, state_fips):
    """Fetch Labor Force Participation Rate from Census DP03"""
    # Similar to existing demographics fetch
```

#### 3. Industry Mix Integration
```python
# Add to existing census_api.py
DP03_INDUSTRY_VARS = {
    "DP03_0033PE": "Agriculture/Mining",
    # ... (13 sectors)
}

def get_industry_mix(county_fips, state_fips):
    """Fetch industry employment percentages for pie chart"""
    # Returns dict ready for Plotly/Streamlit chart
```

### UI Suggestions

1. **Major Employers:** Table with ranking, sortable by employees/industry
2. **LFPR:** KPI card with comparison to state/national
3. **Industry Mix:** Pie chart with drill-down capability

---

## Questions Answered

| Question | Answer |
|----------|--------|
| Is CAFR PDF machine-readable? | ✅ Yes, PyPDF2 works perfectly |
| How current is BLS vs Census LFPR? | BLS monthly (but no LFPR), Census 2-year lag (has LFPR) |
| Does Loudoun's Info sector stand out? | ✅ Yes, 1.9x national average |
| Can all three integrate with existing Census API? | ✅ Yes, minimal refactoring needed |

---

## Files Generated

| File | Description |
|------|-------------|
| `major_employers_fy2025.json` | FY2025 top 10 employers structured data |
| `major_employers_historical.json` | Multi-year employer compilation |
| `test_bls_laus_api.py` | Working BLS LAUS API script |
| `bls_loudoun_response.json` | Full BLS API response |
| `test_census_dp03_api.py` | Working Census DP03 API script |
| `census_dp03_results.json` | Full Census API response |
| `investigation_results.md` | This summary report |
| `cafr_fy2025.pdf` | Downloaded CAFR (14MB) |
| `cafr_fy2024.pdf` | Downloaded CAFR (22MB) |
| `cafr_fy2020.pdf` | Downloaded CAFR (14MB) |

---

## Success Criteria Checklist

- [x] Successfully extract major employers from CAFR PDF
- [x] Working BLS LAUS API call returning Loudoun County data
- [x] Working Census DP03 API call returning LFPR and industry mix
- [x] Comparison of BLS vs Census LFPR data
- [x] JSON output structures ready for integration
- [x] Clear documentation of any limitations or issues

---

## Next Steps

1. **Review this investigation** with stakeholder
2. **Decide implementation approach** for Major Employers (static vs dynamic)
3. **Add LFPR and Industry Mix** to `core/census_api.py`
4. **Create UI components** in `loudoun_streamlit_app.py`
5. **Test with production data**

---

# Phase 2: Economic Data Refinements

**Date:** December 29, 2025

---

## Phase 2 Task 1: Complete Historical Major Employers (2008-2025)

### ✅ COMPLETE

All available CAFRs have been processed to create a complete 18-year timeline of major employers.

#### Data Coverage

| Year | Source | Key Data |
|------|--------|----------|
| 2008 | FY2017 CAFR comparison | AOL #2, LCPS 9,309 |
| 2009 | FY2018 CAFR comparison | Peak at LCPS 10,533 |
| 2010 | FY2019 CAFR comparison | M.C. Dean rises to #3 |
| 2011 | FY2020 CAFR comparison | LCPS 10,098 |
| 2012 | FY2021 CAFR comparison | LCPS dips to 9,663 |
| 2013 | FY2022 CAFR comparison | Stable employer mix |
| 2014 | FY2023 CAFR comparison | AOL's last appearance |
| 2015 | FY2024 CAFR comparison | LCPS 9,822 |
| 2016 | FY2025 CAFR comparison | Verizon peak at #3 |
| 2017 | FY2017 CAFR current | LCPS 10,640 |
| 2018 | FY2018 CAFR current | Orbital ATK merges to Northrop |
| 2019 | FY2019 CAFR current | Pre-pandemic peak |
| 2020 | FY2020 CAFR current | Amazon enters top 10 |
| 2021 | FY2021 CAFR current | LCPS 12,382 |
| 2022 | FY2022 CAFR current | DHS rises to #3 |
| 2023 | FY2023 CAFR current | LCPS 12,804 |
| 2024 | FY2024 CAFR current | LCPS 12,968 |
| 2025 | FY2025 CAFR current | LCPS 13,281 (peak) |

#### Key Trends Discovered

1. **LCPS Employment Growth:** 9,309 (2008) → 13,281 (2025) = **+42.7%**
2. **County Government Growth:** 3,375 (2008) → 5,059 (2025) = **+49.9%**
3. **Amazon Entry:** First appears in 2020, rises to rank 6 by 2025
4. **AOL Departure:** Last appears in 2014 (peak was #2 in 2008)
5. **Verizon Decline:** From #3-4 (2008-2016) to #8 (2025)
6. **Defense Consolidation:** Orbital Sciences → Orbital ATK → Northrop Grumman

#### Files Created

- `major_employers_historical.json` - Complete 2008-2025 JSON with all employers
- `major_employers_complete.csv` - Analysis-ready CSV format

---

## Phase 2 Task 2: Census ACS 1-Year vs 5-Year Comparison

### ✅ COMPLETE

#### Comparison Results

| Metric | 1-Year (2023) | 5-Year (2019-2023) | Difference |
|--------|---------------|---------------------|------------|
| LFPR | 73.4% | 74.1% | -0.7% |
| MOE (±) | 1.0% | 0.6% | — |
| Emp-to-Pop Ratio | 70.4% | 71.3% | -0.9% |

#### Industry Sector Comparison

| Sector | 1-Year | 5-Year | Change |
|--------|--------|--------|--------|
| Professional/Scientific | 31.8% | 29.6% | +2.2% |
| Arts/Entertainment/Food | 5.0% | 6.7% | -1.7% |
| Other Services | 5.4% | 4.7% | +0.7% |

#### Key Findings

1. **Margin of Error:** 1-Year MOE is ~1.9x larger than 5-Year
2. **LFPR Difference:** Within margin of error (not statistically significant)
3. **Professional Services:** Trending UP in 2023 vs 5-year average
4. **Arts/Entertainment:** Trending DOWN (possible COVID recovery lag)

#### Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│  USE 5-YEAR ACS for baseline metrics (LFPR, Industry Mix)  │
│  - More stable, lower margin of error                      │
│  - Suitable for OM narrative and comparisons               │
│                                                            │
│  SUPPLEMENT with 1-Year ACS when available                 │
│  - Note as "most recent" where trends are meaningful       │
│  - Highlight if significant changes from 5-Year baseline   │
└─────────────────────────────────────────────────────────────┘
```

#### Files Created

- `test_census_1yr_vs_5yr.py` - Comparison script
- `census_1yr_vs_5yr_comparison.json` - Full comparison data

---

## Phase 2 Task 3: BLS LAUS Seasonal Adjustment Methodology

### ✅ COMPLETE

BLS county-level LAUS data is **NOT seasonally adjusted**. Month-to-month comparisons can be misleading.

#### Implemented Methodology

1. **Year-over-Year Comparison:** Compare same month across years
2. **12-Month Moving Average:** Smooth out seasonal fluctuations
3. **Trend Direction:** Based on 6-month rolling comparison

#### Current Data (December 2024)

| Metric | Current | Prior Year | YoY Change | 12-Mo Avg | Trend |
|--------|---------|------------|------------|-----------|-------|
| Labor Force | 253,982 | 250,262 | +1.5% | 254,774 | Stable |
| Employment | 248,432 | 245,170 | +1.3% | 248,477 | Stable |
| Unemployment | 5,550 | 5,092 | +9.0% | 6,296 | Declining |
| Unemp Rate | 2.2% | 2.0% | +0.2 pts | 2.5% | Declining |

#### Output Format for OM

```
┌─────────────────────────────────────────────────────────────────────┐
│  LOUDOUN COUNTY LABOR MARKET SNAPSHOT                              │
│  Source: BLS Local Area Unemployment Statistics                     │
│  Data as of: December 2024                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Labor Force:       253,982                                        │
│    └─ YoY Change:   +1.5% vs December 2023                         │
│    └─ 12-Mo Avg:    254,774                                        │
│    └─ Trend:        Stable                                         │
│                                                                     │
│  Unemployment Rate: 2.2%                                           │
│    └─ Virginia:     2.9%                                           │
│                                                                     │
│  ⚠ Data is NOT seasonally adjusted                                 │
│  → Use YoY comparisons for accurate trend analysis                  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Files Updated/Created

- `test_bls_laus_api.py` - Enhanced with YoY and moving average
- `bls_loudoun_processed.json` - Processed output with calculated metrics

---

## Phase 2 Task 4: Dual-Source LFPR Display Format

### ✅ COMPLETE

Created combined data structure that merges Census baseline with BLS current trajectory.

#### Display Format

```
LABOR FORCE PARTICIPATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Baseline Rate: 74.1%
  └─ Source: Census ACS 2019-2023 5-Year Estimates
  └─ Loudoun vs Virginia: +8.5 pts | vs USA: +10.6 pts

Current Labor Force: 253,982 (Dec 2024)
  └─ Source: BLS Local Area Unemployment Statistics
  └─ Year-over-Year: +1.5% vs Dec 2023
  └─ 12-Month Trend: Stable

Note: Census provides stable baseline; BLS shows current trajectory.
```

#### Data Structure

```json
{
  "census_baseline": {
    "lfpr": 74.1,
    "source": "Census ACS 2019-2023 5-Year Estimates",
    "comparison": {
      "virginia": 65.6,
      "usa": 63.5,
      "loudoun_vs_usa": 10.6
    }
  },
  "bls_current": {
    "labor_force": 253982,
    "as_of_date": "December 2024",
    "yoy_change_pct": 1.5,
    "trend_direction": "stable"
  }
}
```

#### Files Created

- `lfpr_combined.json` - Combined Census + BLS data structure

---

## Phase 2 Summary Checklist

- [x] Complete employer data for 2008-2025 (18 years)
- [x] Census 1-Year vs 5-Year comparison with MOE analysis
- [x] BLS YoY and moving average methodology implemented
- [x] Dual-source LFPR format ready for UI implementation

---

## All Files Generated (Phase 1 + Phase 2)

| File | Description | Phase |
|------|-------------|-------|
| `major_employers_fy2025.json` | FY2025 top 10 employers | 1 |
| `major_employers_historical.json` | Complete 2008-2025 data | 1+2 |
| `major_employers_complete.csv` | Analysis-ready CSV | 2 |
| `test_bls_laus_api.py` | BLS API with YoY/moving avg | 1+2 |
| `bls_loudoun_response.json` | Raw BLS response | 1 |
| `bls_loudoun_processed.json` | Processed BLS metrics | 2 |
| `test_census_dp03_api.py` | Census DP03 API script | 1 |
| `census_dp03_results.json` | Census DP03 response | 1 |
| `test_census_1yr_vs_5yr.py` | 1-Year vs 5-Year comparison | 2 |
| `census_1yr_vs_5yr_comparison.json` | Comparison results | 2 |
| `lfpr_combined.json` | Combined LFPR structure | 2 |
| `investigation_results.md` | This report | 1+2 |

---

## Questions Answered (Phase 2)

| Question | Answer |
|----------|--------|
| Complete employer data for 2008-2025? | ✅ Yes, all years covered |
| Census 1-Year reliable enough? | ✅ Yes for Loudoun (pop 430k+), but 5-Year preferred for lower MOE |
| BLS YoY methodology clear? | ✅ Yes, well-documented with non-seasonal adjustment note |
| Dual-source LFPR ready for UI? | ✅ Yes, `lfpr_combined.json` provides complete structure |

---

*Phase 2 investigation completed by Claude Code on branch `claude/add-offering-memorandum-YVwlC`*
