"""
Loudoun County Neighborhood Amenities Analysis Module

Provides nearby places analysis using Google Places API (New).
Includes aggressive caching to minimize API costs.

Categories analyzed:
- Dining (restaurants within 1.5 miles, quality filtered)
- Grocery (supermarkets within 5 miles)
- Shopping (malls within 3 miles)

Cost optimization:
- File-based caching with 7-day TTL
- Field masks to request only needed data
- Limited to 10 results per category
"""

import json
import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from core.api_config import get_api_key

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'loudoun' / 'cache' / 'places'
CACHE_TTL_DAYS = 7

# Place type categories with search configurations
# Radii tuned for suburban Loudoun County
PLACE_CATEGORIES = {
    "dining": {
        "type": "restaurant",
        "radius_miles": 1.5,
        "display_name": "Dining"
    },
    "grocery": {
        "type": "supermarket",
        "radius_miles": 5.0,
        "display_name": "Grocery"
    },
    "shopping": {
        "type": "shopping_mall",
        "radius_miles": 3.0,
        "display_name": "Shopping"
    },
    "pharmacy": {
        "type": "pharmacy",
        "radius_miles": 5.0,
        "display_name": "Pharmacies"
    }
}

# Field mask for cost optimization - only request what we display
# Includes regularOpeningHours for 24-hour pharmacy detection
FIELD_MASK = "places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.types,places.regularOpeningHours"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in miles."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _is_24_hour(place: Dict, name: str) -> bool:
    """
    Detect if a place is open 24 hours.

    Args:
        place: Raw place dict from Google Places API
        name: Place name string

    Returns:
        True if the place appears to be 24-hour operation
    """
    # Check name for 24-hour indicators
    name_lower = name.lower()
    if '24' in name_lower or '24-hour' in name_lower or '24 hour' in name_lower:
        return True

    # Check opening hours from API
    opening_hours = place.get('regularOpeningHours', {})
    periods = opening_hours.get('periods', [])

    # A 24-hour place typically has a single period with open at 0000 and no close
    # Or 7 periods (one per day) each with open 0000 and close 2359
    if len(periods) == 1:
        period = periods[0]
        open_time = period.get('open', {})
        # Check if open at midnight with no close time
        if open_time.get('hour') == 0 and open_time.get('minute') == 0:
            if 'close' not in period:
                return True

    # Check for "Open 24 hours" text description
    weekday_descriptions = opening_hours.get('weekdayDescriptions', [])
    for desc in weekday_descriptions:
        if '24 hours' in desc.lower() or 'open 24' in desc.lower():
            return True

    return False


def _filter_veterinary_pharmacies(places: List[Dict]) -> List[Dict]:
    """
    Filter out veterinary/pet pharmacies from pharmacy results.

    Args:
        places: List of place dicts from API

    Returns:
        Filtered list excluding pet/vet pharmacies
    """
    vet_keywords = ['pet', 'vet', 'veterinary', 'animal']
    vet_types = {'veterinary_care', 'pet_store'}

    filtered = []
    for p in places:
        name_lower = p.get('name', '').lower()
        types = set(p.get('types', []))

        # Skip if name contains vet keywords or types include vet care
        has_vet_keyword = any(kw in name_lower for kw in vet_keywords)
        has_vet_type = bool(types & vet_types)

        if has_vet_keyword or has_vet_type:
            continue

        filtered.append(p)

    return filtered


def _filter_quality_dining(places: List[Dict], min_rating: float = 4.0, min_reviews: int = 50) -> List[Dict]:
    """
    Filter dining places to quality options only.

    Keeps places that are either highly rated OR have significant review counts.
    This filters out random low-review chains while keeping popular local spots.

    Args:
        places: List of place dicts from API
        min_rating: Minimum rating to include (default 4.0)
        min_reviews: Minimum review count to include regardless of rating (default 50)

    Returns:
        Filtered list of quality places
    """
    return [
        p for p in places
        if (p.get('rating') is not None and p.get('rating', 0) >= min_rating) or
           (p.get('review_count', 0) >= min_reviews)
    ]


