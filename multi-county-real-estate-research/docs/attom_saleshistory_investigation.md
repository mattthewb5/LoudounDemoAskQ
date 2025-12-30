# ATTOM Sales History API Investigation

**Date:** December 11, 2025
**Endpoint:** `/saleshistory/detail`
**Test Property:** 43422 Cloister Pl, Leesburg, VA 20176
**Status:** Investigation Complete - Ready for Implementation

---

## Executive Summary

The ATTOM `/saleshistory/detail` endpoint is accessible and returns structured sale history data. However, **Virginia is a non-disclosure state**, meaning all sale prices are **ESTIMATED** rather than actual recorded transaction amounts. This must be clearly disclosed to users in any UI implementation.

---

## 1. Endpoint Access

| Item | Result |
|------|--------|
| HTTP Status | 200 OK |
| API Status Code | `0` ("SuccessWithResult") |
| Endpoint URL | `https://api.gateway.attomdata.com/propertyapi/v1.0.0/saleshistory/detail` |
| Parameters | `address1`, `address2` |

---

## 2. Response Structure

### Top-Level Structure
```json
{
    "status": { ... },
    "property": [{
        "identifier": { ... },
        "address": { ... },
        "location": { ... },
        "summary": { ... },
        "building": { ... },
        "salehistory": [ ... ]  // <-- Sale records here
    }]
}
```

### Sale History Record Structure
```json
{
    "saleSearchDate": "2020-04-28",
    "saleTransDate": "2020-04-27",
    "amount": {
        "saleamt": 1299000,
        "salecode": "ESTIMATED Sale price is not available due to non-disclosure counties",
        "salerecdate": "2020-04-28",
        "saledisclosuretype": 0,
        "saledoctype": "DEED",
        "saledocnum": "20200428030025",
        "saletranstype": "Resale"
    },
    "calculation": {
        "priceperbed": 259800,
        "pricepersizeunit": 234.14
    },
    "vintage": {
        "lastModified": "2020-06-03"
    }
}
```

---

## 3. Field Documentation

| Field | Path | Type | Description |
|-------|------|------|-------------|
| Sale Transaction Date | `saleTransDate` | string | Actual transaction date (YYYY-MM-DD) |
| Sale Recording Date | `amount.salerecdate` | string | Official recording date |
| Sale Amount | `amount.saleamt` | int | Price in dollars (ESTIMATED in VA) |
| Sale Code | `amount.salecode` | string | Indicates if estimated |
| Disclosure Type | `amount.saledisclosuretype` | int | 0 = non-disclosure state |
| Document Type | `amount.saledoctype` | string | e.g., "DEED" |
| Document Number | `amount.saledocnum` | string | Recording document number |
| Transaction Type | `amount.saletranstype` | string | e.g., "Resale", "Foreclosure" |
| Price Per Bed | `calculation.priceperbed` | int | Calculated field |
| Price Per SqFt | `calculation.pricepersizeunit` | float | Calculated $/sqft |

---

## 4. Critical Finding: Non-Disclosure State

```
"salecode": "ESTIMATED Sale price is not available due to non-disclosure counties"
"saledisclosuretype": 0
```

**Virginia does NOT require disclosure of sale prices.** All prices returned by ATTOM for Virginia properties are **ESTIMATES** based on property characteristics, not actual recorded transaction amounts.

### Required UI Disclosure
Any implementation must include clear disclosure:
```
Virginia is a non-disclosure state. Sale prices shown are ESTIMATES
based on property characteristics, not recorded transaction amounts.
```

---

## 5. Data Quality Assessment

| Metric | Test Property Result | Notes |
|--------|---------------------|-------|
| Sales Returned | 1 | Property built 2004 |
| Oldest Sale | 2020 | Missing earlier history |
| Date Format | YYYY-MM-DD | Compatible with existing parsers |
| Transaction Type | "Resale" | Arms-length transaction |

---

## 6. Recommended Dataclass

```python
@dataclass
class SaleHistoryRecord:
    """Individual sale record from ATTOM sales history."""
    sale_price: int                          # amount.saleamt
    sale_date: str                           # saleTransDate
    recording_date: str                      # amount.salerecdate
    transaction_type: Optional[str] = None   # amount.saletranstype
    document_type: Optional[str] = None      # amount.saledoctype
    document_number: Optional[str] = None    # amount.saledocnum
    price_per_sqft: Optional[float] = None   # calculation.pricepersizeunit
    is_estimated: bool = False               # Derived from salecode
    disclosure_type: int = 0                 # amount.saledisclosuretype
```

---

## 7. Integration Notes

### Compatibility with Existing Code
- Date format (YYYY-MM-DD) supported by `parse_sale_date()` in `market_adjustments.py`
- API authentication pattern identical to existing endpoints
- Response structure similar to `/property/detail`

### Implementation Steps
1. Add `get_sale_history(address)` method to `ATTOMClient`
2. Create `SaleHistoryRecord` dataclass
3. Add UI section in `loudoun_streamlit_app.py`
4. Include non-disclosure state warning
5. Display transaction types for data quality context

---

## 8. Recommendation

**PROCEED** with implementation, ensuring:
1. Clear disclosure that Virginia prices are estimated
2. Transaction type displayed to help users assess data quality
3. Handle empty `salehistory` arrays gracefully
4. Note that history may be incomplete for older properties
