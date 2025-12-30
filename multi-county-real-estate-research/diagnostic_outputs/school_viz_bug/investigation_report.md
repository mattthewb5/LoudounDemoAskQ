# School Performance Visualization Bug Investigation

**Date:** 2025-12-22
**Status:** Investigation Complete
**Type:** READ-ONLY (No Code Changes)

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** The x-axis year ordering issue is caused by **missing data for certain years in subject schools** combined with **Plotly's categorical x-axis behavior** that displays values in order of first appearance rather than chronological order.

---

## Bug Description (As Reported)

- **Location:** "School Performance vs State & Peers" section (page 2 of report)
- **Chart:** History Pass Rate Trends (and similar charts)
- **Symptoms:**
  1. X-axis shows years in wrong order: 2021-2022, 2022-2023, 2023-2024, 2024-2025, then "2020-2021" at the end
  2. Two dotted grey lines both labeled "Virginia State Average"

---

## Root Cause Analysis

### Issue 1: Year Ordering Problem

**Finding:** The x-axis displays years in the order they **first appear in the chart data**, not chronologically.

**Evidence (Belmont Ridge Middle, History Pass Rate):**

```
Subject school years: ['2021-2022', '2022-2023', '2023-2024', '2024-2025']
State avg years:      ['2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025']
```

**Data Flow:**
1. `create_performance_chart()` builds `chart_data` list
2. Subject school data is added first (rows 0-3)
3. State average data is added second (rows 4-8)
4. **2020-2021 only exists in state average** (subject has NaN for that year)
5. Plotly's `px.line()` with categorical x-axis shows years in order of first appearance
6. Result: 2020-2021 appears at the END of x-axis

**Raw Data Verification:**
```python
# Belmont Ridge Middle - History data
Year        History_Pass_Rate
2020-2021   NaN          <-- Filtered out due to pd.notna() check
2021-2022   85.0
2022-2023   92.0
2023-2024   92.0
2024-2025   90.0
```

**Scope of Issue:**
- Affects any school with NaN values in specific years for specific subjects
- 6 Loudoun schools completely missing 2020-2021 data
- Many more schools have NaN for specific subjects in specific years
- State Average always has data for all years, causing the ordering mismatch

### Issue 2: Two Virginia State Average Lines

**Hypothesis:** This is likely a visual artifact caused by the x-axis ordering issue, not actual duplicate data.

**Evidence:**
- State average data has exactly 5 entries per school type (one per year)
- No duplicate entries found in CSV (verified with `uniq -c`)
- Only one "Virginia State Average" value appears in chart_data
- Plotly creates only one trace per unique color value

**Alternative Explanation:** The "second line" may be:
1. A visual perception artifact from the scrambled x-axis
2. The line connecting 2024-2025 to 2020-2021 (which appears to "jump back")
3. Confusion with peer school lines that have similar styling

---

## Technical Details

### Bug Location

**File:** `core/loudoun_school_performance.py`
**Function:** `create_performance_chart()` (lines 306-438)

**Problematic Code Pattern:**
```python
# Line 391-398 - No explicit year sorting
fig = px.line(
    chart_df,
    x='Year',           # Categorical, not sorted
    y='Pass_Rate',
    color='School',
    title=f'{metric_name} Pass Rate Trends',
    markers=True
)
```

### Data Quality Issues

| Issue | Description | Impact |
|-------|-------------|--------|
| Missing 2020-2021 data | Many schools have NaN for 2020-2021 (COVID year) | X-axis ordering breaks |
| No explicit sorting | `chart_df` is not sorted before plotting | Years appear in data order |
| Inconsistent year coverage | State avg has all years, schools don't | Creates ordering mismatch |

### Plotly Behavior

- `px.line()` with categorical x-axis uses **order of first appearance**
- Unlike numeric x-axis, categories are NOT automatically sorted
- When traces have different year sets, the order becomes unpredictable

---

## Recommended Fix

### Option 1: Sort Years Before Plotting (Simplest)

**Location:** `core/loudoun_school_performance.py` line ~388

```python
# Create DataFrame for plotting
chart_df = pd.DataFrame(chart_data)

# ADD THIS: Sort by year to ensure chronological order
chart_df = chart_df.sort_values('Year')

# Create chart using px.line matching existing pattern
fig = px.line(...)
```

### Option 2: Explicitly Set Category Order

```python
# Define correct year order
year_order = ['2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025']

fig = px.line(
    chart_df,
    x='Year',
    y='Pass_Rate',
    color='School',
    category_orders={'Year': year_order},  # ADD THIS
    ...
)
```

### Option 3: Convert to Date Type (More Robust)

```python
# Convert year string to sortable format
chart_df['Year_Sort'] = chart_df['Year'].str[:4].astype(int)
chart_df = chart_df.sort_values('Year_Sort')
```

**Recommended:** Option 1 or 2 - both are simple one-line fixes.

---

## Files Involved

| File | Role | Lines |
|------|------|-------|
| `core/loudoun_school_performance.py` | Chart creation function | 306-438 |
| `loudoun_streamlit_app.py` | Calls chart function | 660-840 |
| `data/loudoun/school_performance_trends_with_state_avg.csv` | Data source | N/A |

---

## Test Cases for Verification

After implementing fix, test with:

1. **18989 Coral Reef Sq, Leesburg, VA 20176** - Uses Belmont Ridge Middle
2. **Any property with schools missing 2020-2021 data**
3. **All subject tabs** (History, Math, Reading, Science, Overall)

Expected result: X-axis shows years in chronological order: 2020-2021, 2021-2022, 2022-2023, 2023-2024, 2024-2025

---

## Athens Protection Verification

- `streamlit_app.py`: NOT examined or modified
- `clarke_*`, `athens_*`, `accpd_*`, `gosa_*`: NOT examined or modified
- Only examined: `loudoun_streamlit_app.py`, `core/loudoun_school_performance.py`, data files

---

## Next Steps

1. **Approve fix approach** (Option 1 recommended)
2. **Implement one-line fix** in `create_performance_chart()`
3. **Test with affected properties**
4. **Commit and deploy**

---

## Appendix: Diagnostic Commands Used

```bash
# Check unique years
cut -d',' -f5 data/loudoun/school_performance_trends_with_state_avg.csv | sort -u

# Check state average entries
grep "999999" data/loudoun/school_performance_trends_with_state_avg.csv

# Check for year format variations
grep "2020/2021" data/loudoun/school_performance_trends_with_state_avg.csv
# (None found - all years use "2020-2021" format with dashes)

# Simulate chart data creation
python3 -c "import pandas as pd; df = pd.read_csv('...'); ..."
```