def _get_cache_path(lat: float, lon: float, category: str) -> Path:
    """
    Get cache file path for given coordinates and category.

    Rounds coords to 3 decimal places (~110m precision) for cache key.

    Args:
        lat: Latitude
        lon: Longitude
        category: Place category (dining, grocery, shopping)

    Returns:
        Path to cache file
    """
    # Round to 3 decimal places for cache key
    lat_rounded = round(lat, 3)
    lon_rounded = round(lon, 3)

    # Create cache directory if it doesn't exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Format: 39.041_-77.504_dining.json
    filename = f"{lat_rounded}_{lon_rounded}_{category}.json"
    return CACHE_DIR / filename


def _load_from_cache(cache_path: Path, max_age_days: int = CACHE_TTL_DAYS) -> Optional[Dict]:
    """
    Load data from cache if fresh.

    Args:
        cache_path: Path to cache file
        max_age_days: Maximum age in days before cache is stale

    Returns:
        Cached data dict if valid, None if stale or missing
    """
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        # Check timestamp
        cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
        age = datetime.now() - cached_time

        if age > timedelta(days=max_age_days):
            return None  # Cache is stale

        return cached.get('data')

    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _save_to_cache(cache_path: Path, data: Dict) -> None:
    """
    Save data to cache with timestamp.

    Args:
        cache_path: Path to cache file
        data: Data to cache
    """
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # Ensure directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")


