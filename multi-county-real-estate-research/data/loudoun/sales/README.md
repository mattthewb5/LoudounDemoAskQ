# Loudoun County Sales Data

Official property sales records from the Loudoun County Commissioner of Revenue.

## Overview

**Data Format:** Parquet (converted from Excel for 105x faster loading)
**Coverage:** 2020-01-02 to 2025-present
**Records:** 78,300+ sales transactions
**Properties:** 40,217 unique parcels
**File Size:** 5.3 MB Parquet (vs 7.4 MB Excel)
**Source:** Loudoun County Commissioner of Revenue

## Performance Metrics

### Before Optimization (Excel)
- **File I/O:** 9.98 seconds per load
- **Total Load:** 90-150 seconds (with indexing)
- **Cached Access:** Not available
- **Demo Wait Time:** 90-150 seconds per property

### After Optimization (Parquet + Caching)
- **File I/O:** 0.09 seconds (105x faster)
- **First Load:** 2.83 seconds (97% improvement)
- **Cached Access:** 0.0001 seconds (instant)
- **Demo Wait Time:** 2.83s first property, ~0s subsequent

### Impact
- **First Analysis:** 97% reduction in load time
- **Subsequent Analyses:** Instant (99.99% improvement)
- **File Size:** 28% smaller storage footprint

## File Structure

```
sales/
├── README.md                     # This file
├── combined_sales.parquet        # Optimized Parquet format (USE THIS)
├── combined_sales.xlsx           # Original Excel (kept for reference)
├── 2020_sales.xlsx              # Historical Excel files
├── 2021_sales.XLSX              # (source data for validation)
├── 2022_sales.XLSX
├── 2023_sales.XLSX
├── 2024_sales.XLSX
└── 2025_sales.xlsx
```

## Data Schema

The Parquet file contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `PARID` | String | 12-digit property identifier (e.g., "110394004000") |
| `RECORD DATE` | DateTime | Date of sale recording |
| `PRICE` | Integer | Sale price in USD |
| `SALE VERIFICATION` | String | Transaction type code (see below) |
| `INSTRUMENT#` | String | Recording instrument number |
| `SALEKEY` | String | Unique sale identifier |
| `OLD OWNER` | String | Seller name |
| `NEW OWNER` | String | Buyer name |
| `SALE TYPE` | String | Type of transaction |
| `# OF PARCELS` | Integer | Number of parcels in transaction |

## Sale Verification Codes

### Arms-Length Transactions (Reliable Market Data)
- `1:MARKET SALE` - Standard market sale
- `2:MARKET LAND SALE` - Land-only market sale
- `5:MARKET MULTI-PARCEL SALE` - Multi-parcel market sale
- `V:NEW CONSTRUCTION` - New construction sale

### Non-Arms-Length (Filtered Out)
- `0:N/A` - Not applicable
- `3:NON-MARKET SALE` - Non-market transaction
- `5B:NON-MARKET MULTI-PRCL SALE` - Non-market multi-parcel
- `7:RELATED PARTIES` - Sale between related parties
- `Z:FORECLOSURE` - Foreclosure sale
- `F:ESTATE SALE` - Estate sale
- `K:UNABLE TO VERIFY` - Unverified transaction
- `N:OUTLIER NON-REPRESENTATIVE PRICE` - Outlier pricing
- `C:ADU SALE` - Accessory dwelling unit sale

**Note:** By default, only arms-length transactions are used for market analysis to ensure accurate property valuations.

## Usage

### In Production Code (Streamlit App)

```python
from core.loudoun_sales_data import get_cached_loudoun_sales_data

# Get cached instance (lazy loading, persistent across app reruns)
sales_data = get_cached_loudoun_sales_data()

# Lookup sales history by APN/PARID
result = sales_data.get_sales_history("110-39-4004-000")

if result['found']:
    for sale in result['sales']:
        print(f"Sold on {sale['sale_date']} for ${sale['sale_price']:,}")
```

### In Scripts (Non-Streamlit)

```python
from core.loudoun_sales_data import LoudounSalesData

# Direct instantiation (no caching)
sales_data = LoudounSalesData()

# Same API for lookups
result = sales_data.get_sales_history("110-39-4004-000")
```

### APN/PARID Formats Supported

The module automatically handles both ATTOM and County formats:

```python
# ATTOM format (with dashes)
sales_data.get_sales_history("110-39-4004-000")

# County format (12 digits, no dashes)
sales_data.get_sales_history("110394004000")

# Short format (auto-padded)
sales_data.get_sales_history("123456")  # → "000000123456"
```

## Viewing Parquet Data

### Using Python

```bash
cd /path/to/multi-county-real-estate-research
python scripts/view_parquet_sales.py
```

### Using Pandas Directly

```python
import pandas as pd

df = pd.read_parquet('data/loudoun/sales/combined_sales.parquet')
print(df.head())
print(f"Total records: {len(df):,}")
print(f"Date range: {df['RECORD DATE'].min()} to {df['RECORD DATE'].max()}")
```

### Using DuckDB

```sql
SELECT
    COUNT(*) as total_sales,
    MIN("RECORD DATE") as earliest_sale,
    MAX("RECORD DATE") as latest_sale,
    AVG(PRICE) as avg_price
FROM 'combined_sales.parquet'
WHERE "SALE VERIFICATION" = '1:MARKET SALE';
```

## Data Refresh Procedures

### When to Refresh

- **Frequency:** Quarterly or when new sales data is published
- **Source:** Loudoun County Commissioner of Revenue
- **Indicators:** Missing recent sales, date range gaps

### Refresh Steps

1. **Obtain Updated Excel Files**
   ```bash
   # Download new Excel files from County source
   # Save to data/loudoun/sales/YYYY_sales.xlsx
   ```

