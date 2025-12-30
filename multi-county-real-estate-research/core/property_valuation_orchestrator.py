"""
Property Valuation Orchestrator
Unifies all valuation components into a single clean interface for Streamlit UI.

This module integrates:
- ATTOM API for property data and comparable sales
- RentCast API for rental estimates and value estimates
- ComparableAnalyzer for price analysis
- ForecastEngine for value projections

Usage:
    from core.property_valuation_orchestrator import PropertyValuationOrchestrator

    orchestrator = PropertyValuationOrchestrator()
    result = orchestrator.analyze_property(
        address="123 Main St, Leesburg, VA 20176",
        lat=39.1234,
        lon=-77.5678,
        sqft=2500
    )
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

from core.api_config import get_api_key
from core.attom_client import ATTOMClient, ComparableSale
from core.rentcast_client import RentCastClient
from core.comparable_analyzer import ComparableAnalyzer
from core.forecast_engine import ForecastEngine


class PropertyValuationOrchestrator:
    """
    Unified property valuation interface.

    Combines multiple data sources to provide comprehensive property analysis
    with triangulated value estimates and confidence scoring.
    """

    def __init__(self):
        """Initialize with real API clients."""
        # Load API keys
        attom_key = get_api_key('ATTOM_API_KEY')
        rentcast_key = get_api_key('RENTCAST_API_KEY')

        if not attom_key:
            raise ValueError("ATTOM_API_KEY not found in configuration")
        if not rentcast_key:
            raise ValueError("RENTCAST_API_KEY not found in configuration")

        # Initialize API clients
        self.attom = ATTOMClient(api_key=attom_key)
        self.rentcast = RentCastClient(api_key=rentcast_key)

        # Initialize analyzers
        self.comp_analyzer = ComparableAnalyzer()
        self.forecast_engine = ForecastEngine()

        # Track data sources used
        self.data_sources = []

        # Loudoun County sales data - lazy loaded on first use
        self._sales_data = None

    def _get_sales_data(self):
        """
        Get Loudoun County sales data (cached for instant subsequent loads).

        Performance:
        - First call: ~2-3 seconds (Parquet read + indexing)
        - Cached calls: <0.01 seconds (Streamlit @st.cache_resource)
        - File I/O: 105x faster than original Excel format
        """
        if self._sales_data is None:
            try:
                # Use cached factory function for instant subsequent loads
                # Caching handled by @st.cache_resource in loudoun_sales_data.py
                from core.loudoun_sales_data import get_cached_loudoun_sales_data
                self._sales_data = get_cached_loudoun_sales_data()
            except Exception as e:
                print(f"⚠ Sales data unavailable: {e}")
                self._sales_data = False  # Mark as failed
        return self._sales_data if self._sales_data else None

    def analyze_property(
        self,
        address: str,
        lat: float,
        lon: float,
        sqft: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete property valuation analysis.

        Args:
            address: Full property address
            lat: Latitude coordinate
            lon: Longitude coordinate
            sqft: Square footage (optional, will try to fetch if not provided)

        Returns:
            Comprehensive valuation dictionary with all analysis components
        """
        self.data_sources = []

        # Initialize result structure
        result = self._empty_result()
        result['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result['address'] = address
        result['coordinates'] = {'lat': lat, 'lon': lon}

        # Get ATTOM property data and value estimate
        attom_estimate = None
        attom_valuation_source = None
        attom_comps = []
        property_sqft = sqft

        # First, get property details for sqft and other data
        try:
            property_data = self.attom.get_property_detail(address)
            if property_data:
                self.data_sources.append('ATTOM Property Detail')
                if property_data.sqft and not property_sqft:
                    property_sqft = property_data.sqft
        except Exception as e:
            print(f"ATTOM property detail error: {e}")
            property_data = None

        # Get sales history from Loudoun County records
        sales_history = {'found': False, 'sales': [], 'error': None}
        if property_data and property_data.apn:
            try:
                sales_data = self._get_sales_data()
                if sales_data:
                    sales_history = sales_data.get_sales_history(property_data.apn)
                    if sales_history.get('found'):
                        self.data_sources.append('Loudoun County Sales Records')
            except Exception as e:
                print(f"⚠ Sales history lookup error: {e}")
                sales_history['error'] = str(e)

        # Get ATTOM valuation using AVM with fallback chain
        try:
            avm_result = self.attom.get_valuation(address)
            if avm_result:
                attom_estimate = avm_result.value
                attom_valuation_source = avm_result.source
                self.data_sources.append(f'ATTOM Valuation ({avm_result.source})')
        except Exception as e:
            print(f"ATTOM valuation error: {e}")

        # Get ATTOM comparable sales (use geocoded coords to bypass ATTOM property lookup)
        try:
            comps = self.attom.get_comparable_sales(
                address=address,
                radius_miles=1.0,
                max_results=10,
                enrich_sqft=False,  # Optimization: saves 5-6 API calls per property
                lat=lat,
                lon=lon
            )
            if comps:
                attom_comps = comps
                self.data_sources.append('ATTOM Comparable Sales')
        except Exception as e:
            print(f"ATTOM comparable sales error: {e}")

        # Get RentCast estimates
        rentcast_estimate = None
        rent_estimate = None

        try:
            rentcast_data = self.rentcast.get_complete_estimate(address)
            if rentcast_data:
                self.data_sources.append('RentCast Estimates')
                if rentcast_data.price_estimate:
                    rentcast_estimate = rentcast_data.price_estimate
                if rentcast_data.rent_estimate:
                    rent_estimate = rentcast_data.rent_estimate
                if rentcast_data.sqft and not property_sqft:
                    property_sqft = rentcast_data.sqft
        except Exception as e:
            print(f"RentCast error: {e}")

        # Get RentCast property records for subdivision and HOA data
        subdivision = None
        hoa_fee = None

        try:
            property_records = self.rentcast.get_property_records(address)
            if property_records:
                self.data_sources.append('RentCast Property Records')
                subdivision = property_records.get('subdivision')
                hoa_data = property_records.get('hoa')
                if hoa_data and isinstance(hoa_data, dict):
                    hoa_fee = hoa_data.get('fee')
        except Exception as e:
            print(f"RentCast property records error: {e}")

        # Analyze comparables
        comp_estimate = None
        if attom_comps:
            try:
                comp_analysis = self.comp_analyzer.analyze_comparables(
                    attom_comps,  # Pass ComparableSale objects directly
                    target_sqft=property_sqft
                )
                if comp_analysis.median_sale_price:
                    comp_estimate = int(comp_analysis.median_sale_price)
            except Exception as e:
                print(f"Comparable analysis error: {e}")

        # Triangulate value
        current_value = self._triangulate_value(
            attom_estimate,
            rentcast_estimate,
            comp_estimate
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            [v for v in [attom_estimate, rentcast_estimate, comp_estimate] if v]
        )

        # Populate current value section
        result['current_value'] = {
            'attom_estimate': attom_estimate or 0,
            'rentcast_estimate': rentcast_estimate or 0,
            'triangulated_estimate': current_value,
            'confidence_score': confidence,
            'methodology': self._get_methodology(attom_estimate, rentcast_estimate, comp_estimate)
        }

        # Populate comparable sales
        result['comparable_sales'] = self._format_comparables(attom_comps[:8])

        # Generate forecast
        if current_value > 0:
            result['forecast'] = self._generate_forecast(current_value, confidence)

        # Rental analysis
        if rent_estimate and current_value > 0:
            gross_yield = (rent_estimate * 12 / current_value) * 100
            result['rental_analysis'] = {
                'estimated_rent_monthly': rent_estimate,
                'gross_yield_pct': round(gross_yield, 2),
                'area_avg_yield_pct': 5.5,  # Typical for Loudoun County
                'cash_flow_potential': self._assess_cash_flow(gross_yield)
            }

        # Price per square foot analysis
        if property_sqft and property_sqft > 0:
            property_psf = current_value / property_sqft if current_value > 0 else 0
            comp_psfs = [c.sale_price / c.sqft for c in attom_comps if c.sqft and c.sqft > 0]
            avg_comp_psf = sum(comp_psfs) / len(comp_psfs) if comp_psfs else 0

            result['price_per_sqft'] = {
                'property': round(property_psf, 2),
                'neighborhood_avg': round(avg_comp_psf, 2),
                'comps': [round(p, 2) for p in comp_psfs[:5]],
                'position': self._assess_psf_position(property_psf, avg_comp_psf)
            }

        result['data_sources'] = self.data_sources
        result['api_mode'] = 'live'
        result['sqft'] = property_sqft

        # Subdivision and HOA data from RentCast property records
        result['subdivision'] = subdivision
        result['hoa_fee'] = hoa_fee

        # Loudoun County official sales history
        result['sales_history'] = sales_history

        return result

    def _triangulate_value(
        self,
        attom: Optional[int],
        rentcast: Optional[int],
        comps: Optional[int]
    ) -> int:
        """
        Calculate triangulated value with weighted average.

        Weights: ATTOM 40%, RentCast 30%, Comps 30%
        If sources are missing, redistribute weights proportionally.
        """
        values = []
        weights = []

        if attom and attom > 0:
            values.append(attom)
            weights.append(0.4)

        if rentcast and rentcast > 0:
            values.append(rentcast)
            weights.append(0.3)

        if comps and comps > 0:
            values.append(comps)
            weights.append(0.3)

        if not values:
            return 0

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Calculate weighted average
        triangulated = sum(v * w for v, w in zip(values, normalized_weights))

        return int(triangulated)

    def _calculate_confidence(self, values: List[int]) -> float:
        """
        Calculate confidence score based on source agreement.

        High confidence (8-10): Values agree within 5%
        Medium confidence (6-7): Values agree within 15%
        Lower confidence (<6): Larger variance
        """
        if not values:
            return 0.0

        if len(values) == 1:
            return 5.0  # Single source = moderate confidence

        # Calculate coefficient of variation
        avg = sum(values) / len(values)
        if avg == 0:
            return 0.0

        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / avg

        # Convert CV to confidence score (0-10)
        # CV of 0% = 10, CV of 5% = 8, CV of 15% = 6, CV of 30%+ = 3
        if cv <= 0.05:
            confidence = 10 - (cv * 40)  # 10 to 8
        elif cv <= 0.15:
            confidence = 8 - ((cv - 0.05) * 20)  # 8 to 6
        elif cv <= 0.30:
            confidence = 6 - ((cv - 0.15) * 20)  # 6 to 3
        else:
            confidence = max(1, 3 - ((cv - 0.30) * 10))

        # Bonus for multiple sources
        confidence += (len(values) - 1) * 0.5

        return round(min(10, max(1, confidence)), 1)

    def _get_methodology(
        self,
        attom: Optional[int],
        rentcast: Optional[int],
        comps: Optional[int]
    ) -> str:
        """Generate description of valuation methodology used."""
        sources = []
        if attom:
            sources.append("ATTOM market value")
        if rentcast:
            sources.append("RentCast AVM")
        if comps:
            sources.append("comparable sales analysis")

        if not sources:
            return "No valuation sources available"
        elif len(sources) == 1:
            return f"Single-source valuation using {sources[0]}"
        else:
            return f"Triangulated valuation using {', '.join(sources[:-1])} and {sources[-1]}"

    def _format_comparables(self, comps: List[ComparableSale]) -> List[Dict]:
        """Format comparable sales for output."""
        formatted = []
        for comp in comps:
            formatted.append({
                'address': comp.address,
                'sale_price': comp.sale_price,
                'sale_date': comp.sale_date,
                'distance_miles': round(comp.distance_miles, 2) if comp.distance_miles else 0,
                'sqft': comp.sqft or 0,
                'price_per_sqft': round(comp.sale_price / comp.sqft, 2) if comp.sqft and comp.sqft > 0 else 0,
                'bedrooms': comp.bedrooms,
                'bathrooms': comp.bathrooms
            })
        return formatted

    def _comp_to_dict(self, comp: ComparableSale) -> Dict:
        """Convert ComparableSale dataclass to dict for analyzer."""
        return {
            'address': comp.address,
            'sale_price': comp.sale_price,
            'sale_date': comp.sale_date,
            'sqft': comp.sqft,
            'bedrooms': comp.bedrooms,
            'bathrooms': comp.bathrooms,
            'distance_miles': comp.distance_miles
        }

    def _generate_forecast(self, current_value: int, confidence: float) -> Dict:
        """Generate multi-period forecast."""
        # Determine market trend based on Loudoun County conditions
        market_trend = 'moderate'  # Could be enhanced with market data

        forecast_1y = self.forecast_engine.generate_forecast(
            current_value=current_value,
            months=12,
            market_trend=market_trend,
            confidence_score=confidence * 10
        )

        forecast_3y = self.forecast_engine.generate_forecast(
            current_value=current_value,
            months=36,
            market_trend=market_trend,
            confidence_score=confidence * 10
        )

        forecast_5y = self.forecast_engine.generate_forecast(
            current_value=current_value,
            months=60,
            market_trend=market_trend,
            confidence_score=confidence * 10
        )

        # Determine confidence level description
        conf_score = forecast_1y.confidence_score
        if conf_score >= 70:
            conf_level = "High"
        elif conf_score >= 50:
            conf_level = "Moderate"
        else:
            conf_level = "Low"

        return {
            '1_year': {
                'value': forecast_1y.mid_estimate,
                'change_pct': round((forecast_1y.mid_estimate - current_value) / current_value * 100, 1)
            },
            '3_year': {
                'value': forecast_3y.mid_estimate,
                'change_pct': round((forecast_3y.mid_estimate - current_value) / current_value * 100, 1)
            },
            '5_year': {
                'value': forecast_5y.mid_estimate,
                'change_pct': round((forecast_5y.mid_estimate - current_value) / current_value * 100, 1)
            },
            'confidence': conf_level,
            'factors': forecast_1y.factors
        }

    def _assess_cash_flow(self, gross_yield: float) -> str:
        """Assess cash flow potential based on gross yield."""
        if gross_yield >= 8:
            return "Excellent - Strong positive cash flow likely"
        elif gross_yield >= 6:
            return "Good - Positive cash flow achievable"
        elif gross_yield >= 4:
            return "Moderate - Break-even to modest cash flow"
        else:
            return "Limited - May require appreciation for returns"

    def _assess_psf_position(self, property_psf: float, avg_psf: float) -> str:
        """Assess property's price per sqft relative to comps."""
        if avg_psf == 0:
            return "Insufficient data"

        diff_pct = ((property_psf - avg_psf) / avg_psf) * 100

        if diff_pct < -15:
            return "Significantly below market"
        elif diff_pct < -5:
            return "Below market"
        elif diff_pct < 5:
            return "At market"
        elif diff_pct < 15:
            return "Above market"
        else:
            return "Significantly above market"

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure."""
        return {
            'current_value': {
                'attom_estimate': 0,
                'rentcast_estimate': 0,
                'triangulated_estimate': 0,
                'confidence_score': 0,
                'methodology': 'No data available'
            },
            'comparable_sales': [],
            'forecast': {
                '1_year': {'value': 0, 'change_pct': 0},
                '3_year': {'value': 0, 'change_pct': 0},
                '5_year': {'value': 0, 'change_pct': 0},
                'confidence': 'Low',
                'factors': []
            },
            'rental_analysis': {
                'estimated_rent_monthly': 0,
                'gross_yield_pct': 0,
                'area_avg_yield_pct': 0,
                'cash_flow_potential': 'Unknown'
            },
            'price_per_sqft': {
                'property': 0,
                'neighborhood_avg': 0,
                'comps': [],
                'position': 'Unknown'
            },
            'data_sources': [],
            'analysis_date': '',
            'api_mode': 'live',
            'sales_history': {
                'found': False,
                'sales': [],
                'error': None
            }
        }


if __name__ == '__main__':
    # Test the orchestrator
    print("=" * 60)
    print("PROPERTY VALUATION ORCHESTRATOR TEST")
    print("=" * 60)

    orchestrator = PropertyValuationOrchestrator()

    # Test with 43500 Tuckaway Pl
    result = orchestrator.analyze_property(
        address="43500 Tuckaway Pl, Leesburg, VA 20176",
        lat=39.112665,
        lon=-77.495668,
        sqft=3468
    )

    print(f"\nCurrent Value Estimate:")
    print(f"  ATTOM: ${result['current_value']['attom_estimate']:,.0f}")
    print(f"  RentCast: ${result['current_value']['rentcast_estimate']:,.0f}")
    print(f"  Triangulated: ${result['current_value']['triangulated_estimate']:,.0f}")
    print(f"  Confidence: {result['current_value']['confidence_score']}/10")
    print(f"  Methodology: {result['current_value']['methodology']}")

    if result['forecast']['1_year']['value'] > 0:
        print(f"\nForecast:")
        print(f"  1-Year: ${result['forecast']['1_year']['value']:,.0f} ({result['forecast']['1_year']['change_pct']:+.1f}%)")
        print(f"  3-Year: ${result['forecast']['3_year']['value']:,.0f} ({result['forecast']['3_year']['change_pct']:+.1f}%)")
        print(f"  5-Year: ${result['forecast']['5_year']['value']:,.0f} ({result['forecast']['5_year']['change_pct']:+.1f}%)")

    if result['rental_analysis']['estimated_rent_monthly'] > 0:
        print(f"\nRental Analysis:")
        print(f"  Est. Monthly Rent: ${result['rental_analysis']['estimated_rent_monthly']:,.0f}")
        print(f"  Gross Yield: {result['rental_analysis']['gross_yield_pct']:.1f}%")
        print(f"  Cash Flow: {result['rental_analysis']['cash_flow_potential']}")

    print(f"\nComparable Sales: {len(result['comparable_sales'])} properties")
    for i, comp in enumerate(result['comparable_sales'][:3], 1):
        print(f"  {i}. {comp['address'][:40]} - ${comp['sale_price']:,.0f}")

    print(f"\nData Sources: {', '.join(result['data_sources'])}")
    print(f"Analysis Date: {result['analysis_date']}")

    print("\n" + "=" * 60)
    print("✓ Orchestrator test complete!")
    print("=" * 60)
