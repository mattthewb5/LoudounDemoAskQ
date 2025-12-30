#!/usr/bin/env python3
"""
Script to download school attendance zone data from Athens-Clarke County Open Data Portal
"""

import requests
import json
import os
from typing import Optional

def search_arcgis_portal(search_term: str, portal_url: str = "https://data-athensclarke.opendata.arcgis.com") -> list:
    """
    Search the Athens-Clarke County ArcGIS Open Data Portal for datasets

    Args:
        search_term: Term to search for (e.g., "school", "attendance zone")
        portal_url: Base URL of the portal

    Returns:
        List of dataset results
    """
    # ArcGIS Hub API endpoint for searching
    api_url = f"{portal_url}/api/v3/datasets"

    params = {
        "filter[searchTerms]": search_term,
        "page[size]": 100
    }

    try:
        print(f"Searching for '{search_term}' in Athens-Clarke County Open Data Portal...")
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        datasets = data.get('data', [])

        print(f"Found {len(datasets)} datasets matching '{search_term}'")
        return datasets

    except requests.RequestException as e:
        print(f"Error searching portal: {e}")
        return []


def download_geojson(dataset_id: str, output_file: str, portal_url: str = "https://data-athensclarke.opendata.arcgis.com") -> bool:
    """
    Download a dataset as GeoJSON from the portal

    Args:
        dataset_id: The dataset ID or slug
        output_file: Path to save the GeoJSON file
        portal_url: Base URL of the portal

    Returns:
        True if download successful, False otherwise
    """
    # Try different URL patterns for ArcGIS Open Data
    urls_to_try = [
        f"{portal_url}/datasets/{dataset_id}.geojson",
        f"{portal_url}/api/v3/datasets/{dataset_id}/downloads/geojson",
    ]

    for url in urls_to_try:
        try:
            print(f"Attempting to download from: {url}")
            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                # Check if it's valid JSON
                try:
                    data = response.json()
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Successfully downloaded to {output_file}")
                    return True
                except json.JSONDecodeError:
                    print(f"Response was not valid JSON")
                    continue
            else:
                print(f"Failed with status code: {response.status_code}")

        except requests.RequestException as e:
            print(f"Error downloading from {url}: {e}")
            continue

    return False


def find_and_download_school_zones():
    """
    Search for and download school attendance zone data
    """
    print("=" * 70)
    print("Athens-Clarke County School Attendance Zone Data Downloader")
    print("=" * 70)
    print()

    # Search for school-related datasets
    search_terms = [
        "school attendance zone",
        "school zone",
        "elementary attendance",
        "middle school zone",
        "high school zone",
        "school boundary"
    ]

    all_datasets = []
    for term in search_terms:
        datasets = search_arcgis_portal(term)
        all_datasets.extend(datasets)

    # Remove duplicates based on ID
    unique_datasets = {ds.get('id'): ds for ds in all_datasets}

    if not unique_datasets:
        print("\nNo datasets found through API search.")
        print("\nAttempting to download from known dataset IDs...")
        # Try some common patterns
        known_ids = [
            "elementary-school-attendance-zones",
            "middle-school-attendance-zones",
            "high-school-attendance-zones",
            "school-attendance-zones",
            "schools-4"
        ]

        for dataset_id in known_ids:
            output_file = f"data/{dataset_id}.geojson"
            os.makedirs("data", exist_ok=True)
            download_geojson(dataset_id, output_file)
    else:
        print(f"\nFound {len(unique_datasets)} unique datasets:")
        print()
        for idx, (dataset_id, dataset) in enumerate(unique_datasets.items(), 1):
            attrs = dataset.get('attributes', {})
            print(f"{idx}. {attrs.get('name', 'Unknown')}")
            print(f"   ID: {dataset_id}")
            print(f"   Description: {attrs.get('description', 'N/A')[:100]}...")
            print()

        # Try to download each one
        os.makedirs("data", exist_ok=True)
        for dataset_id, dataset in unique_datasets.items():
            attrs = dataset.get('attributes', {})
            name = attrs.get('name', dataset_id).lower().replace(' ', '-')
            output_file = f"data/{name}.geojson"
            download_geojson(dataset_id, output_file)


if __name__ == "__main__":
    find_and_download_school_zones()

    print("\n" + "=" * 70)
    print("Download attempt complete!")
    print("=" * 70)
    print("\nIf automatic download failed, please manually download zone data from:")
    print("https://data-athensclarke.opendata.arcgis.com/")
    print("\nSearch for 'school attendance zone' and download as GeoJSON format.")
    print("Save files to the 'data/' directory with appropriate names:")
    print("  - data/elementary_zones.geojson")
    print("  - data/middle_zones.geojson")
    print("  - data/high_zones.geojson")
