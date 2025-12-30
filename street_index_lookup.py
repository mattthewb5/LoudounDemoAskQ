#!/usr/bin/env python3
"""
Athens-Clarke County School District Lookup using Street Index
Much more accurate than geocoding + GIS boundaries!
"""

import re
import json
import os
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from address_normalization import standardize_address_format


@dataclass
class SchoolAssignment:
    """School assignment result"""
    elementary: str
    middle: str
    high: str
    street_matched: str
    parameters_matched: str = ""


def load_street_index(data_dir: str = "data") -> Dict[str, List[Tuple]]:
    """
    Load street index from JSON file

    Returns: {normalized_street_name: [(parameters, elementary, middle, high), ...]}
    """
    json_path = os.path.join(data_dir, "street_index.json")

    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Street index not found at {json_path}. "
            f"Please run extract_full_street_index.py first."
        )

    with open(json_path, 'r') as f:
        index_data = json.load(f)

    # Convert from JSON format to our tuple format
    street_index = {}
    for street_name, entries in index_data.items():
        street_index[street_name] = [tuple(entry) for entry in entries]

    return street_index


# Load the full street index from JSON
STREET_INDEX = load_street_index()


def normalize_street_name(street: str) -> str:
    """Normalize street name for lookup"""
    normalized = street.lower().strip()

    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Contract common street suffixes to match PDF format
    # The PDF uses abbreviations (AVE, ST, RD, etc.)
    replacements = {
        ' avenue$': ' ave',
        ' avenue ': ' ave ',
        ' street$': ' st',
        ' street ': ' st ',
        ' road$': ' rd',
        ' road ': ' rd ',
        ' drive$': ' dr',
        ' drive ': ' dr ',
        ' lane$': ' ln',
        ' lane ': ' ln ',
        ' court$': ' ct',
        ' court ': ' ct ',
        ' circle$': ' cir',
        ' circle ': ' cir ',
        ' boulevard$': ' blvd',
        ' boulevard ': ' blvd ',
    }

    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)

    return normalized.strip()


def extract_address_parts(address: str) -> Tuple[Optional[int], str]:
    """
    Extract house number and street name from address
    Returns: (house_number, street_name)
    """
    # Remove city, state, zip
    address = address.split(',')[0].strip()

    # Extract number and street
    match = re.match(r'(\d+)\s+(.+)', address)
    if match:
        number = int(match.group(1))
        street = match.group(2).strip()
        return (number, street)

    return (None, address)


def check_parameters(house_number: Optional[int], parameters: str) -> bool:
    """
    Check if a house number matches the parameters string

    Parameters can be things like:
    - "497 and below"
    - "624 and above"
    - "337 to 475, odd"
    - "even numbers only"
    - "" (empty = matches all)
    """
    if not parameters or house_number is None:
        return True

    params_lower = parameters.lower()

    # "X and below"
    match = re.search(r'(\d+)\s+and\s+below', params_lower)
    if match:
        threshold = int(match.group(1))
        return house_number <= threshold

    # "X and above"
    match = re.search(r'(\d+)\s+and\s+above', params_lower)
    if match:
        threshold = int(match.group(1))
        return house_number >= threshold

    # "X to Y"
    match = re.search(r'(\d+)\s+to\s+(\d+)', params_lower)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        in_range = low <= house_number <= high

        # Check for odd/even
        if 'odd' in params_lower:
            return in_range and (house_number % 2 == 1)
        elif 'even' in params_lower:
            return in_range and (house_number % 2 == 0)
        else:
            return in_range

    # "odd numbers only" or "odd only"
    if 'odd' in params_lower and 'even' not in params_lower:
        return house_number % 2 == 1

    # "even numbers only" or "even only"
    if 'even' in params_lower and 'odd' not in params_lower:
        return house_number % 2 == 0

    # Default: if we can't parse, return True
    return True


def lookup_school_district(address: str) -> Optional[SchoolAssignment]:
    """
    Look up school district for an address using the street index

    Args:
        address: Full address string (e.g., "150 Hancock Avenue, Athens, GA 30601")

    Returns:
        SchoolAssignment object or None if not found
    """
    # Normalize address format (e.g., "Hancock Ave W" -> "W Hancock Ave")
    address = standardize_address_format(address)

    # Parse the address
    house_number, street_name = extract_address_parts(address)
    normalized_street = normalize_street_name(street_name)

    print(f"Looking up: {address}")
    print(f"  Parsed: #{house_number} on '{normalized_street}'")

    # Look up in index
    if normalized_street in STREET_INDEX:
        entries = STREET_INDEX[normalized_street]
        print(f"  Found {len(entries)} possible matches")

        # Check each entry's parameters
        for params, elem, middle, high in entries:
            if check_parameters(house_number, params):
                print(f"  ✓ Matched parameters: '{params}'")
                return SchoolAssignment(
                    elementary=elem,
                    middle=middle,
                    high=high,
                    street_matched=normalized_street,
                    parameters_matched=params
                )

        # If no parameters matched, use first entry
        params, elem, middle, high = entries[0]
        print(f"  Using default entry")
        return SchoolAssignment(
            elementary=elem,
            middle=middle,
            high=high,
            street_matched=normalized_street,
            parameters_matched=params
        )

    print(f"  ✗ Street not found in index")
    return None


def print_assignment(address: str, assignment: Optional[SchoolAssignment]):
    """Pretty print school assignment"""
    print("\n" + "=" * 70)
    print(f"School Assignment for: {address}")
    print("=" * 70)

    if assignment:
        if assignment.parameters_matched:
            print(f"Matched: {assignment.street_matched} ({assignment.parameters_matched})")
        else:
            print(f"Matched: {assignment.street_matched}")
        print()
        print(f"Elementary School: {assignment.elementary}")
        print(f"Middle School:     {assignment.middle}")
        print(f"High School:       {assignment.high}")
    else:
        print("❌ Address not found in street index")
        print("\nThis could mean:")
        print("  - The street name wasn't recognized")
        print("  - The address is outside Athens-Clarke County")
        print("  - There's a typo in the street name")

    print("=" * 70)


def main():
    """Test the lookup with sample addresses"""
    print("Athens-Clarke County School District Lookup")
    print("Using Official Street Index")
    print()

    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601",
    ]

    for address in test_addresses:
        assignment = lookup_school_district(address)
        print_assignment(address, assignment)
        print()


if __name__ == "__main__":
    main()
