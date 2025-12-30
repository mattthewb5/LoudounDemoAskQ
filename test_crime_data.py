#!/usr/bin/env python3
"""
Test script to retrieve recent crime data from Athens-Clarke County Police
Uses ArcGIS REST API to fetch crime incidents
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

# ArcGIS REST API endpoint for Athens-Clarke County crime data
CRIME_API_URL = "https://services2.arcgis.com/xSEULKvB31odt3XQ/arcgis/rest/services/Crime_Web_Layer_CAU_view/FeatureServer/0/query"


def get_recent_crimes(count: int = 10) -> Optional[List[Dict]]:
    """
    Retrieve the most recent crimes from Athens-Clarke County

    Args:
        count: Number of recent crimes to retrieve (default: 10)

    Returns:
        List of crime dictionaries, or None if error
    """
    params = {
        'where': '1=1',  # Get all records
        'outFields': '*',  # Get all fields
        'orderByFields': 'Date DESC',  # Most recent first
        'resultRecordCount': count,
        'f': 'json'  # Return as JSON
    }

    try:
        print(f"🔍 Fetching {count} most recent crimes from Athens-Clarke County...")
        response = requests.get(CRIME_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if 'features' in data:
            return [feature['attributes'] for feature in data['features']]
        else:
            print(f"❌ Unexpected response format: {data.keys()}")
            return None

    except requests.exceptions.Timeout:
        print("❌ Request timed out. Please check your internet connection.")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Please check your internet connection.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def format_timestamp(timestamp_ms: int) -> str:
    """
    Convert Unix timestamp (milliseconds) to readable date string

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        Formatted date string (e.g., "January 18, 2022")
    """
    if not timestamp_ms:
        return "Unknown date"

    try:
        timestamp_sec = timestamp_ms / 1000
        dt = datetime.fromtimestamp(timestamp_sec)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return f"Invalid timestamp: {timestamp_ms}"


def display_crime(crime: Dict, index: int):
    """
    Display a single crime incident in a readable format

    Args:
        crime: Crime data dictionary
        index: Crime number (for display)
    """
    print(f"\n{'='*70}")
    print(f"CRIME #{index}")
    print(f"{'='*70}")

    # Date
    date_str = format_timestamp(crime.get('Date'))
    print(f"📅 Date:          {date_str}")

    # Crime type
    crime_type = crime.get('Crime_Description', 'Unknown')
    print(f"🚨 Crime Type:    {crime_type}")

    # Location
    address = crime.get('Address_Line_1', 'Location not specified')
    print(f"📍 Location:      {address}")

    # Case number
    case_num = crime.get('Case_Number', 'N/A')
    print(f"📋 Case Number:   {case_num}")

    # District and Beat
    district = crime.get('District', 'N/A')
    beat = crime.get('Beat', 'N/A')
    print(f"🚔 District/Beat: District {district}, Beat {beat}")

    # Coordinates (for mapping)
    lat = crime.get('Lat')
    lon = crime.get('Lon')
    if lat and lon:
        print(f"🗺️  Coordinates:   {lat:.6f}, {lon:.6f}")

    # Offense count
    offense_count = crime.get('Total_Offense_Counts', 1)
    if offense_count > 1:
        print(f"⚠️  Offenses:      {offense_count} offenses in this incident")


def display_summary(crimes: List[Dict]):
    """
    Display summary statistics about the retrieved crimes

    Args:
        crimes: List of crime dictionaries
    """
    print(f"\n{'='*70}")
    print("SUMMARY STATISTICS")
    print(f"{'='*70}")

    # Count by crime type
    crime_types = {}
    for crime in crimes:
        crime_type = crime.get('Crime_Description', 'Unknown')
        crime_types[crime_type] = crime_types.get(crime_type, 0) + 1

    print("\n📊 Crimes by Type:")
    for crime_type, count in sorted(crime_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {crime_type}: {count}")

    # Date range
    if crimes:
        dates = [crime.get('Date') for crime in crimes if crime.get('Date')]
        if dates:
            oldest = format_timestamp(min(dates))
            newest = format_timestamp(max(dates))
            print(f"\n📅 Date Range:")
            print(f"   • Oldest: {oldest}")
            print(f"   • Newest: {newest}")

    # Districts
    districts = set(crime.get('District', 'Unknown') for crime in crimes)
    print(f"\n🚔 Districts Covered: {', '.join(sorted(districts))}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("ATHENS-CLARKE COUNTY CRIME DATA TEST")
    print("Data Source: Athens-Clarke County Police Department")
    print("=" * 70)

    # Retrieve recent crimes
    crimes = get_recent_crimes(count=10)

    if not crimes:
        print("\n❌ Failed to retrieve crime data.")
        return

    print(f"\n✅ Successfully retrieved {len(crimes)} crime incidents\n")

    # Display each crime
    for i, crime in enumerate(crimes, 1):
        display_crime(crime, i)

    # Display summary
    display_summary(crimes)

    print("\n" + "=" * 70)
    print("✅ Test completed successfully!")
    print("=" * 70)

    # Data notes
    print("\n⚠️  DATA NOTES:")
    print("   • Data is from Athens-Clarke County Police Department")
    print("   • Certain sensitive offense categories may be excluded")
    print("   • Locations may be approximate for privacy protection")
    print("   • Data should be used for informational purposes only")


if __name__ == "__main__":
    main()
