#!/usr/bin/env python3
"""
Debug address geocoding issues
"""

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

ATHENS_BOUNDS = {
    'lat_min': 33.85,
    'lat_max': 34.05,
    'lon_min': -83.50,
    'lon_max': -83.25
}

def test_address_variations(base_address):
    """Test different variations of an address"""

    variations = [
        base_address,
        base_address.replace("Hancock Avenue W", "W Hancock Avenue"),
        base_address.replace("Hancock Avenue W", "West Hancock Avenue"),
        base_address.replace("Hancock Avenue W", "Hancock Ave W"),
        base_address.replace("Hancock Avenue W", "W Hancock Ave"),
    ]

    geolocator = Nominatim(user_agent="athens_home_buyer_research")

    print("=" * 80)
    print(f"TESTING ADDRESS VARIATIONS")
    print("=" * 80)
    print()

    for i, address in enumerate(variations, 1):
        print(f"\n{i}. Testing: {address}")
        print("-" * 80)

        try:
            location = geolocator.geocode(address, timeout=10)

            if location:
                lat, lon = location.latitude, location.longitude
                print(f"   ✓ Geocoded successfully")
                print(f"   Coordinates: {lat:.6f}, {lon:.6f}")
                print(f"   Full result: {location.address}")

                # Check Athens bounds
                in_bounds = (ATHENS_BOUNDS['lat_min'] <= lat <= ATHENS_BOUNDS['lat_max'] and
                           ATHENS_BOUNDS['lon_min'] <= lon <= ATHENS_BOUNDS['lon_max'])

                if in_bounds:
                    print(f"   ✓ WITHIN Athens-Clarke County bounds")
                else:
                    print(f"   ✗ OUTSIDE Athens-Clarke County bounds")
                    print(f"      Expected lat: {ATHENS_BOUNDS['lat_min']}-{ATHENS_BOUNDS['lat_max']}")
                    print(f"      Expected lon: {ATHENS_BOUNDS['lon_min']}-{ATHENS_BOUNDS['lon_max']}")
            else:
                print(f"   ✗ Not found")

        except GeocoderTimedOut:
            print(f"   ✗ Timeout")
        except GeocoderServiceError as e:
            print(f"   ✗ Service error: {e}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test the user's address
    test_address = "1398 Hancock Avenue W, Athens, GA 30606"
    test_address_variations(test_address)

    # Also test without zip code
    print("\n\nTesting without ZIP code:")
    test_address_variations("1398 W Hancock Avenue, Athens, GA")
