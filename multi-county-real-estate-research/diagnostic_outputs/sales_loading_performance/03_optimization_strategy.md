# Sales Data Loading Optimization Strategy

## Executive Summary

**Current Performance**: ~90-150 seconds (1.5-2.5 minutes) to load 47K records
**Target Performance**: <10 seconds first load, instant subsequent loads
**Root Cause**: Excel format + no caching + row-by-row iteration

## Strategy Options

---

### Option A: Quick Win (Caching Only)

**Changes Required:**
1. Add `@st.cache_resource` decorator to sales data loading
2. Modify orchestrator to use cached instance

**Estimated Results:**
| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| First load | 90-150s | 90-150s | 0% |
| Subsequent loads | 90-150s | <0.01s | 99%+ |
| Memory | ~30 MB | ~30 MB | 0% |

**Implementation Time:** 15-30 minutes

**Pros:**
- Minimal code changes
- Zero risk to data accuracy
- Immediate improvement for common case (multiple analyses per session)
- No file format changes
- Easy to understand and maintain

**Cons:**
- First analysis in each session still takes 2 minutes
- Demo still starts with a long wait
- Increased persistent memory usage

**Best For:**
- If first-load time is acceptable
- If priority is minimal changes
- If users typically analyze multiple properties per session

---

### Option B: Balanced Optimization (Parquet + Caching)

**Changes Required:**
1. Convert combined_sales.xlsx to combined_sales.parquet (one-time)
2. Update LoudounSalesData to use pd.read_parquet()
3. Add `@st.cache_resource` caching
4. Document data refresh process

**Estimated Results:**
| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| First load | 90-150s | 2-5s | 95%+ |
| Subsequent loads | 90-150s | <0.01s | 99%+ |
| File size | 7.37 MB | ~2.5 MB | 66% |
| Memory | ~30 MB | ~30 MB | 0% |

**Implementation Time:** 1-2 hours

**Pros:**
- Dramatic first-load improvement (2-5 seconds instead of 2 minutes)
- Smaller file size (better for git)
- Industry standard format
- Good balance of effort vs benefit
- Future-proof for larger datasets

**Cons:**
- Parquet files are binary (less human-readable)
- Need to update data refresh workflow
- Requires pyarrow library (likely already installed)

**Best For:**
- Best overall choice for most situations
- When demo experience matters
- When data refresh process can be updated

---

### Option C: Maximum Performance

**Changes Required:**
1. All of Option B (Parquet + Caching)
2. Column selection (usecols parameter)
3. Vectorize index building (replace iterrows with groupby)
4. Optional: Pre-compute normalized PARID in conversion step

**Estimated Results:**
| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| First load | 90-150s | <1s | 99%+ |
| Subsequent loads | 90-150s | <0.01s | 99%+ |
| File size | 7.37 MB | ~2 MB | 73% |
| Memory | ~30 MB | ~20 MB | 33% |

**Implementation Time:** 3-4 hours

**Pros:**
- Sub-second first load
- Optimized memory usage
- Handles future data growth well
- Clean, optimized codebase

**Cons:**
- More significant code changes
- Higher testing burden
- More complex than necessary for 47K records
- Diminishing returns vs Option B

**Best For:**
- When absolute minimum load time required
- If dataset expected to grow significantly
- If you want "fully optimized" codebase

---

### Option D: Deferred Loading (Lazy Load)

**Changes Required:**
1. Don't load sales data on startup
2. Load only when first property analysis requested
3. Add `@st.cache_resource` caching after load
4. Add clear loading indicator

**Estimated Results:**
| Metric | Current | After | Improvement |
|--------|---------|-------|-------------|
| App startup | 90-150s | <1s | 99%+ |
| First analysis | 0s | 90-150s | (moved here) |
| Subsequent analyses | 90-150s | <0.01s | 99%+ |

**Implementation Time:** 30-60 minutes

**Pros:**
- App starts instantly
- Loading happens when user is engaged
- Psychological perception may be better

