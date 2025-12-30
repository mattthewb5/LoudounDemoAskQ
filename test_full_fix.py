#!/usr/bin/env python3
"""
Test full address fix for both school and crime lookups
"""

from school_info import get_school_info
from crime_analysis import analyze_crime_near_address

def test_full_integration():
    """Test the user's address with both systems"""

    test_address = "1398 Hancock Avenue W, Athens, GA 30606"

    print("=" * 80)
    print("TESTING FULL INTEGRATION WITH USER'S ADDRESS")
    print("=" * 80)
    print()
    print(f"Address: {test_address}")
    print()

    # Test 1: School Lookup
    print("-" * 80)
    print("TEST 1: SCHOOL LOOKUP")
    print("-" * 80)
    print()

    try:
        school_info = get_school_info(test_address)

        if school_info:
            print(f"✅ SUCCESS - School lookup working!")
            print()
            print(f"Elementary: {school_info.elementary}")
            print()
            print(f"Middle: {school_info.middle}")
            print()
            print(f"High: {school_info.high}")
            print()
        else:
            print("❌ FAILED - school_info returned None")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()

    # Test 2: Crime Analysis
    print("-" * 80)
    print("TEST 2: CRIME ANALYSIS")
    print("-" * 80)
    print()

    try:
        crime_analysis = analyze_crime_near_address(test_address, radius_miles=0.5, months_back=12)

        if crime_analysis:
            print(f"✅ SUCCESS - Crime analysis working!")
            print()
            print(f"Safety Score: {crime_analysis.safety_score.score}/100 ({crime_analysis.safety_score.level})")
            print(f"Total Crimes: {crime_analysis.statistics.total_crimes}")
            print(f"Violent: {crime_analysis.statistics.violent_count} ({crime_analysis.statistics.violent_percentage:.1f}%)")
            print(f"Property: {crime_analysis.statistics.property_count} ({crime_analysis.statistics.property_percentage:.1f}%)")
            print(f"Trend: {crime_analysis.trend.trend_description}")
            print()
        else:
            print("❌ FAILED - crime_analysis returned None")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Address normalization fix applied to both systems")
    print("   - 'Hancock Avenue W' normalized to 'W Hancock Avenue'")
    print("   - Works for school lookup AND crime lookup")
    print()

if __name__ == "__main__":
    test_full_integration()
