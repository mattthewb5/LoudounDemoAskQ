"""
Excel → Parquet conversion for sales data
Supports single county or batch conversion of all counties
Designed to scale as new counties are added
"""

import pandas as pd
import os
from pathlib import Path
import argparse
import time


def find_sales_files():
    """
    Auto-detect all county sales directories and Excel files.

    Returns:
        List of tuples: (county_name, excel_path, parquet_path)
    """
    data_dir = Path('data')
    conversions = []

    # Look for all county directories with sales subdirectories
    for county_dir in data_dir.iterdir():
        if not county_dir.is_dir():
            continue

        sales_dir = county_dir / 'sales'
        if not sales_dir.exists():
            continue

        # Look for combined_sales.xlsx
        for excel_file in sales_dir.glob('combined_sales.xlsx'):
            parquet_file = excel_file.with_suffix('.parquet')
            conversions.append((
                county_dir.name,
                excel_file,
                parquet_file
            ))

    return conversions


def needs_conversion(excel_path, parquet_path):
    """
    Check if conversion is needed.

    Returns True if:
    - Parquet doesn't exist
    - Excel is newer than Parquet
    """
    if not parquet_path.exists():
        return True

    excel_mtime = excel_path.stat().st_mtime
    parquet_mtime = parquet_path.stat().st_mtime

    return excel_mtime > parquet_mtime


def convert_excel_to_parquet(excel_path, parquet_path, county_name):
    """
    Convert single Excel file to Parquet with verification.

    Args:
        excel_path: Path to Excel file
        parquet_path: Path for output Parquet file
        county_name: Name of county (for logging)

    Returns:
        dict with conversion stats
    """
    print(f"\n{'='*60}")
    print(f"Converting: {county_name.upper()}")
    print(f"{'='*60}")

    # Read Excel
    print(f"1. Reading Excel...")
    print(f"   Source: {excel_path}")
    excel_size_mb = excel_path.stat().st_size / 1024 / 1024
    print(f"   Size: {excel_size_mb:.2f} MB")

    start = time.time()
    df = pd.read_excel(excel_path)
    read_time = time.time() - start

    print(f"   ✓ Loaded: {len(df):,} records, {len(df.columns)} columns")
    print(f"   Read time: {read_time:.2f}s")

    # Show preview
    print(f"\n2. Data Preview:")
    print(f"   Columns: {list(df.columns[:5])}...")
    if 'RECORD DATE' in df.columns:
        print(f"   Date range: {df['RECORD DATE'].min()} to {df['RECORD DATE'].max()}")

    # Convert to Parquet
    print(f"\n3. Converting to Parquet...")

    # Handle mixed types - convert object columns to string to avoid pyarrow issues
    # This is safer than trying to detect mixed types
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        # Skip if it's a clean string column (no mixed types)
        if df[col].apply(lambda x: isinstance(x, (str, type(None))) or pd.isna(x)).all():
            continue
        print(f"   ⚠ Converting mixed-type column '{col}' to string")
        df[col] = df[col].astype(str).replace('nan', '')

    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    parquet_size_mb = parquet_path.stat().st_size / 1024 / 1024
    print(f"   ✓ Saved: {parquet_path}")
    print(f"   Size: {parquet_size_mb:.2f} MB ({excel_size_mb / parquet_size_mb:.1f}x smaller)")

    # Verify
    print(f"\n4. Verifying...")
    df_verify = pd.read_parquet(parquet_path)

    checks = {
        'Row count': len(df) == len(df_verify),
        'Column count': len(df.columns) == len(df_verify.columns),
        'Column names': list(df.columns) == list(df_verify.columns),
    }

    all_passed = all(checks.values())
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"   {status} {check}")

    if not all_passed:
        raise ValueError(f"Verification failed for {county_name}!")

    # Performance test
    print(f"\n5. Performance Test:")

    start = time.time()
    _ = pd.read_excel(excel_path)
    excel_load_time = time.time() - start

    start = time.time()
    _ = pd.read_parquet(parquet_path)
    parquet_load_time = time.time() - start

    speedup = excel_load_time / parquet_load_time

    print(f"   Excel load: {excel_load_time:.2f}s")
    print(f"   Parquet load: {parquet_load_time:.2f}s")
    print(f"   Speedup: {speedup:.1f}x faster")

    return {
        'county': county_name,
        'records': len(df),
        'excel_size_mb': excel_size_mb,
        'parquet_size_mb': parquet_size_mb,
        'excel_load_time': excel_load_time,
        'parquet_load_time': parquet_load_time,
        'speedup': speedup
    }


def main():
    parser = argparse.ArgumentParser(
        description='Convert sales data from Excel to Parquet format'
    )
    parser.add_argument(
        '--county',
        help='Specific county to convert (e.g., "loudoun"). If not specified, converts all counties.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force conversion even if Parquet is up-to-date'
    )

    args = parser.parse_args()

    print("="*60)
    print("SALES DATA CONVERSION: Excel → Parquet")
    print("="*60)

    # Find all conversion candidates
    conversions = find_sales_files()

    if not conversions:
        print("\n✗ No sales Excel files found!")
        print("   Looking for: data/*/sales/combined_sales.xlsx")
        return

    print(f"\nFound {len(conversions)} county/counties with sales data:")
    for county, excel_path, parquet_path in conversions:
        status = "✓ Current" if parquet_path.exists() and not needs_conversion(excel_path, parquet_path) else "⚠ Needs conversion"
        print(f"  - {county}: {status}")

    # Filter by county if specified
    if args.county:
        conversions = [c for c in conversions if c[0].lower() == args.county.lower()]
        if not conversions:
            print(f"\n✗ County '{args.county}' not found!")
            return

    # Filter out up-to-date conversions unless --force
    if not args.force:
        conversions = [c for c in conversions if needs_conversion(c[1], c[2])]
        if not conversions:
            print("\n✓ All Parquet files are up-to-date!")
            print("   Use --force to reconvert anyway")
            return

    print(f"\nConverting {len(conversions)} county/counties...")

    # Convert each county
    results = []
    for county_name, excel_path, parquet_path in conversions:
        try:
            result = convert_excel_to_parquet(excel_path, parquet_path, county_name)
            results.append(result)
        except Exception as e:
            print(f"\n✗ FAILED: {county_name}")
            print(f"   Error: {e}")
            continue

    # Summary
    if results:
        print("\n" + "="*60)
        print("CONVERSION SUMMARY")
        print("="*60)

        for r in results:
            print(f"\n{r['county'].upper()}:")
            print(f"  Records: {r['records']:,}")
            print(f"  Size: {r['excel_size_mb']:.1f} MB → {r['parquet_size_mb']:.1f} MB ({r['excel_size_mb']/r['parquet_size_mb']:.1f}x smaller)")
            print(f"  Speed: {r['excel_load_time']:.1f}s → {r['parquet_load_time']:.1f}s ({r['speedup']:.1f}x faster)")

        print("\n" + "="*60)
        print("✓ CONVERSION COMPLETE")
        print("="*60)
        print(f"Converted {len(results)} county/counties successfully")
        print("\nNext steps:")
        print("  1. Verify Parquet file works correctly")
        print("  2. Update code to use .parquet files (Part 2)")
        print("  3. Add caching decorators (Part 2)")


if __name__ == '__main__':
    main()
