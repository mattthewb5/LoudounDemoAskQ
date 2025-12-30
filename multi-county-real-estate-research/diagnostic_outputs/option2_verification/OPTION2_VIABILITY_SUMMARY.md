# Option 2 Viability Assessment

## Executive Summary

**Is Option 2 Viable?** NO - The existing `match_school_in_performance_data()` function has a bug that returns the wrong school for names with common first words.

**Recommendation:** Use **Exact Normalized Match** approach instead, which requires:
1. Fixing lines 604-614 and 628-638 in `loudoun_streamlit_app.py`
2. Fixing `match_school_in_performance_data()` in `core/loudoun_school_performance.py`

## Findings

### Existing Function Status
- Function `match_school_in_performance_data()` exists: **Yes**
- Location: `core/loudoun_school_performance.py:217-252`
- Matching logic: Hybrid (exact → partial → **first word fallback**)

### Critical Bug in Existing Function

The function has a **first-word fallback** on lines 244-250 that:
1. Returns the FIRST school that shares the same first word
2. Depends on data file order (not alphabetical or correct match)

**Example:**
- Input: "Belmont Ridge Middle"
- Expected: "Belmont Ridge Middle"
- Actual: "Belmont Station Elementary" (appears first in data file)

### Why Lines 650-841 Appear to Work (But Don't)

| Aspect | Buggy Code (604-614) | "Working" Code (650-841) |
|--------|---------------------|-------------------------|
| Pattern | `str.contains(first_word)` | `match_school_in_performance_data()` |
| Returns | Multiple schools | One school |
| Visual | Duplicate lines | Single line |
| Data | Multiple schools' data | **Wrong school's data** |

The "working" code hides the problem by returning only ONE match, but that match is often the WRONG school.

### Test Results

| School | Option 2 Returns | Correct? |
|--------|------------------|----------|
| Steuart Weller Elementary | Steuart W. Weller Elementary | ✓ Yes (partial match) |
| Belmont Ridge Middle | Belmont Station Elementary | ✗ **WRONG** |
| Riverside High | Riverside High | ✓ Yes (file order coincidence) |

- Eliminates Belmont Ridge duplicates: Yes
- Works for all three test schools: **NO**
- Edge cases handled properly: **NO**

## Implementation Path

### Recommended: Exact Normalized Match

**Changes Required:**
- Files affected: 2
  - `loudoun_streamlit_app.py` (lines 604-614, 628-638)
  - `core/loudoun_school_performance.py` (lines 244-250)
- Lines changed: ~15
- Risk level: **Low**

**Steps:**

1. **Add import** in `loudoun_streamlit_app.py`:
```python
from core.loudoun_school_performance import normalize_school_name
```

2. **Replace lines 606-608** with:
```python
normalized_target = normalize_school_name(school)
school_data = performance_df[
    performance_df['School_Name'].apply(normalize_school_name) == normalized_target
]
```

3. **Replace lines 630-632** with same pattern (Math chart)

4. **Fix `match_school_in_performance_data()`** - Remove or fix first-word fallback:
```python
# REMOVE lines 244-250 (first word fallback)
# Or reorder to prioritize exact matches across ALL schools first
```

### Edge Case: Name Variations

**Problem:** School boundary data uses "Steuart Weller Elementary" but VADOE uses "Steuart W. Weller Elementary"

**Solutions:**
1. Fix source data to match (preferred)
2. Enhanced normalizer that removes middle initials
3. Fuzzy matching fallback with strict threshold

### Alternative: Simple str.strip() Match (Quick Fix)

If exact normalized match is too complex:
```python
school_data = performance_df[
    performance_df['School_Name'].str.strip().str.lower() == school.strip().lower()
]
```
⚠️ This only works if names are exactly the same (fails for Steuart Weller)

## Recommendation Rationale

**Option 2 is NOT viable** because:
1. The existing function has the same class of bug (first-word matching)
2. It trades duplicate lines for wrong data (worse in some ways)
3. Success depends on unpredictable data file order

**Exact normalized match is best** because:
1. The `normalize_school_name()` function already handles suffixes correctly
2. Keeps distinguishing words ("RIDGE" in "BELMONT RIDGE")
3. No collision for current Loudoun schools (except Sterling which is cross-level)
4. Easy to implement and test

## Files in This Investigation

| File | Description |
|------|-------------|
| `01_existing_functions.txt` | Analysis of match_school_in_performance_data() |
| `02_working_code_excerpt.py` | Lines 650-841 with annotations |
| `03_pattern_comparison.txt` | Buggy vs "working" pattern analysis |
| `04_option2_test_results.txt` | Test results showing Option 2 failures |
| `05_implementation_requirements.txt` | Implementation details |
| `06_exact_match_fallback.txt` | Exact match approach analysis |
