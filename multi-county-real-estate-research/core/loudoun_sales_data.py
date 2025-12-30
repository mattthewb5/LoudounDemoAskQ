"""
Loudoun County Sales Data Lookup Module

Provides efficient lookup of property sales history from Loudoun County
Commissioner of Revenue official records (2020-2025).

Data Source: Loudoun County Commissioner of Revenue
Coverage: 2020-01-02 to present (updated periodically)
Records: ~78,000 sales transactions
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

import pandas as pd


# Arms-length transaction codes (reliable market indicators)
ARMS_LENGTH_CODES = {
    '1:MARKET SALE',
    '2:MARKET LAND SALE',
    '5:MARKET MULTI-PARCEL SALE',
    'V:NEW CONSTRUCTION',
}

# Non-arms-length codes (exclude from valuation analysis)
NON_ARMS_LENGTH_CODES = {
    '0:N/A',
    '3:NON-MARKET SALE',
    '5B:NON-MARKET MULTI-PRCL SALE',
    '7:RELATED PARTIES',
    'Z:FORECLOSURE',
    'F:ESTATE SALE',
    'K:UNABLE TO VERIFY',
    'N:OUTLIER NON-REPRESENTATIVE PRICE',
    'C:ADU SALE',
}


class LoudounSalesData:
    """
    Efficient lookup of Loudoun County property sales history.

    Loads sales data from Parquet file (converted from Excel for 100x faster loading)
    and indexes by PARID for O(1) lookup performance.

    Usage:
        sales_data = LoudounSalesData()
        history = sales_data.get_sales_history("110-39-4004-000")
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Load and index sales data.

        Args:
            data_path: Path to combined_sales.parquet. If None, uses default location.
        """
        if data_path is None:
            # Default path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, 'data', 'loudoun', 'sales', 'combined_sales.parquet')

        self.data_path = data_path
        self.df = None
        self.sales_index: Dict[str, List[Dict]] = defaultdict(list)
        self.data_loaded = False
        self.load_error: Optional[str] = None
        self.stats: Dict = {}

        self._load_data()

    def _load_data(self) -> None:
        """Load and index sales data from Parquet file."""
        try:
            if not os.path.exists(self.data_path):
                self.load_error = f"Sales data file not found: {self.data_path}"
                return

            # Load from Parquet (converted from Excel for 100x faster loading)
            # Original Excel: 9.98s load time, Parquet: 0.09s (105x speedup)
            # Use scripts/convert_sales_to_parquet.py to update when source data changes
            self.df = pd.read_parquet(self.data_path)

            # Validate required columns
            required_cols = ['PARID', 'RECORD DATE', 'PRICE', 'SALE VERIFICATION']
            missing_cols = [c for c in required_cols if c not in self.df.columns]
            if missing_cols:
                self.load_error = f"Missing required columns: {missing_cols}"
                return

            # Convert RECORD DATE to datetime
            self.df['RECORD DATE'] = pd.to_datetime(self.df['RECORD DATE'], errors='coerce')

            # Calculate statistics before filtering
            total_records = len(self.df)

            # Filter for arms-length transactions only
            arms_length_mask = self.df['SALE VERIFICATION'].isin(ARMS_LENGTH_CODES)
            self.df_arms_length = self.df[arms_length_mask].copy()
            arms_length_count = len(self.df_arms_length)

            # Index by PARID (normalized to 12-digit string)
            for _, row in self.df_arms_length.iterrows():
                parid = self._normalize_parid(str(row['PARID']))
                if parid:
                    sale_record = {
                        'sale_date': row['RECORD DATE'],
                        'sale_price': row['PRICE'] if pd.notna(row['PRICE']) else None,
                        'verification_code': row['SALE VERIFICATION'],
                        'instrument_number': row.get('INSTRUMENT#', ''),
                        'sale_key': row.get('SALEKEY', ''),
                        'old_owner': row.get('OLD OWNER', ''),
                        'new_owner': row.get('NEW OWNER', ''),
                        'sale_type': row.get('SALE TYPE', ''),
                        'num_parcels': row.get('# OF PARCELS', 1),
                    }
                    self.sales_index[parid].append(sale_record)

            # Sort each PARID's sales by date (newest first)
            for parid in self.sales_index:
                self.sales_index[parid].sort(
                    key=lambda x: x['sale_date'] if pd.notna(x['sale_date']) else datetime.min,
                    reverse=True
                )

            # Calculate date range
            valid_dates = self.df_arms_length['RECORD DATE'].dropna()
            min_date = valid_dates.min() if len(valid_dates) > 0 else None
            max_date = valid_dates.max() if len(valid_dates) > 0 else None

            # Store statistics
            self.stats = {
                'total_records': total_records,
                'arms_length_records': arms_length_count,
                'unique_properties': len(self.sales_index),
                'date_range_start': min_date.strftime('%Y-%m-%d') if min_date else None,
                'date_range_end': max_date.strftime('%Y-%m-%d') if max_date else None,
                'filtered_out': total_records - arms_length_count,
            }

            self.data_loaded = True

        except Exception as e:
            self.load_error = f"Error loading sales data: {str(e)}"

    def _normalize_parid(self, parid: str) -> Optional[str]:
        """
        Normalize PARID to 12-digit string format.

        Args:
            parid: Raw PARID string (may have various formats)

        Returns:
            12-digit normalized PARID or None if invalid
        """
        if not parid:
            return None

        # Remove any non-numeric characters
        digits_only = re.sub(r'[^0-9]', '', str(parid))

        # Pad to 12 digits if needed
        if len(digits_only) > 0:
            return digits_only.zfill(12)

        return None

    def _convert_apn_to_parid(self, apn: str) -> str:
        """
        Convert ATTOM APN format to County PARID format.

        ATTOM format: "110-39-4004-000" (with dashes)
        County format: "110394004000" (12 digits, no dashes)

        Args:
            apn: ATTOM-style APN with dashes

        Returns:
            12-digit PARID string
        """
        # Strip all non-numeric characters (dashes, spaces, etc.)
        digits_only = re.sub(r'[^0-9]', '', str(apn))

        # Ensure 12-digit format
        return digits_only.zfill(12)

    def get_sales_history(self, apn: str, max_records: int = 3,
                          include_non_arms_length: bool = False) -> Dict:
        """
        Get sales history for a property by APN/PARID.

        Args:
            apn: Property APN (ATTOM format like "110-39-4004-000" or PARID "110394004000")
            max_records: Maximum number of sales to return (default 3)
            include_non_arms_length: If True, also search non-arms-length sales (default False)

        Returns:
            Dictionary with sales history and metadata:
            {
                'found': bool,
                'sale_count': int,
                'sales': [
                    {
                        'sale_date': 'YYYY-MM-DD',
                        'sale_price': int or None,
                        'verification_code': str,
                        'instrument_number': str,
                        'is_arms_length': bool,
                        'old_owner': str,
                        'new_owner': str
                    }
                ],
                'apn_input': str,
                'parid_lookup': str,
                'data_range': str,
                'source': str,
                'arms_length_only': bool,
                'error': str or None
            }
        """
        result = {
            'found': False,
            'sale_count': 0,
            'sales': [],
            'apn_input': apn,
            'parid_lookup': None,
            'data_range': None,
            'source': 'Loudoun County Commissioner of Revenue',
            'arms_length_only': not include_non_arms_length,
            'error': None,
        }

        # Check if data is loaded
        if not self.data_loaded:
            result['error'] = self.load_error or "Sales data not loaded"
            return result

        # Convert APN to PARID
        parid = self._convert_apn_to_parid(apn)
        result['parid_lookup'] = parid

        # Set data range
        if self.stats.get('date_range_start') and self.stats.get('date_range_end'):
            start_year = self.stats['date_range_start'][:4]
            end_year = self.stats['date_range_end'][:4]
            result['data_range'] = f"{start_year}-{end_year}"

        # Lookup in index
        sales = self.sales_index.get(parid, [])

        if not sales and include_non_arms_length:
            # Also check non-arms-length sales if requested
            non_arms_length_mask = ~self.df['SALE VERIFICATION'].isin(ARMS_LENGTH_CODES)
            non_arms_df = self.df[non_arms_length_mask]

            for _, row in non_arms_df.iterrows():
                row_parid = self._normalize_parid(str(row['PARID']))
                if row_parid == parid:
                    sale_record = {
                        'sale_date': row['RECORD DATE'],
                        'sale_price': row['PRICE'] if pd.notna(row['PRICE']) else None,
                        'verification_code': row['SALE VERIFICATION'],
                        'instrument_number': row.get('INSTRUMENT#', ''),
                        'is_arms_length': False,
                        'old_owner': row.get('OLD OWNER', ''),
                        'new_owner': row.get('NEW OWNER', ''),
                    }
                    sales.append(sale_record)

            # Sort by date
            sales.sort(
                key=lambda x: x['sale_date'] if pd.notna(x.get('sale_date')) else datetime.min,
                reverse=True
            )

        if not sales:
            return result

        # Limit to max_records
        sales = sales[:max_records]

        # Format sales for output
        formatted_sales = []
        for sale in sales:
            sale_date = sale['sale_date']
            if pd.notna(sale_date):
                if isinstance(sale_date, str):
                    date_str = sale_date
                else:
                    date_str = sale_date.strftime('%Y-%m-%d')
            else:
                date_str = None

            formatted_sale = {
                'sale_date': date_str,
                'sale_price': int(sale['sale_price']) if sale['sale_price'] and pd.notna(sale['sale_price']) else None,
                'verification_code': sale['verification_code'],
                'instrument_number': str(sale.get('instrument_number', '')),
                'is_arms_length': sale.get('verification_code') in ARMS_LENGTH_CODES,
                'old_owner': str(sale.get('old_owner', '')),
                'new_owner': str(sale.get('new_owner', '')),
            }
            formatted_sales.append(formatted_sale)

        result['found'] = True
        result['sale_count'] = len(formatted_sales)
        result['sales'] = formatted_sales

        return result

    def get_stats(self) -> Dict:
        """
        Get data quality statistics.

        Returns:
            Dictionary with loading statistics and data quality metrics
        """
        return {
            'loaded': self.data_loaded,
            'error': self.load_error,
            **self.stats
        }


# =============================================================================
# Unit Tests
# =============================================================================

def test_apn_conversion():
    """Test APN to PARID conversion."""
    sales = LoudounSalesData.__new__(LoudounSalesData)
    sales._convert_apn_to_parid = LoudounSalesData._convert_apn_to_parid.__get__(sales)

    # Test ATTOM format with dashes
    assert sales._convert_apn_to_parid("110-39-4004-000") == "110394004000"

    # Test already-clean format
    assert sales._convert_apn_to_parid("110394004000") == "110394004000"

    # Test with spaces
    assert sales._convert_apn_to_parid("110 39 4004 000") == "110394004000"

    # Test shorter format (should pad)
    assert sales._convert_apn_to_parid("123456") == "000000123456"

    print("✅ APN conversion tests passed")


def test_parid_normalization():
    """Test PARID normalization."""
    sales = LoudounSalesData.__new__(LoudounSalesData)
    sales._normalize_parid = LoudounSalesData._normalize_parid.__get__(sales)

    # Test standard format
    assert sales._normalize_parid("110394004000") == "110394004000"

    # Test with leading zeros needed
    assert sales._normalize_parid("1234567890") == "001234567890"

    # Test empty/invalid
    assert sales._normalize_parid("") is None
    assert sales._normalize_parid(None) is None

    print("✅ PARID normalization tests passed")


def test_arms_length_filtering():
    """Test that arms-length codes are correctly identified."""
    # Verify our code sets
    assert '1:MARKET SALE' in ARMS_LENGTH_CODES
    assert 'V:NEW CONSTRUCTION' in ARMS_LENGTH_CODES
    assert '3:NON-MARKET SALE' in NON_ARMS_LENGTH_CODES
    assert 'Z:FORECLOSURE' in NON_ARMS_LENGTH_CODES

    # No overlap between sets
    assert len(ARMS_LENGTH_CODES & NON_ARMS_LENGTH_CODES) == 0

    print("✅ Arms-length filtering tests passed")


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*50)
    print("Running LoudounSalesData Unit Tests")
    print("="*50 + "\n")

    test_apn_conversion()
    test_parid_normalization()
    test_arms_length_filtering()

    print("\n" + "="*50)
    print("All unit tests passed!")
    print("="*50)


# =============================================================================
# Integration Test with Real Data
# =============================================================================

if __name__ == '__main__':
    import sys

    # Run unit tests first
    run_all_tests()

    print("\n" + "="*60)
    print("Integration Test: Loading Real Sales Data")
    print("="*60 + "\n")

    # Initialize with real data
    sales_data = LoudounSalesData()

    # Check loading status
    stats = sales_data.get_stats()
    print("Data Loading Statistics:")
    print(f"  Loaded: {stats.get('loaded')}")
    if stats.get('error'):
        print(f"  Error: {stats.get('error')}")
        sys.exit(1)

    print(f"  Total records: {stats.get('total_records', 0):,}")
    print(f"  Arms-length records: {stats.get('arms_length_records', 0):,}")
    print(f"  Unique properties: {stats.get('unique_properties', 0):,}")
    print(f"  Date range: {stats.get('date_range_start')} to {stats.get('date_range_end')}")
    print(f"  Filtered out (non-arms-length): {stats.get('filtered_out', 0):,}")

    # Test lookup for 43422 Cloister Pl (APN: 110-39-4004-000)
    print("\n" + "="*60)
    print("Test Property: 43422 Cloister Pl, Leesburg")
    print("APN: 110-39-4004-000")
    print("="*60 + "\n")

    result = sales_data.get_sales_history("110-39-4004-000")

    print(f"Found: {result['found']}")
    print(f"PARID lookup: {result['parid_lookup']}")
    print(f"Data range: {result['data_range']}")
    print(f"Sale count: {result['sale_count']}")

    if result['found']:
        print("\nSales History (newest first):")
        for i, sale in enumerate(result['sales'], 1):
            print(f"\n  Sale #{i}:")
            print(f"    Date: {sale['sale_date']}")
            print(f"    Price: ${sale['sale_price']:,}" if sale['sale_price'] else "    Price: N/A")
            print(f"    Type: {sale['verification_code']}")
            print(f"    From: {sale['old_owner'][:40]}..." if len(sale['old_owner']) > 40 else f"    From: {sale['old_owner']}")
            print(f"    To: {sale['new_owner'][:40]}..." if len(sale['new_owner']) > 40 else f"    To: {sale['new_owner']}")
    else:
        print("\nNo arms-length sales found in 2020-2025 range.")
        print("This property may not have sold during this period.")

        # Try including non-arms-length sales
        print("\nChecking for any sales (including non-arms-length)...")
        result_all = sales_data.get_sales_history("110-39-4004-000", include_non_arms_length=True)
        if result_all['found']:
            print(f"Found {result_all['sale_count']} non-arms-length sale(s):")
            for sale in result_all['sales']:
                print(f"  - {sale['sale_date']}: ${sale['sale_price']:,} ({sale['verification_code']})"
                      if sale['sale_price'] else f"  - {sale['sale_date']}: N/A ({sale['verification_code']})")
        else:
            print("No sales found at all for this PARID.")

    print("\n" + "="*60)
    print("Integration test complete!")
    print("="*60)


# ============================================================================
# STREAMLIT CACHING - MULTI-COUNTY PATTERN
# ============================================================================
# Each county gets its own cached factory function for lazy loading.
# This pattern scales efficiently to multiple counties:
# - Memory: Only loads counties actually used (~30 MB per county)
# - Startup: Fast (loads on first use, not at app startup)
# - Performance: Instant after first load per county
#
# Adding new counties:
# 1. Create CountySalesData class (follow Loudoun pattern)
# 2. Add cached factory: get_cached_[county]_sales_data()
# 3. Use in orchestrator: self.sales_data = get_cached_[county]_sales_data()
# ============================================================================

try:
    import streamlit as st

    @st.cache_resource
    def get_cached_loudoun_sales_data() -> 'LoudounSalesData':
        """
        Get cached LoudounSalesData instance (lazy loading pattern).

        Caching Strategy:
        - Loads once per Streamlit session
        - Persists until server restart or manual cache clear
        - Subsequent property analyses use cached instance (instant)
        - Only loads when Loudoun data is actually needed

        Performance (from Part 1 conversion):
        - First load: ~2-3 seconds (Parquet read + indexing)
        - Cached loads: <0.01 seconds (memory access only)
        - File I/O speedup: 105x faster than Excel

        Multi-County Scaling:
        - Pattern: Each county has own cached function
        - Example: get_cached_athens_sales_data(), get_cached_clarke_sales_data()
        - Memory: ~30 MB per county (only loaded counties)
        - Total memory for 5 counties: ~150 MB

        Returns:
            Cached LoudounSalesData instance
        """
        print("Loading Loudoun County sales data (47K records)...")
        sales_data = LoudounSalesData()
        print("✓ Sales data loaded")
        return sales_data

except ImportError:
    # Streamlit not available (running outside of Streamlit app)
    def get_cached_loudoun_sales_data() -> 'LoudounSalesData':
        """Non-cached version for use outside Streamlit."""
        return LoudounSalesData()
