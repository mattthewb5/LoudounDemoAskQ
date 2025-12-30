#!/usr/bin/env python3
"""
Test suite for county configuration system.

Tests:
- County registry functionality
- Helper functions
- Athens and Loudoun configurations
- Multi-jurisdiction features
- Validation capabilities

Run: python tests/test_config.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CountyConfig,
    SUPPORTED_COUNTIES,
    get_county_config,
    get_all_counties,
    get_production_counties,
    get_primary_county,
    get_counties_with_feature,
    can_validate_county,
    get_county_display_name,
    get_counties_by_state,
    get_multi_jurisdiction_counties,
    ATHENS_CLARKE_CONFIG,
    LOUDOUN_CONFIG
)


def test_county_registry():
    """Test that county registry is properly populated."""
    print("Testing county registry...")

    assert "athens_clarke" in SUPPORTED_COUNTIES, "Athens not in registry"
    assert "loudoun" in SUPPORTED_COUNTIES, "Loudoun not in registry"
    assert len(SUPPORTED_COUNTIES) == 2, f"Expected 2 counties, got {len(SUPPORTED_COUNTIES)}"

    print("  ✓ Registry has 2 counties: athens_clarke, loudoun")


def test_get_county_config():
    """Test getting county configurations."""
    print("\nTesting get_county_config()...")

    athens = get_county_config("athens_clarke")
    assert athens is not None, "Athens config is None"
    assert isinstance(athens, CountyConfig), "Athens config is not CountyConfig"
    assert athens.county_name == "athens_clarke", f"Expected 'athens_clarke', got '{athens.county_name}'"

    loudoun = get_county_config("loudoun")
    assert loudoun is not None, "Loudoun config is None"
    assert isinstance(loudoun, CountyConfig), "Loudoun config is not CountyConfig"
    assert loudoun.county_name == "loudoun", f"Expected 'loudoun', got '{loudoun.county_name}'"

    # Test non-existent county
    fake = get_county_config("fake_county")
    assert fake is None, "Non-existent county should return None"

    print("  ✓ Can retrieve Athens and Loudoun configs")
    print("  ✓ Non-existent county returns None")


def test_athens_config():
    """Test Athens-Clarke County configuration."""
    print("\nTesting Athens-Clarke County configuration...")

    athens = ATHENS_CLARKE_CONFIG

    # Identity
    assert athens.county_name == "athens_clarke"
    assert athens.state == "GA"
    assert athens.display_name == "Athens-Clarke County"
    assert athens.is_production_ready == True, "Athens should be production-ready"
    assert athens.is_primary_county == False, "Athens should not be primary county"

    # Features
    assert athens.has_school_data == True, "Athens should have school data"
    assert athens.has_crime_data == True, "Athens should have crime data"
    assert athens.has_zoning_data == True, "Athens should have zoning data"

    # Jurisdiction
    assert athens.has_incorporated_towns == False, "Athens has no incorporated towns"
    assert athens.get_jurisdiction_count() == 1, "Athens should have 1 jurisdiction"

    # Validation
    assert athens.can_validate_locally == False, "Athens cannot be validated locally"

    print("  ✓ Athens identity correct (GA, production-ready)")
    print("  ✓ Athens has all three data types")
    print("  ✓ Athens is single jurisdiction")


def test_loudoun_config():
    """Test Loudoun County configuration."""
    print("\nTesting Loudoun County configuration...")

    loudoun = LOUDOUN_CONFIG

    # Identity
    assert loudoun.county_name == "loudoun"
    assert loudoun.state == "VA"
    assert loudoun.display_name == "Loudoun County"
    assert loudoun.is_production_ready == False, "Loudoun should not be production-ready yet"
    assert loudoun.is_primary_county == True, "Loudoun should be primary county"

    # Features
    assert loudoun.has_school_data == False, "Loudoun school data not implemented yet"
    assert loudoun.has_crime_data == False, "Loudoun crime data not implemented yet"
    assert loudoun.has_zoning_data == True, "Loudoun zoning data implemented (Phase 1 complete!)"

    # Jurisdiction
    assert loudoun.has_incorporated_towns == True, "Loudoun has incorporated towns"
    assert len(loudoun.incorporated_towns) == 7, f"Expected 7 towns, got {len(loudoun.incorporated_towns)}"

    expected_towns = ["Leesburg", "Purcellville", "Middleburg", "Hamilton", "Lovettsville", "Round Hill", "Hillsboro"]
    for town in expected_towns:
        assert town in loudoun.incorporated_towns, f"{town} should be in incorporated towns"

    assert loudoun.get_jurisdiction_count() == 8, "Loudoun should have 8 jurisdictions (1 county + 7 towns)"

    # Validation
    assert loudoun.can_validate_locally == True, "Loudoun can be validated locally"

    print("  ✓ Loudoun identity correct (VA, primary county)")
    print("  ✓ Loudoun has 7 incorporated towns")
    print("  ✓ Loudoun can be validated locally")


def test_get_all_counties():
    """Test getting all county names."""
    print("\nTesting get_all_counties()...")

    counties = get_all_counties()
    assert len(counties) == 2, f"Expected 2 counties, got {len(counties)}"
    assert "athens_clarke" in counties, "Athens not in county list"
    assert "loudoun" in counties, "Loudoun not in county list"

    print(f"  ✓ All counties: {counties}")


def test_get_production_counties():
    """Test getting production-ready counties."""
    print("\nTesting get_production_counties()...")

    prod = get_production_counties()
    assert len(prod) == 1, f"Expected 1 production county, got {len(prod)}"
    assert "athens_clarke" in prod, "Athens should be production-ready"
    assert "loudoun" not in prod, "Loudoun should not be production-ready"

    print(f"  ✓ Production counties: {prod}")


def test_get_primary_county():
    """Test getting primary county."""
    print("\nTesting get_primary_county()...")

    primary = get_primary_county()
    assert primary == "loudoun", f"Expected 'loudoun', got '{primary}'"

    print(f"  ✓ Primary county: {primary}")


def test_get_counties_with_feature():
    """Test getting counties by feature."""
    print("\nTesting get_counties_with_feature()...")

    # Athens has all features, Loudoun has zoning only
    with_schools = get_counties_with_feature('school')
    assert "athens_clarke" in with_schools, "Athens should have school data"
    assert "loudoun" not in with_schools, "Loudoun should not have school data yet"

    with_crime = get_counties_with_feature('crime')
    assert "athens_clarke" in with_crime, "Athens should have crime data"
    assert "loudoun" not in with_crime, "Loudoun should not have crime data yet"

    with_zoning = get_counties_with_feature('zoning')
    assert "athens_clarke" in with_zoning, "Athens should have zoning data"
    assert "loudoun" in with_zoning, "Loudoun should have zoning data (Phase 1 complete!)"

    print(f"  ✓ Counties with schools: {with_schools}")
    print(f"  ✓ Counties with crime: {with_crime}")
    print(f"  ✓ Counties with zoning: {with_zoning}")


def test_can_validate_county():
    """Test validation capability check."""
    print("\nTesting can_validate_county()...")

    assert can_validate_county("loudoun") == True, "Loudoun should be validatable"
    assert can_validate_county("athens_clarke") == False, "Athens should not be validatable"
    assert can_validate_county("fake_county") == False, "Fake county should not be validatable"

    print("  ✓ Loudoun can be validated locally")
    print("  ✓ Athens cannot be validated locally")


def test_get_county_display_name():
    """Test display name retrieval."""
    print("\nTesting get_county_display_name()...")

    athens_name = get_county_display_name("athens_clarke")
    assert athens_name == "Athens-Clarke County", f"Expected 'Athens-Clarke County', got '{athens_name}'"

    loudoun_name = get_county_display_name("loudoun")
    assert loudoun_name == "Loudoun County", f"Expected 'Loudoun County', got '{loudoun_name}'"

    fake_name = get_county_display_name("fake_county")
    assert fake_name is None, "Fake county should return None"

    print(f"  ✓ Athens display name: {athens_name}")
    print(f"  ✓ Loudoun display name: {loudoun_name}")


def test_get_counties_by_state():
    """Test getting counties by state."""
    print("\nTesting get_counties_by_state()...")

    ga_counties = get_counties_by_state("GA")
    assert len(ga_counties) == 1, f"Expected 1 GA county, got {len(ga_counties)}"
    assert "athens_clarke" in ga_counties, "Athens should be in GA"

    va_counties = get_counties_by_state("VA")
    assert len(va_counties) == 1, f"Expected 1 VA county, got {len(va_counties)}"
    assert "loudoun" in va_counties, "Loudoun should be in VA"

    nc_counties = get_counties_by_state("NC")
    assert len(nc_counties) == 0, "No NC counties should exist"

    print(f"  ✓ GA counties: {ga_counties}")
    print(f"  ✓ VA counties: {va_counties}")


def test_get_multi_jurisdiction_counties():
    """Test getting multi-jurisdiction counties."""
    print("\nTesting get_multi_jurisdiction_counties()...")

    multi = get_multi_jurisdiction_counties()
    assert len(multi) == 1, f"Expected 1 multi-jurisdiction county, got {len(multi)}"
    assert "loudoun" in multi, "Loudoun should be multi-jurisdiction"
    assert "athens_clarke" not in multi, "Athens should not be multi-jurisdiction"

    print(f"  ✓ Multi-jurisdiction counties: {multi}")


def test_jurisdiction_detection():
    """Test jurisdiction detection methods."""
    print("\nTesting jurisdiction detection methods...")

    loudoun = LOUDOUN_CONFIG

    # Test is_town_incorporated
    assert loudoun.is_town_incorporated("Leesburg") == True, "Leesburg should be incorporated"
    assert loudoun.is_town_incorporated("Purcellville") == True, "Purcellville should be incorporated"
    assert loudoun.is_town_incorporated("Ashburn") == False, "Ashburn should not be incorporated"
    assert loudoun.is_town_incorporated("Sterling") == False, "Sterling should not be incorporated"

    # Test get_zoning_authority
    leesburg_auth = loudoun.get_zoning_authority(is_in_town=True, town_name="Leesburg")
    assert leesburg_auth == "Town of Leesburg", f"Expected 'Town of Leesburg', got '{leesburg_auth}'"

    county_auth = loudoun.get_zoning_authority(is_in_town=False)
    assert county_auth == "Loudoun County", f"Expected 'Loudoun County', got '{county_auth}'"

    print("  ✓ Town incorporation detection works")
    print("  ✓ Zoning authority determination works")


def test_data_update_frequencies():
    """Test data update frequency configuration."""
    print("\nTesting data update frequencies...")

    athens = ATHENS_CLARKE_CONFIG
    assert athens.data_update_frequency['schools'] == 'annually', "Athens schools should update annually"
    assert athens.data_update_frequency['crime'] == 'weekly', "Athens crime should update weekly"
    assert athens.data_update_frequency['zoning'] == 'as_amended', "Athens zoning updates as amended"

    loudoun = LOUDOUN_CONFIG
    assert loudoun.data_update_frequency['schools'] == 'annually', "Loudoun schools should update annually"
    assert loudoun.data_update_frequency['crime'] == 'nightly', "Loudoun crime should update nightly"
    assert loudoun.data_update_frequency['zoning'] == 'hourly', "Loudoun zoning should update hourly"

    print("  ✓ Athens update frequencies: annually/weekly/as_amended")
    print("  ✓ Loudoun update frequencies: annually/nightly/hourly")


def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("COUNTY CONFIGURATION SYSTEM TEST SUITE")
    print("=" * 60)

    test_functions = [
        test_county_registry,
        test_get_county_config,
        test_athens_config,
        test_loudoun_config,
        test_get_all_counties,
        test_get_production_counties,
        test_get_primary_county,
        test_get_counties_with_feature,
        test_can_validate_county,
        test_get_county_display_name,
        test_get_counties_by_state,
        test_get_multi_jurisdiction_counties,
        test_jurisdiction_detection,
        test_data_update_frequencies,
    ]

    failed = []

    for test_func in test_functions:
        try:
            test_func()
        except AssertionError as e:
            print(f"\n  ✗ FAILED: {e}")
            failed.append((test_func.__name__, str(e)))
        except Exception as e:
            print(f"\n  ✗ ERROR: {e}")
            failed.append((test_func.__name__, str(e)))

    print("\n" + "=" * 60)
    if failed:
        print(f"TESTS FAILED: {len(failed)} failures")
        for name, error in failed:
            print(f"  - {name}: {error}")
        print("=" * 60)
        return False
    else:
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
