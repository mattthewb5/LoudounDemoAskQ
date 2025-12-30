"""
VDOT Traffic Volume Analyzer for Loudoun County

Provides Average Daily Traffic (ADT) data for highways and collectors.
Data source: VDOT Bidirectional Traffic Volume (local GeoJSON extract)

Usage:
    analyzer = LoudounTrafficVolumeAnalyzer()
    result = analyzer.get_traffic_volume("LEESBURG PIKE", lat, lon)
    if result:
        print(f"ADT: {analyzer.format_adt(result['adt'])}")
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)

# Path to data files (relative to this module)
DATA_DIR = Path(__file__).parent.parent / "data" / "loudoun"
TRAFFIC_FILE = DATA_DIR / "gis" / "traffic" / "vdot_traffic_volume.geojson"
MAPPING_FILE = DATA_DIR / "config" / "vdot_road_mapping.json"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in miles.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def point_to_line_distance(point: Tuple[float, float], line_coords: List[List[float]]) -> float:
    """
    Calculate minimum distance from a point to a polyline in miles.

    Args:
        point: (lat, lon) tuple
        line_coords: List of [lon, lat] coordinate pairs (GeoJSON format)

    Returns:
        Minimum distance in miles
    """
    min_dist = float('inf')
    lat, lon = point

    for coord in line_coords:
        # GeoJSON uses [lon, lat] order
        line_lon, line_lat = coord[0], coord[1]
        dist = haversine_distance(lat, lon, line_lat, line_lon)
        if dist < min_dist:
            min_dist = dist

    return min_dist


class LoudounTrafficVolumeAnalyzer:
    """Analyzes traffic volume for roads near a property."""

    def __init__(self):
        """Initialize the analyzer and load data files."""
        self.traffic_data: List[Dict] = []
        self.road_mapping: Dict = {}
        self.data_loaded = False
        self._load_data()

    def _load_data(self) -> None:
        """Load traffic GeoJSON and road mapping."""
        # Load traffic data
        if TRAFFIC_FILE.exists():
            try:
                with open(TRAFFIC_FILE, 'r') as f:
                    data = json.load(f)
                    self.traffic_data = data.get('features', [])
                    logger.info(f"Loaded {len(self.traffic_data)} traffic segments")
            except Exception as e:
                logger.warning(f"Failed to load traffic data: {e}")
                self.traffic_data = []
        else:
            logger.warning(f"Traffic data file not found: {TRAFFIC_FILE}")

        # Load road mapping
        if MAPPING_FILE.exists():
            try:
                with open(MAPPING_FILE, 'r') as f:
                    self.road_mapping = json.load(f)
                    logger.info("Loaded road name mapping")
            except Exception as e:
                logger.warning(f"Failed to load road mapping: {e}")
                self.road_mapping = {}
        else:
            logger.warning(f"Road mapping file not found: {MAPPING_FILE}")

        self.data_loaded = bool(self.traffic_data)

    def get_traffic_volume(self, road_name: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get ADT for a road near the given coordinates.

        Args:
            road_name: Loudoun County road name (e.g., "LEESBURG PIKE")
            lat, lon: Property coordinates

        Returns:
            Dictionary with traffic data or None if not found:
            {
                'adt': 45000,
                'vdot_route': 'VA-7E',
                'vdot_route_name': 'R-VA SR00007EB',
                'data_source': 'VDOT Bidirectional Traffic Volume',
                'found_via': 'mapping' or 'coordinate_lookup'
            }
        """
        if not self.data_loaded:
            logger.warning("Traffic data not loaded")
            return None

        # Try mapping lookup first
        result = self._lookup_by_mapping(road_name, lat, lon)
        if result:
            return result

        # Fall back to coordinate lookup
        result = self._lookup_by_coordinates(lat, lon, radius_miles=0.5)
        if result:
            return result

        return None

    def _lookup_by_mapping(self, road_name: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Try to find ADT using road name mapping.

        Args:
            road_name: Loudoun County road name
            lat, lon: Property coordinates

        Returns:
            Traffic data dict or None
        """
        if not self.road_mapping:
            return None

        # Normalize road name for lookup
        road_upper = road_name.upper().strip()

        # Check highways first
        highways = self.road_mapping.get('highways', {})
        mapping_entry = highways.get(road_upper)

        # Check collectors if not found in highways
        if not mapping_entry:
            collectors = self.road_mapping.get('collectors', {})
            mapping_entry = collectors.get(road_upper)

        if not mapping_entry:
            # Try partial match
            for key in list(highways.keys()) + list(self.road_mapping.get('collectors', {}).keys()):
                if key in road_upper or road_upper in key:
                    mapping_entry = highways.get(key) or self.road_mapping.get('collectors', {}).get(key)
                    break

        if not mapping_entry:
            return None

        # Get VDOT route patterns to search for
        vdot_routes = mapping_entry.get('vdot_routes', [])
        vdot_codes = mapping_entry.get('vdot_codes', [])

        # Search traffic data for matching routes near the coordinates
        best_match = None
        best_distance = float('inf')

        for feature in self.traffic_data:
            props = feature.get('properties', {})
            route_common = props.get('ROUTE_COMMON_NAME', '')
            route_name = props.get('ROUTE_NAME', '')

            # Check if this feature matches any of our target routes
            matched = False
            for vdot_route in vdot_routes:
                if vdot_route in route_common:
                    matched = True
                    break

            if not matched:
                for vdot_code in vdot_codes:
                    if vdot_code in route_common:
                        matched = True
                        break

            if not matched:
                continue

            # Calculate distance to this road segment
            geometry = feature.get('geometry', {})
            coords = geometry.get('coordinates', [])

            if not coords:
                continue

            # Handle both LineString and MultiLineString
            if geometry.get('type') == 'MultiLineString':
                all_coords = [c for line in coords for c in line]
            else:
                all_coords = coords

            distance = point_to_line_distance((lat, lon), all_coords)

            # Keep the closest match within 5 miles
            if distance < best_distance and distance < 5.0:
                best_distance = distance
                best_match = {
                    'adt': props.get('ADT'),
                    'vdot_route': route_common,
                    'vdot_route_name': route_name,
                    'distance_to_segment': round(distance, 2),
                    'data_source': 'VDOT Bidirectional Traffic Volume',
                    'found_via': 'mapping'
                }

        return best_match

    def _lookup_by_coordinates(self, lat: float, lon: float, radius_miles: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Fallback: find nearest high-ADT road segment by coordinates.

        Args:
            lat, lon: Property coordinates
            radius_miles: Search radius

        Returns:
            Traffic data dict or None
        """
        best_match = None
        best_distance = radius_miles

        for feature in self.traffic_data:
            props = feature.get('properties', {})
            adt = props.get('ADT', 0)

            # Only consider roads with significant traffic
            if not adt or adt < 5000:
                continue

            geometry = feature.get('geometry', {})
            coords = geometry.get('coordinates', [])

            if not coords:
                continue

            # Handle both LineString and MultiLineString
            if geometry.get('type') == 'MultiLineString':
                all_coords = [c for line in coords for c in line]
            else:
                all_coords = coords

            distance = point_to_line_distance((lat, lon), all_coords)

            if distance < best_distance:
                best_distance = distance
                best_match = {
                    'adt': adt,
                    'vdot_route': props.get('ROUTE_COMMON_NAME', 'Unknown'),
                    'vdot_route_name': props.get('ROUTE_NAME', ''),
                    'distance_to_segment': round(distance, 2),
                    'data_source': 'VDOT Bidirectional Traffic Volume',
                    'found_via': 'coordinate_lookup'
                }

        return best_match

    def format_adt(self, adt: int) -> str:
        """
        Format ADT as human-readable string.

        Args:
            adt: Average Daily Traffic count

        Returns:
            Formatted string like "~45,000 vehicles/day"
        """
        if not adt:
            return "N/A"

        # Round to nearest thousand for cleaner display
        rounded = round(adt / 1000) * 1000
        return f"~{rounded:,} vehicles/day"

    def format_adt_full(self, adt: int) -> str:
        """
        Format ADT with full description.

        Args:
            adt: Average Daily Traffic count

        Returns:
            Formatted string like "~45,000 vehicles/day"
        """
        if not adt:
            return "N/A"

        rounded = round(adt / 1000) * 1000
        return f"~{rounded:,} vehicles/day"


def test_traffic_analyzer():
    """Test the traffic volume analyzer."""
    print("=" * 60)
    print("TRAFFIC VOLUME ANALYZER TEST")
    print("=" * 60)

    analyzer = LoudounTrafficVolumeAnalyzer()

    print(f"\nData loaded: {analyzer.data_loaded}")
    print(f"Traffic segments: {len(analyzer.traffic_data)}")
    print(f"Road mapping entries: {len(analyzer.road_mapping.get('highways', {})) + len(analyzer.road_mapping.get('collectors', {}))}")

    # Test coordinates near Leesburg (43422 Cloister Pl area)
    test_lat = 39.115
    test_lon = -77.564

    print(f"\n--- Test Location: ({test_lat}, {test_lon}) ---")

    # Test highway lookup
    print("\n1. Testing LEESBURG PIKE lookup:")
    result = analyzer.get_traffic_volume("LEESBURG PIKE", test_lat, test_lon)
    if result:
        print(f"   ADT: {analyzer.format_adt(result['adt'])} ({result['adt']:,})")
        print(f"   VDOT Route: {result['vdot_route']}")
        print(f"   Found via: {result['found_via']}")
        print(f"   Distance to segment: {result.get('distance_to_segment', 'N/A')} miles")
    else:
        print("   Not found")

    # Test US-15 lookup
    print("\n2. Testing JAMES MONROE HWY lookup:")
    result = analyzer.get_traffic_volume("JAMES MONROE HWY", test_lat, test_lon)
    if result:
        print(f"   ADT: {analyzer.format_adt(result['adt'])} ({result['adt']:,})")
        print(f"   VDOT Route: {result['vdot_route']}")
        print(f"   Found via: {result['found_via']}")
    else:
        print("   Not found")

    # Test collector lookup
    print("\n3. Testing LOUDOUN COUNTY PKWY lookup:")
    result = analyzer.get_traffic_volume("LOUDOUN COUNTY PKWY", test_lat, test_lon)
    if result:
        print(f"   ADT: {analyzer.format_adt(result['adt'])} ({result['adt']:,})")
        print(f"   VDOT Route: {result['vdot_route']}")
        print(f"   Found via: {result['found_via']}")
    else:
        print("   Not found")

    # Test coordinate fallback
    print("\n4. Testing coordinate fallback (unknown road):")
    result = analyzer.get_traffic_volume("SOME UNKNOWN ROAD", test_lat, test_lon)
    if result:
        print(f"   ADT: {analyzer.format_adt(result['adt'])} ({result['adt']:,})")
        print(f"   VDOT Route: {result['vdot_route']}")
        print(f"   Found via: {result['found_via']}")
    else:
        print("   Not found (expected - outside radius)")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_traffic_analyzer()
