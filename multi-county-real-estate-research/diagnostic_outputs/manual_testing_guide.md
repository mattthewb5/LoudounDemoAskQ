# Manual Testing Guide - School Trend Line Fix

## Purpose
Verify the duplicate school trend line bug is fixed in the actual Streamlit application.

## Test Environment
- Branch: claude/verify-neighborhood-integration-MGlc6
- Application: loudoun_streamlit_app.py
- Fix: 4 commits implementing priority matching

## Test Cases

### Test 1: Original Bug Address (CRITICAL)
**Address**: 44750 Maynard Sq, Ashburn, VA 20147

**Expected Schools**:
- Elementary: Steuart W. Weller Elementary
- Middle: Belmont Ridge Middle
- High: Riverside High

**What to Check**:
1. Navigate to "School Performance Trends" section
2. Reading Proficiency Trends chart:
   - Count trend lines: Should see exactly 3 (one per school)
   - Belmont Ridge Middle: Should show 1 solid line (NOT 3 overlapping lines)
   - Line should have ~5 data points (years 2020-2025)
   - Pass rates should be in reasonable range (70-85%)
3. Math Proficiency Trends chart:
   - Same verification as Reading chart
   - Should also show exactly 3 distinct lines
4. Check browser console for errors (F12 → Console tab)
5. Check terminal running streamlit for errors

**Before Fix**: Belmont Ridge Middle showed 3 overlapping lines (Belmont Elementary, Belmont Ridge, Belmont Station)
**After Fix**: Belmont Ridge Middle shows 1 clean line

**Status**: [ ] PASS  [ ] FAIL
**Notes**: _____________________________________

---

### Test 2: Sterling Collision Case
**Find an address assigned to**: Sterling Elementary or Sterling Middle

**Purpose**: Verify collision disambiguation works correctly

**What to Check**:
- If Sterling Elementary: Should show only Sterling Elementary data
- If Sterling Middle: Should show only Sterling Middle data
- Should NOT mix data from both schools

**Status**: [ ] PASS  [ ] FAIL  [ ] SKIP (couldn't find address)
**Notes**: _____________________________________

---

### Test 3: Riverside Collision Case
**Address**: Any address assigned to Riverside High (test address 44750 works)

**Purpose**: Verify Riverside High doesn't pull Riverside Elementary data

**What to Check**:
- High school chart should show "Riverside High" only
- Should NOT show data from Riverside Elementary

**Status**: [ ] PASS  [ ] FAIL
**Notes**: _____________________________________

---

### Test 4: Middle Initial Matching
**Address**: 44750 Maynard Sq, Ashburn, VA 20147

**Purpose**: Verify Steuart W. Weller Elementary data loads correctly

**What to Check**:
- Elementary school chart shows data (not empty)
- School name label is "Steuart Weller Elementary" (assigned name)
- Data displayed is from "Steuart W. Weller Elementary" (VADOE name)
- Trend line has 5 data points

**Status**: [ ] PASS  [ ] FAIL
**Notes**: _____________________________________

---

## Running the Tests

### Start the Application
```bash
cd /home/user/NewCo/multi-county-real-estate-research
python -m streamlit run loudoun_streamlit_app.py
```

### Access the Application
Open browser to: http://localhost:8501

### For Each Test
1. Enter the test address
2. Click "Analyze Property"
3. Scroll to "School Performance Trends" section
4. Verify charts as described above
5. Record PASS/FAIL and any notes

## Success Criteria
- All 4 tests marked PASS
- No errors in browser console
- No errors in terminal
- Belmont Ridge Middle shows single line (most critical)

## If Tests Fail
Document:
1. Which test failed
2. What you expected to see
3. What you actually saw
4. Screenshot if possible
5. Any error messages

## Testing Complete
**All tests passed**: [ ] YES  [ ] NO
**Tested by**: _____________________
**Date**: _____________________
**Ready for demo**: [ ] YES  [ ] NO
