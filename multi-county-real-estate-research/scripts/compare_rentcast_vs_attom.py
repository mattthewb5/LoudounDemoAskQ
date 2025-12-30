#!/usr/bin/env python3
"""
RentCast vs ATTOM API Comparison Script

This script compares property data and valuations between RentCast and ATTOM APIs
to determine if RentCast can replace or supplement ATTOM as a data source.

Usage:
    python scripts/compare_rentcast_vs_attom.py --test 5      # Test with 5 properties
    python scripts/compare_rentcast_vs_attom.py --limit 100   # Run full comparison
    python scripts/compare_rentcast_vs_attom.py --resume      # Resume from checkpoint

Outputs:
    - diagnostic_outputs/api_comparison/raw_results.json     # Complete API responses
    - diagnostic_outputs/api_comparison/comparison_metrics.csv  # Calculated metrics
    - diagnostic_outputs/api_comparison/summary_stats.json   # Summary statistics
"""

import sys
import os
import json
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.api_config import get_api_key
from core.attom_client import ATTOMClient, PropertyData, AVMResult
from core.rentcast_client import RentCastClient, RentEstimate

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / 'diagnostic_outputs' / 'api_comparison'
SAMPLE_FILE = OUTPUT_DIR / 'test_sample.csv'
RESULTS_FILE = OUTPUT_DIR / 'raw_results.json'
CHECKPOINT_FILE = OUTPUT_DIR / 'checkpoint.json'
METRICS_FILE = OUTPUT_DIR / 'comparison_metrics.csv'
SUMMARY_FILE = OUTPUT_DIR / 'summary_stats.json'

# Rate limiting (seconds between API calls)
RATE_LIMIT_DELAY = 0.5  # 500ms between calls


