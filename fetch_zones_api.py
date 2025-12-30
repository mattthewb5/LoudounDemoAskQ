#!/usr/bin/env python3
"""
Fetch school zone data from ArcGIS REST API
"""

import requests
import json
import os

def query_arcgis_feature_service(service_url: str, output_file: str, where_clause: str = "1=1") -> bool:
    """
    Query an ArcGIS Feature Service and download all features as GeoJSON

    Args:
        service_url: URL to the feature service layer (ending with /FeatureServer/0 or similar)
        output_file: Path to save GeoJSON
        where_clause: SQL where clause (default "1=1" gets all records)

    Returns:
        True if successful
    """
    # ArcGIS REST API query endpoint
    query_url = f"{service_url}/query"

    params = {
        "where": where_clause,
        "outFields": "*",
        "f": "geojson",
        "returnGeometry": "true"
    }

    try:
        print(f"Querying: {service_url}")
        response = requests.get(query_url, params=params, timeout=60)

        if response.status_code == 200:
            # Check if it's valid GeoJSON
            data = response.json()

            if 'features' in data or 'type' in data:
                os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"✓ Successfully downloaded {len(data.get('features', []))} features to {output_file}")
                return True
            else:
                print(f"✗ Response doesn't appear to be valid GeoJSON")
                print(f"Response keys: {data.keys()}")
                return False
        else:
            print(f"✗ HTTP {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def try_common_service_patterns():
    """
    Try common URL patterns for Athens-Clarke County school zone data
    """
    print("=" * 70)
    print("Attempting to fetch school zone data from ArcGIS REST APIs")
    print("=" * 70)
    print()

    # Common base URLs for Athens-Clarke County
    base_urls = [
        "https://services.arcgis.com/",
        "https://maps.accgov.com/arcgis/rest/services/",
        "https://gis.accgov.com/arcgis/rest/services/",
    ]

    # Common service names to try
    service_patterns = [
        "Elementary_School_Zones/FeatureServer/0",
        "Middle_School_Zones/FeatureServer/0",
        "High_School_Zones/FeatureServer/0",
        "School_Attendance_Zones/FeatureServer/0",
        "Schools/FeatureServer/0",
        "Education/Schools/MapServer/0",
        "Education/School_Zones/MapServer/0",
    ]

    # Also try to find the org ID for ArcGIS Online
    # Athens-Clarke County might host their data on ArcGIS Online
    arcgis_online_patterns = [
        # These are guesses - we'd need to find the actual org ID
        "https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Elementary_School_Zones/FeatureServer/0",
        "https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/School_Zones/FeatureServer/0",
    ]

    success_count = 0

    # Try all combinations
    for base_url in base_urls:
        for service in service_patterns:
            test_url = f"{base_url.rstrip('/')}/{service.lstrip('/')}"
            output_file = f"data/{service.split('/')[0].lower().replace('_', '-')}.geojson"

            if query_arcgis_feature_service(test_url, output_file):
                success_count += 1

    return success_count


def try_specific_rest_endpoint():
    """
    Try the specific REST endpoint if we know it
    """
    # Let's try to access the service catalog first
    catalog_urls = [
        "https://services.arcgis.com/catalog",
        "https://maps.accgov.com/arcgis/rest/services?f=json",
    ]

    for url in catalog_urls:
        try:
            print(f"\nChecking service catalog: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                print(f"✓ Service catalog accessible")
                data = response.json()
                print(json.dumps(data, indent=2)[:500])
        except Exception as e:
            print(f"✗ Cannot access: {e}")


if __name__ == "__main__":
    # First, try to find available services
    try_specific_rest_endpoint()

    # Then try common patterns
    success_count = try_common_service_patterns()

    print("\n" + "=" * 70)
    print(f"Successfully downloaded {success_count} datasets")
    print("=" * 70)

    if success_count == 0:
        print("\nAutomatic fetch failed. The data may require manual download.")
        print("\nNext steps:")
        print("1. Visit: https://data-athensclarke.opendata.arcgis.com/")
        print("2. Search for 'school' or browse datasets")
        print("3. Find attendance zone datasets")
        print("4. Click on each dataset and look for 'Download' or 'API' button")
        print("5. Download as GeoJSON format")
        print("6. Save to data/ directory")
