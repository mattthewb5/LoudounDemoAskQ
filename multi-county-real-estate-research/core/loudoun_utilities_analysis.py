"""
Loudoun County Utilities Analysis Module

Provides power line proximity analysis for property assessment.
Uses official Loudoun County Major Power Lines GeoJSON data.

Data source: Loudoun County GIS
- 80 power line segments (LineString geometries)
- Voltage levels: 138kV, 230kV, 500kV
- Status: Built, Approved (tracks future infrastructure)
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

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


def point_to_segment_distance(
    point_lat: float,
    point_lon: float,
    seg_start_lat: float,
    seg_start_lon: float,
    seg_end_lat: float,
    seg_end_lon: float
) -> float:
    """
    Calculate the minimum distance from a point to a line segment.

    Uses projection to find the closest point on the segment,
    then calculates haversine distance to that point.

    Args:
        point_lat, point_lon: Coordinates of the point
        seg_start_lat, seg_start_lon: Segment start coordinates
        seg_end_lat, seg_end_lon: Segment end coordinates

    Returns:
        Distance in miles to the closest point on the segment
    """
    # Convert to a local coordinate system for projection calculation
    # Using the point as origin, approximate planar geometry for small distances

    # Vector from segment start to end
    dx = seg_end_lon - seg_start_lon
    dy = seg_end_lat - seg_start_lat

    # Vector from segment start to point
    px = point_lon - seg_start_lon
    py = point_lat - seg_start_lat

    # Calculate projection parameter t
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-12:
        # Segment is essentially a point
        return haversine_distance(point_lat, point_lon, seg_start_lat, seg_start_lon)

    # t is the projection of point onto the line, normalized to [0, 1] for the segment
    t = max(0, min(1, (px * dx + py * dy) / seg_len_sq))

    # Calculate the closest point on the segment
    closest_lon = seg_start_lon + t * dx
    closest_lat = seg_start_lat + t * dy

    return haversine_distance(point_lat, point_lon, closest_lat, closest_lon)


def point_to_linestring_distance(
    point_lat: float,
    point_lon: float,
    coordinates: List[List[float]]
) -> float:
    """
    Calculate minimum distance from a point to a LineString geometry.

    Args:
        point_lat, point_lon: Coordinates of the point
        coordinates: List of [lon, lat] coordinate pairs (GeoJSON format)

    Returns:
        Minimum distance in miles to any segment of the LineString
    """
    if len(coordinates) < 2:
        if len(coordinates) == 1:
            return haversine_distance(point_lat, point_lon, coordinates[0][1], coordinates[0][0])
        return float('inf')

    min_distance = float('inf')

    for i in range(len(coordinates) - 1):
        # GeoJSON coordinates are [lon, lat]
        seg_start_lon, seg_start_lat = coordinates[i]
        seg_end_lon, seg_end_lat = coordinates[i + 1]

        dist = point_to_segment_distance(
            point_lat, point_lon,
            seg_start_lat, seg_start_lon,
            seg_end_lat, seg_end_lon
        )

        min_distance = min(min_distance, dist)

    return min_distance


class PowerLineAnalyzer:
    """
    Analyzes proximity of properties to major power transmission lines.

    Features:
    - Distance calculation to nearest power lines
    - Voltage-based stratification (138kV, 230kV, 500kV)
    - Separate tracking of built vs approved (future) lines
    - Visual impact scoring (1-5 scale)

    Usage:
        # Option 1: Direct instantiation (loads from file)
        analyzer = PowerLineAnalyzer()

        # Option 2: Use cached factory (recommended for Streamlit apps)
        analyzer = get_cached_power_line_analyzer()
    """

    def __init__(self, geojson_path: Optional[str] = None, preloaded_data: Optional[List[Dict]] = None):
        """
        Initialize the PowerLineAnalyzer.

        Args:
            geojson_path: Path to Major_Power_Lines.geojson file.
                         If None, uses default location.
            preloaded_data: Optional list of pre-loaded power line dicts.
                           If provided, skips loading from disk (for cached usage).
        """
        self.power_lines: List[Dict] = []

        # Use pre-loaded data if provided (for caching)
        if preloaded_data is not None:
            self.power_lines = preloaded_data
            print(f"Power lines initialized from pre-loaded cache ({len(self.power_lines)} lines)")
            return

        if geojson_path is None:
            # Default path relative to this module
            module_dir = Path(__file__).parent.parent
            geojson_path = module_dir / "data" / "loudoun" / "utilities" / "Major_Power_Lines.geojson"

        self.geojson_path = Path(geojson_path)
        self._load_power_lines()

    def _load_power_lines(self) -> None:
        """Load and parse the power lines GeoJSON file."""
        if not self.geojson_path.exists():
            print(f"⚠️ Power lines file not found: {self.geojson_path}")
            return

        try:
            with open(self.geojson_path, 'r') as f:
                data = json.load(f)

            for feature in data.get('features', []):
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})

                if geom.get('type') != 'LineString':
                    continue

                self.power_lines.append({
                    'id': props.get('OBJECTID'),
                    'voltage': props.get('MA_VOLTAGE', 0),
                    'status': props.get('MA_STATUS', 'Unknown'),
                    'voltage_class': props.get('MA_CLASS', ''),
                    'updated': props.get('MA_UPD_DATE', ''),
                    'coordinates': geom.get('coordinates', [])
                })

            print(f"✅ Loaded {len(self.power_lines)} power lines")

        except Exception as e:
            print(f"❌ Error loading power lines: {e}")

    def analyze_proximity(self, lat: float, lon: float, radius_miles: float = 2.0) -> Dict:
        """
        Analyze power line proximity for a given location.

        Args:
            lat: Latitude of the property
            lon: Longitude of the property
            radius_miles: Maximum search radius (default 2.0 miles)

        Returns:
            Dict containing:
            - nearest_built_line: {distance_miles, voltage, line_id} or None
            - nearest_approved_line: {distance_miles, voltage, line_id} or None
            - lines_within_quarter_mile: count of lines within 0.25 miles
            - lines_within_half_mile: count of lines within 0.5 miles
            - lines_within_one_mile: count of lines within 1.0 miles
            - lines_within_two_miles: count of lines within 2.0 miles
            - visual_impact_score: 1-5 scale
            - visual_impact_level: text description
            - all_nearby_lines: list of all lines within radius with details
        """
        if not self.power_lines:
            return self._empty_result()

        nearby_lines = []

        for line in self.power_lines:
            distance = point_to_linestring_distance(lat, lon, line['coordinates'])

            if distance <= radius_miles:
                nearby_lines.append({
                    'line_id': line['id'],
                    'voltage': line['voltage'],
                    'status': line['status'],
                    'distance_miles': round(distance, 3)
                })

        # Sort by distance
        nearby_lines.sort(key=lambda x: x['distance_miles'])

        # Separate built vs approved
        built_lines = [l for l in nearby_lines if l['status'] == 'Built']
        approved_lines = [l for l in nearby_lines if l['status'] == 'Approved']

        # Find nearest of each type
        nearest_built = None
        if built_lines:
            nb = built_lines[0]
            nearest_built = {
                'distance_miles': nb['distance_miles'],
                'voltage': nb['voltage'],
                'line_id': nb['line_id']
            }

        nearest_approved = None
        if approved_lines:
            na = approved_lines[0]
            nearest_approved = {
                'distance_miles': na['distance_miles'],
                'voltage': na['voltage'],
                'line_id': na['line_id']
            }

        # Count lines at various radii
        lines_quarter = len([l for l in nearby_lines if l['distance_miles'] <= 0.25])
        lines_half = len([l for l in nearby_lines if l['distance_miles'] <= 0.5])
        lines_one = len([l for l in nearby_lines if l['distance_miles'] <= 1.0])
        lines_two = len([l for l in nearby_lines if l['distance_miles'] <= 2.0])

        # Calculate visual impact score
        impact_score, impact_level = self._calculate_visual_impact(nearby_lines)

        return {
            'nearest_built_line': nearest_built,
            'nearest_approved_line': nearest_approved,
            'lines_within_quarter_mile': lines_quarter,
            'lines_within_half_mile': lines_half,
            'lines_within_one_mile': lines_one,
            'lines_within_two_miles': lines_two,
            'visual_impact_score': impact_score,
            'visual_impact_level': impact_level,
            'all_nearby_lines': nearby_lines
        }

    def _calculate_visual_impact(self, nearby_lines: List[Dict]) -> Tuple[int, str]:
        """
        Calculate visual impact score based on voltage and distance.

        Scoring logic:
        - 5 (Very High): 500kV <0.25mi OR 230kV <0.15mi
        - 4 (High): 500kV 0.25-0.5mi OR 230kV 0.15-0.3mi
        - 3 (Moderate): 230kV 0.3-0.5mi OR 500kV 0.5-1.0mi
        - 2 (Low): Any line 0.5-1.0mi (not covered above)
        - 1 (None): No lines within 1.0mi

        Returns:
            Tuple of (score, level_text)
        """
        if not nearby_lines:
            return 1, "None"

        # Check for highest impact scenarios first
        for line in nearby_lines:
            dist = line['distance_miles']
            voltage = line['voltage']

            # Score 5: Very High impact
            if voltage >= 500 and dist < 0.25:
                return 5, "Very High"
            if voltage >= 230 and dist < 0.15:
                return 5, "Very High"

        for line in nearby_lines:
            dist = line['distance_miles']
            voltage = line['voltage']

            # Score 4: High impact
            if voltage >= 500 and 0.25 <= dist < 0.5:
                return 4, "High"
            if voltage >= 230 and 0.15 <= dist < 0.3:
                return 4, "High"

        for line in nearby_lines:
            dist = line['distance_miles']
            voltage = line['voltage']

            # Score 3: Moderate impact
            if voltage >= 230 and 0.3 <= dist < 0.5:
                return 3, "Moderate"
            if voltage >= 500 and 0.5 <= dist < 1.0:
                return 3, "Moderate"

        # Check for any lines within 1 mile
        lines_within_mile = [l for l in nearby_lines if l['distance_miles'] < 1.0]
        if lines_within_mile:
            return 2, "Low"

        # No significant impact
        return 1, "None"

    def _empty_result(self) -> Dict:
        """Return empty result when no data is available."""
        return {
            'nearest_built_line': None,
            'nearest_approved_line': None,
            'lines_within_quarter_mile': 0,
            'lines_within_half_mile': 0,
            'lines_within_one_mile': 0,
            'lines_within_two_miles': 0,
            'visual_impact_score': 1,
            'visual_impact_level': "None",
            'all_nearby_lines': [],
            'error': 'Power line data not available'
        }


# Module-level instance for convenience (legacy - prefer get_cached_power_line_analyzer)
_analyzer_instance: Optional[PowerLineAnalyzer] = None


def get_power_line_analyzer() -> PowerLineAnalyzer:
    """
    Get or create the singleton PowerLineAnalyzer instance.

    Note: This is the legacy method. For Streamlit apps, prefer
    get_cached_power_line_analyzer() which uses Streamlit caching.
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PowerLineAnalyzer()
    return _analyzer_instance


