"""
ATTOM API Replacement Examples
===============================

Examples of how to replace ATTOM functionality with alternatives.
This is NOT production code - just examples for decision-making.

File: diagnostic_outputs/api_analysis/02_replacement_examples.py
Purpose: Demonstrate alternative implementations to ATTOM API calls
Status: REFERENCE ONLY - Do not use in production without testing

Usage:
    # These are examples only. To test:
    python 02_replacement_examples.py
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


# =============================================================================
# EXAMPLE 1: Property Characteristics from RentCast Instead of ATTOM
# =============================================================================
# Current: Uses ATTOM /property/detail for beds, baths, sqft, year_built
# Alternative: Use RentCast /v1/avm/value response (already calling this!)

class PropertyCharacteristicsAlternative:
    """
    Example: Get property details from RentCast instead of ATTOM.

    Current ATTOM implementation (core/property_valuation_orchestrator.py):
        property_data = self.attom.get_property_detail(address)
        if property_data:
            property_sqft = property_data.sqft

    Alternative using RentCast:
        rentcast_data = self.rentcast.get_complete_estimate(address)
        if rentcast_data:
            property_sqft = rentcast_data.sqft
    """

    def get_characteristics_current(self, address: str) -> Dict:
        """
        CURRENT: Uses ATTOM /property/detail
        Cost: 1 ATTOM API call (~$0.10-0.30)
        """
        # Pseudocode - actual implementation in core/attom_client.py
        # property_data = self.attom.get_property_detail(address)
        return {
            'source': 'ATTOM',
            'api_calls': 1,
            'cost': '$0.10-0.30',
            'data': {
                'sqft': 3468,
                'bedrooms': 5,
                'bathrooms': 4.5,
                'year_built': 2004,
                'lot_size': 43560,
                'property_type': 'SFR'
            }
        }

    def get_characteristics_alternative(self, address: str) -> Dict:
        """
        ALTERNATIVE: Uses RentCast /v1/avm/value (already calling this!)
        Cost: $0 additional (already making this call for valuation)

        Implementation change needed in orchestrator.py:

        BEFORE (lines 121-129):
            property_data = self.attom.get_property_detail(address)
            if property_data:
                if property_data.sqft and not property_sqft:
                    property_sqft = property_data.sqft

        AFTER:
            # Get characteristics from RentCast (already calling this)
            rentcast_data = self.rentcast.get_complete_estimate(address)
            if rentcast_data:
                if rentcast_data.sqft and not property_sqft:
                    property_sqft = rentcast_data.sqft

            # Only call ATTOM if RentCast missing critical data
            if not property_sqft:
                property_data = self.attom.get_property_detail(address)
                if property_data and property_data.sqft:
                    property_sqft = property_data.sqft
        """
        # Pseudocode - actual implementation in core/rentcast_client.py
        # rentcast_data = self.rentcast.get_complete_estimate(address)
        return {
            'source': 'RentCast',
            'api_calls': 0,  # Already making this call!
            'cost': '$0.00 additional',
            'data': {
                'sqft': 3468,  # RentCast provides this
                'bedrooms': 5,
                'bathrooms': 4.5,
                'year_built': 2004,
                'lot_size': 43560,
                'property_type': 'Single Family'
            }
        }


# =============================================================================
# EXAMPLE 2: Comparable Sales from County Data Instead of ATTOM
# =============================================================================
# Current: Uses ATTOM /sale/snapshot for radius-based comp search
# Alternative: Geocode county sales data and query spatially

@dataclass
class GeocodedSale:
    """Sale record with lat/lon for spatial queries."""
    parid: str
    address: str
    price: int
    sale_date: str
    latitude: float
    longitude: float
    sqft: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None


class ComparableSalesAlternative:
    """
    Example: Get comparable sales from geocoded county data.

    Current ATTOM implementation:
        comps = self.attom.get_comparable_sales(
            address=address,
            radius_miles=1.0,
            max_results=10
        )
        # Cost: 2-12 ATTOM calls

    Alternative using geocoded county data:
        comps = self.find_nearby_sales(
            lat=target_lat, lon=target_lon,
            radius_miles=1.0,
            max_results=10
        )
        # Cost: $0 (local data query)

    Requirements:
        1. Geocode 78K sales records (one-time, ~$780 at $0.01/address)
        2. Add lat/lon to combined_sales.parquet
        3. Build spatial index (optional, improves performance)
    """

    def __init__(self, geocoded_sales: List[GeocodedSale]):
        """Initialize with geocoded sales data."""
        self.sales = geocoded_sales

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in miles.

        This is the same calculation ATTOM uses internally.
        """
        R = 3959.87433  # Earth radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def find_nearby_sales(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        max_results: int = 10,
        months_back: int = 12
    ) -> List[Dict]:
        """
        Find comparable sales within radius.

        This replaces ATTOM's /sale/snapshot endpoint.

        Args:
            lat: Target property latitude
            lon: Target property longitude
            radius_miles: Search radius
            max_results: Maximum number of results
            months_back: How many months back to search

        Returns:
            List of comparable sales with distance
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=months_back * 30)

        nearby = []
        for sale in self.sales:
            # Calculate distance
            distance = self.haversine_distance(lat, lon, sale.latitude, sale.longitude)

            if distance <= radius_miles:
                # Parse sale date and filter by time
                try:
                    sale_date = datetime.strptime(sale.sale_date, '%Y-%m-%d')
                    if sale_date >= cutoff_date:
                        nearby.append({
                            'address': sale.address,
                            'sale_price': sale.price,
                            'sale_date': sale.sale_date,
                            'distance_miles': round(distance, 2),
                            'sqft': sale.sqft,
                            'bedrooms': sale.bedrooms,
                            'bathrooms': sale.bathrooms
                        })
                except ValueError:
                    continue

        # Sort by distance and limit results
        nearby.sort(key=lambda x: x['distance_miles'])
        return nearby[:max_results]

    def geocode_batch_example(self) -> str:
        """
        Example of how to geocode the sales data.

        One-time process to add lat/lon to combined_sales.parquet.
        """
        return """
