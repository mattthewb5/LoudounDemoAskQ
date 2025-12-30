#!/usr/bin/env python3
"""
Direct API test to verify the spatial query is working
"""

import requests
from datetime import datetime, timedelta


CRIME_API_URL = "https://services2.arcgis.com/xSEULKvB31odt3XQ/arcgis/rest/services/Crime_Web_Layer_CAU_view/FeatureServer/0/query"


def test_no_spatial_filter():
    """Test API without spatial filter"""
    print("Test 1: Query recent crimes (no spatial filter)")
    print("="*60)

    date_threshold = datetime.now() - timedelta(days=365)
    date_threshold_ms = int(date_threshold.timestamp() * 1000)

    params = {
        'where': f'Date >= {date_threshold_ms}',
        'outFields': '*',
        'orderByFields': 'Date DESC',
        'resultRecordCount': 5,
        'f': 'json'
    }

    response = requests.get(CRIME_API_URL, params=params, timeout=15)
    data = response.json()

    if 'features' in data:
        crimes = [f['attributes'] for f in data['features']]
        print(f"✅ Found {len(crimes)} crimes\n")

        for crime in crimes:
            date_ms = crime.get('Date')
            if date_ms:
                date = datetime.fromtimestamp(date_ms / 1000)
                print(f"  • {date.strftime('%Y-%m-%d')} - {crime.get('Crime_Description')}")
                print(f"    Location: {crime.get('Address_Line_1')}")
                print(f"    Coords: {crime.get('Lat')}, {crime.get('Lon')}\n")
    else:
        print(f"❌ No features found. Response: {data}")


def test_with_spatial_filter():
    """Test API with spatial filter"""
    print("\n\nTest 2: Query crimes near 150 Hancock Ave with spatial filter")
    print("="*60)

    # 150 Hancock Avenue coords
    center_lat = 33.959945
    center_lon = -83.376797

    radius_miles = 2.0
    radius_meters = radius_miles * 1609.34

    date_threshold = datetime.now() - timedelta(days=365)
    date_threshold_ms = int(date_threshold.timestamp() * 1000)

    params = {
        'geometry': f'{center_lon},{center_lat}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'distance': radius_meters,
        'units': 'esriSRUnit_Meter',
        'where': f'Date >= {date_threshold_ms}',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json'
    }

    print(f"Query params:")
    print(f"  Center: {center_lat}, {center_lon}")
    print(f"  Radius: {radius_miles} miles ({radius_meters} meters)")
    print(f"  Date threshold: {date_threshold.strftime('%Y-%m-%d')}\n")

    response = requests.get(CRIME_API_URL, params=params, timeout=15)
    data = response.json()

    if 'features' in data:
        crimes = [f['attributes'] for f in data['features']]
        print(f"✅ Found {len(crimes)} crimes\n")

        for crime in crimes[:5]:
            date_ms = crime.get('Date')
            if date_ms:
                date = datetime.fromtimestamp(date_ms / 1000)
                print(f"  • {date.strftime('%Y-%m-%d')} - {crime.get('Crime_Description')}")
                print(f"    Location: {crime.get('Address_Line_1')}")
                print(f"    Coords: {crime.get('Lat')}, {crime.get('Lon')}\n")
    else:
        print(f"Result: {data}")
        if 'error' in data:
            print(f"❌ Error: {data['error']}")


if __name__ == "__main__":
    test_no_spatial_filter()
    test_with_spatial_filter()
