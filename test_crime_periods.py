#!/usr/bin/env python3
"""
Test crime lookup with different time periods
Demonstrates flexibility to query 12 months, 3 years, or 5 years
"""

from crime_lookup import get_crimes_near_address, format_crime_summary


def test_time_periods():
    """Test one address with multiple time periods"""
    address = "150 Hancock Avenue, Athens, GA 30601"
    radius = 0.5

    print("=" * 80)
    print("CRIME LOOKUP - DIFFERENT TIME PERIODS")
    print("=" * 80)
    print(f"\nAddress: {address}")
    print(f"Radius: {radius} miles\n")

    # Test different time periods
    periods = [
        (12, "Last 12 months (1 year)"),
        (36, "Last 36 months (3 years)"),
        (60, "Last 60 months (5 years - DEFAULT)")
    ]

    results = {}

    for months, description in periods:
        print(f"\n{'='*80}")
        print(f"Testing: {description}")
        print(f"{'='*80}\n")

        try:
            crimes = get_crimes_near_address(address, radius_miles=radius, months_back=months)

            if crimes is not None:
                results[months] = len(crimes)
                print(f"✅ Found {len(crimes)} crimes")

                # Show top 5 crime types
                crime_types = {}
                for crime in crimes:
                    crime_types[crime.crime_type] = crime_types.get(crime.crime_type, 0) + 1

                print(f"\nTop 5 Crime Types:")
                for crime_type, count in sorted(crime_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  • {crime_type}: {count}")

                # Show date range
                if crimes:
                    dates = [c.date for c in crimes]
                    oldest = min(dates)
                    newest = max(dates)
                    print(f"\nDate Range:")
                    print(f"  Oldest: {oldest.strftime('%B %d, %Y')}")
                    print(f"  Newest: {newest.strftime('%B %d, %Y')}")

            else:
                print("❌ Failed to retrieve data")

        except Exception as e:
            print(f"❌ Error: {e}")

    # Summary comparison
    print(f"\n\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}\n")

    for months, description in periods:
        if months in results:
            print(f"{description:40s} {results[months]:4d} crimes")

    print(f"\n{'='*80}")
    print("USAGE EXAMPLES")
    print(f"{'='*80}\n")

    print("# Get last 12 months (1 year)")
    print("crimes = get_crimes_near_address('150 Hancock Ave', months_back=12)")
    print()

    print("# Get last 36 months (3 years)")
    print("crimes = get_crimes_near_address('150 Hancock Ave', months_back=36)")
    print()

    print("# Get last 60 months (5 years - DEFAULT)")
    print("crimes = get_crimes_near_address('150 Hancock Ave')  # uses default")
    print("# or explicitly:")
    print("crimes = get_crimes_near_address('150 Hancock Ave', months_back=60)")
    print()

    print("# Custom time periods")
    print("crimes = get_crimes_near_address('150 Hancock Ave', months_back=24)  # 2 years")
    print("crimes = get_crimes_near_address('150 Hancock Ave', months_back=6)   # 6 months")


if __name__ == "__main__":
    test_time_periods()
