#!/usr/bin/env python3
"""
Test ATTOM optimization: enrich_sqft=False

Verifies the optimization is in place and documents expected savings.
Can be run with API keys to validate production behavior.
"""

import sys
import ast
import json
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def verify_optimization_in_code():
    """Verify the optimization is present in the orchestrator code."""
    orchestrator_path = PROJECT_ROOT / 'core' / 'property_valuation_orchestrator.py'

    with open(orchestrator_path, 'r') as f:
        content = f.read()

    # Check for the optimization
    if 'enrich_sqft=False' in content:
        return True, "enrich_sqft=False found in property_valuation_orchestrator.py"
    elif 'enrich_sqft=True' in content:
        return False, "enrich_sqft=True found - optimization NOT applied"
    else:
        return False, "enrich_sqft parameter not found - using default (True)"


def verify_attom_client_default():
    """Check the default value in attom_client.py."""
    client_path = PROJECT_ROOT / 'core' / 'attom_client.py'

    with open(client_path, 'r') as f:
        content = f.read()

    # Find get_comparable_sales signature
    if 'enrich_sqft=True' in content or 'enrich_sqft: bool = True' in content:
        return True, "Default is enrich_sqft=True (confirmed)"
    else:
        return None, "Could not determine default value"


def calculate_savings():
    """Calculate expected savings from the optimization."""

    # Cost assumptions
    COST_PER_CALL = 0.095

    # Before optimization (typical)
    calls_before = 8  # property + AVM + comps + ~5 enrichments
    cost_before = calls_before * COST_PER_CALL

    # After optimization
    calls_after = 3  # property + AVM + comps
    cost_after = calls_after * COST_PER_CALL

    # Savings
    calls_saved = calls_before - calls_after
    cost_saved = cost_before - cost_after
    reduction_pct = (calls_saved / calls_before) * 100

    return {
        'calls_before': calls_before,
        'calls_after': calls_after,
        'calls_saved': calls_saved,
        'cost_before': cost_before,
        'cost_after': cost_after,
        'cost_saved_per_property': cost_saved,
        'reduction_percent': reduction_pct,
        'annual_savings_1k_month': cost_saved * 1000 * 12,
        'annual_savings_5k_month': cost_saved * 5000 * 12,
    }


def run_live_test(num_properties: int = 5):
    """
    Run live test with actual API calls.
    Requires ATTOM_API_KEY environment variable.
    """
    import os

    api_key = os.environ.get('ATTOM_API_KEY')
    if not api_key:
        return None, "ATTOM_API_KEY not set - skipping live test"

    # Add project to path
    sys.path.insert(0, str(PROJECT_ROOT))

    try:
        from core.property_valuation_orchestrator import PropertyValuationOrchestrator

        # Test addresses
        test_addresses = [
            "43500 Tuckaway Pl, Leesburg, VA 20176",
            "23704 Velvet Grass Ln, Ashburn, VA 20148",
            "42713 Newcomer Ter, Chantilly, VA 20152",
            "41690 Dillinger Mill Pl, Aldie, VA 20105",
            "24756 Stonehill Farm Ct, Aldie, VA 20105",
        ][:num_properties]

        orchestrator = PropertyValuationOrchestrator()
        results = []

        for i, addr in enumerate(test_addresses, 1):
            print(f"\n{i}. Testing: {addr[:50]}...")
            try:
                result = orchestrator.analyze_property(addr)
                has_value = result.get('valuation', {}).get('estimate') is not None
                comp_count = len(result.get('valuation', {}).get('comparables', []))

                results.append({
                    'address': addr,
                    'success': True,
                    'has_valuation': has_value,
                    'comp_count': comp_count
                })
                print(f"   ✓ Valuation: {has_value}, Comps: {comp_count}")

            except Exception as e:
                results.append({
                    'address': addr,
                    'success': False,
                    'error': str(e)
                })
                print(f"   ✗ Error: {e}")

        return results, f"Tested {len(results)} properties"

    except ImportError as e:
        return None, f"Import error: {e}"


def main():
    print("=" * 70)
    print("ATTOM OPTIMIZATION VERIFICATION")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Project: {PROJECT_ROOT}")
    print()

    # Check 1: Verify optimization in orchestrator
    print("CHECK 1: Optimization in property_valuation_orchestrator.py")
    print("-" * 70)
    success, message = verify_optimization_in_code()
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {message}")

    # Check 2: Verify default in attom_client
    print("\nCHECK 2: Default value in attom_client.py")
    print("-" * 70)
    result, message = verify_attom_client_default()
    status = "✓ INFO" if result else "? UNKNOWN"
    print(f"  {status}: {message}")

    # Check 3: Calculate savings
    print("\nCHECK 3: Expected Savings Calculation")
    print("-" * 70)
    savings = calculate_savings()
    print(f"  API calls per property: {savings['calls_before']} → {savings['calls_after']}")
    print(f"  Reduction: {savings['reduction_percent']:.0f}%")
    print(f"  Cost per property: ${savings['cost_before']:.3f} → ${savings['cost_after']:.3f}")
    print(f"  Savings per property: ${savings['cost_saved_per_property']:.3f}")
    print(f"  Annual savings (1K/month): ${savings['annual_savings_1k_month']:,.0f}")
    print(f"  Annual savings (5K/month): ${savings['annual_savings_5k_month']:,.0f}")

    # Check 4: Live test (if API key available)
    print("\nCHECK 4: Live API Test")
    print("-" * 70)
    results, message = run_live_test(5)
    if results is None:
        print(f"  ⚠ SKIPPED: {message}")
        print("  Set ATTOM_API_KEY environment variable to run live tests")
    else:
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"  Tested: {len(results)} properties")
        print(f"  Successful: {success_count}")
        print(f"  {message}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if success:
        print("✓ Optimization is IN PLACE")
        print(f"  - enrich_sqft=False set in orchestrator")
        print(f"  - Expected {savings['reduction_percent']:.0f}% reduction in API calls")
        print(f"  - Estimated savings: ${savings['annual_savings_1k_month']:,.0f}/year (at 1K props/month)")
    else:
        print("✗ Optimization NOT FOUND")
        print("  - Check property_valuation_orchestrator.py")
        print("  - Ensure enrich_sqft=False is set")

    print("=" * 70)

    # Save results
    output_dir = PROJECT_ROOT / 'diagnostic_outputs' / 'attom_optimization'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'optimization_verification.json'
    with open(output_file, 'w') as f:
        json.dump({
            'verification_date': datetime.now().isoformat(),
            'optimization_present': success,
            'savings_calculation': savings,
            'live_test_results': results if results else 'skipped'
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
