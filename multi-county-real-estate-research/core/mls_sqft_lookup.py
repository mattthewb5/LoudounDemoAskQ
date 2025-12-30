#!/usr/bin/env python3
"""
MLS Square Footage Lookup via Web Search

Uses web search to find property listing square footage from MLS-based sites
like Redfin, Zillow, Realtor.com which include finished basements.

This is the PRIMARY source for square footage since it matches what consumers
see when searching for properties.
"""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class SqftSource:
    """Square footage from a single source."""
    source: str
    sqft: int
    tier: int  # 1 = most trusted (Redfin/Zillow), 2 = trusted, 3 = ignore


# Source categorization
TIER_1_SOURCES = {
    'redfin': 'Redfin',
    'zillow': 'Zillow',
    'realtor.com': 'Realtor.com',
    'realtor': 'Realtor.com'
}

TIER_2_SOURCES = {
    'coldwellbanker': 'Coldwell Banker',
    'coldwell banker': 'Coldwell Banker',
    'rockethomes': 'RocketHomes',
    'longandfoster': 'Long & Foster',
    'long & foster': 'Long & Foster',
    'remax': 'RE/MAX',
    're/max': 'RE/MAX',
    'trulia': 'Trulia',
    'homesnap': 'Homesnap',
    'compass': 'Compass'
}

# Sites to ignore (tax assessor based, not MLS)
IGNORE_SOURCES = {
    'xome', 'homes.com', 'propertyshark', 'property shark',
    'publicrecords', 'public records', 'county', 'assessor'
}


