# Virginia School Data - Handoff to Claude Code

## What Was Done

Processed 12 Virginia Department of Education Excel files (Subject-Area test scores + Accreditation reports) into 3 clean CSV files ready for integration into the Loudoun County real estate platform.

## Files Created

### 1. `school_performance_trends.csv` (758 KB)
**Primary file - mimics Athens GOSA structure**

**Purpose**: Multi-year school performance trends for all Virginia schools

**Structure**:
- One row per school per year
- Covers 2020-2021 through 2024-2025 (5 years of actual test data)
- Note: 2019-2020 is in source files but all NaN (COVID - tests cancelled)

**Columns**:
- `School_ID`: Numeric school identifier
- `School_Name`: Full school name
- `Division_Name`: County/city name (e.g., "Loudoun County")
- `School_Type`: Elem, Middle, High, Combined
- `Year`: Academic year (e.g., "2023-2024")
- `Reading_Pass_Rate`: % students passing SOL Reading tests
- `Writing_Pass_Rate`: % students passing SOL Writing tests
- `Math_Pass_Rate`: % students passing SOL Math tests
- `Science_Pass_Rate`: % students passing SOL Science tests
- `History_Pass_Rate`: % students passing SOL History/Social Science tests
- `Overall_Pass_Rate`: Average of all 5 subjects (calculated)

**Data Coverage**:
- Total Virginia schools: 1,863
- Loudoun County schools: 99
- Total records: 9,210 (school-year combinations)
- Loudoun records: 491

**Example row**:
```
School_ID,School_Name,Division_Name,School_Type,Year,Reading_Pass_Rate,Math_Pass_Rate,Science_Pass_Rate,History_Pass_Rate,Writing_Pass_Rate,Overall_Pass_Rate
192,Sugarland Elementary,Loudoun County,Elem,2024-2025,54.0,65.0,75.0,61.0,70.0,66.2
```

---

### 2. `school_accreditation.csv` (653 KB)
**Virginia-specific enhancement - Athens doesn't have equivalent**

**Purpose**: School accreditation status and quality indicators

**Structure**:
- One row per school per year
- Covers 2018-2019, 2019-2020, 2022-2023, 2023-2024, 2024-2025
- Note: Accreditation was waived 2020-2022 due to COVID

**Columns**:
- `School_ID`: Numeric school identifier
- `School_Name`: Full school name
- `Division_Name`: County/city name
- `Year`: Academic year
- `Accreditation_Status`: Official status (see values below)
- `Num_L3_Indicators`: Count of Level 3 (needs improvement) indicators
- `Has_L3_Indicators`: Boolean flag (True if any L3 indicators exist)

**Accreditation Status Values**:
- `Accredited`: Fully accredited (best status)
- `Accredited with Conditions`: Has quality concerns
- `Conditionally Accredited (New School)`: New school, conditional status
- Other values may appear for schools with serious issues

**Data Coverage**:
- Total Virginia schools: ~1,820 per year
- Loudoun schools: 98-101 (varies by year as schools open/close)
- Total records: 9,112

**Loudoun Breakdown (2024-2025)**:
- Accredited: 94 schools
- Accredited with Conditions: 2 schools
- Conditionally Accredited (New School): 2 schools

---

### 3. `school_metadata.csv` (110 KB)
**Reference file - school inventory**

**Purpose**: Master list of all Virginia schools with metadata

**Structure**:
- One row per unique school
- Based on most recent year of data

**Columns**:
- `School_ID`: Numeric school identifier
- `School_Name`: Full school name
- `Division_Name`: County/city name
- `School_Type`: Elem, Middle, High, Combined
- `Latest_Data_Year`: Most recent year with data
- `Years_of_Data`: Count of years with performance data

**Data Coverage**:
- Total Virginia schools: 1,863
- Loudoun schools: 99

**Loudoun School Types**:
- Elementary: 62 schools
- Middle: 19 schools
- High: 13 schools
- Combined: 5 schools

---

## Key Differences from Athens Setup

### Similarities (What We Matched):
✅ Performance trends file with multi-year data
✅ Test scores by subject area
✅ Overall performance metric
✅ All schools in dataset (filter by county at runtime)

### Enhancements (What Virginia Has That Athens Doesn't):
🆕 **Accreditation status** - major quality signal for homebuyers
🆕 **5 years of data** vs Athens' 5 years (same coverage, but Athens goes back further to 2016)
🆕 **Level 3 indicators** - flags schools with specific quality concerns
🆕 **More school types** - Virginia has "Combined" schools
🆕 **5 test subjects** - Virginia tests Writing separately (Athens combines)

### What We Lost from Original Data (Intentionally):
❌ Student subgroup breakdowns (ELL, IEP, Economically Disadvantaged) - too granular for v1
❌ Advanced pass rates - kept it simple with overall pass rates
❌ Grade-level test details - focused on school-wide performance
❌ 2016-2019 data - older files had different structure, kept 5 years (2020-2025)

---

## Integration Guide for Claude Code

### File Locations
Place these 3 CSV files in:
```
/multi-county-real-estate-research/data/loudoun/
├── school_performance_trends.csv
├── school_accreditation.csv
└── school_metadata.csv
```

### Python Integration Pattern (Matching Athens)

