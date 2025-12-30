#!/usr/bin/env python3
"""
Address normalization utilities
Shared by both crime lookup and school lookup systems
"""

import re


def normalize_directional(address: str) -> str:
    """
    Normalize directional suffix to prefix format

    Handles common variations like:
    - "1398 Hancock Avenue W" -> "1398 W Hancock Avenue" (suffix to prefix)
    - "123 Main Street E" -> "123 E Main Street"
    - Already prefix format passes through unchanged

    Args:
        address: Original address string

    Returns:
        Normalized address string with directional as prefix
    """
    # Work with a copy
    normalized = address.strip()

    # Pattern to match directional suffix (e.g., "Street Name W" or "Avenue Name North")
    # Captures: number, street name, street type, directional suffix, rest
    suffix_pattern = r'^(\d+)\s+(.+?)\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl)\s+(W|E|N|S|West|East|North|South|NW|NE|SW|SE|Northwest|Northeast|Southwest|Southeast)(\s*,?\s*.*)$'

    match = re.match(suffix_pattern, normalized, re.IGNORECASE)

    if match:
        number = match.group(1)
        street_name = match.group(2)
        street_type = match.group(3)
        direction = match.group(4)
        rest = match.group(5)  # City, state, zip

        # Reconstruct as: number + direction + street_name + street_type + rest
        normalized = f"{number} {direction} {street_name} {street_type}{rest}"
        print(f"🔧 Normalized directional: '{address}' -> '{normalized}'")

    return normalized


def standardize_address_format(address: str) -> str:
    """
    Apply all address normalization rules

    This is the main function that should be called by both
    crime lookup and school lookup systems.

    Args:
        address: Raw address string from user

    Returns:
        Normalized address string
    """
    # Apply directional normalization (suffix -> prefix)
    normalized = normalize_directional(address)

    # Additional normalizations can be added here
    # - Case normalization
    # - Extra whitespace removal
    # - etc.

    return normalized.strip()
