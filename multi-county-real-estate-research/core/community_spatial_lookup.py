"""
Spatial community lookup using GIS boundaries.

Matches property coordinates to community polygons using point-in-polygon queries.
Falls back to pattern matching if spatial lookup fails.
"""

import geopandas as gpd
from shapely.geometry import Point
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CommunitySpatialLookup:
    """Spatial lookup for community boundaries."""

    def __init__(self, boundaries_path: str = None):
        """Initialize with path to community boundaries GeoJSON."""
        if boundaries_path is None:
            # Default path
            base_path = Path(__file__).parent.parent
            boundaries_path = base_path / "data/loudoun/gis/community_boundaries.geojson"

        self.boundaries_path = Path(boundaries_path)
        self.gdf = None
        self._load_boundaries()

    def _load_boundaries(self):
        """Load community boundaries from GeoJSON."""
        try:
            self.gdf = gpd.read_file(self.boundaries_path)
            logger.info(f"Loaded {len(self.gdf)} community boundaries")
        except Exception as e:
            logger.error(f"Failed to load boundaries: {e}")
            self.gdf = None

    def get_community_by_location(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find community containing the given coordinates.

        Args:
            latitude: Property latitude (WGS84)
            longitude: Property longitude (WGS84)

        Returns:
            Dictionary with community info, or None if not found
        """
        if self.gdf is None:
            logger.warning("Boundaries not loaded, cannot perform spatial lookup")
            return None

        try:
            # Create point geometry
            point = Point(longitude, latitude)

            # Find communities containing this point
            matches = self.gdf[self.gdf.contains(point)]

            if len(matches) == 0:
                return None

            # Return first match (should only be one)
            match = matches.iloc[0]

            return {
                "name": match["name"],
                "subdivision_count": int(match["subdivision_count"]),
                "area_acres": float(match["area_acres"]),
                "centroid_lat": float(match["centroid_lat"]),
                "centroid_lon": float(match["centroid_lon"]),
                "match_type": "spatial",
                "confidence": "high"
            }

        except Exception as e:
            logger.error(f"Spatial lookup error: {e}")
            return None

    def get_nearest_community(
        self,
        latitude: float,
        longitude: float,
        max_distance_miles: float = 2.0
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """
        Find nearest community if point is not within any boundary.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            max_distance_miles: Maximum distance to search (miles)

        Returns:
            Tuple of (community_info, distance_miles) or None
        """
        if self.gdf is None:
            return None

        try:
            point = Point(longitude, latitude)

            # Calculate distances to all communities
            distances = self.gdf.geometry.distance(point)

            # Find nearest
            nearest_idx = distances.idxmin()
            nearest_distance = distances[nearest_idx]

            # Convert degrees to approximate miles (at this latitude, ~69 miles per degree)
            distance_miles = nearest_distance * 69

            if distance_miles > max_distance_miles:
                return None

            nearest = self.gdf.loc[nearest_idx]

            community_info = {
                "name": nearest["name"],
                "subdivision_count": int(nearest["subdivision_count"]),
                "area_acres": float(nearest["area_acres"]),
                "centroid_lat": float(nearest["centroid_lat"]),
                "centroid_lon": float(nearest["centroid_lon"]),
                "match_type": "nearest",
                "confidence": "medium"
            }

            return (community_info, distance_miles)

        except Exception as e:
            logger.error(f"Nearest community lookup error: {e}")
            return None

    def get_community_boundary(self, community_name: str) -> Optional[Dict[str, Any]]:
        """
        Get boundary geometry for a specific community.

        Args:
            community_name: Name of community

        Returns:
            GeoJSON-like dict with geometry, or None
        """
        if self.gdf is None:
            return None

        matches = self.gdf[self.gdf["name"] == community_name]

        if len(matches) == 0:
            return None

        match = matches.iloc[0]

        return {
            "type": "Feature",
            "properties": {
                "name": match["name"],
                "subdivision_count": int(match["subdivision_count"]),
                "area_acres": float(match["area_acres"])
            },
            "geometry": match["geometry"].__geo_interface__
        }

    def list_communities(self) -> List[str]:
        """Get list of all community names."""
        if self.gdf is None:
            return []
        return sorted(self.gdf["name"].tolist())

    def get_communities_in_bounds(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float
    ) -> List[Dict[str, Any]]:
        """
        Get all communities within a bounding box.

        Useful for map display optimization.
        """
        if self.gdf is None:
            return []

        from shapely.geometry import box
        bounds = box(min_lon, min_lat, max_lon, max_lat)

        matches = self.gdf[self.gdf.intersects(bounds)]

        return [
            {
                "name": row["name"],
                "centroid_lat": float(row["centroid_lat"]),
                "centroid_lon": float(row["centroid_lon"]),
                "area_acres": float(row["area_acres"])
            }
            for _, row in matches.iterrows()
        ]


# Cached instance for Streamlit
_cached_lookup = None

def get_cached_spatial_lookup() -> CommunitySpatialLookup:
    """Get or create cached spatial lookup instance."""
    global _cached_lookup
    if _cached_lookup is None:
        _cached_lookup = CommunitySpatialLookup()
    return _cached_lookup


# Convenience function for quick lookups
def lookup_community(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Quick lookup of community by coordinates.

    Returns community info if found within boundary,
    or nearest community within 2 miles if not.
    """
    lookup = get_cached_spatial_lookup()

    # Try direct spatial match first
    result = lookup.get_community_by_location(latitude, longitude)
    if result:
        return result

    # Fall back to nearest community
    nearest = lookup.get_nearest_community(latitude, longitude)
    if nearest:
        community_info, distance = nearest
        community_info["distance_miles"] = round(distance, 2)
        return community_info

    return None


if __name__ == "__main__":
    # Test the module
    print("Testing CommunitySpatialLookup")
    print("=" * 50)

    lookup = CommunitySpatialLookup()
    print(f"Loaded {len(lookup.gdf)} communities")

    # Test a known location (Brambleton)
    result = lookup.get_community_by_location(38.9753, -77.5328)
    if result:
        print(f"\nTest lookup (38.9753, -77.5328):")
        print(f"  Community: {result['name']}")
        print(f"  Match type: {result['match_type']}")
    else:
        print("\nTest lookup failed")