# =============================================================================
# CACHED FACTORY FUNCTION (Streamlit)
# =============================================================================

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

if _HAS_STREAMLIT:
    @st.cache_resource
    def get_cached_power_line_analyzer() -> PowerLineAnalyzer:
        """
        Get a cached PowerLineAnalyzer with pre-loaded data.

        Uses Streamlit's @cache_resource for persistent caching.
        First call loads power lines (~0.2 seconds).
        Subsequent calls return cached analyzer instantly.

        This is the recommended way to use PowerLineAnalyzer in
        Streamlit apps for best performance.

        Returns:
            Cached PowerLineAnalyzer instance
        """
        from core.loudoun_gis_data import get_cached_loudoun_power_lines

        print("Creating cached PowerLineAnalyzer...")
        power_lines = get_cached_loudoun_power_lines()
        analyzer = PowerLineAnalyzer(preloaded_data=power_lines)
        print("✓ PowerLineAnalyzer cached and ready")
        return analyzer

else:
    # Non-Streamlit fallback
    _cached_power_analyzer = None

    def get_cached_power_line_analyzer() -> PowerLineAnalyzer:
        """Get cached analyzer (non-Streamlit fallback)."""
        global _cached_power_analyzer
        if _cached_power_analyzer is None:
            from core.loudoun_gis_data import get_cached_loudoun_power_lines

            print("Creating cached PowerLineAnalyzer...")
            power_lines = get_cached_loudoun_power_lines()
            _cached_power_analyzer = PowerLineAnalyzer(preloaded_data=power_lines)
            print("✓ PowerLineAnalyzer cached and ready")
        return _cached_power_analyzer


