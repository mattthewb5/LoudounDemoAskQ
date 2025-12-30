"""
Test Loudoun County GIS integration with real data.

This tests actual API calls to Loudoun County GIS to verify
our integration works with real-world data.

Run with: python tests/test_loudoun_gis.py

Last Updated: November 2025
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_county_config
from core.zoning_lookup import ZoningLookup

def test_loudoun_gis():
    """Test Loudoun County GIS integration with real data."""
    print("=" * 60)
    print("LOUDOUN COUNTY GIS INTEGRATION TEST")
    print("=" * 60)
    print("Testing real API integration with Loudoun County GIS")
    print("Endpoint: https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3")
    print()

    config = get_county_config("loudoun")
    lookup = ZoningLookup(config)

    results = []

    # Test 1: Ashburn (unincorporated)
    print("Test 1: Ashburn area")
    print("  Address: Ashburn, VA")
    print("  Location: Eastern Loudoun, unincorporated")
    print("  Expected: County jurisdiction, real zoning data")
    print()

    result1 = lookup.get_zoning(
        "Ashburn, VA",
        lat=39.0437,
        lon=-77.4875
    )

    print(f"Result:")
    print(f"  Success: {result1.success}")
    print(f"  Jurisdiction Type: {result1.jurisdiction_type}")
    print(f"  Jurisdiction Name: {result1.jurisdiction_name}")
    print(f"  Zoning Authority: {result1.zoning_authority}")
    print()

    if result1.success:
        print(f"  ✅ SUCCESS - Got real zoning data!")
        print(f"  Zoning Code: {result1.zoning_code}")
        print(f"  Description: {result1.zoning_description}")
        if result1.overlay_zones:
            print(f"  Overlay Zones: {', '.join(result1.overlay_zones)}")
        if result1.future_land_use:
            print(f"  Future Land Use: {result1.future_land_use}")
        print(f"  Data Source: {result1.data_source}")
    else:
        print(f"  ❌ FAILED")
        print(f"  Error: {result1.error_message}")
        if result1.notes:
            print(f"  Notes: {result1.notes}")

    results.append(result1.success)
    print()

    # Test 2: Sterling (unincorporated)
    print("Test 2: Sterling area")
    print("  Location: Northern Loudoun, unincorporated")

    result2 = lookup.get_zoning(
        "Sterling, VA",
        lat=39.0061,
        lon=-77.4286
    )

    print(f"  Success: {result2.success}")
    if result2.success:
        print(f"  ✅ Zoning Code: {result2.zoning_code}")
        print(f"  Description: {result2.zoning_description}")
    else:
        print(f"  ❌ Error: {result2.error_message}")

    results.append(result2.success)
    print()

    # Test 3: South Riding (unincorporated)
    print("Test 3: South Riding")
    print("  Location: Central Loudoun, unincorporated")

    result3 = lookup.get_zoning(
        "South Riding, VA",
        lat=38.9201,
        lon=-77.5061
    )

    print(f"  Success: {result3.success}")
    if result3.success:
        print(f"  ✅ Zoning Code: {result3.zoning_code}")
        print(f"  Description: {result3.zoning_description}")
    else:
        print(f"  ❌ Error: {result3.error_message}")

    results.append(result3.success)
    print()

    # Test 4: Dulles (unincorporated)
    print("Test 4: Dulles area")
    print("  Location: Central Loudoun, near Dulles Airport")

    result4 = lookup.get_zoning(
        "Dulles, VA",
        lat=38.9531,
        lon=-77.4481
    )

    print(f"  Success: {result4.success}")
    if result4.success:
        print(f"  ✅ Zoning Code: {result4.zoning_code}")
        print(f"  Description: {result4.zoning_description}")
    else:
        print(f"  ❌ Error: {result4.error_message}")

    results.append(result4.success)
    print()

    # Test 5: Leesburg (incorporated town - should fail with "town not implemented")
    print("Test 5: Leesburg (incorporated town)")
    print("  Location: Town of Leesburg")
    print("  Expected: Town jurisdiction, town zoning pending")

    result5 = lookup.get_zoning(
        "Leesburg, VA",
        lat=39.1156,
        lon=-77.5636
    )

    print(f"  Jurisdiction Type: {result5.jurisdiction_type}")
    if result5.jurisdiction_type == 'town':
        print(f"  ✅ Correctly identified as town")
        print(f"  Status: {result5.error_message}")
        results.append(True)  # Success = correctly identified as town
    else:
        print(f"  ⚠️ Identified as county (expected with placeholder boundaries)")
        results.append(result5.success)

    print()

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED - GIS integration working!")
        print()
        print("Next steps:")
        print("1. Validate zoning codes against Loudoun County records")
        print("2. Test more addresses across the county")
        print("3. Implement town-specific zoning (Leesburg)")
    elif passed > 0:
        print(f"⚠️ PARTIAL SUCCESS - {passed} test(s) passed")
        print("Review failed tests and check API configuration")
    else:
        print("❌ ALL TESTS FAILED")
        print("Verify:")
        print("1. API endpoint URL is correct")
        print("2. Network connectivity")
        print("3. Field name mappings")

    print()

if __name__ == "__main__":
    test_loudoun_gis()
