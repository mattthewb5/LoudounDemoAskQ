#!/usr/bin/env python3
"""
Test address normalization fix
"""

from crime_lookup import get_crimes_near_address

def test_user_address():
    """Test the exact address the user provided"""

    test_address = "1398 Hancock Avenue W, Athens, GA 30606"

    print("=" * 80)
    print("TESTING USER'S ADDRESS WITH FIX")
    print("=" * 80)
    print()
    print(f"Address: {test_address}")
    print()

    try:
        crimes = get_crimes_near_address(test_address, radius_miles=0.5, months_back=12)

        if crimes is not None:
            print(f"\n✅ SUCCESS! Found {len(crimes)} crimes within 0.5 miles")
            print()
            print("First 5 incidents:")
            for i, crime in enumerate(crimes[:5], 1):
                print(f"  {i}. {crime.crime_type}")
                print(f"     Date: {crime.date.strftime('%Y-%m-%d')}")
                print(f"     Distance: {crime.distance_miles:.3f} miles")
                print()
        else:
            print("❌ FAILED - returned None")

    except ValueError as e:
        print(f"❌ ValueError: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_user_address()
