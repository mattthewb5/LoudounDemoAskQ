#!/usr/bin/env python3
"""
Extract the complete street index from the PDF and save to JSON
"""

import fitz  # PyMuPDF
import re
import json
from typing import List, Dict


def is_street_name(line: str) -> bool:
    """Check if a line looks like a street name"""
    if not line:
        return False

    # Street names are usually all caps
    if line != line.upper():
        return False

    # Common street suffixes
    suffixes = ['ST', 'AVE', 'RD', 'DR', 'LN', 'CT', 'CIR', 'WAY', 'PL', 'BLVD',
                'TRL', 'PKWY', 'HWY', 'LOOP', 'PATH', 'ROW', 'SQ', 'TER', 'WALK']

    # Check if ends with a street suffix
    for suffix in suffixes:
        if line.endswith(' ' + suffix) or line.endswith(suffix):
            return True

    # Some streets might not have suffixes (like "LOOP")
    # Check if it's all caps and doesn't contain school names
    school_keywords = ['ELEMENTARY', 'MIDDLE', 'HIGH', 'SCHOOL', 'CLARKE', 'CEDAR', 'SHOALS']
    if not any(keyword in line for keyword in school_keywords):
        return True

    return False


def is_parameter_line(line: str) -> bool:
    """Check if a line looks like a parameter (address range, odd/even, etc.)"""
    if not line:
        return False

    line_lower = line.lower()

    # Check for common parameter patterns
    patterns = [
        r'\d+\s+and\s+(below|above)',  # "497 and below"
        r'\d+\s+to\s+\d+',  # "100 to 200"
        r'(odd|even)\s+(numbers|only)',  # "odd numbers only"
        r'zip\s+code',  # "Zip Code 30606"
        r'\d{5}',  # Zip codes
    ]

    for pattern in patterns:
        if re.search(pattern, line_lower):
            return True

    return False


def extract_street_index(pdf_path: str) -> List[Dict]:
    """
    Extract all streets from the PDF street index

    Returns list of dicts with: street, parameters, elementary, middle, high
    """
    streets = []

    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"Processing page {page_num + 1}/{len(doc)}...")

        # Extract text from page
        text = page.get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # Skip header/preamble lines
        i = 0
        while i < len(lines):
            if lines[i] in ['Street', 'Parameters', 'Elementary Zone', 'Middle Zone', 'High Zone']:
                i += 1
                continue

            # Skip preamble
            if 'students are placed' in lines[i].lower():
                i += 1
                continue

            # Look for street entries
            if is_street_name(lines[i]):
                street = lines[i]
                i += 1

                # Check if next line is a parameter
                parameters = ""
                if i < len(lines) and is_parameter_line(lines[i]):
                    parameters = lines[i]
                    i += 1

                # Next 3 lines should be elementary, middle, high
                if i + 2 < len(lines):
                    elementary = lines[i] if i < len(lines) else ""
                    middle = lines[i + 1] if i + 1 < len(lines) else ""
                    high = lines[i + 2] if i + 2 < len(lines) else ""

                    streets.append({
                        'street': street,
                        'parameters': parameters,
                        'elementary': elementary,
                        'middle': middle,
                        'high': high
                    })

                    i += 3
                else:
                    i += 1
            else:
                i += 1

    doc.close()

    print(f"\nExtracted {len(streets)} street entries from PDF")

    return streets


def normalize_street_name(street: str) -> str:
    """Normalize street name for indexing"""
    normalized = street.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def build_lookup_index(streets: List[Dict]) -> Dict:
    """
    Build a lookup index grouped by normalized street name

    Returns: {normalized_street: [(params, elem, middle, high), ...]}
    """
    index = {}

    for entry in streets:
        normalized = normalize_street_name(entry['street'])

        if normalized not in index:
            index[normalized] = []

        index[normalized].append((
            entry['parameters'],
            entry['elementary'],
            entry['middle'],
            entry['high']
        ))

    return index


def main():
    """Extract data from PDF and save to JSON"""
    pdf_path = "data/street_index.pdf"
    output_json = "data/street_index.json"

    print("=" * 70)
    print("Athens-Clarke County Street Index Extractor")
    print("=" * 70)
    print()

    try:
        # Extract data from PDF
        print(f"Reading PDF: {pdf_path}")
        streets = extract_street_index(pdf_path)
        print(f"✓ Extracted {len(streets)} street entries")
        print()

        # Build lookup index
        print("Building lookup index...")
        index = build_lookup_index(streets)
        print(f"✓ Created index with {len(index)} unique streets")
        print()

        # Save to JSON
        print(f"Saving to: {output_json}")
        with open(output_json, 'w') as f:
            json.dump(index, f, indent=2)
        print("✓ Data saved successfully")
        print()

        # Show some statistics
        print("Statistics:")
        print(f"  Total street entries: {len(streets)}")
        print(f"  Unique street names: {len(index)}")

        # Show sample
        print()
        print("Sample entries:")
        for street_name in list(index.keys())[:5]:
            entries = index[street_name]
            print(f"  {street_name}: {len(entries)} assignment(s)")

    except FileNotFoundError:
        print(f"✗ Error: Could not find {pdf_path}")
        print()
        print("Please ensure the street index PDF is in the data/ directory")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
