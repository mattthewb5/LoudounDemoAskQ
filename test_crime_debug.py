#!/usr/bin/env python3
"""
Debug script to test crime lookup with different parameters
"""

from crime_lookup import get_crimes_near_address


def main():
    address = "150 Hancock Avenue, Athens, GA 30601"

    print("Testing with different time periods:\n")

    # Test with different months_back values
    for months in [12, 24, 36, 60]:
        print(f"--- Last {months} months (radius: 1.0 miles) ---")
        try:
            crimes = get_crimes_near_address(address, radius_miles=1.0, months_back=months)
            print(f"✅ Found {len(crimes)} crimes\n")

            if crimes and len(crimes) > 0:
                print("Sample crimes found:")
                for crime in crimes[:3]:
                    print(f"  • {crime.date.strftime('%Y-%m-%d')} - {crime.crime_type}")
                break  # Found some, stop testing

        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
