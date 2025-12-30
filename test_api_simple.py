#!/usr/bin/env python3
"""
Test spatial query without date filtering
"""

import requests
from datetime import datetime
import math


CRIME_API_URL = "https://services2.arcgis.com/xSEULKvB31odt3XQ/arcgis/rest/services/Crime_Web_Layer_CAU_view/FeatureServer/0/query"


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 3959 * c


def test_spatial_query():
    """Test spatial query WITHOUT date filter"""
    print("Testing spatial query (no date filter)")
    print("="*60)

    # 150 Hancock Avenue coords
    center_lat = 33.959945
    center_lon = -83.376797
    radius_miles = 2.0
    radius_meters = radius_miles * 1609.34

    params = {
        'geometry': f'{center_lon},{center_lat}',
        'geometryType': 'esriGeometryPoint',
        'inSR': '4326',
        'spatialRel': 'esriSpatialRelIntersects',
        'distance': radius_meters,
        'units': 'esriSRUnit_Meter',
        'where': '1=1',  # Get all (no date filter)
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'json'
    }

    print(f"Searching within {radius_miles} miles of:")
    print(f"  {center_lat}, {center_lon}\n")

    response = requests.get(CRIME_API_URL, params=params, timeout=15)
    data = response.json()

    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return

    if 'features' in data:
        crimes = [f['attributes'] for f in data['features']]
        print(f"✅ Found {len(crimes)} total crimes in database within radius\n")

        # Calculate distances and filter recent ones
        recent_crimes = []
        for crime in crimes:
            crime_lat = crime.get('Lat')
            crime_lon = crime.get('Lon')
            date_ms = crime.get('Date')

            if not crime_lat or not crime_lon or not date_ms:
                continue

            distance = haversine_distance(center_lat, center_lon, crime_lat, crime_lon)
            date = datetime.fromtimestamp(date_ms / 1000)

            crime['distance'] = distance
            crime['date_obj'] = date

            # Only show crimes from 2024 or 2025
            if date.year >= 2024:
                recent_crimes.append(crime)

        print(f"Crimes from 2024-2025: {len(recent_crimes)}\n")

        if recent_crimes:
            # Sort by distance
            recent_crimes.sort(key=lambda x: x['distance'])

            print("Closest recent crimes:")
            for crime in recent_crimes[:10]:
                print(f"  • {crime['date_obj'].strftime('%Y-%m-%d')} - {crime.get('Crime_Description')}")
                print(f"    {crime.get('Address_Line_1')}")
                print(f"    Distance: {crime['distance']:.3f} miles\n")
        else:
            print("No crimes from 2024-2025 found in this area")

            # Show a few older crimes as examples
            print("\nOlder crimes in this area (examples):")
            crimes_with_dist = [c for c in crimes if 'distance' in c]
            crimes_with_dist.sort(key=lambda x: x.get('date_obj', datetime.min), reverse=True)

            for crime in crimes_with_dist[:5]:
                if 'date_obj' in crime:
                    print(f"  • {crime['date_obj'].strftime('%Y-%m-%d')} - {crime.get('Crime_Description')}")
                    print(f"    {crime.get('Address_Line_1')}")
                    print(f"    Distance: {crime['distance']:.3f} miles\n")


if __name__ == "__main__":
    test_spatial_query()
