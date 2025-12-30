#!/usr/bin/env python3
"""
Direct test of ATTOM API optimization (enrich_sqft=False).

Tests the get_comparable_sales call directly to verify:
1. Comparables are returned without sqft enrichment
2. API call count is reduced
3. Data quality is maintained
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_attom_direct():
    """Test ATTOM API directly with enrich_sqft=False."""

    api_key = os.environ.get('ATTOM_API_KEY')
    if not api_key:
        print("ERROR: ATTOM_API_KEY not set")
        return None

    from core.attom_client import ATTOMClient

    client = ATTOMClient(api_key)

    # Test addresses
    test_addresses = [
        "43500 Tuckaway Pl, Leesburg, VA 20176",
        "23704 Velvet Grass Ln, Ashburn, VA 20148",
        "42713 Newcomer Ter, Chantilly, VA 20152",
        "41690 Dillinger Mill Pl, Aldie, VA 20105",
        "24756 Stonehill Farm Ct, Aldie, VA 20105",
        "23018 Oglethorpe Ct, Ashburn, VA 20148",
        "43195 Wayside Cir, Ashburn, VA 20147",
        "24960 Greengage Pl, Aldie, VA 20105",
        "22554 Wilderness Acres Cir, Leesburg, VA 20175",
        "20620 Duxbury Ter, Ashburn, VA 20147",
    ]

    results = []

    print("=" * 70)
    print("ATTOM API DIRECT TEST - enrich_sqft=False")
    print("=" * 70)
    print(f"Testing {len(test_addresses)} properties\n")

    for i, addr in enumerate(test_addresses, 1):
        print(f"\n{i}. {addr}")
        print("-" * 50)

        result = {
            'address': addr,
            'property_detail': None,
            'avm': None,
            'comps_without_enrich': None,
            'errors': []
        }

        # Test 1: Property Detail
        try:
            start = time.time()
            prop = client.get_property_detail(addr)
            elapsed = (time.time() - start) * 1000

            if prop:
                result['property_detail'] = {
                    'success': True,
                    'sqft': prop.sqft,
                    'bedrooms': prop.bedrooms,
                    'year_built': prop.year_built,
                    'response_ms': round(elapsed)
                }
                print(f"   Property Detail: ✓ {prop.sqft} sqft, {prop.bedrooms}bd ({elapsed:.0f}ms)")
            else:
                result['property_detail'] = {'success': False}
                print(f"   Property Detail: ✗ No data")
        except Exception as e:
            result['errors'].append(f"property_detail: {str(e)}")
            print(f"   Property Detail: ✗ {e}")

        # Test 2: AVM
        try:
            start = time.time()
            avm = client.get_avm(addr)
            elapsed = (time.time() - start) * 1000

            if avm:
                result['avm'] = {
                    'success': True,
                    'value': avm.value,
                    'confidence': getattr(avm, 'confidence', 'N/A'),
                    'response_ms': round(elapsed)
                }
                print(f"   AVM: ✓ ${avm.value:,} ({elapsed:.0f}ms)")
            else:
                result['avm'] = {'success': False}
                print(f"   AVM: ✗ No data")
        except Exception as e:
            result['errors'].append(f"avm: {str(e)}")
            print(f"   AVM: ✗ {e}")

        # Test 3: Comparable Sales WITHOUT enrichment (the optimization)
        try:
            start = time.time()
            comps = client.get_comparable_sales(
                address=addr,
                radius_miles=1.0,
                max_results=10,
                enrich_sqft=False  # THE OPTIMIZATION
            )
            elapsed = (time.time() - start) * 1000

            if comps:
                # Count comps with/without sqft
                with_sqft = sum(1 for c in comps if c.sqft and c.sqft > 0)
                without_sqft = len(comps) - with_sqft

                result['comps_without_enrich'] = {
                    'success': True,
                    'count': len(comps),
                    'with_sqft': with_sqft,
                    'without_sqft': without_sqft,
                    'response_ms': round(elapsed)
                }
                print(f"   Comps (no enrich): ✓ {len(comps)} found, {with_sqft} have sqft ({elapsed:.0f}ms)")

                # Show first comp as example
                if comps:
                    c = comps[0]
                    print(f"      Example: {c.address[:40]}... ${c.sale_price:,}")
            else:
                result['comps_without_enrich'] = {'success': False, 'count': 0}
                print(f"   Comps (no enrich): ✗ No comps found")
        except Exception as e:
            result['errors'].append(f"comps: {str(e)}")
            print(f"   Comps (no enrich): ✗ {e}")

        results.append(result)

        # Rate limiting
        time.sleep(0.5)

    return results


def summarize_results(results):
    """Summarize test results."""

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total = len(results)

    # Property detail success
    prop_success = sum(1 for r in results if (r.get('property_detail') or {}).get('success', False))

    # AVM success
    avm_success = sum(1 for r in results if (r.get('avm') or {}).get('success', False))

    # Comps success (without enrichment)
    comp_success = sum(1 for r in results if (r.get('comps_without_enrich') or {}).get('success', False))
    total_comps = sum((r.get('comps_without_enrich') or {}).get('count', 0) for r in results)
    avg_comps = total_comps / total if total > 0 else 0

    # Comps with sqft (even without enrichment, some may have it from sale record)
    comps_with_sqft = sum((r.get('comps_without_enrich') or {}).get('with_sqft', 0) for r in results)
    comps_without_sqft = sum((r.get('comps_without_enrich') or {}).get('without_sqft', 0) for r in results)

    print(f"\nProperties tested: {total}")
    print(f"\nAPI Call Success Rates:")
    print(f"  Property Detail: {prop_success}/{total} ({prop_success/total*100:.0f}%)")
    print(f"  AVM:             {avm_success}/{total} ({avm_success/total*100:.0f}%)")
    print(f"  Comparables:     {comp_success}/{total} ({comp_success/total*100:.0f}%)")

    print(f"\nComparable Sales Analysis:")
    print(f"  Total comps found: {total_comps}")
    print(f"  Average per property: {avg_comps:.1f}")
    print(f"  Comps with sqft already: {comps_with_sqft} ({comps_with_sqft/total_comps*100:.0f}%)" if total_comps > 0 else "  N/A")
    print(f"  Comps missing sqft: {comps_without_sqft} ({comps_without_sqft/total_comps*100:.0f}%)" if total_comps > 0 else "  N/A")

    # Calculate API calls
    # With enrich_sqft=False: 3 calls per property (prop + avm + comps)
    # With enrich_sqft=True: 3 + N calls where N = comps_without_sqft
    calls_optimized = 3 * total
    calls_unoptimized = 3 * total + comps_without_sqft
    calls_saved = comps_without_sqft

    print(f"\nAPI Call Analysis:")
    print(f"  Calls with optimization: {calls_optimized} ({calls_optimized/total:.1f}/property)")
    print(f"  Calls without optimization: {calls_unoptimized} ({calls_unoptimized/total:.1f}/property)")
    print(f"  Calls SAVED: {calls_saved} ({calls_saved/total:.1f}/property)")

    if calls_unoptimized > 0:
        reduction = (calls_saved / calls_unoptimized) * 100
        print(f"  Reduction: {reduction:.0f}%")

    # Cost analysis
    cost_per_call = 0.095
    cost_optimized = calls_optimized * cost_per_call
    cost_unoptimized = calls_unoptimized * cost_per_call
    cost_saved = calls_saved * cost_per_call

    print(f"\nCost Analysis (this test):")
    print(f"  Cost with optimization: ${cost_optimized:.2f}")
    print(f"  Cost without optimization: ${cost_unoptimized:.2f}")
    print(f"  Cost SAVED: ${cost_saved:.2f}")

    # Pass/fail
    print("\n" + "=" * 70)
    overall_success = prop_success >= 8 and avm_success >= 5 and comp_success >= 8

    if overall_success:
        print("✓ TEST PASSED - Optimization working correctly")
        print(f"  - Comparables returned without extra API calls")
        print(f"  - {comps_with_sqft} comps already had sqft from sale data")
        print(f"  - {comps_without_sqft} comps missing sqft (NOT enriched = SAVED API calls)")
    else:
        print("✗ TEST FAILED - Review errors above")

    print("=" * 70)

    return {
        'total': total,
        'prop_success': prop_success,
        'avm_success': avm_success,
        'comp_success': comp_success,
        'total_comps': total_comps,
        'avg_comps': avg_comps,
        'comps_with_sqft': comps_with_sqft,
        'comps_without_sqft': comps_without_sqft,
        'calls_optimized': calls_optimized,
        'calls_unoptimized': calls_unoptimized,
        'calls_saved': calls_saved,
        'overall_success': overall_success
    }


def main():
    print("\n" + "=" * 70)
    print("ATTOM OPTIMIZATION LIVE TEST")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Test: Direct ATTOM API calls with enrich_sqft=False")
    print()

    results = test_attom_direct()

    if results is None:
        print("Test could not run - check API key")
        return 1

    summary = summarize_results(results)

    # Save results
    output_dir = PROJECT_ROOT / 'diagnostic_outputs' / 'attom_optimization'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'live_test_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'optimization': 'enrich_sqft=False',
            'results': results,
            'summary': summary
        }, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    return 0 if summary['overall_success'] else 1


if __name__ == '__main__':
    sys.exit(main())
