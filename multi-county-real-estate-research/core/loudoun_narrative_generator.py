"""
Loudoun County AI Property Narrative Generator

Compiles structured property data from multiple analyzers and generates
AI-powered narrative summaries using Claude API.

Usage:
    from core.loudoun_narrative_generator import (
        compile_narrative_data,
        generate_property_narrative
    )

    # Compile all analysis data
    data = compile_narrative_data(
        address="43422 Cloister Pl, Leesburg, VA 20176",
        coords=(39.0892, -77.5034),
        sqft=3200,
        schools_info={"elementary": "Seldens Landing ES", ...}
    )

    # Generate narrative
    narrative = generate_property_narrative(data)
    print(narrative['sections']['what_stands_out'])
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import core analyzers
from core.loudoun_metro_analysis import analyze_metro_access
from core.location_quality_analyzer import LocationQualityAnalyzer, get_cached_location_analyzer
from core.loudoun_places_analysis import analyze_neighborhood
from core.loudoun_school_percentiles import get_school_context
from core.loudoun_valuation_context import (
    get_valuation_narrative_context,
    format_valuation_narrative_sentence
)
from core.api_config import get_api_key


# ============================================================================
# CONSTANTS
# ============================================================================

CACHE_DIR = Path(__file__).parent.parent / 'cache' / 'narratives'
CACHE_TTL_HOURS = 24  # Cache narratives for 24 hours

# The narrative system prompt for Claude
NARRATIVE_SYSTEM_PROMPT = """You are a local real estate expert writing property analysis for Loudoun County, Virginia.

Your role: Generate concise, insight-dense narratives that help buyers and sellers understand a property's true value and livability. Focus on LOCAL CONTEXT that generic tools miss.

