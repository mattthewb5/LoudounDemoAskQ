#!/usr/bin/env python3
"""
Test Athens-Clarke County Zoning APIs
Explores what data is available from the county's GIS system
"""

import requests
import json
from typing import Dict, Any, Optional


def test_zoning_api(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Test the Parcel Zoning Types API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        JSON response from API or None if error
    """
    print("=" * 80)
    print("TESTING PARCEL ZONING TYPES API")
    print("=" * 80)
    print()

    url = "https://enigma.accgov.com/server/rest/services/Parcel_Zoning_Types/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': 100,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json'
    }

    print(f"Testing coordinates: ({latitude}, {longitude})")
    print(f"URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print()

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        print("✅ API Request Successful!")
        print()

        # Show response structure
        print("Response Structure:")
        print(f"  Keys: {list(data.keys())}")
        print()

        # Show fields if available
        if 'fields' in data:
            print("Available Fields:")
            for field in data['fields']:
                field_name = field.get('name', 'Unknown')
                field_type = field.get('type', 'Unknown')
                field_alias = field.get('alias', '')
                print(f"  • {field_name} ({field_type})")
                if field_alias and field_alias != field_name:
                    print(f"    Alias: {field_alias}")
            print()

        # Show features if available
        if 'features' in data:
            feature_count = len(data['features'])
            print(f"Features Found: {feature_count}")
            print()

            if feature_count > 0:
                print("First Feature Data:")
                first_feature = data['features'][0]

                if 'attributes' in first_feature:
                    print("  Attributes:")
                    for key, value in first_feature['attributes'].items():
                        print(f"    • {key}: {value}")
                    print()

                if 'geometry' in first_feature:
                    print("  Geometry:")
                    print(f"    {json.dumps(first_feature['geometry'], indent=4)}")
                    print()

        # Print full JSON for reference
        print("-" * 80)
        print("FULL JSON RESPONSE:")
        print("-" * 80)
        print(json.dumps(data, indent=2))
        print()

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Response text: {response.text[:500]}")
        return None


def test_future_land_use_api(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Test the Future Land Use API

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        JSON response from API or None if error
    """
    print("=" * 80)
    print("TESTING FUTURE LAND USE API")
    print("=" * 80)
    print()

    url = "https://enigma.accgov.com/server/rest/services/FutureLandUse/FeatureServer/0/query"

    params = {
        'geometry': f'{longitude},{latitude}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',  # WGS84 (standard lat/lon)
        'distance': 100,
        'units': 'esriSRUnit_Meter',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json'
    }

    print(f"Testing coordinates: ({latitude}, {longitude})")
    print(f"URL: {url}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print()

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        print("✅ API Request Successful!")
        print()

        # Show response structure
        print("Response Structure:")
        print(f"  Keys: {list(data.keys())}")
        print()

        # Show fields if available
        if 'fields' in data:
            print("Available Fields:")
            for field in data['fields']:
                field_name = field.get('name', 'Unknown')
                field_type = field.get('type', 'Unknown')
                field_alias = field.get('alias', '')
                print(f"  • {field_name} ({field_type})")
                if field_alias and field_alias != field_name:
                    print(f"    Alias: {field_alias}")
            print()

        # Show features if available
        if 'features' in data:
            feature_count = len(data['features'])
            print(f"Features Found: {feature_count}")
            print()

            if feature_count > 0:
                print("First Feature Data:")
                first_feature = data['features'][0]

                if 'attributes' in first_feature:
                    print("  Attributes:")
                    for key, value in first_feature['attributes'].items():
                        print(f"    • {key}: {value}")
                    print()

                if 'geometry' in first_feature:
                    print("  Geometry:")
                    print(f"    {json.dumps(first_feature['geometry'], indent=4)}")
                    print()

        # Print full JSON for reference
        print("-" * 80)
        print("FULL JSON RESPONSE:")
        print("-" * 80)
        print(json.dumps(data, indent=2))
        print()

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Response text: {response.text[:500]}")
        return None


def main():
    """Main test function"""
    # Test coordinates for 150 Hancock Ave, Athens GA
    test_lat = 33.9519
    test_lon = -83.3774

    print("🏠 Testing Athens-Clarke County Zoning APIs")
    print(f"📍 Test Location: 150 Hancock Avenue, Athens, GA")
    print(f"📍 Coordinates: ({test_lat}, {test_lon})")
    print()
    print()

    # Test Parcel Zoning Types API
    zoning_data = test_zoning_api(test_lat, test_lon)

    print()
    print()

    # Test Future Land Use API
    land_use_data = test_future_land_use_api(test_lat, test_lon)

    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()

    if zoning_data:
        feature_count = len(zoning_data.get('features', []))
        print(f"✅ Zoning API: {feature_count} features found")
    else:
        print("❌ Zoning API: Failed")

    if land_use_data:
        feature_count = len(land_use_data.get('features', []))
        print(f"✅ Future Land Use API: {feature_count} features found")
    else:
        print("❌ Future Land Use API: Failed")

    print()


if __name__ == "__main__":
    main()
