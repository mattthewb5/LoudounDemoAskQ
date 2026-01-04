"""
Flood Zone Analysis for Loudoun County

Provides functions to check FEMA flood zone status for properties.
Designed for AI tool integration.

Data source: Loudoun County GIS - FEMA Flood Map Service
Live API: https://logis.loudoun.gov/gis/rest/services/COL/FEMAFlood/MapServer/5/query
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests


# Cache configuration
_MODULE_DIR = Path(__file__).parent.parent
_CACHE_DIR = _MODULE_DIR / 'data' / 'loudoun' / 'cache' / 'flood_zone'
_CACHE_TTL_DAYS = 30  # Flood zone data changes infrequently


def _get_cache_key(lat: float, lon: float) -> str:
    """Generate cache key from coordinates (3 decimal precision)."""
    key_str = f"{round(lat, 3)}_{round(lon, 3)}"
    return hashlib.md5(key_str.encode()).hexdigest()[:12]


def _load_from_cache(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Load flood zone result from cache if valid."""
    cache_key = _get_cache_key(lat, lon)
    cache_file = _CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > _CACHE_TTL_DAYS * 86400:
            return None  # Cache expired

        with open(cache_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_to_cache(lat: float, lon: float, data: Dict[str, Any]) -> None:
    """Save flood zone result to cache."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_key = _get_cache_key(lat, lon)
        cache_file = _CACHE_DIR / f"{cache_key}.json"

        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except OSError:
        pass  # Caching is optional


def check_flood_zone(lat: float, lon: float, use_cache: bool = True) -> Dict[str, Any]:
    """
    Check if property is in a FEMA flood zone using Loudoun County GIS.

    Uses the official Loudoun County GIS FEMA Flood layer API to determine
    flood zone status. Returns plain English descriptions for homeowner clarity.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        use_cache: Whether to use cached results (default True)

    Returns:
        Dictionary with:
        - available: True if check completed
        - in_flood_zone: True/False/None
        - zone_type: 'AE', 'A', 'FLOODWAY', or None
        - zone_description: Raw description from API
        - insurance_required: True/False/None
        - summary: Plain English summary
        - data_source: Source attribution
        - from_cache: Whether result was cached
    """
    # Check cache first
    if use_cache:
        cached = _load_from_cache(lat, lon)
        if cached:
            cached['from_cache'] = True
            return cached

    ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/FEMAFlood/MapServer/5/query"

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',  # WGS84
        'outFields': 'COL_DESCRIPTION_DETAIL',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if not features:
            # Not in flood zone - good news!
            result = {
                'available': True,
                'in_flood_zone': False,
                'zone_type': None,
                'zone_description': None,
                'insurance_required': False,
                'summary': 'This property is NOT in a FEMA-designated flood zone. Flood insurance is not required by mortgage lenders.',
                'data_source': 'Loudoun County GIS - FEMA Flood Zones',
                'from_cache': False
            }
            if use_cache:
                _save_to_cache(lat, lon, result)
            return result

        # Parse zone type from response
        zone_raw = features[0]['attributes'].get('COL_DESCRIPTION_DETAIL', '')

        # Determine zone type for plain English display
        if 'FLOODWAY' in zone_raw.upper():
            zone_type = 'FLOODWAY'
            summary = 'This property is in a FEMA FLOODWAY - the highest-risk flood zone. Flood insurance is REQUIRED and building restrictions apply.'
        elif 'ZONE AE' in zone_raw.upper():
            zone_type = 'AE'
            summary = 'This property is in FEMA Zone AE (1% annual flood risk). Flood insurance is REQUIRED by mortgage lenders.'
        elif 'ZONE A' in zone_raw.upper():
            zone_type = 'A'
            summary = 'This property is in FEMA Zone A (1% annual flood risk). Flood insurance is REQUIRED by mortgage lenders.'
        else:
            zone_type = zone_raw
            summary = f'This property is in a mapped flood zone ({zone_raw}). Flood insurance may be required.'

        result = {
            'available': True,
            'in_flood_zone': True,
            'zone_type': zone_type,
            'zone_description': zone_raw,
            'insurance_required': True,
            'summary': summary,
            'data_source': 'Loudoun County GIS - FEMA Flood Zones',
            'from_cache': False
        }
        if use_cache:
            _save_to_cache(lat, lon, result)
        return result

    except requests.Timeout:
        return {
            'available': False,
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'summary': 'Flood zone data temporarily unavailable (timeout). Please try again.',
            'data_source': None,
            'from_cache': False,
            'error': 'Timeout'
        }
    except requests.RequestException as e:
        return {
            'available': False,
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'summary': f'Flood zone service error: {str(e)}',
            'data_source': None,
            'from_cache': False,
            'error': str(e)
        }


def get_flood_zone_summary(lat: float, lon: float) -> str:
    """
    Get a plain-text summary of flood zone status for a location.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Human-readable summary string
    """
    result = check_flood_zone(lat, lon)
    return result.get('summary', 'Flood zone status unknown.')
