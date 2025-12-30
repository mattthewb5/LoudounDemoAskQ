#!/usr/bin/env python3
"""
Generate Road Context Data with Travel Times

One-time script to query Google Distance Matrix API and generate
static travel time data for major Loudoun County roads.

Usage:
    GOOGLE_MAPS_API_KEY=<key> python scripts/generate_road_context.py

Output:
    data/loudoun/config/road_context.json
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import googlemaps
except ImportError:
    print("ERROR: googlemaps library not installed. Run: pip install googlemaps")
    sys.exit(1)


# === CONFIGURATION ===

# Key destinations for travel time calculations
DESTINATIONS = {
    "tysons": {
        "name": "Tysons Corner",
        "address": "Tysons Corner Center, 1961 Chain Bridge Rd, McLean, VA 22102",
        "description": "Major employment & retail hub"
    },
    "dc": {
        "name": "Downtown DC",
        "address": "1600 K Street NW, Washington, DC 20006",
        "description": "Federal employment center"
    },
    "dulles": {
        "name": "Dulles Airport",
        "address": "1 Saarinen Cir, Dulles, VA 20166",
        "description": "Washington Dulles International (IAD)"
    },
    "reston": {
        "name": "Reston Town Center",
        "address": "11900 Market St, Reston, VA 20190",
        "description": "Tech corridor hub"
    }
}

# Toll roads in Loudoun County
TOLL_ROADS = [
    "DULLES GREENWAY",
    "GREENWAY",
    "DULLES TOLL RD",
    "DULLES ACCESS RD"
]

# Roads with heavy eastbound AM / westbound PM commute patterns
EASTBOUND_COMMUTE_ROADS = [
    "LEESBURG PIKE",
    "HARRY BYRD HWY",
    "DULLES GREENWAY",
    "GREENWAY",
    "DULLES TOLL RD",
    "DULLES ACCESS RD",
    "WAXPOOL RD",
    "RYAN RD",
    "OLD OX RD",
    "LEE JACKSON HWY",
    "JOHN MOSBY HWY"
]

# Priority highways to process (subset of road_mapping highways)
PRIORITY_HIGHWAYS = [
    "LEESBURG PIKE",
    "SULLY RD",
    "DULLES GREENWAY",
    "DULLES TOLL RD",
    "LEE JACKSON HWY",
    "JOHN MOSBY HWY",
    "JAMES MONROE HWY"
]

# Priority collectors to process
PRIORITY_COLLECTORS = [
    "LOUDOUN COUNTY PKWY",
    "WAXPOOL RD",
    "OLD OX RD",
    "CASCADES PKWY",
    "BELMONT RIDGE RD",
    "RYAN RD",
    "SYCOLIN RD",
    "EDWARDS FERRY RD"
]


def load_road_mapping() -> Dict:
    """Load the VDOT road mapping configuration."""
    mapping_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'loudoun', 'config', 'vdot_road_mapping.json'
    )
    with open(mapping_path, 'r') as f:
        return json.load(f)


def load_traffic_geojson() -> Dict:
    """Load the VDOT traffic volume GeoJSON."""
    geojson_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'loudoun', 'gis', 'traffic', 'vdot_traffic_volume.geojson'
    )
    with open(geojson_path, 'r') as f:
        return json.load(f)


def find_road_segments(road_name: str, road_config: Dict, geojson: Dict) -> List[Dict]:
    """
    Find all GeoJSON segments matching a road's VDOT routes.

    Returns list of matching feature geometries.
    """
    matching_segments = []

    # Get VDOT route patterns to search for
    vdot_routes = road_config.get('vdot_routes', [])
    vdot_codes = road_config.get('vdot_codes', [])
    vdot_aliases = road_config.get('vdot_aliases', [])

    # Build search patterns
    search_patterns = []
    for route in vdot_routes:
        # Handle patterns like "VA-7E", "VA-7W", "SR-7"
        # In GeoJSON, these appear as "R-VA107VA007EB" or similar
        base = route.replace('-', '').replace('E', '').replace('W', '').replace('N', '').replace('S', '')
        search_patterns.append(base.lower())
        search_patterns.append(route.lower())

    for code in vdot_codes:
        # Handle patterns like "SC-607N (Loudoun County)"
        search_patterns.append(code.lower())

    # Also search by road name in common name field
    search_patterns.append(road_name.lower())
    for alias in vdot_aliases:
        search_patterns.append(alias.lower())

    # Search through features
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        route_name = str(props.get('ROUTE_NAME', '')).lower()
        common_name = str(props.get('ROUTE_COMMON_NAME', '')).lower()

        # Check if any pattern matches
        for pattern in search_patterns:
            if pattern and (pattern in route_name or pattern in common_name):
                matching_segments.append(feature)
                break

    return matching_segments


def calculate_centroid(segments: List[Dict]) -> Optional[Tuple[float, float]]:
    """
    Calculate the centroid of all road segment coordinates.

    Returns (lat, lon) tuple or None if no valid coordinates.
    """
    all_coords = []

    for segment in segments:
        geometry = segment.get('geometry', {})
        coords = geometry.get('coordinates', [])

        # Handle LineString coordinates [[lon, lat], ...]
        if geometry.get('type') == 'LineString':
            for coord in coords:
                if len(coord) >= 2:
                    all_coords.append((coord[1], coord[0]))  # lat, lon

    if not all_coords:
        return None

    # Calculate centroid (simple average)
    avg_lat = sum(c[0] for c in all_coords) / len(all_coords)
    avg_lon = sum(c[1] for c in all_coords) / len(all_coords)

    return (round(avg_lat, 6), round(avg_lon, 6))


def get_next_tuesday_times() -> Tuple[datetime, datetime]:
    """
    Get the next Tuesday at 8:00 AM and 2:00 PM Eastern time.

    Returns (rush_hour_dt, offpeak_dt) as datetime objects.
    """
    now = datetime.now()

    # Find next Tuesday (weekday 1)
    days_until_tuesday = (1 - now.weekday()) % 7
    if days_until_tuesday == 0 and now.hour >= 8:
        days_until_tuesday = 7

    next_tuesday = now + timedelta(days=days_until_tuesday)

    rush_hour = next_tuesday.replace(hour=8, minute=0, second=0, microsecond=0)
    offpeak = next_tuesday.replace(hour=14, minute=0, second=0, microsecond=0)

    return rush_hour, offpeak


def query_travel_times(
    gmaps: googlemaps.Client,
    origin_coords: Tuple[float, float],
    destinations: Dict,
    rush_time: datetime,
    offpeak_time: datetime
) -> Dict[str, Dict]:
    """
    Query Google Distance Matrix API for travel times to all destinations.

    Returns dict mapping destination key to travel time info.
    """
    results = {}

    origin = f"{origin_coords[0]},{origin_coords[1]}"

    for dest_key, dest_info in destinations.items():
        try:
            # Rush hour query
            rush_result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[dest_info['address']],
                mode="driving",
                departure_time=rush_time,
                traffic_model="best_guess"
            )

            # Small delay to avoid rate limiting
            time.sleep(0.3)

            # Off-peak query
            offpeak_result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[dest_info['address']],
                mode="driving",
                departure_time=offpeak_time,
                traffic_model="best_guess"
            )

            time.sleep(0.3)

            # Parse results
            rush_element = rush_result['rows'][0]['elements'][0]
            offpeak_element = offpeak_result['rows'][0]['elements'][0]

            if rush_element['status'] == 'OK' and offpeak_element['status'] == 'OK':
                # Distance in miles (convert from meters)
                distance_meters = rush_element['distance']['value']
                distance_miles = round(distance_meters / 1609.34, 1)

                # Duration in traffic (minutes)
                rush_duration = rush_element.get('duration_in_traffic', rush_element['duration'])
                rush_min = round(rush_duration['value'] / 60)

                offpeak_duration = offpeak_element.get('duration_in_traffic', offpeak_element['duration'])
                offpeak_min = round(offpeak_duration['value'] / 60)

                results[dest_key] = {
                    "miles": distance_miles,
                    "rush_min": rush_min,
                    "offpeak_min": offpeak_min
                }
            else:
                results[dest_key] = {"error": "No route found"}

        except Exception as e:
            results[dest_key] = {"error": str(e)}

    return results


def get_route_number(road_name: str, road_config: Dict) -> str:
    """Extract display route number from road config."""
    vdot_routes = road_config.get('vdot_routes', [])
    if vdot_routes:
        # Return first route, cleaned up
        route = vdot_routes[0]
        # Convert "VA-7E" to "VA-7"
        route = route.rstrip('EWNS')
        return route
    return ""


def main():
    """Main script execution."""

    # Get API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("ERROR: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Usage: GOOGLE_MAPS_API_KEY=<key> python scripts/generate_road_context.py")
        sys.exit(1)

    print("=" * 60)
    print("ROAD CONTEXT GENERATION SCRIPT")
    print("=" * 60)
    print()

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)
    print("[OK] Google Maps client initialized")

    # Load data
    road_mapping = load_road_mapping()
    geojson = load_traffic_geojson()
    print(f"[OK] Loaded road mapping ({len(road_mapping.get('highways', {}))} highways, {len(road_mapping.get('collectors', {}))} collectors)")
    print(f"[OK] Loaded GeoJSON ({len(geojson.get('features', []))} features)")
    print()

    # Get departure times
    rush_time, offpeak_time = get_next_tuesday_times()
    print(f"Rush hour departure: {rush_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Off-peak departure:  {offpeak_time.strftime('%Y-%m-%d %H:%M')}")
    print()

    # Initialize output structure
    output = {
        "_metadata": {
            "generated": datetime.utcnow().isoformat() + "Z",
            "source": "Google Distance Matrix API",
            "rush_hour": rush_time.strftime('%A %H:%M'),
            "offpeak": offpeak_time.strftime('%A %H:%M'),
            "notes": "Travel times are estimates based on typical traffic patterns"
        },
        "destinations": {k: {"name": v["name"], "description": v["description"]}
                        for k, v in DESTINATIONS.items()},
        "roads": {},
        "_errors": []
    }

    # Process highways
    print("Processing highways...")
    highways = road_mapping.get('highways', {})

    # Use priority list, but dedupe (LEESBURG PIKE and HARRY BYRD HWY are same road)
    processed_routes = set()

    for road_name in PRIORITY_HIGHWAYS:
        if road_name not in highways:
            print(f"  [SKIP] {road_name} - not in mapping")
            continue

        road_config = highways[road_name]
        route_key = tuple(sorted(road_config.get('vdot_routes', [])))

        if route_key in processed_routes:
            print(f"  [SKIP] {road_name} - duplicate of already processed route")
            continue
        processed_routes.add(route_key)

        print(f"  Processing {road_name}...")

        # Find segments
        segments = find_road_segments(road_name, road_config, geojson)
        if not segments:
            print(f"    [WARN] No VDOT segments found")
            output['_errors'].append(f"{road_name}: No VDOT segments found")
            continue

        print(f"    Found {len(segments)} segments")

        # Calculate centroid
        centroid = calculate_centroid(segments)
        if not centroid:
            print(f"    [WARN] Could not calculate centroid")
            output['_errors'].append(f"{road_name}: Could not calculate centroid")
            continue

        print(f"    Centroid: {centroid}")

        # Query travel times
        travel_times = query_travel_times(gmaps, centroid, DESTINATIONS, rush_time, offpeak_time)

        # Build road entry
        is_toll = road_name in TOLL_ROADS
        is_eastbound = road_name in EASTBOUND_COMMUTE_ROADS

        output['roads'][road_name] = {
            "route_number": get_route_number(road_name, road_config),
            "toll": is_toll,
            "commute_pattern": "Heavy eastbound AM, westbound PM" if is_eastbound else "Varies by segment",
            "midpoint_coords": list(centroid),
            "travel_times": travel_times
        }

        # Show sample result
        if 'tysons' in travel_times and 'error' not in travel_times['tysons']:
            t = travel_times['tysons']
            print(f"    -> Tysons: {t['miles']}mi, {t['rush_min']}min rush / {t['offpeak_min']}min off-peak")

    print()

    # Process priority collectors
    print("Processing collectors...")
    collectors = road_mapping.get('collectors', {})

    for road_name in PRIORITY_COLLECTORS:
        if road_name not in collectors:
            print(f"  [SKIP] {road_name} - not in mapping")
            continue

        road_config = collectors[road_name]

        print(f"  Processing {road_name}...")

        # Find segments
        segments = find_road_segments(road_name, road_config, geojson)
        if not segments:
            print(f"    [WARN] No VDOT segments found")
            output['_errors'].append(f"{road_name}: No VDOT segments found")
            continue

        print(f"    Found {len(segments)} segments")

        # Calculate centroid
        centroid = calculate_centroid(segments)
        if not centroid:
            print(f"    [WARN] Could not calculate centroid")
            output['_errors'].append(f"{road_name}: Could not calculate centroid")
            continue

        print(f"    Centroid: {centroid}")

        # Query travel times
        travel_times = query_travel_times(gmaps, centroid, DESTINATIONS, rush_time, offpeak_time)

        # Build road entry
        is_toll = road_name in TOLL_ROADS
        is_eastbound = road_name in EASTBOUND_COMMUTE_ROADS

        output['roads'][road_name] = {
            "route_number": get_route_number(road_name, road_config),
            "toll": is_toll,
            "commute_pattern": "Heavy eastbound AM, westbound PM" if is_eastbound else "Local collector",
            "midpoint_coords": list(centroid),
            "travel_times": travel_times
        }

        # Show sample result
        if 'tysons' in travel_times and 'error' not in travel_times['tysons']:
            t = travel_times['tysons']
            print(f"    -> Tysons: {t['miles']}mi, {t['rush_min']}min rush / {t['offpeak_min']}min off-peak")

    print()

    # Save output
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'loudoun', 'config', 'road_context.json'
    )

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Roads processed: {len(output['roads'])}")
    print(f"Errors: {len(output['_errors'])}")
    print(f"Output saved to: {output_path}")
    print()

    # API cost estimate
    # Distance Matrix: $5 per 1000 elements (origins x destinations)
    # We query 2 times (rush + offpeak) per road per destination
    num_roads = len(output['roads'])
    num_destinations = len(DESTINATIONS)
    total_elements = num_roads * num_destinations * 2
    estimated_cost = (total_elements / 1000) * 5

    print(f"API elements used: {total_elements}")
    print(f"Estimated API cost: ${estimated_cost:.2f}")


if __name__ == "__main__":
    main()
