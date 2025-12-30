#!/usr/bin/env python3
"""
Extract address from natural language queries
"""

import re
from typing import Optional, Tuple


def extract_address_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract address and question from a natural language query

    Examples:
        "Is 150 Hancock Ave a good area for families?"
        -> address: "150 Hancock Ave", question: "Is this a good area for families?"

        "What are the schools like at 1398 W Hancock Avenue, Athens, GA 30606?"
        -> address: "1398 W Hancock Avenue, Athens, GA 30606", question: "What are the schools like?"

    Args:
        query: User's natural language input

    Returns:
        Tuple of (address, question) or (None, None) if no address found
    """
    if not query or not query.strip():
        return (None, None)

    query = query.strip()

    # Common patterns for addresses in Athens
    # Pattern 1: Number + Street Name + optional suffix + optional city/state/zip
    # e.g., "150 Hancock Ave", "1398 W Hancock Avenue, Athens, GA 30606"
    # Using non-greedy matching and word boundaries to prevent over-capturing
    address_patterns = [
        # Full address with city, state, zip - limit street name to 1-5 words
        r'(\d+\s+(?:[NSEW]\s+)?(?:[A-Z][a-z]+\s+){0,4}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl|Parkway|Pkwy)(?:\s+[NSEW])?\s*,?\s*(?:Athens|athens)\s*,?\s*(?:GA|Georgia|ga)\s*\d{5})',

        # Address with city but no zip - limit street name to 1-5 words
        r'(\d+\s+(?:[NSEW]\s+)?(?:[A-Z][a-z]+\s+){0,4}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl|Parkway|Pkwy)(?:\s+[NSEW])?\s*,?\s*(?:Athens|athens))',

        # Just street address with clear word boundary after suffix - limit to 1-5 words
        r'(\d+\s+(?:[NSEW]\s+)?(?:[A-Z][a-z]+\s+){0,4}(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Place|Pl|Parkway|Pkwy)(?:\s+[NSEW])?)(?:\s*,|\s+(?:Athens|in|is|a|the|for|with)|$)',

        # Simpler case-insensitive pattern with word limit (1-5 words for street name)
        r'(\d+\s+(?:[NSEW]\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}\s+(?:Avenue|Ave|Street|St|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Boulevard|Blvd|Parkway|Pkwy))(?:\s*,|\s+(?:Athens|in|is|a|the|for|with)|$)',

        # Case-insensitive fallback: number + 1-5 words + street suffix + word boundary
        # This will match even if user types in lowercase
        r'(\d+\s+(?:[NSEW]\s+)?(?:\w+\s+){0,4}\w+\s+(?:Avenue|Ave|Street|St|Road|Rd|Drive|Dr|Lane|Ln|Way|Court|Ct|Boulevard|Blvd|Parkway|Pkwy|Circle|Cir|Place|Pl))(?=\s*(?:,|\s+(?:Athens|in|is|a|the|for|with|good|bad|safe)|$))',
    ]

    extracted_address = None

    for pattern in address_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            extracted_address = match.group(1).strip()
            # Clean up the address
            extracted_address = re.sub(r'\s+', ' ', extracted_address)  # Remove extra spaces

            # Title case the street name for consistency
            parts = extracted_address.split()
            if len(parts) >= 2:
                # Capitalize each word except directional indicators in the middle
                formatted_parts = []
                for i, part in enumerate(parts):
                    if i == 0:  # Keep number as is
                        formatted_parts.append(part)
                    elif part.upper() in ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW']:
                        formatted_parts.append(part.upper())
                    elif part.lower() in ['avenue', 'ave', 'street', 'st', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 'way', 'court', 'ct', 'boulevard', 'blvd', 'parkway', 'pkwy', 'circle', 'cir', 'place', 'pl']:
                        # Keep street suffix capitalized properly
                        formatted_parts.append(part.capitalize())
                    else:
                        formatted_parts.append(part.capitalize())
                extracted_address = ' '.join(formatted_parts)

            break

    if not extracted_address:
        return (None, None)

    # Extract the question by removing the address (case-insensitive)
    # Find the address in the original query (might have different casing)
    address_pattern = re.escape(extracted_address)
    # Create a case-insensitive pattern
    question = re.sub(address_pattern, 'this address', query, count=1, flags=re.IGNORECASE).strip()

    # Clean up question
    question = re.sub(r'^[,\.\?!\s\-]+', '', question)  # Remove leading punctuation
    question = re.sub(r'[,\.\?!\s]+$', '', question)  # Remove trailing punctuation

    # Clean up common artifacts and phrases
    question = re.sub(r'\s+at\s+this address\b', ' at this address', question, flags=re.IGNORECASE)
    question = re.sub(r'\bat\s+this address\b', 'for this address', question, flags=re.IGNORECASE)
    question = re.sub(r'\bfor\s+this address\b', 'for this address', question, flags=re.IGNORECASE)

    # Remove common prefixes that don't make sense without the address
    question = re.sub(r'^(?:is|was|are|were|will|would|can|could|does|do)\s+this address\b', 'Is this address', question, flags=re.IGNORECASE)

    # If question is just "this address" or similar, provide better default
    if re.match(r'^this address[\s,\.\?!]*$', question, re.IGNORECASE):
        question = "Tell me about this area"

    # If question is empty or too short, provide default
    if not question or len(question) < 5:
        question = "Tell me about this area"

    # Ensure question ends with ?
    if not question.endswith('?'):
        question += '?'

    return (extracted_address, question)


def test_extraction():
    """Test the extraction function"""
    test_cases = [
        "Is 150 Hancock Ave a good area for families?",
        "What are the schools like at 1398 W Hancock Avenue, Athens, GA 30606?",
        "How safe is 220 College Station Road",
        "1000 Jennings Mill Road - is this good for kids?",
        "Tell me about crime at 585 Reese Street, Athens, GA",
        "150 Hancock Avenue Athens GA 30601",
        "Is 1398 Hancock Avenue W, Athens, GA 30606 a good neighborhood?",
    ]

    print("=" * 80)
    print("ADDRESS EXTRACTION TEST")
    print("=" * 80)
    print()

    for test in test_cases:
        address, question = extract_address_from_query(test)
        print(f"Input:    {test}")
        print(f"Address:  {address}")
        print(f"Question: {question}")
        print("-" * 80)
        print()


if __name__ == "__main__":
    test_extraction()
