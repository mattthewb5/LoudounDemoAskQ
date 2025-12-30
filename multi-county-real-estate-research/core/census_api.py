"""
Census Bureau and BLS API Clients for Demographics Data

Census Client:
    Fetches American Community Survey (ACS) 5-Year data at block group level
    for demographic analysis within specified radii of a property.

BLS Client:
    Fetches Bureau of Labor Statistics Local Area Unemployment Statistics (LAUS)
    for current monthly unemployment data at the county level.

Usage:
    from core.census_api import CensusClient, get_census_client
    from core.census_api import BLSClient, get_bls_client

    # Census data
    client = get_census_client()
    block_groups = client.get_block_group_data(state='51', county='107')
    county_data = client.get_county_data(state='51', county='107')

    # BLS data
    bls_client = get_bls_client()
    unemployment = bls_client.get_county_unemployment(state_fips='51', county_fips='107')

API Documentation:
    Census: https://www.census.gov/data/developers/data-sets/acs-5year.html
    BLS: https://www.bls.gov/developers/api_signature_v2.htm
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.api_config import get_api_key


# Census API Base URL
CENSUS_API_BASE = "https://api.census.gov/data"

# ACS 5-Year Dataset (2019-2023 is latest)
ACS_YEAR = "2023"
ACS_DATASET = "acs/acs5"

# Virginia FIPS
STATE_FIPS = "51"

# Loudoun County FIPS
LOUDOUN_COUNTY_FIPS = "107"

# BLS API Configuration
BLS_API_BASE = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# BLS LAUS Series ID Format:
# LAUCN + [State FIPS 2 digits] + [County FIPS 3 digits] + 00000000 + [Measure Code 2 digits]
# Measure codes: 03 = unemployment rate, 04 = unemployment, 05 = employment, 06 = labor force
BLS_MEASURE_UNEMPLOYMENT_RATE = "03"
BLS_MEASURE_LABOR_FORCE = "06"  # Labor force count (not participation rate)


# Required Census Variables for Demographics
CENSUS_VARIABLES = {
    # Population
    'B01003_001E': 'total_population',
    'B01002_001E': 'median_age',

    # Age Distribution (for chart)
    'B01001_003E': 'male_under_5',
    'B01001_004E': 'male_5_9',
    'B01001_005E': 'male_10_14',
    'B01001_006E': 'male_15_17',
    'B01001_007E': 'male_18_19',
    'B01001_008E': 'male_20',
    'B01001_009E': 'male_21',
    'B01001_010E': 'male_22_24',
    'B01001_011E': 'male_25_29',
    'B01001_012E': 'male_30_34',
    'B01001_013E': 'male_35_39',
    'B01001_014E': 'male_40_44',
    'B01001_015E': 'male_45_49',
    'B01001_016E': 'male_50_54',
    'B01001_017E': 'male_55_59',
    'B01001_018E': 'male_60_61',
    'B01001_019E': 'male_62_64',
    'B01001_020E': 'male_65_66',
    'B01001_021E': 'male_67_69',
    'B01001_022E': 'male_70_74',
    'B01001_023E': 'male_75_79',
    'B01001_024E': 'male_80_84',
    'B01001_025E': 'male_85_plus',
    'B01001_027E': 'female_under_5',
    'B01001_028E': 'female_5_9',
    'B01001_029E': 'female_10_14',
    'B01001_030E': 'female_15_17',
    'B01001_031E': 'female_18_19',
    'B01001_032E': 'female_20',
    'B01001_033E': 'female_21',
    'B01001_034E': 'female_22_24',
    'B01001_035E': 'female_25_29',
    'B01001_036E': 'female_30_34',
    'B01001_037E': 'female_35_39',
    'B01001_038E': 'female_40_44',
    'B01001_039E': 'female_45_49',
    'B01001_040E': 'female_50_54',
    'B01001_041E': 'female_55_59',
    'B01001_042E': 'female_60_61',
    'B01001_043E': 'female_62_64',
    'B01001_044E': 'female_65_66',
    'B01001_045E': 'female_67_69',
    'B01001_046E': 'female_70_74',
    'B01001_047E': 'female_75_79',
    'B01001_048E': 'female_80_84',
    'B01001_049E': 'female_85_plus',

    # Households
    'B11001_001E': 'total_households',
    'B25010_001E': 'avg_household_size',
    'B25003_002E': 'owner_occupied',
    'B25003_003E': 'renter_occupied',

    # Income
    'B19013_001E': 'median_household_income',
    'B19025_001E': 'aggregate_household_income',

    # Income Distribution (for chart) - B19001 series
    'B19001_002E': 'income_under_10k',
    'B19001_003E': 'income_10k_15k',
    'B19001_004E': 'income_15k_20k',
    'B19001_005E': 'income_20k_25k',
    'B19001_006E': 'income_25k_30k',
    'B19001_007E': 'income_30k_35k',
    'B19001_008E': 'income_35k_40k',
    'B19001_009E': 'income_40k_45k',
    'B19001_010E': 'income_45k_50k',
    'B19001_011E': 'income_50k_60k',
    'B19001_012E': 'income_60k_75k',
    'B19001_013E': 'income_75k_100k',
    'B19001_014E': 'income_100k_125k',
    'B19001_015E': 'income_125k_150k',
    'B19001_016E': 'income_150k_200k',
    'B19001_017E': 'income_200k_plus',

    # Education (Bachelor's degree and higher for population 25+)
    'B15003_001E': 'edu_total_25_plus',
    'B15003_022E': 'edu_bachelors',
    'B15003_023E': 'edu_masters',
    'B15003_024E': 'edu_professional',
    'B15003_025E': 'edu_doctorate',

    # Employment
    'B23025_003E': 'labor_force',
    'B23025_005E': 'unemployed',
    'B23025_002E': 'labor_force_16_plus',  # Total in labor force (for participation rate)
}

# Block group geography variables
GEO_VARIABLES = ['NAME', 'GEO_ID']


class CensusAPIError(Exception):
    """Custom exception for Census API errors."""
    pass


class BLSAPIError(Exception):
    """Custom exception for BLS API errors."""
    pass


class CensusClient:
    """
    Client for fetching Census Bureau ACS 5-Year data.

    Supports fetching data at block group and county levels for
    demographic analysis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Census API client.

        Args:
            api_key: Census API key. If not provided, will attempt to
                    load from config via get_api_key('CENSUS_API_KEY')
        """
        self.api_key = api_key or get_api_key('CENSUS_API_KEY')
        self.base_url = f"{CENSUS_API_BASE}/{ACS_YEAR}/{ACS_DATASET}"
        self._session = requests.Session()

    def _build_variable_batches(self, max_per_batch: int = 48) -> List[List[str]]:
        """
        Split Census variables into batches to respect API limits.

        The Census API limits requests to 50 variables. We use 48 to leave
        room for geography fields (NAME, state, county, tract, block group).

        Args:
            max_per_batch: Maximum variables per request

        Returns:
            List of variable lists, each with at most max_per_batch items
        """
        all_vars = list(CENSUS_VARIABLES.keys())
        batches = []
        for i in range(0, len(all_vars), max_per_batch):
            batches.append(all_vars[i:i + max_per_batch])
        return batches

    def _parse_response(self, response_data: List[List], include_geo: bool = True) -> List[Dict[str, Any]]:
        """
        Parse Census API response into list of dictionaries.

        Args:
            response_data: Raw API response (list of lists with header row)
            include_geo: Whether geography columns are included

        Returns:
            List of dictionaries with variable names as keys
        """
        if not response_data or len(response_data) < 2:
            return []

        headers = response_data[0]
        results = []

        for row in response_data[1:]:
            record = {}
            for i, header in enumerate(headers):
                value = row[i] if i < len(row) else None

                # Convert numeric values
                if header in CENSUS_VARIABLES:
                    try:
                        # Census uses -666666666 for missing data
                        if value is None or value == '' or int(float(value)) < 0:
                            record[CENSUS_VARIABLES[header]] = None
                        else:
                            record[CENSUS_VARIABLES[header]] = int(float(value))
                    except (ValueError, TypeError):
                        record[CENSUS_VARIABLES[header]] = None
                else:
                    # Keep geography and other fields as strings
                    record[header] = value

            results.append(record)

        return results

    def _fetch_batch(
        self,
        variables: List[str],
        geo_for: str,
        geo_in: str
    ) -> List[List]:
        """
        Fetch a single batch of variables from Census API.

        Args:
            variables: List of Census variable codes
            geo_for: Geography 'for' clause (e.g., 'block group:*')
            geo_in: Geography 'in' clause (e.g., 'state:51&in=county:107')

        Returns:
            Raw API response data (list of lists)
        """
        var_str = ','.join(variables)
        url = (
            f"{self.base_url}?get=NAME,{var_str}"
            f"&for={geo_for}"
            f"&in={geo_in}"
            f"&key={self.api_key}"
        )

        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def _merge_batch_results(
        self,
        batch_results: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Merge results from multiple batched API calls.

        Uses geography fields (state, county, tract, block group) as keys
        to combine data from multiple batches.

        Args:
            batch_results: List of parsed results from each batch

        Returns:
            Merged list of dictionaries with all variables
        """
        if not batch_results:
            return []

        # Use first batch as base
        merged = {self._make_geo_key(r): dict(r) for r in batch_results[0]}

        # Merge subsequent batches
        for batch in batch_results[1:]:
            for record in batch:
                key = self._make_geo_key(record)
                if key in merged:
                    # Add new variables to existing record
                    for k, v in record.items():
                        if k not in ['NAME', 'state', 'county', 'tract', 'block group']:
                            merged[key][k] = v
                else:
                    merged[key] = dict(record)

        return list(merged.values())

    def _make_geo_key(self, record: Dict) -> str:
        """Create a unique key from geography fields."""
        return f"{record.get('state', '')}-{record.get('county', '')}-{record.get('tract', '')}-{record.get('block group', '')}"

    def get_block_group_data(
        self,
        state: str = STATE_FIPS,
        county: str = LOUDOUN_COUNTY_FIPS
    ) -> List[Dict[str, Any]]:
        """
        Fetch all block group data for a county.

        Makes multiple API calls if needed to handle the 50-variable limit.

        Args:
            state: State FIPS code (default: 51 for Virginia)
            county: County FIPS code (default: 107 for Loudoun)

        Returns:
            List of dictionaries, one per block group, with demographic data

        Raises:
            CensusAPIError: If API request fails
        """
        if not self.api_key:
            raise CensusAPIError(
                "Census API key not configured. "
                "Set CENSUS_API_KEY in ~/.config/newco/api_keys.json"
            )

        batches = self._build_variable_batches()
        geo_for = "block%20group:*"
        geo_in = f"state:{state}&in=county:{county}"

        try:
            batch_results = []
            for batch_vars in batches:
                data = self._fetch_batch(batch_vars, geo_for, geo_in)
                parsed = self._parse_response(data)
                batch_results.append(parsed)

            return self._merge_batch_results(batch_results)

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    raise CensusAPIError(
                        f"Invalid Census API request: {e.response.text}"
                    )
                elif e.response.status_code == 401:
                    raise CensusAPIError(
                        "Invalid Census API key. Please verify your key."
                    )
                else:
                    raise CensusAPIError(
                        f"Census API HTTP error {e.response.status_code}: {e}"
                    )
            raise CensusAPIError(f"Census API HTTP error: {e}")

        except requests.exceptions.RequestException as e:
            raise CensusAPIError(f"Census API request failed: {e}")

        except ValueError as e:
            raise CensusAPIError(f"Failed to parse Census API response: {e}")

    def get_county_data(
        self,
        state: str = STATE_FIPS,
        county: str = LOUDOUN_COUNTY_FIPS
    ) -> Dict[str, Any]:
        """
        Fetch county-level demographic data for comparison.

        Makes multiple API calls if needed to handle the 50-variable limit.

        Args:
            state: State FIPS code (default: 51 for Virginia)
            county: County FIPS code (default: 107 for Loudoun)

        Returns:
            Dictionary with county-level demographic data

        Raises:
            CensusAPIError: If API request fails
        """
        if not self.api_key:
            raise CensusAPIError(
                "Census API key not configured. "
                "Set CENSUS_API_KEY in ~/.config/newco/api_keys.json"
            )

        batches = self._build_variable_batches()
        geo_for = f"county:{county}"
        geo_in = f"state:{state}"

        try:
            batch_results = []
            for batch_vars in batches:
                data = self._fetch_batch(batch_vars, geo_for, geo_in)
                parsed = self._parse_response(data)
                batch_results.append(parsed)

            merged = self._merge_batch_results(batch_results)

            if merged:
                return merged[0]
            else:
                raise CensusAPIError("No county data returned")

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    raise CensusAPIError(
                        f"Invalid Census API request: {e.response.text}"
                    )
                elif e.response.status_code == 401:
                    raise CensusAPIError(
                        "Invalid Census API key. Please verify your key."
                    )
                else:
                    raise CensusAPIError(
                        f"Census API HTTP error {e.response.status_code}: {e}"
                    )
            raise CensusAPIError(f"Census API HTTP error: {e}")

        except requests.exceptions.RequestException as e:
            raise CensusAPIError(f"Census API request failed: {e}")

        except ValueError as e:
            raise CensusAPIError(f"Failed to parse Census API response: {e}")

    def get_block_group_centroids(
        self,
        state: str = STATE_FIPS,
        county: str = LOUDOUN_COUNTY_FIPS
    ) -> List[Dict[str, Any]]:
        """
        Fetch block group centroids from Census Tiger/Line.

        This is used to identify which block groups fall within
        a given radius of a property.

        Note: For MVP, we use a simplified approach where we calculate
        approximate centroids from the block group FIPS code pattern.
        A full implementation would use the TIGERweb API or shapefiles.

        Args:
            state: State FIPS code
            county: County FIPS code

        Returns:
            List of dicts with block group IDs and centroid coordinates
        """
        # For MVP, centroids will be fetched from a supplementary source
        # or calculated from shapefile data in demographics_calculator.py
        # This method is a placeholder for future enhancement
        raise NotImplementedError(
            "Block group centroids require TIGERweb API or shapefile data. "
            "Use demographics_calculator.py for spatial calculations."
        )


