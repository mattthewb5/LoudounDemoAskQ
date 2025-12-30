#!/usr/bin/env python3
"""
Quick test to verify crime proximity lookup with different radii
"""

from crime_lookup import get_crimes_near_address, format_crime_summary


def test_address_with_radii(address: str):
    """Test an address with different search radii"""
    print(f"\n{'='*80}")
    print(f"TESTING: {address}")
    print(f"{'='*80}\n")

    radii = [0.5, 1.0, 2.0]

    for radius in radii:
        try:
            print(f"\n--- Radius: {radius} miles ---")
            crimes = get_crimes_near_address(address, radius_miles=radius, months_back=12)

            if crimes is not None:
                print(f"✅ Found {len(crimes)} crimes within {radius} miles")

                if crimes:
                    # Show a few examples
                    print(f"\nFirst 3 crimes:")
                    for crime in crimes[:3]:
                        print(f"  • {crime.crime_type} - {crime.address} ({crime.distance_miles:.2f} mi)")
            else:
                print(f"❌ Failed to retrieve crime data")

        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    # Test with one address at different radii
    test_address_with_radii("150 Hancock Avenue, Athens, GA 30601")


if __name__ == "__main__":
    main()
