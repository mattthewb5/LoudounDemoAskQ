"""
Parquet file viewer for debugging and inspection
Use this when you need to quickly inspect sales data without Excel
"""

import pandas as pd
import argparse
from pathlib import Path


def view_parquet(parquet_path, sample_size=20, export_csv=None):
    """
    Display Parquet file contents and optionally export to CSV.

    Args:
        parquet_path: Path to Parquet file
        sample_size: Number of rows to display
        export_csv: Optional path to export sample as CSV
    """
    print("="*60)
    print(f"PARQUET VIEWER: {parquet_path}")
    print("="*60)

    # Load
    df = pd.read_parquet(parquet_path)

    # Basic info
    print(f"\nRows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Memory: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

    # Column info
    print(f"\nColumns:")
    for col in df.columns:
        dtype = df[col].dtype
        nulls = df[col].isna().sum()
        null_pct = 100 * nulls / len(df)
        print(f"  {col:25s} {str(dtype):12s} {nulls:>6,} nulls ({null_pct:>5.1f}%)")

    # Sample data
    print(f"\nFirst {sample_size} rows:")
    print(df.head(sample_size).to_string())

    # Statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        print(f"\nNumeric column statistics:")
        print(df[numeric_cols].describe().to_string())

    # Export if requested
    if export_csv:
        export_path = Path(export_csv)
        df.head(sample_size * 10).to_csv(export_path, index=False)
        print(f"\n✓ Exported {sample_size * 10} rows to: {export_path}")


def main():
    parser = argparse.ArgumentParser(
        description='View Parquet sales data files'
    )
    parser.add_argument(
        'county',
        help='County name (e.g., "loudoun")'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=20,
        help='Number of rows to display (default: 20)'
    )
    parser.add_argument(
        '--export',
        help='Export sample to CSV file'
    )

    args = parser.parse_args()

    # Find parquet file
    parquet_path = Path(f'data/{args.county}/sales/combined_sales.parquet')

    if not parquet_path.exists():
        print(f"✗ Parquet file not found: {parquet_path}")
        print(f"   Have you run convert_sales_to_parquet.py?")
        return

    view_parquet(parquet_path, args.sample, args.export)


if __name__ == '__main__':
    main()
