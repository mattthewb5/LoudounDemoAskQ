#!/usr/bin/env python3
"""
Loudoun County Parks Data Fetch Script

ONE-TIME USE SCRIPT to fetch parks and playgrounds from Google Places API
and save to a static JSON file for the property intelligence platform.

This script:
1. Queries 5 strategic points across Loudoun County
2. Fetches 'park' and 'playground' place types
3. Deduplicates results by place_id
4. Saves to data/loudoun/config/parks.json

Cost: ~$0.32 (10 API calls x $0.032 each)

Usage:
    python scripts/fetch_parks_data.py

Author: NewCo Property Intelligence Platform
Date: December 2025
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.api_config import get_api_key

# =============================================================================
# CONFIGURATION
# =============================================================================

# 10 strategic points covering Loudoun County with overlapping 5-mile radii
SEARCH_POINTS = [
    {"name": "Purcellville", "lat": 39.14, "lon": -77.72},       # Northwest
    {"name": "Round Hill", "lat": 39.13, "lon": -77.78},         # Far West
    {"name": "Sterling", "lat": 39.01, "lon": -77.40},           # Northeast
    {"name": "Ashburn", "lat": 39.04, "lon": -77.49},            # East Central
    {"name": "Leesburg", "lat": 39.11, "lon": -77.56},           # Center
    {"name": "Middleburg", "lat": 38.97, "lon": -77.73},         # Southwest
    {"name": "South Riding", "lat": 38.92, "lon": -77.50},       # Southeast
    {"name": "Brambleton", "lat": 38.98, "lon": -77.54},         # South Central
    {"name": "Aldie", "lat": 38.97, "lon": -77.64},              # South
    {"name": "Hamilton", "lat": 39.13, "lon": -77.66},           # North Central
]

# Place types to fetch
PLACE_TYPES = ["park", "playground"]

# Search radius in meters (5 miles = 8,047 meters)
SEARCH_RADIUS_METERS = 8047.0

# Output file path
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "loudoun" / "config" / "parks.json"

# API endpoint
PLACES_API_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Field mask - only request needed fields to minimize response size
FIELD_MASK = "places.displayName,places.location,places.id,places.types,places.shortFormattedAddress"


# =============================================================================
# API FUNCTIONS
# =============================================================================

def fetch_parks_from_point(lat: float, lon: float, place_type: str, api_key: str) -> list:
    """
    Fetch parks/playgrounds from a single point using Google Places API.

    Args:
        lat: Latitude of search center
        lon: Longitude of search center
        place_type: Type of place to search ('park' or 'playground')
        api_key: Google Maps API key

    Returns:
        List of park dictionaries
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK
    }

    body = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": SEARCH_RADIUS_METERS
            }
        },
        "includedTypes": [place_type],
        "maxResultCount": 20  # API max is 20
    }

    try:
        response = requests.post(PLACES_API_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()

        parks = []
        for place in data.get("places", []):
            # Extract fields
            display_name = place.get("displayName", {})
            location = place.get("location", {})

            park = {
                "name": display_name.get("text", "Unknown Park"),
                "latitude": location.get("latitude", 0),
                "longitude": location.get("longitude", 0),
                "place_id": place.get("id", ""),
                "types": place.get("types", []),
                "vicinity": place.get("shortFormattedAddress", "")
            }
            parks.append(park)

        return parks

    except requests.RequestException as e:
        print(f"  ERROR: API request failed - {e}")
        return []


def deduplicate_parks(all_parks: list) -> list:
    """
    Remove duplicate parks based on place_id.

    Args:
        all_parks: List of all parks from all queries

    Returns:
        Deduplicated list of parks
    """
    seen_ids = set()
    unique_parks = []

    for park in all_parks:
        place_id = park.get("place_id", "")
        if place_id and place_id not in seen_ids:
            seen_ids.add(place_id)
            unique_parks.append(park)

    # Sort by name for consistent output
    unique_parks.sort(key=lambda x: x.get("name", ""))

    return unique_parks


def save_parks_json(parks: list) -> None:
    """
    Save parks data to JSON file with metadata.

    Args:
        parks: List of deduplicated park dictionaries
    """
    # Build output structure
    output = {
        "_metadata": {
            "description": "Loudoun County parks and recreation areas for property proximity analysis",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "data_source": "Google Places API (one-time pull)",
            "query_points": len(SEARCH_POINTS),
            "place_types": PLACE_TYPES,
            "search_radius_miles": round(SEARCH_RADIUS_METERS / 1609.34, 1),
            "total_parks": len(parks),
            "notes": "Static file - update annually or as needed. Cost: ~$0.32 per refresh."
        },
        "parks": parks
    }

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(parks)} parks to {OUTPUT_FILE}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("Loudoun County Parks Data Fetch")
    print("=" * 60)
    print(f"Search points: {len(SEARCH_POINTS)}")
    print(f"Place types: {PLACE_TYPES}")
    print(f"Search radius: {SEARCH_RADIUS_METERS / 1609.34:.1f} miles")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 60)

    # Get API key
    api_key = get_api_key('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("ERROR: Google Maps API key not found!")
        print("Please ensure GOOGLE_MAPS_API_KEY is set in environment or .env file")
        sys.exit(1)

    print(f"API key: ...{api_key[-8:]}")
    print()

    # Fetch parks from all points
    all_parks = []
    successful_queries = 0
    failed_queries = 0

    for point in SEARCH_POINTS:
        for place_type in PLACE_TYPES:
            print(f"Fetching {place_type} near {point['name']}...", end=" ")

            parks = fetch_parks_from_point(
                point['lat'],
                point['lon'],
                place_type,
                api_key
            )

            if parks:
                print(f"Found {len(parks)} results")
                all_parks.extend(parks)
                successful_queries += 1
            else:
                print("No results or error")
                failed_queries += 1

            # Rate limiting - wait between requests (2 seconds to avoid 403)
            time.sleep(2.0)

    print()
    print(f"Query summary: {successful_queries} successful, {failed_queries} failed")
    print(f"Total results before deduplication: {len(all_parks)}")

    # Deduplicate
    unique_parks = deduplicate_parks(all_parks)
    print(f"Unique parks after deduplication: {len(unique_parks)}")

    # Save to JSON
    save_parks_json(unique_parks)

    # Print some sample parks for verification
    print("\nSample parks (first 10):")
    for park in unique_parks[:10]:
        print(f"  - {park['name']} ({park['vicinity']})")

    print("\n" + "=" * 60)
    print("DONE! Parks data saved to parks.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
