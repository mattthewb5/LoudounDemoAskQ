"""
Loudoun County Zoning Analysis Module.

Includes:
- Place Types query (2019 Comprehensive Plan)
- Development Probability scoring
- Integrated zoning analysis

This module ONLY handles Loudoun County-specific zoning analysis.
Do NOT add: school integration, property valuation, crime data, or UI code.

Data Sources:
- Place Types: https://logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer/10
- Policy Areas: https://logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer/8
- Current Zoning: https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3

Last Updated: December 2025
"""

import requests
from typing import Dict, Optional, Any


# ===== API ENDPOINTS =====

# Planning MapServer
PLACE_TYPES_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer/10/query"
POLICY_AREAS_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer/8/query"

# County Zoning (Layer 3 - unincorporated Loudoun County)
ZONING_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3/query"

# Town Boundaries (Layer 1 - for jurisdiction detection)
TOWN_BOUNDARIES_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/CountyBoundary/MapServer/1/query"

# Town-Specific Zoning Layers
LEESBURG_ZONING_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/0/query"
PURCELLVILLE_ZONING_ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/pol_connect/MapServer/26/query"

# Tier 1: Incorporated towns with full GIS zoning integration
TIER1_TOWNS = ['LEESBURG', 'PURCELLVILLE']

# Tier 2: Incorporated towns without dedicated GIS layers (use county fallback + conservative scoring)
# These small towns have their own zoning but data is not in county GIS
TIER2_TOWNS = ['MIDDLEBURG', 'HAMILTON', 'HILLSBORO', 'LOVETTSVILLE', 'ROUND HILL']

# All incorporated towns in Loudoun County
ALL_TOWNS = TIER1_TOWNS + TIER2_TOWNS

# Backwards compatibility alias
SUPPORTED_TOWNS = TIER1_TOWNS


# ===== PART 1: PLACE TYPES API INTEGRATION =====

