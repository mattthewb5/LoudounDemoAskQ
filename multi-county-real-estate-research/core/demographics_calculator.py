"""
Demographics Calculator for Census Data Aggregation

Calculates demographic statistics within specified radii of a property
using Census block group data with population-weighted aggregation.

Usage:
    from core.demographics_calculator import calculate_demographics

    demographics = calculate_demographics(
        lat=39.1157,
        lon=-77.5647,
        address="43422 Cloister Pl, Leesburg, VA 20176"
    )

Approach:
    MVP uses block group centroids to determine which block groups
    fall within each radius. More accurate area-weighted intersection
    can be implemented as a future enhancement.
"""

import math
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st

from core.census_api import (
    CensusClient,
    get_census_client,
    CensusAPIError,
    BLSClient,
    get_bls_client,
    BLSAPIError,
    ACS_YEAR,
    STATE_FIPS,
    LOUDOUN_COUNTY_FIPS
)


# Earth radius in miles (for distance calculations)
EARTH_RADIUS_MILES = 3958.8

# Analysis radii in miles
RADII = [1, 3]

# TIGERweb API for block group centroids
TIGERWEB_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/8/query"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in miles.

    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)

    Returns:
        Distance in miles
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_MILES * c


def fetch_block_group_centroids(
    state: str = STATE_FIPS,
    county: str = LOUDOUN_COUNTY_FIPS
) -> List[Dict[str, Any]]:
    """
    Fetch block group centroids from TIGERweb API.

    Args:
        state: State FIPS code
        county: County FIPS code

    Returns:
        List of dicts with block_group_id, centroid_lat, centroid_lon
    """
    # Query TIGERweb for block groups in the county
    params = {
        'where': f"STATE='{state}' AND COUNTY='{county}'",
        'outFields': 'GEOID,CENTLAT,CENTLON,AREALAND',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(TIGERWEB_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'features' not in data:
            return []

        centroids = []
        for feature in data['features']:
            attrs = feature.get('attributes', {})
            if attrs.get('CENTLAT') and attrs.get('CENTLON'):
                centroids.append({
                    'block_group_id': attrs.get('GEOID'),
                    'centroid_lat': float(attrs['CENTLAT']),
                    'centroid_lon': float(attrs['CENTLON']),
                    'land_area_sqm': attrs.get('AREALAND', 0)
                })

        return centroids

    except Exception as e:
        # Log error and return empty list
        print(f"Error fetching block group centroids: {e}")
        return []


def identify_block_groups_in_radius(
    property_lat: float,
    property_lon: float,
    radius_miles: float,
    centroids: List[Dict[str, Any]]
) -> List[str]:
    """
    Identify block groups whose centroids fall within the radius.

    Args:
        property_lat: Property latitude
        property_lon: Property longitude
        radius_miles: Search radius in miles
        centroids: List of block group centroid data

    Returns:
        List of block group GEOIDs within the radius
    """
    block_groups_in_radius = []

    for centroid in centroids:
        distance = haversine_distance(
            property_lat, property_lon,
            centroid['centroid_lat'], centroid['centroid_lon']
        )

        if distance <= radius_miles:
            block_groups_in_radius.append(centroid['block_group_id'])

    return block_groups_in_radius


def aggregate_block_group_data(
    block_group_ids: List[str],
    all_block_groups: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate Census data from selected block groups using population weighting.

    Args:
        block_group_ids: List of block group GEOIDs to include
        all_block_groups: Complete Census data for all block groups

    Returns:
        Aggregated demographic data dictionary
    """
    # Filter to selected block groups
    selected = [
        bg for bg in all_block_groups
        if _extract_geoid(bg) in block_group_ids
    ]

    if not selected:
        return _empty_demographics()

    # Calculate totals and weighted averages
    total_pop = sum(bg.get('total_population') or 0 for bg in selected)
    total_households = sum(bg.get('total_households') or 0 for bg in selected)

    if total_pop == 0:
        return _empty_demographics()

    # Population-weighted median age
    weighted_age_sum = sum(
        (bg.get('median_age') or 0) * (bg.get('total_population') or 0)
        for bg in selected
    )
    median_age = weighted_age_sum / total_pop if total_pop > 0 else None

    # Household-weighted median income
    weighted_income_sum = sum(
        (bg.get('median_household_income') or 0) * (bg.get('total_households') or 0)
        for bg in selected
    )
    median_income = weighted_income_sum / total_households if total_households > 0 else None

    # Average household income (from aggregate)
    total_aggregate_income = sum(bg.get('aggregate_household_income') or 0 for bg in selected)
    avg_income = total_aggregate_income / total_households if total_households > 0 else None

    # Housing tenure
    owner_occupied = sum(bg.get('owner_occupied') or 0 for bg in selected)
    renter_occupied = sum(bg.get('renter_occupied') or 0 for bg in selected)
    total_occupied = owner_occupied + renter_occupied
    owner_pct = (owner_occupied / total_occupied * 100) if total_occupied > 0 else None
    renter_pct = (renter_occupied / total_occupied * 100) if total_occupied > 0 else None

    # Average household size (weighted)
    weighted_hh_size_sum = sum(
        (bg.get('avg_household_size') or 0) * (bg.get('total_households') or 0)
        for bg in selected
    )
    avg_hh_size = weighted_hh_size_sum / total_households if total_households > 0 else None

    # Education - Bachelor's degree or higher
    edu_total = sum(bg.get('edu_total_25_plus') or 0 for bg in selected)
    edu_bachelors_plus = sum(
        (bg.get('edu_bachelors') or 0) +
        (bg.get('edu_masters') or 0) +
        (bg.get('edu_professional') or 0) +
        (bg.get('edu_doctorate') or 0)
        for bg in selected
    )
    bachelors_plus_pct = (edu_bachelors_plus / edu_total * 100) if edu_total > 0 else None

    # Employment
    labor_force = sum(bg.get('labor_force') or 0 for bg in selected)
    unemployed = sum(bg.get('unemployed') or 0 for bg in selected)
    unemployment_rate = (unemployed / labor_force * 100) if labor_force > 0 else None

    labor_force_16_plus = sum(bg.get('labor_force_16_plus') or 0 for bg in selected)
    # Approximate civilian labor force participation
    labor_force_participation = (labor_force_16_plus / total_pop * 100) if total_pop > 0 else None

    # Income distribution for chart
    income_distribution = _aggregate_income_distribution(selected)

    # Age distribution for chart
    age_distribution = _aggregate_age_distribution(selected)

    # Count households earning $100k+
    hh_100k_plus = sum(
        (bg.get('income_100k_125k') or 0) +
        (bg.get('income_125k_150k') or 0) +
        (bg.get('income_150k_200k') or 0) +
        (bg.get('income_200k_plus') or 0)
        for bg in selected
    )
    pct_over_100k = (hh_100k_plus / total_households * 100) if total_households > 0 else None

    return {
        'population': {
            'total': total_pop,
            'median_age': round(median_age, 1) if median_age else None,
            'age_distribution': age_distribution
        },
        'households': {
            'total': total_households,
            'avg_size': round(avg_hh_size, 1) if avg_hh_size else None,
            'owner_occupied_pct': round(owner_pct, 0) if owner_pct else None,
            'renter_occupied_pct': round(renter_pct, 0) if renter_pct else None
        },
        'income': {
            'median': round(median_income, 0) if median_income else None,
            'average': round(avg_income, 0) if avg_income else None,
            'pct_over_100k': round(pct_over_100k, 0) if pct_over_100k else None,
            'distribution': income_distribution
        },
        'education': {
            'bachelors_plus_pct': round(bachelors_plus_pct, 0) if bachelors_plus_pct else None
        },
        'employment': {
            'labor_force_participation_pct': round(labor_force_participation, 0) if labor_force_participation else None,
            'unemployment_rate': round(unemployment_rate, 1) if unemployment_rate else None
        },
        'block_groups_included': len(selected)
    }


def _aggregate_income_distribution(block_groups: List[Dict]) -> Dict[str, int]:
    """Aggregate income distribution across block groups."""
    brackets = {
        'Under $25K': sum(
            (bg.get('income_under_10k') or 0) +
            (bg.get('income_10k_15k') or 0) +
            (bg.get('income_15k_20k') or 0) +
            (bg.get('income_20k_25k') or 0)
            for bg in block_groups
        ),
        '$25K-$50K': sum(
            (bg.get('income_25k_30k') or 0) +
            (bg.get('income_30k_35k') or 0) +
            (bg.get('income_35k_40k') or 0) +
            (bg.get('income_40k_45k') or 0) +
            (bg.get('income_45k_50k') or 0)
            for bg in block_groups
        ),
        '$50K-$75K': sum(
            (bg.get('income_50k_60k') or 0) +
            (bg.get('income_60k_75k') or 0)
            for bg in block_groups
        ),
        '$75K-$100K': sum(
            (bg.get('income_75k_100k') or 0)
            for bg in block_groups
        ),
        '$100K-$150K': sum(
            (bg.get('income_100k_125k') or 0) +
            (bg.get('income_125k_150k') or 0)
            for bg in block_groups
        ),
        '$150K-$200K': sum(
            (bg.get('income_150k_200k') or 0)
            for bg in block_groups
        ),
        '$200K+': sum(
            (bg.get('income_200k_plus') or 0)
            for bg in block_groups
        )
    }
    return brackets


def _aggregate_age_distribution(block_groups: List[Dict]) -> Dict[str, int]:
    """Aggregate age distribution across block groups."""
    brackets = {
        '0-17 (Children)': sum(
            (bg.get('male_under_5') or 0) + (bg.get('female_under_5') or 0) +
            (bg.get('male_5_9') or 0) + (bg.get('female_5_9') or 0) +
            (bg.get('male_10_14') or 0) + (bg.get('female_10_14') or 0) +
            (bg.get('male_15_17') or 0) + (bg.get('female_15_17') or 0)
            for bg in block_groups
        ),
        '18-24 (Young Adults)': sum(
            (bg.get('male_18_19') or 0) + (bg.get('female_18_19') or 0) +
            (bg.get('male_20') or 0) + (bg.get('female_20') or 0) +
            (bg.get('male_21') or 0) + (bg.get('female_21') or 0) +
            (bg.get('male_22_24') or 0) + (bg.get('female_22_24') or 0)
            for bg in block_groups
        ),
        '25-34 (Young Professionals)': sum(
            (bg.get('male_25_29') or 0) + (bg.get('female_25_29') or 0) +
            (bg.get('male_30_34') or 0) + (bg.get('female_30_34') or 0)
            for bg in block_groups
        ),
        '35-54 (Peak Earning)': sum(
            (bg.get('male_35_39') or 0) + (bg.get('female_35_39') or 0) +
            (bg.get('male_40_44') or 0) + (bg.get('female_40_44') or 0) +
            (bg.get('male_45_49') or 0) + (bg.get('female_45_49') or 0) +
            (bg.get('male_50_54') or 0) + (bg.get('female_50_54') or 0)
            for bg in block_groups
        ),
        '55-64 (Pre-Retirement)': sum(
            (bg.get('male_55_59') or 0) + (bg.get('female_55_59') or 0) +
            (bg.get('male_60_61') or 0) + (bg.get('female_60_61') or 0) +
            (bg.get('male_62_64') or 0) + (bg.get('female_62_64') or 0)
            for bg in block_groups
        ),
        '65+ (Seniors)': sum(
            (bg.get('male_65_66') or 0) + (bg.get('female_65_66') or 0) +
            (bg.get('male_67_69') or 0) + (bg.get('female_67_69') or 0) +
            (bg.get('male_70_74') or 0) + (bg.get('female_70_74') or 0) +
            (bg.get('male_75_79') or 0) + (bg.get('female_75_79') or 0) +
            (bg.get('male_80_84') or 0) + (bg.get('female_80_84') or 0) +
            (bg.get('male_85_plus') or 0) + (bg.get('female_85_plus') or 0)
            for bg in block_groups
        )
    }
    return brackets


def _extract_geoid(block_group: Dict) -> str:
    """Extract block group GEOID from Census API response."""
    # The Census API returns state, county, tract, and block group as separate fields
    state = block_group.get('state', '')
    county = block_group.get('county', '')
    tract = block_group.get('tract', '')
    bg = block_group.get('block group', '')

    if state and county and tract and bg:
        return f"{state}{county}{tract}{bg}"

    # Fallback: check for GEO_ID field
    geo_id = block_group.get('GEO_ID', '')
    if geo_id:
        # GEO_ID format: 1500000US51107100201
        return geo_id.split('US')[-1] if 'US' in geo_id else geo_id

    return ''


def _empty_demographics() -> Dict[str, Any]:
    """Return empty demographics structure."""
    return {
        'population': {'total': 0, 'median_age': None, 'age_distribution': {}},
        'households': {'total': 0, 'avg_size': None, 'owner_occupied_pct': None, 'renter_occupied_pct': None},
        'income': {'median': None, 'average': None, 'pct_over_100k': None, 'distribution': {}},
        'education': {'bachelors_plus_pct': None},
        'employment': {'labor_force_participation_pct': None, 'unemployment_rate': None},
        'block_groups_included': 0
    }


@st.cache_data(ttl=86400)  # Cache for 24 hours - BLS updates monthly
def fetch_bls_labor_stats(
    state_fips: str = STATE_FIPS,
    county_fips: str = LOUDOUN_COUNTY_FIPS
) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive labor statistics from BLS LAUS including
    current unemployment rate and year-over-year trajectory.

    Args:
        state_fips: State FIPS code (default: 51 for Virginia)
        county_fips: County FIPS code (default: 107 for Loudoun)

    Returns:
        BLS labor stats dict or None if unavailable
    """
    try:
        client = get_bls_client()
        return client.get_county_labor_stats(state_fips, county_fips)
    except BLSAPIError as e:
        # Log error but don't fail - BLS data is supplementary
        print(f"BLS API error (non-fatal): {e}")
        return None
    except Exception as e:
        print(f"Unexpected BLS error (non-fatal): {e}")
        return None


def calculate_county_comparison(county_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate county-level statistics for comparison.

    Args:
        county_data: County-level Census data

    Returns:
        Dictionary with county comparison metrics
    """
    # Housing tenure
    owner = county_data.get('owner_occupied') or 0
    renter = county_data.get('renter_occupied') or 0
    total_occupied = owner + renter
    owner_pct = (owner / total_occupied * 100) if total_occupied > 0 else None

    # Education
    edu_total = county_data.get('edu_total_25_plus') or 0
    edu_ba_plus = (
        (county_data.get('edu_bachelors') or 0) +
        (county_data.get('edu_masters') or 0) +
        (county_data.get('edu_professional') or 0) +
        (county_data.get('edu_doctorate') or 0)
    )
    bachelors_pct = (edu_ba_plus / edu_total * 100) if edu_total > 0 else None

    # Employment
    labor_force = county_data.get('labor_force') or 0
    unemployed = county_data.get('unemployed') or 0
    unemployment = (unemployed / labor_force * 100) if labor_force > 0 else None

    return {
        'median_income': county_data.get('median_household_income'),
        'median_age': county_data.get('median_age'),
        'owner_occupied_pct': round(owner_pct, 0) if owner_pct else None,
        'bachelors_plus_pct': round(bachelors_pct, 0) if bachelors_pct else None,
        'unemployment_rate': round(unemployment, 1) if unemployment else None
    }


@st.cache_data(ttl=31536000)  # Cache for 1 year
def calculate_demographics(
    lat: float,
    lon: float,
    address: str,
    radii: List[int] = None
) -> Dict[str, Any]:
    """
    Calculate demographics for property location at specified radii.

    This is the main entry point for demographics calculation.
    Results are cached for 1 year since Census data updates annually.

    Args:
        lat: Property latitude
        lon: Property longitude
        address: Property address (for metadata)
        radii: List of radii in miles (default: [1, 3])

    Returns:
        Complete demographics data structure with:
        - metadata: Property info, calculation timestamp
        - radii_data: Demographics for each radius
        - county_comparison: Loudoun County benchmarks
    """
    if radii is None:
        radii = RADII

    try:
        # Get Census client
        client = get_census_client()

        # Fetch all block group data for Loudoun County
        block_groups = client.get_block_group_data()

        # Fetch block group centroids from TIGERweb
        centroids = fetch_block_group_centroids()

        if not centroids:
            return {
                'metadata': {
                    'property_address': address,
                    'lat': lat,
                    'lon': lon,
                    'error': 'Could not fetch block group centroids'
                },
                'radii_data': {},
                'county_comparison': {}
            }

        # Calculate demographics for each radius
        radii_data = {}
        for radius in radii:
            bg_ids = identify_block_groups_in_radius(lat, lon, radius, centroids)
            aggregated = aggregate_block_group_data(bg_ids, block_groups)
            radii_data[f'{radius}_mile'] = aggregated

        # Fetch county-level data for comparison
        county_data = client.get_county_data()
        county_comparison = calculate_county_comparison(county_data)

        # Fetch BLS labor stats including unemployment trajectory (supplementary data)
        bls_labor_stats = fetch_bls_labor_stats()

        # Add BLS data to county comparison if available
        if bls_labor_stats and bls_labor_stats.get('unemployment'):
            unemp = bls_labor_stats['unemployment']
            county_comparison['bls_unemployment'] = {
                'rate': unemp.get('current_rate'),
                'period': unemp.get('current_period'),
                'year': unemp.get('current_year'),
                'source': unemp.get('source', 'BLS LAUS (Monthly)'),
                # Trajectory data
                'year_ago_rate': unemp.get('year_ago_rate'),
                'year_ago_period': unemp.get('year_ago_period'),
                'year_ago_year': unemp.get('year_ago_year'),
                'change': unemp.get('change'),
                'direction': unemp.get('direction')
            }
            # Keep Census unemployment as separate field for clarity
            county_comparison['census_unemployment'] = {
                'rate': county_comparison.get('unemployment_rate'),
                'period': f'{int(ACS_YEAR)-4}-{ACS_YEAR}',
                'source': 'Census ACS 5-Year'
            }

        return {
            'metadata': {
                'property_address': address,
                'lat': lat,
                'lon': lon,
                'radii': radii,
                'county': 'Loudoun County, VA',
                'census_year': ACS_YEAR,
                'acs_dataset': f'{int(ACS_YEAR)-4}-{ACS_YEAR}',
                'calculated_at': datetime.now().isoformat(),
                'bls_data_available': bls_labor_stats is not None and bls_labor_stats.get('unemployment') is not None
            },
            'radii_data': radii_data,
            'county_comparison': county_comparison
        }

    except CensusAPIError as e:
        return {
            'metadata': {
                'property_address': address,
                'lat': lat,
                'lon': lon,
                'error': str(e)
            },
            'radii_data': {},
            'county_comparison': {}
        }

    except Exception as e:
        return {
            'metadata': {
                'property_address': address,
                'lat': lat,
                'lon': lon,
                'error': f'Unexpected error: {str(e)}'
            },
            'radii_data': {},
            'county_comparison': {}
        }


def test_demographics_calculation(
    lat: float = 39.1157,
    lon: float = -77.5647,
    address: str = "43422 Cloister Pl, Leesburg, VA 20176"
) -> Dict[str, Any]:
    """
    Test demographics calculation with sample property.

    Args:
        lat: Property latitude
        lon: Property longitude
        address: Property address

    Returns:
        Demographics data or error information
    """
    # Clear cache for testing
    calculate_demographics.clear()

    return calculate_demographics(lat, lon, address)


if __name__ == '__main__':
    import json

    print("Testing Demographics Calculator")
    print("=" * 60)
    print("Test Property: 43422 Cloister Pl, Leesburg, VA 20176")
    print("Coordinates: 39.1157, -77.5647")
    print("=" * 60)

    result = test_demographics_calculation()

    if 'error' in result.get('metadata', {}):
        print(f"\nError: {result['metadata']['error']}")
    else:
        print("\nDemographics calculated successfully!")
        print(json.dumps(result, indent=2, default=str))
