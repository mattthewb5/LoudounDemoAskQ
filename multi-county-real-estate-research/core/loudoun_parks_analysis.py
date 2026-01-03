"""
Parks & Recreation Access Analysis for Loudoun County

Provides functions to analyze nearby parks and recreational facilities.
Designed for AI tool integration.

Data source: Google Places API (pre-cached in parks.json)
Cache file: data/loudoun/config/parks.json
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional


# Data paths
_MODULE_DIR = Path(__file__).parent.parent
_DATA_DIR = _MODULE_DIR / 'data' / 'loudoun'
_PARKS_FILE = _DATA_DIR / 'config' / 'parks.json'

# Module-level cache for parks data
_parks_cache: Optional[Dict[str, Any]] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def load_parks_data() -> Dict[str, Any]:
    """
    Load parks data from static JSON file.

    The parks.json file contains pre-fetched data from Google Places API
    covering parks and playgrounds across Loudoun County.

    Returns:
        dict: Parks data with 'available', 'parks' list, 'metadata', and 'total_parks'
    """
    global _parks_cache

    # Return cached data if available
    if _parks_cache is not None:
        return _parks_cache

    try:
        if not _PARKS_FILE.exists():
            return {"available": False, "error": "Parks data file not found"}

        with open(_PARKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        _parks_cache = {
            "available": True,
            "parks": data.get("parks", []),
            "metadata": data.get("_metadata", {}),
            "total_parks": len(data.get("parks", []))
        }
        return _parks_cache

    except Exception as e:
        return {"available": False, "error": str(e)}


def get_nearest_parks(lat: float, lon: float, parks_data: Dict[str, Any] = None,
                      limit: int = 5, max_distance: float = 10.0) -> Dict[str, Any]:
    """
    Get nearest parks to a property location.

    Uses haversine formula to calculate straight-line distances from the property
    to all parks in the database, then returns the nearest ones.

    Args:
        lat: Property latitude
        lon: Property longitude
        parks_data: Output from load_parks_data() (optional, will load if None)
        limit: Maximum parks to return (default 5)
        max_distance: Maximum distance in miles to consider (default 10)

    Returns:
        dict: {
            'available': bool,
            'nearest_park': dict or None (closest park with distance),
            'nearby_parks': list (up to 'limit' parks sorted by distance),
            'count_within_5mi': int (parks within 5 miles),
            'parks_within_1mi': int
        }
    """
    if parks_data is None:
        parks_data = load_parks_data()

    if not parks_data.get("available"):
        return {"available": False, "error": parks_data.get("error", "Parks data unavailable")}

    parks = parks_data.get("parks", [])

    if not parks:
        return {"available": False, "error": "No parks in database"}

    # Calculate distances to all parks
    results = []
    for park in parks:
        distance = haversine_distance(
            lat, lon,
            park['latitude'],
            park['longitude']
        )

        if distance <= max_distance:
            results.append({
                'name': park.get('name', 'Unknown Park'),
                'latitude': park['latitude'],
                'longitude': park['longitude'],
                'type': park.get('type', 'park'),
                'distance_miles': round(distance, 2)
            })

    # Sort by distance (nearest first)
    results.sort(key=lambda x: x['distance_miles'])

    # Count parks at different radii
    count_1mi = sum(1 for p in results if p['distance_miles'] <= 1.0)
    count_5mi = sum(1 for p in results if p['distance_miles'] <= 5.0)

    return {
        "available": True,
        "nearest_park": results[0] if results else None,
        "nearby_parks": results[:limit],
        "parks_within_1mi": count_1mi,
        "count_within_5mi": count_5mi,
        "total_found": len(results)
    }


def analyze_park_access(lat: float, lon: float, limit: int = 5) -> Dict[str, Any]:
    """
    Complete parks access analysis for a location.

    Main entry point for AI tool integration.

    Args:
        lat: Property latitude
        lon: Property longitude
        limit: Maximum parks to return (default 5)

    Returns:
        Dict with:
        - available: bool
        - parks_count: int (total parks found within 10 miles)
        - parks_within_1mi: int
        - nearest_park: dict with name, distance, type
        - parks: list of nearby parks
        - summary: text summary
        - data_source: source attribution
    """
    parks_data = load_parks_data()
    result = get_nearest_parks(lat, lon, parks_data, limit=limit)

    if not result.get("available"):
        return {
            "available": False,
            "parks_count": 0,
            "summary": "Parks data is not available.",
            "data_source": None
        }

    # Build summary
    parks_count = result.get("total_found", 0)
    parks_1mi = result.get("parks_within_1mi", 0)
    nearest = result.get("nearest_park")

    if nearest:
        summary_parts = [f"{parks_count} parks within 10 miles."]
        summary_parts.append(f"Nearest: {nearest['name']} at {nearest['distance_miles']:.1f} miles.")
        if parks_1mi > 0:
            summary_parts.append(f"{parks_1mi} park(s) within 1 mile for easy access.")
    else:
        summary_parts = ["No parks found within 10 miles."]

    return {
        "available": True,
        "parks_count": parks_count,
        "parks_within_1mi": parks_1mi,
        "nearest_park": nearest,
        "parks": result.get("nearby_parks", []),
        "summary": " ".join(summary_parts),
        "data_source": "Google Places API (pre-cached)"
    }


def get_parks_summary(lat: float, lon: float) -> str:
    """
    Get a plain-text summary of parks access for a location.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Human-readable summary string
    """
    result = analyze_park_access(lat, lon)
    return result.get('summary', 'Parks access information unavailable.')
