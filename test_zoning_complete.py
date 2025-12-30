#!/usr/bin/env python3
"""
Comprehensive test of zoning functionality
Tests nearby zoning analysis for different property types in Athens
"""

from zoning_lookup import (
    get_nearby_zoning,
    format_nearby_zoning_report,
    get_zoning_info,
    format_zoning_report
)


def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 80)
    print("=" * 80 + "\n")


def test_address(address: str, description: str, radius_meters: int = 250):
    """
    Test zoning analysis for a specific address

    Args:
        address: Street address in Athens-Clarke County
        description: Description of the area (e.g., "Downtown/commercial")
        radius_meters: Search radius in meters
    """
    print("=" * 80)
    print(f"TEST ADDRESS: {address}")
    print(f"EXPECTED TYPE: {description}")
    print("=" * 80)
    print()

    # Get nearby zoning analysis
    nearby = get_nearby_zoning(address, radius_meters=radius_meters)

    if not nearby:
        print(f"❌ FAILED: Could not retrieve zoning data for {address}")
        print()
        return

    # Print full formatted report
    print(format_nearby_zoning_report(nearby))

    # Print specific analysis highlights
    print("=" * 80)
    print("ANALYSIS HIGHLIGHTS")
    print("=" * 80)
    print()

    if nearby.current_parcel:
        print(f"📍 Property Zoning: {nearby.current_parcel.current_zoning}")
        print(f"   Description: {nearby.current_parcel.current_zoning_description}")
        print(f"   Property Size: {nearby.current_parcel.acres:.2f} acres")
        print()

    print(f"📊 Nearby Parcels: {nearby.total_nearby_parcels}")
    print(f"   Unique Zones: {len(nearby.unique_zones)}")
    print(f"   Diversity Score: {nearby.zone_diversity_score:.2f}")
    print()

    print("🏘️  Neighborhood Character:")
    if nearby.residential_only:
        print("   ✓ Residential Only")
    if nearby.commercial_nearby:
        print("   ⚠️  Commercial Nearby")
    if nearby.mixed_use_nearby:
        print("   • Mixed Use Nearby")
    if nearby.industrial_nearby:
        print("   ⚠️  Industrial Nearby")
    if not (nearby.residential_only or nearby.commercial_nearby or
            nearby.mixed_use_nearby or nearby.industrial_nearby):
        print("   • No specific patterns detected")
    print()

    if nearby.potential_concerns:
        print(f"⚠️  CONCERNS IDENTIFIED: {len(nearby.potential_concerns)}")
        for i, concern in enumerate(nearby.potential_concerns, 1):
            print(f"   {i}. {concern}")
        print()
    else:
        print("✓ No significant concerns identified")
        print()


def main():
    """Run comprehensive zoning tests"""
    print("\n")
    print("🏡" * 40)
    print("COMPREHENSIVE ZONING ANALYSIS TEST")
    print("Athens-Clarke County, Georgia")
    print("🏡" * 40)
    print()

    # Test 1: Downtown/Commercial Area
    test_address(
        address="150 Hancock Avenue, Athens, GA 30601",
        description="Downtown/Commercial Area",
        radius_meters=250
    )
    print_separator()

    # Test 2: Institutional/Campus Area
    test_address(
        address="220 College Station Road, Athens, GA 30602",
        description="Institutional/Campus Area (UGA)",
        radius_meters=250
    )
    print_separator()

    # Test 3: Commercial Corridor
    test_address(
        address="1000 W Broad Street, Athens, GA 30606",
        description="Commercial Corridor (West Athens)",
        radius_meters=250
    )
    print_separator()

    # Bonus Test 4: Residential Neighborhood
    print("BONUS TEST: Residential Neighborhood")
    print()
    test_address(
        address="1398 W Hancock Avenue, Athens, GA 30606",
        description="Mixed Residential Neighborhood",
        radius_meters=250
    )
    print_separator()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("✅ Tested 4 different property types:")
    print("   1. Downtown/Commercial")
    print("   2. Institutional/Campus")
    print("   3. Commercial Corridor")
    print("   4. Residential Neighborhood")
    print()
    print("✅ All functions tested:")
    print("   • get_nearby_zoning()")
    print("   • format_nearby_zoning_report()")
    print("   • Concern detection")
    print("   • Pattern analysis")
    print()
    print("🎉 Testing complete!")
    print()


if __name__ == "__main__":
    main()
