"""
Loudoun County Metro Proximity Analysis Module

Provides Silver Line Metro station proximity analysis for property assessment.
Calculates distances to all 4 Loudoun County Metro stations and provides
accessibility tier classification.

Data source: WMATA Silver Line stations in Loudoun County
Stations: Ashburn, Loudoun Gateway, Innovation Center, Dulles Airport
"""

import math
from typing import Dict, List, Optional, Tuple

# Silver Line Metro stations in Loudoun County with verified coordinates
# Source: WMATA / Google Maps verification
LOUDOUN_METRO_STATIONS = [
    {
        "name": "Ashburn",
        "lat": 39.0057,
        "lon": -77.4910,
        "location": "Route 772 - Moorefield",
        "opened": "November 2022"
    },
    {
        "name": "Loudoun Gateway",
        "lat": 38.9556,
        "lon": -77.4377,
        "location": "Route 606 - Near Airport",
        "opened": "November 2022"
    },
    {
        "name": "Innovation Center",
        "lat": 38.9614,
        "lon": -77.4143,
        "location": "Route 28",
        "opened": "November 2022"
    },
    {
        "name": "Dulles Airport",
        "lat": 38.9531,
        "lon": -77.4483,
        "location": "Washington Dulles International Airport",
        "opened": "November 2022"
    }
]

