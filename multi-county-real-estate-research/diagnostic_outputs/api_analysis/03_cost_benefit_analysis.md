# ATTOM Replacement - Cost-Benefit Analysis

> **File:** diagnostic_outputs/api_analysis/03_cost_benefit_analysis.md
> **Date:** 2025-12-21
> **Purpose:** Financial analysis of ATTOM API alternatives

---

## Executive Summary

| Metric | Current (with ATTOM) | After Optimization |
|--------|---------------------|-------------------|
| Cost per property | $0.60 - $1.80 | $0.06 - $0.15 |
| Annual cost (1K/month) | $7,200 - $21,600 | $720 - $1,800 |
| One-time development | $0 | $15,000 - $25,000 |
| Break-even point | N/A | 2-4 months |

**Recommendation:** Implement phased migration starting Q1 2025.

---

## Current State (with ATTOM)

### Usage Pattern
```
Per Property Analysis:
├── /property/detail     → 1 call (property characteristics)
├── /attomavm/detail     → 1-3 calls (valuation with fallbacks)
├── /sale/snapshot       → 1 call (comparable sales)
└── /property/detail     → 0-10 calls (comp enrichment)
                           ─────────
                           3-16 calls per property
```

### Current Costs

| Usage Level | API Calls/Month | Cost @ $0.10/call | Cost @ $0.15/call | Cost @ $0.30/call |
|-------------|-----------------|-------------------|-------------------|-------------------|
| Demo (50) | 300 | $30 | $45 | $90 |
| Early (100) | 600 | $60 | $90 | $180 |
| Growth (500) | 3,000 | $300 | $450 | $900 |
| Scale (1,000) | 6,000 | $600 | $900 | $1,800 |
| Volume (5,000) | 30,000 | $3,000 | $4,500 | $9,000 |
| High (10,000) | 60,000 | $6,000 | $9,000 | $18,000 |

### Current Benefits
- ✓ Already implemented and tested
- ✓ Comprehensive data coverage
- ✓ Reliable API uptime
- ✓ No development maintenance

### Current Risks
- ✗ Cost scales linearly with growth
- ✗ Single vendor dependency for comps
- ✗ API pricing could increase
- ✗ Generic model (not Loudoun-optimized)

---

## Option A: Reduce ATTOM Usage (Quick Wins)

### Changes
1. **Disable comp enrichment** (0-10 calls saved)
2. **Use RentCast for characteristics** (1 call saved)
3. **Skip ATTOM when RentCast sufficient** (1 call saved)

### Implementation
```python
# Change in orchestrator.py

# BEFORE:
comps = self.attom.get_comparable_sales(address, enrich_sqft=True)

# AFTER:
comps = self.attom.get_comparable_sales(address, enrich_sqft=False)
```

### Costs

| Item | Cost | Notes |
|------|------|-------|
| Development | 4-8 hours | Simple code changes |
| Testing | 2-4 hours | Verify no regressions |
| **Total** | **$600-$1,200** | At $100/hour |

### Benefits

| Usage Level | Before | After | Savings/Month |
|-------------|--------|-------|---------------|
| 100/month | $60-180 | $30-60 | $30-120 |
| 500/month | $300-900 | $150-300 | $150-600 |
| 1,000/month | $600-1,800 | $300-600 | $300-1,200 |

### ROI Calculation
- Investment: $1,200
- Monthly savings at 500/month: $375 average
- **Break-even: 1 month**
- Year 1 ROI: **375%**

### Risks
- LOW: Display changes only, no data quality impact
- Comps without sqft still useful for price trends

---

## Option B: Geocode Sales for Local Comps

### Changes
1. **One-time geocoding** of 78K sales addresses
2. **Build spatial query** for radius search
3. **Replace ATTOM /sale/snapshot** with local query

### Implementation Approach
```
Phase 1: Geocoding (one-time)
├── Batch geocode 78K unique addresses
├── Add lat/lon to combined_sales.parquet
└── Validate coverage (expect 95%+ success)

Phase 2: Query Engine
├── Build haversine distance function
├── Create spatial index (optional, for performance)
└── Integrate with orchestrator

Phase 3: Integration
├── Replace get_comparable_sales with local query
├── A/B test against ATTOM for accuracy
└── Full migration
```