def extract_sqft_from_text(text: str) -> Optional[int]:
    """
    Extract square footage from text using regex patterns.

    Args:
        text: Text to search for square footage

    Returns:
        Square footage as integer, or None if not found
    """
    # Patterns to match square footage
    patterns = [
        r'(\d{1,2}[,\s]?\d{3})\s*square\s*foot',
        r'(\d{1,2}[,\s]?\d{3})\s*square\s*feet',
        r'(\d{1,2}[,\s]?\d{3})\s*sq\.?\s*ft',
        r'(\d{1,2}[,\s]?\d{3})\s*sqft',
        r'(\d{1,2}[,\s]?\d{3})\s*sf\b',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Extract number and remove commas/spaces
            sqft_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                sqft = int(sqft_str)
                # Sanity check: residential properties typically 500-50000 sqft
                if 500 <= sqft <= 50000:
                    return sqft
            except ValueError:
                continue

    return None


def categorize_source(url: str, title: str) -> tuple[Optional[str], int]:
    """
    Categorize a search result source.

    Args:
        url: URL of the search result
        title: Title of the search result

    Returns:
        (source_name, tier) where tier is 1 (best), 2 (good), or 3 (ignore)
    """
    text = (url + ' ' + title).lower()

    # Check if we should ignore this source
    for ignore_term in IGNORE_SOURCES:
        if ignore_term in text:
            return None, 3

    # Check Tier 1 sources
    for key, name in TIER_1_SOURCES.items():
        if key in text:
            return name, 1

    # Check Tier 2 sources
    for key, name in TIER_2_SOURCES.items():
        if key in text:
            return name, 2

    # Unknown source - treat as Tier 2 if it looks like a real estate site
    real_estate_terms = ['homes', 'property', 'real estate', 'realty', 'listings']
    if any(term in text for term in real_estate_terms):
        # Extract domain for display
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            return domain, 2

    return None, 3


def parse_mls_sqft_from_search(search_results) -> Dict:
    """
    Parse search results for property square footage from MLS sources.

    Args:
        search_results: Search results string or dict from WebSearch tool

    Returns:
        {
            "mls_sqft": int or None,
            "sqft_sources": [{"source": "Redfin", "sqft": 7371, "tier": 1}, ...],
            "confidence": "high" | "medium" | "low" | "none",
            "method": "web_search"
        }
    """
    result = {
        "mls_sqft": None,
        "sqft_sources": [],
        "confidence": "none",
        "method": "web_search"
    }

    try:
        # Parse search results for square footage
        sqft_findings: List[SqftSource] = []

        # Handle string output from WebSearch tool (markdown format)
        if isinstance(search_results, str):
            # Parse markdown-style search results
            # Format: "text from result [Title](URL) more text"
            # Extract URLs and surrounding text
            url_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.finditer(url_pattern, search_results)

            for match in matches:
                title = match.group(1)
                url = match.group(2)

                # Get context around the link (snippet)
                start = max(0, match.start() - 200)
                end = min(len(search_results), match.end() + 200)
                snippet = search_results[start:end]

                source_name, tier = categorize_source(url, title)
                if tier == 3 or source_name is None:
                    continue

                sqft = extract_sqft_from_text(snippet)
                if sqft:
                    sqft_findings.append(SqftSource(
                        source=source_name,
                        sqft=sqft,
                        tier=tier
                    ))

        # Handle dict/list format (if available)
        elif isinstance(search_results, dict) and 'results' in search_results:
            results_list = search_results['results']
        elif isinstance(search_results, list):
            results_list = search_results
        else:
            results_list = []

        if isinstance(search_results, (dict, list)) and not isinstance(search_results, str):
            for item in results_list[:10]:  # Check top 10 results
                if isinstance(item, dict):
                    url = item.get('url', '')
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                else:
                    continue

                # Categorize the source
                source_name, tier = categorize_source(url, title)

                # Skip if we should ignore this source
                if tier == 3 or source_name is None:
                    continue

                # Try to extract sqft from title and snippet
                combined_text = f"{title} {snippet}"
                sqft = extract_sqft_from_text(combined_text)

                if sqft:
                    sqft_findings.append(SqftSource(
                        source=source_name,
                        sqft=sqft,
                        tier=tier
                    ))

        # Store all findings
        result["sqft_sources"] = [
            {"source": f.source, "sqft": f.sqft, "tier": f.tier}
            for f in sqft_findings
        ]

        if not sqft_findings:
            result["confidence"] = "none"
            return result

        # Determine consensus sqft and confidence
        # Group by sqft value
        sqft_counts = {}
        for finding in sqft_findings:
            sqft_counts[finding.sqft] = sqft_counts.get(finding.sqft, []) + [finding]

        # Find most common sqft value
        if sqft_counts:
            # Sort by: number of occurrences, then by highest tier
            most_common_sqft = max(
                sqft_counts.keys(),
                key=lambda s: (len(sqft_counts[s]),
                              sum(1.0/f.tier for f in sqft_counts[s]))
            )

            supporting_sources = sqft_counts[most_common_sqft]
            tier_1_count = sum(1 for s in supporting_sources if s.tier == 1)
            total_count = len(supporting_sources)

            # Set confidence based on agreement
            if tier_1_count >= 2 or total_count >= 3:
                result["confidence"] = "high"
            elif tier_1_count >= 1 or total_count >= 2:
                result["confidence"] = "medium"
            elif total_count >= 1:
                result["confidence"] = "low"
            else:
                result["confidence"] = "none"

            result["mls_sqft"] = most_common_sqft

    except Exception as e:
        print(f"  ⚠️  Error searching for MLS sqft: {e}")
        result["confidence"] = "none"

    return result


def format_sqft_sources(sources: List[Dict]) -> str:
    """Format source list for display."""
    if not sources:
        return "No sources"

    # Group by tier
    tier_1 = [s['source'] for s in sources if s['tier'] == 1]
    tier_2 = [s['source'] for s in sources if s['tier'] == 2]

    parts = []
    if tier_1:
        parts.append(', '.join(tier_1))
    if tier_2:
        parts.append(', '.join(tier_2))

    return ' | '.join(parts) if parts else sources[0]['source']


if __name__ == "__main__":
    # Test with a sample address
    print("MLS Square Footage Lookup Module")
    print("=" * 60)
    print("\nThis module searches web results for property square footage")
    print("from MLS-based sources (Redfin, Zillow, etc.)")
    print("\nUse from main.py - this is a library module.")
