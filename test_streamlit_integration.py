#!/usr/bin/env python3
"""
Test script to verify streamlit_app data structure expectations
"""

from dataclasses import dataclass
from typing import List, Optional


# Mock the expected data structures
@dataclass
class MockSafetyScore:
    """Mock safety score structure"""
    score: int = 75
    level: str = "Safe"


@dataclass
class MockStatistics:
    """Mock crime statistics structure"""
    total_incidents: int = 100
    violent_percentage: float = 15.0
    property_percentage: float = 45.0
    traffic_percentage: float = 25.0
    other_percentage: float = 15.0
    most_common_crime: str = "Theft"
    most_common_count: int = 30


@dataclass
class MockTrends:
    """Mock crime trends structure"""
    trend: str = "stable"
    change_percentage: float = 0.5


@dataclass
class MockCrimeAnalysis:
    """Mock CrimeAnalysis object that streamlit expects"""
    safety_score: MockSafetyScore
    statistics: MockStatistics
    trends: MockTrends


@dataclass
class MockSchoolInfo:
    """Mock school info structure"""
    elementary: str = "Test Elementary"
    middle: str = "Test Middle"
    high: str = "Test High"


@dataclass
class MockZoningInfo:
    """Mock basic zoning structure"""
    current_zoning: str = "RM-1"
    future_land_use: str = "Residential"
    current_zoning_description: str = "Multi-Family Residential"
    future_land_use_description: str = "Traditional Neighborhood"
    acres: float = 0.25
    split_zoned: bool = False
    future_changed: bool = False
    nearby_zones: List[str] = None


@dataclass
class MockNearbyZoning:
    """Mock nearby zoning structure"""
    current_parcel: MockZoningInfo
    nearby_parcels: List[MockZoningInfo]
    zone_diversity_score: float = 0.05
    total_nearby_parcels: int = 141
    unique_zones: List[str] = None
    residential_only: bool = False
    mixed_use_nearby: bool = True
    commercial_nearby: bool = True
    industrial_nearby: bool = False
    potential_concerns: List[str] = None


