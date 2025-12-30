#!/usr/bin/env python3
"""
Athens-Clarke County School District Lookup Tool

This script takes an address in Athens-Clarke County, Georgia and returns
which elementary, middle, and high school attendance zones it belongs to.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

try:
    from shapely.geometry import Point, shape
    from shapely.prepared import prep
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("Warning: shapely not installed. Install with: pip install shapely")

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("Warning: geopy not installed. Install with: pip install geopy")


@dataclass
class SchoolAssignment:
    """Represents a school assignment for an address"""
    elementary: Optional[str] = None
    middle: Optional[str] = None
    high: Optional[str] = None
    address_normalized: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddressNormalizer:
    """Handles address normalization for better matching"""

    # Common abbreviations and their full forms
    STREET_SUFFIXES = {
        'st': 'street',
        'ave': 'avenue',
        'rd': 'road',
        'dr': 'drive',
        'ln': 'lane',
        'ct': 'court',
        'cir': 'circle',
        'blvd': 'boulevard',
        'pkwy': 'parkway',
        'pl': 'place',
        'ter': 'terrace',
        'way': 'way'
    }

    DIRECTIONALS = {
        'n': 'north',
        's': 'south',
        'e': 'east',
        'w': 'west',
        'ne': 'northeast',
        'nw': 'northwest',
        'se': 'southeast',
        'sw': 'southwest'
    }

    @classmethod
    def normalize(cls, address: str) -> str:
        """
        Normalize an address for consistent matching

        Args:
            address: Raw address string

        Returns:
            Normalized address string
        """
        # Convert to lowercase
        addr = address.lower().strip()

        # Remove extra whitespace
        addr = re.sub(r'\s+', ' ', addr)

        # Remove punctuation except spaces and numbers
        addr = re.sub(r'[^\w\s]', '', addr)

        # Split into parts
        parts = addr.split()
        normalized_parts = []

        for part in parts:
            # Expand street suffixes
            if part in cls.STREET_SUFFIXES:
                normalized_parts.append(cls.STREET_SUFFIXES[part])
            # Expand directionals
            elif part in cls.DIRECTIONALS:
                normalized_parts.append(cls.DIRECTIONALS[part])
            else:
                normalized_parts.append(part)

        return ' '.join(normalized_parts)


class SchoolDistrictLookup:
    """Main class for looking up school districts by address"""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the lookup tool

        Args:
            data_dir: Directory containing GeoJSON zone files
        """
        self.data_dir = data_dir
        self.zones = {
            'elementary': None,
            'middle': None,
            'high': None
        }
        self.prepared_zones = {
            'elementary': [],
            'middle': [],
            'high': []
        }

        # Initialize geocoder
        if GEOPY_AVAILABLE:
            self.geocoder = Nominatim(user_agent="athens_school_lookup")
        else:
            self.geocoder = None
            print("Warning: Geocoding not available. Install geopy.")

        # Load zone data
        self._load_zones()

    def _load_zones(self):
        """Load school zone GeoJSON files"""
        zone_files = {
            'elementary': ['elementary_zones.geojson', 'elementary-school-attendance-zones.geojson', 'elem_zones.geojson'],
            'middle': ['middle_zones.geojson', 'middle-school-attendance-zones.geojson', 'mid_zones.geojson'],
            'high': ['high_zones.geojson', 'high-school-attendance-zones.geojson', 'hs_zones.geojson']
        }

        for level, possible_files in zone_files.items():
            for filename in possible_files:
                filepath = os.path.join(self.data_dir, filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r') as f:
                            self.zones[level] = json.load(f)
                        print(f"✓ Loaded {level} zones from {filename}")

                        # Prepare geometries for faster spatial queries
                        if SHAPELY_AVAILABLE and 'features' in self.zones[level]:
                            for feature in self.zones[level]['features']:
                                geom = shape(feature['geometry'])
                                prepared = prep(geom)
                                self.prepared_zones[level].append({
                                    'geometry': prepared,
                                    'properties': feature['properties']
                                })
                        break
                    except Exception as e:
                        print(f"✗ Error loading {filename}: {e}")

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert an address to latitude/longitude coordinates

        Args:
            address: Address string

        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not self.geocoder:
            print("Geocoder not available")
            return None

        # Add Athens, GA if not already included
        if 'athens' not in address.lower():
            address = f"{address}, Athens, GA"

        try:
            location = self.geocoder.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            else:
                print(f"Could not geocode address: {address}")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error: {e}")
            return None

    def find_zone(self, latitude: float, longitude: float, level: str) -> Optional[str]:
        """
        Find which school zone a point falls into

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            level: School level ('elementary', 'middle', or 'high')

        Returns:
            School name or None if not found
        """
        if not SHAPELY_AVAILABLE:
            print("Shapely not available for spatial queries")
            return None

        point = Point(longitude, latitude)

        # Use prepared geometries for faster lookup
        for zone in self.prepared_zones.get(level, []):
            if zone['geometry'].contains(point):
                # Try to find school name in properties
                props = zone['properties']
                # Common field names for school names
                name_fields = ['school', 'name', 'SCHOOL', 'NAME', 'School_Name',
                              'SCHOOL_NAME', 'SchoolName', 'school_name']

                for field in name_fields:
                    if field in props and props[field]:
                        return props[field]

                # If no name field found, return first property value
                if props:
                    return str(list(props.values())[0])

        return None

    def lookup_school_district(self, address: str) -> SchoolAssignment:
        """
        Look up school district assignment for an address

        Args:
            address: Street address in Athens-Clarke County

        Returns:
            SchoolAssignment object with elementary, middle, and high school
        """
        result = SchoolAssignment()

        # Normalize the address
        normalized_addr = AddressNormalizer.normalize(address)
        result.address_normalized = normalized_addr

        # Geocode the address
        coords = self.geocode_address(address)
        if not coords:
            print(f"Unable to geocode address: {address}")
            return result

        result.latitude, result.longitude = coords
        print(f"Geocoded to: {result.latitude:.6f}, {result.longitude:.6f}")

        # Look up each school level
        if SHAPELY_AVAILABLE:
            result.elementary = self.find_zone(result.latitude, result.longitude, 'elementary')
            result.middle = self.find_zone(result.latitude, result.longitude, 'middle')
            result.high = self.find_zone(result.latitude, result.longitude, 'high')
        else:
            print("Cannot perform spatial lookup without shapely library")

        return result


def print_school_assignment(address: str, assignment: SchoolAssignment):
    """Pretty print school assignment results"""
    print("\n" + "=" * 70)
    print(f"School Assignment for: {address}")
    print("=" * 70)

    if assignment.latitude and assignment.longitude:
        print(f"Location: {assignment.latitude:.6f}, {assignment.longitude:.6f}")

    if assignment.address_normalized:
        print(f"Normalized: {assignment.address_normalized}")

    print()
    print(f"Elementary School: {assignment.elementary or 'Not found'}")
    print(f"Middle School:     {assignment.middle or 'Not found'}")
    print(f"High School:       {assignment.high or 'Not found'}")
    print("=" * 70)


def main():
    """Main function to run the lookup tool"""
    print("Athens-Clarke County School District Lookup Tool")
    print()

    # Initialize lookup
    lookup = SchoolDistrictLookup()

    # Check if we have data loaded
    if not any(lookup.zones.values()):
        print("\n⚠ WARNING: No school zone data found!")
        print("\nPlease download school zone GeoJSON files from:")
        print("https://data-athensclarke.opendata.arcgis.com/")
        print("\nSearch for 'school attendance zone' and download as GeoJSON.")
        print("Save the files to the 'data/' directory with names:")
        print("  - elementary_zones.geojson")
        print("  - middle_zones.geojson")
        print("  - high_zones.geojson")
        print("\nContinuing with geocoding only...\n")

    # Test addresses
    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    print("Testing with provided addresses:")
    print()

    for address in test_addresses:
        assignment = lookup.lookup_school_district(address)
        print_school_assignment(address, assignment)
        print()


if __name__ == "__main__":
    # Check dependencies
    if not SHAPELY_AVAILABLE or not GEOPY_AVAILABLE:
        print("\nMissing dependencies! Install with:")
        print("  pip install shapely geopy")
        print()

    main()
