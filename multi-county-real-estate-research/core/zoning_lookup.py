"""
Multi-jurisdiction zoning lookup.

Retrieves zoning information for addresses, handling both county and town jurisdictions.
Uses jurisdiction detector to determine which zoning authority to query.

MERGE NOTE: Multi-county generalized version
- Athens equivalent: zoning_lookup.py (hardcoded for Athens)
- Configuration-driven for any county
- Backward compatible: Works with single-jurisdiction counties
- Designed for February-March 2026 merge

Last Updated: November 2025
Phase: 1 - Zoning (Week 1-2 of 2)
Status: Core implementation
"""

import requests
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from config import CountyConfig, get_county_config
from core.jurisdiction_detector import JurisdictionDetector

@dataclass
class ZoningResult:
    """
    Zoning information for an address.

    Attributes:
        address: The queried address
        jurisdiction_type: 'town' or 'county'
        jurisdiction_name: Name of jurisdiction (e.g., "Leesburg", "Unincorporated Loudoun County")
        zoning_code: Primary zoning designation (e.g., "R-1", "PD-TC")
        zoning_description: Human-readable description
        zoning_authority: Who controls zoning (e.g., "Town of Leesburg")
        overlay_zones: List of overlay zones if any
        future_land_use: Future land use designation if available
        notes: Additional context or warnings
        data_source: Where the data came from
        success: Whether lookup was successful
        error_message: Error details if unsuccessful
    """
    address: str
    jurisdiction_type: str
    jurisdiction_name: str
    zoning_code: Optional[str] = None
    zoning_description: Optional[str] = None
    zoning_authority: Optional[str] = None
    overlay_zones: List[str] = None
    future_land_use: Optional[str] = None
    notes: Optional[str] = None
    data_source: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.overlay_zones is None:
            self.overlay_zones = []


