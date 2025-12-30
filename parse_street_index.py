#!/usr/bin/env python3
"""
Parse the Athens-Clarke County Street Index PDF and create a structured lookup database
"""

import re
import csv
import json
from typing import List, Dict, Optional

def parse_street_index_text(pdf_text: str) -> List[Dict]:
    """
    Parse the street index from PDF text into structured data

    Returns a list of dicts with keys: street, parameters, elementary, middle, high
    """
    streets = []

    # The PDF has been read - text is in the document
    # For now, I'll manually create the data structure from the visible content
    # In production, you'd use pdfplumber or PyPDF2 to extract this

    sample_streets = [
        {"street": "HANCOCK AVENUE", "parameters": "497 and below", "elementary": "Barrow", "middle": "Clarke Middle", "high": "Clarke Central"},
        {"street": "HANCOCK AVENUE", "parameters": "624 and above", "elementary": "Johnnie L. Burks", "middle": "Clarke Middle", "high": "Clarke Central"},
        {"street": "REESE STREET", "parameters": "337 and above", "elementary": "Johnnie L. Burks", "middle": "Clarke Middle", "high": "Clarke Central"},
        {"street": "HOYT STREET", "parameters": "", "elementary": "Barrow", "middle": "Clarke Middle", "high": "Clarke Central"},
    ]

    return sample_streets


def normalize_street_name(street: str) -> str:
    """Normalize street name for matching"""
    # Remove common suffixes and convert to lowercase
    normalized = street.lower().strip()

    # Standardize abbreviations
    replacements = {
        ' st': ' street',
        ' ave': ' avenue',
        ' rd': ' road',
        ' dr': ' drive',
        ' ln': ' lane',
        ' ct': ' court',
        ' cir': ' circle',
        ' blvd': ' boulevard',
        ' pkwy': ' parkway',
        ' pl': ' place',
    }

    for abbrev, full in replacements.items():
        if normalized.endswith(abbrev):
            normalized = normalized[:-len(abbrev)] + full

    return normalized


def extract_address_number(address: str) -> Optional[int]:
    """Extract house number from address"""
    match = re.match(r'(\d+)', address.strip())
    if match:
        return int(match.group(1))
    return None


def parse_address(address: str) -> tuple:
    """
    Parse an address into components
    Returns: (number, street_name, city, state, zip)
    """
    # Simple parser - in production use a library like usaddress
    parts = address.split(',')

    if len(parts) >= 1:
        # Get street part
        street_part = parts[0].strip()
        match = re.match(r'(\d+)\s+(.+)', street_part)
        if match:
            number = int(match.group(1))
            street = match.group(2).strip()
            return (number, street, None, None, None)

    return (None, address, None, None, None)


if __name__ == "__main__":
    print("Street Index Parser")
    print("=" * 70)

    # In production, extract from PDF
    # For now, demonstrate with sample data
    streets = parse_street_index_text("")

    print(f"Parsed {len(streets)} street records (sample)")
    print()

    for street in streets:
        print(f"{street['street']:<30} {street['parameters']:<25} -> {street['elementary']}")