2. **Update Combined Excel File**
   ```bash
   # Manually combine all years into combined_sales.xlsx
   # Or use County-provided combined file
   ```

3. **Convert to Parquet**
   ```bash
   cd /path/to/multi-county-real-estate-research
   python scripts/convert_sales_to_parquet.py --county loudoun
   ```

4. **Verify Conversion**
   ```bash
   # Check output for:
   # - Row count matches Excel
   # - Column names identical
   # - Date range correct
   # - Performance speedup >50x
   ```

5. **Test in Application**
   ```bash
   # Test a few known properties
   python -m core.loudoun_sales_data

   # Or run integration tests
   python scripts/test_parquet_loading.py
   ```

6. **Clear Streamlit Cache**
   ```bash
   # In Streamlit app, use:
   st.cache_resource.clear()

   # Or restart Streamlit server
   ```

## Troubleshooting

### Problem: "Sales data file not found"

**Solution:**
```bash
# Verify file exists
ls -lh data/loudoun/sales/combined_sales.parquet

# If missing, convert from Excel
python scripts/convert_sales_to_parquet.py --county loudoun
```

### Problem: "Missing required columns"

**Cause:** Parquet file structure changed or corrupted

**Solution:**
```bash
# Delete and reconvert
rm data/loudoun/sales/combined_sales.parquet
python scripts/convert_sales_to_parquet.py --county loudoun --force
```

### Problem: Slow loading (>10 seconds)

**Possible causes:**
1. Not using cached version (check for `@st.cache_resource`)
2. Large dataset (>100k records may need optimization)
3. Network/disk I/O issues

**Solution:**
```python
# Verify caching is enabled
from core.loudoun_sales_data import get_cached_loudoun_sales_data
sales = get_cached_loudoun_sales_data()  # Should show "Loading..." once only
```

### Problem: No sales found for valid property

**Debugging:**
```python
from core.loudoun_sales_data import LoudounSalesData

sales = LoudounSalesData()

# Check statistics
print(sales.get_stats())

# Try with non-arms-length included
result = sales.get_sales_history("110-39-4004-000", include_non_arms_length=True)
print(result)

# Verify PARID normalization
print(sales._convert_apn_to_parid("110-39-4004-000"))  # Should be "110394004000"
```

### Problem: Parquet file corrupted

**Solution:**
```bash
# Reconvert from source Excel (force overwrite)
python scripts/convert_sales_to_parquet.py --county loudoun --force

# Verify with test script
python scripts/test_parquet_loading.py
```

## Data Quality Notes

### What's Included
- All recorded sales 2020-2025
- Both residential and commercial properties
- Multi-parcel transactions
- New construction sales

### What's Filtered (By Default)
- Non-arms-length transactions (family transfers, foreclosures, etc.)
- Sales with missing or invalid prices
- Related party transactions
- Outlier/non-representative prices

### Known Limitations
- Historical data only extends to 2020
- Some properties may have incomplete ownership information
- Instrument numbers may be missing for older records
- Prices reflect recording date, not agreement date

## Multi-County Pattern

This sales data module follows a pattern designed to scale to multiple counties:

### Scalability Design
- **Per-County Files:** Each county maintains separate Parquet files
- **Lazy Loading:** Data only loads when accessed
- **Independent Caching:** Each county cached separately
- **Memory Efficient:** ~30 MB per county (only loaded counties consume memory)

### Adding New Counties

1. Create `data/<county>/sales/combined_sales.xlsx`
2. Convert to Parquet: `python scripts/convert_sales_to_parquet.py --county <county>`
3. Create `<County>SalesData` class (follow `LoudounSalesData` pattern)
4. Add cached factory: `get_cached_<county>_sales_data()`
5. Update orchestrator to use cached factory

See `docs/MULTI_COUNTY_SCALING.md` for complete guide.

## Technical Details

### Why Parquet?

1. **Speed:** Columnar format enables fast filtering/aggregation
2. **Size:** Compression reduces file size by ~30%
3. **Schema:** Enforces data types (datetime, int, string)
4. **Compatibility:** Works with pandas, duckdb, spark, etc.
5. **Industry Standard:** Used by AWS, Google, Microsoft for big data

### Caching Strategy

```python
@st.cache_resource
def get_cached_loudoun_sales_data() -> 'LoudounSalesData':
    """
    Streamlit caching pattern:
    - Loads once per session
    - Persists until server restart
    - Shared across all users
    - Instant access after first load
    """
    sales_data = LoudounSalesData()
    return sales_data
```

**Benefits:**
- First property: 2.83s load
- All subsequent properties: <0.001s (instant)
- No memory leaks (cached at resource level)
- Automatic invalidation on server restart

### Indexing Strategy

The module builds an in-memory index for O(1) lookup:

```python
sales_index: Dict[str, List[Dict]] = {
    "110394004000": [
        {"sale_date": "2023-05-15", "sale_price": 850000, ...},
        {"sale_date": "2020-03-20", "sale_price": 725000, ...},
    ],
    ...
}
```

**Performance:**
- Index build time: ~2 seconds for 78k records
- Lookup time: <0.001 seconds per property
- Memory usage: ~30 MB for full index

## Version History

- **v2.0** (2025-12-19): Parquet format, Streamlit caching, 105x speedup
- **v1.0** (2024): Original Excel-based implementation

## Support

**Data Questions:** Loudoun County Commissioner of Revenue
**Technical Issues:** See `docs/PERFORMANCE_OPTIMIZATION.md`
**Code Updates:** See commit history for this file

---

Last Updated: 2025-12-19
Maintained by: Development Team
Data Source: Loudoun County Commissioner of Revenue
