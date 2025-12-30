#!/usr/bin/env python3
"""
Test the redesigned zoning section with multiple property types.

Tests:
1. Plain English translations (zoning codes + place types)
2. Building permit characterization
3. Zone proximity analysis
4. Nearby zoning summary generation

Usage:
    python scripts/test_zoning_redesign.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loudoun_zoning_analysis import (
    get_plain_english_zoning,
    get_plain_english_placetype,
    characterize_building_permits,
    analyze_zone_proximity,
    get_nearby_zoning_summary,
    analyze_property_zoning_loudoun
)


def test_translations():
    """Test plain English translations."""
    print("=" * 80)
    print("TESTING PLAIN ENGLISH TRANSLATIONS")
    print("=" * 80)

    # Test zoning codes
    print("\nZONING CODES:")
    test_codes = ['PDH3', 'PDH4', 'GI', 'R-3', 'R-8', 'TC', 'AR-1', 'IP', 'RC']
    all_passed = True

    for code in test_codes:
        translation = get_plain_english_zoning(code)
        plain = translation.get('plain_english', 'FAILED')
        if plain and plain != f"Zoning: {code}":
            print(f"  ✓ {code:8} -> {plain}")
        else:
            print(f"  ✗ {code:8} -> TRANSLATION FAILED")
            all_passed = False

    # Test place types
    print("\n" + "-" * 80)
    print("\nPLACE TYPES:")
    test_places = ['SUBNBR', 'LJLMRN', 'RURNTH', 'URBTC', 'TOWN', 'SUBCMP', 'SUBMUS']

    for place in test_places:
        translation = get_plain_english_placetype(place)
        plain = translation.get('plain_english', 'FAILED')
        if plain and translation.get('success'):
            print(f"  ✓ {place:8} -> {plain}")
        else:
            print(f"  ✗ {place:8} -> TRANSLATION FAILED")
            all_passed = False

    return all_passed


def test_dynamic_r_series():
    """Test dynamic R-series translation."""
    print("\n" + "=" * 80)
    print("TESTING DYNAMIC R-SERIES TRANSLATION")
    print("=" * 80)

    # Note: R-1 uses singular "home" not "homes" (grammatically correct)
    test_cases = [
        ('R-1', ['1 home/acre', '1 homes/acre']),  # Accept either
        ('R-2', ['2 homes/acre']),
        ('R-3', ['3 homes/acre']),
        ('R-4', ['4 homes/acre']),
        ('R-8', ['8 homes/acre']),
        ('R-16', ['16 homes/acre']),
        ('R-24', ['24 homes/acre']),
    ]

    all_passed = True
    for code, expected_options in test_cases:
        result = get_plain_english_zoning(code)
        plain = result.get('plain_english', '')
        if any(exp in plain for exp in expected_options):
            print(f"  ✓ {code:6} -> {plain}")
        else:
            print(f"  ✗ {code:6} -> Expected one of {expected_options} in '{plain}'")
            all_passed = False

    return all_passed


def test_building_permits():
    """Test building permit characterization."""
    print("\n" + "=" * 80)
    print("TESTING BUILDING PERMIT CHARACTERIZATION")
    print("=" * 80)

    # Test property (River Creek area)
    lat, lon = 39.112492, -77.497378
    print(f"\nTest Location: {lat}, {lon}")

    permits = characterize_building_permits(lat, lon, radius_miles=2)

    if permits and permits.get('success'):
        print(f"\n  ✓ Total permits: {permits['total_permits']}")
        print(f"  ✓ Activity level: {permits.get('recent_activity', 'Unknown')}")
        print(f"  ✓ Permits by type: {permits.get('permits_by_type', {})}")
        return True
    else:
        print("  ✗ Building permits characterization failed")
        return False


def test_zone_proximity():
    """Test zone proximity analysis."""
    print("\n" + "=" * 80)
    print("TESTING ZONE PROXIMITY")
    print("=" * 80)

    # Test property (River Creek area)
    lat, lon = 39.112492, -77.497378
    print(f"\nTest Location: {lat}, {lon}")

    proximity = analyze_zone_proximity(lat, lon, radius_miles=5)

    if proximity:
        print(f"\n  ✓ Found {len(proximity)} zone types nearby:")
        for zone_code, info in list(proximity.items())[:5]:
            print(f"    - {zone_code}: {info['count']} areas "
                  f"(nearest {info['nearest_distance_miles']:.1f} mi)")
        return True
    else:
        print("  ✗ Zone proximity analysis returned no results")
        return False


def test_nearby_summary():
    """Test nearby zoning summary."""
    print("\n" + "=" * 80)
    print("TESTING NEARBY ZONING SUMMARY")
    print("=" * 80)

    lat, lon = 39.112492, -77.497378
    print(f"\nTest Location: {lat}, {lon}")

    summary = get_nearby_zoning_summary(lat, lon)
    if summary and "Nearby zoning" in summary:
        print("\n  ✓ Summary generated successfully:")
        for line in summary.split('\n')[:6]:
            print(f"    {line}")
        return True
    else:
        print("  ✗ Summary generation failed")
        return False


def test_full_analysis():
    """Test complete property analysis."""
    print("\n" + "=" * 80)
    print("TESTING FULL PROPERTY ANALYSIS")
    print("=" * 80)

    # Test property (River Creek area)
    lat, lon = 39.112492, -77.497378
    print(f"\nTest Location: {lat}, {lon}")

    result = analyze_property_zoning_loudoun(lat, lon)

    if result:
        print(f"\n  ✓ Jurisdiction: {result.get('jurisdiction')}")
        print(f"  ✓ Town Name: {result.get('town_name', 'None')}")

        zoning = result.get('current_zoning', {})
        print(f"  ✓ Zoning Code: {zoning.get('zoning')}")
        print(f"  ✓ Zoning Success: {zoning.get('success')}")

        place = result.get('place_type', {})
        print(f"  ✓ Place Type: {place.get('place_type')}")

        dev = result.get('development_probability', {})
        print(f"  ✓ Dev Score: {dev.get('score')}")
        print(f"  ✓ Risk Level: {dev.get('risk_level')}")

        return True
    else:
        print("  ✗ Full analysis failed")
        return False


def test_edge_cases():
    """Test edge case handling."""
    print("\n" + "=" * 80)
    print("TESTING EDGE CASES")
    print("=" * 80)

    # Test with invalid coordinates (should not crash)
    print("\n1. Testing invalid coordinates (0, 0):")
    try:
        result = analyze_property_zoning_loudoun(0, 0)
        if result:
            print("  ✓ Graceful handling - returned result (possibly with error)")
        else:
            print("  ✓ Graceful handling - returned None")
        passed = True
    except Exception as e:
        print(f"  ✗ Exception raised: {e}")
        passed = False

    # Test with coordinates outside Loudoun
    print("\n2. Testing coordinates far from Loudoun (NYC):")
    try:
        result = analyze_property_zoning_loudoun(40.7128, -74.0060)
        if result:
            print("  ✓ Graceful handling - returned result")
            print(f"      Zoning: {result.get('current_zoning', {}).get('zoning', 'N/A')}")
        else:
            print("  ✓ Graceful handling - returned None")
    except Exception as e:
        print(f"  ✗ Exception raised: {e}")
        passed = False

    return passed


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("ZONING REDESIGN TESTING SUITE")
    print("=" * 80)

    results = {}

    try:
        results['translations'] = test_translations()
        results['dynamic_r'] = test_dynamic_r_series()
        results['permits'] = test_building_permits()
        results['proximity'] = test_zone_proximity()
        results['summary'] = test_nearby_summary()
        results['full_analysis'] = test_full_analysis()
        results['edge_cases'] = test_edge_cases()

        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        all_passed = True
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {test_name}")
            if not passed:
                all_passed = False

        print("\n" + "=" * 80)
        if all_passed:
            print("✅ ALL TESTS PASSED")
        else:
            print("⚠️  SOME TESTS FAILED - Review output above")
        print("=" * 80)

        print("\nNext step: Manual testing in Streamlit app")
        print("  python -m streamlit run loudoun_streamlit_app.py")
        print("  Test address: 43422 Cloister Pl, Leesburg, VA 20176")

        sys.exit(0 if all_passed else 1)

    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
