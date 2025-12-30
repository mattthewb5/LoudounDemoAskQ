"""
Demographics Formatter for Presentation Layer

Formats Census demographics data for display in Streamlit app:
- AI-generated consumer-friendly summary (Claude API)
- Detailed OM-standard data table
- Plotly charts (income distribution, age distribution)

Usage:
    from core.demographics_formatter import (
        generate_demographics_summary,
        format_demographics_table,
        create_income_chart,
        create_age_chart,
        display_demographics_section
    )
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.api_config import get_api_key

# Cache directory for AI summaries
CACHE_DIR = Path(__file__).parent.parent / 'cache' / 'demographics_summaries'


# =============================================================================
# AI SUMMARY GENERATION
# =============================================================================

DEMOGRAPHICS_SUMMARY_PROMPT = """You are a real estate analyst writing a brief demographic overview for a property location.

Your goal: Create a consumer-friendly summary that helps buyers understand the neighborhood character. Focus on what makes this area distinctive.

TONE:
- Concise and factual
- Highlight genuinely notable characteristics
- Compare to county averages when meaningful
- Use specific numbers, not vague descriptions

OUTPUT FORMAT:
Return a single paragraph (3-5 sentences) summarizing the key demographic characteristics.
Focus on the 3-MILE RADIUS as the primary neighborhood context.

WHAT TO HIGHLIGHT (pick the most notable 3-4 points):
- Income levels relative to county (affluent, middle-income, etc.)
- Age/family composition (young professionals, families with children, retirees)
- Education levels if notably high or low
- Housing tenure (owner vs renter dominated)
- Employment characteristics

DO NOT:
- Use generic real estate language ("desirable", "sought-after")
- Make value judgments about residents
- Speculate beyond the data provided
- Include statistics without context"""


def _compute_cache_key(demographics: Dict[str, Any]) -> str:
    """Compute cache key from demographics data."""
    # Use lat/lon and census year for cache key
    meta = demographics.get('metadata', {})
    key_data = f"{meta.get('lat')}-{meta.get('lon')}-{meta.get('census_year')}"
    return hashlib.md5(key_data.encode()).hexdigest()[:16]


def _get_cached_summary(cache_key: str) -> Optional[str]:
    """Retrieve cached summary if available."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                return cached.get('summary')
        except (json.JSONDecodeError, IOError):
            pass
    return None


def _save_summary_to_cache(cache_key: str, summary: str) -> None:
    """Save summary to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with open(cache_file, 'w') as f:
        json.dump({
            'summary': summary,
            'cached_at': datetime.now().isoformat()
        }, f)


def generate_demographics_summary(
    demographics: Dict[str, Any],
    use_cache: bool = True,
    model: str = "claude-sonnet-4-20250514"
) -> Dict[str, Any]:
    """
    Generate AI-powered demographics summary using Claude API.

    Args:
        demographics: Output from calculate_demographics()
        use_cache: Whether to use/store cached summaries
        model: Claude model to use

    Returns:
        Dictionary with:
        {
            'summary': str,  # The consumer-friendly paragraph
            'metadata': {
                'generated_at': str,
                'model': str,
                'cached': bool
            }
        }
    """
    cache_key = _compute_cache_key(demographics)

    # Check cache first
    if use_cache:
        cached = _get_cached_summary(cache_key)
        if cached:
            # Escape dollar signs only if not already escaped (for backwards compatibility)
            # Use regex to avoid double-escaping
            import re
            escaped_cached = re.sub(r'(?<!\\)\$', r'\\$', cached)
            return {
                'summary': escaped_cached,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'model': model,
                    'cached': True
                }
            }

    # Get API key
    api_key = get_api_key('ANTHROPIC_API_KEY')
    if not api_key:
        return {
            'summary': _generate_fallback_summary(demographics),
            'metadata': {
                'error': 'ANTHROPIC_API_KEY not found - using template summary',
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }

    # Build user prompt with demographics data
    user_prompt = f"""Generate a demographic summary for this property location:

ADDRESS: {demographics.get('metadata', {}).get('property_address', 'Unknown')}

DEMOGRAPHICS DATA:
{json.dumps(demographics, indent=2, default=str)}

Write a single paragraph (3-5 sentences) summarizing the key demographic characteristics of the 3-mile radius area."""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=model,
            max_tokens=300,
            system=DEMOGRAPHICS_SUMMARY_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        summary = message.content[0].text.strip()

        # Escape dollar signs to prevent Streamlit LaTeX interpretation
        summary = summary.replace('$', '\\$')

        # Cache the result
        if use_cache:
            _save_summary_to_cache(cache_key, summary)

        return {
            'summary': summary,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'model': model,
                'cached': False,
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        }

    except ImportError:
        return {
            'summary': _generate_fallback_summary(demographics),
            'metadata': {
                'error': 'anthropic package not installed',
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }

    except Exception as e:
        return {
            'summary': _generate_fallback_summary(demographics),
            'metadata': {
                'error': str(e),
                'generated_at': datetime.now().isoformat(),
                'cached': False
            }
        }


def _generate_fallback_summary(demographics: Dict[str, Any]) -> str:
    """Generate a template-based summary when AI is unavailable."""
    data_3mi = demographics.get('radii_data', {}).get('3_mile', {})
    county = demographics.get('county_comparison', {})

    if not data_3mi:
        return "Demographic data not available for this location."

    pop = data_3mi.get('population', {})
    income = data_3mi.get('income', {})
    households = data_3mi.get('households', {})
    education = data_3mi.get('education', {})

    # Build summary parts
    parts = []

    # Population and age
    if pop.get('total'):
        parts.append(f"The 3-mile radius has a population of {pop['total']:,}")
        if pop.get('median_age'):
            parts.append(f"with a median age of {pop['median_age']}")

    # Income comparison
    if income.get('median') and county.get('median_income'):
        pct_of_county = (income['median'] / county['median_income']) * 100
        if pct_of_county >= 110:
            income_desc = "above the county average"
        elif pct_of_county <= 90:
            income_desc = "below the county average"
        else:
            income_desc = "near the county average"
        parts.append(f"Median household income is \\${income['median']:,.0f}, {income_desc}.")

    # Housing tenure
    if households.get('owner_occupied_pct'):
        if households['owner_occupied_pct'] >= 70:
            parts.append("The area is predominantly owner-occupied.")
        elif households['owner_occupied_pct'] <= 50:
            parts.append("The area has a significant renter population.")

    # Education
    if education.get('bachelors_plus_pct'):
        if education['bachelors_plus_pct'] >= 50:
            parts.append(f"{education['bachelors_plus_pct']}% of adults hold a bachelor's degree or higher.")

    return " ".join(parts) if parts else "Demographic data available for this location."


# =============================================================================
# TABLE FORMATTING
# =============================================================================

def format_demographics_table(demographics: Dict[str, Any]) -> str:
    """
    Format demographics data as a markdown table for display.

    Args:
        demographics: Output from calculate_demographics()

    Returns:
        Markdown-formatted table string
    """
    data_1mi = demographics.get('radii_data', {}).get('1_mile', {})
    data_3mi = demographics.get('radii_data', {}).get('3_mile', {})
    county = demographics.get('county_comparison', {})

    def fmt_num(val, prefix='', suffix=''):
        if val is None:
            return '-'
        # Escape dollar signs to prevent Streamlit LaTeX interpretation
        escaped_prefix = prefix.replace('$', '\\$') if prefix else ''
        if isinstance(val, float):
            return f"{escaped_prefix}{val:,.0f}{suffix}"
        return f"{escaped_prefix}{val:,}{suffix}"

    def fmt_pct(val):
        if val is None:
            return '-'
        return f"{val:.0f}%"

    def fmt_unemp(val):
        """Format unemployment rate with one decimal place."""
        if val is None:
            return '-'
        return f"{val:.1f}%"

    def calc_variance(local_val, county_val):
        """Calculate variance as percentage points difference for rate metrics."""
        if local_val is None or county_val is None:
            return '-'
        diff = local_val - county_val
        if abs(diff) < 0.5:
            return '-'
        abs_diff = abs(diff)
        direction = 'higher' if diff > 0 else 'lower'
        return f"{abs_diff:.0f} pp {direction}"

    def calc_income_variance(local_val, county_val):
        """Calculate income variance as percentage."""
        if local_val is None or county_val is None:
            return '-'
        pct_diff = ((local_val - county_val) / county_val) * 100
        if abs(pct_diff) < 1:
            return '-'
        sign = '+' if pct_diff > 0 else ''
        return f"{sign}{pct_diff:.0f}%"

    def calc_unemp_variance(local_val, county_val):
        """Calculate unemployment variance with one decimal place for rate metrics."""
        if local_val is None or county_val is None:
            return '-'
        diff = local_val - county_val
        if abs(diff) < 0.1:
            return '-'
        abs_diff = abs(diff)
        direction = 'higher' if diff > 0 else 'lower'
        return f"{abs_diff:.1f} pp {direction}"

    # Build unemployment display - show BLS current if available
    bls_data = county.get('bls_unemployment', {})
    census_unemp = county.get('census_unemployment', {})

    # Format unemployment rows with both sources if BLS is available
    # Get unemployment values for radius calculations
    unemp_1mi = data_1mi.get('employment', {}).get('unemployment_rate')
    unemp_3mi = data_3mi.get('employment', {}).get('unemployment_rate')
    census_county_rate = census_unemp.get('rate') if census_unemp else county.get('unemployment_rate')

    # Trajectory row (only if BLS data has year-over-year comparison)
    unemployment_trajectory_row = None

    if bls_data and bls_data.get('rate') is not None:
        bls_rate = bls_data.get('rate')
        # Shorten month name for display (e.g., "September" -> "Sep")
        bls_month = bls_data.get('period', '')[:3]
        bls_period = f"{bls_month} {bls_data.get('year', '')}"

        # BLS row: County-level only, show "-" for radius columns
        unemployment_bls_row = f"| Current Unemployment (BLS) | - | - | {bls_rate:.1f}% ({bls_period}) | - |"

        # Build trajectory row if year-ago data available
        year_ago_rate = bls_data.get('year_ago_rate')
        change = bls_data.get('change')
        if year_ago_rate is not None and change is not None:
            if abs(change) < 0.1:
                trajectory_display = "↔ stable"
            else:
                arrow = "↑" if change > 0 else "↓"
                trajectory_display = f"{arrow} {abs(change):.1f} pp from {year_ago_rate:.1f}%"
            unemployment_trajectory_row = f"| 12-Month Change | - | - | {trajectory_display} | - |"

        # Census row: Show radius values with variance against county
        unemployment_census_row = f"| Unemployment (Census) | {fmt_unemp(unemp_1mi)} | {fmt_unemp(unemp_3mi)} | {fmt_unemp(census_county_rate)} | {calc_unemp_variance(unemp_3mi, census_county_rate)} |"
    else:
        # No BLS data - show Census only with decimal formatting
        unemployment_bls_row = f"| Unemployment Rate | {fmt_unemp(unemp_1mi)} | {fmt_unemp(unemp_3mi)} | {fmt_unemp(county.get('unemployment_rate'))} | {calc_unemp_variance(unemp_3mi, county.get('unemployment_rate'))} |"
        unemployment_census_row = None

    # Build the table
    lines = [
        "| Metric | 1-Mile | 3-Mile | Loudoun Co. | 3-Mile vs County |",
        "|--------|--------|--------|-------------|------------------|",
        "| **POPULATION** |||||",
        f"| Total Population | {fmt_num(data_1mi.get('population', {}).get('total'))} | {fmt_num(data_3mi.get('population', {}).get('total'))} | 427,082 | - |",
        f"| Median Age | {fmt_num(data_1mi.get('population', {}).get('median_age'))} | {fmt_num(data_3mi.get('population', {}).get('median_age'))} | {fmt_num(county.get('median_age'))} | - |",
        "| **HOUSEHOLDS** |||||",
        f"| Total Households | {fmt_num(data_1mi.get('households', {}).get('total'))} | {fmt_num(data_3mi.get('households', {}).get('total'))} | - | - |",
        f"| Avg Household Size | {data_1mi.get('households', {}).get('avg_size') or '-'} | {data_3mi.get('households', {}).get('avg_size') or '-'} | - | - |",
        f"| Owner-Occupied | {fmt_pct(data_1mi.get('households', {}).get('owner_occupied_pct'))} | {fmt_pct(data_3mi.get('households', {}).get('owner_occupied_pct'))} | {fmt_pct(county.get('owner_occupied_pct'))} | {calc_variance(data_3mi.get('households', {}).get('owner_occupied_pct'), county.get('owner_occupied_pct'))} |",
        "| **INCOME** |||||",
        f"| Median HH Income | {fmt_num(data_1mi.get('income', {}).get('median'), '$')} | {fmt_num(data_3mi.get('income', {}).get('median'), '$')} | {fmt_num(county.get('median_income'), '$')} | {calc_income_variance(data_3mi.get('income', {}).get('median'), county.get('median_income'))} |",
        f"| Avg HH Income | {fmt_num(data_1mi.get('income', {}).get('average'), '$')} | {fmt_num(data_3mi.get('income', {}).get('average'), '$')} | - | - |",
        f"| HH Earning $100K+ | {fmt_pct(data_1mi.get('income', {}).get('pct_over_100k'))} | {fmt_pct(data_3mi.get('income', {}).get('pct_over_100k'))} | - | - |",
        "| **EDUCATION** |||||",
        f"| Bachelor's Degree+ | {fmt_pct(data_1mi.get('education', {}).get('bachelors_plus_pct'))} | {fmt_pct(data_3mi.get('education', {}).get('bachelors_plus_pct'))} | {fmt_pct(county.get('bachelors_plus_pct'))} | {calc_variance(data_3mi.get('education', {}).get('bachelors_plus_pct'), county.get('bachelors_plus_pct'))} |",
        "| **EMPLOYMENT** |||||",
        unemployment_bls_row,
    ]

    # Add trajectory row if available (shows 12-month change)
    if unemployment_trajectory_row:
        lines.append(unemployment_trajectory_row)

    # Add Census row if BLS data is available (shows both sources)
    if unemployment_census_row:
        lines.append(unemployment_census_row)

    return "\n".join(lines)


def get_data_source_note(demographics: Dict[str, Any]) -> str:
    """Get formatted data source attribution."""
    meta = demographics.get('metadata', {})
    county = demographics.get('county_comparison', {})

    # Check if BLS data is available
    bls_data = county.get('bls_unemployment', {})
    if bls_data and bls_data.get('rate') is not None:
        bls_period = f"{bls_data.get('period', '')} {bls_data.get('year', '')}"
        return (
            f"*Data Sources: U.S. Census Bureau ACS {meta.get('acs_dataset', '2019-2023')}; "
            f"BLS Local Area Unemployment Statistics ({bls_period})*"
        )
    else:
        return f"*Data Source: U.S. Census Bureau, American Community Survey {meta.get('acs_dataset', '2019-2023')}*"


# =============================================================================
# PLOTLY CHARTS
# =============================================================================

def create_income_chart(demographics: Dict[str, Any], radius: str = '3_mile'):
    """
    Create horizontal bar chart for income distribution.

    Args:
        demographics: Output from calculate_demographics()
        radius: Which radius to display ('1_mile' or '3_mile')

    Returns:
        Plotly figure object, or None if data unavailable
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    data = demographics.get('radii_data', {}).get(radius, {})
    distribution = data.get('income', {}).get('distribution', {})

    if not distribution:
        return None

    # Order brackets from lowest to highest income
    bracket_order = [
        'Under $25K',
        '$25K-$50K',
        '$50K-$75K',
        '$75K-$100K',
        '$100K-$150K',
        '$150K-$200K',
        '$200K+'
    ]

    labels = []
    values = []
    for bracket in bracket_order:
        if bracket in distribution:
            labels.append(bracket)
            values.append(distribution[bracket])

    if not values:
        return None

    # Calculate percentages
    total = sum(values)
    percentages = [(v / total * 100) if total > 0 else 0 for v in values]

    # Create horizontal bar chart
    fig = go.Figure(data=[
        go.Bar(
            y=labels,
            x=percentages,
            orientation='h',
            marker_color='#6366f1',
            text=[f'{p:.0f}%' for p in percentages],
            textposition='outside',
            hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
        )
    ])

    radius_label = radius.replace('_', '-').title()
    fig.update_layout(
        title=f'Household Income Distribution ({radius_label} Radius)',
        xaxis_title='Percentage of Households',
        yaxis_title='',
        xaxis=dict(range=[0, max(percentages) * 1.2], ticksuffix='%'),
        height=300,
        margin=dict(l=100, r=40, t=40, b=40),
        showlegend=False
    )

    return fig


