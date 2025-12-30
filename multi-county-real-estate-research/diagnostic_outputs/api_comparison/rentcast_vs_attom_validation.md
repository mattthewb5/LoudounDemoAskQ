# RentCast vs ATTOM API Validation Report

**Analysis Date:** 2025-12-22
**Properties Tested:** 96

---

## Executive Summary

### Recommendation: **NO-GO**
**Confidence Level:** High

RentCast accuracy does not meet requirements for ATTOM replacement.
Recommend: Keep ATTOM, focus on DIY AVM development.

### Key Findings

- **Valuation Agreement:** 29.0% within 10% of each other
- **Mean Absolute Difference:** 33.17%
- **RentCast Success Rate:** 100.0%
- **ATTOM AVM Success Rate:** 71.9%

---

## Detailed Results

### API Success Rates

| Metric | Rate | Count |
|--------|------|-------|
| RentCast Value Estimate | 100.0% | 96/96 |
| ATTOM Property Detail | 75.0% | 72/96 |
| ATTOM AVM | 71.9% | 69/96 |
| Both Have Valuations | 71.9% | 69/96 |

### Valuation Comparison

**Comparable Properties:** 69 (have both RentCast and ATTOM valuations)

| Metric | Value |
|--------|-------|
| Mean Difference (RC - ATTOM) | +2.81% |
| Mean Absolute Difference | 33.17% |
| Median Absolute Difference | 19.25% |
| Standard Deviation | 63.31% |
| Min Difference | -95.60% |
| Max Difference | +376.15% |

**Agreement Distribution:**

| Range | Percentage |
|-------|------------|
| Within 5% | 10.1% |
| Within 10% | 29.0% |
| Within 15% | 34.8% |
| Within 20% | 53.6% |
| Over 20% | 46.4% |

**Direction of Difference:**

- RentCast higher: 27 properties
- ATTOM higher: 42 properties

### Property Characteristics Comparison

| Field | Match Rate | Sample Size |
|-------|------------|-------------|

### API Response Times

| API | Average Response Time |
|-----|----------------------|
| RentCast Value | 435 ms |
| ATTOM Property | 302 ms |
| ATTOM AVM | 338 ms |
| ATTOM Total | 640 ms |

### Results by City

| City | Count | RC Success | ATTOM Success | Mean Diff |
|------|-------|------------|---------------|-----------|
| ASHBURN | 26 | 100.0% | 76.9% | -3.9% |
| STERLING | 24 | 100.0% | 45.8% | +15.1% |
| LEESBURG | 17 | 100.0% | 88.2% | -1.0% |
| ALDIE | 9 | 100.0% | 100.0% | -15.7% |
| CHANTILLY | 6 | 100.0% | 0.0% | N/A |
| PURCELLVILLE | 4 | 100.0% | 100.0% | -12.8% |
| ROUND HILL | 3 | 100.0% | 100.0% | -20.6% |
| WATERFORD | 1 | 100.0% | 100.0% | +376.1% |
| LOVETTSVILLE | 1 | 100.0% | 100.0% | -43.1% |
| MIDDLEBURG | 1 | 100.0% | 100.0% | -19.3% |
| HAMILTON | 1 | 100.0% | 100.0% | +26.1% |
| BLUEMONT | 1 | 100.0% | 100.0% | +16.2% |
| PAEONIAN SPRINGS | 1 | 100.0% | 100.0% | +49.3% |
| GREAT FALLS | 1 | 100.0% | 100.0% | -29.8% |

---

## Cost-Benefit Analysis

### Current ATTOM Costs (Estimated)

- ~$0.10-0.15 per API call
- 2-3 calls per property (property detail + AVM)
- At 1,000 properties/month: **$200-450/month**
- At 10,000 properties/month: **$2,000-4,500/month**

### RentCast Costs

- ~$0.03 per API call
- 1 call per property (value estimate includes all data)
- At 1,000 properties/month: **$30/month**
- At 10,000 properties/month: **$300/month**

### Potential Savings

| Scenario | Monthly Savings | Annual Savings |
|----------|-----------------|----------------|
| Full RentCast Migration | $1,700-4,200 | $20,400-50,400 |
| Hybrid (80% RentCast) | $1,360-3,360 | $16,320-40,320 |
| Keep ATTOM (baseline) | $0 | $0 |

---

## Recommendations

### Keep ATTOM, Explore Alternatives

1. Continue using ATTOM as primary source
2. Negotiate volume discounts with ATTOM
3. Accelerate DIY AVM model development using:
   - Loudoun County sales data (78K records)
   - Tax assessment data
   - Machine learning models

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RentCast accuracy degradation | Low | Medium | Monitor weekly, keep ATTOM backup |
| API rate limits | Low | Low | Implement caching, batch processing |
| Missing data for some properties | Medium | Low | Fallback to ATTOM or assessment data |
| Valuation bias in specific areas | Medium | Medium | Geographic monitoring, calibration |

---

## Appendix

### Methodology

- **Sample Size:** 96 properties
- **Geographic Coverage:** Loudoun County, VA (multiple cities/towns)
- **Property Selection:** Stratified sample from building permits (2024-2025)
- **Comparison Metrics:** Valuation difference, characteristic match rates

### Data Sources

- RentCast API: `/v1/avm/value` endpoint
- ATTOM API: `/property/detail` and `/attomavm/detail` endpoints
- Test sample: `diagnostic_outputs/api_comparison/test_sample.csv`

### Files Generated

- `raw_results.json` - Complete API responses
- `summary_stats.json` - Summary statistics
- `comparison_metrics.csv` - Per-property metrics
- `rentcast_vs_attom_validation.md` - This report
