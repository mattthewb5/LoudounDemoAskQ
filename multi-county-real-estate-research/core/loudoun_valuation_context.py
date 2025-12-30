"""
Loudoun County Valuation Context Extractor

Extracts narrative-ready valuation context from the PropertyValuationOrchestrator
output for use in AI-generated property analysis narratives.

Usage:
    from core.loudoun_valuation_context import get_valuation_narrative_context

    # Assuming you have orchestrator output
    val_data = orchestrator.analyze_property(address, lat, lon, sqft)
    narrative_context = get_valuation_narrative_context(val_data)

    print(f"Estimate: {narrative_context['estimate_formatted']}")
    print(f"Position: {narrative_context['price_per_sqft']['position']}")
"""

from typing import Dict, Any, Optional, List


# Position values returned by orchestrator._assess_psf_position()
POSITION_VALUES = [
    "Insufficient data",
    "Significantly below market",
    "Below market",
    "At market",
    "Above market",
    "Significantly above market"
]

# Mapping position to narrative-friendly descriptors
POSITION_TO_NARRATIVE = {
    "Insufficient data": "unable to compare to neighborhood",
    "Significantly below market": "significantly below neighborhood average",
    "Below market": "below neighborhood average",
    "At market": "in line with the neighborhood",
    "Above market": "above neighborhood average",
    "Significantly above market": "significantly above neighborhood average"
}


def _get_confidence_level(score: float) -> str:
    """
    Convert numeric confidence score to level descriptor.

    Args:
        score: Confidence score from 0-10

    Returns:
        "high" (8-10), "medium" (6-7), or "lower" (<6)
    """
    if score >= 8:
        return "high"
    elif score >= 6:
        return "medium"
    else:
        return "lower"


def _get_confidence_descriptor(score: float, sources_count: int) -> str:
    """
    Generate a descriptive confidence statement.

    Args:
        score: Confidence score from 0-10
        sources_count: Number of data sources used

    Returns:
        Descriptive string explaining confidence level
    """
    level = _get_confidence_level(score)

    if level == "high":
        return f"high confidence - {sources_count} sources agree within 5%"
    elif level == "medium":
        return f"moderate confidence - sources show some variance"
    else:
        if sources_count == 1:
            return "lower confidence - single data source only"
        else:
            return "lower confidence - significant variance between sources"


def _get_value_descriptor(position: str) -> str:
    """
    Get narrative descriptor for property value relative to neighborhood.

    Args:
        position: Position string from orchestrator

    Returns:
        Narrative-friendly descriptor
    """
    return POSITION_TO_NARRATIVE.get(position, "relative to neighborhood unknown")


def _extract_sources(data_sources: List[str]) -> List[str]:
    """
    Normalize and extract source names for display.

    Args:
        data_sources: Raw source strings from orchestrator

    Returns:
        Clean source names
    """
    source_mapping = {
        "ATTOM Property Detail": "ATTOM",
        "ATTOM Comparable Sales": "Comparable Sales",
        "RentCast Estimates": "RentCast"
    }

    clean_sources = []
    for source in data_sources:
        clean_name = source_mapping.get(source, source)
        if clean_name not in clean_sources:
            clean_sources.append(clean_name)

    return clean_sources


def _count_same_subdivision_comps(comps: List[Dict], target_subdivision: Optional[str] = None) -> int:
    """
    Count comparables that are in the same subdivision as target.

    Note: Currently the orchestrator doesn't pass subdivision info through
    to the formatted comps, so this returns 0. Future enhancement would be
    to track subdivision in comparable_sales list.

    Args:
        comps: List of comparable sale dicts
        target_subdivision: Target property's subdivision name

    Returns:
        Count of comps in same subdivision
    """
    if not target_subdivision or not comps:
        return 0

    count = 0
    for comp in comps:
        comp_subdiv = comp.get('subdivision', '')
        if comp_subdiv and target_subdivision.upper() in comp_subdiv.upper():
            count += 1

    return count