**Cons:**
- Still have 2-minute wait (just moved)
- First property analysis still slow
- Doesn't actually fix the loading speed

**Best For:**
- If app startup time is the concern
- Temporary solution before full optimization

---

## Decision Matrix

| Criteria | A: Cache | B: Parquet+Cache | C: Maximum | D: Lazy |
|----------|----------|------------------|------------|---------|
| First load time | ❌ 90-150s | ✅ 2-5s | ✅ <1s | ❌ 90-150s |
| Subsequent loads | ✅ Instant | ✅ Instant | ✅ Instant | ✅ Instant |
| Implementation time | ✅ 15 min | ✅ 1-2 hrs | ⚠️ 3-4 hrs | ✅ 30 min |
| Risk level | ✅ Very low | ✅ Low | ⚠️ Medium | ✅ Low |
| Code complexity | ✅ Minimal | ✅ Low | ⚠️ Medium | ✅ Low |
| Maintenance burden | ✅ None | ⚠️ Data pipeline | ⚠️ Higher | ✅ None |
| Demo experience | ❌ Poor | ✅ Good | ✅ Excellent | ❌ Poor |

Legend: ✅ Good | ⚠️ Moderate | ❌ Poor

---

## Recommendation

**For most use cases, Option B (Parquet + Caching) is recommended** because:

1. **Best effort-to-benefit ratio**: 1-2 hours of work eliminates 95%+ of wait time
2. **Fixes the actual problem**: First load drops from 2 minutes to 2-5 seconds
3. **Demo-ready**: No awkward 2-minute wait at start of demo
4. **Low risk**: Parquet is mature, well-supported, industry standard
5. **Future-proof**: Handles dataset growth gracefully

However, **if you prefer minimal changes**, Option A (caching only) gives immediate improvement for subsequent analyses with just 15 minutes of work.

---

## Questions for Matt

Before implementing, please clarify:

1. **Data refresh frequency**: How often is combined_sales.xlsx updated?
   - If rarely: Parquet conversion is easy one-time step
   - If frequently: Need to document/automate conversion

2. **Historical data needs**: Does any feature require sales older than 3 years?
   - If no: Could filter to recent data for additional speedup
   - If yes: Keep all records

3. **Typical session pattern**: Do users analyze one property or multiple per session?
   - If multiple: Caching alone may be sufficient
   - If one: First-load time matters more

4. **Demo priority**: How important is eliminating the initial 2-minute wait?
   - High priority: Go with Option B or C
   - Lower priority: Option A may suffice

---

## Next Steps

Once Matt selects an option:

### For Option A:
1. Add @st.cache_resource to sales data loading
2. Verify caching works correctly
3. Test with multiple property analyses
4. Done (~15-30 minutes)

### For Option B:
1. Install pyarrow if not present: `pip install pyarrow`
2. Create conversion script to convert xlsx -> parquet
3. Run conversion on combined_sales.xlsx
4. Update LoudounSalesData to read parquet
5. Add @st.cache_resource caching
6. Test thoroughly
7. Document data refresh process
8. Done (~1-2 hours)

### For Option C:
1. All of Option B
2. Add usecols parameter to limit columns
3. Refactor _load_data() with vectorized groupby
4. Optimize normalize_parid as vectorized operation
5. Comprehensive testing
6. Done (~3-4 hours)

### For Option D:
1. Move sales data loading to first analysis request
2. Add @st.cache_resource
3. Add loading spinner with message
4. Done (~30-60 minutes)

---

## Summary

| Metric | Current | Option A | Option B | Option C | Option D |
|--------|---------|----------|----------|----------|----------|
| First load | 90-150s | 90-150s | 2-5s | <1s | 90-150s |
| Effort | - | 15 min | 1-2 hrs | 3-4 hrs | 30 min |
| Risk | - | Very low | Low | Medium | Low |
| **Recommendation** | - | Quick fix | **Best value** | Over-engineered | Temporary |

**Awaiting Matt's decision to proceed with implementation.**