### Costs

| Item | Cost | Notes |
|------|------|-------|
| Geocoding API | $780 | 78K addresses @ $0.01/address |
| Development | $2,400-$4,000 | 24-40 hours @ $100/hour |
| Testing | $800-$1,600 | 8-16 hours |
| **Total** | **$4,000-$6,400** | |

### Benefits

| Usage Level | Before (ATTOM) | After (Local) | Savings/Month |
|-------------|----------------|---------------|---------------|
| 100/month | $45-135 | $0 | $45-135 |
| 500/month | $225-675 | $0 | $225-675 |
| 1,000/month | $450-1,350 | $0 | $450-1,350 |
| 5,000/month | $2,250-6,750 | $0 | $2,250-6,750 |

### ROI Calculation
- Investment: $5,200 average
- Monthly savings at 500/month: $450 average
- **Break-even: 3 months**
- Year 1 ROI: **936%**

### Additional Benefits
- More sales data (78K vs ATTOM sample)
- Full control over filtering
- Arms-length verification
- Faster queries (no API latency)

### Risks
- MEDIUM: Requires development and testing
- Geocoding accuracy (typically 95%+)
- Ongoing maintenance for new sales

---

## Option C: Build Proprietary AVM

### Changes
1. **Train ML model** on 78K Loudoun sales
2. **Feature engineering** for local factors
3. **Replace ATTOM AVM** with local model

### Model Features
```
Core Features:
├── Square footage
├── Bedrooms/bathrooms
├── Year built
├── Lot size
└── Property type

Location Features:
├── Latitude/longitude cluster
├── School district quality
├── Metro proximity
├── Data center proximity (Loudoun-specific)
└── Neighborhood median prices

Time Features:
├── Month of year
├── Market trend indicator
└── Days since last sale
```

### Implementation Timeline

| Phase | Duration | Hours | Cost @ $100/hr |
|-------|----------|-------|----------------|
| Data preparation | 2 weeks | 16-24 | $1,600-$2,400 |
| Model development | 3 weeks | 40-60 | $4,000-$6,000 |
| Validation | 1 week | 16-24 | $1,600-$2,400 |
| Integration | 1 week | 16-24 | $1,600-$2,400 |
| A/B testing | 2 weeks | 8-16 | $800-$1,600 |
| **Total** | **9 weeks** | **96-148** | **$9,600-$14,800** |

### Expected Performance
- Mean Absolute Error: <5% of sale price
- Better than generic AVMs for Loudoun
- Confidence intervals based on model uncertainty

### ROI Calculation
- Investment: $12,200 average
- Monthly savings at 500/month: $150 (AVM portion)
- Plus competitive advantage (priceless)
- **Break-even: 6-8 months** (cost savings only)

### Strategic Benefits
- **Competitive moat**: Unique to NewCo
- **Loudoun expertise**: Better than ATTOM for local market
- **Scalability**: Apply same approach to new counties
- **Investor story**: Proprietary technology differentiator

---

## Option D: Complete ATTOM Elimination

### Combined Implementation

| Component | Cost | Timeline |
|-----------|------|----------|
| Quick wins (Option A) | $1,000 | Week 1-2 |
| Geocoded comps (Option B) | $5,200 | Week 3-8 |
| Proprietary AVM (Option C) | $12,200 | Week 5-14 |
| APN index | $2,000 | Week 6-8 |
| Integration & testing | $3,000 | Week 12-16 |
| **Total** | **$23,400** | **16 weeks** |

### Cost Comparison (per property)

| Component | Current (ATTOM) | Future (Local) |
|-----------|-----------------|----------------|
| Property details | $0.10-$0.30 | $0 (RentCast) |
| Valuation (AVM) | $0.10-$0.30 | $0 (local model) |
| Comp sales | $0.30-$0.90 | $0 (local query) |
| Comp enrichment | $0-$3.00 | $0 (not needed) |
| **Total** | **$0.60-$4.50** | **$0.03-$0.10** |