def get_place_type_loudoun(lat: float, lon: float) -> Dict[str, Any]:
    """
    Query Loudoun County 2019 Comprehensive Plan Place Types.

    API Endpoint: https://logis.loudoun.gov/gis/rest/services/COL/Planning/MapServer
    Layer 10: Place Types
    Layer 8: Policy Areas

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        dict: {
            'place_type': str,  # e.g., "Suburban Mixed Use", "Rural"
            'place_type_code': str,  # e.g., "SUBMXU", "RURNTH"
            'policy_area': str,  # e.g., "Suburban", "Transition", "Rural"
            'policy_area_code': str,  # e.g., "SUBN", "TRANS", "RUR"
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'place_type': None,
        'place_type_code': None,
        'policy_area': None,
        'policy_area_code': None,
        'success': False,
        'error': None
    }

    # Query parameters for ArcGIS REST API
    base_params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',  # WGS84 spatial reference - CRITICAL for Loudoun GIS
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        # Query Place Types layer
        place_response = requests.get(PLACE_TYPES_ENDPOINT, params=base_params, timeout=10)
        place_response.raise_for_status()
        place_data = place_response.json()

        place_features = place_data.get('features', [])
        if place_features:
            attrs = place_features[0].get('attributes', {})
            result['place_type_code'] = attrs.get('PT_PLACETYPE')
            # Format the full name - convert to title case
            pt_full = attrs.get('PT_PLACETYPE_FULL', '')
            if pt_full:
                result['place_type'] = _format_place_type_name(pt_full)

        # Query Policy Areas layer
        policy_response = requests.get(POLICY_AREAS_ENDPOINT, params=base_params, timeout=10)
        policy_response.raise_for_status()
        policy_data = policy_response.json()

        policy_features = policy_data.get('features', [])
        if policy_features:
            attrs = policy_features[0].get('attributes', {})
            result['policy_area_code'] = attrs.get('PO_POLICY')
            # Format the full name - convert to title case
            po_full = attrs.get('PO_POLICY_FULL', '')
            if po_full:
                result['policy_area'] = po_full.title()

        # Check if we got any data
        if result['place_type'] or result['policy_area']:
            result['success'] = True
        else:
            result['error'] = "No place type data found at this location"

    except requests.Timeout:
        result['error'] = "Request timeout - Loudoun GIS server not responding"
    except requests.RequestException as e:
        result['error'] = f"API request failed: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def _format_place_type_name(name: str) -> str:
    """
    Format place type name from uppercase to proper title case.

    Handles special cases like:
    - "SUBURBAN NEIGHBORHOOD" -> "Suburban Neighborhood"
    - "TOWNS" -> "Town"
    - "URBAN TRANSIT CENTER" -> "Urban Transit Center"
    """
    if not name:
        return name

    # Special case for "TOWNS" which should be "Town"
    if name.upper() == "TOWNS":
        return "Town"

    # Convert to title case
    return name.title()


# ===== PART 1B: JURISDICTION DETECTION & TOWN ZONING =====

def detect_jurisdiction(lat: float, lon: float) -> Dict[str, Any]:
    """
    Detect whether a property is in unincorporated Loudoun County or in an
    incorporated town (Leesburg, Purcellville, etc.).

    Uses Loudoun County GIS Town Boundaries layer (Layer 1).

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        {
            'jurisdiction': str,  # 'LOUDOUN', 'LEESBURG', 'PURCELLVILLE', or 'OTHER_TOWN'
            'town_name': str or None,  # Full town name if in a town
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'jurisdiction': 'LOUDOUN',  # Default to unincorporated county
        'town_name': None,
        'success': False,
        'error': None
    }

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outFields': 'TO_TOWN',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(TOWN_BOUNDARIES_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if features:
            # Property is within a town boundary
            attrs = features[0].get('attributes', {})
            town_name = attrs.get('TO_TOWN', '').upper().strip()

            if town_name:
                result['town_name'] = town_name.title()  # e.g., "Leesburg"

                # Determine jurisdiction code based on tier
                if town_name == 'LEESBURG':
                    result['jurisdiction'] = 'LEESBURG'
                elif town_name == 'PURCELLVILLE':
                    result['jurisdiction'] = 'PURCELLVILLE'
                elif town_name in TIER2_TOWNS:
                    # Tier 2 towns: Middleburg, Hamilton, Hillsboro, Lovettsville, Round Hill
                    result['jurisdiction'] = 'TIER2_TOWN'
                elif town_name in ALL_TOWNS:
                    result['jurisdiction'] = 'OTHER_TOWN'
                else:
                    # Unknown town - treat as county
                    result['jurisdiction'] = 'LOUDOUN'

        # If no features, property is in unincorporated county (default)
        result['success'] = True

    except requests.Timeout:
        result['error'] = "Request timeout - Loudoun GIS server not responding"
    except requests.RequestException as e:
        result['error'] = f"API request failed: {str(e)}"
        # On error, default to county jurisdiction but mark as failed
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def get_leesburg_zoning(lat: float, lon: float) -> Dict[str, Any]:
    """
    Query zoning for properties in the Town of Leesburg.

    API: https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/0
    Layer: 0 (Leesburg Zoning)
    Field: LB_ZONE

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        {
            'zoning': str,  # Zoning code (e.g., 'R-1', 'B-3', 'GC')
            'zoning_description': str,  # Human-readable description
            'jurisdiction': 'LEESBURG',
            'success': bool,
            'error': str or None
        }

    Common Leesburg Zoning Codes:
        RE   - Single Family Residential Estate District
        R-1  - Single Family Residential District (1 unit/acre)
        R-2  - Single Family Residential District (2 units/acre)
        R-3  - Residential Attached District
        R-4  - Residential Multi-Family District
        B-1  - Community (Downtown) Business District
        B-2  - Established Corridor Commercial District
        B-3  - Community Retail/Commercial District
        B-4  - Mixed-Use Business District
        PRN  - Planned Residential Neighborhood District
        CDD  - Crescent Design District
        MA   - Municipal Airport District
        GC   - Government Center District
        I-1  - Industrial/Research Park District
    """
    result = {
        'zoning': None,
        'zoning_description': None,
        'jurisdiction': 'LEESBURG',
        'success': False,
        'error': None
    }

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(LEESBURG_ZONING_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if features:
            attrs = features[0].get('attributes', {})
            result['zoning'] = attrs.get('LB_ZONE')
            result['zoning_description'] = _get_leesburg_zone_description(result['zoning'])
            result['success'] = True
        else:
            result['error'] = "No Leesburg zoning data found at this location"

    except requests.Timeout:
        result['error'] = "Request timeout - Loudoun GIS server not responding"
    except requests.RequestException as e:
        result['error'] = f"API request failed: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def _get_leesburg_zone_description(zone_code: str) -> str:
    """Get human-readable description for Leesburg zoning codes."""
    if not zone_code:
        return None

    descriptions = {
        'RE': 'Single Family Residential Estate District',
        'R-1': 'Single Family Residential District (1 unit/acre)',
        'R-2': 'Single Family Residential District (2 units/acre)',
        'R-3': 'Residential Attached District',
        'R-4': 'Residential Multi-Family District',
        'B-1': 'Community (Downtown) Business District',
        'B-2': 'Established Corridor Commercial District',
        'B-3': 'Community Retail/Commercial District',
        'B-4': 'Mixed-Use Business District',
        'PRN': 'Planned Residential Neighborhood District',
        'CDD': 'Crescent Design District',
        'MA': 'Municipal Airport District',
        'GC': 'Government Center District',
        'I-1': 'Industrial/Research Park District',
        'PEC': 'Planned Employment Center District',
        'O-1': 'Office District',
    }

    return descriptions.get(zone_code.upper(), f'Town of Leesburg - {zone_code}')


def get_purcellville_zoning(lat: float, lon: float) -> Dict[str, Any]:
    """
    Query zoning for properties in the Town of Purcellville.

    API: https://logis.loudoun.gov/gis/rest/services/COL/pol_connect/MapServer/26
    Layer: 26 (ZoningPurcellville)
    Field: PV_ZONE

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        {
            'zoning': str,  # Zoning code
            'zoning_description': str,  # Human-readable description
            'jurisdiction': 'PURCELLVILLE',
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'zoning': None,
        'zoning_description': None,
        'jurisdiction': 'PURCELLVILLE',
        'success': False,
        'error': None
    }

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(PURCELLVILLE_ZONING_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if features:
            attrs = features[0].get('attributes', {})
            result['zoning'] = attrs.get('PV_ZONE')
            result['zoning_description'] = _get_purcellville_zone_description(result['zoning'])
            result['success'] = True
        else:
            result['error'] = "No Purcellville zoning data found at this location"

    except requests.Timeout:
        result['error'] = "Request timeout - Loudoun GIS server not responding"
    except requests.RequestException as e:
        result['error'] = f"API request failed: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def _get_purcellville_zone_description(zone_code: str) -> str:
    """Get human-readable description for Purcellville zoning codes."""
    if not zone_code:
        return None

    descriptions = {
        'R-1': 'Single Family Residential District',
        'R-2': 'Medium Density Residential District',
        'R-3': 'High Density Residential District',
        'C-1': 'Neighborhood Commercial District',
        'C-2': 'General Commercial District',
        'C-3': 'Central Commercial District',
        'C-4': 'Highway Commercial District',
        'M-1': 'Light Industrial District',
        'M-2': 'General Industrial District',
        'PUD': 'Planned Unit Development',
        'MC': 'Mixed Commercial District',
        'IP': 'Industrial Park District',
    }

    return descriptions.get(zone_code.upper(), f'Town of Purcellville - {zone_code}')


# ===== PART 2: DEVELOPMENT PROBABILITY SCORING =====

def calculate_development_probability_loudoun(
    current_zoning: str,
    place_type: str,
    jurisdiction: str = 'LOUDOUN'
) -> int:
    """
    Calculate development probability score (0-100) based on mismatch
    between current zoning and planned place type.

    Args:
        current_zoning (str): Current zoning code (e.g., "R-1", "AR-1", "PD-TC")
        place_type (str): Place type from 2019 Comp Plan (e.g., "Suburban Mixed Use")
        jurisdiction (str): 'LOUDOUN', 'LEESBURG', or 'PURCELLVILLE'

    Returns:
        int: Score from 0-100
    """
    if not current_zoning or not place_type:
        return 0

    score = 0

    # Normalize inputs
    zoning_upper = current_zoning.upper()
    place_upper = place_type.upper()

    # Calculate intensity alignment FIRST (needed for scaling)
    zoning_intensity = _get_zoning_intensity(zoning_upper, jurisdiction)
    place_intensity = _get_place_type_intensity(place_upper)
    intensity_diff = place_intensity - zoning_intensity

    # Factor 1: Mismatch between current and planned (40 points max)
    mismatch_score = _calculate_mismatch_score(zoning_upper, place_upper, jurisdiction)
    score += mismatch_score

    # Factor 2: Current zoning restrictiveness (30 points max)
    # SCALE BY ALIGNMENT: Restrictive zoning only matters if there's pressure to change it
    restrictiveness_score = _calculate_restrictiveness_score(zoning_upper, jurisdiction)
    if intensity_diff <= 0:
        # Well-aligned or over-developed: restrictiveness doesn't indicate change potential
        # Reduce to 1/6 of base score (e.g., 30 → 5)
        restrictiveness_score = restrictiveness_score // 6
    elif intensity_diff == 1:
        # Minor mismatch: restrictiveness partially relevant
        # Reduce to half (e.g., 30 → 15)
        restrictiveness_score = restrictiveness_score // 2
    # For diff >= 2, keep full restrictiveness (indicates room to upzone)
    score += restrictiveness_score

    # Factor 3: Place type development pressure (30 points max)
    # Pass intensity_diff for proper scaling
    pressure_score = _calculate_pressure_score(place_upper, intensity_diff)
    score += pressure_score

    return min(score, 100)


def _calculate_mismatch_score(zoning: str, place_type: str, jurisdiction: str = 'LOUDOUN') -> int:
    """
    Calculate score based on mismatch between current zoning and planned place type.

    Args:
        zoning: Zoning code
        place_type: Place type designation
        jurisdiction: 'LOUDOUN', 'LEESBURG', or 'PURCELLVILLE'

    Returns 0-40 points:
    - +40 if place type suggests significantly higher intensity (diff >= 2)
    - +15 if place type somewhat more intense (diff = 1)
    - +5 if aligned or similar intensity (diff = 0)
    - +0 if lower intensity (diff < 0)
    """
    # Define intensity levels (1 = lowest, 5 = highest)
    zoning_intensity = _get_zoning_intensity(zoning, jurisdiction)
    place_intensity = _get_place_type_intensity(place_type)

    intensity_diff = place_intensity - zoning_intensity

    if intensity_diff >= 2:
        # Place type is significantly more intense than current zoning
        # High development pressure to upzone
        return 40
    elif intensity_diff == 1:
        # Place type is somewhat more intense - minor upzone potential
        return 15
    elif intensity_diff == 0:
        # Well-aligned: zoning matches comprehensive plan
        # Minimal development pressure - property is at intended use
        return 5
    else:
        # Place type is less intense (unusual, low development pressure)
        # Property is actually MORE developed than plan calls for
        return 0


def _get_zoning_intensity(zoning: str, jurisdiction: str = 'LOUDOUN') -> int:
    """
    Get intensity level for current zoning code.

    Args:
        zoning: Zoning code
        jurisdiction: 'LOUDOUN', 'LEESBURG', or 'PURCELLVILLE'

    Returns 1-5 scale:
    1 = Very low (Agricultural/Rural)
    2 = Low (Single-family residential)
    3 = Medium (Multi-family residential)
    4 = High (Commercial/Industrial)
    5 = Very high (Mixed-use/Town Center)
    """
    if not zoning:
        return 3

    zoning_upper = zoning.upper()

    # ===== LEESBURG-SPECIFIC ZONING CODES =====
    if jurisdiction == 'LEESBURG':
        # Single-family residential - low intensity
        if zoning_upper in ['RE', 'R-1', 'R-2']:
            return 2
        # PRN = Planned Residential Neighborhood - ESTABLISHED community
        # Already built to master plan specs, not awaiting development
        if zoning_upper == 'PRN':
            return 2  # Treat as established low-density (like R-2)
        # Attached/Multi-family residential - medium intensity
        if zoning_upper in ['R-3', 'R-4']:
            return 3
        # Downtown/Commercial - high intensity
        if zoning_upper in ['B-1', 'B-2', 'B-3']:
            return 4
        # Mixed-use/Special districts - very high intensity
        if zoning_upper in ['B-4', 'CDD']:
            return 5
        # Government/Industrial - high intensity (but unlikely to change)
        if zoning_upper in ['GC', 'I-1', 'PEC', 'O-1']:
            return 4
        # Airport - special case (very restricted)
        if zoning_upper == 'MA':
            return 1
        return 3  # Default for unknown Leesburg codes

    # ===== PURCELLVILLE-SPECIFIC ZONING CODES =====
    if jurisdiction == 'PURCELLVILLE':
        # Single-family residential - low intensity
        if zoning_upper == 'R-1':
            return 2
        # Medium/High density residential - medium intensity
        if zoning_upper in ['R-2', 'R-3', 'PUD']:
            return 3
        # Commercial districts - high intensity
        if zoning_upper in ['C-1', 'C-2', 'C-3', 'C-4', 'MC']:
            return 4
        # Industrial - high intensity
        if zoning_upper in ['M-1', 'M-2', 'IP']:
            return 4
        return 3  # Default for unknown Purcellville codes

    # ===== LOUDOUN COUNTY (UNINCORPORATED) ZONING CODES =====

    # Agricultural/Rural - lowest intensity
    if any(code in zoning_upper for code in ['AR-1', 'AR-2', 'A-3', 'A-10', 'CR-1', 'CR-2', 'CR-3', 'CR-4']):
        return 1

    # Rural Commercial
    if zoning_upper in ['RC', 'JLMA-3', 'JLMA-20']:
        return 2

    # Single-family residential (handle both hyphenated and non-hyphenated codes)
    # GIS may return R-1 or R1 depending on data source
    if any(code in zoning_upper for code in ['R-1', 'R-2', 'R-3', 'R-4', 'R-8', 'R-16']):
        return 2
    # Handle non-hyphenated versions explicitly (R1, R2, etc.)
    if zoning_upper in ['R1', 'R2', 'R3', 'R4', 'R8', 'R16']:
        return 2

    # Planned Development Housing (various densities)
    if 'PDH' in zoning_upper:
        # PDH-4, PDH-8, PDH-16 etc. - extract density if possible
        try:
            density = int(''.join(filter(str.isdigit, zoning_upper.split('PDH')[-1][:2])))
            if density <= 4:
                return 2
            elif density <= 8:
                return 3
            else:
                return 4
        except:
            return 3

    # Commercial zones
    if any(code in zoning_upper for code in ['CL', 'CG', 'CI', 'CH', 'CC', 'C1', 'GB']):
        return 4

    # Industrial zones
    if any(code in zoning_upper for code in ['GI', 'LI', 'MR']):
        return 4

    # Planned Development - various types
    if 'PD-' in zoning_upper:
        # PD-TC (Town Center) - very high
        if 'TC' in zoning_upper:
            return 5
        # PD-MU (Mixed Use) - very high
        if 'MU' in zoning_upper:
            return 5
        # PD-CC (Commercial Center) - high
        if 'CC' in zoning_upper or 'COM' in zoning_upper:
            return 4
        # PD-RDP, PD-H - varies
        return 3

    # Town/Mixed Use - highest intensity
    if any(code in zoning_upper for code in ['TC', 'MU', 'TOD']):
        return 5

    # "TOWNS" code from county layer means property is in incorporated town
    if zoning_upper == 'TOWNS':
        return 3  # Default medium intensity

    # Default
    return 3


def _get_place_type_intensity(place_type: str) -> int:
    """
    Get intensity level for place type designation.

    Returns 1-5 scale based on 2019 Comprehensive Plan place types.
    """
    place_upper = place_type.upper()

    # ===== ADMINISTRATIVE BOUNDARIES (check first) =====
    # JLMA = Joint Land Management Area - administrative boundary, NOT development signal
    # "Leesburg JLMA Residential Neighborhood" = stable residential, not growth area
    if 'JLMA' in place_upper:
        # JLMA with "RESIDENTIAL" or "NEIGHBORHOOD" = stable established community
        if any(kw in place_upper for kw in ['RESIDENTIAL', 'NEIGHBORHOOD']):
            return 2  # Low intensity - stable residential
        # Other JLMA (rare) - treat as moderate
        return 3

    # Check SUBURBAN patterns FIRST (more specific before general)
    # This prevents "SUBURBAN NEIGHBORHOOD" from matching "URBAN"
    # Handle both full names and abbreviated codes (SUBNBR, SUBMUS, etc.)

    # Medium intensity - Suburban Neighborhood (most common)
    if 'SUBURBAN NEIGHBORHOOD' in place_upper or place_upper == 'SUBNBR':
        return 3

    # High intensity - Suburban Mixed Use or Compact
    if any(pt in place_upper for pt in ['SUBURBAN MIXED USE', 'SUBURBAN COMPACT']):
        return 4
    if place_upper in ['SUBMUS', 'SUBCMP']:
        return 4

    # Very high intensity - Urban areas (NOT SUBURBAN)
    if any(pt in place_upper for pt in ['URBAN TRANSIT', 'TOWN CENTER', 'METROPOLITAN']):
        return 5
    if place_upper in ['URBTC', 'URBMUS']:
        return 5

    # High intensity - Other mixed use or employment
    if any(pt in place_upper for pt in ['MIXED USE', 'EMPLOYMENT']):
        return 4
    if place_upper == 'SUBEM':
        return 4

    # Low intensity - Transition areas
    if any(pt in place_upper for pt in ['TRANSITION', 'LARGE LOT']):
        return 2
    if place_upper in ['TRNLLN', 'TRNSLN', 'TRNCMP', 'TRNCC', 'TRNLI', 'TRNIM']:
        return 2

    # Very low intensity - Rural areas
    if any(pt in place_upper for pt in ['RURAL', 'AGRICULTURAL']):
        return 1
    if place_upper in ['RURNTH', 'RURSTH', 'RURVLG']:
        return 1

    # Special cases
    if 'TOWN' in place_upper and 'CENTER' not in place_upper:
        # Incorporated town (not Town Center) - stable, established area
        # This is just a jurisdiction indicator, not a development designation
        return 2  # Low intensity - already developed

    # Default
    return 3


def _calculate_restrictiveness_score(zoning: str, jurisdiction: str = 'LOUDOUN') -> int:
    """
    Calculate score based on how restrictive current zoning is.
    More restrictive zoning = higher development potential (if place type allows).

    Args:
        zoning: Zoning code
        jurisdiction: 'LOUDOUN', 'LEESBURG', or 'PURCELLVILLE'

    Returns 0-30 points:
    - +30 for very restrictive (AR-1, AR-2, A-3)
    - +20 for moderately restrictive (R-1, R-2)
    - +10 for flexible (PD-*)
    - +5 for already flexible (TC, MU)
    """
    if not zoning:
        return 15

    zoning_upper = zoning.upper()

    # ===== LEESBURG-SPECIFIC =====
    if jurisdiction == 'LEESBURG':
        # PRN = ESTABLISHED community (River Creek, etc.) - already at designed intensity
        # These are fully built-out master-planned communities with NO development potential
        if zoning_upper == 'PRN':
            return 5  # Very low - already developed per master plan
        # Very restrictive - Single-family estate
        if zoning_upper in ['RE', 'R-1']:
            return 20
        # Moderately restrictive - Residential
        if zoning_upper in ['R-2', 'R-3', 'R-4']:
            return 15
        # Flexible - Commercial
        if zoning_upper in ['B-1', 'B-2', 'B-3']:
            return 10
        # Very flexible - Mixed-use
        if zoning_upper in ['B-4', 'CDD']:
            return 5
        # Special constraints - Government/Airport (unlikely to change)
        if zoning_upper in ['GC', 'MA', 'I-1', 'PEC']:
            return 5  # Low score = less likely to redevelop
        return 15

    # ===== PURCELLVILLE-SPECIFIC =====
    if jurisdiction == 'PURCELLVILLE':
        # Restrictive - Single-family
        if zoning_upper == 'R-1':
            return 20
        # Moderately restrictive - Residential
        if zoning_upper in ['R-2', 'R-3', 'PUD']:
            return 15
        # Flexible - Commercial
        if zoning_upper in ['C-1', 'C-2', 'C-3', 'C-4', 'MC']:
            return 10
        # Industrial (specialized, less likely to change)
        if zoning_upper in ['M-1', 'M-2', 'IP']:
            return 5
        return 15

    # ===== LOUDOUN COUNTY (UNINCORPORATED) =====

    # Very restrictive - Agricultural/Rural
    if any(code in zoning_upper for code in ['AR-1', 'AR-2', 'A-3', 'A-10', 'CR-1', 'CR-2', 'CR-3', 'CR-4']):
        return 30

    # Moderately restrictive - Single-family (handle both hyphenated and non-hyphenated)
    if any(code in zoning_upper for code in ['R-1', 'R-2', 'R-3', 'R-4', 'RC']):
        return 20
    if zoning_upper in ['R1', 'R2', 'R3', 'R4']:
        return 20

    # Somewhat flexible - Medium density residential
    if any(code in zoning_upper for code in ['R-8', 'R-16']):
        return 15
    if zoning_upper in ['R8', 'R16']:
        return 15

    # PDH = Planned Development Housing - BUILT-OUT communities (like PRN in Leesburg)
    # Master plan already executed, no further development potential
    if 'PDH' in zoning_upper:
        return 5  # Very low - already developed per master plan

    # Flexible - Planned Development (non-housing)
    if 'PD-' in zoning_upper:
        return 10

    # Already flexible - Commercial/Industrial
    if any(code in zoning_upper for code in ['CL', 'CG', 'CI', 'CH', 'GI', 'LI', 'GB']):
        return 10

    # Very flexible - Town Center, Mixed Use
    if any(code in zoning_upper for code in ['TC', 'MU', 'TOD']):
        return 5

    # "TOWNS" from county layer - conservative score (need actual town zoning)
    if zoning_upper == 'TOWNS':
        return 10

    # Default
    return 15


def _calculate_pressure_score(place_type: str, intensity_diff: int = 0) -> int:
    """
    Calculate score based on development pressure from place type designation.

    Args:
        place_type: Place type code from comprehensive plan
        intensity_diff: Difference between place type and zoning intensity
                       (place_intensity - zoning_intensity)

    Returns:
        Pressure score (0-30 points, scaled by alignment)

    Scoring:
    - Raw +30 for high pressure (Urban Transit Center, Town Center, Mixed Use)
    - Raw +20 for moderate-high (Suburban Compact, Employment)
    - Raw +10 for moderate (Suburban Neighborhood)
    - Raw +5 for low (Transition, Rural)
    - Raw +0 for administrative boundaries (JLMA)

    Scaling by alignment:
    - intensity_diff <= 0: ÷6 (already at or above target intensity)
    - intensity_diff == 1: ÷2 (minor gap)
    - intensity_diff >= 2: full score (significant development potential)
    """
    place_upper = place_type.upper()

    # ===== ADMINISTRATIVE BOUNDARIES (check first) =====
    # JLMA = Joint Land Management Area - administrative boundary, NOT development signal
    # These properties are already in established communities
    if 'JLMA' in place_upper:
        return 0  # No development pressure - administrative boundary

    # Check SUBURBAN patterns FIRST (more specific before general)
    # This prevents "SUBURBAN NEIGHBORHOOD" from matching "URBAN"

    # Moderate pressure - suburban neighborhood development
    if 'SUBURBAN NEIGHBORHOOD' in place_upper:
        pressure_score = 10
    # High pressure - suburban mixed use planned
    elif 'SUBURBAN MIXED USE' in place_upper:
        pressure_score = 30
    # Moderate-high pressure - suburban compact planned
    elif 'SUBURBAN COMPACT' in place_upper:
        pressure_score = 20
    # High pressure - actively planned for urban development (NOT suburban)
    elif any(pt in place_upper for pt in ['URBAN TRANSIT', 'TOWN CENTER', 'METROPOLITAN']):
        pressure_score = 30
    # High pressure - general mixed use planned
    elif 'MIXED USE' in place_upper:
        pressure_score = 30
    # Moderate-high pressure - employment areas
    elif 'EMPLOYMENT' in place_upper:
        pressure_score = 20
    # Low pressure - transition/rural
    elif any(pt in place_upper for pt in ['TRANSITION', 'RURAL', 'AGRICULTURAL']):
        pressure_score = 5
    # Incorporated town (NOT Town Center) - just indicates jurisdiction
    # This is a stable designation, not development pressure
    # "Town" place type = already in established incorporated area
    elif 'TOWN' in place_upper and 'CENTER' not in place_upper:
        pressure_score = 5  # Low pressure - stable jurisdiction designation
    else:
        # Default
        pressure_score = 10

    # ===== SCALE BY ALIGNMENT (same pattern as restrictiveness) =====
    # Pressure only matters if there's a gap between current and planned intensity
    if intensity_diff <= 0:
        # Already at or above planned intensity - minimal actual pressure
        pressure_score = pressure_score // 6
    elif intensity_diff == 1:
        # Minor gap - partial pressure
        pressure_score = pressure_score // 2
    # For intensity_diff >= 2, keep full pressure score

    return pressure_score


def _get_mismatch_reason(intensity_diff: int) -> str:
    """Generate brief reason text for mismatch score."""
    if intensity_diff >= 2:
        return "Significant gap between current and planned intensity"
    elif intensity_diff == 1:
        return "Minor gap between current and planned intensity"
    elif intensity_diff == 0:
        return "Current zoning matches comprehensive plan"
    else:
        return "Already at or above planned intensity"


def _get_restrictiveness_reason(zoning_code: str, intensity_diff: int) -> str:
    """Generate brief reason text for restrictiveness score."""
    if not zoning_code:
        return "Unknown zoning"

    code = zoning_code.upper()

    # Determine base restrictiveness level
    if code.startswith('AR') or code.startswith('A-') or code.startswith('CR'):
        base = "Very restrictive agricultural/rural zoning"
    elif code.startswith('R-') and code not in ['R-8', 'R-16', 'R-24']:
        base = "Moderately restrictive residential zoning"
    elif code in ['R1', 'R2', 'R3', 'R4'] and not code.startswith('R-'):
        # Handle non-hyphenated codes
        base = "Moderately restrictive residential zoning"
    elif code.startswith('R-8') or code.startswith('R-16') or code.startswith('R-24') or code in ['R8', 'R16', 'R24']:
        base = "Medium-density residential zoning"
    elif code == 'PRN' or code.startswith('PDH'):
        base = "Established master-planned community"
    elif 'TC' in code or 'MU' in code or 'TOD' in code:
        base = "Flexible mixed-use/town center zoning"
    elif code.startswith('PD-'):
        base = "Planned development zoning"
    elif any(c in code for c in ['GI', 'LI', 'CI', 'CL', 'CG', 'CH']):
        base = "Commercial/industrial zoning"
    else:
        base = "Standard zoning district"

    # Add scaling note if applicable
    if intensity_diff <= 0:
        return f"{base} (reduced 85% - aligned with plan)"
    elif intensity_diff == 1:
        return f"{base} (reduced 50% - near alignment)"
    else:
        return f"{base} (full weight - policy mismatch)"


def _get_pressure_reason(place_type: str, intensity_diff: int) -> str:
    """Generate brief reason text for pressure score."""
    if not place_type:
        return "Unknown place type"

    place = place_type.upper()

    # Determine base pressure level
    if 'JLMA' in place:
        base = "Administrative boundary (no pressure)"
    elif any(p in place for p in ['URBAN TRANSIT', 'URBTC']):
        base = "Urban transit center designation"
    elif any(p in place for p in ['TOWN CENTER', 'METROPOLITAN']):
        base = "Town center/metropolitan designation"
    elif 'SUBURBAN MIXED USE' in place or 'SUBMUS' in place:
        base = "Suburban mixed-use designation"
    elif 'SUBURBAN COMPACT' in place or 'SUBCMP' in place:
        base = "Compact suburban designation"
    elif 'MIXED USE' in place:
        base = "Mixed-use designation"
    elif 'EMPLOYMENT' in place or 'SUBEM' in place:
        base = "Employment center designation"
    elif 'SUBURBAN NEIGHBORHOOD' in place or 'SUBNBR' in place:
        base = "Stable suburban neighborhood"
    elif any(p in place for p in ['RURAL', 'AGRICULTURAL', 'RUR']):
        base = "Rural preservation designation"
    elif 'TRANSITION' in place or 'TRN' in place:
        base = "Transition area designation"
    elif 'TOWN' in place and 'CENTER' not in place:
        base = "Incorporated town (stable)"
    else:
        base = "Standard place type designation"

    # Add scaling note if applicable
    if intensity_diff <= 0:
        return f"{base} (reduced 85% - aligned with plan)"
    elif intensity_diff == 1:
        return f"{base} (reduced 50% - near alignment)"
    else:
        return f"{base} (full weight)"


def calculate_development_probability_detailed(
    current_zoning: str,
    place_type: str,
    jurisdiction: str = 'LOUDOUN'
) -> Dict[str, Any]:
    """
    Calculate development probability with detailed component breakdown.

    Args:
        current_zoning (str): Current zoning code
        place_type (str): Place type from comprehensive plan
        jurisdiction (str): 'LOUDOUN', 'LEESBURG', or 'PURCELLVILLE'

    Returns:
        Dict with score, components, and reasons for transparency
    """
    if not current_zoning or not place_type:
        return {
            'score': 0,
            'risk_level': 'Low',
            'component_scores': {'mismatch': 0, 'restrictiveness': 0, 'pressure': 0},
            'component_reasons': {
                'mismatch': 'Missing zoning or place type data',
                'restrictiveness': 'Missing zoning data',
                'pressure': 'Missing place type data'
            },
            'intensity_diff': 0
        }

    # Normalize inputs
    zoning_upper = current_zoning.upper()
    place_upper = place_type.upper()

    # Calculate intensity alignment
    zoning_intensity = _get_zoning_intensity(zoning_upper, jurisdiction)
    place_intensity = _get_place_type_intensity(place_upper)
    intensity_diff = place_intensity - zoning_intensity

    # Factor 1: Mismatch score
    mismatch_score = _calculate_mismatch_score(zoning_upper, place_upper, jurisdiction)

    # Factor 2: Restrictiveness score (with scaling)
    raw_restrictiveness = _calculate_restrictiveness_score(zoning_upper, jurisdiction)
    if intensity_diff <= 0:
        restrictiveness_score = raw_restrictiveness // 6
    elif intensity_diff == 1:
        restrictiveness_score = raw_restrictiveness // 2
    else:
        restrictiveness_score = raw_restrictiveness

    # Factor 3: Pressure score (with scaling)
    pressure_score = _calculate_pressure_score(place_upper, intensity_diff)

    # Total
    total_score = min(mismatch_score + restrictiveness_score + pressure_score, 100)
    risk_level = classify_development_risk(total_score)

    return {
        'score': total_score,
        'risk_level': risk_level,
        'component_scores': {
            'mismatch': mismatch_score,
            'restrictiveness': restrictiveness_score,
            'pressure': pressure_score
        },
        'component_reasons': {
            'mismatch': _get_mismatch_reason(intensity_diff),
            'restrictiveness': _get_restrictiveness_reason(current_zoning, intensity_diff),
            'pressure': _get_pressure_reason(place_type, intensity_diff)
        },
        'intensity_diff': intensity_diff
    }


def classify_development_risk(score: int) -> str:
    """
    Classify development risk based on score.

    Args:
        score (int): Development probability score (0-100)

    Returns:
        str: "Low", "Moderate", "High", or "Very High"
    """
    if score >= 76:
        return "Very High"
    elif score >= 51:
        return "High"
    elif score >= 26:
        return "Moderate"
    else:
        return "Low"


def generate_development_interpretation_loudoun(
    current_zoning: str,
    place_type: str,
    score: int,
    risk_level: str
) -> str:
    """
    Generate human-readable interpretation of development probability.

    Args:
        current_zoning (str): Current zoning code
        place_type (str): Place type designation
        score (int): Development probability score
        risk_level (str): Risk classification

    Returns:
        str: Markdown-formatted interpretation text
    """
    # Determine mismatch context
    zoning_intensity = _get_zoning_intensity(current_zoning.upper()) if current_zoning else 3
    place_intensity = _get_place_type_intensity(place_type.upper()) if place_type else 3
    intensity_diff = place_intensity - zoning_intensity

    # Mismatch description
    if intensity_diff >= 2:
        mismatch_desc = "significant mismatch - comprehensive plan envisions substantially higher intensity development"
    elif intensity_diff == 1:
        mismatch_desc = "moderate mismatch - comprehensive plan allows for some intensification"
    elif intensity_diff == 0:
        mismatch_desc = "good alignment - current zoning matches comprehensive plan intent"
    else:
        mismatch_desc = "conservative - current zoning may exceed comprehensive plan density"

    # Development scenarios based on place type
    scenarios = _get_development_scenarios(place_type, current_zoning)

    # Timeline estimate
    if risk_level == "Very High":
        timeline = "Short-term (0-5 years)"
        certainty = "High"
    elif risk_level == "High":
        timeline = "Medium-term (5-10 years)"
        certainty = "Moderate-High"
    elif risk_level == "Moderate":
        timeline = "Long-term (10+ years)"
        certainty = "Moderate"
    else:
        timeline = "Unlikely / Very Long-term"
        certainty = "Low"

    interpretation = f"""**Development Risk: {risk_level}** (Score: {score}/100)

**Current Status:**
- Zoned: {current_zoning or 'Unknown'}
- Planned Place Type: {place_type or 'Unknown'}

**Analysis:**
This property shows {mismatch_desc}.

**Potential Changes:**
{scenarios}

**Timeline:** {timeline}
**Certainty:** {certainty}

*Based on Loudoun County 2019 Comprehensive Plan Place Types and current zoning.*"""

    return interpretation


def _get_development_scenarios(place_type: str, current_zoning: str) -> str:
    """Generate development scenario descriptions based on place type."""
    if not place_type:
        return "- Unable to determine likely development scenarios without place type data"

    # Check for established community zoning first (PRN, etc.)
    if current_zoning and current_zoning.upper() == 'PRN':
        return """- Established master-planned residential community (fully built)
- Very low development risk - community is complete
- No significant redevelopment or rezoning expected
- Stable neighborhood character maintained by HOA covenants"""

    place_upper = place_type.upper()

    # Check more specific patterns FIRST (order matters!)
    # "SUBURBAN" checks must come before "URBAN" check since SUBURBAN contains URBAN

    # Suburban Neighborhood - most common residential
    if 'SUBURBAN NEIGHBORHOOD' in place_upper:
        return """- Traditional suburban development patterns
- Single-family homes or townhomes
- Density consistent with existing neighborhood character
- Limited redevelopment pressure"""

    # Suburban Mixed Use
    if 'SUBURBAN MIXED USE' in place_upper:
        return """- Commercial development with residential components
- Potential for townhomes or low-rise apartments
- Neighborhood-serving retail and services
- Possible rezoning from residential to mixed-use"""

    # Suburban Compact Neighborhood
    if 'SUBURBAN COMPACT' in place_upper:
        return """- Higher-density residential development (townhomes, small-lot single family)
- Walkable neighborhood design
- Potential rezoning to PDH-8 or higher density
- Infrastructure improvements likely"""

    # Now check for URBAN (standalone, not part of SUBURBAN)
    if any(pt in place_upper for pt in ['URBAN TRANSIT', 'METROPOLITAN']):
        return """- High-density mixed-use development (residential + commercial)
- Transit-oriented development with reduced parking
- Potential for 4+ story buildings
- Walkable urban environment with ground-floor retail"""

    # Town Center / Mixed Use
    if any(pt in place_upper for pt in ['TOWN CENTER', 'MIXED USE']):
        return """- Mixed-use development with retail/office and residential
- Medium-density housing (townhomes, condos, apartments)
- Potential rezoning to PD-TC or similar
- Pedestrian-oriented design with street-level commercial"""

    # Employment areas
    if 'EMPLOYMENT' in place_upper:
        return """- Employment centers or business parks
- Office, industrial, or flex space development
- Limited residential unless mixed-use designated
- Infrastructure and road improvements likely"""

    if any(pt in place_upper for pt in ['TRANSITION']):
        return """- Low-density residential with rural character
- Potential for limited subdivision
- Transition between suburban and rural areas
- Septic/well systems likely required"""

    if any(pt in place_upper for pt in ['RURAL', 'AGRICULTURAL']):
        return """- Agricultural preservation priority
- Very limited development potential
- Large lot single-family only (if any)
- Strong policy protection against intensification"""

    if 'TOWN' in place_upper:
        return """- Development governed by incorporated town zoning
- Check with town planning department for specific regulations
- May have different density allowances than county
- Town comprehensive plan applies"""

    return "- Development potential depends on specific site characteristics and market conditions"


# ===== PART 3: INTEGRATED ZONING ANALYSIS =====

def get_zoning_data_loudoun(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get current zoning data for a location in Loudoun County.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        dict: {
            'zoning': str,  # Zoning code (e.g., "R-1", "PD-TC")
            'zoning_description': str,  # Full description
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'zoning': None,
        'zoning_description': None,
        'success': False,
        'error': None
    }

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(ZONING_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if features:
            attrs = features[0].get('attributes', {})
            result['zoning'] = attrs.get('ZO_ZONE')
            result['zoning_description'] = attrs.get('ZD_ZONE_DESC') or attrs.get('ZD_ZONE_NAME')
            result['success'] = True
        else:
            result['error'] = "No zoning data found at this location"

    except requests.Timeout:
        result['error'] = "Request timeout - Loudoun GIS server not responding"
    except requests.RequestException as e:
        result['error'] = f"API request failed: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"

    return result


def analyze_property_zoning_loudoun(lat: float, lon: float) -> Dict[str, Any]:
    """
    Complete zoning analysis including jurisdiction detection, current zoning,
    place types, and development probability.

    Routes to appropriate zoning source based on detected jurisdiction:
    - LOUDOUN: Unincorporated county (Layer 3)
    - LEESBURG: Town of Leesburg (Layer 0) - full integration
    - PURCELLVILLE: Town of Purcellville (pol_connect Layer 26) - full integration
    - TIER2_TOWN: Middleburg, Hamilton, Hillsboro, Lovettsville, Round Hill
                  (county fallback with conservative scoring)
    - OTHER_TOWN: Other incorporated towns (limited data)

    Edge cases handled:
    - Missing/unzoned properties
    - Incorporated town zoning detection
    - API failures with graceful degradation

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        dict: {
            'jurisdiction': str,  # 'LOUDOUN', 'LEESBURG', 'PURCELLVILLE', 'TIER2_TOWN', 'OTHER_TOWN'
            'town_name': str or None,  # Name of town if in incorporated area
            'current_zoning': {...},  # Zoning data with 'zoning', 'zoning_description'
            'place_type': {...},  # Place type data
            'development_probability': {
                'score': int,
                'risk_level': str,
                'interpretation': str
            }
        }
    """
    try:
        # Step 1: Detect jurisdiction (county vs town)
        jurisdiction_data = detect_jurisdiction(lat, lon)
        jurisdiction = jurisdiction_data['jurisdiction']
        town_name = jurisdiction_data['town_name']

        # Step 2: Route to appropriate zoning source based on jurisdiction
        if jurisdiction == 'LEESBURG':
            zoning_data = get_leesburg_zoning(lat, lon)
        elif jurisdiction == 'PURCELLVILLE':
            zoning_data = get_purcellville_zoning(lat, lon)
        elif jurisdiction == 'TIER2_TOWN':
            # Tier 2 towns: Middleburg, Hamilton, Hillsboro, Lovettsville, Round Hill
            # These have their own zoning but no GIS layers - use county fallback
            zoning_data = get_zoning_data_loudoun(lat, lon)
            if zoning_data['success']:
                # County layer shows "TOWNS" for incorporated areas
                zoning_data['zoning_description'] = f"Town of {town_name} (zoning data from county layer)"
                zoning_data['note'] = f"For detailed zoning, contact Town of {town_name} planning department"
                zoning_data['tier'] = 2  # Flag as Tier 2 town
        elif jurisdiction == 'OTHER_TOWN':
            # Other incorporated towns - use county layer but note limitation
            zoning_data = get_zoning_data_loudoun(lat, lon)
            if zoning_data['success']:
                zoning_data['zoning_description'] = f"County layer - Town of {town_name} zoning may differ"
                zoning_data['note'] = f"For accurate zoning, check with Town of {town_name} planning department"
        else:
            # Unincorporated Loudoun County
            zoning_data = get_zoning_data_loudoun(lat, lon)

        # Edge case: Handle missing/unzoned properties
        if not zoning_data.get('success') or not zoning_data.get('zoning'):
            zoning_data = {
                'zoning': 'UNZONED',
                'zoning_description': 'Zoning information not available for this location',
                'note': 'This may occur for properties in annexation, recently platted lots, '
                        'or boundary disputes. Contact Loudoun County Planning & Zoning: (703) 777-0397',
                'success': False,
                'jurisdiction': jurisdiction
            }

        # Add jurisdiction info to zoning data
        zoning_data['jurisdiction'] = jurisdiction

        # Step 3: Get place type (applies to all jurisdictions)
        place_type_data = get_place_type_loudoun(lat, lon)

        # Step 4: Calculate development probability with detailed breakdown
        if zoning_data.get('success') and place_type_data.get('success'):
            # Use detailed function for component breakdown
            dev_detailed = calculate_development_probability_detailed(
                zoning_data['zoning'],
                place_type_data['place_type'],
                jurisdiction  # Pass jurisdiction for proper code interpretation
            )

            score = dev_detailed['score']
            risk_level = dev_detailed['risk_level']
            component_scores = dev_detailed['component_scores']
            component_reasons = dev_detailed['component_reasons']

            # Apply conservative scoring for Tier 2 towns
            # These are small, historic towns with generally low development pressure
            # Cap the score since we have limited zoning data
            if jurisdiction == 'TIER2_TOWN':
                # Conservative cap: max score of 30 (Low-Moderate boundary)
                # Tier 2 towns like Middleburg are historic, stable communities
                original_score = score
                score = min(score, 30)
                if original_score > score:
                    zoning_data['score_adjustment'] = f"Capped from {original_score} due to limited town data"
                    risk_level = classify_development_risk(score)

            interpretation = generate_development_interpretation_loudoun(
                zoning_data['zoning'],
                place_type_data['place_type'],
                score,
                risk_level
            )

            # Add jurisdiction context to interpretation for towns
            if jurisdiction in ['LEESBURG', 'PURCELLVILLE']:
                interpretation += f"\n\n*Note: This property is in the incorporated Town of {town_name}. Town zoning regulations apply.*"
            elif jurisdiction == 'TIER2_TOWN':
                interpretation += f"\n\n*Note: This property is in the Town of {town_name}. Limited GIS data available - contact town planning department for detailed zoning information. Score reflects conservative estimate.*"
            elif jurisdiction == 'OTHER_TOWN':
                interpretation += f"\n\n*Note: This property is in the incorporated Town of {town_name}. Contact the town planning department for accurate zoning information.*"
        else:
            score = None
            risk_level = None
            component_scores = {'mismatch': 0, 'restrictiveness': 0, 'pressure': 0}
            component_reasons = {
                'mismatch': 'Data unavailable',
                'restrictiveness': 'Data unavailable',
                'pressure': 'Data unavailable'
            }
            # Generate partial interpretation if we have some data
            if zoning_data.get('success') and not place_type_data.get('success'):
                interpretation = f"Unable to calculate development probability - place type data unavailable. Error: {place_type_data.get('error', 'Unknown')}"
            elif place_type_data.get('success') and not zoning_data.get('success'):
                interpretation = f"Unable to calculate development probability - zoning data unavailable. Error: {zoning_data.get('error', 'Unknown')}"
            else:
                interpretation = "Unable to calculate development probability - both zoning and place type data unavailable"

        return {
            'jurisdiction': jurisdiction,
            'town_name': town_name,
            'current_zoning': zoning_data,
            'place_type': place_type_data,
            'development_probability': {
                'score': score,
                'risk_level': risk_level,
                'interpretation': interpretation,
                'component_scores': component_scores,
                'component_reasons': component_reasons
            }
        }

    except Exception as e:
        # Graceful degradation on any error
        return {
            'jurisdiction': 'LOUDOUN',
            'town_name': None,
            'current_zoning': {
                'zoning': 'ERROR',
                'zoning_description': 'Unable to load zoning data at this time',
                'note': f'Error: {str(e)}. Please try again. If problem persists, contact support.',
                'success': False
            },
            'place_type': {
                'place_type': None,
                'place_type_code': None,
                'success': False,
                'error': str(e)
            },
            'development_probability': {
                'score': None,
                'risk_level': None,
                'interpretation': 'Unable to analyze zoning due to a system error.',
                'component_scores': {'mismatch': 0, 'restrictiveness': 0, 'pressure': 0},
                'component_reasons': {
                    'mismatch': 'System error',
                    'restrictiveness': 'System error',
                    'pressure': 'System error'
                }
            }
        }


# ===== PART 4: PLAIN ENGLISH TRANSLATIONS =====

import json
import re
from pathlib import Path
from math import radians, cos, sin, asin, sqrt


def _load_translation_file(filename: str) -> Dict:
    """Load a translation JSON file from config directory."""
    config_dir = Path(__file__).parent.parent / "data" / "loudoun" / "config"
    file_path = config_dir / filename

    if not file_path.exists():
        return {}

    with open(file_path, 'r') as f:
        return json.load(f)


def get_plain_english_placetype(place_type_code: str) -> Dict[str, Any]:
    """
    Translate a Loudoun County place type code to plain English.

    Args:
        place_type_code: Place type code (e.g., "SUBNBR", "URBTC")

    Returns:
        dict: {
            'code': str,  # Original code
            'plain_english': str,  # Plain English translation
            'official_name': str,  # Official Loudoun County name
            'description': str,  # Full description
            'typical_uses': list,  # Common uses
            'density_range': str,  # Density information
            'character': str,  # Neighborhood character
            'success': bool
        }

    Example:
        >>> result = get_plain_english_placetype("SUBNBR")
        >>> result['plain_english']
        'Suburban neighborhood'
    """
    result = {
        'code': place_type_code,
        'plain_english': None,
        'official_name': None,
        'description': None,
        'typical_uses': [],
        'density_range': None,
        'character': None,
        'success': False
    }

    if not place_type_code:
        return result

    # Load translations
    data = _load_translation_file("placetype_translations.json")
    translations = data.get('translations', {})

    # Normalize code (uppercase, no spaces)
    code_upper = place_type_code.upper().strip()

    # Look up translation
    if code_upper in translations:
        trans = translations[code_upper]
        result['plain_english'] = trans.get('plain_english')
        result['official_name'] = trans.get('official_name')
        result['description'] = trans.get('description')
        result['typical_uses'] = trans.get('typical_uses', [])
        result['density_range'] = trans.get('density_range')
        result['character'] = trans.get('character')
        result['success'] = True
    else:
        # Fallback: format the code as best we can
        result['plain_english'] = place_type_code.replace('_', ' ').title()
        result['official_name'] = place_type_code
        result['description'] = f"Loudoun County place type: {place_type_code}"

    return result


def get_plain_english_zoning(zoning_code: str) -> Dict[str, Any]:
    """
    Translate a Loudoun County zoning code to plain English.

    Supports both static translations for known codes and dynamic
    pattern matching for R-series, PDH-series, etc.

    Args:
        zoning_code: Zoning code (e.g., "PDH3", "R-3", "GI")

    Returns:
        dict: {
            'code': str,  # Original code
            'plain_english': str,  # Plain English translation
            'official_name': str,  # Official name
            'description': str,  # Full description
            'typical_homes': str,  # Housing types
            'character': str,  # Area character
            'success': bool
        }

    Examples:
        >>> result = get_plain_english_zoning("PDH3")
        >>> result['plain_english']
        'Planned neighborhood (up to 3 homes/acre)'

        >>> result = get_plain_english_zoning("R-3")
        >>> result['plain_english']
        'Residential (3 homes/acre allowed)'
    """
    result = {
        'code': zoning_code,
        'plain_english': None,
        'official_name': None,
        'description': None,
        'typical_homes': None,
        'character': None,
        'success': False
    }

    if not zoning_code:
        return result

    # Load translations
    data = _load_translation_file("zoning_translations.json")
    static_trans = data.get('static_translations', {})
    dynamic_patterns = data.get('dynamic_patterns', {})

    # Normalize code (uppercase, no spaces)
    code_upper = zoning_code.upper().strip()
    # Also try without hyphen for matching
    code_no_hyphen = code_upper.replace('-', '')

    # First try static lookup (exact match)
    if code_upper in static_trans:
        trans = static_trans[code_upper]
        result['plain_english'] = trans.get('plain_english')
        result['official_name'] = trans.get('official_name')
        result['description'] = trans.get('description')
        result['typical_homes'] = trans.get('typical_homes')
        result['character'] = trans.get('character')
        result['success'] = True
        return result

    # Try without hyphen
    if code_no_hyphen in static_trans:
        trans = static_trans[code_no_hyphen]
        result['plain_english'] = trans.get('plain_english')
        result['official_name'] = trans.get('official_name')
        result['description'] = trans.get('description')
        result['typical_homes'] = trans.get('typical_homes')
        result['character'] = trans.get('character')
        result['success'] = True
        return result

    # Try dynamic pattern matching
    for pattern_name, pattern_info in dynamic_patterns.items():
        pattern = pattern_info.get('pattern', '')
        match = re.match(pattern, code_upper)
        if match:
            n = match.group(1)  # Extract the number
            template = pattern_info.get('template', '')
            desc_template = pattern_info.get('description_template', '')

            result['plain_english'] = template.replace('{n}', n)
            result['description'] = desc_template.replace('{n}', n)
            result['official_name'] = f"{pattern_name.split('-')[0]}-{n}"
            result['success'] = True
            return result

    # Fallback: format as best we can
    result['plain_english'] = f"Zoning: {zoning_code}"
    result['official_name'] = zoning_code
    result['description'] = f"Loudoun County zoning district: {zoning_code}"

    return result


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in miles using Haversine formula.
    """
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return R * c


def characterize_building_permits(
    lat: float,
    lon: float,
    radius_miles: float = 0.5,
    months_back: int = 6
) -> Optional[Dict[str, Any]]:
    """
    Analyze building permits near a location to characterize development activity.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        radius_miles: Search radius in miles (default 0.5)
        months_back: Only include permits from the last N months (default 6)

    Returns:
        dict: {
            'total_permits': int,  # Total permits found
            'permits_by_type': dict,  # Count by permit type (BLDC, BLDR, etc.)
            'work_class_breakdown': dict,  # Count by work class (New, Alteration, Addition)
            'cost_summary': dict,  # Total, average, median, max costs
            'major_projects': list,  # Projects over $3M
            'community_counts': dict,  # Permit counts by subdivision/community
            'property_community': str,  # Community name for the searched location
            'recent_activity': str,  # Development activity level
            'sample_permits': list,  # Up to 5 recent permits
            'radius_miles': float,
            'months_back': int,
            'success': bool
        }

        Returns None if permit data is unavailable.

    Example:
        >>> result = characterize_building_permits(39.112492, -77.497378, radius_miles=2)
        >>> result['total_permits']
        31
        >>> result['work_class_breakdown']
        {'Alteration': 18, 'Addition': 5, 'New': 3}
    """
    # Try to load building permits data
    data_dir = Path(__file__).parent.parent / "data" / "loudoun" / "building_permits"

    # Try multiple possible file names - prefer complete file with richer data
    possible_files = [
        "loudoun_permits_2024_2025_complete.csv",  # Rich data with costs, work class
        "loudoun_permits_2024_2025_geocoded.csv",
        "loudoun_permits_2024_2025_FINAL.csv",
        "loudoun_permits_CLEAN (2).csv",
    ]

    permits_file = None
    for filename in possible_files:
        filepath = data_dir / filename
        if filepath.exists():
            permits_file = filepath
            break

    if not permits_file:
        return None

    # Parse CSV and find permits within radius
    nearby_permits = []
    work_class_counts = {}
    costs = []
    community_counts = {}
    property_community = None

    try:
        import csv
        from datetime import datetime, timedelta

        # Calculate cutoff date for filtering
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)

        # Use latin-1 encoding for Windows-generated CSVs (handles non-UTF8 chars)
        with open(permits_file, 'r', encoding='latin-1') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Filter by date - only include recent permits
                    date_str = row.get('Permit Issue Date', row.get('issue_date', ''))
                    if date_str:
                        try:
                            # Try YYYY-MM-DD format first (complete file)
                            permit_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            try:
                                # Try M/D/YYYY format (geocoded file)
                                permit_date = datetime.strptime(date_str, '%m/%d/%Y')
                            except ValueError:
                                permit_date = None

                        if permit_date and permit_date < cutoff_date:
                            continue  # Skip permits older than cutoff

                    # Handle different column naming conventions
                    permit_lat = float(row.get('Latitude', row.get('latitude', 0)))
                    permit_lon = float(row.get('Longitude', row.get('longitude', 0)))

                    if permit_lat == 0 or permit_lon == 0:
                        continue

                    distance = _haversine_distance(lat, lon, permit_lat, permit_lon)

                    if distance <= radius_miles:
                        # Extract permit info with fallbacks for different column names
                        permit_number = row.get('Permit Number', row.get('permit_number', 'Unknown'))
                        issue_date = row.get('Permit Issue Date', row.get('issue_date', ''))
                        address = row.get('Address', row.get('full_address', row.get('geocoded_address', '')))
                        work_class = row.get('Permit Work Class', row.get('work_class', ''))
                        subdivision = row.get('Subdivision', row.get('subdivision', ''))
                        structure_type = row.get('Structure Type', row.get('structure_type', ''))
                        description = row.get('Permit Description', row.get('description', ''))

                        # Parse cost
                        cost_str = row.get('Estimated Construction Cost', row.get('estimated_cost', '0'))
                        try:
                            cost = float(str(cost_str).replace(',', '').replace('$', ''))
                        except (ValueError, TypeError):
                            cost = 0

                        nearby_permits.append({
                            'permit_number': permit_number,
                            'issue_date': issue_date,
                            'address': address,
                            'work_class': work_class,
                            'subdivision': subdivision,
                            'structure_type': structure_type,
                            'description': description,
                            'cost': cost,
                            'distance_miles': round(distance, 2)
                        })

                        # Track work class
                        if work_class:
                            work_class_counts[work_class] = work_class_counts.get(work_class, 0) + 1

                        # Track costs (only non-zero)
                        if cost > 0:
                            costs.append(cost)

                        # Track community counts
                        if subdivision:
                            community_counts[subdivision] = community_counts.get(subdivision, 0) + 1

                        # Track closest permit's community for property context
                        if property_community is None and subdivision:
                            property_community = subdivision

                except (ValueError, TypeError):
                    continue
    except Exception as e:
        return None

    # Sort by distance
    nearby_permits.sort(key=lambda x: x['distance_miles'])

    # Update property_community to closest permit's community
    if nearby_permits and nearby_permits[0].get('subdivision'):
        property_community = nearby_permits[0]['subdivision']

    # Characterize activity level
    total = len(nearby_permits)
    if total == 0:
        activity = "None"
    elif total <= 3:
        activity = "Low"
    elif total <= 10:
        activity = "Moderate"
    elif total <= 25:
        activity = "High"
    else:
        activity = "Very High"

    # Categorize permits by type (based on permit number prefix)
    permits_by_type = {}
    for permit in nearby_permits:
        permit_num = permit['permit_number']
        # Extract prefix (e.g., BLDC, BLDR, ELEC, etc.)
        prefix = permit_num.split('-')[0] if '-' in permit_num else 'OTHER'
        permits_by_type[prefix] = permits_by_type.get(prefix, 0) + 1

    # Calculate cost summary
    cost_summary = {
        'total_value': sum(costs) if costs else 0,
        'average_cost': sum(costs) / len(costs) if costs else 0,
        'median_cost': sorted(costs)[len(costs) // 2] if costs else 0,
        'max_cost': max(costs) if costs else 0,
        'permits_with_costs': len(costs)
    }

    # Identify major projects (>$3M)
    major_projects = [
        {
            'permit_number': p['permit_number'],
            'address': p['address'],
            'cost': p['cost'],
            'description': p['description'],
            'structure_type': p['structure_type']
        }
        for p in nearby_permits if p['cost'] > 3_000_000
    ]
    major_projects.sort(key=lambda x: x['cost'], reverse=True)

    return {
        'total_permits': total,
        'permits_by_type': permits_by_type,
        'work_class_breakdown': work_class_counts,
        'cost_summary': cost_summary,
        'major_projects': major_projects[:5],  # Top 5 major projects
        'community_counts': community_counts,
        'property_community': property_community,
        'recent_activity': activity,
        'sample_permits': nearby_permits[:5],  # First 5 closest
        'radius_miles': radius_miles,
        'months_back': months_back,
        'success': True
    }


# ============================================================================
# NARRATIVE GENERATION HELPER FUNCTIONS
# ============================================================================

def _format_large_cost(cost: float) -> str:
    """Format large costs as $XM or $XK for readability. Escaped for Streamlit."""
    if cost >= 1_000_000:
        return f"\\${cost / 1_000_000:.1f}M"
    elif cost >= 1_000:
        return f"\\${cost / 1_000:.0f}K"
    else:
        return f"\\${cost:,.0f}"


def _pluralize(count: int, singular: str, plural: str = None) -> str:
    """Return singular or plural form based on count."""
    if plural is None:
        plural = singular + 's'
    return singular if count == 1 else plural


def _clean_structure_type(structure_type: str) -> str:
    """Convert technical structure types to readable names."""
    if not structure_type:
        return 'project'
    type_map = {
        'other - public (commercial)': 'public building',
        'other - residential': 'residential structure',
        'data center': 'data center',
        'single family dwelling': 'single-family home',
        'townhouse': 'townhouse',
        'commercial': 'commercial building',
    }
    return type_map.get(structure_type.lower(), structure_type.lower())


def generate_zoning_narrative(
    zoning_data: dict,
    place_data: dict,
    community_data: Optional[dict] = None
) -> str:
    """
    Generate flowing prose narrative explaining property's zoning.

    Args:
        zoning_data: From zoning translation dictionary
            - plain_english: "Planned neighborhood (3 homes/acre)"
            - description: "Master-planned residential community..."
            - typical_homes: "Single-family homes, some townhouses"
            - density: "Up to 3 units per acre"
            - character: "Established planned community"
        place_data: From place type translation dictionary
            - plain_english: "Suburban neighborhood"
            - description: Area character description
            - character: Brief descriptor
        community_data: Optional HOA/community info
            - name: Community name
            - amenities: List of amenities

    Returns:
        str: 2-3 paragraph flowing narrative (200-350 words)
    """
    paragraphs = []

    # Extract zoning info
    plain_english = zoning_data.get('plain_english', 'a zoned area')
    description = zoning_data.get('description', '')
    typical_homes = zoning_data.get('typical_homes', '')
    density = zoning_data.get('density', '')
    character = zoning_data.get('character', '')

    # PARAGRAPH 1: What this zoning means practically
    # Add article "a" or "an" before the zoning type
    plain_lower = plain_english.lower()
    article = "an" if plain_lower[0] in 'aeiou' else "a"
    p1 = f"This property sits in {article} {plain_lower}"

    # Add description context
    if description:
        # Transform technical language to conversational
        desc_lower = description.lower()
        if 'master-planned' in desc_lower:
            p1 += " where developers designed a cohesive community"
        elif 'agricultural' in desc_lower:
            p1 += " preserving the rural character of western Loudoun"
        elif 'commercial' in desc_lower:
            p1 += " intended for business and retail uses"
        else:
            p1 += f". {description}"

    # Add typical homes context
    if typical_homes:
        homes_lower = typical_homes.lower()
        if 'single-family' in homes_lower and 'townhouse' in homes_lower:
            p1 += " mixing single-family homes with some townhouses"
        elif 'single-family' in homes_lower:
            p1 += " with primarily single-family homes"
        elif 'townhouse' in homes_lower or 'attached' in homes_lower:
            p1 += " featuring attached homes and townhouses"
        elif 'apartment' in homes_lower or 'multi' in homes_lower:
            p1 += " including multi-family apartment buildings"

    p1 += "."

    # Add density context with comparison
    import re
    # Try to extract density from description if not in density field
    density_text = density if density else description
    if density_text:
        density_lower = density_text.lower()
        # Extract density number for comparison
        density_match = re.search(r'(\d+)\s*(?:units?|homes?)', density_lower)
        if density_match:
            density_num = int(density_match.group(1))
            if density_num <= 3:
                p1 += f" The {density_num}-home-per-acre density cap means larger lots compared to newer developments (which often run 6-8 units/acre). This lower density typically translates to more private yards and less traffic."
            elif density_num <= 6:
                p1 += f" At {density_num} homes per acre, lot sizes are moderate for suburban Loudoun, balancing privacy with community density."
            else:
                p1 += f" The {density_num}-unit-per-acre density allows for more compact development typical of urban metro areas, prioritizing walkability and amenities over large lots."
    elif character:
        # Use character if no density available
        p1 += f" The neighborhood has a {character.lower()} feel."

    paragraphs.append(p1)

    # PARAGRAPH 2: Community amenities if available
    if community_data:
        name = community_data.get('name', '')
        amenities = community_data.get('amenities', [])

        if name and amenities:
            # Format amenities with proper articles
            formatted_amenities = []
            for amenity in amenities:
                amenity_lower = amenity.lower().strip()
                # Check if already has article or is plural
                if (amenity_lower.startswith(('a ', 'an ', 'the ')) or
                    (amenity_lower.endswith('s') and not amenity_lower.endswith('ss'))):
                    # Already formatted or plural - use as-is
                    formatted_amenities.append(amenity)
                elif amenity_lower[0].isdigit():
                    # Numbers: 8, 11, 18 start with vowel sounds
                    vowel_sound_numbers = ('8', '11', '18')
                    if amenity_lower.startswith(vowel_sound_numbers):
                        formatted_amenities.append(f"an {amenity}")
                    else:
                        formatted_amenities.append(f"a {amenity}")
                else:
                    # Add article for singular items
                    art = "an" if amenity_lower[0] in 'aeiou' else "a"
                    formatted_amenities.append(f"{art} {amenity}")

            p2 = f"You're in {name}, which offers "
            if len(formatted_amenities) == 1:
                p2 += formatted_amenities[0]
            elif len(formatted_amenities) == 2:
                p2 += f"{formatted_amenities[0]} and {formatted_amenities[1]}"
            else:
                p2 += ", ".join(formatted_amenities[:-1]) + f", and {formatted_amenities[-1]}"
            p2 += ". These amenities are protected by the community's HOA and zoning regulations."
            paragraphs.append(p2)
        elif name:
            p2 = f"You're in the {name} community, an established neighborhood with its own character and HOA governance."
            paragraphs.append(p2)

    # PARAGRAPH 3: Broader area character
    place_plain = place_data.get('plain_english', '')
    place_char = place_data.get('character', '')

    if place_plain or place_char:
        p3 = "The broader area: "
        if place_plain:
            # Capitalize proper nouns in place name
            place_formatted = place_plain
            for proper_noun in ['leesburg', 'loudoun', 'ashburn', 'sterling', 'purcellville']:
                place_formatted = place_formatted.replace(proper_noun, proper_noun.capitalize())
                place_formatted = place_formatted.replace(proper_noun.capitalize().lower(), proper_noun.capitalize())
            p3 += f"this is part of {place_formatted}"
        if place_char:
            # Capitalize proper nouns in character description
            char_formatted = place_char.lower()
            for proper_noun in ['leesburg', 'loudoun', 'ashburn', 'sterling', 'purcellville']:
                char_formatted = char_formatted.replace(proper_noun, proper_noun.capitalize())
            p3 += f", with {char_formatted} character."
        elif not p3.endswith('.'):
            p3 += "."
        paragraphs.append(p3)

    return "\n\n".join(paragraphs)


def generate_permit_narrative(
    permit_data: dict,
    activity_level: str,
    property_community: Optional[str] = None
) -> str:
    """
    Generate flowing narrative about building permit activity.

    Args:
        permit_data: From characterize_building_permits()
            - total_permits: 149
            - permits_by_type: {'BLDR': 137, 'BLDC': 11, ...}
            - work_class_breakdown: {'Addition': 32, 'New Construction': 36, ...}
            - cost_summary: {total_value, average_cost, median_cost, max_cost}
            - major_projects: [{address, cost, description}, ...]
            - community_counts: {community_name: permit_count, ...}
            - property_community: 'RIVER CREEK'
            - radius_miles: 2
            - months_back: 6
        activity_level: 'Low', 'Moderate', 'High', 'Very High'
        property_community: Current property's community name

    Returns:
        str: 2-4 paragraph flowing narrative (400-700 words)
    """
    # Extract key metrics
    total = permit_data.get('total_permits', 0)
    radius = permit_data.get('radius_miles', 2)
    months = permit_data.get('months_back', 6)

    work_class = permit_data.get('work_class_breakdown', {})
    costs = permit_data.get('cost_summary', {})
    major_projects = permit_data.get('major_projects', [])
    permits_by_type = permit_data.get('permits_by_type', {})
    community_counts = permit_data.get('community_counts', {})

    if not property_community:
        property_community = permit_data.get('property_community', '')

    paragraphs = []

    # PARAGRAPH 1: Overall activity with breakdown
    residential = permits_by_type.get('BLDR', 0)
    commercial = permits_by_type.get('BLDC', 0)
    total_value = costs.get('total_value', 0)

    p1 = f"The {radius}-mile radius around this property has seen {total} building permits over the past {months} months"

    if residential and commercial:
        p1 += f", breaking down to {residential} residential and {commercial} commercial projects"
    elif residential:
        p1 += ", all residential projects"

    if total_value > 0:
        p1 += f", totaling {_format_large_cost(total_value)} in construction value"

    p1 += ". "

    # Add interpretation based on activity level
    if activity_level == 'Very High' and total > 50:
        # Calculate % of minor improvements
        minor_types = ['Addition', 'Alteration', 'Deck - County Typical',
                       'Basement - County Typical', 'Pool', 'Repair']
        minor = sum(work_class.get(t, 0) for t in minor_types)

        if total > 0 and minor / total > 0.5:
            pct = int((minor / total) * 100)
            p1 += f"But here's the important context: {pct}% of this activity is homeowner renovations (additions, decks, basements), not new development. "
        else:
            new_construction = work_class.get('New Construction - From Masterfile (R)', 0) + work_class.get('New Construction', 0)
            if new_construction > 0:
                p1 += f"This includes {new_construction} new home constructions, indicating active development. "
    elif activity_level == 'Low':
        p1 += "This low activity suggests a stable, established neighborhood where major development has concluded. "
    elif activity_level == 'Moderate':
        p1 += "This moderate pace reflects a mature community with ongoing improvements rather than expansion. "

    paragraphs.append(p1)

    # PARAGRAPH 2: Detailed breakdown
    p2 = "Breaking down the construction types: "

    # Sort and format work class items
    sorted_work = sorted(work_class.items(), key=lambda x: -x[1])[:6]
    breakdown_parts = []

    for work_class_name, count in sorted_work:
        # Convert technical names to readable and pluralize properly
        name_lower = work_class_name.lower()

        if 'new construction - from masterfile' in name_lower:
            readable = _pluralize(count, 'new home build')
        elif 'new construction' in name_lower:
            readable = 'new construction'  # Uncountable
        elif 'addition' in name_lower:
            readable = _pluralize(count, 'addition')
        elif 'alteration' in name_lower:
            readable = _pluralize(count, 'alteration')
        elif 'deck' in name_lower:
            readable = _pluralize(count, 'deck')
        elif 'basement' in name_lower:
            readable = _pluralize(count, 'basement')
        elif 'pool' in name_lower:
            readable = _pluralize(count, 'pool')
        elif 'tenant fit-up' in name_lower:
            readable = _pluralize(count, 'commercial tenant fit-up')
        elif 'repair' in name_lower:
            readable = _pluralize(count, 'repair')
        elif 'demolition' in name_lower:
            readable = _pluralize(count, 'demolition')
        else:
            # Default: just use the name as-is
            readable = work_class_name.replace(' - County Typical', '').lower()

        breakdown_parts.append(f"{count} {readable}")

    p2 += ", ".join(breakdown_parts) + ". "

    # Add cost context
    avg_cost = costs.get('average_cost', 0)
    median_cost = costs.get('median_cost', 0)
    max_cost = costs.get('max_cost', 0)

    if median_cost > 0:
        p2 += f"The median project cost is {_format_large_cost(median_cost)}"
        if avg_cost > 0:
            p2 += f" with an average of {_format_large_cost(avg_cost)}"

        # Interpret cost distribution
        if avg_cost > 0 and median_cost < avg_cost * 0.4:
            p2 += " (most projects are modest improvements, with a few large outliers pulling up the average)"
        elif avg_cost > 0 and median_cost > avg_cost * 0.8:
            p2 += " (costs are fairly consistent across projects)"

        p2 += "."

    paragraphs.append(p2)

    # PARAGRAPH 3: Major projects (if any >$3M)
    if major_projects:
        num_major = len(major_projects)
        p3 = f"Notable major project{'s' if num_major > 1 else ''} in this radius: "

        project_descriptions = []
        for proj in major_projects[:3]:
            cost_str = _format_large_cost(proj['cost'])
            addr = proj.get('address', 'Unknown location')
            # Truncate long addresses
            if len(addr) > 45:
                addr = addr[:42] + "..."
            structure = _clean_structure_type(proj.get('structure_type', ''))

            project_descriptions.append(f"a {cost_str} {structure} at {addr}")

        p3 += ", ".join(project_descriptions) + ". "

        # Interpret major projects
        structures = [p.get('structure_type', '').lower() for p in major_projects]
        if 'data center' in ' '.join(structures):
            p3 += "Data center construction is common in eastern Loudoun but typically well-separated from residential areas."

        paragraphs.append(p3)

    # PARAGRAPH 4: Community comparison
    if community_counts and property_community:
        # Get top communities for comparison
        sorted_communities = sorted(community_counts.items(), key=lambda x: -x[1])
        top_5 = sorted_communities[:5]

        property_count = community_counts.get(property_community, 0)

        p4 = f"Comparing activity across communities in this radius: "

        # Find property's position
        position = None
        for i, (name, count) in enumerate(sorted_communities):
            if name == property_community:
                position = i + 1
                break

        if position and position <= 3:
            p4 += f"{property_community} ranks #{position} for permit activity with {property_count} permits. "
        elif property_count > 0:
            p4 += f"{property_community} has {property_count} permits. "

        # Name top communities for comparison
        others = [(n, c) for n, c in top_5 if n != property_community][:3]
        if others:
            comparisons = [f"{name} ({count})" for name, count in others]
            p4 += f"Top activity areas: {', '.join(comparisons)}."

        paragraphs.append(p4)

    return "\n\n".join(paragraphs)


def generate_nearby_zoning_narrative(
    zone_proximity_data: Dict[str, Dict],
    current_zoning: str,
    translations: dict
) -> str:
    """
    Generate interpretive narrative about nearby zoning patterns.

    Args:
        zone_proximity_data: Dict from analyze_zone_proximity()
            Each key is zoning code, value is dict with:
            - count: Number of parcels with this zoning
            - plain_english: Plain English translation
            - nearest_distance_miles: Distance to nearest parcel
        current_zoning: Current property's zoning code
        translations: Dict with 'zoning_translations' and 'placetype_translations'

    Returns:
        str: 2-3 paragraph flowing narrative (300-500 words)
    """
    if not zone_proximity_data:
        return "No nearby zoning data available for analysis."

    zoning_trans = translations.get('zoning_translations', {})

    paragraphs = []

    # Convert dict to list with distances for easier processing
    zones_list = []
    for code, data in zone_proximity_data.items():
        zones_list.append({
            'code': code,
            'count': data.get('count', 1),
            'distance': data.get('nearest_distance_miles', 5.0),
            'plain_english': data.get('plain_english', code)
        })

    # Separate by distance
    immediate = [z for z in zones_list if z['distance'] <= 0.5]
    nearby = [z for z in zones_list if 0.5 < z['distance'] <= 2.0]
    broader = [z for z in zones_list if z['distance'] > 2.0]

    # PARAGRAPH 1: Immediate buffer (0-0.5 miles)
    p1 = "Looking at the immediate half-mile around your property: "

    if not immediate:
        p1 += "the surrounding area is primarily open or part of the same development. "
    else:
        # Group by type
        immediate_sorted = sorted(immediate, key=lambda x: x['distance'])

        if len(immediate) == 1:
            z = immediate[0]
            p1 += f"you're surrounded by {z['plain_english'].lower()} zoning, meaning consistent neighborhood character. "
        else:
            zone_names = [z['plain_english'].lower() for z in immediate_sorted[:3]]
            p1 += f"you'll find {', '.join(zone_names)}. "

    # Check if buffered by similar zoning
    current_plain = zoning_trans.get(current_zoning, {}).get('plain_english', current_zoning)
    similar_nearby = any(z['code'] == current_zoning for z in immediate)
    if similar_nearby:
        p1 += f"Your property is well-buffered by similar {current_plain.lower()} development."

    paragraphs.append(p1)

    # PARAGRAPH 2: Nearby patterns (0.5-2 miles) - where daily life happens
    if nearby or broader:
        p2 = "Looking at the broader 2-mile radius where you'd run errands and commute: "

        all_zones = nearby + broader[:5]  # Focus on closer zones

        # Categorize
        residential = []
        commercial = []
        industrial = []

        for z in all_zones:
            plain_lower = z['plain_english'].lower()
            if any(word in plain_lower for word in ['residential', 'neighborhood', 'home', 'planned']):
                residential.append(z)
            elif any(word in plain_lower for word in ['commercial', 'office', 'retail', 'business', 'town center']):
                commercial.append(z)
            elif any(word in plain_lower for word in ['industrial', 'manufacturing']):
                industrial.append(z)

        total_nearby = len(all_zones)

        if total_nearby > 0:
            res_pct = len(residential) / total_nearby * 100
            com_pct = len(commercial) / total_nearby * 100

            if res_pct > 70:
                p2 += "the area is predominantly residential "
            elif com_pct > 30:
                p2 += "there's a healthy mix of residential and commercial zoning "
            else:
                p2 += "zoning is varied "

        # Find commercial placement
        if commercial:
            nearest_comm = min(commercial, key=lambda x: x['distance'])
            p2 += f"with commercial areas starting at {nearest_comm['distance']:.1f} miles"

            if nearest_comm['distance'] > 1.5:
                p2 += " (appropriately separated from residential)"
            elif nearest_comm['distance'] < 0.5:
                p2 += " (convenient walkable distance)"
            else:
                p2 += " (a short drive away)"

        p2 += "."
        paragraphs.append(p2)

    # PARAGRAPH 3: Interpretation and key observations
    p3 = "What this means for you: "

    # Check for concerning patterns
    industrial_zones = [z for z in zones_list if 'industrial' in z['plain_english'].lower()]
    high_density = [z for z in zones_list if any(word in z['plain_english'].lower()
                    for word in ['apartment', 'multi-family', '8 homes', '16 homes', '24 homes'])]

    concerns = []
    positives = []

    if industrial_zones:
        nearest_ind = min(industrial_zones, key=lambda x: x['distance'])
        if nearest_ind['distance'] < 2:
            concerns.append(f"industrial zoning {nearest_ind['distance']:.1f} miles away (check for noise/traffic)")
        else:
            positives.append("industrial areas are well-separated from your neighborhood")

    if high_density:
        nearest_hd = min(high_density, key=lambda x: x['distance'])
        if nearest_hd['distance'] < 0.5:
            concerns.append(f"higher-density development ({nearest_hd['plain_english'].lower()}) immediately adjacent")

    if not industrial_zones and not [z for z in high_density if z['distance'] < 1]:
        positives.append("your neighborhood's character is protected by consistent residential zoning")

    # Check residential consistency
    if immediate and all('residential' in z['plain_english'].lower() or 'neighborhood' in z['plain_english'].lower()
                         or 'planned' in z['plain_english'].lower() for z in immediate):
        positives.append("similar development surrounds you on all sides")

    if concerns:
        p3 += "Note: " + "; ".join(concerns) + ". "
    if positives:
        p3 += " ".join([p.capitalize() + "." if not p.endswith('.') else p.capitalize() for p in positives[:2]])

    if not concerns and not positives:
        p3 += "The surrounding zoning patterns suggest a stable area with no immediate development pressure."

    # Add a note about what zoning stability means
    if len(positives) >= 2 or not concerns:
        p3 += " Consistent zoning around your property helps maintain property values and neighborhood character over time."

    paragraphs.append(p3)

    return "\n\n".join(paragraphs)


def analyze_zone_proximity(
    lat: float,
    lon: float,
    radius_miles: float = 5.0
) -> Optional[Dict[str, Any]]:
    """
    Analyze zoning districts within a radius of a location.

    Uses the local GeoJSON file for efficient proximity analysis.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        radius_miles: Search radius in miles (default 5.0)

    Returns:
        dict with zone code as key: {
            'zone_code': {
                'count': int,  # Number of parcels
                'plain_english': str,  # Plain English translation
                'nearest_distance_miles': float
            }
        }

        Returns None if zoning data is unavailable.

    Example:
        >>> result = analyze_zone_proximity(39.112492, -77.497378)
        >>> len(result)
        5
        >>> result['PDH4']['count']
        3
    """
    # Load zoning GeoJSON
    data_dir = Path(__file__).parent.parent / "data" / "loudoun" / "gis" / "zoning"
    zoning_file = data_dir / "loudoun_zoning.geojson"

    if not zoning_file.exists():
        return None

    try:
        with open(zoning_file, 'r') as f:
            geojson_data = json.load(f)
    except Exception:
        return None

    features = geojson_data.get('features', [])
    if not features:
        return None

    # Analyze each feature
    zone_analysis = {}

    for feature in features:
        props = feature.get('properties', {})
        zone_code = props.get('ZO_ZONE', 'UNKNOWN')

        # Get centroid of geometry (simplified - use first coordinate for polygons)
        geometry = feature.get('geometry', {})
        geom_type = geometry.get('type', '')
        coords = geometry.get('coordinates', [])

        # Extract a representative point
        try:
            if geom_type == 'Polygon' and coords:
                # Use first point of exterior ring
                ring = coords[0]
                if ring:
                    feat_lon, feat_lat = ring[0][0], ring[0][1]
                else:
                    continue
            elif geom_type == 'MultiPolygon' and coords:
                # Use first point of first polygon's exterior ring
                first_poly = coords[0]
                if first_poly and first_poly[0]:
                    feat_lon, feat_lat = first_poly[0][0][0], first_poly[0][0][1]
                else:
                    continue
            else:
                continue

            # Calculate distance
            distance = _haversine_distance(lat, lon, feat_lat, feat_lon)

            if distance <= radius_miles:
                if zone_code not in zone_analysis:
                    # Get plain English translation
                    trans = get_plain_english_zoning(zone_code)
                    zone_analysis[zone_code] = {
                        'count': 0,
                        'plain_english': trans['plain_english'],
                        'nearest_distance_miles': distance
                    }

                zone_analysis[zone_code]['count'] += 1
                zone_analysis[zone_code]['nearest_distance_miles'] = min(
                    zone_analysis[zone_code]['nearest_distance_miles'],
                    distance
                )
        except (IndexError, TypeError, KeyError):
            continue

    if not zone_analysis:
        return None

    # Sort by nearest distance
    sorted_zones = dict(sorted(
        zone_analysis.items(),
        key=lambda x: x[1]['nearest_distance_miles']
    ))

    return sorted_zones


def get_nearby_zoning_summary(lat: float, lon: float) -> str:
    """
    Generate a plain English summary of nearby zoning.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        str: Human-readable summary of nearby zoning

    Example:
        >>> summary = get_nearby_zoning_summary(39.112492, -77.497378)
        >>> print(summary)
        Nearby zoning (within 5 miles):
        - Planned neighborhood (up to 4 homes/acre): 12 areas
        - Industrial zone: 5 areas
    """
    proximity = analyze_zone_proximity(lat, lon)

    if not proximity:
        return "Unable to analyze nearby zoning - data unavailable"

    lines = ["Nearby zoning (within 5 miles):"]

    for zone_code, info in list(proximity.items())[:10]:  # Top 10
        count = info['count']
        plain = info['plain_english']
        distance = info['nearest_distance_miles']

        if count == 1:
            lines.append(f"- {plain}: 1 area ({distance:.1f} mi away)")
        else:
            lines.append(f"- {plain}: {count} areas (nearest {distance:.1f} mi)")

    return "\n".join(lines)


# ===== TESTING =====

def test_place_type_query():
    """Test place type query with known address."""
    print("=" * 60)
    print("PLACE TYPE QUERY TEST")
    print("=" * 60)

    # Test coordinates: 43470 Plantation Ter, Leesburg, VA 20176
    lat = 39.0845
    lon = -77.5400

    print(f"Testing: 43470 Plantation Ter, Leesburg, VA 20176")
    print(f"Coordinates: {lat}, {lon}")
    print()

    result = get_place_type_loudoun(lat, lon)

    print(f"Success: {result['success']}")
    print(f"Place Type: {result['place_type']}")
    print(f"Place Type Code: {result['place_type_code']}")
    print(f"Policy Area: {result['policy_area']}")
    print(f"Policy Area Code: {result['policy_area_code']}")
    if result['error']:
        print(f"Error: {result['error']}")
    print()

    return result


def test_development_probability():
    """Test development probability scoring."""
    print("=" * 60)
    print("DEVELOPMENT PROBABILITY TEST")
    print("=" * 60)

    test_cases = [
        ("AR-1", "Suburban Mixed Use"),      # High mismatch
        ("R-1", "Suburban Neighborhood"),    # Low mismatch
        ("PD-TC", "Town Center"),            # Already aligned
        ("RC", "Urban Transit Center"),      # Extreme mismatch
        ("PDH4", "Suburban Compact Neighborhood"),  # Moderate
    ]

    for zoning, place_type in test_cases:
        score = calculate_development_probability_loudoun(zoning, place_type)
        risk = classify_development_risk(score)
        print(f"Zoning: {zoning:10} | Place Type: {place_type:30} | Score: {score:3} | Risk: {risk}")

    print()


def test_full_analysis():
    """Test complete property analysis with the specified test address."""
    print("=" * 60)
    print("FULL PROPERTY ZONING ANALYSIS")
    print("=" * 60)

    # Test address: 43470 Plantation Ter, Leesburg, VA 20176
    lat = 39.0845
    lon = -77.5400

    print(f"Address: 43470 Plantation Ter, Leesburg, VA 20176")
    print(f"Coordinates: lat={lat}, lon={lon}")
    print(f"Type: Confirmed single-family residential in River Creek")
    print()

    result = analyze_property_zoning_loudoun(lat, lon)

    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()

    print("Jurisdiction:")
    print(f"  Jurisdiction: {result['jurisdiction']}")
    print(f"  Town Name: {result['town_name']}")
    print()

    print("Current Zoning:")
    print(f"  Success: {result['current_zoning']['success']}")
    print(f"  Zoning Code: {result['current_zoning']['zoning']}")
    print(f"  Description: {result['current_zoning']['zoning_description']}")
    if result['current_zoning'].get('error'):
        print(f"  Error: {result['current_zoning']['error']}")
    print()

    print("Place Type:")
    print(f"  Success: {result['place_type']['success']}")
    print(f"  Place Type: {result['place_type']['place_type']}")
    print(f"  Policy Area: {result['place_type']['policy_area']}")
    if result['place_type'].get('error'):
        print(f"  Error: {result['place_type']['error']}")
    print()

    print("Development Probability:")
    print(f"  Score: {result['development_probability']['score']}")
    print(f"  Risk Level: {result['development_probability']['risk_level']}")
    print()
    print("Interpretation:")
    print(result['development_probability']['interpretation'])
    print()

    return result


def test_town_zoning():
    """Test zoning queries for all three jurisdictions."""
    import json

    print("=" * 70)
    print("TOWN ZONING INTEGRATION TESTS")
    print("=" * 70)
    print()

    # Test cases with coordinates
    test_cases = [
        {
            'name': 'TEST 1: Unincorporated Loudoun (Ashburn)',
            'address': 'Ashburn, VA',
            'lat': 39.0437,
            'lon': -77.4875,
            'expected_jurisdiction': 'LOUDOUN'
        },
        {
            'name': 'TEST 2: Leesburg (Downtown)',
            'address': '25 W Market St, Leesburg, VA 20176',
            'lat': 39.1157,
            'lon': -77.5637,
            'expected_jurisdiction': 'LEESBURG'
        },
        {
            'name': 'TEST 3: Purcellville (Downtown)',
            'address': '221 S Nursery Ave, Purcellville, VA 20132',
            'lat': 39.1375,
            'lon': -77.7147,
            'expected_jurisdiction': 'PURCELLVILLE'
        }
    ]

    results = []

    for test in test_cases:
        print("-" * 70)
        print(test['name'])
        print("-" * 70)
        print(f"Address: {test['address']}")
        print(f"Coordinates: lat={test['lat']}, lon={test['lon']}")
        print(f"Expected Jurisdiction: {test['expected_jurisdiction']}")
        print()

        result = analyze_property_zoning_loudoun(test['lat'], test['lon'])

        # Check if jurisdiction matches expected
        jurisdiction_match = result['jurisdiction'] == test['expected_jurisdiction']
        status = "✅ PASS" if jurisdiction_match else "❌ FAIL"

        print(f"Results:")
        print(f"  Jurisdiction: {result['jurisdiction']} {status}")
        print(f"  Town Name: {result['town_name']}")
        print(f"  Zoning Code: {result['current_zoning']['zoning']}")
        print(f"  Zoning Description: {result['current_zoning']['zoning_description']}")
        print(f"  Place Type: {result['place_type']['place_type']}")
        print(f"  Development Score: {result['development_probability']['score']}")
        print(f"  Risk Level: {result['development_probability']['risk_level']}")
        print()

        results.append({
            'test': test['name'],
            'passed': jurisdiction_match,
            'result': result
        })

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r['passed'])
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"  {status} {r['test']}")

    print()

    if passed == total:
        print("✅ ALL TESTS PASSED - Town zoning integration working!")
    else:
        print("⚠️  Some tests failed - review results above")

    return results


if __name__ == "__main__":
    print()
    test_town_zoning()  # Primary test - all three jurisdictions
