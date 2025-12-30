"""
ATTOM Data API Client
Fetches property data and comparable sales from ATTOM Data API.

API Documentation: https://api.gateway.attomdata.com/propertyapi/v1.0.0/
"""

import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class AVMResult:
    """Automated Valuation Model result from ATTOM."""
    value: int
    value_low: Optional[int] = None
    value_high: Optional[int] = None
    confidence_score: Optional[float] = None
    as_of_date: Optional[str] = None
    source: str = "ATTOM AVM"


@dataclass
class PropertyData:
    """Property information from ATTOM."""
    address: str
    city: str
    state: str
    zipcode: str
    latitude: float
    longitude: float
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    sqft_source: Optional[str] = None  # 'Tax Records', 'MLS', 'Manual Override'
    year_built: Optional[int] = None
    lot_size: Optional[int] = None
    property_type: Optional[str] = None
    subdivision: Optional[str] = None  # Subdivision/neighborhood name
    apn: Optional[str] = None  # Assessor's Parcel Number (for sales lookup)
    last_sale_price: Optional[int] = None
    last_sale_date: Optional[str] = None
    assessed_value: Optional[int] = None
    market_value: Optional[int] = None


@dataclass
class ComparableSale:
    """Comparable sale information."""
    address: str
    city: str
    state: str
    zipcode: str
    sale_price: int
    sale_date: str
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    sqft: Optional[int]
    year_built: Optional[int]
    distance_miles: float
    price_per_sqft: Optional[float] = None
    subdivision: Optional[str] = None  # Subdivision/neighborhood name
    adjusted_sale_price: Optional[int] = None  # Time-adjusted price
    time_adjustment_pct: Optional[float] = None  # e.g., 5.2 for +5.2%
    adjusted_price_per_sqft: Optional[float] = None  # Adjusted $/sqft
    similarity_score: Optional[float] = None  # Comp similarity score (0-100)

    def __post_init__(self):
        """Calculate price per sqft if sqft is available."""
        if self.sqft and self.sqft > 0:
            self.price_per_sqft = round(self.sale_price / self.sqft, 2)