Note: RentCast cost ($0.03-$0.10) already being paid.

### Savings Projection

| Year | Monthly Analyses | ATTOM Cost | New Cost | Annual Savings |
|------|------------------|------------|----------|----------------|
| 2025 | 500 | $4,500 | $450 | $48,600 |
| 2026 | 2,000 | $18,000 | $1,800 | $194,400 |
| 2027 | 5,000 | $45,000 | $4,500 | $486,000 |

### ROI Calculation
- Investment: $23,400
- Year 1 savings: $48,600 (at 500/month average)
- **Year 1 ROI: 207%**
- **Payback period: 6 months**

---

## Recommended Approach: Phased Implementation

### Phase 1: Quick Wins (January 2025)
- Disable comp enrichment
- RentCast-first for characteristics
- **Investment:** $1,000
- **Monthly savings:** $150-$600

### Phase 2: Geocoded Comps (February-March 2025)
- Batch geocode sales data
- Build local comp search
- **Investment:** $5,200
- **Monthly savings:** $450 additional

### Phase 3: Proprietary AVM (Q2 2025)
- Train ML model
- Integrate and validate
- **Investment:** $12,200
- **Competitive advantage:** Priceless

### Phase 4: Full Migration (Q3 2025)
- APN index
- Final integration
- ATTOM subscription review
- **Investment:** $5,000
- **Monthly savings:** Complete

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Geocoding failures | Medium | Low | Use multiple providers, manual review |
| Model accuracy | Medium | Medium | Extensive validation, keep ATTOM as fallback |
| RentCast data gaps | Low | Medium | ATTOM fallback for missing data |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Development delays | Medium | Low | Phased approach, quick wins first |
| ATTOM rate changes | Medium | Medium | Accelerates ROI if prices increase |
| New features needed | Low | Low | ATTOM available as backup |

### Recommended Fallback Strategy
1. Keep ATTOM credentials active (minimal cost when not used)
2. Log when RentCast/local data insufficient
3. Automatic ATTOM fallback for critical data
4. Monthly review of fallback usage

---

## Decision Matrix

| Criteria | Weight | Option A | Option B | Option C | Option D |
|----------|--------|----------|----------|----------|----------|
| Cost savings | 30% | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Implementation risk | 25% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Time to value | 20% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Strategic value | 15% | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Maintenance | 10% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Weighted Score** | | **3.8** | **2.9** | **2.6** | **3.2** |

### Recommendation

**Start with Option A (Quick Wins)** immediately for low-risk savings.

**Plan Option D (Full Migration)** over Q1-Q2 2025 for maximum long-term value.

The phased approach provides:
1. Immediate cost reduction (Week 1-2)
2. Validated approach before major investment
3. Proprietary technology moat
4. 90%+ cost reduction at scale

---

## Appendix: Implementation Checklist

### Week 1-2: Quick Wins
- [ ] Create branch `feature/reduce-attom-usage`
- [ ] Disable `enrich_sqft` in get_comparable_sales
- [ ] Add RentCast-first logic for property details
- [ ] Test with 10 sample properties
- [ ] Deploy and monitor

### Week 3-6: Geocoding
- [ ] Set up Google Maps API credentials
- [ ] Create batch geocoding script
- [ ] Run geocoding (expect 2-3 hours runtime)
- [ ] Validate coverage (target: 95%+)
- [ ] Update Parquet file

### Week 5-10: Local Comp Search
- [ ] Implement haversine distance function
- [ ] Build find_nearby_sales function
- [ ] Create comparison report vs ATTOM
- [ ] Integrate with orchestrator (behind feature flag)
- [ ] A/B test for 2 weeks

### Week 8-14: Proprietary AVM
- [ ] Prepare training dataset
- [ ] Feature engineering
- [ ] Model training and evaluation
- [ ] Integration with orchestrator
- [ ] Validation against ATTOM predictions

### Week 14-16: Final Integration
- [ ] Build APN lookup index
- [ ] Remove ATTOM feature flags
- [ ] Update documentation
- [ ] Review ATTOM subscription
- [ ] Monitor for 2 weeks

---

*End of Cost-Benefit Analysis*
