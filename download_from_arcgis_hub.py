#!/usr/bin/env python3
"""
Download school zone data from ArcGIS Hub using direct feature service access
"""

import requests
import json
import os


def find_arcgis_item_id(dataset_name: str) -> str:
    """
    Try to find the ArcGIS item ID by searching the hub
    """
    search_url = "https://www.arcgis.com/sharing/rest/search"

    params = {
        'f': 'json',
        'q': f'{dataset_name} AND owner:AthensClarke',
        'num': 10
    }

    try:
        response = requests.get(search_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                print(f"Found {len(results)} results for '{dataset_name}':")
                for r in results:
                    print(f"  - {r.get('title')} (ID: {r.get('id')})")
                    print(f"    Type: {r.get('type')}")
                    if 'url' in r:
                        print(f"    URL: {r.get('url')}")
                return results
    except Exception as e:
        print(f"Search error: {e}")

    return []


def download_from_feature_service(service_url: str, output_file: str):
    """
    Download from a feature service URL
    """
    # Build query URL
    query_url = f"{service_url}/query"

    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'returnGeometry': 'true'
    }

    try:
        print(f"Querying: {query_url}")
        response = requests.get(query_url, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Downloaded to {output_file}")
            print(f"  Features: {len(data.get('features', []))}")
            return True
        else:
            print(f"✗ Failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("Searching for Athens-Clarke County school zone data on ArcGIS Online...")
    print()

    # Search for different terms
    search_terms = [
        "Athens Clarke Elementary School",
        "Athens Clarke Middle School",
        "Athens Clarke High School",
        "Clarke County School Zones",
        "CCSD Attendance Zones"
    ]

    all_results = []
    for term in search_terms:
        print(f"\nSearching for: {term}")
        results = find_arcgis_item_id(term)
        all_results.extend(results)
        print()

    # Try to download any feature services found
    for result in all_results:
        if 'url' in result and 'FeatureServer' in result.get('url', ''):
            service_url = result['url']
            # Try each layer
            for layer_id in range(5):  # Try first 5 layers
                test_url = f"{service_url}/{layer_id}"
                output = f"data/{result.get('title', 'unknown').lower().replace(' ', '-')}-{layer_id}.geojson"
                download_from_feature_service(test_url, output)