class ATTOMClient:
    """Client for ATTOM Data API."""

    BASE_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"

    def __init__(self, api_key: str):
        """
        Initialize ATTOM client.

        Args:
            api_key: ATTOM API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'apikey': api_key,
            'Accept': 'application/json'
        })

    def get_property_detail(self, address: str) -> Optional[PropertyData]:
        """
        Get detailed property information.

        Args:
            address: Full address (e.g., "43500 Tuckaway Pl, Leesburg, VA 20176")

        Returns:
            PropertyData object or None if not found
        """
        try:
            # Use the property/detail endpoint
            url = f"{self.BASE_URL}/property/detail"
            params = {'address': address}

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('code') != 0:
                print(f"API Error: {data.get('status', {}).get('msg')}")
                return None

            property_info = data.get('property', [{}])[0]

            # Extract address components
            addr = property_info.get('address', {})
            location = property_info.get('location', {})
            building = property_info.get('building', {})
            lot = property_info.get('lot', {})
            area = property_info.get('area', {})
            assessment = property_info.get('assessment', {})
            sale = property_info.get('sale', {})
            summary = property_info.get('summary', {})  # Top-level summary has yearbuilt/proptype
            identifier = property_info.get('identifier', {})  # Contains APN for sales lookup

            sqft = building.get('size', {}).get('livingsize')

            # Extract subdivision
            subdivision = (area.get('subdname') or
                         addr.get('subdname') or
                         property_info.get('subdivision'))

            return PropertyData(
                address=addr.get('oneLine', address),
                city=addr.get('locality', ''),
                state=addr.get('countrySubd', ''),
                zipcode=addr.get('postal1', ''),
                latitude=float(location.get('latitude', 0.0)),
                longitude=float(location.get('longitude', 0.0)),
                bedrooms=building.get('rooms', {}).get('beds'),
                bathrooms=building.get('rooms', {}).get('bathstotal'),
                sqft=sqft,
                sqft_source='Tax Records (above-grade only)' if sqft else None,
                year_built=summary.get('yearbuilt'),  # From top-level summary, not building.summary
                lot_size=lot.get('lotsize1'),
                property_type=summary.get('proptype'),  # From top-level summary, not building.summary
                subdivision=subdivision,
                apn=identifier.get('apn'),  # For Loudoun County sales lookup
                last_sale_price=sale.get('amount', {}).get('saleamt'),
                last_sale_date=sale.get('amount', {}).get('salerecdate'),
                assessed_value=assessment.get('assessed', {}).get('assdttlvalue'),
                market_value=assessment.get('market', {}).get('mktttlvalue')
            )

        except requests.exceptions.RequestException as e:
            # Silently handle 401 (expired API key) and other errors
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    return None  # Expired API key - fail silently
            return None

    def get_property_expanded(self, address: str) -> Optional[Dict]:
        """
        Get expanded property details including building characteristics.

        This endpoint provides more detailed building information including
        square footage that may not be available in basic endpoints.

        Args:
            address: Full property address

        Returns:
            Dictionary with expanded property data or None if not found
        """
        try:
            url = f"{self.BASE_URL}/property/expandedprofile"
            params = {'address': address}

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('code') != 0:
                return None

            property_info = data.get('property', [{}])[0]
            return property_info

        except requests.exceptions.RequestException:
            return None

    def get_avm(self, address: str) -> Optional[AVMResult]:
        """
        Get Automated Valuation Model (AVM) data from ATTOM.

        Uses the /attomavm/detail endpoint which provides current market
        value estimates with confidence scoring.

        Args:
            address: Full property address

        Returns:
            AVMResult object or None if not available
        """
        try:
            # ATTOM AVM endpoint
            url = f"{self.BASE_URL}/attomavm/detail"
            params = {'address': address}

            response = self.session.get(url, params=params)

            if response.status_code == 404:
                # AVM not available for this property - try assessment endpoint
                return self._get_assessment_value(address)

            response.raise_for_status()
            data = response.json()

            if data.get('status', {}).get('code') != 0:
                # API error - try assessment fallback
                return self._get_assessment_value(address)

            property_info = data.get('property', [{}])[0]
            avm = property_info.get('avm', {})

            # Extract AVM values
            avm_value = avm.get('amount', {}).get('value')
            if not avm_value:
                # No AVM value - try assessment fallback
                return self._get_assessment_value(address)

            return AVMResult(
                value=int(avm_value),
                value_low=avm.get('amount', {}).get('low'),
                value_high=avm.get('amount', {}).get('high'),
                confidence_score=avm.get('amount', {}).get('fsd'),  # Forecast Standard Deviation
                as_of_date=avm.get('eventDate'),
                source="ATTOM AVM"
            )

        except requests.exceptions.RequestException as e:
            # Silently handle 401 (expired API key) and other errors
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    return None  # Expired API key - fail silently
            # Try assessment fallback for other errors
            return self._get_assessment_value(address)

    def _get_assessment_value(self, address: str) -> Optional[AVMResult]:
        """
        Get assessment-based value estimate as fallback.

        Uses the /assessment/detail endpoint for tax assessment data,
        then applies a market adjustment factor.

        Args:
            address: Full property address

        Returns:
            AVMResult object with adjusted assessed value, or None
        """
        try:
            url = f"{self.BASE_URL}/assessment/detail"
            params = {'address': address}

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                return None

            data = response.json()

            if data.get('status', {}).get('code') != 0:
                return None

            property_info = data.get('property', [{}])[0]
            assessment = property_info.get('assessment', {})

            # Try market value first
            market_value = assessment.get('market', {}).get('mktttlvalue')
            if market_value:
                return AVMResult(
                    value=int(market_value),
                    source="ATTOM Market Assessment"
                )

            # Fall back to assessed value with adjustment
            assessed_value = assessment.get('assessed', {}).get('assdttlvalue')
            if assessed_value:
                # Apply typical assessment ratio adjustment (assessed usually ~85-95% of market)
                adjusted_value = int(assessed_value * 1.1)
                return AVMResult(
                    value=adjusted_value,
                    source="ATTOM Assessed (adjusted)"
                )

            return None

        except requests.exceptions.RequestException:
            return None

    def get_valuation(self, address: str) -> Optional[AVMResult]:
        """
        Get property valuation using best available method.

        Tries sources in order:
        1. AVM endpoint (most accurate)
        2. Assessment endpoint (market value)
        3. Property detail (assessed value with adjustment)

        Args:
            address: Full property address

        Returns:
            AVMResult object or None if no valuation available
        """
        # Try AVM first (includes assessment fallback)
        avm_result = self.get_avm(address)
        if avm_result:
            return avm_result

        # Last resort: try property detail's assessment data
        property_data = self.get_property_detail(address)
        if property_data:
            if property_data.market_value:
                return AVMResult(
                    value=property_data.market_value,
                    source="ATTOM Property Detail (market)"
                )
            if property_data.assessed_value:
                return AVMResult(
                    value=int(property_data.assessed_value * 1.1),
                    source="ATTOM Property Detail (assessed, adjusted)"
                )

        return None

    def enrich_comparable_with_sqft(self, comp: ComparableSale) -> ComparableSale:
        """
        Enrich a comparable sale with square footage data from expanded profile.

        Args:
            comp: ComparableSale object to enrich

        Returns:
            Updated ComparableSale object with sqft data if available
        """
        # If already has sqft, no need to fetch
        if comp.sqft and comp.sqft > 0:
            return comp

        # Try to get property details - property/detail has better building data
        full_address = f"{comp.address}, {comp.city}, {comp.state} {comp.zipcode}"
        property_data = self.get_property_detail(full_address)

        if property_data and property_data.sqft and property_data.sqft > 0:
            # Update the comparable with sqft data
            comp.sqft = property_data.sqft
            # Recalculate price per sqft
            comp.price_per_sqft = round(comp.sale_price / property_data.sqft, 2)
            # Also update other fields if available
            if property_data.bedrooms:
                comp.bedrooms = property_data.bedrooms
            if property_data.bathrooms:
                comp.bathrooms = property_data.bathrooms
            if property_data.year_built:
                comp.year_built = property_data.year_built

        return comp

    def get_comparable_sales(
        self,
        address: str,
        radius_miles: float = 0.5,
        months_back: int = 12,
        max_results: int = 10,
        enrich_sqft: bool = True,
        lat: float = None,
        lon: float = None
    ) -> List[ComparableSale]:
        """
        Get comparable sales near a property.

        Args:
            address: Target property address
            radius_miles: Search radius in miles
            months_back: How many months back to search
            max_results: Maximum number of results to return
            enrich_sqft: If True, fetch sqft data from expandedprofile endpoint
            lat: Optional latitude (bypasses ATTOM property lookup if provided with lon)
            lon: Optional longitude (bypasses ATTOM property lookup if provided with lat)

        Returns:
            List of ComparableSale objects
        """
        # Use provided coordinates if available, otherwise lookup via ATTOM
        if lat is not None and lon is not None:
            target_lat, target_lon = lat, lon
        else:
            # Fall back to ATTOM property lookup
            target_property = self.get_property_detail(address)
            if not target_property:
                print(f"Could not find target property: {address}")
                return []
            target_lat = target_property.latitude
            target_lon = target_property.longitude

        try:
            # Calculate date range for filtering results
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)

            # Use the sale/snapshot endpoint to find comparable sales
            # Note: ATTOM API doesn't support date filtering in the request,
            # so we'll filter results after fetching
            url = f"{self.BASE_URL}/sale/snapshot"

            params = {
                'latitude': target_lat,
                'longitude': target_lon,
                'radius': radius_miles,
                'pagesize': max_results * 5  # Get more to account for date filtering
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('code') != 0:
                print(f"API Error: {data.get('status', {}).get('msg')}")
                return []

            # Parse comparable sales
            comparables = []
            properties = data.get('property', [])

            for prop in properties:
                addr = prop.get('address', {})
                building = prop.get('building', {})
                sale = prop.get('sale', {})
                area = prop.get('area', {})
                distance = prop.get('distance', 0.0)

                # Skip if no sale price
                sale_price = sale.get('amount', {}).get('saleamt')
                if not sale_price:
                    continue

                # Check sale date and filter by date range
                sale_date_str = sale.get('amount', {}).get('salerecdate', '')
                if sale_date_str and months_back > 0:
                    try:
                        # Try both date formats
                        try:
                            sale_date = datetime.strptime(sale_date_str, '%m/%d/%Y')
                        except ValueError:
                            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')

                        if sale_date < start_date or sale_date > end_date:
                            continue  # Skip sales outside our date range
                    except ValueError:
                        # If both date formats fail, skip this sale (don't include old data)
                        print(f"  ⚠️ Skipping sale with unparseable date: {sale_date_str}")
                        continue

                # Extract subdivision (may be in area.subdname or addr.subdname)
                subdivision = (area.get('subdname') or
                             addr.get('subdname') or
                             prop.get('subdivision'))

                comp = ComparableSale(
                    address=addr.get('oneLine', ''),
                    city=addr.get('locality', ''),
                    state=addr.get('countrySubd', ''),
                    zipcode=addr.get('postal1', ''),
                    sale_price=sale_price,
                    sale_date=sale_date_str,
                    bedrooms=building.get('rooms', {}).get('beds'),
                    bathrooms=building.get('rooms', {}).get('bathstotal'),
                    sqft=building.get('size', {}).get('livingsize'),
                    year_built=building.get('summary', {}).get('yearbuilt'),
                    distance_miles=round(distance, 2),
                    subdivision=subdivision
                )

                comparables.append(comp)

            # Exclude the subject property itself from comparables
            # (Properties at distance 0.0 miles with the exact same address)
            subject_address_normalized = target_property.address.upper().replace(',', '').replace('.', '')
            comparables = [
                c for c in comparables
                if not (c.distance_miles == 0.0 and
                        c.address.upper().replace(',', '').replace('.', '') == subject_address_normalized)
            ]

            # Sort by distance
            comparables.sort(key=lambda x: x.distance_miles)

            # Limit to max results
            comparables = comparables[:max_results]

            # Enrich with sqft data if requested
            if enrich_sqft:
                print(f"Enriching {len(comparables)} comparables with sqft data...")
                enriched_comparables = []
                for i, comp in enumerate(comparables, 1):
                    if comp.sqft and comp.sqft > 0:
                        print(f"  {i}/{len(comparables)}: {comp.address} - sqft already available ({comp.sqft} sqft)")
                        enriched_comparables.append(comp)
                    else:
                        print(f"  {i}/{len(comparables)}: {comp.address} - fetching sqft...")
                        enriched_comp = self.enrich_comparable_with_sqft(comp)
                        if enriched_comp.sqft:
                            print(f"    ✓ Found: {enriched_comp.sqft} sqft (${enriched_comp.price_per_sqft:.2f}/sqft)")
                        else:
                            print(f"    ✗ Not available")
                        enriched_comparables.append(enriched_comp)
                comparables = enriched_comparables

            return comparables

        except requests.exceptions.RequestException as e:
            # Silently handle 401 (expired API key) and other errors
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    return []  # Expired API key - fail silently
            return []

    def format_property_report(self, property_data: PropertyData) -> str:
        """Format a property report for display."""
        lines = [
            "=" * 70,
            "PROPERTY DETAILS",
            "=" * 70,
            f"Address: {property_data.address}",
            f"City: {property_data.city}, {property_data.state} {property_data.zipcode}",
            f"Location: ({property_data.latitude}, {property_data.longitude})",
            "",
            "Building Information:",
            f"  Bedrooms: {property_data.bedrooms or 'N/A'}",
            f"  Bathrooms: {property_data.bathrooms or 'N/A'}",
            f"  Living Area: {property_data.sqft or 'N/A'} sqft",
            f"  Year Built: {property_data.year_built or 'N/A'}",
            f"  Lot Size: {property_data.lot_size or 'N/A'} sqft",
            f"  Property Type: {property_data.property_type or 'N/A'}",
            "",
            "Valuation:",
            f"  Last Sale Price: ${property_data.last_sale_price:,}" if property_data.last_sale_price else "  Last Sale Price: N/A",
            f"  Last Sale Date: {property_data.last_sale_date or 'N/A'}",
            f"  Assessed Value: ${property_data.assessed_value:,}" if property_data.assessed_value else "  Assessed Value: N/A",
            f"  Market Value: ${property_data.market_value:,}" if property_data.market_value else "  Market Value: N/A",
            "=" * 70
        ]
        return "\n".join(lines)

    def format_comparables_report(self, comparables: List[ComparableSale]) -> str:
        """Format comparable sales report for display."""
        if not comparables:
            return "No comparable sales found."

        lines = [
            "",
            "=" * 70,
            f"COMPARABLE SALES (Found {len(comparables)} properties)",
            "=" * 70
        ]

        for i, comp in enumerate(comparables, 1):
            price_per_sqft = f"${comp.price_per_sqft:.2f}/sqft" if comp.price_per_sqft else "N/A"
            lines.extend([
                f"\n#{i} - {comp.address}",
                f"  Location: {comp.city}, {comp.state} {comp.zipcode}",
                f"  Distance: {comp.distance_miles} miles",
                f"  Sale Price: ${comp.sale_price:,}",
                f"  Sale Date: {comp.sale_date}",
                f"  Bedrooms: {comp.bedrooms or 'N/A'} | Bathrooms: {comp.bathrooms or 'N/A'}",
                f"  Living Area: {comp.sqft or 'N/A'} sqft",
                f"  Price per sqft: {price_per_sqft}",
                f"  Year Built: {comp.year_built or 'N/A'}"
            ])

        lines.append("=" * 70)
        return "\n".join(lines)


if __name__ == '__main__':
    # Test the client
    from api_config import get_api_key

    api_key = get_api_key('ATTOM_API_KEY')
    if not api_key:
        print("Error: ATTOM_API_KEY not found in config")
        exit(1)

    client = ATTOMClient(api_key)

    # Test with the provided address
    test_address = "43500 Tuckaway Pl, Leesburg, VA 20176"

    print(f"Testing ATTOM API with: {test_address}\n")

    # Get property details
    property_data = client.get_property_detail(test_address)
    if property_data:
        print(client.format_property_report(property_data))
    else:
        print("Failed to retrieve property details")

    # Get comparable sales
    print("\nFetching comparable sales...")
    comparables = client.get_comparable_sales(test_address, radius_miles=0.5, months_back=6)
    print(client.format_comparables_report(comparables))