TONE:
- Direct and factual, like a trusted advisor
- Highlight genuinely notable features (don't oversell average properties)
- Acknowledge trade-offs honestly
- Use specific data points, not vague descriptions

OUTPUT FORMAT:
Return ONLY a JSON object with these 6 sections (each 2-4 sentences):

{
  "what_stands_out": "Opening hook - the 1-2 most distinctive features",
  "schools_reality": "School assignment context with percentile rankings",
  "daily_reality": "Commute, traffic patterns, and neighborhood convenience",
  "worth_knowing": "Important context that might not be obvious",
  "investment_lens": "Development activity at BOTH radii, market position, growth indicators",
  "bottom_line": "Synthesis - who this property is ideal for"
}

RULES:
1. Every claim must be grounded in the provided data
2. If data is missing for a section, acknowledge it briefly and focus on what IS available
3. Use specific numbers (e.g., "0.4 miles to Silver Line" not "close to Metro")
4. Compare to Loudoun County context (e.g., "top 15% of county schools")
5. Mention traffic volumes and road classifications when relevant
6. For investment_lens: Reference BOTH development radii when available:
   - 2-mile radius = immediate neighborhood activity
   - 5-mile radius = regional context (captures Data Center Alley, the world's largest data center market with $1.5B+ construction)
7. Be honest about weaknesses - buyers respect candor
8. NO generic real estate fluff or superlatives without data backing

DEMOGRAPHICS INTEGRATION:
When demographics data is provided, weave insights naturally throughout sections (NOT as a separate topic):
- In what_stands_out: Mention affluence level if notably high/low (e.g., "This affluent area with median income of $163K...")
- In daily_reality: Reference workforce characteristics if relevant (e.g., "The highly educated workforce (68% bachelor's+) supports...")
- In investment_lens: Connect demographics to investment thesis (e.g., "Strong income levels ($143K median) and low unemployment (2.8%) indicate economic stability...")
- In bottom_line: Factor demographics into buyer profile

IMPORTANT: Do NOT correlate demographics with school performance. Keep school analysis based solely on SOL/performance data."""


# ============================================================================
# CACHE UTILITIES
# ============================================================================

def _get_cache_key(address: str, data_hash: str) -> str:
    """Generate cache key from address and data hash."""
    normalized_address = address.lower().strip().replace(' ', '_').replace(',', '')
    return f"{normalized_address}_{data_hash[:12]}"


def _compute_data_hash(compiled_data: Dict[str, Any]) -> str:
    """Compute hash of compiled data to detect changes."""
    # Convert to JSON string for consistent hashing
    data_str = json.dumps(compiled_data, sort_keys=True, default=str)
    return hashlib.md5(data_str.encode()).hexdigest()


def _get_cached_narrative(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached narrative if exists and not expired.

    Args:
        cache_key: Cache key for the narrative

    Returns:
        Cached narrative dict or None if not found/expired
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        # Check TTL
        cached_at = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            return None  # Expired

        return cached.get('narrative')

    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _save_narrative_to_cache(cache_key: str, narrative: Dict[str, Any]) -> None:
    """Save narrative to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    cache_data = {
        'cached_at': datetime.now().isoformat(),
        'narrative': narrative
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, default=str)


# ============================================================================
# DATA COMPILATION
# ============================================================================

def compile_narrative_data(
    address: str,
    coords: Tuple[float, float],
    sqft: Optional[int] = None,
    schools_info: Optional[Dict[str, str]] = None,
    valuation_result: Optional[Dict[str, Any]] = None,
    development_2mi: Optional[Dict[str, Any]] = None,
    development_5mi: Optional[Dict[str, Any]] = None,
    demographics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compile all property analysis data into a single structure for narrative generation.

    Args:
        address: Full property address
        coords: (latitude, longitude) tuple
        sqft: Property square footage (optional, used for valuation)
        schools_info: Dict with school assignments like:
            {"elementary": "School Name", "middle": "School Name", "high": "School Name"}
        valuation_result: Pre-computed valuation orchestrator result (optional)
        development_2mi: Pre-computed development analysis at 2-mile radius (immediate area)
        development_5mi: Pre-computed development analysis at 5-mile radius (regional/Data Center Alley)
        demographics: Pre-computed demographics from calculate_demographics() (optional)

    Returns:
        Compiled data dictionary with all analysis results
    """
    lat, lon = coords

    # Initialize result structure
    compiled = {
        'property': {
            'address': address,
            'latitude': lat,
            'longitude': lon,
            'sqft': sqft
        },
        'schools': {},
        'location': {},
        'metro': {},
        'neighborhood': {},
        'valuation': {},
        'development': {},
        'demographics': {},
        'compilation_timestamp': datetime.now().isoformat()
    }

    # -------------------------------------------------------------------------
    # 1. SCHOOL CONTEXT
    # -------------------------------------------------------------------------
    if schools_info:
        for level, school_name in schools_info.items():
            if school_name:
                # Determine school type from level
                type_map = {
                    'elementary': 'Elementary',
                    'middle': 'Middle',
                    'high': 'High'
                }
                school_type = type_map.get(level.lower())

                context = get_school_context(school_name, school_type)
                if context:
                    compiled['schools'][level] = {
                        'name': context.get('school_name'),
                        'county_percentile': context.get('county', {}).get('percentile'),
                        'county_bucket': context.get('county', {}).get('bucket'),
                        'state_percentile': context.get('state', {}).get('percentile'),
                        'trajectory': context.get('trajectory', {}).get('direction'),
                        'trajectory_delta': context.get('trajectory', {}).get('delta'),
                        'narrative': context.get('narrative', {})
                    }
                else:
                    compiled['schools'][level] = {
                        'name': school_name,
                        'county_percentile': None,
                        'note': 'Performance data not available'
                    }

    # -------------------------------------------------------------------------
    # 2. LOCATION QUALITY (Road classification, highway proximity, etc.)
    # -------------------------------------------------------------------------
    try:
        # Use cached analyzer for better performance
        location_analyzer = get_cached_location_analyzer()
        location_result = location_analyzer.analyze_location(lat, lon, address)

        compiled['location'] = {
            'road_classification': location_result.get('road_classification'),
            'highway_proximity': location_result.get('highway_proximity'),
            'collector_proximity': location_result.get('collector_proximity'),
            'airport_proximity': location_result.get('airport_proximity'),
            'aiod_status': location_result.get('aiod_status'),
            'data_center_corridor': location_result.get('data_center_corridor'),
            'characteristics': location_result.get('characteristics', []),
            'narrative': location_result.get('narrative')
        }

        # Extract traffic volume if available
        road_class = location_result.get('road_classification', {})
        if road_class and road_class.get('adt'):
            compiled['location']['traffic_adt'] = road_class.get('adt')
            compiled['location']['traffic_display'] = road_class.get('adt_display')

    except Exception as e:
        compiled['location'] = {'error': str(e)}

    # -------------------------------------------------------------------------
    # 3. METRO ACCESS
    # -------------------------------------------------------------------------
    try:
        metro_result = analyze_metro_access(coords)

        if metro_result.get('available'):
            prox = metro_result.get('proximity', {})
            compiled['metro'] = {
                'available': True,
                'nearest_station': prox.get('nearest_station'),
                'distance_miles': prox.get('distance_miles'),
                'tier': metro_result.get('tier', {}).get('tier'),
                'tier_description': metro_result.get('tier', {}).get('tier_description'),
                'drive_time_minutes': metro_result.get('drive_time', {}).get('minutes'),
                'narrative': metro_result.get('narrative')
            }
        else:
            compiled['metro'] = {'available': False}

    except Exception as e:
        compiled['metro'] = {'error': str(e)}

    # -------------------------------------------------------------------------
    # 4. NEIGHBORHOOD (Places/Amenities)
    # -------------------------------------------------------------------------
    try:
        neighborhood_result = analyze_neighborhood(coords)

        if neighborhood_result.get('available'):
            compiled['neighborhood'] = {
                'available': True,
                'dining': neighborhood_result.get('amenities', {}).get('dining', []),
                'grocery': neighborhood_result.get('amenities', {}).get('grocery', []),
                'shopping': neighborhood_result.get('amenities', {}).get('shopping', []),
                'amenity_summary': neighborhood_result.get('amenities', {}).get('summary'),
                'convenience_score': neighborhood_result.get('convenience', {}).get('score'),
                'convenience_rating': neighborhood_result.get('convenience', {}).get('rating'),
                'highlights': neighborhood_result.get('convenience', {}).get('highlights', []),
                'narrative': neighborhood_result.get('narrative')
            }
        else:
            compiled['neighborhood'] = {'available': False}

    except Exception as e:
        compiled['neighborhood'] = {'error': str(e)}

    # -------------------------------------------------------------------------
    # 5. VALUATION CONTEXT
    # -------------------------------------------------------------------------
    if valuation_result:
        val_context = get_valuation_narrative_context(valuation_result)
        compiled['valuation'] = {
            'estimate': val_context.get('estimate'),
            'estimate_formatted': val_context.get('estimate_formatted'),
            'confidence_level': val_context.get('confidence_level'),
            'confidence_score': val_context.get('confidence_score'),
            'price_per_sqft': val_context.get('price_per_sqft', {}),
            'comps_count': val_context.get('comps_summary', {}).get('count'),
            'comps_median_price': val_context.get('comps_summary', {}).get('median_price'),
            'sources': val_context.get('sources_used', []),
            'narrative_sentence': format_valuation_narrative_sentence(val_context),
            'value_descriptor': val_context.get('narrative_helpers', {}).get('value_descriptor')
        }
    else:
        compiled['valuation'] = {'available': False}

    # -------------------------------------------------------------------------
    # 6. DEVELOPMENT ACTIVITY (Dual Radius: 2mi immediate, 5mi regional)
    # -------------------------------------------------------------------------
    def _format_dev_value(val: int) -> str:
        """Format development value for display."""
        if val >= 1_000_000_000:
            return f"${val/1_000_000_000:.1f}B"
        elif val >= 1_000_000:
            return f"${val/1_000_000:.0f}M"
        else:
            return f"${val:,.0f}"

    def _extract_dev_data(dev_result: Dict[str, Any], radius: float) -> Dict[str, Any]:
        """Extract development data from analyze_development result."""
        if not dev_result:
            return {'available': False}
        return {
            'available': True,
            'radius_miles': radius,
            'total_permits': dev_result.get('total_permits', 0),
            'total_value': dev_result.get('total_value', 0),
            'value_display': _format_dev_value(dev_result.get('total_value', 0)),
            'datacenter_count': dev_result.get('datacenter_count', 0),
            'fiber_count': dev_result.get('fiber_count', 0),
            'infrastructure_count': dev_result.get('infrastructure_count', 0),
            'recent_count': dev_result.get('recent_count', 0)
        }

    compiled['development'] = {
        'immediate': _extract_dev_data(development_2mi, 2.0),  # 2-mile radius
        'regional': _extract_dev_data(development_5mi, 5.0)    # 5-mile radius (Data Center Alley)
    }

    # Set overall availability flag
    compiled['development']['available'] = (
        compiled['development']['immediate'].get('available', False) or
        compiled['development']['regional'].get('available', False)
    )

    # -------------------------------------------------------------------------
    # 7. DEMOGRAPHICS (Census Data)
    # -------------------------------------------------------------------------
    if demographics and not demographics.get('metadata', {}).get('error'):
        data_3mi = demographics.get('radii_data', {}).get('3_mile', {})
        county = demographics.get('county_comparison', {})

        compiled['demographics'] = {
            'available': True,
            'population': {
                'total': data_3mi.get('population', {}).get('total'),
                'median_age': data_3mi.get('population', {}).get('median_age')
            },
            'income': {
                'median': data_3mi.get('income', {}).get('median'),
                'pct_over_100k': data_3mi.get('income', {}).get('pct_over_100k'),
                'vs_county': _calc_pct_diff(
                    data_3mi.get('income', {}).get('median'),
                    county.get('median_income')
                )
            },
            'education': {
                'bachelors_plus_pct': data_3mi.get('education', {}).get('bachelors_plus_pct'),
                'vs_county': _calc_pct_diff(
                    data_3mi.get('education', {}).get('bachelors_plus_pct'),
                    county.get('bachelors_plus_pct')
                )
            },
            'employment': {
                'unemployment_rate': data_3mi.get('employment', {}).get('unemployment_rate')
            },
            'homeownership': {
                'owner_occupied_pct': data_3mi.get('households', {}).get('owner_occupied_pct')
            },
            'county_benchmarks': {
                'median_income': county.get('median_income'),
                'bachelors_plus_pct': county.get('bachelors_plus_pct'),
                'unemployment_rate': county.get('unemployment_rate')
            }
        }
    else:
        compiled['demographics'] = {'available': False}

    return compiled


def _calc_pct_diff(local_val: Optional[float], county_val: Optional[float]) -> Optional[str]:
    """Calculate percentage difference vs county benchmark."""
    if local_val is None or county_val is None or county_val == 0:
        return None
    pct_diff = ((local_val - county_val) / county_val) * 100
    if abs(pct_diff) < 1:
        return "at county average"
    sign = "+" if pct_diff > 0 else ""
    return f"{sign}{pct_diff:.0f}% vs county"


# ============================================================================
# NARRATIVE GENERATION
# ============================================================================

def _parse_narrative_response(response_text: str) -> Dict[str, str]:
    """
    Parse Claude's response into section dict.

    Args:
        response_text: Raw response from Claude API

    Returns:
        Dict with section keys and narrative text values
    """
    # Try to extract JSON from the response
    try:
        # First try direct JSON parse
        sections = json.loads(response_text)
        if isinstance(sections, dict):
            return sections
    except json.JSONDecodeError:
        pass

    # Try to find JSON within the response (sometimes Claude adds explanation)
    import re
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            sections = json.loads(json_match.group())
            if isinstance(sections, dict):
                return sections
        except json.JSONDecodeError:
            pass

    # If all parsing fails, return error structure
    return {
        'what_stands_out': 'Unable to generate narrative - parsing error',
        'schools_reality': '',
        'daily_reality': '',
        'worth_knowing': '',
        'investment_lens': '',
        'bottom_line': '',
        'raw_response': response_text
    }


def generate_property_narrative(
    compiled_data: Dict[str, Any],
    use_cache: bool = True,
    model: str = "claude-sonnet-4-20250514"
) -> Dict[str, Any]:
    """
    Generate AI-powered property narrative using Claude API.

    Args:
        compiled_data: Output from compile_narrative_data()
        use_cache: Whether to use/store cached narratives (default True)
        model: Claude model to use (default claude-sonnet-4)

    Returns:
        Dictionary with:
        {
            'sections': {
                'what_stands_out': str,
                'schools_reality': str,
                'daily_reality': str,
                'worth_knowing': str,
                'investment_lens': str,
                'bottom_line': str
            },
            'metadata': {
                'generated_at': str,
                'model': str,
                'cached': bool,
                'data_hash': str
            }
        }
    """
    # Compute data hash for cache key
    data_hash = _compute_data_hash(compiled_data)
    address = compiled_data.get('property', {}).get('address', 'unknown')
    cache_key = _get_cache_key(address, data_hash)

    # Check cache first
    if use_cache:
        cached = _get_cached_narrative(cache_key)
        if cached:
            cached['metadata']['cached'] = True
            return cached

    # Get API key
    api_key = get_api_key('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            'sections': {
                'what_stands_out': 'API key not configured',
                'schools_reality': '',
                'daily_reality': '',
                'worth_knowing': '',
                'investment_lens': '',
                'bottom_line': ''
            },
            'metadata': {
                'error': 'ANTHROPIC_API_KEY not found in config',
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }

    # Build the user prompt with compiled data
    user_prompt = f"""Generate a property analysis narrative for:

ADDRESS: {compiled_data.get('property', {}).get('address')}

PROPERTY DATA:
{json.dumps(compiled_data, indent=2, default=str)}

Generate the 6-section JSON narrative based on this data. Focus on specific facts and local context."""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=model,
            max_tokens=1500,
            system=NARRATIVE_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract response text
        response_text = message.content[0].text

        # Parse the response
        sections = _parse_narrative_response(response_text)

        result = {
            'sections': sections,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'model': model,
                'cached': False,
                'data_hash': data_hash,
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        }

        # Save to cache
        if use_cache:
            _save_narrative_to_cache(cache_key, result)

        return result

    except ImportError:
        return {
            'sections': {
                'what_stands_out': 'anthropic package not installed',
                'schools_reality': '',
                'daily_reality': '',
                'worth_knowing': '',
                'investment_lens': '',
                'bottom_line': ''
            },
            'metadata': {
                'error': 'pip install anthropic required',
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }

    except Exception as e:
        return {
            'sections': {
                'what_stands_out': f'Error generating narrative: {str(e)}',
                'schools_reality': '',
                'daily_reality': '',
                'worth_knowing': '',
                'investment_lens': '',
                'bottom_line': ''
            },
            'metadata': {
                'error': str(e),
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_narrative_for_property(
    address: str,
    coords: Tuple[float, float],
    sqft: Optional[int] = None,
    schools_info: Optional[Dict[str, str]] = None,
    valuation_result: Optional[Dict[str, Any]] = None,
    development_2mi: Optional[Dict[str, Any]] = None,
    development_5mi: Optional[Dict[str, Any]] = None,
    demographics: Optional[Dict[str, Any]] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    One-call convenience function to compile data and generate narrative.

    Args:
        address: Full property address
        coords: (latitude, longitude) tuple
        sqft: Property square footage
        schools_info: School assignments dict
        valuation_result: Pre-computed valuation result
        development_2mi: Pre-computed development at 2-mile radius (immediate)
        development_5mi: Pre-computed development at 5-mile radius (regional)
        demographics: Pre-computed demographics from calculate_demographics()
        use_cache: Whether to use caching

    Returns:
        Generated narrative dict
    """
    compiled = compile_narrative_data(
        address=address,
        coords=coords,
        sqft=sqft,
        schools_info=schools_info,
        valuation_result=valuation_result,
        development_2mi=development_2mi,
        development_5mi=development_5mi,
        demographics=demographics
    )

    return generate_property_narrative(compiled, use_cache=use_cache)


def clear_narrative_cache(address: Optional[str] = None) -> int:
    """
    Clear cached narratives.

    Args:
        address: If provided, only clear cache for this address.
                 If None, clear all cached narratives.

    Returns:
        Number of cache files deleted
    """
    if not CACHE_DIR.exists():
        return 0

    deleted = 0

    if address:
        # Clear for specific address
        normalized = address.lower().strip().replace(' ', '_').replace(',', '')
        for cache_file in CACHE_DIR.glob(f"{normalized}_*.json"):
            cache_file.unlink()
            deleted += 1
    else:
        # Clear all
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
            deleted += 1

    return deleted


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_compile_narrative_data():
    """Test data compilation with mock data."""
    print("=" * 70)
    print("TEST 1: Data Compilation")
    print("=" * 70)

    # Test address
    address = "43422 Cloister Pl, Leesburg, VA 20176"
    coords = (39.0892, -77.5034)

    # Mock school assignments
    schools_info = {
        'elementary': 'Seldens Landing ES',
        'middle': 'J. Lupton Simpson MS',
        'high': 'Rock Ridge High'
    }

    # Mock valuation result (from orchestrator)
    mock_valuation = {
        'current_value': {
            'triangulated_estimate': 895000,
            'confidence_score': 8.2
        },
        'price_per_sqft': {
            'property': 285.00,
            'neighborhood_avg': 273.08,
            'position': 'Above market'
        },
        'comparable_sales': [
            {'address': '123 Test St', 'sale_price': 850000, 'sqft': 3200},
            {'address': '125 Test St', 'sale_price': 875000, 'sqft': 3100},
            {'address': '127 Test St', 'sale_price': 920000, 'sqft': 3400},
        ],
        'data_sources': ['ATTOM Property Detail', 'RentCast Estimates']
    }

    # Mock development results (dual radius)
    mock_development_2mi = {
        'total_permits': 1068,
        'total_value': 263000000,
        'datacenter_count': 2,
        'fiber_count': 15,
        'infrastructure_count': 45,
        'recent_count': 234
    }

    mock_development_5mi = {
        'total_permits': 4250,
        'total_value': 1500000000,  # $1.5B - Data Center Alley
        'datacenter_count': 18,
        'fiber_count': 65,
        'infrastructure_count': 180,
        'recent_count': 890
    }

    # Compile the data
    print(f"\nCompiling data for: {address}")
    print(f"Coordinates: {coords}")

    compiled = compile_narrative_data(
        address=address,
        coords=coords,
        sqft=3200,
        schools_info=schools_info,
        valuation_result=mock_valuation,
        development_2mi=mock_development_2mi,
        development_5mi=mock_development_5mi
    )

    # Display results
    print("\n--- Compiled Data Structure ---")
    print(f"\nProperty: {compiled['property']}")

    print("\nSchools:")
    for level, info in compiled['schools'].items():
        print(f"  {level}: {info.get('name')}")
        if info.get('county_percentile'):
            print(f"    County Percentile: {info['county_percentile']}")
            print(f"    Bucket: {info.get('county_bucket')}")

    print(f"\nLocation: {compiled['location'].get('road_classification', {}).get('road_type', 'N/A')}")
    if compiled['location'].get('traffic_adt'):
        print(f"  Traffic ADT: {compiled['location']['traffic_display']}")

    print(f"\nMetro: {compiled['metro'].get('nearest_station', 'N/A')}")
    if compiled['metro'].get('distance_miles'):
        print(f"  Distance: {compiled['metro']['distance_miles']} miles")

    print(f"\nValuation: {compiled['valuation'].get('estimate_formatted', 'N/A')}")
    print(f"  Confidence: {compiled['valuation'].get('confidence_level', 'N/A')}")
    print(f"  Position: {compiled['valuation'].get('price_per_sqft', {}).get('position', 'N/A')}")

    print(f"\nDevelopment (Dual Radius):")
    imm = compiled['development'].get('immediate', {})
    reg = compiled['development'].get('regional', {})
    print(f"  2mi (immediate): {imm.get('total_permits', 0)} permits, {imm.get('value_display', 'N/A')}")
    print(f"  5mi (regional):  {reg.get('total_permits', 0)} permits, {reg.get('value_display', 'N/A')}")

    return compiled


def test_narrative_generation_mock():
    """Test narrative generation with mock compiled data (no API call)."""
    print("\n" + "=" * 70)
    print("TEST 2: Narrative Generation (Mock Response)")
    print("=" * 70)

    # Create mock compiled data
    mock_compiled = {
        'property': {
            'address': '43422 Cloister Pl, Leesburg, VA 20176',
            'latitude': 39.0892,
            'longitude': -77.5034,
            'sqft': 3200
        },
        'schools': {
            'elementary': {
                'name': 'Seldens Landing ES',
                'county_percentile': 72,
                'county_bucket': 'Above Average',
                'state_percentile': 89,
                'trajectory': 'stable'
            }
        },
        'location': {
            'road_classification': {
                'road_type': 'Residential/Local',
                'adt': None
            },
            'highway_proximity': {'distance_miles': 2.1, 'highway': 'VA-7'}
        },
        'metro': {
            'available': True,
            'nearest_station': 'Ashburn',
            'distance_miles': 4.2,
            'tier': 'Metro Accessible'
        },
        'valuation': {
            'estimate_formatted': '$895,000',
            'confidence_level': 'high',
            'price_per_sqft': {'position': 'Above market', 'difference_pct': 4.4}
        },
        'development': {
            'total_permits': 1068,
            'value_display': '$263M',
            'datacenter_count': 2
        }
    }

    # Mock the response parsing
    mock_response = """{
  "what_stands_out": "This Lansdowne property sits in a sweet spot: 4.2 miles from the Ashburn Silver Line station with $263M in nearby development activity. The 3,200 sqft home is priced 4.4% above neighborhood average at $280/sqft.",
  "schools_reality": "Assigned to Seldens Landing ES (72nd percentile in Loudoun, 89th statewide) - solidly above average for the county with stable performance trajectory. Loudoun context matters: mid-pack here often means top-tier statewide.",
  "daily_reality": "Residential street location means minimal through-traffic. VA-7 access is 2.1 miles away. The Silver Line opens up Tysons/DC commute options without Metro-adjacent noise or density.",
  "worth_knowing": "Two data center permits within 2 miles signal continued infrastructure investment in this corridor. This typically correlates with commercial amenity growth.",
  "investment_lens": "1,068 building permits representing $263M in development within 2mi radius. High confidence valuation from multiple sources. Property positioned above market suggests recent upgrades or premium lot.",
  "bottom_line": "Best suited for families prioritizing strong schools and future appreciation who can accept a 4+ mile Metro commute. The development activity suggests this corridor is still maturing."
}"""

    sections = _parse_narrative_response(mock_response)

    print("\n--- Parsed Sections ---")
    for section, content in sections.items():
        print(f"\n{section.upper()}:")
        print(f"  {content[:100]}..." if len(content) > 100 else f"  {content}")

    print("\nMock test complete.")


def test_cache_operations():
    """Test cache save and retrieve operations."""
    print("\n" + "=" * 70)
    print("TEST 3: Cache Operations")
    print("=" * 70)

    test_address = "123 Test Cache Rd, Leesburg, VA 20176"
    test_hash = "abc123def456"
    cache_key = _get_cache_key(test_address, test_hash)

    print(f"\nCache key: {cache_key}")

    # Test narrative to cache
    test_narrative = {
        'sections': {
            'what_stands_out': 'Test narrative content',
            'schools_reality': 'Test schools',
            'daily_reality': 'Test daily',
            'worth_knowing': 'Test worth knowing',
            'investment_lens': 'Test investment',
            'bottom_line': 'Test bottom line'
        },
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'model': 'test-model',
            'cached': False
        }
    }

    # Save to cache
    _save_narrative_to_cache(cache_key, test_narrative)
    print(f"Saved to cache: {CACHE_DIR / f'{cache_key}.json'}")

    # Retrieve from cache
    retrieved = _get_cached_narrative(cache_key)
    if retrieved:
        print("Successfully retrieved from cache!")
        print(f"  what_stands_out: {retrieved['sections']['what_stands_out']}")
    else:
        print("Cache retrieval failed!")

    # Clean up test cache
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        cache_file.unlink()
        print("Cleaned up test cache file.")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("LOUDOUN NARRATIVE GENERATOR - TEST SUITE")
    print("=" * 70)

    # Test 1: Data compilation
    compiled = test_compile_narrative_data()

    # Test 2: Mock narrative generation
    test_narrative_generation_mock()

    # Test 3: Cache operations
    test_cache_operations()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    run_all_tests()
