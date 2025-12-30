# School Trend Line Duplicate Investigation

## Test Address
44750 Maynard Sq, Ashburn, VA 20147

## Findings

### Root Cause

**The search pattern `school.split()[0]` on line 607 of `loudoun_streamlit_app.py` extracts only the FIRST WORD of the school name for matching.**

For "Belmont Ridge Middle", it searches for "Belmont" which matches:
- **Belmont Elementary** (WRONG - elementary school)
- **Belmont Ridge Middle** (CORRECT)
- **Belmont Station Elementary** (WRONG - different school entirely)

All three schools' data is then added to the chart with the label "Belmont Ridge Middle", creating the visual appearance of duplicate/overlapping lines.

### Evidence

- **Pipeline stage where duplicates first appear**: Chart Data Creation (lines 604-614)
- **Number of duplicate records for test case**: 15 records instead of expected 5
- **Affected schools in test case**:
  - Belmont Ridge Middle: Also shows Belmont Elementary, Belmont Station Elementary data
  - Riverside High: Also shows Riverside Elementary data

### Problematic Code

```python
# loudoun_streamlit_app.py lines 604-614
for level, school in assignments.items():
    if school:
        school_data = performance_df[
            performance_df['School_Name'].str.contains(
                school.split()[0],  # <-- BUG: Only uses first word
                case=False,
                na=False
            )
        ]
```

### Data Quality Issues

1. **Search Pattern Too Broad**: Using only the first word matches unrelated schools
2. **Trailing Whitespace**: Some school names have trailing spaces (e.g., "Belmont Station Elementary ")
3. **No School Type Filtering**: The search doesn't filter by school level (Elementary/Middle/High)

### Impact Assessment

- **Is this Belmont Ridge-specific?** NO - This affects 973 schools (54% of all schools in the dataset)
- **Does it affect other school levels?** YES
  - Elementary schools affected: 547
  - Middle schools affected: 156
  - High schools affected: 157
- **Estimated scope**: Any property assigned to a school with a common first word name (John, George, Mary, Virginia, William, etc.)

**Most Problematic First Words:**
| First Word | Schools Sharing It |
|------------|-------------------|
| John | 21 schools |
| Virginia | 16 schools |
| William | 15 schools |
| George | 15 schools |
| Mary | 12 schools |

## Recommended Fix

**Location**: `loudoun_streamlit_app.py` lines 604-614 and 628-638

**Option 1 - Exact Match (Simplest)**:
```python
school_data = performance_df[
    performance_df['School_Name'].str.strip().str.lower() == school.strip().lower()
]
```

**Option 2 - Use Existing Correct Pattern**:
The codebase already has `match_school_in_performance_data()` in `core/loudoun_school_performance.py` which handles matching correctly. Replace the inline search with a call to this function.

**Option 3 - Normalize and Match**:
```python
from core.loudoun_school_performance import normalize_school_name

normalized_target = normalize_school_name(school)
school_data = performance_df[
    performance_df['School_Name'].apply(normalize_school_name) == normalized_target
]
```

## Next Steps

1. **Implement fix in lines 604-614 and 628-638** - Replace `str.contains(school.split()[0])` with exact matching
2. **Test with problematic addresses**:
   - 44750 Maynard Sq, Ashburn (Belmont Ridge Middle)
   - Any address in Riverside High attendance zone
   - Any address assigned to schools starting with John/George/Mary/Virginia
3. **Consider caching normalized school names** to avoid repeated string operations
4. **Clean up data** - Strip trailing whitespace from school names in source CSV

## Files Produced

| File | Description |
|------|-------------|
| data_pipeline_map.txt | Complete data flow documentation |
| 01_school_assignments.json | Assigned schools for test address |
| 02_raw_vadoe_belmont_ridge.csv | Raw VADOE data matching "Belmont" |
| 03_merged_middle_school_data.csv | Chart data showing duplicates |
| 05_duplicate_analysis.txt | Detailed duplicate detection results |
| 06_name_variations.txt | School name consistency analysis |
| 07_other_schools_check.txt | Scope analysis for other schools |