# scripts/geocode_sales_data.py
# One-time script to geocode 78K sales records

import pandas as pd
import googlemaps
from tqdm import tqdm
import time

# Initialize Google Maps client
gmaps = googlemaps.Client(key='YOUR_GOOGLE_MAPS_API_KEY')

# Load sales data
df = pd.read_parquet('data/loudoun/sales/combined_sales.parquet')

# Add lat/lon columns
df['latitude'] = None
df['longitude'] = None

# Get unique addresses (to avoid duplicate geocoding)
unique_addresses = df['ADDRESS'].unique()
print(f"Geocoding {len(unique_addresses)} unique addresses...")

# Cost: $0.005/request for Geocoding API (first 100K free/month)
# For 78K addresses: ~$390 if over free tier

address_coords = {}
for address in tqdm(unique_addresses):
    try:
        result = gmaps.geocode(f"{address}, Loudoun County, VA")
        if result:
            location = result[0]['geometry']['location']
            address_coords[address] = (location['lat'], location['lng'])
        time.sleep(0.05)  # Rate limiting
    except Exception as e:
        print(f"Failed to geocode {address}: {e}")
        continue

# Apply coordinates to dataframe
for idx, row in df.iterrows():
    coords = address_coords.get(row['ADDRESS'])
    if coords:
        df.at[idx, 'latitude'] = coords[0]
        df.at[idx, 'longitude'] = coords[1]

# Save updated parquet
df.to_parquet('data/loudoun/sales/combined_sales_geocoded.parquet')
print(f"Saved with {df['latitude'].notna().sum()} geocoded addresses")
"""


# =============================================================================
# EXAMPLE 3: Proprietary AVM Instead of ATTOM
# =============================================================================
# Current: Uses ATTOM /attomavm/detail for valuation
# Alternative: Build ML model trained on 78K local sales

class ProprietaryAVMExample:
    """
    Example: Build proprietary AVM using local sales data.

    Current ATTOM implementation:
        avm_result = self.attom.get_valuation(address)
        # Cost: 1-3 ATTOM API calls (~$0.30-0.90)

    Alternative using local model:
        avm_result = self.proprietary_avm.estimate(
            sqft=3468, beds=5, baths=4.5,
            year_built=2004, lat=39.11, lon=-77.49
        )
        # Cost: $0 (local computation)

    Model approach:
        1. Train on 78K Loudoun County sales (2020-2025)
        2. Features: sqft, beds, baths, year_built, location, schools
        3. Model: XGBoost or Random Forest
        4. Validation: 20% holdout, compare to ATTOM predictions
    """

    def estimate_simple(
        self,
        sqft: int,
        beds: int,
        baths: float,
        year_built: int,
        lat: float,
        lon: float
    ) -> Dict:
        """
        Simple example AVM (NOT production-ready).

        A real implementation would use trained ML model.
        This shows the concept only.
        """
        # Base price per sqft (Loudoun County average ~$300/sqft in 2024)
        base_psf = 300

        # Age adjustment (-0.5% per year over 10 years old)
        age = 2024 - year_built
        age_adjustment = max(-20, min(0, -0.5 * max(0, age - 10)))

        # Size adjustment (larger homes slightly lower $/sqft)
        if sqft > 4000:
            size_adjustment = -5
        elif sqft < 2000:
            size_adjustment = 10
        else:
            size_adjustment = 0

        # Calculate estimate
        adjusted_psf = base_psf * (1 + (age_adjustment + size_adjustment) / 100)
        estimate = int(sqft * adjusted_psf)

        # Range based on model uncertainty
        low = int(estimate * 0.92)
        high = int(estimate * 1.08)

        return {
            'value': estimate,
            'value_low': low,
            'value_high': high,
            'confidence_score': 75,  # Would come from model uncertainty
            'source': 'NewCo Proprietary AVM',
            'methodology': 'ML model trained on 78K Loudoun County sales'
        }

    def training_approach(self) -> str:
        """
        Approach for training a real AVM model.
        """
        return """