def analyze_power_line_proximity(lat: float, lon: float) -> Dict:
    """
    Convenience function to analyze power line proximity.

    Uses cached analyzer for better performance in Streamlit apps.

    Args:
        lat: Latitude of the property
        lon: Longitude of the property

    Returns:
        Power line proximity analysis results
    """
    # Use cached analyzer for better performance
    analyzer = get_cached_power_line_analyzer()
    return analyzer.analyze_proximity(lat, lon)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("POWER LINE ANALYZER TEST")
    print("=" * 60)

    # Test with a sample location in Sterling, VA
    test_lat = 39.0062
    test_lon = -77.4286

    print(f"\nTest location: {test_lat}, {test_lon}")
    print("(Near Sterling, VA)")

    result = analyze_power_line_proximity(test_lat, test_lon)

    print(f"\nResults:")
    print(f"  Visual Impact: {result['visual_impact_score']}/5 ({result['visual_impact_level']})")

    if result['nearest_built_line']:
        nb = result['nearest_built_line']
        print(f"  Nearest built line: {nb['voltage']}kV at {nb['distance_miles']:.2f} miles")
    else:
        print(f"  Nearest built line: None within 2 miles")

    if result['nearest_approved_line']:
        na = result['nearest_approved_line']
        print(f"  Nearest approved line: {na['voltage']}kV at {na['distance_miles']:.2f} miles")
    else:
        print(f"  Nearest approved line: None within 2 miles")

    print(f"\n  Lines within 0.25 mi: {result['lines_within_quarter_mile']}")
    print(f"  Lines within 0.5 mi: {result['lines_within_half_mile']}")
    print(f"  Lines within 1.0 mi: {result['lines_within_one_mile']}")
    print(f"  Lines within 2.0 mi: {result['lines_within_two_miles']}")

    if result['all_nearby_lines']:
        print(f"\n  All nearby lines ({len(result['all_nearby_lines'])}):")
        for line in result['all_nearby_lines'][:5]:
            print(f"    - {line['voltage']}kV ({line['status']}) at {line['distance_miles']:.2f} mi")