def get_valuation_narrative_context(orchestrator_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts narrative-ready valuation context from orchestrator output.

    Args:
        orchestrator_result: Dictionary returned by PropertyValuationOrchestrator.analyze_property()

    Returns:
        Dictionary with extracted and computed narrative-ready context:
        {
            "estimate": 895000,
            "estimate_formatted": "$895,000",
            "confidence_score": 8.5,
            "confidence_level": "high",

            "price_per_sqft": {
                "property": 285.00,
                "neighborhood_avg": 280.00,
                "position": "At market",
                "difference_pct": 1.8
            },

            "comps_summary": {
                "count": 8,
                "median_price": 875000,
                "median_sqft": 3200,
                "same_subdivision": 0
            },

            "sources_used": ["ATTOM", "RentCast", "Comparable Sales"],

            "narrative_helpers": {
                "value_descriptor": "in line with the neighborhood",
                "confidence_descriptor": "high confidence - 3 sources agree within 5%"
            }
        }
    """
    result = {
        "estimate": 0,
        "estimate_formatted": "N/A",
        "confidence_score": 0.0,
        "confidence_level": "lower",
        "price_per_sqft": {
            "property": 0.0,
            "neighborhood_avg": 0.0,
            "position": "Insufficient data",
            "difference_pct": 0.0
        },
        "comps_summary": {
            "count": 0,
            "median_price": 0,
            "median_sqft": 0,
            "same_subdivision": 0
        },
        "sources_used": [],
        "narrative_helpers": {
            "value_descriptor": "unable to compare to neighborhood",
            "confidence_descriptor": "insufficient data for confidence assessment"
        }
    }

    if not orchestrator_result:
        return result

    # Extract current value estimate
    current_value = orchestrator_result.get('current_value', {})
    estimate = current_value.get('triangulated_estimate', 0)
    confidence_score = current_value.get('confidence_score', 0.0)

    result['estimate'] = estimate
    result['estimate_formatted'] = f"${estimate:,.0f}" if estimate else "N/A"
    result['confidence_score'] = confidence_score
    result['confidence_level'] = _get_confidence_level(confidence_score)

    # Extract price per sqft data
    psf_data = orchestrator_result.get('price_per_sqft', {})
    property_psf = psf_data.get('property', 0.0)
    neighborhood_avg = psf_data.get('neighborhood_avg', 0.0)
    position = psf_data.get('position', 'Insufficient data')

    # Calculate difference percentage
    difference_pct = 0.0
    if neighborhood_avg > 0:
        difference_pct = round(((property_psf - neighborhood_avg) / neighborhood_avg) * 100, 1)

    result['price_per_sqft'] = {
        "property": property_psf,
        "neighborhood_avg": neighborhood_avg,
        "position": position,
        "difference_pct": difference_pct
    }

    # Extract comparable sales summary
    comps = orchestrator_result.get('comparable_sales', [])
    if comps:
        prices = [c.get('sale_price', 0) for c in comps if c.get('sale_price', 0) > 0]
        sqfts = [c.get('sqft', 0) for c in comps if c.get('sqft', 0) > 0]

        # Calculate medians
        if prices:
            prices_sorted = sorted(prices)
            mid = len(prices_sorted) // 2
            median_price = prices_sorted[mid] if len(prices_sorted) % 2 else (prices_sorted[mid-1] + prices_sorted[mid]) // 2
        else:
            median_price = 0

        if sqfts:
            sqfts_sorted = sorted(sqfts)
            mid = len(sqfts_sorted) // 2
            median_sqft = sqfts_sorted[mid] if len(sqfts_sorted) % 2 else (sqfts_sorted[mid-1] + sqfts_sorted[mid]) // 2
        else:
            median_sqft = 0

        result['comps_summary'] = {
            "count": len(comps),
            "median_price": median_price,
            "median_sqft": median_sqft,
            "same_subdivision": _count_same_subdivision_comps(comps)
        }

    # Extract and clean data sources
    data_sources = orchestrator_result.get('data_sources', [])
    result['sources_used'] = _extract_sources(data_sources)

    # Generate narrative helpers
    result['narrative_helpers'] = {
        "value_descriptor": _get_value_descriptor(position),
        "confidence_descriptor": _get_confidence_descriptor(confidence_score, len(result['sources_used']))
    }

    return result


def format_valuation_narrative_sentence(context: Dict[str, Any]) -> str:
    """
    Generate a one-sentence narrative about property valuation.

    Example outputs:
    - "Estimated at $895,000 (high confidence), in line with the neighborhood at $285/sqft."
    - "Estimated at $750,000 (moderate confidence), below neighborhood average at $220/sqft vs $250/sqft area average."

    Args:
        context: Output from get_valuation_narrative_context()

    Returns:
        Narrative sentence
    """
    estimate = context.get('estimate_formatted', 'N/A')
    confidence = context.get('confidence_level', 'lower')

    psf = context.get('price_per_sqft', {})
    property_psf = psf.get('property', 0)
    neighborhood_avg = psf.get('neighborhood_avg', 0)
    position = psf.get('position', 'Insufficient data')
    diff_pct = psf.get('difference_pct', 0)

    value_desc = context.get('narrative_helpers', {}).get('value_descriptor', '')

    # Build narrative based on position
    if position == "At market":
        psf_phrase = f"in line with the neighborhood at ${property_psf:.0f}/sqft"
    elif position == "Insufficient data":
        psf_phrase = ""
    else:
        psf_phrase = f"{value_desc} at ${property_psf:.0f}/sqft vs ${neighborhood_avg:.0f}/sqft area average"

    if psf_phrase:
        return f"Estimated at {estimate} ({confidence} confidence), {psf_phrase}."
    else:
        return f"Estimated at {estimate} ({confidence} confidence)."


# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_valuation_context():
    """Test the valuation context extraction with mock data."""
    print("=" * 70)
    print("VALUATION CONTEXT EXTRACTOR TEST")
    print("=" * 70)

    # Mock orchestrator output (based on actual structure)
    mock_result = {
        'current_value': {
            'attom_estimate': 875000,
            'rentcast_estimate': 910000,
            'triangulated_estimate': 895000,
            'confidence_score': 8.2,
            'methodology': 'Triangulated valuation using ATTOM market value, RentCast AVM and comparable sales analysis'
        },
        'comparable_sales': [
            {'address': '123 Test St', 'sale_price': 850000, 'sqft': 3200, 'price_per_sqft': 265.63},
            {'address': '125 Test St', 'sale_price': 875000, 'sqft': 3100, 'price_per_sqft': 282.26},
            {'address': '127 Test St', 'sale_price': 920000, 'sqft': 3400, 'price_per_sqft': 270.59},
            {'address': '129 Test St', 'sale_price': 890000, 'sqft': 3250, 'price_per_sqft': 273.85},
        ],
        'price_per_sqft': {
            'property': 285.00,
            'neighborhood_avg': 273.08,
            'comps': [265.63, 282.26, 270.59, 273.85],
            'position': 'At market'
        },
        'data_sources': ['ATTOM Property Detail', 'ATTOM Comparable Sales', 'RentCast Estimates']
    }

    print("\n--- Mock Input ---")
    print(f"Triangulated Estimate: ${mock_result['current_value']['triangulated_estimate']:,}")
    print(f"Confidence Score: {mock_result['current_value']['confidence_score']}")
    print(f"Property $/sqft: ${mock_result['price_per_sqft']['property']}")
    print(f"Neighborhood avg: ${mock_result['price_per_sqft']['neighborhood_avg']}")
    print(f"Position: {mock_result['price_per_sqft']['position']}")

    # Extract context
    context = get_valuation_narrative_context(mock_result)

    print("\n--- Extracted Context ---")
    print(f"Estimate: {context['estimate_formatted']}")
    print(f"Confidence: {context['confidence_score']} ({context['confidence_level']})")
    print(f"Property $/sqft: ${context['price_per_sqft']['property']:.2f}")
    print(f"Neighborhood avg: ${context['price_per_sqft']['neighborhood_avg']:.2f}")
    print(f"Position: {context['price_per_sqft']['position']}")
    print(f"Difference: {context['price_per_sqft']['difference_pct']:+.1f}%")
    print(f"Comps count: {context['comps_summary']['count']}")
    print(f"Median price: ${context['comps_summary']['median_price']:,}")
    print(f"Sources: {', '.join(context['sources_used'])}")
    print(f"Value descriptor: \"{context['narrative_helpers']['value_descriptor']}\"")
    print(f"Confidence descriptor: \"{context['narrative_helpers']['confidence_descriptor']}\"")

    # Generate narrative
    narrative = format_valuation_narrative_sentence(context)
    print(f"\n--- Generated Narrative ---")
    print(f"\"{narrative}\"")

    # Test with different positions
    print("\n" + "=" * 70)
    print("POSITION VALUE TESTS")
    print("=" * 70)

    test_positions = [
        ("Significantly below market", 200.00, 280.00),
        ("Below market", 250.00, 280.00),
        ("At market", 280.00, 280.00),
        ("Above market", 310.00, 280.00),
        ("Significantly above market", 350.00, 280.00),
    ]

    for position, prop_psf, avg_psf in test_positions:
        test_result = {
            'current_value': {'triangulated_estimate': 800000, 'confidence_score': 7.5},
            'price_per_sqft': {
                'property': prop_psf,
                'neighborhood_avg': avg_psf,
                'position': position
            },
            'comparable_sales': [],
            'data_sources': ['ATTOM Property Detail']
        }
        ctx = get_valuation_narrative_context(test_result)
        narrative = format_valuation_narrative_sentence(ctx)
        print(f"\n{position}:")
        print(f"  {narrative}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_valuation_context()