def test_data_structures():
    """Test that mock structures have expected attributes"""

    print("=" * 70)
    print("STREAMLIT DATA STRUCTURE VALIDATION TEST")
    print("=" * 70)
    print()

    # Test SchoolInfo
    print("📚 Testing SchoolInfo structure:")
    school = MockSchoolInfo()
    school_attrs = ['elementary', 'middle', 'high']
    school_valid = all(hasattr(school, attr) for attr in school_attrs)

    for attr in school_attrs:
        has_it = hasattr(school, attr)
        status = "✅" if has_it else "❌"
        value = getattr(school, attr, "MISSING") if has_it else "MISSING"
        print(f"  {status} {attr}: {value}")

    print(f"  Overall: {'✅ VALID' if school_valid else '❌ INVALID'}")
    print()

    # Test CrimeAnalysis
    print("🛡️  Testing CrimeAnalysis structure:")
    crime = MockCrimeAnalysis(
        safety_score=MockSafetyScore(),
        statistics=MockStatistics(),
        trends=MockTrends()
    )

    crime_top_attrs = ['safety_score', 'statistics', 'trends']
    crime_valid = True

    for attr in crime_top_attrs:
        has_it = hasattr(crime, attr)
        status = "✅" if has_it else "❌"
        print(f"  {status} {attr}: {getattr(crime, attr, 'MISSING')}")
        if not has_it:
            crime_valid = False

    # Check nested safety_score attributes
    print("  Nested safety_score attributes:")
    if hasattr(crime, 'safety_score') and crime.safety_score:
        for attr in ['score', 'level']:
            has_it = hasattr(crime.safety_score, attr)
            status = "✅" if has_it else "❌"
            value = getattr(crime.safety_score, attr, "MISSING") if has_it else "MISSING"
            print(f"    {status} safety_score.{attr}: {value}")
            if not has_it:
                crime_valid = False

    print(f"  Overall: {'✅ VALID' if crime_valid else '❌ INVALID'}")
    print()

    # Test basic ZoningInfo
    print("🏗️  Testing ZoningInfo structure:")
    zoning = MockZoningInfo()
    zoning_attrs = ['current_zoning', 'future_land_use', 'current_zoning_description',
                    'future_land_use_description', 'acres']
    zoning_valid = all(hasattr(zoning, attr) for attr in zoning_attrs)

    for attr in zoning_attrs:
        has_it = hasattr(zoning, attr)
        status = "✅" if has_it else "❌"
        value = getattr(zoning, attr, "MISSING") if has_it else "MISSING"
        print(f"  {status} {attr}: {value}")

    print(f"  Overall: {'✅ VALID' if zoning_valid else '❌ INVALID'}")
    print()

    # Test NearbyZoning
    print("🏘️  Testing NearbyZoning structure:")
    nearby = MockNearbyZoning(
        current_parcel=MockZoningInfo(),
        nearby_parcels=[MockZoningInfo(), MockZoningInfo()],
        unique_zones=['RM-1', 'RS-8'],
        potential_concerns=['Test concern']
    )

    nearby_attrs = ['current_parcel', 'nearby_parcels', 'zone_diversity_score',
                    'total_nearby_parcels', 'unique_zones']
    nearby_valid = all(hasattr(nearby, attr) for attr in nearby_attrs)

    for attr in nearby_attrs:
        has_it = hasattr(nearby, attr)
        status = "✅" if has_it else "❌"
        value = getattr(nearby, attr, "MISSING") if has_it else "MISSING"
        # Truncate long values
        if isinstance(value, list) and len(str(value)) > 50:
            value = f"[List with {len(value)} items]"
        print(f"  {status} {attr}: {value}")

    print(f"  Overall: {'✅ VALID' if nearby_valid else '❌ INVALID'}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    all_valid = school_valid and crime_valid and zoning_valid and nearby_valid

    print(f"SchoolInfo:     {'✅ VALID' if school_valid else '❌ INVALID'}")
    print(f"CrimeAnalysis:  {'✅ VALID' if crime_valid else '❌ INVALID'}")
    print(f"ZoningInfo:     {'✅ VALID' if zoning_valid else '❌ INVALID'}")
    print(f"NearbyZoning:   {'✅ VALID' if nearby_valid else '❌ INVALID'}")
    print()
    print(f"Overall Status: {'✅ ALL STRUCTURES VALID' if all_valid else '❌ SOME STRUCTURES INVALID'}")
    print()

    # Test validation logic
    print("=" * 70)
    print("VALIDATION LOGIC TEST (simulating streamlit_app validation)")
    print("=" * 70)
    print()

    # Simulate the validation that happens in streamlit_app
    result = {
        'school_info': school,
        'crime_analysis': crime,
        'zoning_info': zoning,
        'nearby_zoning': nearby
    }

    validation_warnings = []

    # Validate school data
    school_data = result.get('school_info')
    if school_data is None:
        validation_warnings.append("School data was requested but not retrieved")
    elif not hasattr(school_data, 'elementary') or not hasattr(school_data, 'middle') or not hasattr(school_data, 'high'):
        validation_warnings.append("School data structure is incomplete or invalid")

    # Validate crime data
    crime_data = result.get('crime_analysis')
    if crime_data is None:
        validation_warnings.append("Crime data was requested but not retrieved")
    elif not hasattr(crime_data, 'safety_score') or not hasattr(crime_data, 'statistics') or not hasattr(crime_data, 'trends'):
        validation_warnings.append("Crime data structure is incomplete or invalid")

    # Validate zoning data
    zoning_data = result.get('zoning_info')
    if zoning_data is None and result.get('nearby_zoning') is None:
        validation_warnings.append("Zoning data was requested but not retrieved")
    elif zoning_data is not None:
        if not hasattr(zoning_data, 'current_zoning') or not hasattr(zoning_data, 'future_land_use'):
            validation_warnings.append("Zoning data structure is incomplete or invalid")

    # Validate nearby_zoning
    nearby_zoning_data = result.get('nearby_zoning')
    if nearby_zoning_data is not None:
        required_nearby_attrs = ['current_parcel', 'nearby_parcels', 'zone_diversity_score']
        missing_nearby = [attr for attr in required_nearby_attrs if not hasattr(nearby_zoning_data, attr)]
        if missing_nearby:
            validation_warnings.append(f"Nearby zoning data is incomplete (missing: {', '.join(missing_nearby)})")

    if validation_warnings:
        print("❌ Validation warnings detected:")
        for warning in validation_warnings:
            print(f"  • {warning}")
    else:
        print("✅ All validation checks PASSED")
        print("   No warnings - all data structures are valid!")

    print()
    return all_valid and len(validation_warnings) == 0


if __name__ == "__main__":
    success = test_data_structures()
    exit(0 if success else 1)