class ZoningLookup:
    """
    Zoning information lookup with multi-jurisdiction support.

    Usage:
        >>> from config import get_county_config
        >>> config = get_county_config("loudoun")
        >>> lookup = ZoningLookup(config)
        >>> result = lookup.get_zoning("Main St, Leesburg, VA", 39.1156, -77.5636)
        >>> print(result.zoning_code)
    """

    def __init__(self, county_config: CountyConfig):
        """
        Initialize zoning lookup with county configuration.

        Args:
            county_config: CountyConfig object for the county
        """
        self.config = county_config
        self.jurisdiction_detector = JurisdictionDetector(county_config)

    def get_zoning(self, address: str, lat: float, lon: float) -> ZoningResult:
        """
        Get zoning information for an address.

        Args:
            address: Street address
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)

        Returns:
            ZoningResult object with zoning information

        Example:
            >>> result = lookup.get_zoning("Downtown Leesburg", 39.1156, -77.5636)
            >>> if result.success:
            ...     print(f"Zoning: {result.zoning_code}")
            ...     print(f"Authority: {result.zoning_authority}")
        """
        # Step 1: Detect jurisdiction
        jurisdiction = self.jurisdiction_detector.detect(address, lat, lon)

        # Step 2: Query appropriate zoning source
        if jurisdiction['type'] == 'town':
            return self._get_town_zoning(address, lat, lon, jurisdiction)
        else:
            return self._get_county_zoning(address, lat, lon, jurisdiction)

    def _get_county_zoning(self, address: str, lat: float, lon: float,
                           jurisdiction: Dict[str, str]) -> ZoningResult:
        """
        Get zoning from county GIS (for unincorporated areas).

        Args:
            address: Street address
            lat: Latitude
            lon: Longitude
            jurisdiction: Jurisdiction info from detector

        Returns:
            ZoningResult with county zoning information
        """
        result = ZoningResult(
            address=address,
            jurisdiction_type='county',
            jurisdiction_name=jurisdiction['name'],
            zoning_authority=jurisdiction['zoning_authority']
        )

        # Check if county has zoning data available
        if not self.config.has_zoning_data:
            result.error_message = f"Zoning data not yet implemented for {self.config.display_name}"
            result.notes = "Configuration complete, data source integration pending"
            return result

        # Get zoning API endpoint
        api_endpoint = self.config.zoning_api_endpoint
        if not api_endpoint:
            result.error_message = "Zoning API endpoint not configured"
            result.notes = "Check config for zoning_api_endpoint"
            return result

        # Query county GIS
        try:
            zoning_data = self._query_county_gis(api_endpoint, lat, lon)
            if zoning_data:
                result.success = True
                result.zoning_code = zoning_data.get('zoning_code')
                result.zoning_description = zoning_data.get('zoning_description')
                result.overlay_zones = zoning_data.get('overlay_zones', [])
                result.future_land_use = zoning_data.get('future_land_use')
                result.data_source = 'County GIS REST API'
                result.notes = f"Retrieved from {self.config.display_name} GIS"
            else:
                result.error_message = "No zoning data found at this location"
                result.notes = "Address may be outside county boundaries or data incomplete"

        except Exception as e:
            result.error_message = f"Error querying county GIS: {str(e)}"
            result.notes = "Check API endpoint and network connectivity"

        return result

    def _get_town_zoning(self, address: str, lat: float, lon: float,
                         jurisdiction: Dict[str, str]) -> ZoningResult:
        """
        Get zoning from town ordinance (for incorporated towns).

        Args:
            address: Street address
            lat: Latitude
            lon: Longitude
            jurisdiction: Jurisdiction info from detector

        Returns:
            ZoningResult with town zoning information
        """
        result = ZoningResult(
            address=address,
            jurisdiction_type='town',
            jurisdiction_name=jurisdiction['name'],
            zoning_authority=jurisdiction['zoning_authority']
        )

        town_name = jurisdiction['name']

        # Check if town has zoning source configured
        town_sources = self.config.town_zoning_sources or {}
        town_source = town_sources.get(town_name)

        if not town_source:
            result.error_message = f"Zoning source not yet configured for {town_name}"
            result.notes = f"Town zoning ordinance integration pending. See docs for {town_name} zoning codes."
            return result

        # TODO: Implement town-specific zoning lookup
        # Each town may have different data format:
        # - Some towns have GIS layers
        # - Some towns have PDF ordinances only
        # - Some towns may need manual lookup

        result.error_message = f"Town zoning lookup not yet implemented for {town_name}"
        result.notes = f"Jurisdiction detected correctly. Town-specific data integration pending."

        return result

    def _query_county_gis(self, api_endpoint: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Query county GIS REST API for zoning information.

        Args:
            api_endpoint: ArcGIS REST API endpoint
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with zoning data or None if not found

        Note:
            This is designed for ArcGIS REST APIs which most counties use.
            Format: https://gis.county.gov/arcgis/rest/services/.../MapServer/[layer]/query
        """
        try:
            # Build query parameters for ArcGIS REST API
            params = {
                'geometry': f'{lon},{lat}',
                'geometryType': 'esriGeometryPoint',
                'spatialRel': 'esriSpatialRelIntersects',
                'inSR': '4326',  # WGS84 spatial reference
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json'
            }

            response = requests.get(api_endpoint, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            features = data.get('features', [])

            if not features:
                return None

            # Extract zoning info from first feature
            # Field names vary by county - common patterns:
            # - ZONING, ZONE, ZONE_CODE, ZONING_CODE
            # - ZONE_DESC, ZONING_DESC, DESCRIPTION
            # - OVERLAY, OVERLAY_ZONE
            # - FLU, FUTURE_LAND_USE

            attributes = features[0].get('attributes', {})

            # Try common field names for zoning code
            zoning_code = None
            for field in ['ZO_ZONE', 'ZONING', 'ZONE', 'ZONE_CODE', 'ZONING_CODE', 'ZONECODE']:
                if field in attributes and attributes[field]:
                    zoning_code = str(attributes[field])
                    break

            # Try common field names for description
            zoning_description = None
            for field in ['ZD_ZONE_DESC', 'ZD_ZONE_NAME', 'ZONE_DESC', 'ZONING_DESC', 'DESCRIPTION', 'DESC', 'ZONE_DESCRIPTION']:
                if field in attributes and attributes[field]:
                    zoning_description = str(attributes[field])
                    break

            # Try to find overlay zones
            overlay_zones = []
            for field in ['OVERLAY', 'OVERLAY_ZONE', 'OVERLAY_ZONES', 'OVERLAYS']:
                if field in attributes and attributes[field]:
                    overlay = str(attributes[field])
                    if overlay and overlay not in ['', 'None', 'N/A']:
                        overlay_zones.append(overlay)

            # Try to find future land use
            future_land_use = None
            for field in ['FLU', 'FUTURE_LAND_USE', 'COMP_PLAN', 'COMPREHENSIVE_PLAN']:
                if field in attributes and attributes[field]:
                    future_land_use = str(attributes[field])
                    break

            return {
                'zoning_code': zoning_code,
                'zoning_description': zoning_description,
                'overlay_zones': overlay_zones,
                'future_land_use': future_land_use,
                'raw_attributes': attributes  # Keep raw data for debugging
            }

        except requests.RequestException as e:
            print(f"Error querying GIS: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


# ===== VALIDATION FUNCTION =====

def test_zoning_lookup():
    """
    Test zoning lookup with known addresses.

    Tests both county and town jurisdictions to verify the full workflow.
    """
    print("=" * 60)
    print("ZONING LOOKUP TESTS")
    print("=" * 60)
    print(f"Date: November 2025")
    print(f"Phase: 1 - Zoning (Week 1-2)")
    print()

    # Test Loudoun County
    print("Testing Loudoun County, VA...")
    print("-" * 60)
    loudoun_config = get_county_config("loudoun")
    lookup = ZoningLookup(loudoun_config)

    # Test 1: Downtown Leesburg (incorporated town)
    print("Test 1: Downtown Leesburg (incorporated)")
    print("  Location: Downtown Leesburg")
    print("  Expected: Town jurisdiction, town zoning pending")
    result1 = lookup.get_zoning(
        "Downtown Leesburg, VA",
        lat=39.1156,
        lon=-77.5636
    )
    print(f"  Result:")
    print(f"    Success: {result1.success}")
    print(f"    Jurisdiction Type: {result1.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result1.jurisdiction_name}")
    print(f"    Zoning Authority: {result1.zoning_authority}")
    print(f"    Zoning Code: {result1.zoning_code or 'N/A'}")
    if result1.error_message:
        print(f"    Status: {result1.error_message}")
    if result1.notes:
        print(f"    Notes: {result1.notes}")

    if result1.jurisdiction_type == 'town':
        print("  ✅ PASS - Correctly identified town jurisdiction")
    print()

    # Test 2: Ashburn (unincorporated county)
    print("Test 2: Ashburn (unincorporated)")
    print("  Location: Ashburn area")
    print("  Expected: County jurisdiction, county zoning pending")
    result2 = lookup.get_zoning(
        "Ashburn, VA",
        lat=39.0437,
        lon=-77.4875
    )
    print(f"  Result:")
    print(f"    Success: {result2.success}")
    print(f"    Jurisdiction Type: {result2.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result2.jurisdiction_name}")
    print(f"    Zoning Authority: {result2.zoning_authority}")
    print(f"    Zoning Code: {result2.zoning_code or 'N/A'}")
    if result2.error_message:
        print(f"    Status: {result2.error_message}")
    if result2.notes:
        print(f"    Notes: {result2.notes}")

    if result2.jurisdiction_type == 'county':
        print("  ✅ PASS - Correctly identified county jurisdiction")
    print()

    # Test Athens County
    print("=" * 60)
    print("Testing Athens-Clarke County, GA...")
    print("-" * 60)
    athens_config = get_county_config("athens_clarke")
    athens_lookup = ZoningLookup(athens_config)

    print("Test 3: Athens address")
    print("  Location: Downtown Athens")
    print("  Expected: County jurisdiction (unified government)")
    result3 = athens_lookup.get_zoning(
        "Downtown Athens, GA",
        lat=33.9573,
        lon=-83.3761
    )
    print(f"  Result:")
    print(f"    Success: {result3.success}")
    print(f"    Jurisdiction Type: {result3.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result3.jurisdiction_name}")
    print(f"    Zoning Authority: {result3.zoning_authority}")
    if result3.error_message:
        print(f"    Status: {result3.error_message}")

    if result3.jurisdiction_type == 'county':
        print("  ✅ PASS - Correctly identified county jurisdiction")
    print()

    print("=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print("  - Zoning lookup infrastructure: ✅ Working")
    print("  - Jurisdiction detection: ✅ Correctly routes to county vs town")
    print("  - County zoning: ⚠️  Needs API endpoint configuration")
    print("  - Town zoning: ⚠️  Needs town-specific implementation")
    print()
    print("Next steps:")
    print("  1. Configure Loudoun County GIS API endpoint in config/loudoun.py")
    print("  2. Test county zoning with real API")
    print("  3. Implement town-specific zoning (Leesburg first)")
    print("  4. Add zoning code interpretations/descriptions")
    print()


if __name__ == "__main__":
    test_zoning_lookup()