class BLSClient:
    """
    Client for fetching Bureau of Labor Statistics unemployment data.

    Uses the BLS LAUS (Local Area Unemployment Statistics) API to get
    current monthly unemployment rates at the county level.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize BLS API client.

        Args:
            api_key: BLS API key. If not provided, will attempt to
                    load from config via get_api_key('BLS_API_KEY')
        """
        self.api_key = api_key or get_api_key('BLS_API_KEY')
        self.base_url = BLS_API_BASE
        self._session = requests.Session()

    def _build_series_id(
        self,
        state_fips: str,
        county_fips: str,
        measure: str = BLS_MEASURE_UNEMPLOYMENT_RATE
    ) -> str:
        """
        Build a BLS LAUS series ID for a county.

        Format: LAUCN + [State FIPS 2 digits] + [County FIPS 3 digits] + 00000000 + [Measure Code]

        Args:
            state_fips: 2-digit state FIPS code (e.g., '51' for Virginia)
            county_fips: 3-digit county FIPS code (e.g., '107' for Loudoun)
            measure: 2-digit measure code ('03' = unemployment rate)

        Returns:
            BLS series ID string (e.g., 'LAUCN511070000000003' for Loudoun County)
        """
        # Ensure proper formatting
        state = state_fips.zfill(2)
        county = county_fips.zfill(3)
        return f"LAUCN{state}{county}00000000{measure}"

    def get_county_unemployment(
        self,
        state_fips: str = STATE_FIPS,
        county_fips: str = LOUDOUN_COUNTY_FIPS,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current unemployment rate for a county.

        Args:
            state_fips: State FIPS code (default: 51 for Virginia)
            county_fips: County FIPS code (default: 107 for Loudoun)
            start_year: Start year for data (default: current year - 1)
            end_year: End year for data (default: current year)

        Returns:
            Dictionary with unemployment data:
            {
                'rate': 2.8,
                'period': 'November',
                'year': '2024',
                'series_id': 'LAUCN511070000000003',
                'source': 'BLS LAUS (Monthly)'
            }

        Raises:
            BLSAPIError: If API request fails
        """
        if not self.api_key:
            raise BLSAPIError(
                "BLS API key not configured. "
                "Set BLS_API_KEY in ~/.config/newco/api_keys.json"
            )

        # Default to fetching last 2 years of data to ensure we have recent data
        current_year = datetime.now().year
        if not start_year:
            start_year = str(current_year - 1)
        if not end_year:
            end_year = str(current_year)

        series_id = self._build_series_id(state_fips, county_fips)

        try:
            headers = {'Content-type': 'application/json'}
            payload = json.dumps({
                "seriesid": [series_id],
                "startyear": start_year,
                "endyear": end_year,
                "registrationkey": self.api_key
            })

            response = self._session.post(
                self.base_url,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            json_data = response.json()

            # Check BLS API status
            if json_data.get('status') != 'REQUEST_SUCCEEDED':
                error_msg = json_data.get('message', ['Unknown error'])
                raise BLSAPIError(f"BLS API error: {error_msg}")

            # Extract the most recent data point
            series_data = json_data.get('Results', {}).get('series', [])
            if not series_data:
                raise BLSAPIError("No series data returned from BLS API")

            data_points = series_data[0].get('data', [])
            if not data_points:
                raise BLSAPIError("No unemployment data available for this county")

            # BLS returns data in reverse chronological order (most recent first)
            # Filter for actual monthly data (periods M01-M12), not annual averages (M13)
            monthly_data = [d for d in data_points if d.get('period', '').startswith('M')
                          and d.get('period') != 'M13']

            if not monthly_data:
                raise BLSAPIError("No monthly unemployment data available")

            latest = monthly_data[0]

            return {
                'rate': float(latest['value']),
                'period': latest.get('periodName', 'Unknown'),
                'year': latest.get('year', 'Unknown'),
                'series_id': series_id,
                'source': 'BLS LAUS (Monthly)',
                'footnotes': [fn.get('text', '') for fn in latest.get('footnotes', [])
                             if fn.get('text')]
            }

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    raise BLSAPIError(
                        "Invalid BLS API key. Please verify your key."
                    )
                elif e.response.status_code == 429:
                    raise BLSAPIError(
                        "BLS API rate limit exceeded. Try again later."
                    )
                else:
                    raise BLSAPIError(
                        f"BLS API HTTP error {e.response.status_code}: {e}"
                    )
            raise BLSAPIError(f"BLS API HTTP error: {e}")

        except requests.exceptions.RequestException as e:
            raise BLSAPIError(f"BLS API request failed: {e}")

        except (ValueError, KeyError) as e:
            raise BLSAPIError(f"Failed to parse BLS API response: {e}")

    def get_county_labor_stats(
        self,
        state_fips: str = STATE_FIPS,
        county_fips: str = LOUDOUN_COUNTY_FIPS,
        years_back: int = 2
    ) -> Dict[str, Any]:
        """
        Get comprehensive labor statistics including unemployment trajectory
        and labor force participation rate.

        Args:
            state_fips: State FIPS code (default: 51 for Virginia)
            county_fips: County FIPS code (default: 107 for Loudoun)
            years_back: Number of years of historical data to fetch (default: 2)

        Returns:
            Dictionary with comprehensive labor data:
            {
                'unemployment': {
                    'current_rate': 3.1,
                    'current_period': 'September',
                    'current_year': '2025',
                    'year_ago_rate': 3.8,
                    'year_ago_period': 'September',
                    'year_ago_year': '2024',
                    'direction': 'improving',  # 'improving', 'worsening', or 'stable'
                    'change': -0.7,  # negative = rate dropped = improving
                    'source': 'BLS LAUS (Monthly)'
                },
                'labor_force': {
                    'count': 250323,  # Total civilian labor force
                    'period': 'September',
                    'year': '2025',
                    'source': 'BLS LAUS (Monthly)'
                }
            }

            Note: BLS LAUS provides labor force COUNT at county level, not
            participation rate. Participation rate = labor_force / civilian_population.

        Raises:
            BLSAPIError: If API request fails
        """
        if not self.api_key:
            raise BLSAPIError(
                "BLS API key not configured. "
                "Set BLS_API_KEY in ~/.config/newco/api_keys.json"
            )

        current_year = datetime.now().year
        start_year = str(current_year - years_back + 1)
        end_year = str(current_year)

        # Build series IDs for both metrics
        unemp_series_id = self._build_series_id(
            state_fips, county_fips, BLS_MEASURE_UNEMPLOYMENT_RATE
        )
        lf_series_id = self._build_series_id(
            state_fips, county_fips, BLS_MEASURE_LABOR_FORCE
        )

        try:
            headers = {'Content-type': 'application/json'}
            payload = json.dumps({
                "seriesid": [unemp_series_id, lf_series_id],
                "startyear": start_year,
                "endyear": end_year,
                "registrationkey": self.api_key
            })

            response = self._session.post(
                self.base_url,
                data=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            json_data = response.json()

            # Check BLS API status
            if json_data.get('status') != 'REQUEST_SUCCEEDED':
                error_msg = json_data.get('message', ['Unknown error'])
                raise BLSAPIError(f"BLS API error: {error_msg}")

            series_list = json_data.get('Results', {}).get('series', [])
            if not series_list:
                raise BLSAPIError("No series data returned from BLS API")

            # Parse results by series ID
            result = {
                'unemployment': None,
                'labor_force': None
            }

            for series in series_list:
                series_id = series.get('seriesID', '')
                data_points = series.get('data', [])

                # Filter for actual monthly data (M01-M12), not annual averages (M13)
                monthly_data = [
                    d for d in data_points
                    if d.get('period', '').startswith('M') and d.get('period') != 'M13'
                ]

                if not monthly_data:
                    continue

                # Data is in reverse chronological order (newest first)
                latest = monthly_data[0]
                latest_period = latest.get('periodName', 'Unknown')
                latest_year = latest.get('year', 'Unknown')
                latest_rate = float(latest['value'])

                if series_id == unemp_series_id:
                    # Find same month from a year ago for trajectory
                    year_ago_rate = None
                    year_ago_period = None
                    year_ago_year = None

                    target_period = latest.get('period')  # e.g., 'M09'
                    target_year = str(int(latest_year) - 1)

                    for dp in monthly_data:
                        if dp.get('period') == target_period and dp.get('year') == target_year:
                            year_ago_rate = float(dp['value'])
                            year_ago_period = dp.get('periodName', 'Unknown')
                            year_ago_year = dp.get('year', 'Unknown')
                            break

                    # Calculate direction
                    direction = 'stable'
                    change = None
                    if year_ago_rate is not None:
                        change = round(latest_rate - year_ago_rate, 1)
                        if change < -0.1:
                            direction = 'improving'  # Rate dropped = good
                        elif change > 0.1:
                            direction = 'worsening'  # Rate increased = bad

                    result['unemployment'] = {
                        'current_rate': latest_rate,
                        'current_period': latest_period,
                        'current_year': latest_year,
                        'year_ago_rate': year_ago_rate,
                        'year_ago_period': year_ago_period,
                        'year_ago_year': year_ago_year,
                        'direction': direction,
                        'change': change,
                        'series_id': series_id,
                        'source': 'BLS LAUS (Monthly)'
                    }

                elif series_id == lf_series_id:
                    result['labor_force'] = {
                        'count': int(latest_rate),  # This is a count, not a rate
                        'period': latest_period,
                        'year': latest_year,
                        'series_id': series_id,
                        'source': 'BLS LAUS (Monthly)'
                    }

            return result

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    raise BLSAPIError("Invalid BLS API key. Please verify your key.")
                elif e.response.status_code == 429:
                    raise BLSAPIError("BLS API rate limit exceeded. Try again later.")
                else:
                    raise BLSAPIError(f"BLS API HTTP error {e.response.status_code}: {e}")
            raise BLSAPIError(f"BLS API HTTP error: {e}")

        except requests.exceptions.RequestException as e:
            raise BLSAPIError(f"BLS API request failed: {e}")

        except (ValueError, KeyError) as e:
            raise BLSAPIError(f"Failed to parse BLS API response: {e}")


# Module-level client instances (lazy initialization)
_client: Optional[CensusClient] = None
_bls_client: Optional[BLSClient] = None


def get_census_client() -> CensusClient:
    """
    Get or create a Census API client instance.

    Returns:
        CensusClient instance
    """
    global _client
    if _client is None:
        _client = CensusClient()
    return _client


def get_bls_client() -> BLSClient:
    """
    Get or create a BLS API client instance.

    Returns:
        BLSClient instance
    """
    global _bls_client
    if _bls_client is None:
        _bls_client = BLSClient()
    return _bls_client


def test_census_connection() -> Dict[str, Any]:
    """
    Test Census API connection and return sample data.

    Returns:
        Dictionary with connection status and sample data
    """
    try:
        client = get_census_client()

        # Try to fetch county data as a simple test
        county_data = client.get_county_data()

        return {
            'status': 'success',
            'message': 'Census API connection successful',
            'county_name': county_data.get('NAME', 'Unknown'),
            'total_population': county_data.get('total_population'),
            'median_income': county_data.get('median_household_income'),
            'median_age': county_data.get('median_age'),
        }

    except CensusAPIError as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def test_bls_connection() -> Dict[str, Any]:
    """
    Test BLS API connection and return sample data.

    Returns:
        Dictionary with connection status and sample unemployment data
    """
    try:
        client = get_bls_client()

        # Try to fetch Loudoun County unemployment data
        unemployment = client.get_county_unemployment()

        return {
            'status': 'success',
            'message': 'BLS API connection successful',
            'unemployment_rate': unemployment.get('rate'),
            'period': unemployment.get('period'),
            'year': unemployment.get('year'),
            'series_id': unemployment.get('series_id'),
            'source': unemployment.get('source'),
        }

    except BLSAPIError as e:
        return {
            'status': 'error',
            'message': str(e)
        }


if __name__ == '__main__':
    # Test the module
    print("Testing Census API Client")
    print("=" * 50)

    result = test_census_connection()

    if result['status'] == 'success':
        print(f"Connection: {result['message']}")
        print(f"County: {result['county_name']}")
        print(f"Population: {result['total_population']:,}")
        print(f"Median Income: ${result['median_income']:,}")
        print(f"Median Age: {result['median_age']}")
    else:
        print(f"Error: {result['message']}")

    print()
    print("Testing BLS API Client")
    print("=" * 50)

    bls_result = test_bls_connection()

    if bls_result['status'] == 'success':
        print(f"Connection: {bls_result['message']}")
        print(f"Unemployment Rate: {bls_result['unemployment_rate']}%")
        print(f"Period: {bls_result['period']} {bls_result['year']}")
        print(f"Series ID: {bls_result['series_id']}")
        print(f"Source: {bls_result['source']}")
    else:
        print(f"Error: {bls_result['message']}")