@dataclass
class ComparisonResult:
    """Result of comparing one property across both APIs."""
    sample_id: int
    address: str
    city: str
    latitude: float
    longitude: float

    # API call status
    rentcast_success: bool
    attom_property_success: bool
    attom_avm_success: bool

    # Timing
    rentcast_time_ms: float
    attom_property_time_ms: float
    attom_avm_time_ms: float

    # RentCast data
    rc_price_estimate: Optional[int] = None
    rc_price_low: Optional[int] = None
    rc_price_high: Optional[int] = None
    rc_bedrooms: Optional[int] = None
    rc_bathrooms: Optional[float] = None
    rc_sqft: Optional[int] = None
    rc_year_built: Optional[int] = None
    rc_property_type: Optional[str] = None
    rc_lot_size: Optional[int] = None

    # ATTOM data
    attom_avm_value: Optional[int] = None
    attom_avm_low: Optional[int] = None
    attom_avm_high: Optional[int] = None
    attom_avm_confidence: Optional[float] = None
    attom_avm_source: Optional[str] = None
    attom_bedrooms: Optional[int] = None
    attom_bathrooms: Optional[float] = None
    attom_sqft: Optional[int] = None
    attom_year_built: Optional[int] = None
    attom_property_type: Optional[str] = None
    attom_lot_size: Optional[int] = None
    attom_assessed_value: Optional[int] = None
    attom_market_value: Optional[int] = None
    attom_last_sale_price: Optional[int] = None
    attom_last_sale_date: Optional[str] = None

    # Calculated differences
    valuation_diff_pct: Optional[float] = None  # (RC - ATTOM) / ATTOM * 100
    beds_match: Optional[bool] = None
    baths_match: Optional[bool] = None
    sqft_diff_pct: Optional[float] = None
    year_built_match: Optional[bool] = None

    # Error messages
    rentcast_error: Optional[str] = None
    attom_error: Optional[str] = None

    # Timestamp
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class APIComparison:
    """Compare RentCast and ATTOM API data quality."""

    def __init__(self):
        """Initialize API clients."""
        # Load API keys
        attom_key = get_api_key('ATTOM_API_KEY')
        rentcast_key = get_api_key('RENTCAST_API_KEY')

        if not attom_key:
            raise ValueError("ATTOM_API_KEY not found in configuration")
        if not rentcast_key:
            raise ValueError("RENTCAST_API_KEY not found in configuration")

        self.attom = ATTOMClient(api_key=attom_key)
        self.rentcast = RentCastClient(api_key=rentcast_key)

        # Track API calls for cost estimation
        self.api_calls = {
            'rentcast_value': 0,
            'attom_property': 0,
            'attom_avm': 0
        }

        # Results storage
        self.results: List[ComparisonResult] = []

        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def load_sample(self) -> List[Dict]:
        """Load test sample from CSV."""
        if not SAMPLE_FILE.exists():
            raise FileNotFoundError(f"Sample file not found: {SAMPLE_FILE}")

        sample = []
        with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample.append(row)

        return sample

    def load_checkpoint(self) -> set:
        """Load processed sample IDs from checkpoint."""
        if not CHECKPOINT_FILE.exists():
            return set()

        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except (json.JSONDecodeError, KeyError):
            return set()

    def save_checkpoint(self, processed_ids: set):
        """Save checkpoint with processed sample IDs."""
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'processed_ids': list(processed_ids),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def call_rentcast(self, address: str) -> Tuple[Optional[RentEstimate], float, Optional[str]]:
        """
        Call RentCast API for property valuation.

        Returns:
            Tuple of (result, time_ms, error_message)
        """
        start = time.time()
        error = None
        result = None

        try:
            result = self.rentcast.get_value_estimate(address)
            self.api_calls['rentcast_value'] += 1
        except Exception as e:
            error = str(e)

        elapsed_ms = (time.time() - start) * 1000
        return result, elapsed_ms, error

    def call_attom_property(self, address: str) -> Tuple[Optional[PropertyData], float, Optional[str]]:
        """
        Call ATTOM API for property details.

        Returns:
            Tuple of (result, time_ms, error_message)
        """
        start = time.time()
        error = None
        result = None

        try:
            result = self.attom.get_property_detail(address)
            self.api_calls['attom_property'] += 1
        except Exception as e:
            error = str(e)

        elapsed_ms = (time.time() - start) * 1000
        return result, elapsed_ms, error

    def call_attom_avm(self, address: str) -> Tuple[Optional[AVMResult], float, Optional[str]]:
        """
        Call ATTOM API for AVM valuation.

        Returns:
            Tuple of (result, time_ms, error_message)
        """
        start = time.time()
        error = None
        result = None

        try:
            result = self.attom.get_avm(address)
            self.api_calls['attom_avm'] += 1
        except Exception as e:
            error = str(e)

        elapsed_ms = (time.time() - start) * 1000
        return result, elapsed_ms, error

    def compare_property(self, sample_row: Dict) -> ComparisonResult:
        """
        Compare a single property across both APIs.

        Args:
            sample_row: Dictionary with sample data (sample_id, full_address, city, latitude, longitude)

        Returns:
            ComparisonResult with all comparison data
        """
        sample_id = int(sample_row['sample_id'])
        address = sample_row['full_address']
        city = sample_row['city']
        lat = float(sample_row['latitude'])
        lon = float(sample_row['longitude'])

        # Call RentCast
        rc_result, rc_time, rc_error = self.call_rentcast(address)
        time.sleep(RATE_LIMIT_DELAY)

        # Call ATTOM property detail
        attom_prop, attom_prop_time, attom_prop_error = self.call_attom_property(address)
        time.sleep(RATE_LIMIT_DELAY)

        # Call ATTOM AVM
        attom_avm, attom_avm_time, attom_avm_error = self.call_attom_avm(address)
        time.sleep(RATE_LIMIT_DELAY)

        # Build result
        result = ComparisonResult(
            sample_id=sample_id,
            address=address,
            city=city,
            latitude=lat,
            longitude=lon,

            # Success flags
            rentcast_success=rc_result is not None,
            attom_property_success=attom_prop is not None,
            attom_avm_success=attom_avm is not None,

            # Timing
            rentcast_time_ms=rc_time,
            attom_property_time_ms=attom_prop_time,
            attom_avm_time_ms=attom_avm_time,

            # Errors
            rentcast_error=rc_error,
            attom_error=attom_prop_error or attom_avm_error
        )

        # Extract RentCast data
        if rc_result:
            result.rc_price_estimate = rc_result.price_estimate
            result.rc_price_low = rc_result.price_range_low
            result.rc_price_high = rc_result.price_range_high
            result.rc_bedrooms = rc_result.bedrooms
            result.rc_bathrooms = rc_result.bathrooms
            result.rc_sqft = rc_result.sqft
            result.rc_year_built = rc_result.year_built
            result.rc_property_type = rc_result.property_type
            result.rc_lot_size = rc_result.lot_size

        # Extract ATTOM property data
        if attom_prop:
            result.attom_bedrooms = attom_prop.bedrooms
            result.attom_bathrooms = attom_prop.bathrooms
            result.attom_sqft = attom_prop.sqft
            result.attom_year_built = attom_prop.year_built
            result.attom_property_type = attom_prop.property_type
            result.attom_lot_size = attom_prop.lot_size
            result.attom_assessed_value = attom_prop.assessed_value
            result.attom_market_value = attom_prop.market_value
            result.attom_last_sale_price = attom_prop.last_sale_price
            result.attom_last_sale_date = attom_prop.last_sale_date

        # Extract ATTOM AVM data
        if attom_avm:
            result.attom_avm_value = attom_avm.value
            result.attom_avm_low = attom_avm.value_low
            result.attom_avm_high = attom_avm.value_high
            result.attom_avm_confidence = attom_avm.confidence_score
            result.attom_avm_source = attom_avm.source

        # Calculate differences
        if result.rc_price_estimate and result.attom_avm_value:
            result.valuation_diff_pct = (
                (result.rc_price_estimate - result.attom_avm_value)
                / result.attom_avm_value * 100
            )

        if result.rc_bedrooms is not None and result.attom_bedrooms is not None:
            result.beds_match = result.rc_bedrooms == result.attom_bedrooms

        if result.rc_bathrooms is not None and result.attom_bathrooms is not None:
            result.baths_match = result.rc_bathrooms == result.attom_bathrooms

        if result.rc_sqft and result.attom_sqft:
            result.sqft_diff_pct = (
                (result.rc_sqft - result.attom_sqft) / result.attom_sqft * 100
            )

        if result.rc_year_built is not None and result.attom_year_built is not None:
            result.year_built_match = result.rc_year_built == result.attom_year_built

        return result

    def run_comparison(self, limit: Optional[int] = None, resume: bool = False) -> List[ComparisonResult]:
        """
        Run comparison on all sample properties.

        Args:
            limit: Maximum number of properties to process (None for all)
            resume: If True, resume from last checkpoint

        Returns:
            List of ComparisonResult objects
        """
        # Load sample
        sample = self.load_sample()
        total = len(sample)

        if limit:
            sample = sample[:limit]

        # Check for resume
        processed_ids = set()
        if resume:
            processed_ids = self.load_checkpoint()
            print(f"Resuming from checkpoint: {len(processed_ids)} already processed")

        # Load existing results if resuming
        if resume and RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    self.results = [
                        ComparisonResult(**r) for r in existing.get('results', [])
                    ]
            except (json.JSONDecodeError, TypeError):
                self.results = []

        # Process each property
        start_time = datetime.now()

        for i, row in enumerate(sample):
            sample_id = int(row['sample_id'])

            # Skip if already processed
            if sample_id in processed_ids:
                print(f"[{i+1}/{len(sample)}] Skipping #{sample_id} (already processed)")
                continue

            print(f"[{i+1}/{len(sample)}] Processing #{sample_id}: {row['full_address'][:50]}...")

            try:
                result = self.compare_property(row)
                self.results.append(result)
                processed_ids.add(sample_id)

                # Print status
                rc_status = "✓" if result.rentcast_success else "✗"
                attom_status = "✓" if result.attom_avm_success else "✗"

                val_diff = f"{result.valuation_diff_pct:+.1f}%" if result.valuation_diff_pct else "N/A"

                print(f"    RentCast: {rc_status} | ATTOM: {attom_status} | Diff: {val_diff}")

                # Save checkpoint after each property
                self.save_checkpoint(processed_ids)
                self.save_results()

            except Exception as e:
                print(f"    ERROR: {e}")

        elapsed = datetime.now() - start_time
        print(f"\n{'='*60}")
        print(f"Comparison complete: {len(self.results)} properties processed")
        print(f"Elapsed time: {elapsed}")
        print(f"API calls: {self.api_calls}")

        return self.results

    def save_results(self):
        """Save raw results to JSON."""
        data = {
            'run_date': datetime.now().isoformat(),
            'api_calls': self.api_calls,
            'total_results': len(self.results),
            'results': [asdict(r) for r in self.results]
        }

        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comparison metrics from results."""
        if not self.results:
            return {}

        metrics = {
            'total_properties': len(self.results),
            'run_date': datetime.now().isoformat(),
        }

        # Success rates
        rc_success = sum(1 for r in self.results if r.rentcast_success)
        attom_prop_success = sum(1 for r in self.results if r.attom_property_success)
        attom_avm_success = sum(1 for r in self.results if r.attom_avm_success)
        both_success = sum(1 for r in self.results if r.rentcast_success and r.attom_avm_success)

        metrics['success_rates'] = {
            'rentcast': rc_success / len(self.results) * 100,
            'attom_property': attom_prop_success / len(self.results) * 100,
            'attom_avm': attom_avm_success / len(self.results) * 100,
            'both_have_valuation': both_success / len(self.results) * 100
        }

        # Valuation comparison (only where both have data)
        val_diffs = [r.valuation_diff_pct for r in self.results if r.valuation_diff_pct is not None]

        if val_diffs:
            abs_diffs = [abs(d) for d in val_diffs]
            metrics['valuation_comparison'] = {
                'count_with_both': len(val_diffs),
                'mean_diff_pct': sum(val_diffs) / len(val_diffs),
                'mean_abs_diff_pct': sum(abs_diffs) / len(abs_diffs),
                'median_abs_diff_pct': sorted(abs_diffs)[len(abs_diffs)//2],
                'max_diff_pct': max(val_diffs),
                'min_diff_pct': min(val_diffs),
                'within_5_pct': sum(1 for d in abs_diffs if d <= 5) / len(abs_diffs) * 100,
                'within_10_pct': sum(1 for d in abs_diffs if d <= 10) / len(abs_diffs) * 100,
                'within_15_pct': sum(1 for d in abs_diffs if d <= 15) / len(abs_diffs) * 100,
                'over_20_pct': sum(1 for d in abs_diffs if d > 20) / len(abs_diffs) * 100,
            }

        # Property characteristics match rates
        beds_results = [r.beds_match for r in self.results if r.beds_match is not None]
        baths_results = [r.baths_match for r in self.results if r.baths_match is not None]
        year_results = [r.year_built_match for r in self.results if r.year_built_match is not None]
        sqft_diffs = [r.sqft_diff_pct for r in self.results if r.sqft_diff_pct is not None]

        metrics['characteristic_matches'] = {
            'bedrooms': {
                'count': len(beds_results),
                'match_rate': sum(beds_results) / len(beds_results) * 100 if beds_results else None
            },
            'bathrooms': {
                'count': len(baths_results),
                'match_rate': sum(baths_results) / len(baths_results) * 100 if baths_results else None
            },
            'year_built': {
                'count': len(year_results),
                'match_rate': sum(year_results) / len(year_results) * 100 if year_results else None
            },
            'sqft': {
                'count': len(sqft_diffs),
                'mean_diff_pct': sum(sqft_diffs) / len(sqft_diffs) if sqft_diffs else None,
                'within_5_pct': sum(1 for d in sqft_diffs if abs(d) <= 5) / len(sqft_diffs) * 100 if sqft_diffs else None
            }
        }

        # Response times
        rc_times = [r.rentcast_time_ms for r in self.results]
        attom_times = [r.attom_property_time_ms + r.attom_avm_time_ms for r in self.results]

        metrics['response_times_ms'] = {
            'rentcast_avg': sum(rc_times) / len(rc_times),
            'attom_total_avg': sum(attom_times) / len(attom_times),
        }

        # API call cost estimate
        metrics['api_calls'] = self.api_calls
        metrics['estimated_cost'] = {
            'rentcast': self.api_calls['rentcast_value'] * 0.03,  # ~$0.03 per call
            'attom': (self.api_calls['attom_property'] + self.api_calls['attom_avm']) * 0.10,  # ~$0.10 per call
            'total': self.api_calls['rentcast_value'] * 0.03 + (self.api_calls['attom_property'] + self.api_calls['attom_avm']) * 0.10
        }

        return metrics

    def save_metrics(self, metrics: Dict):
        """Save metrics to files."""
        # Save summary JSON
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

        # Save detailed CSV
        rows = []
        for r in self.results:
            rows.append(asdict(r))

        if rows:
            with open(METRICS_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        print(f"\nMetrics saved to:")
        print(f"  - {SUMMARY_FILE}")
        print(f"  - {METRICS_FILE}")

    def print_summary(self, metrics: Dict):
        """Print summary of comparison results."""
        print("\n" + "="*70)
        print("RENTCAST VS ATTOM COMPARISON SUMMARY")
        print("="*70)

        print(f"\nTotal Properties Tested: {metrics['total_properties']}")

        print("\n--- SUCCESS RATES ---")
        sr = metrics['success_rates']
        print(f"  RentCast API:        {sr['rentcast']:.1f}%")
        print(f"  ATTOM Property:      {sr['attom_property']:.1f}%")
        print(f"  ATTOM AVM:           {sr['attom_avm']:.1f}%")
        print(f"  Both Have Valuation: {sr['both_have_valuation']:.1f}%")

        if 'valuation_comparison' in metrics:
            print("\n--- VALUATION COMPARISON ---")
            vc = metrics['valuation_comparison']
            print(f"  Properties with both valuations: {vc['count_with_both']}")
            print(f"  Mean difference (RC - ATTOM):    {vc['mean_diff_pct']:+.1f}%")
            print(f"  Mean absolute difference:        {vc['mean_abs_diff_pct']:.1f}%")
            print(f"  Median absolute difference:      {vc['median_abs_diff_pct']:.1f}%")
            print(f"\n  Agreement levels:")
            print(f"    Within 5%:  {vc['within_5_pct']:.1f}%")
            print(f"    Within 10%: {vc['within_10_pct']:.1f}%")
            print(f"    Within 15%: {vc['within_15_pct']:.1f}%")
            print(f"    Over 20%:   {vc['over_20_pct']:.1f}%")

        print("\n--- CHARACTERISTIC MATCH RATES ---")
        cm = metrics['characteristic_matches']
        for field, data in cm.items():
            if data['count'] > 0:
                rate = data.get('match_rate') or data.get('within_5_pct')
                if rate is not None:
                    print(f"  {field.capitalize()}: {rate:.1f}% ({data['count']} comparisons)")

        print("\n--- ESTIMATED COST ---")
        ec = metrics['estimated_cost']
        print(f"  RentCast: ${ec['rentcast']:.2f}")
        print(f"  ATTOM:    ${ec['attom']:.2f}")
        print(f"  Total:    ${ec['total']:.2f}")

        print("\n" + "="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare RentCast and ATTOM API data quality'
    )
    parser.add_argument(
        '--test', type=int, metavar='N',
        help='Test mode: only process N properties'
    )
    parser.add_argument(
        '--limit', type=int, metavar='N',
        help='Limit to N properties'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--metrics-only', action='store_true',
        help='Only calculate metrics from existing results'
    )

    args = parser.parse_args()

    try:
        comparison = APIComparison()

        if args.metrics_only:
            # Load existing results
            if RESULTS_FILE.exists():
                with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    comparison.results = [
                        ComparisonResult(**r) for r in data.get('results', [])
                    ]
                print(f"Loaded {len(comparison.results)} existing results")
            else:
                print("No existing results found")
                return
        else:
            # Run comparison
            limit = args.test or args.limit
            comparison.run_comparison(limit=limit, resume=args.resume)

        # Calculate and save metrics
        metrics = comparison.calculate_metrics()
        comparison.save_metrics(metrics)
        comparison.print_summary(metrics)

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