def search_nearby_places(
    coords: Tuple[float, float],
    category: str,
    radius_miles: float
) -> Tuple[List[Dict], bool]:
    """
    Search for nearby places using Google Places API (New).

    Checks cache first to minimize API costs.

    Args:
        coords: (latitude, longitude) tuple
        category: Place category key from PLACE_CATEGORIES
        radius_miles: Search radius in miles

    Returns:
        Tuple of (list of place dicts, from_cache boolean)
    """
    lat, lon = coords
    cache_path = _get_cache_path(lat, lon, category)

    # Check cache first
    cached_data = _load_from_cache(cache_path)
    if cached_data is not None:
        print(f"  [CACHE HIT] {category}: Loaded from cache")
        # Apply pharmacy filter to cached results too (in case cache predates filter)
        if category == 'pharmacy':
            cached_data = _filter_veterinary_pharmacies(cached_data)
        return cached_data, True

    print(f"  [API CALL] {category}: Calling Places API...")

    # Get API key
    api_key = get_api_key('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print(f"Warning: Google Maps API key not found")
        return [], False

    # Get place type from category config
    category_config = PLACE_CATEGORIES.get(category)
    if not category_config:
        print(f"Warning: Unknown category: {category}")
        return [], False

    place_type = category_config['type']

    # Build API request
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
        "Content-Type": "application/json"
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": radius_miles * 1609.34  # Convert miles to meters
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        print(f"Warning: Places API error for {category}: {e}")
        return [], False

    # Parse results
    places = []
    raw_places = data.get('places', [])

    for place in raw_places:
        # Extract location
        location = place.get('location', {})
        place_lat = location.get('latitude', 0)
        place_lon = location.get('longitude', 0)

        # Calculate distance
        distance = haversine_distance(lat, lon, place_lat, place_lon)

        # Extract display name
        display_name = place.get('displayName', {})
        name = display_name.get('text', 'Unknown')

        # Parse price level (PRICE_LEVEL_FREE=0, PRICE_LEVEL_INEXPENSIVE=1, etc.)
        price_level_str = place.get('priceLevel', '')
        price_level = 0
        if 'INEXPENSIVE' in price_level_str:
            price_level = 1
        elif 'MODERATE' in price_level_str:
            price_level = 2
        elif 'EXPENSIVE' in price_level_str:
            price_level = 3
        elif 'VERY_EXPENSIVE' in price_level_str:
            price_level = 4

        # Detect 24-hour operation (useful for pharmacies)
        is_24_hour = _is_24_hour(place, name)

        places.append({
            'name': name,
            'address': place.get('formattedAddress', ''),
            'rating': place.get('rating'),
            'review_count': place.get('userRatingCount', 0),
            'distance_miles': round(distance, 2),
            'price_level': price_level,
            'types': place.get('types', []),
            'is_24_hour': is_24_hour
        })

    # Sort by distance
    places.sort(key=lambda x: x['distance_miles'])

    # Filter out veterinary pharmacies for pharmacy category
    if category == 'pharmacy':
        places = _filter_veterinary_pharmacies(places)

    # Save to cache
    _save_to_cache(cache_path, places)

    return places, False


def get_neighborhood_amenities(coords: Tuple[float, float]) -> Dict:
    """
    Get complete neighborhood amenities analysis.

    Args:
        coords: (latitude, longitude) tuple

    Returns:
        Dict with amenity data for all categories plus summary
    """
    result = {
        "dining": {},
        "grocery": {},
        "shopping": {},
        "summary": {
            "total_amenities": 0,
            "walkable_count": 0,
            "api_calls_made": 0,
            "served_from_cache": True
        }
    }

    api_calls = 0
    total_places = 0
    walkable = 0
    all_from_cache = True

    for category, config in PLACE_CATEGORIES.items():
        places, from_cache = search_nearby_places(
            coords,
            category,
            config['radius_miles']
        )

        if not from_cache:
            api_calls += 1
            all_from_cache = False

        # Apply quality filter for dining only
        if category == 'dining':
            places = _filter_quality_dining(places)

        # Calculate walkable (within 0.5 miles)
        cat_walkable = sum(1 for p in places if p['distance_miles'] <= 0.5)
        walkable += cat_walkable

        # Get nearest distance
        nearest_dist = places[0]['distance_miles'] if places else None

        result[category] = {
            'count': len(places),
            'places': places,
            'nearest_distance': nearest_dist,
            'display_name': config['display_name']
        }

        total_places += len(places)

    result['summary'] = {
        'total_amenities': total_places,
        'walkable_count': walkable,
        'api_calls_made': api_calls,
        'served_from_cache': all_from_cache
    }

    return result


def calculate_convenience_score(amenities: Dict) -> Dict:
    """
    Calculate convenience score based on amenity availability.

    Scoring (tuned for suburban Loudoun County):
    - Has quality dining within 1.5 miles: +3 points
    - Has grocery within 2 miles: +3 points (was 1 mile - adjusted for suburbs)
    - Has shopping within 3 miles: +2 points
    - Has walkable options (<0.5 mi): +2 points

    Max score: 10

    Args:
        amenities: Result from get_neighborhood_amenities()

    Returns:
        Dict with score, rating, and highlights
    """
    score = 0
    highlights = []

    # Quality dining within 1.5 miles (+3)
    dining = amenities.get('dining', {})
    dining_count = dining.get('count', 0)
    dining_nearest = dining.get('nearest_distance')

    if dining_count > 0 and dining_nearest and dining_nearest <= 1.5:
        score += 3
        highlights.append(f"{dining_count} quality restaurants within 1.5 miles")

    # Grocery within 2 miles (+3) - adjusted for suburban reality
    grocery = amenities.get('grocery', {})
    grocery_count = grocery.get('count', 0)
    grocery_nearest = grocery.get('nearest_distance')

    if grocery_count > 0 and grocery_nearest and grocery_nearest <= 2.0:
        score += 3
        highlights.append(f"Grocery store {grocery_nearest:.1f} miles away")
    elif grocery_count > 0 and grocery_nearest and grocery_nearest <= 3.0:
        score += 2
        highlights.append(f"Grocery store {grocery_nearest:.1f} miles away")

    # Shopping within 3 miles (+2)
    shopping = amenities.get('shopping', {})
    shopping_count = shopping.get('count', 0)
    shopping_nearest = shopping.get('nearest_distance')

    if shopping_count > 0 and shopping_nearest and shopping_nearest <= 3.0:
        score += 2
        highlights.append(f"Shopping mall {shopping_nearest:.1f} miles away")

    # Walkable options (+2)
    walkable = amenities.get('summary', {}).get('walkable_count', 0)
    if walkable > 0:
        score += 2
        highlights.append(f"{walkable} places within walking distance (0.5 mi)")

    # Determine rating
    if score >= 8:
        rating = "Excellent"
    elif score >= 6:
        rating = "Good"
    elif score >= 4:
        rating = "Fair"
    else:
        rating = "Limited"

    return {
        'score': min(score, 10),  # Cap at 10
        'rating': rating,
        'highlights': highlights
    }


def generate_neighborhood_narrative(amenities: Dict, convenience: Dict) -> str:
    """
    Generate professional narrative about neighborhood amenities.

    Args:
        amenities: Result from get_neighborhood_amenities()
        convenience: Result from calculate_convenience_score()

    Returns:
        Professional narrative string
    """
    score = convenience.get('score', 0)
    rating = convenience.get('rating', 'Unknown')

    dining = amenities.get('dining', {})
    grocery = amenities.get('grocery', {})
    shopping = amenities.get('shopping', {})

    dining_count = dining.get('count', 0)
    grocery_nearest = grocery.get('nearest_distance')
    shopping_count = shopping.get('count', 0)

    if rating == "Excellent":
        narrative = (
            f"This property enjoys excellent neighborhood convenience with {dining_count} quality dining "
            f"options nearby. "
        )
        if grocery_nearest and grocery_nearest < 2.0:
            narrative += f"A grocery store is just {grocery_nearest:.1f} miles away, making daily errands easy. "
        if shopping_count > 0:
            narrative += "Shopping centers are also easily accessible. "
        narrative += "Residents benefit from a well-amenitized neighborhood."

    elif rating == "Good":
        narrative = (
            f"This location offers good access to neighborhood amenities with {dining_count} quality restaurants "
            f"within reach. "
        )
        if grocery_nearest:
            narrative += f"The nearest grocery store is {grocery_nearest:.1f} miles away. "
        narrative += "Most daily needs can be met with a short drive."

    elif rating == "Fair":
        narrative = (
            "This property has fair access to neighborhood amenities. "
        )
        if dining_count > 0:
            narrative += f"There are {dining_count} dining options in the area. "
        if grocery_nearest:
            narrative += f"Grocery shopping is {grocery_nearest:.1f} miles away. "
        narrative += "Some amenities may require a longer drive."

    else:  # Limited
        narrative = (
            "Neighborhood amenities are limited in this area, which is typical for more rural "
            "locations in Loudoun County. "
        )
        if grocery_nearest:
            narrative += f"The nearest grocery store is {grocery_nearest:.1f} miles away. "
        narrative += "Residents should plan trips for shopping and dining."

    return narrative


def analyze_neighborhood(coords: Tuple[float, float]) -> Dict:
    """
    Complete neighborhood amenity analysis.

    Main entry point combining all analysis functions.

    Args:
        coords: (latitude, longitude) tuple

    Returns:
        Complete analysis dict with amenities, score, and narrative
    """
    try:
        amenities = get_neighborhood_amenities(coords)
        convenience = calculate_convenience_score(amenities)
        narrative = generate_neighborhood_narrative(amenities, convenience)

        return {
            'available': True,
            'amenities': amenities,
            'convenience': convenience,
            'narrative': narrative
        }

    except Exception as e:
        print(f"Error in neighborhood analysis: {e}")
        return {
            'available': False,
            'error': str(e)
        }


def precache_demo_addresses() -> None:
    """
    Pre-cache neighborhood data for demo addresses.

    Run this once before demos to ensure fast responses and no API costs
    during live demonstrations.
    """
    demo_addresses = [
        ("43273 Clearnight Ter, Ashburn", (39.0406, -77.5043)),
        ("43500 Tuckaway Pl, Leesburg", (39.0889, -77.5350)),
        ("44031 Pipeline Plaza, Ashburn", (39.0048, -77.4891)),  # Near Metro
    ]

    print("=" * 60)
    print("PRE-CACHING NEIGHBORHOOD DATA FOR DEMO ADDRESSES")
    print("=" * 60)

    for address, coords in demo_addresses:
        print(f"\n📍 {address}")
        print(f"   Coords: {coords[0]:.4f}, {coords[1]:.4f}")

        result = analyze_neighborhood(coords)

        if result.get('available'):
            conv = result.get('convenience', {})
            summary = result.get('amenities', {}).get('summary', {})

            print(f"   Score: {conv.get('score', 0)}/10 ({conv.get('rating', 'Unknown')})")
            print(f"   Total amenities: {summary.get('total_amenities', 0)}")
            print(f"   API calls: {summary.get('api_calls_made', 0)}")
            print(f"   Cached: {summary.get('served_from_cache', False)}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")

    print("\n" + "=" * 60)
    print("Pre-caching complete!")
    print("=" * 60)


# Test function
def test_neighborhood_analysis():
    """Test the neighborhood analysis with a sample location."""
    # Test with Ashburn location near One Loudoun
    coords = (39.0406, -77.5043)

    print("=" * 60)
    print("NEIGHBORHOOD AMENITIES ANALYSIS TEST")
    print("=" * 60)
    print(f"\nLocation: {coords[0]:.4f}, {coords[1]:.4f}")

    result = analyze_neighborhood(coords)

    if result.get('available'):
        amenities = result.get('amenities', {})
        convenience = result.get('convenience', {})
        narrative = result.get('narrative', '')

        print(f"\n📊 Convenience Score: {convenience.get('score', 0)}/10")
        print(f"   Rating: {convenience.get('rating', 'Unknown')}")

        print(f"\n🍽️  Dining: {amenities.get('dining', {}).get('count', 0)} places")
        print(f"🛒 Grocery: {amenities.get('grocery', {}).get('count', 0)} places")
        print(f"🛍️  Shopping: {amenities.get('shopping', {}).get('count', 0)} places")

        print(f"\n📝 Narrative: {narrative}")

        print(f"\n📈 Summary:")
        summary = amenities.get('summary', {})
        print(f"   Total amenities: {summary.get('total_amenities', 0)}")
        print(f"   Walkable places: {summary.get('walkable_count', 0)}")
        print(f"   API calls made: {summary.get('api_calls_made', 0)}")
        print(f"   Served from cache: {summary.get('served_from_cache', False)}")

        if convenience.get('highlights'):
            print(f"\n✅ Highlights:")
            for h in convenience['highlights']:
                print(f"   • {h}")

    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown')}")

    print("\n" + "=" * 60)


def get_pharmacy_access(lat: float, lon: float, radius_miles: float = 5.0) -> Dict:
    """
    Get pharmacy access information for a location.

    Tool-callable wrapper for pharmacy search with 24-hour detection.

    Args:
        lat: Latitude of property
        lon: Longitude of property
        radius_miles: Search radius (default 5 miles)

    Returns:
        Dict with:
        - available: bool (any pharmacies found)
        - pharmacy_count: int
        - has_24_hour: bool
        - pharmacies: List of pharmacy details
        - nearest_24_hour: Dict or None
        - summary: Text summary
    """
    coords = (lat, lon)

    # Use existing search function
    results, from_cache = search_nearby_places(coords, 'pharmacy', radius_miles)

    # Find 24-hour pharmacies
    has_24_hour = any(p.get('is_24_hour', False) for p in results)

    # Get nearest 24-hour if available
    nearest_24_hour = None
    if has_24_hour:
        twenty_four_hr = [p for p in results if p.get('is_24_hour', False)]
        if twenty_four_hr:
            nearest_24_hour = min(twenty_four_hr,
                                 key=lambda p: p.get('distance_miles', float('inf')))

    # Generate summary
    if results:
        summary_parts = [f"{len(results)} pharmacies within {radius_miles} miles."]
        if has_24_hour:
            count_24hr = len([p for p in results if p.get('is_24_hour', False)])
            summary_parts.append(f"{count_24hr} are open 24 hours.")
            if nearest_24_hour:
                summary_parts.append(f"Nearest 24-hour: {nearest_24_hour['name']} at {nearest_24_hour['distance_miles']:.1f} mi.")
        else:
            summary_parts.append("No 24-hour pharmacies found in this radius.")
        if results:
            nearest = results[0]
            summary_parts.append(f"Nearest pharmacy: {nearest['name']} at {nearest['distance_miles']:.1f} mi.")
        summary = ' '.join(summary_parts)
    else:
        summary = f"No pharmacies found within {radius_miles} miles."

    return {
        'available': len(results) > 0,
        'pharmacy_count': len(results),
        'has_24_hour': has_24_hour,
        'pharmacies': results,
        'nearest_24_hour': nearest_24_hour,
        'from_cache': from_cache,
        'summary': summary
    }


if __name__ == "__main__":
    test_neighborhood_analysis()