# Accessibility tier definitions
ACCESSIBILITY_TIERS = {
    "Walk-to-Metro": {
        "max_miles": 0.5,
        "description": "Premium walkable location",
        "score_impact": "very_positive",
        "icon": "🟢"
    },
    "Bike-to-Metro": {
        "max_miles": 1.5,
        "description": "Easy bike or short drive",
        "score_impact": "very_positive",
        "icon": "🟢"
    },
    "Metro-Accessible": {
        "max_miles": 5.0,
        "description": "Convenient drive to Metro",
        "score_impact": "positive",
        "icon": "🟡"
    },
    "Metro-Available": {
        "max_miles": 10.0,
        "description": "Metro access requires planning",
        "score_impact": "neutral",
        "icon": "🟠"
    },
    "Metro-Distant": {
        "max_miles": float('inf'),
        "description": "Metro not practical for daily commute",
        "score_impact": "negative",
        "icon": "🔴"
    }
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Coordinates of first point (degrees)
        lat2, lon2: Coordinates of second point (degrees)

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def load_metro_stations() -> List[Dict]:
    """
    Load Metro station data.

    Returns:
        List of station dictionaries with name, coordinates, and metadata
    """
    return LOUDOUN_METRO_STATIONS.copy()


def calculate_metro_proximity(property_coords: Tuple[float, float]) -> Dict:
    """
    Calculate distance from property to all Metro stations.

    Args:
        property_coords: (latitude, longitude) tuple of property location

    Returns:
        Dictionary containing:
        - nearest_station: Name of closest station
        - distance_miles: Distance to nearest station in miles
        - all_stations: List of all stations with distances, sorted by distance
    """
    prop_lat, prop_lon = property_coords

    # Calculate distance to each station
    station_distances = []
    for station in LOUDOUN_METRO_STATIONS:
        distance = haversine_distance(
            prop_lat, prop_lon,
            station["lat"], station["lon"]
        )
        station_distances.append({
            "name": station["name"],
            "distance_miles": round(distance, 2),
            "location": station["location"],
            "lat": station["lat"],
            "lon": station["lon"]
        })

    # Sort by distance
    station_distances.sort(key=lambda x: x["distance_miles"])

    nearest = station_distances[0]

    return {
        "nearest_station": nearest["name"],
        "distance_miles": nearest["distance_miles"],
        "nearest_location": nearest["location"],
        "all_stations": station_distances
    }


def get_accessibility_tier(distance_miles: float) -> Dict:
    """
    Classify property based on Metro accessibility tier.

    Args:
        distance_miles: Distance to nearest Metro station in miles

    Returns:
        Dictionary containing:
        - tier: Tier name (e.g., "Metro-Accessible")
        - tier_description: Human-readable description
        - score_impact: Impact on property score
        - icon: Visual indicator emoji
    """
    for tier_name, tier_info in ACCESSIBILITY_TIERS.items():
        if distance_miles <= tier_info["max_miles"]:
            return {
                "tier": tier_name,
                "tier_description": tier_info["description"],
                "score_impact": tier_info["score_impact"],
                "icon": tier_info["icon"]
            }

    # Fallback (shouldn't reach here)
    return {
        "tier": "Metro-Distant",
        "tier_description": ACCESSIBILITY_TIERS["Metro-Distant"]["description"],
        "score_impact": "negative",
        "icon": "🔴"
    }


def estimate_drive_time(distance_miles: float) -> Dict:
    """
    Estimate drive time to Metro station.

    Uses 25 mph average for local roads (conservative, accounts for traffic lights).

    Args:
        distance_miles: Distance to station in miles

    Returns:
        Dictionary containing:
        - minutes: Estimated drive time in minutes
        - display: Formatted display string
        - rush_hour_note: Note about peak hour variations
    """
    # 25 mph average = 0.417 miles per minute = 2.4 minutes per mile
    avg_speed_mph = 25
    minutes = (distance_miles / avg_speed_mph) * 60

    # Round to nearest minute, minimum 1
    minutes_rounded = max(1, round(minutes))

    # Calculate rush hour estimate (add 50-100% for peak hours)
    rush_hour_min = round(minutes * 1.5)
    rush_hour_max = round(minutes * 2.0)

    # Format display
    if minutes_rounded <= 2:
        display = "< 2 min"
    else:
        display = f"~{minutes_rounded} min"

    return {
        "minutes": minutes_rounded,
        "display": display,
        "rush_hour_note": f"May be {rush_hour_min}-{rush_hour_max} min during peak hours" if distance_miles > 0.5 else "Walking distance"
    }


def generate_metro_narrative(proximity_data: Dict, tier_data: Dict) -> str:
    """
    Generate professional narrative about Metro access.

    Args:
        proximity_data: Result from calculate_metro_proximity()
        tier_data: Result from get_accessibility_tier()

    Returns:
        Professional narrative string suitable for property reports
    """
    station = proximity_data["nearest_station"]
    distance = proximity_data["distance_miles"]
    tier = tier_data["tier"]

    if tier == "Walk-to-Metro":
        walk_time = round(distance * 20)  # ~20 min/mile walking pace
        return (
            f"This property offers exceptional Metro access at just {distance:.1f} miles "
            f"from {station} station - approximately a {walk_time}-minute walk. "
            f"Walk-to-Metro properties command premium valuations and offer "
            f"car-optional living for DC commuters. The Silver Line provides "
            f"direct access to Tysons, Arlington, and downtown Washington DC."
        )

    elif tier == "Bike-to-Metro":
        bike_time = round(distance * 5)  # ~5 min/mile biking pace
        drive_time = estimate_drive_time(distance)
        return (
            f"This property is {distance:.1f} miles from {station} station, "
            f"an easy {bike_time}-minute bike ride or {drive_time['display']} drive. "
            f"Bike-to-Metro locations offer flexibility for commuters and benefit "
            f"from Silver Line connectivity to Tysons, Arlington, and DC. "
            f"Properties in this tier typically see strong appreciation."
        )

    elif tier == "Metro-Accessible":
        drive_time = estimate_drive_time(distance)
        return (
            f"This property is {distance:.1f} miles from {station} station, "
            f"approximately {drive_time['display']} by car. The Silver Line "
            f"provides direct access to Tysons Corner, Arlington, and downtown "
            f"Washington DC, making this an attractive location for commuters. "
            f"{drive_time['rush_hour_note']}."
        )

    elif tier == "Metro-Available":
        drive_time = estimate_drive_time(distance)
        return (
            f"The nearest Metro station ({station}) is {distance:.1f} miles away, "
            f"approximately {drive_time['display']} by car. While Metro access "
            f"requires some planning, the Silver Line does provide connectivity "
            f"to the broader DC region. This distance is typical for suburban "
            f"Loudoun County properties."
        )

    else:  # Metro-Distant
        return (
            f"The nearest Metro station ({station}) is {distance:.1f} miles away. "
            f"While Metro access is limited from this location, the property may "
            f"benefit from a more rural setting, larger lot sizes, or proximity "
            f"to other employment centers. Consider commute alternatives such as "
            f"commuter bus routes or remote work arrangements."
        )


def analyze_metro_access(property_coords: Tuple[float, float]) -> Dict:
    """
    Complete Metro access analysis for a property.

    This is the main entry point for Metro analysis, combining all metrics.

    Args:
        property_coords: (latitude, longitude) tuple of property location

    Returns:
        Dictionary containing complete Metro access analysis:
        - proximity: Distance data for all stations
        - tier: Accessibility classification
        - drive_time: Estimated travel time
        - narrative: Professional description
    """
    try:
        proximity = calculate_metro_proximity(property_coords)
        tier = get_accessibility_tier(proximity["distance_miles"])
        drive_time = estimate_drive_time(proximity["distance_miles"])
        narrative = generate_metro_narrative(proximity, tier)

        return {
            "available": True,
            "proximity": proximity,
            "tier": tier,
            "drive_time": drive_time,
            "narrative": narrative
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


# Test function for validation
def test_metro_analysis():
    """Test the Metro analysis with sample addresses."""
    test_cases = [
        # Close to Ashburn Metro
        ("44031 Pipeline Plaza, Ashburn", (39.0048, -77.4891)),
        # Medium distance - Leesburg area
        ("43500 Tuckaway Pl, Leesburg", (39.0889, -77.5350)),
        # Far from Metro - western Leesburg
        ("40272 Thomas Mill Rd, Leesburg", (39.1150, -77.6200)),
    ]

    print("=" * 60)
    print("METRO PROXIMITY ANALYSIS TEST")
    print("=" * 60)

    for address, coords in test_cases:
        print(f"\n📍 {address}")
        print(f"   Coordinates: {coords[0]:.4f}, {coords[1]:.4f}")

        result = analyze_metro_access(coords)

        if result["available"]:
            prox = result["proximity"]
            tier = result["tier"]
            drive = result["drive_time"]

            print(f"   Nearest Station: {prox['nearest_station']}")
            print(f"   Distance: {prox['distance_miles']:.1f} miles")
            print(f"   Drive Time: {drive['display']}")
            print(f"   Tier: {tier['icon']} {tier['tier']} - {tier['tier_description']}")

            print(f"\n   All Stations:")
            for station in prox['all_stations']:
                print(f"   • {station['name']}: {station['distance_miles']:.1f} mi")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_metro_analysis()
