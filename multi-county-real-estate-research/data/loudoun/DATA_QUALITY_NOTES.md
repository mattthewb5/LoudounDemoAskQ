# Loudoun Building Permits - Data Quality Notes

## Geocoding Issues

### Known Coordinate Errors

**42376 Patriot Park Dr** (Permit Value: $64.4M)
- **Issue**: Geocoded to downtown Leesburg (39.115452, -77.564532) instead of industrial area
- **Impact**: Originally showed as 0.05 miles from test address when actually ~10 miles away
- **Fix**: Manual correction applied using nearby 42630 Patriot Park coordinates (38.973708, -77.551509) as proxy
- **Date Identified**: 2024-12-01

### How Errors Were Detected

1. User research indicated 42376 Patriot Park Dr is a data center campus near Sycolin Road
2. Investigation found the geocoded coordinates placed it in historic downtown Leesburg
3. Comparison with nearby address 42630 Patriot Park Dr (correctly geocoded ~10 miles south) confirmed the error
4. The permit description mentions "Third building on the campus" - a multi-building industrial campus would not be in downtown Leesburg

### Validation Approach

The `infrastructure_detector.py` module includes validation for:

1. **Null coordinates** - Rejects (0,0) or missing values
2. **Out of bounds** - Rejects coordinates outside Loudoun County (38.8-39.3°N, 77.3-77.9°W)
3. **Downtown misplacement** - Flags data centers geocoded near exact downtown Leesburg coordinates (within 0.01°)

### Adding New Corrections

To add corrections for additional addresses:

1. Edit `data/loudoun/coordinate_corrections.csv`
2. Add row with columns:
   - `address`: Full address (must match CSV exactly, including punctuation)
   - `original_lat`, `original_lon`: The incorrect coordinates
   - `corrected_lat`, `corrected_lon`: The correct coordinates
   - `correction_reason`: Brief explanation
   - `date_corrected`: Date the correction was added
3. Corrections are automatically applied by `find_nearby_infrastructure()`

### Address Matching Requirements

- Address must match EXACTLY (case-insensitive)
- Include proper punctuation (e.g., "LEESBURG, VA 20175" not "LEESBURG VA 20175")
- Check actual address format in the permits CSV before adding corrections

## Data Coverage

- **Dataset**: Loudoun County Building Permits
- **Date Range**: April 2024 - October 2025
- **Total Permits**: 15,752
- **Geocoded Success Rate**: 99.6% (15,689 permits with valid coordinates)

## Infrastructure Summary

From Phase 1 analysis:

| Category | Count | Total Value |
|----------|-------|-------------|
| Data Centers (Structure Type) | 332 | $5.17B |
| Telecom Tower/Antenna | 111 | - |
| Fiber Projects | 2 | - |
| Telecom Equipment | 34 | - |

## Known Limitations

1. **Geocoding Accuracy**: Some addresses may have incorrect coordinates (like Patriot Park). New errors should be added to the corrections file.

2. **Fiber Detection**: Only 2 explicit fiber permits found. Most fiber work may be bundled into larger utility or conduit permits.

3. **Address Variations**: Different permit records may have slightly different address formats for the same location.

4. **Date Filtering**: The `find_nearby_infrastructure()` function filters by permit issue date, so very recent or very old permits may not appear in results.