**Loading performance data**:
```python
import pandas as pd

# Load all Virginia schools
df_perf = pd.read_csv('data/loudoun/school_performance_trends.csv')

# Filter for Loudoun County (at runtime, like Athens does)
loudoun_perf = df_perf[df_perf['Division_Name'] == 'Loudoun County']

# Get specific school's trends
school_trends = loudoun_perf[loudoun_perf['School_Name'] == 'Aldie Elementary']

# Build trends dict for School object
trends_dict = {}
for subject in ['Reading', 'Math', 'Science', 'History', 'Writing', 'Overall']:
    col_name = f'{subject}_Pass_Rate'
    if col_name in school_trends.columns:
        trends_dict[f'{subject.lower()}_trends'] = dict(
            zip(school_trends['Year'], school_trends[col_name])
        )
```

**Loading accreditation data**:
```python
# Load accreditation
df_accred = pd.read_csv('data/loudoun/school_accreditation.csv')
loudoun_accred = df_accred[df_accred['Division_Name'] == 'Loudoun County']

# Get specific school's current status
school_accred = loudoun_accred[loudoun_accred['School_Name'] == 'Aldie Elementary']
current_status = school_accred[school_accred['Year'] == '2024-2025'].iloc[0]

# Add to School object
school.accreditation_status = current_status['Accreditation_Status']
school.has_quality_concerns = current_status['Has_L3_Indicators']
```

**Populating School dataclass** (like Athens):
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class School:
    school_id: str
    name: str
    school_type: str
    test_scores: Dict[str, Any]

# Build test_scores dict (like Athens GOSA)
test_scores = {
    'reading_trends': {
        '2024-2025': 85.0,
        '2023-2024': 83.5,
        # ... all years
    },
    'math_trends': {...},
    'overall_trends': {...},
    # NEW for Virginia
    'accreditation_status': 'Accredited',
    'has_quality_concerns': False
}

school = School(
    school_id='192',
    name='Aldie Elementary',
    school_type='Elementary',
    test_scores=test_scores
)
```

---

## Claude Code Prompts

### Prompt 1: Copy Files to Project
```
Copy these 3 CSV files from /home/claude/loudoun_processed_data/ to the Loudoun data directory:

Source: /home/claude/loudoun_processed_data/
- school_performance_trends.csv
- school_accreditation.csv  
- school_metadata.csv

Destination: /home/user/NewCo/multi-county-real-estate-research/data/loudoun/

After copying, confirm the files are in place and show file sizes.
```

### Prompt 2: Test Data Loading
```
Test loading the Virginia school data files:

1. Load school_performance_trends.csv
2. Filter for Loudoun County schools
3. Show summary statistics:
   - Number of Loudoun schools
   - Years covered
   - Sample of 3 schools with their 5-year trends
4. Load school_accreditation.csv for Loudoun County
5. Show current accreditation status breakdown

Verify data matches Athens structure for compatibility.
```

### Prompt 3: Create School Lookup Function
```
Create a function get_school_performance(school_name, county='Loudoun County') that:

1. Loads performance trends and accreditation data
2. Returns a dict matching Athens School.test_scores format:
   {
     'reading_trends': {year: pass_rate, ...},
     'math_trends': {...},
     'science_trends': {...},
     'history_trends': {...},
     'writing_trends': {...},
     'overall_trends': {...},
     'accreditation_status': 'Accredited',
     'has_quality_concerns': False
   }

Test with 'Aldie Elementary' and display results.
```

### Prompt 4: Integrate with Existing SchoolLookup Class
```
Update the SchoolLookup class in /home/user/NewCo/multi-county-real-estate-research/core/school_lookup.py:

1. Add method to load Virginia data files
2. Modify _get_school_performance_data() to handle Virginia format
3. Add Virginia-specific fields (accreditation_status, has_quality_concerns)
4. Test with Loudoun County address lookup
5. Ensure backwards compatibility with Athens code

CRITICAL: Use guardrails - only modify school_lookup.py, don't touch other files.
```

---

## Data Quality Notes

### Known Issues:
- **2019-2020 Missing**: COVID cancelled testing - no pass rates for this year
- **2020-2021 Asterisk**: Reduced participation, results may not be fully comparable
- **Accreditation Gap**: No data for 2020-2021, 2021-2022 (waived due to COVID)
- **Some schools have <5 years**: New schools or closed schools may have fewer years

### Data Validation Checks Done:
✅ All Loudoun County schools (99) present in performance data
✅ Pass rates are valid percentages (0-100)
✅ Accreditation statuses match official Virginia categories
✅ School IDs match across performance and accreditation files
✅ School types standardized (Elem, Middle, High, Combined)
✅ Division names consistent ("Loudoun County" not "Loudoun" or variants)

### Quality Assurance:
- Spot-checked 10 random Loudoun schools against official VDOE website ✓
- Verified accreditation statuses match Virginia School Quality Profiles ✓
- Confirmed year coverage and data completeness ✓

---

## Next Steps for Claude Code

1. **Copy files** to project directory
2. **Test loading** and filtering for Loudoun County
3. **Update SchoolLookup class** to use Virginia data format
4. **Add accreditation display** to Streamlit UI
5. **Test with real address** (43500 Tuckaway Pl, Leesburg, VA 20176)
6. **Verify trends visualization** works with 5-year data

---

## Contact/Questions

If Claude Code encounters issues:
- Check file paths are correct
- Verify Division_Name == 'Loudoun County' (exact match, case-sensitive)
- Confirm School_Name matches exactly (includes trailing spaces in some cases)
- Remember: This is ALL Virginia schools - must filter by Division_Name
- Accreditation data has gaps (2020-2022) - handle NaN gracefully

**Data processed by**: Claude (Assistant) on 2024-12-01
**Ready for**: Claude Code integration
**Status**: ✅ Production-ready
