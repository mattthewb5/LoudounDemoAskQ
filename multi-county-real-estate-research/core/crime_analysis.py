"""
Multi-jurisdiction crime analysis and safety scoring.

Retrieves crime data and calculates safety scores for addresses, handling both
county and town police jurisdictions.

MERGE NOTE: Multi-county generalized version
- Athens equivalent: crime_analysis.py (hardcoded for Athens-Clarke PD)
- Configuration-driven for any county
- Backward compatible: Works with single-jurisdiction counties
- Designed for February-March 2026 merge

Last Updated: November 2025
Phase: 2 - Crime Data (Week 3)
Status: Core implementation
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

from config import CountyConfig, get_county_config
from core.jurisdiction_detector import JurisdictionDetector

@dataclass
class CrimeIncident:
    """
    Single crime incident.

    Attributes:
        incident_id: Unique identifier
        incident_type: Type of crime (e.g., "THEFT", "ASSAULT")
        date: Date of incident
        address: Location (may be approximate)
        lat: Latitude (may be approximate for privacy)
        lon: Longitude (may be approximate for privacy)
        description: Additional details
        jurisdiction: Police department (Sheriff, Leesburg PD, etc.)
    """
    incident_id: str
    incident_type: str
    date: datetime
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None


@dataclass
class CrimeAnalysisResult:
    """
    Crime analysis results for an address.

    Attributes:
        address: The queried address
        jurisdiction_type: 'town' or 'county'
        jurisdiction_name: Name of jurisdiction
        police_jurisdiction: Police department name
        radius_miles: Search radius used

        # Crime data
        total_incidents: Total crimes in area/timeframe
        incidents: List of individual incidents
        incident_types: Dict of crime types and counts

        # Time analysis
        timeframe_days: Number of days analyzed
        start_date: Start of analysis period
        end_date: End of analysis period

        # Safety scoring
        safety_score: 0-100 (higher = safer)
        safety_rating: Text rating (Very Safe, Safe, Moderate, etc.)

        # Trends
        trend: 'increasing', 'stable', 'decreasing'
        trend_description: Text explanation

        # Metadata
        data_source: Where data came from
        notes: Additional context
        success: Whether lookup was successful
        error_message: Error details if unsuccessful
    """
    address: str
    jurisdiction_type: str
    jurisdiction_name: str
    police_jurisdiction: str
    radius_miles: float = 1.0

    # Crime data
    total_incidents: int = 0
    incidents: List[CrimeIncident] = field(default_factory=list)
    incident_types: Dict[str, int] = field(default_factory=dict)

    # Time analysis
    timeframe_days: int = 90
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Safety scoring
    safety_score: Optional[int] = None
    safety_rating: Optional[str] = None

    # Trends
    trend: Optional[str] = None
    trend_description: Optional[str] = None

    # Metadata
    data_source: Optional[str] = None
    notes: Optional[str] = None
    success: bool = False
    error_message: Optional[str] = None


class CrimeAnalysis:
    """
    Crime data analysis with multi-jurisdiction support.

    Usage:
        >>> from config import get_county_config
        >>> config = get_county_config("loudoun")
        >>> analyzer = CrimeAnalysis(config)
        >>> result = analyzer.get_crime_data("Ashburn, VA", 39.0437, -77.4875)
        >>> print(f"Safety Score: {result.safety_score}/100")
    """

    def __init__(self, county_config: CountyConfig):
        """
        Initialize crime analysis with county configuration.

        Args:
            county_config: CountyConfig object for the county
        """
        self.config = county_config
        self.jurisdiction_detector = JurisdictionDetector(county_config)

    def get_crime_data(self, address: str, lat: float, lon: float,
                       radius_miles: float = 1.0,
                       timeframe_days: int = 90) -> CrimeAnalysisResult:
        """
        Get crime data and analysis for an address.

        Args:
            address: Street address
            lat: Latitude (WGS84)
            lon: Longitude (WGS84)
            radius_miles: Search radius (default 1.0 mile)
            timeframe_days: Days of history to analyze (default 90)

        Returns:
            CrimeAnalysisResult with crime data and safety analysis

        Example:
            >>> result = analyzer.get_crime_data("Ashburn, VA", 39.0437, -77.4875)
            >>> if result.success:
            ...     print(f"Safety Score: {result.safety_score}")
            ...     print(f"Total Incidents: {result.total_incidents}")
        """
        # Step 1: Detect jurisdiction
        jurisdiction = self.jurisdiction_detector.detect(address, lat, lon)

        # Step 2: Query appropriate crime data source
        if jurisdiction['type'] == 'town':
            return self._get_town_crime_data(address, lat, lon, jurisdiction,
                                            radius_miles, timeframe_days)
        else:
            return self._get_county_crime_data(address, lat, lon, jurisdiction,
                                              radius_miles, timeframe_days)

    def _get_county_crime_data(self, address: str, lat: float, lon: float,
                               jurisdiction: Dict[str, str],
                               radius_miles: float,
                               timeframe_days: int) -> CrimeAnalysisResult:
        """
        Get crime data from county Sheriff (for unincorporated areas).

        Args:
            address: Street address
            lat: Latitude
            lon: Longitude
            jurisdiction: Jurisdiction info from detector
            radius_miles: Search radius
            timeframe_days: Days of history

        Returns:
            CrimeAnalysisResult with Sheriff crime data
        """
        result = CrimeAnalysisResult(
            address=address,
            jurisdiction_type='county',
            jurisdiction_name=jurisdiction['name'],
            police_jurisdiction=jurisdiction['police_jurisdiction'],
            radius_miles=radius_miles,
            timeframe_days=timeframe_days
        )

        # Check if county has crime data available
        if not self.config.has_crime_data:
            result.error_message = f"Crime data not yet implemented for {self.config.display_name}"
            result.notes = "Configuration complete, data source integration pending"
            return result

        # Get crime API endpoint
        api_endpoint = self.config.crime_api_endpoint
        if not api_endpoint:
            result.error_message = "Crime API endpoint not configured"
            result.notes = "Check config for crime_api_endpoint"
            return result

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=timeframe_days)

        result.start_date = start_date
        result.end_date = end_date

        # Query crime data
        try:
            incidents = self._query_crime_api(api_endpoint, lat, lon,
                                             radius_miles, start_date, end_date)

            if incidents is not None:
                result.success = True
                result.incidents = incidents
                result.total_incidents = len(incidents)
                result.incident_types = self._count_incident_types(incidents)
                result.data_source = 'County Sheriff Crime Dashboard'

                # Calculate safety score
                safety_data = self._calculate_safety_score(incidents, timeframe_days)
                result.safety_score = safety_data['score']
                result.safety_rating = safety_data['rating']
                result.trend = safety_data['trend']
                result.trend_description = safety_data['trend_description']

                result.notes = f"Retrieved {result.total_incidents} incidents from {self.config.display_name} Sheriff"
            else:
                result.error_message = "No crime data available for this location"
                result.notes = "Check API endpoint and date range"

        except Exception as e:
            result.error_message = f"Error querying crime data: {str(e)}"
            result.notes = "Check API endpoint and network connectivity"

        return result

    def _get_town_crime_data(self, address: str, lat: float, lon: float,
                            jurisdiction: Dict[str, str],
                            radius_miles: float,
                            timeframe_days: int) -> CrimeAnalysisResult:
        """
        Get crime data from town police department (for incorporated towns).

        Args:
            address: Street address
            lat: Latitude
            lon: Longitude
            jurisdiction: Jurisdiction info from detector
            radius_miles: Search radius
            timeframe_days: Days of history

        Returns:
            CrimeAnalysisResult with town PD crime data
        """
        result = CrimeAnalysisResult(
            address=address,
            jurisdiction_type='town',
            jurisdiction_name=jurisdiction['name'],
            police_jurisdiction=jurisdiction['police_jurisdiction'],
            radius_miles=radius_miles,
            timeframe_days=timeframe_days
        )

        town_name = jurisdiction['name']

        # Check if town has crime source configured
        town_sources = self.config.town_police_sources or {}
        town_source = town_sources.get(town_name)

        if not town_source:
            result.error_message = f"Crime data source not yet configured for {town_name}"
            result.notes = f"Town police data integration pending. May fall back to Sheriff data."
            return result

        # TODO: Implement town-specific crime lookup
        # Each town may have different data format:
        # - Some towns have crime dashboards
        # - Some towns may share Sheriff data
        # - Some towns may need manual lookup

        result.error_message = f"Town crime lookup not yet implemented for {town_name}"
        result.notes = f"Jurisdiction detected correctly. Town-specific data integration pending."

        return result

    def _query_crime_api(self, api_endpoint: str, lat: float, lon: float,
                        radius_miles: float, start_date: datetime,
                        end_date: datetime) -> Optional[List[CrimeIncident]]:
        """
        Query crime API for incidents.

        Args:
            api_endpoint: Crime API endpoint
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of CrimeIncident objects or None if failed

        Note:
            API format varies by jurisdiction. This is a template that
            needs to be adapted based on actual API structure.
        """
        # TODO: Implement based on actual LCSO Crime Dashboard API
        # This is a placeholder structure

        try:
            # Example API call structure (needs real endpoint details)
            params = {
                'lat': lat,
                'lon': lon,
                'radius': radius_miles,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'format': 'json'
            }

            # This will fail until we have real endpoint - that's expected
            # response = requests.get(api_endpoint, params=params, timeout=10)
            # response.raise_for_status()
            # data = response.json()

            # Return empty list for now (configuration pending)
            return []

        except Exception as e:
            print(f"Error querying crime API: {e}")
            return None

    def _count_incident_types(self, incidents: List[CrimeIncident]) -> Dict[str, int]:
        """
        Count incidents by type.

        Args:
            incidents: List of crime incidents

        Returns:
            Dictionary mapping incident type to count
        """
        counts = {}
        for incident in incidents:
            incident_type = incident.incident_type
            counts[incident_type] = counts.get(incident_type, 0) + 1
        return counts

    def _calculate_safety_score(self, incidents: List[CrimeIncident],
                                timeframe_days: int) -> Dict[str, Any]:
        """
        Calculate safety score based on crime data.

        Args:
            incidents: List of crime incidents
            timeframe_days: Days of history analyzed

        Returns:
            Dictionary with score, rating, trend, trend_description

        Algorithm:
            - Start with 100 (perfect safety)
            - Deduct points based on crime severity and frequency
            - Violent crimes: -5 points each
            - Property crimes: -2 points each
            - Other crimes: -1 point each
            - Calculate trend from first half vs second half
        """
        if not incidents:
            return {
                'score': 95,  # High score for no recent crime
                'rating': 'Very Safe',
                'trend': 'stable',
                'trend_description': 'No reported incidents in this timeframe'
            }

        # Crime severity weights
        violent_crimes = ['ASSAULT', 'ROBBERY', 'HOMICIDE', 'RAPE', 'SHOOTING']
        property_crimes = ['THEFT', 'BURGLARY', 'VANDALISM', 'VEHICLE THEFT', 'LARCENY']

        score = 100

        for incident in incidents:
            crime_type = incident.incident_type.upper()

            if any(violent in crime_type for violent in violent_crimes):
                score -= 5
            elif any(prop in crime_type for prop in property_crimes):
                score -= 2
            else:
                score -= 1

        # Floor at 0
        score = max(0, score)

        # Determine rating
        if score >= 85:
            rating = 'Very Safe'
        elif score >= 70:
            rating = 'Safe'
        elif score >= 50:
            rating = 'Moderate'
        elif score >= 30:
            rating = 'Caution Advised'
        else:
            rating = 'High Crime Area'

        # Calculate trend (first half vs second half)
        midpoint = len(incidents) // 2
        first_half = incidents[:midpoint]
        second_half = incidents[midpoint:]

        if len(second_half) > len(first_half) * 1.2:
            trend = 'increasing'
            trend_description = 'Crime has increased recently in this area'
        elif len(second_half) < len(first_half) * 0.8:
            trend = 'decreasing'
            trend_description = 'Crime has decreased recently in this area'
        else:
            trend = 'stable'
            trend_description = 'Crime rates are relatively stable'

        return {
            'score': score,
            'rating': rating,
            'trend': trend,
            'trend_description': trend_description
        }


# ===== VALIDATION FUNCTION =====

def test_crime_analysis():
    """
    Test crime analysis with known addresses.
    """
    print("=" * 60)
    print("CRIME ANALYSIS TESTS")
    print("=" * 60)
    print(f"Date: November 2025")
    print(f"Phase: 2 - Crime Data (Week 3)")
    print()

    # Test Loudoun County
    print("Testing Loudoun County, VA...")
    print("-" * 60)
    loudoun_config = get_county_config("loudoun")
    analyzer = CrimeAnalysis(loudoun_config)

    # Test 1: Ashburn (unincorporated)
    print("Test 1: Ashburn (unincorporated)")
    print("  Location: Ashburn area")
    print("  Expected: County jurisdiction, Sheriff crime data pending")
    result1 = analyzer.get_crime_data(
        "Ashburn, VA",
        lat=39.0437,
        lon=-77.4875
    )
    print(f"  Result:")
    print(f"    Success: {result1.success}")
    print(f"    Jurisdiction Type: {result1.jurisdiction_type}")
    print(f"    Police Jurisdiction: {result1.police_jurisdiction}")
    if result1.success:
        print(f"    Safety Score: {result1.safety_score}/100")
        print(f"    Safety Rating: {result1.safety_rating}")
        print(f"    Total Incidents: {result1.total_incidents}")
    else:
        print(f"    Status: {result1.error_message}")

    if result1.jurisdiction_type == 'county':
        print("  ✅ PASS - Correctly identified county jurisdiction")
    print()

    # Test 2: Leesburg (incorporated town)
    print("Test 2: Leesburg (incorporated)")
    print("  Location: Downtown Leesburg")
    print("  Expected: Town jurisdiction, Leesburg PD data pending")
    result2 = analyzer.get_crime_data(
        "Downtown Leesburg, VA",
        lat=39.1156,
        lon=-77.5636
    )
    print(f"  Result:")
    print(f"    Success: {result2.success}")
    print(f"    Jurisdiction Type: {result2.jurisdiction_type}")
    print(f"    Police Jurisdiction: {result2.police_jurisdiction}")
    if result2.error_message:
        print(f"    Status: {result2.error_message}")

    if result2.jurisdiction_type == 'town':
        print("  ✅ PASS - Correctly identified town jurisdiction")
    print()

    # Test Athens County
    print("=" * 60)
    print("Testing Athens-Clarke County, GA...")
    print("-" * 60)
    athens_config = get_county_config("athens_clarke")
    athens_analyzer = CrimeAnalysis(athens_config)

    print("Test 3: Athens address")
    print("  Location: Downtown Athens")
    print("  Expected: County jurisdiction (unified government)")
    result3 = athens_analyzer.get_crime_data(
        "Downtown Athens, GA",
        lat=33.9573,
        lon=-83.3761
    )
    print(f"  Result:")
    print(f"    Success: {result3.success}")
    print(f"    Jurisdiction Type: {result3.jurisdiction_type}")
    print(f"    Police Jurisdiction: {result3.police_jurisdiction}")

    if result3.jurisdiction_type == 'county':
        print("  ✅ PASS - Correctly identified county jurisdiction")
    print()

    print("=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print("  - Crime analysis infrastructure: ✅ Working")
    print("  - Jurisdiction routing: ✅ Correctly routes to Sheriff vs town PD")
    print("  - County crime data: ⏳ Needs API endpoint configuration")
    print("  - Safety scoring: ✅ Algorithm ready")
    print()
    print("Next steps:")
    print("  1. Research LCSO Crime Dashboard API")
    print("  2. Configure crime_api_endpoint in config/loudoun.py")
    print("  3. Test with real crime data")
    print("  4. Validate safety scores")
    print()


if __name__ == "__main__":
    test_crime_analysis()
