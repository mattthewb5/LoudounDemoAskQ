"""
County configuration registry and helper functions.

This module provides:
- County configuration registry (SUPPORTED_COUNTIES)
- Helper functions to query county capabilities
- Configuration validation

Usage:
    from config import get_county_config, get_production_counties

    # Get a specific county's config
    loudoun = get_county_config("loudoun")

    # Get all production-ready counties
    prod_counties = get_production_counties()
"""

from typing import Dict, List, Optional
from .base_config import CountyConfig
from .athens_clarke import ATHENS_CLARKE_CONFIG, get_athens_config
from .loudoun import LOUDOUN_CONFIG, get_loudoun_config


# ===== COUNTY REGISTRY =====

SUPPORTED_COUNTIES: Dict[str, CountyConfig] = {
    "athens_clarke": ATHENS_CLARKE_CONFIG,
    "loudoun": LOUDOUN_CONFIG,
}


# ===== HELPER FUNCTIONS =====

def get_county_config(county_name: str) -> Optional[CountyConfig]:
    """
    Get configuration for a specific county.

    Args:
        county_name: County identifier (e.g., "athens_clarke", "loudoun")

    Returns:
        CountyConfig object if county exists, None otherwise

    Example:
        >>> config = get_county_config("loudoun")
        >>> print(config.display_name)
        'Loudoun County'
    """
    return SUPPORTED_COUNTIES.get(county_name)


def get_all_counties() -> List[str]:
    """
    Get list of all supported county names.

    Returns:
        List of county identifiers

    Example:
        >>> counties = get_all_counties()
        >>> print(counties)
        ['athens_clarke', 'loudoun']
    """
    return list(SUPPORTED_COUNTIES.keys())


def get_production_counties() -> List[str]:
    """
    Get list of production-ready counties.

    Returns:
        List of county identifiers where is_production_ready=True

    Example:
        >>> prod = get_production_counties()
        >>> print(prod)
        ['athens_clarke']
    """
    return [
        name for name, config in SUPPORTED_COUNTIES.items()
        if config.is_production_ready
    ]


def get_primary_county() -> Optional[str]:
    """
    Get the developer's primary county (for validation).

    Returns:
        County identifier where is_primary_county=True, or None

    Example:
        >>> primary = get_primary_county()
        >>> print(primary)
        'loudoun'
    """
    for name, config in SUPPORTED_COUNTIES.items():
        if config.is_primary_county:
            return name
    return None


def get_counties_with_feature(feature: str) -> List[str]:
    """
    Get counties that have a specific feature implemented.

    Args:
        feature: Feature name ('school', 'crime', 'zoning')

    Returns:
        List of county identifiers with that feature

    Example:
        >>> with_schools = get_counties_with_feature('school')
        >>> print(with_schools)
        ['athens_clarke']
    """
    feature_flags = {
        'school': 'has_school_data',
        'crime': 'has_crime_data',
        'zoning': 'has_zoning_data'
    }

    flag_name = feature_flags.get(feature)
    if not flag_name:
        raise ValueError(f"Unknown feature: {feature}. Must be 'school', 'crime', or 'zoning'")

    return [
        name for name, config in SUPPORTED_COUNTIES.items()
        if getattr(config, flag_name, False)
    ]


def can_validate_county(county_name: str) -> bool:
    """
    Check if a county can be validated locally.

    Args:
        county_name: County identifier

    Returns:
        True if developer can validate results locally

    Example:
        >>> can_validate_county("loudoun")
        True
        >>> can_validate_county("athens_clarke")
        False
    """
    config = get_county_config(county_name)
    if config:
        return config.can_validate_locally
    return False


def get_county_display_name(county_name: str) -> Optional[str]:
    """
    Get human-readable county name.

    Args:
        county_name: County identifier

    Returns:
        Display name (e.g., "Loudoun County") or None

    Example:
        >>> get_county_display_name("loudoun")
        'Loudoun County'
    """
    config = get_county_config(county_name)
    if config:
        return config.display_name
    return None


def get_counties_by_state(state: str) -> List[str]:
    """
    Get all counties in a specific state.

    Args:
        state: Two-letter state code (e.g., "VA", "GA")

    Returns:
        List of county identifiers in that state

    Example:
        >>> va_counties = get_counties_by_state("VA")
        >>> print(va_counties)
        ['loudoun']
    """
    return [
        name for name, config in SUPPORTED_COUNTIES.items()
        if config.state == state
    ]


def get_multi_jurisdiction_counties() -> List[str]:
    """
    Get counties with incorporated towns (multi-jurisdiction).

    Returns:
        List of county identifiers with incorporated towns

    Example:
        >>> multi = get_multi_jurisdiction_counties()
        >>> print(multi)
        ['loudoun']
    """
    return [
        name for name, config in SUPPORTED_COUNTIES.items()
        if config.has_incorporated_towns
    ]


# ===== EXPORTS =====

__all__ = [
    # Base config
    'CountyConfig',

    # County configs
    'ATHENS_CLARKE_CONFIG',
    'LOUDOUN_CONFIG',
    'SUPPORTED_COUNTIES',

    # Helper functions
    'get_county_config',
    'get_all_counties',
    'get_production_counties',
    'get_primary_county',
    'get_counties_with_feature',
    'can_validate_county',
    'get_county_display_name',
    'get_counties_by_state',
    'get_multi_jurisdiction_counties',

    # Direct accessors
    'get_athens_config',
    'get_loudoun_config',
]