# Development approach for proprietary AVM:

1. DATA PREPARATION (8-16 hours)
   - Load combined_sales.parquet (78K records)
   - Join with property characteristics
   - Filter to arms-length sales only
   - Handle missing values
   - Feature engineering:
     * Price per sqft (target)
     * Age of property
     * Location clusters (lat/lon k-means)
     * School district quality scores
     * Metro proximity
     * Days on market (if available)

2. MODEL DEVELOPMENT (40-60 hours)
   - Train/test split (80/20)
   - Try multiple models:
     * XGBoost (typically best for tabular data)
     * Random Forest
     * Gradient Boosting
   - Hyperparameter tuning
   - Cross-validation
   - Feature importance analysis

3. VALIDATION (16-24 hours)
   - Compare predictions to ATTOM for 100 properties
   - Calculate MAE, RMSE, MAPE
   - Analyze systematic biases
   - Test on recent sales (last 30 days)

4. DEPLOYMENT (24-40 hours)
   - Save model artifacts
   - Create prediction API
   - Add to orchestrator
   - A/B test against ATTOM
   - Monitor prediction accuracy

TOTAL DEVELOPMENT: 100-140 hours

Expected outcome:
   - MAE: Within 5% of sale price (better than generic AVMs)
   - Local context: Understands Loudoun-specific factors
   - Cost: $0 per prediction
   - Competitive advantage: Unique to NewCo
"""


# =============================================================================
# EXAMPLE 4: APN Lookup Without ATTOM
# =============================================================================
# Current: Uses ATTOM /property/detail to get APN
# Alternative: Build address-to-APN index from sales data

class APNLookupAlternative:
    """
    Example: Get APN from local data instead of ATTOM.

    Current usage:
        property_data = self.attom.get_property_detail(address)
        apn = property_data.apn
        sales_history = sales_data.get_sales_history(apn)

    Alternative:
        apn = self.apn_index.lookup(address)
        sales_history = sales_data.get_sales_history(apn)

    Building the index:
        - Sales data already has PARID (same as APN)
        - Build address -> PARID mapping
        - Fuzzy matching for address variations
    """

    def __init__(self):
        """Initialize APN index (would be loaded from Parquet)."""
        self.address_to_apn = {}

    def build_index_example(self) -> str:
        """
        Example of building address-to-APN index.
        """
        return """
# Building APN index from sales data

import pandas as pd
import re

# Load sales data (already has PARID)
df = pd.read_parquet('data/loudoun/sales/combined_sales.parquet')

# Normalize addresses for matching
def normalize_address(addr):
    addr = addr.upper().strip()
    addr = re.sub(r'\\s+', ' ', addr)
    addr = re.sub(r'\\bSTREET\\b', 'ST', addr)
    addr = re.sub(r'\\bROAD\\b', 'RD', addr)
    addr = re.sub(r'\\bDRIVE\\b', 'DR', addr)
    addr = re.sub(r'\\bLANE\\b', 'LN', addr)
    addr = re.sub(r'\\bPLACE\\b', 'PL', addr)
    return addr

# Build index
apn_index = {}
for _, row in df.iterrows():
    normalized = normalize_address(row['ADDRESS'])
    apn_index[normalized] = row['PARID']

# Save index
import json
with open('data/loudoun/apn_index.json', 'w') as f:
    json.dump(apn_index, f)

