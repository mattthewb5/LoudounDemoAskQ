"""
Healthcare Access Analysis for Loudoun County

Provides functions to analyze hospital, maternity care, and
urgent care facility proximity for property locations.
Designed for AI tool integration.

Data sources:
- Maternity hospitals: Leapfrog Group, CMS Hospital Compare
- General hospitals/ERs: Loudoun County GIS
- Urgent care: Loudoun County GIS
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


# Data paths - relative to this module's location
_MODULE_DIR = Path(__file__).parent.parent
_DATA_DIR = _MODULE_DIR / 'data' / 'loudoun'
_HEALTHCARE_DIR = _DATA_DIR / 'healthcare'


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def load_maternity_hospitals() -> Dict[str, Any]:
    """Load maternity hospitals data from JSON file."""
    json_path = _HEALTHCARE_DIR / 'maternity_hospitals.json'
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'hospitals': [], 'error': 'Maternity hospitals data file not found'}
    except json.JSONDecodeError:
        return {'hospitals': [], 'error': 'Invalid JSON in maternity hospitals file'}


def get_nicu_level_description(level: str) -> str:
    """Get plain-English description for NICU level."""
    descriptions = {
        'I': 'Basic nursery for healthy full-term babies',
        'II': 'Special care for babies 32+ weeks with moderate issues',
        'III': 'Full NICU for premature/seriously ill babies',
        'IV': 'Regional center with surgery & highest-risk care'
    }
    return descriptions.get(level, 'Unknown')


def get_csection_status(rate: float) -> Tuple[str, str]:
    """
    Return color and status for C-section rate.
    Leapfrog standard: 23.6% or less
    """
    if rate <= 0.236:
        return 'green', 'Meets Standard'
    elif rate <= 0.28:
        return 'orange', 'Slightly Above'
    else:
        return 'red', 'Above Standard'


def format_star_rating(rating: int) -> str:
    """Format CMS star rating as emoji stars."""
    if not rating or rating < 1:
        return 'N/A'
    return '⭐' * rating


def load_healthcare_facilities() -> List[Dict[str, Any]]:
    """
    Load hospitals and urgent care facilities from GeoJSON file.

    Returns list of facilities with parsed properties and coordinates.
    """
    geojson_path = _HEALTHCARE_DIR / 'Loudoun_Hospitals_and_Urgent_Care (1).geojson'
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        facilities = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])

            facilities.append({
                'name': props.get('FACILITY_NAME', 'Unknown'),
                'type': props.get('FACILITY', 'U'),  # H=Hospital, U=Urgent Care
                'address': props.get('Address', ''),
                'longitude': coords[0],
                'latitude': coords[1],
                'phone': props.get('Phone', ''),
                'cms_rating': props.get('CMS_Rating'),
                'hospital_type': props.get('Hospital_Type', ''),
                'beds': props.get('Beds'),
                'health_system': props.get('Health_System', ''),
                'emergency_services': props.get('Emergency_Services', False)
            })
        return facilities
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def analyze_healthcare_access(lat: float, lon: float, radius_miles: float = 10.0) -> Dict[str, Any]:
    """
    Complete healthcare access analysis for a location.

    Args:
        lat: Latitude of property
        lon: Longitude of property
        radius_miles: Search radius (default 10 miles)

    Returns:
        Dict with:
        - available: bool
        - maternity_hospitals: List of birthing hospitals with details
        - general_hospitals: List of hospitals/ERs with distances
        - urgent_care: List of urgent care facilities
        - healthcare_summary: Text summary
    """
    result = {
        'available': True,
        'maternity_hospitals': [],
        'general_hospitals': [],
        'urgent_care': [],
        'healthcare_summary': ''
    }

    # Load and process maternity hospitals
    maternity_data = load_maternity_hospitals()
    if 'error' not in maternity_data:
        hospitals = maternity_data.get('hospitals', [])
        for hospital in hospitals:
            coords = hospital.get('coordinates', {})
            h_lat = coords.get('latitude', 0)
            h_lon = coords.get('longitude', 0)
            distance = haversine_distance(lat, lon, h_lat, h_lon)

            if distance <= radius_miles:
                maternity = hospital.get('maternity', {})
                quality = hospital.get('quality', {})

                # Get C-section status
                csection_rate = maternity.get('c_section_rate', 0)
                _, csection_status = get_csection_status(csection_rate)

                result['maternity_hospitals'].append({
                    'name': hospital.get('name', 'Unknown'),
                    'distance_miles': round(distance, 1),
                    'in_loudoun': hospital.get('in_loudoun_county', False),
                    'address': hospital.get('address', ''),
                    'city': hospital.get('city', ''),
                    'health_system': hospital.get('health_system', ''),
                    'cms_rating': quality.get('cms_overall_rating'),
                    'cms_stars': format_star_rating(quality.get('cms_overall_rating')),
                    'safety_grade': quality.get('leapfrog_safety_grade', 'N/A'),
                    'nicu_level': maternity.get('nicu_level', 'N/A'),
                    'nicu_description': get_nicu_level_description(maternity.get('nicu_level', '')),
                    'live_births_annual': maternity.get('live_births_annual', 0),
                    'c_section_rate': csection_rate,
                    'c_section_pct': round(csection_rate * 100, 1),
                    'c_section_status': csection_status,
                    'midwives_available': maternity.get('midwives_available', False),
                    'vbac_offered': maternity.get('vbac_offered', False),
                    'magnet_status': quality.get('magnet_status', False),
                    'top_hospital': quality.get('leapfrog_top_hospital', False)
                })

        # Sort by distance
        result['maternity_hospitals'].sort(key=lambda x: x['distance_miles'])

    # Load and process general healthcare facilities
    facilities = load_healthcare_facilities()
    for facility in facilities:
        distance = haversine_distance(lat, lon, facility['latitude'], facility['longitude'])

        if distance <= radius_miles:
            facility_data = {
                'name': facility['name'],
                'distance_miles': round(distance, 1),
                'address': facility['address'],
                'phone': facility.get('phone', ''),
                'type': facility['type'],
                'cms_rating': facility.get('cms_rating'),
                'cms_stars': format_star_rating(facility.get('cms_rating')) if facility.get('cms_rating') else None,
                'health_system': facility.get('health_system', ''),
                'beds': facility.get('beds'),
                'emergency_services': facility.get('emergency_services', False)
            }

            if facility['type'] == 'H':  # Hospital
                result['general_hospitals'].append(facility_data)
            else:  # Urgent Care
                result['urgent_care'].append(facility_data)

    # Sort by distance
    result['general_hospitals'].sort(key=lambda x: x['distance_miles'])
    result['urgent_care'].sort(key=lambda x: x['distance_miles'])

    # Generate summary
    summary_parts = []
    if result['maternity_hospitals']:
        nearest_mat = result['maternity_hospitals'][0]
        loudoun_count = len([h for h in result['maternity_hospitals'] if h['in_loudoun']])
        summary_parts.append(f"{len(result['maternity_hospitals'])} maternity hospitals within {radius_miles} miles "
                           f"({loudoun_count} in Loudoun County). Nearest: {nearest_mat['name']} at {nearest_mat['distance_miles']} mi.")

    if result['general_hospitals']:
        nearest_hosp = result['general_hospitals'][0]
        summary_parts.append(f"{len(result['general_hospitals'])} hospitals/ERs. Nearest: {nearest_hosp['name']} at {nearest_hosp['distance_miles']} mi.")

    if result['urgent_care']:
        nearest_uc = result['urgent_care'][0]
        summary_parts.append(f"{len(result['urgent_care'])} urgent care centers. Nearest: {nearest_uc['name']} at {nearest_uc['distance_miles']} mi.")

    result['healthcare_summary'] = ' '.join(summary_parts) if summary_parts else 'No healthcare facilities found within search radius.'

    return result


def get_maternity_hospitals_nearby(lat: float, lon: float, radius_miles: float = 15.0) -> List[Dict[str, Any]]:
    """
    Get maternity hospitals near a location with detailed birthing information.

    Args:
        lat: Latitude of property
        lon: Longitude of property
        radius_miles: Search radius (default 15 miles for maternity)

    Returns:
        List of maternity hospitals with full details, sorted by distance
    """
    result = analyze_healthcare_access(lat, lon, radius_miles)
    return result['maternity_hospitals']


def get_healthcare_summary(lat: float, lon: float) -> str:
    """
    Get a plain-text summary of healthcare access for a location.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Human-readable summary string
    """
    result = analyze_healthcare_access(lat, lon)

    lines = ["Healthcare Access Summary:"]
    lines.append("")

    # Maternity
    if result['maternity_hospitals']:
        lines.append(f"MATERNITY HOSPITALS ({len(result['maternity_hospitals'])} found):")
        for hosp in result['maternity_hospitals'][:3]:
            lines.append(f"  - {hosp['name']}: {hosp['distance_miles']} mi | {hosp['cms_stars']} | Safety: {hosp['safety_grade']}")
            lines.append(f"    NICU Level {hosp['nicu_level']}: {hosp['nicu_description']}")
    else:
        lines.append("MATERNITY HOSPITALS: None found within 10 miles")

    lines.append("")

    # General hospitals
    if result['general_hospitals']:
        lines.append(f"HOSPITALS/ERs ({len(result['general_hospitals'])} found):")
        for hosp in result['general_hospitals'][:3]:
            rating = hosp['cms_stars'] if hosp['cms_stars'] else 'Not rated'
            lines.append(f"  - {hosp['name']}: {hosp['distance_miles']} mi | {rating}")
    else:
        lines.append("HOSPITALS: None found within 10 miles")

    lines.append("")

    # Urgent care
    if result['urgent_care']:
        lines.append(f"URGENT CARE ({len(result['urgent_care'])} found):")
        for uc in result['urgent_care'][:3]:
            lines.append(f"  - {uc['name']}: {uc['distance_miles']} mi")
    else:
        lines.append("URGENT CARE: None found within 10 miles")

    return "\n".join(lines)