def create_age_chart(demographics: Dict[str, Any], radius: str = '3_mile'):
    """
    Create horizontal bar chart for age distribution.

    Args:
        demographics: Output from calculate_demographics()
        radius: Which radius to display ('1_mile' or '3_mile')

    Returns:
        Plotly figure object, or None if data unavailable
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    data = demographics.get('radii_data', {}).get(radius, {})
    distribution = data.get('population', {}).get('age_distribution', {})

    if not distribution:
        return None

    # Order age brackets
    bracket_order = [
        '0-17 (Children)',
        '18-24 (Young Adults)',
        '25-34 (Young Professionals)',
        '35-54 (Peak Earning)',
        '55-64 (Pre-Retirement)',
        '65+ (Seniors)'
    ]

    labels = []
    values = []
    for bracket in bracket_order:
        if bracket in distribution:
            labels.append(bracket)
            values.append(distribution[bracket])

    if not values:
        return None

    # Calculate percentages
    total = sum(values)
    percentages = [(v / total * 100) if total > 0 else 0 for v in values]

    # Create horizontal bar chart
    fig = go.Figure(data=[
        go.Bar(
            y=labels,
            x=percentages,
            orientation='h',
            marker_color='#22c55e',
            text=[f'{p:.0f}%' for p in percentages],
            textposition='outside',
            hovertemplate='%{y}: %{x:.1f}%<extra></extra>'
        )
    ])

    radius_label = radius.replace('_', '-').title()
    fig.update_layout(
        title=f'Age Distribution ({radius_label} Radius)',
        xaxis_title='Percentage of Population',
        yaxis_title='',
        xaxis=dict(range=[0, max(percentages) * 1.2], ticksuffix='%'),
        height=300,
        margin=dict(l=150, r=40, t=40, b=40),
        showlegend=False
    )

    return fig


# =============================================================================
# STREAMLIT DISPLAY HELPER
# =============================================================================

def display_demographics_section(
    demographics: Dict[str, Any],
    st_module,
    show_ai_summary: bool = True,
    show_table: bool = True,
    show_charts: bool = True
) -> None:
    """
    Display complete demographics section in Streamlit.

    This is a convenience function that renders all demographics components.

    Args:
        demographics: Output from calculate_demographics()
        st_module: Streamlit module (pass `st` from the calling code)
        show_ai_summary: Whether to show AI-generated summary
        show_table: Whether to show detailed data table
        show_charts: Whether to show distribution charts
    """
    st = st_module

    # Check for errors
    if 'error' in demographics.get('metadata', {}):
        st.warning(f"Demographics data unavailable: {demographics['metadata']['error']}")
        return

    # AI Summary
    if show_ai_summary:
        st.markdown("### Area Overview")
        summary_result = generate_demographics_summary(demographics)
        st.markdown(summary_result['summary'])
        st.markdown("")

    # Charts in columns
    if show_charts:
        col1, col2 = st.columns(2)

        with col1:
            income_fig = create_income_chart(demographics, '3_mile')
            if income_fig:
                st.plotly_chart(income_fig, width='stretch')

        with col2:
            age_fig = create_age_chart(demographics, '3_mile')
            if age_fig:
                st.plotly_chart(age_fig, width='stretch')

    # Detailed Table
    if show_table:
        with st.expander("Detailed Demographics Data", expanded=False):
            st.markdown(format_demographics_table(demographics))
            st.markdown("")
            st.markdown(get_data_source_note(demographics))


# =============================================================================
# TESTING
# =============================================================================

if __name__ == '__main__':
    # Test with sample demographics data
    sample_demographics = {
        'metadata': {
            'property_address': '43422 Cloister Pl, Leesburg, VA 20176',
            'lat': 39.1157,
            'lon': -77.5647,
            'census_year': '2023',
            'acs_dataset': '2019-2023'
        },
        'radii_data': {
            '1_mile': {
                'population': {'total': 10021, 'median_age': 38.8},
                'households': {'total': 3750, 'avg_size': 2.2, 'owner_occupied_pct': 72.0},
                'income': {'median': 111991, 'average': 141919, 'pct_over_100k': 58.0},
                'education': {'bachelors_plus_pct': 59.0},
                'employment': {'unemployment_rate': 3.4}
            },
            '3_mile': {
                'population': {
                    'total': 50032,
                    'median_age': 36.3,
                    'age_distribution': {
                        '0-17 (Children)': 13320,
                        '18-24 (Young Adults)': 3742,
                        '25-34 (Young Professionals)': 7332,
                        '35-54 (Peak Earning)': 14650,
                        '55-64 (Pre-Retirement)': 6066,
                        '65+ (Seniors)': 4922
                    }
                },
                'households': {'total': 16817, 'avg_size': 2.4, 'owner_occupied_pct': 72.0},
                'income': {
                    'median': 143890,
                    'average': 175890,
                    'pct_over_100k': 66.0,
                    'distribution': {
                        'Under $25K': 972,
                        '$25K-$50K': 1231,
                        '$50K-$75K': 1651,
                        '$75K-$100K': 1887,
                        '$100K-$150K': 2852,
                        '$150K-$200K': 2788,
                        '$200K+': 5436
                    }
                },
                'education': {'bachelors_plus_pct': 58.0},
                'employment': {'unemployment_rate': 2.8}
            }
        },
        'county_comparison': {
            'median_income': 178707,
            'median_age': 37,
            'owner_occupied_pct': 78.0,
            'bachelors_plus_pct': 64.0,
            'unemployment_rate': 3.2
        }
    }

    print("=" * 60)
    print("DEMOGRAPHICS FORMATTER TEST")
    print("=" * 60)
    print()

    # Test table formatting
    print("DETAILED TABLE:")
    print(format_demographics_table(sample_demographics))
    print()
    print(get_data_source_note(sample_demographics))
    print()

    # Test AI summary (will use fallback if no API key)
    print("AI SUMMARY:")
    summary = generate_demographics_summary(sample_demographics, use_cache=False)
    print(summary['summary'])
    print()
    print(f"Metadata: {summary['metadata']}")
