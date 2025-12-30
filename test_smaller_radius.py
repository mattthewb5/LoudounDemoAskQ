#!/usr/bin/env python3
"""
Test if smaller radius avoids API limit
"""

from crime_analysis import analyze_crime_near_address

def test_radii():
    """Test different radii to find sweet spot"""
    address = "150 Hancock Avenue, Athens, GA 30601"
    radii = [0.25, 0.5]

    print("=" * 80)
    print("TESTING DIFFERENT RADII TO AVOID API LIMIT")
    print("=" * 80)
    print(f"\nAddress: {address}")
    print(f"Time Period: 12 months\n")

    for radius in radii:
        print(f"\n{'='*80}")
        print(f"Testing {radius} mile radius")
        print(f"{'='*80}\n")

        try:
            analysis = analyze_crime_near_address(address, radius_miles=radius, months_back=12)

            if analysis:
                stats = analysis.statistics
                print(f"\n✅ Results:")
                print(f"   Total Crimes: {stats.total_crimes}")
                print(f"   Violent: {stats.violent_count} ({stats.violent_percentage}%)")
                print(f"   Property: {stats.property_count} ({stats.property_percentage}%)")
                print(f"   Safety Score: {analysis.safety_score.score}/5 ({analysis.safety_score.level})")
            else:
                print(f"❌ Failed to analyze")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")
    print("If 0.25 miles avoids the API limit:")
    print("  → Use 0.25 miles for complete data in high-crime areas")
    print("  → 0.5 miles is still reasonable for most areas")
    print("\nIf both hit the limit:")
    print("  → Accept that these are extremely high-activity areas")
    print("  → The 12-month data we get is still accurate and useful")


if __name__ == "__main__":
    test_radii()