print(f"Built index with {len(apn_index)} addresses")
"""

    def lookup(self, address: str) -> Optional[str]:
        """
        Look up APN by address.

        Returns:
            APN string or None if not found
        """
        normalized = self.normalize_address(address)
        return self.address_to_apn.get(normalized)

    @staticmethod
    def normalize_address(addr: str) -> str:
        """Normalize address for matching."""
        import re
        addr = addr.upper().strip()
        addr = re.sub(r'\s+', ' ', addr)
        addr = re.sub(r'\bSTREET\b', 'ST', addr)
        addr = re.sub(r'\bROAD\b', 'RD', addr)
        addr = re.sub(r'\bDRIVE\b', 'DR', addr)
        addr = re.sub(r'\bLANE\b', 'LN', addr)
        addr = re.sub(r'\bPLACE\b', 'PL', addr)
        return addr


# =============================================================================
# EXAMPLE 5: Complete ATTOM-Free Orchestrator
# =============================================================================

class ATTOMFreeOrchestrator:
    """
    Example: Property valuation without any ATTOM calls.

    This shows how the orchestrator would work after implementing
    all the alternatives above.

    Current orchestrator makes 3-16 ATTOM calls per property.
    This version makes 0 ATTOM calls.
    """

    def analyze_property_without_attom(
        self,
        address: str,
        lat: float,
        lon: float,
        sqft: Optional[int] = None
    ) -> Dict:
        """
        Complete property analysis without ATTOM.

        Data sources:
        1. RentCast - Property characteristics, AVM, rent estimate
        2. Loudoun County Sales - Sales history, comparable sales
        3. Proprietary AVM - Second valuation source

        Cost: RentCast calls only (~$0.03-0.10 per property)
        """
        return {
            'current_value': {
                # Two-source triangulation instead of three
                'rentcast_estimate': 875000,  # From RentCast /avm/value
                'proprietary_estimate': 890000,  # From local ML model
                'triangulated_estimate': 882500,  # 50/50 weighted
                'confidence_score': 7.5,
                'methodology': 'Triangulated using RentCast AVM and NewCo proprietary model'
            },
            'comparable_sales': [
                # From geocoded county data instead of ATTOM
                {
                    'address': '123 Oak St',
                    'sale_price': 850000,
                    'sale_date': '2024-10-15',
                    'distance_miles': 0.3,
                    'source': 'Loudoun County Records'
                }
            ],
            'property_details': {
                # From RentCast instead of ATTOM
                'sqft': 3468,
                'bedrooms': 5,
                'bathrooms': 4.5,
                'year_built': 2004,
                'source': 'RentCast'
            },
            'sales_history': {
                # Already using county data, not ATTOM
                'found': True,
                'sales': [
                    {'date': '2018-06-15', 'price': 675000}
                ],
                'source': 'Loudoun County Commissioner of Revenue'
            },
            'rental_analysis': {
                # Already from RentCast, not ATTOM
                'estimated_rent_monthly': 4500,
                'source': 'RentCast'
            },
            'data_sources': [
                'RentCast Property Value',
                'RentCast Rent Estimate',
                'NewCo Proprietary AVM',
                'Loudoun County Sales Records (geocoded)',
                'Loudoun County Commissioner of Revenue'
            ],
            'api_calls': {
                'attom': 0,
                'rentcast': 3,  # value + rent + properties
                'local': 2  # AVM + comp search
            },
            'estimated_cost': '$0.06-0.15'  # vs $0.60-1.80 current
        }


# =============================================================================
# MAIN: Run examples
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("ATTOM REPLACEMENT EXAMPLES")
    print("=" * 70)
    print()
    print("These examples demonstrate how to replace ATTOM API functionality")
    print("with alternatives. See 01_attom_usage_audit.txt for full analysis.")
    print()

    # Example 1: Property Characteristics
    print("-" * 70)
    print("EXAMPLE 1: Property Characteristics")
    print("-" * 70)
    prop_alt = PropertyCharacteristicsAlternative()
    current = prop_alt.get_characteristics_current("43500 Tuckaway Pl, Leesburg, VA")
    alternative = prop_alt.get_characteristics_alternative("43500 Tuckaway Pl, Leesburg, VA")
    print(f"Current (ATTOM): {current['api_calls']} calls, {current['cost']}")
    print(f"Alternative (RentCast): {alternative['api_calls']} additional calls, {alternative['cost']}")
    print()

    # Example 2: Comparable Sales
    print("-" * 70)
    print("EXAMPLE 2: Comparable Sales")
    print("-" * 70)
    print("Current: ATTOM /sale/snapshot (2-12 calls per property)")
    print("Alternative: Geocoded county data (0 API calls)")
    print(f"One-time setup: ~$780 to geocode 78K addresses")
    print()

    # Example 3: AVM
    print("-" * 70)
    print("EXAMPLE 3: Automated Valuation Model")
    print("-" * 70)
    avm = ProprietaryAVMExample()
    estimate = avm.estimate_simple(
        sqft=3468, beds=5, baths=4.5,
        year_built=2004, lat=39.11, lon=-77.49
    )
    print(f"Simple example estimate: ${estimate['value']:,}")
    print(f"Range: ${estimate['value_low']:,} - ${estimate['value_high']:,}")
    print(f"Source: {estimate['source']}")
    print()

    # Summary
    print("-" * 70)
    print("SUMMARY: ATTOM-Free Implementation")
    print("-" * 70)
    print("Development time: 120-200 hours total")
    print("One-time costs: ~$780 (geocoding)")
    print("Per-property cost reduction: $0.60-1.80 -> $0.06-0.15")
    print("Annual savings at 1K/month: $7,200 - $21,600")
    print()
    print("See 03_cost_benefit_analysis.md for detailed financial analysis.")
    print("=" * 70)
