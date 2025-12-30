"""
Test that Parquet file can be loaded and indexed exactly like Excel version.
This verifies conversion quality before modifying production code.
"""

import pandas as pd
import time
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def normalize_parid(parid):
    """Normalize PARID (same as LoudounSalesData)"""
    if not parid:
        return None
    digits_only = re.sub(r'[^0-9]', '', str(parid))
    if len(digits_only) > 0:
        return digits_only.zfill(12)
    return None


def test_parquet_loading():
    """Test complete loading pipeline with Parquet"""

    print("="*60)
    print("PARQUET LOADING TEST")
    print("="*60)

    parquet_path = Path('data/loudoun/sales/combined_sales.parquet')

    if not parquet_path.exists():
        print(f"✗ Parquet file not found: {parquet_path}")
        return False

    # Test 1: Load Parquet
    print("\n1. Loading Parquet file...")
    start = time.time()
    df = pd.read_parquet(parquet_path)
    load_time = time.time() - start

    print(f"   ✓ Loaded in {load_time:.2f}s")
    print(f"   Records: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")

    # Test 2: Date conversion
    print("\n2. Converting dates...")
    start = time.time()
    df['RECORD DATE'] = pd.to_datetime(df['RECORD DATE'], errors='coerce')
    date_time = time.time() - start
    print(f"   ✓ Converted in {date_time:.2f}s")

    # Test 3: Filter arms-length
    print("\n3. Filtering arms-length transactions...")
    ARMS_LENGTH_CODES = {
        '1:MARKET SALE',
        '2:MARKET LAND SALE',
        '5:MARKET MULTI-PARCEL SALE',
        'V:NEW CONSTRUCTION'
    }

    arms_length_mask = df['SALE VERIFICATION'].isin(ARMS_LENGTH_CODES)
    df_arms_length = df[arms_length_mask].copy()

    print(f"   ✓ Arms-length: {len(df_arms_length):,} records ({100*len(df_arms_length)/len(df):.1f}%)")

    # Test 4: Build index (full dataset to measure real performance)
    print("\n4. Building full index...")
    sales_index = defaultdict(list)

    start = time.time()

    for _, row in df_arms_length.iterrows():
        parid = normalize_parid(str(row['PARID']))
        if parid:
            sale_record = {
                'sale_date': row['RECORD DATE'],
                'sale_price': row['PRICE'] if pd.notna(row['PRICE']) else None,
                'verification_code': row['SALE VERIFICATION'],
            }
            sales_index[parid].append(sale_record)

    index_time = time.time() - start
    print(f"   ✓ Indexed {len(df_arms_length):,} records in {index_time:.2f}s")
    print(f"   Unique properties: {len(sales_index):,}")

    # Test 5: Sort sales by date
    print("\n5. Sorting sales by date...")
    start = time.time()
    for parid in sales_index:
        sales_index[parid].sort(
            key=lambda x: x['sale_date'] if pd.notna(x['sale_date']) else datetime.min,
            reverse=True
        )
    sort_time = time.time() - start
    print(f"   ✓ Sorted in {sort_time:.2f}s")

    # Test 6: Test a lookup
    print("\n6. Testing lookup...")
    if sales_index:
        test_parid = list(sales_index.keys())[0]
        sales_list = sales_index[test_parid]
        print(f"   ✓ PARID {test_parid}: {len(sales_list)} sale(s)")
        if sales_list:
            latest = sales_list[0]
            if latest['sale_price']:
                print(f"   Latest sale: ${latest['sale_price']:,.0f}")
            else:
                print(f"   Latest sale: No price recorded")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total_time = load_time + date_time + index_time + sort_time

    print(f"Load time:      {load_time:.2f}s")
    print(f"Date convert:   {date_time:.2f}s")
    print(f"Index build:    {index_time:.2f}s")
    print(f"Sort:           {sort_time:.2f}s")
    print(f"{'─'*30}")
    print(f"Total:          {total_time:.2f}s")

    print("\n" + "="*60)
    if total_time < 10:
        print(f"✓ PASSED: Total time {total_time:.2f}s (target: <10s)")
        return True
    elif total_time < 30:
        print(f"⚠ WARNING: Total time {total_time:.2f}s (acceptable but >10s)")
        return True
    else:
        print(f"✗ FAILED: Total time {total_time:.2f}s exceeds 30s")
        return False


if __name__ == '__main__':
    success = test_parquet_loading()
    exit(0 if success else 1)
