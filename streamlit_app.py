#!/usr/bin/env python3
"""
Athens Home Buyer Research Assistant - Web Interface
Streamlit web app for comprehensive neighborhood research (schools + crime/safety)
"""

# Standard library imports
import os
import traceback
from collections import Counter

# Third-party imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from anthropic import Anthropic

# Local application imports
from school_info import get_school_info, format_complete_report
from ai_school_assistant import SchoolAIAssistant
from crime_analysis import analyze_crime_near_address, format_analysis_report
from gosa_data_loader import get_gosa_loader, get_school_performance_for_analysis
from zoning_lookup import (
    format_zoning_report,
    format_nearby_zoning_report,
    get_zoning_code_description,
    calculate_development_probability,
    classify_risk_level,
    generate_development_interpretation
)
from unified_ai_assistant import UnifiedAIAssistant
from address_extraction import extract_address_from_query
from crime_visualizations import (
    create_category_chart_data,
    create_trend_chart_data,
    create_comparison_chart_data,
    create_safety_score_html,
    create_comparison_html,
    format_crime_stats_table,
    get_safety_color,
    get_category_colors
)


def get_display_school_name(abbreviated_name):
    """Convert abbreviated school names to full display names"""
    display_names = {
        # Elementary schools
        'elementary c': 'Cleveland Road Elementary School',
        'cleveland': 'Cleveland Road Elementary School',
        'barrow': 'David C. Barrow Elementary School',
        'bettye h. holston': 'Bettye Henderson Holston Elementary School',
        'johnnie l. burks': 'Johnnie Lay Burks Elementary School',
        'jj harris': 'Judia Jackson Harris Elementary School',
        'stroud': 'Howard B. Stroud Elementary School',
        'whit davis': 'Whit Davis Road Elementary School',
        'whitehead': 'Whitehead Road Elementary School',
        'oglethorpe': 'Oglethorpe Avenue Elementary School',
        'fowler': 'Fowler Drive Elementary School',
        'timothy': 'Timothy Road Elementary School',
        'gaines': 'Gaines Elementary School',
        'barnett shoals': 'Barnett Shoals Elementary School',
        'winterville': 'Winterville Elementary School',

        # Middle schools
        'b-h-l': 'Burney-Harris-Lyons Middle School',
        'bhl': 'Burney-Harris-Lyons Middle School',
        'clarke middle': 'Clarke Middle School',
        'hilsman': 'Hilsman Middle School',
        'coile': 'W.R. Coile Middle School',

        # High schools
        'clarke central': 'Clarke Central High School',
        'cedar shoals': 'Cedar Shoals High School',
    }

    normalized = abbreviated_name.lower().strip()
    return display_names.get(normalized, abbreviated_name)


def generate_school_performance_analysis(school_name: str, performance_data: dict, api_key: str) -> str:
    """
    Generate AI analysis of school performance using Claude API

    Args:
        school_name: Name of the school
        performance_data: Dict with performance metrics from GOSA data
        api_key: Anthropic API key

    Returns:
        3-4 sentence analysis of school quality and trends
    """
    if not performance_data:
        return "Performance data not available for this school."

    try:
        client = Anthropic(api_key=api_key)

        # Format the data for the prompt
        subjects_text = ", ".join([f"{subj}: {pct:.1f}%" for subj, pct in performance_data['subjects'].items()])

        # Format year trends if available
        years_text = ""
        if performance_data.get('years'):
            years_sorted = sorted(performance_data['years'].items())
            if len(years_sorted) > 1:
                years_text = f"\nProficiency Trend: " + ", ".join([f"{yr}: {pct:.1f}%" for yr, pct in years_sorted])

        # Build prompt with high school metrics if available
        hs_metrics_text = ""
        if performance_data.get('is_high_school'):
            hs_parts = []
            if performance_data.get('graduation_rate'):
                hs_parts.append(f"Graduation Rate: {performance_data['graduation_rate']:.1f}%")
            if performance_data.get('sat_total'):
                hs_parts.append(f"Average SAT: {performance_data['sat_total']:.0f}")
            if performance_data.get('act_composite'):
                hs_parts.append(f"Average ACT: {performance_data['act_composite']:.1f}")
            if performance_data.get('hope_eligibility_pct'):
                hs_parts.append(f"HOPE Eligibility: {performance_data['hope_eligibility_pct']:.1f}%")
            if hs_parts:
                hs_metrics_text = "\nHigh School Metrics: " + ", ".join(hs_parts)

        prompt = f"""Analyze this school's performance data and provide exactly 3-4 sentences about school quality and any notable patterns.

School: {school_name}
Average Proficiency: {performance_data['avg_proficiency']:.1f}%
Subject Proficiencies: {subjects_text}
Total Students Tested: {performance_data['total_tested']}{years_text}{hs_metrics_text}

Be direct and specific. Mention strengths and weaknesses. Comment on trends if multi-year data available. Do not use first-person pronouns."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    except Exception as e:
        return f"Unable to generate analysis: {str(e)}"


@st.cache_data(ttl=3600)
def get_cached_school_analysis(school_name: str, perf_data_str: str, api_key: str) -> str:
    """Cached wrapper for school performance analysis"""
    import json
    performance_data = json.loads(perf_data_str)
    return generate_school_performance_analysis(school_name, performance_data, api_key)


# Page configuration
st.set_page_config(
    page_title="6:14",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        text-align: center;
        color: #1e3a8a;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 0.2em;
    }

    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2em;
        margin-bottom: 2em;
    }

    /* Input section styling */
    .stTextInput > label {
        font-weight: 600;
        color: #334155;
    }

    .stTextArea > label {
        font-weight: 600;
        color: #334155;
    }

    /* Button styling */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.75em 2em;
        border-radius: 0.5em;
        border: none;
        width: 100%;
    }

    .stButton > button:hover {
        background-color: #1d4ed8;
    }

    /* Response box styling */
    .response-box {
        background-color: #f8fafc;
        border-left: 4px solid #2563eb;
        padding: 1.5em;
        margin: 1em 0;
        border-radius: 0.5em;
    }

    /* Disclaimer styling */
    .disclaimer {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1em;
        margin: 2em 0;
        border-radius: 0.5em;
        font-size: 0.9em;
    }

    /* Info box */
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1em;
        margin: 1em 0;
        border-radius: 0.5em;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85em;
        margin-top: 3em;
        padding-top: 2em;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🏡 6:14</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered school, safety, & zoning research for Athens-Clarke County, Georgia</p>', unsafe_allow_html=True)

# About the Data - moved to footer (commented out for now to focus on main interface)
if False:  # Set to True to show About section
    with st.expander("📖 About the Data - Sources, Updates & Limitations"):
        st.markdown("""
        ### 📚 Data Sources

        This tool combines data from four official sources:

    **School Information:**
    - **School Assignments**: Clarke County School District Official Street Index (2024-25 school year)
    - **School Performance**: Georgia Governor's Office of Student Achievement (GOSA) - 2023-24 data
    - **Metrics**: CCRPI scores, Content Mastery, Literacy/Math proficiency, Graduation rates
    - **Verify**: [clarke.k12.ga.us/page/school-attendance-zones](https://www.clarke.k12.ga.us/page/school-attendance-zones)

    **Crime & Safety Information:**
    - **Source**: Athens-Clarke County Police Department Official Database
    - **Coverage**: Last 12 months of reported incidents
    - **Search Radius**: 0.5 miles from address (configurable)
    - **Categories**: Violent, Property, Traffic, and Other offenses
    - **Verify**: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)

    **Zoning & Land Use Information:**
    - **Source**: Athens-Clarke County Planning Department GIS
    - **Data**: Current zoning codes, future land use comprehensive plan, property size
    - **Coverage**: All parcels in Athens-Clarke County
    - **Includes**: Nearby parcel context, split zoning detection, plan changes
    - **Verify**: Contact Planning Department at (706) 613-3515 or visit [Athens-Clarke GIS Portal](https://enigma.accgov.com/)

    ---

    ### 🔄 Update Frequency

    - **School Assignments**: Updated annually (current: 2024-25 school year)
    - **School Performance**: Updated annually after state assessment (current: 2023-24 data)
    - **Crime Data**:
      - Individual address queries: Cached for 24 hours
      - Athens baseline comparison: Refreshed weekly
      - Source database: Updated regularly by Athens-Clarke PD
    - **AI Analysis**: Generated in real-time using Claude 3 Haiku

    ---

    ### ⚠️ Important Limitations

    **What This Tool DOES Provide:**
    - ✓ School assignments for a specific address
    - ✓ School performance metrics from official state data
    - ✓ Crime statistics within a radius of the address
    - ✓ Safety trends and comparisons to Athens average
    - ✓ AI-synthesized insights combining schools and safety

    **What This Tool DOES NOT Provide:**
    - ✗ Home prices or property values
    - ✗ Traffic patterns or commute times
    - ✗ Parks, recreation, or walkability scores
    - ✗ Restaurants, shopping, or amenities
    - ✗ Future development plans
    - ✗ Community "feel" or culture
    - ✗ Unreported crimes or private security incidents
    - ✗ Crimes on UGA campus (separate jurisdiction)

    **Always Remember:**
    - This is for **research purposes only**
    - School zones can change - verify with the district
    - Crime patterns evolve - data is historical
    - Visit neighborhoods in person
    - Talk to local residents and realtors
    - Consider your specific needs and priorities

    ---

    ### 🎯 How the Safety Score Works

    The 1-100 safety score is calculated using a transparent algorithm:

    1. **Start at 100** (perfect score)
    2. **Crime Density Deduction** (0 to -50 points):
       - Based on crimes per month within 0.5 mile radius
       - More crimes = larger deduction
    3. **Violent Crime Percentage** (0 to -25 points):
       - Higher percentage of violent crimes = larger deduction
    4. **Trend Adjustment** (-15 to +5 points):
       - Crime decreasing = bonus points
       - Crime increasing = deduction
    5. **Final Score**: Clipped to range [1-100]

    **Score Ranges:**
    - 80-100: Very Safe (Green)
    - 60-79: Safe (Light Green)
    - 40-59: Moderate (Yellow/Orange)
    - 20-39: Concerning (Red)
    - 1-19: High Risk (Dark Red)

    This scale is designed for expansion to other U.S. cities with varying crime levels.

    ---

    ### 🤖 About the AI

    - **Model**: Claude 3 Haiku by Anthropic
    - **Purpose**: Synthesizes data from multiple sources and answers questions in plain English
    - **What it does**: Combines school performance, crime statistics, and zoning data to provide contextual insights
    - **What it doesn't do**: Make up information, predict the future, or provide legal/financial advice
    - **Citations**: All AI responses reference specific data points and sources

    ---

    ### 📬 Contact & Feedback

    **This is a demo/research tool** built to showcase AI-powered neighborhood research capabilities.

    - **Not affiliated with**: Clarke County School District, Georgia Department of Education, or Athens-Clarke County Government
    - **Data accuracy**: We strive for accuracy but cannot guarantee completeness - always verify independently
    - **Questions about school zones**: Contact Clarke County Schools directly at (706) 546-7721
    - **Questions about crime data**: Contact Athens-Clarke County Police Department
    - **Questions about zoning**: Contact ACC Planning Department at (706) 613-3515
    - **Technical questions or feedback about this tool**: Submit issues at the project repository

    ---

    ### 🛡️ Privacy & Usage

    - **No data collection**: We do not store your queries or search history
    - **No personal information**: No login or personal data required
    - **Public data only**: All information comes from publicly available sources
    - **API usage**: Queries are sent to Anthropic's Claude API for analysis (see their privacy policy)

    **Ethical Use:**
    This tool should be used to help people make informed decisions about where to live. It should not be used to:
    - Discriminate against or stigmatize neighborhoods
    - Make decisions solely based on historical crime data without context
    - Replace professional advice (real estate, legal, financial)
    - Spread misinformation or unsupported claims

    ---

    **Last Updated**: November 2024 | **Geographic Coverage**: Athens-Clarke County, Georgia only
    """)

# Check for API key
api_key = os.environ.get('ANTHROPIC_API_KEY')

if not api_key:
    st.markdown("""
    <div class="info-box">
        ℹ️ <strong>Setup Required:</strong> To use AI features, set your ANTHROPIC_API_KEY environment variable.<br>
        Get your API key at: <a href="https://console.anthropic.com/" target="_blank">console.anthropic.com</a><br><br>
        <code>export ANTHROPIC_API_KEY='your-api-key-here'</code><br>
        <code>streamlit run streamlit_app.py</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize session state
if 'unified_assistant' not in st.session_state:
    try:
        st.session_state.unified_assistant = UnifiedAIAssistant(api_key=api_key)
        st.session_state.api_ready = True
    except Exception as e:
        st.session_state.api_ready = False
        st.error(f"❌ Error initializing AI assistant: {str(e)}")
        st.stop()

# Main input area - Simplified
user_query = st.text_area(
    "Enter the Address & Your Question",
    placeholder="Example: Is 150 Hancock Avenue a good area for families with young kids?\n\nOr try: What are the schools like at 1398 W Hancock Ave, Athens, GA 30606?",
    height=100,
    help="Type your question about any property in Athens. Include the street address in your question, and I'll analyze schools, safety, and zoning data for you."
)

# Always include all three analysis types (no checkboxes)
include_schools = True
include_crime = True
include_zoning = True

# Search button
# TODO: After Dec 31, 2025 - Replace use_container_width with new Streamlit parameter
# See: https://docs.streamlit.io for updated syntax
search_button = st.button("SEARCH", use_container_width=True)

# Process search
if search_button:
    if not user_query or not user_query.strip():
        st.warning("""
        ⚠️ **Please enter your question**

        **Example:**
        - Is 150 Hancock Avenue a good area for families with young kids?
        - What are the schools like at 1398 W Hancock Ave, Athens, GA 30606?
        - How safe is 220 College Station Road?
        """)
    else:
        # Extract address and question from user query
        address_input, question_input = extract_address_from_query(user_query)

        if not address_input:
            st.error("""
            📍 **Couldn't find an address in your question**

            Please include a street address in Athens, GA. For example:
            - Is **150 Hancock Avenue** a good area for families?
            - What are the schools like at **1398 W Hancock Ave, Athens, GA 30606**?
            - How safe is **220 College Station Road**?

            Make sure to include a street number and street name!
            """)
        else:
            # Show what was extracted - always visible in blue bordered box
            st.markdown("""
            <div style="border: 2px solid #3b82f6; padding: 1.5em; border-radius: 0.5em; margin: 1em 0; background-color: white;">
                <h4 style="margin-top: 0; text-align: center;">What I understood</h4>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**Address:** {address_input}")
            st.markdown("")  # Spacing

            # Add Athens, GA if not present
            full_address = address_input
            if 'athens' not in address_input.lower():
                full_address = f"{address_input}, Athens, GA"

            # Show loading state
            loading_msg = "🔍 Analyzing"
            data_types = []
            if include_schools:
                data_types.append("schools")
            if include_crime:
                data_types.append("crime")
            if include_zoning:
                data_types.append("zoning")

            if len(data_types) == 3:
                loading_msg += " schools, crime, and zoning data"
            elif len(data_types) == 2:
                loading_msg += f" {data_types[0]} and {data_types[1]} data"
            elif len(data_types) == 1:
                loading_msg += f" {data_types[0]} data"

            loading_msg += f" for: {full_address}..."

            with st.spinner(loading_msg):
                try:
                    # Get comprehensive analysis
                    result = st.session_state.unified_assistant.get_comprehensive_analysis(
                        address=full_address,
                        question=question_input,
                        include_schools=include_schools,
                        include_crime=include_crime,
                        include_zoning=include_zoning,
                        radius_miles=0.5,
                        months_back=12
                    )

                    if result['error']:
                        error_msg = result['error']

                        # Provide helpful error messages based on error type
                        if "outside" in error_msg.lower() or "not in athens" in error_msg.lower():
                            st.error("""
                            🌍 **Address Outside Athens-Clarke County**

                            This tool currently only works for addresses within Athens-Clarke County, Georgia.

                            **What you can do:**
                            - Try a different address within Athens city limits
                            - Check if you spelled the street name correctly
                            - Make sure you're not searching in Watkinsville, Bogart, or other nearby towns

                            **Sample Athens addresses to try:**
                            - 150 Hancock Avenue, Athens, GA 30601 (downtown)
                            - 220 College Station Road, Athens, GA 30602 (suburban)
                            - 1000 Jennings Mill Road, Athens, GA 30606 (southeast)
                            """)
                        elif "not found" in error_msg.lower() or "geocod" in error_msg.lower():
                            st.error("""
                            📍 **Address Not Found**

                            We couldn't locate that address. This might happen if:
                            - The address has a typo or misspelling
                            - It's a very new address not yet in mapping databases
                            - The street name format is unusual

                            **What you can do:**
                            - Double-check the spelling of the street name
                            - Try using the full format: "123 Main Street, Athens, GA 30601"
                            - Verify the address exists on Google Maps first
                            - Try a nearby address on the same street
                            """)
                        elif "school" in error_msg.lower():
                            st.error(f"""
                            🎓 **School Data Issue**

                            {error_msg}

                            **What you can do:**
                            - The address might be outside Athens-Clarke County school district
                            - School zone data is from 2024-25 - new construction may not be included yet
                            - Try unchecking "School Information" and searching with just Crime/Safety data
                            - Contact Clarke County Schools directly at (706) 546-7721 for official zone information
                            """)
                        elif "crime" in error_msg.lower() or "api" in error_msg.lower():
                            st.error(f"""
                            🛡️ **Crime Data Issue**

                            {error_msg}

                            **What you can do:**
                            - The crime database might be temporarily unavailable
                            - Try again in a few moments
                            - Try unchecking "Crime & Safety Analysis" and searching with just School Information
                            - You can view the Athens crime map directly: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)
                            """)
                        else:
                            st.error(f"""
                            ❌ **Something Went Wrong**

                            {error_msg}

                            **What you can do:**
                            - Check that your address is within Athens-Clarke County, GA
                            - Try a different address format
                            - Verify the address exists on Google Maps
                            - If the problem persists, try one of our demo addresses:
                              - 150 Hancock Avenue, Athens, GA 30601
                              - 220 College Station Road, Athens, GA 30602
                            """)

                    # Display results - Simplified layout matching the design
                    st.markdown("")  # Spacing

                    # Key Insights at a Glance - show first
                    st.markdown("""
                    <div style="background-color: #f0f0f0; padding: 1.5em; border-radius: 0.5em; margin: 1em 0;">
                        <h3 style="margin-top: 0; text-align: center;">🎯 Key Insights at a Glance</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    insights_col1, insights_col2 = st.columns(2)

                    with insights_col1:
                        st.markdown("**✅ Strengths:**")
                        strengths = []

                        # School strengths
                        if result.get('school_info'):
                            school_info = result['school_info']
                            if hasattr(school_info, 'elementary'):
                                strengths.append(f"Assigned to {get_display_school_name(school_info.elementary)}, {get_display_school_name(school_info.middle)}, {get_display_school_name(school_info.high)}")

                        # Safety strengths
                        if result.get('crime_analysis'):
                            crime = result['crime_analysis']
                            if hasattr(crime, 'safety_score') and crime.safety_score:
                                if crime.safety_score.score >= 80:
                                    strengths.append(f"Very safe area (Safety Score: {crime.safety_score.score}/100)")
                                elif crime.safety_score.score >= 60:
                                    strengths.append(f"Safe area (Safety Score: {crime.safety_score.score}/100)")
                                if hasattr(crime, 'trends') and crime.trends and crime.trends.trend == "decreasing":
                                    strengths.append(f"Crime trending down ({crime.trends.change_percentage:+.1f}%)")

                        # Zoning strengths
                        if result.get('nearby_zoning'):
                            nearby_zoning = result['nearby_zoning']
                            if hasattr(nearby_zoning, 'residential_only') and nearby_zoning.residential_only:
                                strengths.append("Residential neighborhood with uniform zoning")

                        if strengths:
                            for strength in strengths[:5]:
                                st.markdown(f"• {strength}")
                        else:
                            st.markdown("*See detailed analysis below*")

                    with insights_col2:
                        st.markdown("**⚠️ Things to Consider:**")
                        considerations = []

                        # Safety considerations
                        if result.get('crime_analysis'):
                            crime = result['crime_analysis']
                            if hasattr(crime, 'safety_score') and crime.safety_score and crime.safety_score.score < 60:
                                considerations.append(f"Safety score below 60 ({crime.safety_score.score}/100)")
                            if hasattr(crime, 'statistics') and crime.statistics:
                                if hasattr(crime.statistics, 'violent_count') and crime.statistics.violent_count > 10:
                                    considerations.append(f"{crime.statistics.violent_count} violent crimes reported")
                            if hasattr(crime, 'trends') and crime.trends and crime.trends.trend == "increasing":
                                considerations.append(f"Crime trending up ({crime.trends.change_percentage:+.1f}%)")

                        # Zoning considerations
                        if result.get('nearby_zoning'):
                            nearby_zoning = result['nearby_zoning']
                            if hasattr(nearby_zoning, 'mixed_use_nearby') and nearby_zoning.mixed_use_nearby:
                                considerations.append("Mixed-use zoning nearby")
                            if hasattr(nearby_zoning, 'potential_concerns') and nearby_zoning.potential_concerns:
                                for concern in nearby_zoning.potential_concerns[:2]:
                                    considerations.append(concern)

                        if considerations:
                            for consideration in considerations[:5]:
                                st.markdown(f"• {consideration}")
                        else:
                            st.markdown("*No major concerns identified*")

                    st.markdown("")  # Spacing

                    # Three AI Analysis Boxes (replacing all detailed visualizations)

                    # 1. Crime & Safety Analysis Box - Combined
                    crime_content = ""
                    if result.get('crime_response'):
                        crime_content = result['crime_response']
                    elif result.get('crime_analysis'):
                        crime = result['crime_analysis']
                        if hasattr(crime, 'safety_score') and crime.safety_score:
                            crime_content = f"<strong>Safety Score:</strong> {crime.safety_score.score}/100 ({crime.safety_score.level})<br><br>Crime analysis data is available for this address."
                        else:
                            crime_content = "Crime analysis data is available for this address."
                    else:
                        crime_content = "Crime data is not available for this address."

                    st.markdown(f"""
                    <div style="border-left: 4px solid #ef4444; padding: 1.5em; margin: 1.5em 0; background-color: #fef2f2; border-radius: 0.5em;">
                        <h3 style="margin-top: 0; color: #991b1b;">🛡️ Crime & Safety Analysis</h3>
                        <div style="background-color: #f8fafc; padding: 1em; border-radius: 0.3em; margin-top: 1em;">
                            {crime_content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. School Analysis Box - Combined
                    school_content = ""
                    if result.get('school_response'):
                        school_content = result['school_response']
                    elif result.get('school_info'):
                        school_info = result['school_info']
                        if hasattr(school_info, 'elementary'):
                            school_content = f"<strong>Assigned Schools:</strong><br>• Elementary: {get_display_school_name(school_info.elementary)}<br>• Middle: {get_display_school_name(school_info.middle)}<br>• High: {get_display_school_name(school_info.high)}<br><br>School performance data is available for detailed analysis."
                        else:
                            school_content = "School data is available for this address."
                    else:
                        school_content = "School data is not available for this address."

                    st.markdown(f"""
                    <div style="border-left: 4px solid #3b82f6; padding: 1.5em; margin: 1.5em 0; background-color: #eff6ff; border-radius: 0.5em;">
                        <h3 style="margin-top: 0; color: #1e40af;">🎓 School Analysis</h3>
                        <div style="background-color: #f8fafc; padding: 1em; border-radius: 0.3em; margin-top: 1em;">
                            {school_content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # School Performance Analysis Section
                    if result.get('school_info'):
                        school_info = result['school_info']
                        st.markdown("#### 📊 School Performance Analysis")

                        # Get GOSA data loader
                        gosa_loader = get_gosa_loader()

                        # Analyze each assigned school
                        schools_to_analyze = [
                            ("Elementary", get_display_school_name(school_info.elementary)),
                            ("Middle", get_display_school_name(school_info.middle)),
                            ("High", get_display_school_name(school_info.high))
                        ]

                        for school_level, school_name in schools_to_analyze:
                            perf_data = get_school_performance_for_analysis(school_name)

                            if perf_data:
                                with st.expander(f"📈 {school_name} Performance", expanded=False):
                                    # Create Plotly line chart of proficiency over time
                                    years_data = perf_data.get('years', {})

                                    if years_data and len(years_data) > 0:
                                        # Prepare data for line chart
                                        years_sorted = sorted(years_data.items())
                                        chart_df = pd.DataFrame({
                                            'School Year': [y[0] for y in years_sorted],
                                            'Average Proficiency (%)': [y[1] for y in years_sorted]
                                        })

                                        # Create Plotly Express line chart
                                        fig = px.line(
                                            chart_df,
                                            x='School Year',
                                            y='Average Proficiency (%)',
                                            markers=True,
                                            title=f'{school_name} - Proficiency Over Time'
                                        )

                                        # Add dashed horizontal line at y=45 for state average
                                        fig.add_hline(
                                            y=45,
                                            line_dash="dash",
                                            line_color="red",
                                            annotation_text="State Average (45%)",
                                            annotation_position="top right"
                                        )

                                        # Update layout
                                        fig.update_layout(
                                            yaxis_range=[0, 100],
                                            height=350,
                                            margin=dict(l=20, r=20, t=40, b=20)
                                        )

                                        # TODO: After Dec 31, 2025 - Replace use_container_width with new Streamlit parameter
                                        # See: https://docs.streamlit.io for updated syntax
                                        st.plotly_chart(fig, use_container_width=True)

                                    # Show key metrics
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Average Proficiency", f"{perf_data['avg_proficiency']:.1f}%")
                                    with col2:
                                        st.metric("Students Tested", f"{perf_data['total_tested']:,}")

                                    # Show high school metrics if available
                                    if perf_data.get('is_high_school'):
                                        st.markdown("**High School Metrics:**")
                                        hs_cols = st.columns(4)
                                        if perf_data.get('graduation_rate'):
                                            hs_cols[0].metric("Graduation Rate", f"{perf_data['graduation_rate']:.1f}%")
                                        if perf_data.get('sat_total'):
                                            hs_cols[1].metric("Avg SAT", f"{perf_data['sat_total']:.0f}")
                                        if perf_data.get('act_composite'):
                                            hs_cols[2].metric("Avg ACT", f"{perf_data['act_composite']:.1f}")
                                        if perf_data.get('hope_eligibility_pct'):
                                            hs_cols[3].metric("HOPE Eligible", f"{perf_data['hope_eligibility_pct']:.1f}%")

                                    # Generate AI analysis
                                    if api_key:
                                        import json
                                        # Serialize perf_data for caching
                                        perf_data_str = json.dumps(perf_data, default=str)

                                        with st.spinner("Generating analysis..."):
                                            analysis = get_cached_school_analysis(
                                                school_name,
                                                perf_data_str,
                                                api_key
                                            )

                                        st.markdown("**AI Analysis:**")
                                        st.write(analysis)
                            else:
                                with st.expander(f"📈 {school_name} Performance", expanded=False):
                                    st.info(f"Performance data not available for {school_name}.")

                    # 3. Zoning Analysis Box - Combined header and content
                    # Generate narrative zoning analysis
                    zoning_narrative = ""

                    # Check for nearby zoning (more comprehensive)
                    if result.get('nearby_zoning'):
                        nearby = result['nearby_zoning']
                        if hasattr(nearby, 'current_parcel') and nearby.current_parcel:
                            parcel = nearby.current_parcel

                            # Build narrative analysis
                            if hasattr(parcel, 'current_zoning'):
                                zoning_code = parcel.current_zoning
                                zoning_desc = getattr(parcel, 'current_zoning_description', '')

                                zoning_narrative += f"This property is currently zoned as <strong>{zoning_code}</strong> ({zoning_desc}). "

                            # Future land use narrative
                            if hasattr(parcel, 'future_land_use') and parcel.future_land_use:
                                future_use = parcel.future_land_use
                                future_desc = getattr(parcel, 'future_land_use_description', '')
                                zoning_narrative += f"According to the comprehensive land use plan, this area is designated for <strong>{future_use}</strong> ({future_desc}). "

                            # Neighborhood context narrative
                            if hasattr(nearby, 'zone_diversity_score'):
                                diversity_pct = nearby.zone_diversity_score * 100
                                if nearby.zone_diversity_score < 0.03:
                                    zoning_narrative += "The surrounding neighborhood shows <strong>low zoning diversity</strong>, indicating a uniform residential character with consistent development patterns. "
                                elif nearby.zone_diversity_score < 0.06:
                                    zoning_narrative += "The neighborhood has <strong>moderate zoning diversity</strong>, with a mix of different residential types creating varied housing options. "
                                else:
                                    zoning_narrative += "This area shows <strong>high zoning diversity</strong>, suggesting a transitional neighborhood with mixed uses and varying development styles. "

                            # Nearby parcels context
                            if hasattr(nearby, 'total_nearby_parcels') and hasattr(nearby, 'unique_zones'):
                                zoning_narrative += f"Our analysis of <strong>{nearby.total_nearby_parcels} nearby parcels</strong> (within 250 meters) found <strong>{len(nearby.unique_zones)} different zoning classifications</strong>, "
                                if nearby.residential_only if hasattr(nearby, 'residential_only') else False:
                                    zoning_narrative += "all of which are residential in nature. "
                                else:
                                    zoning_narrative += "indicating a mixed-use environment. "

                            # Concerns or considerations
                            if hasattr(nearby, 'potential_concerns') and nearby.potential_concerns:
                                zoning_narrative += "<br><br><strong>Important Considerations:</strong><br>"
                                for concern in nearby.potential_concerns:
                                    zoning_narrative += f"• {concern}<br>"

                            if hasattr(parcel, 'split_zoned') and parcel.split_zoned:
                                zoning_narrative += "<br>⚠️ <strong>Note:</strong> This property has split zoning, meaning different zoning regulations may apply to different portions of the lot. Be sure to verify specific restrictions with the Planning Department. "

                    # Fallback to basic zoning info with narrative
                    elif result.get('zoning_info'):
                        zoning = result['zoning_info']
                        if hasattr(zoning, 'current_zoning'):
                            zoning_code = zoning.current_zoning
                            zoning_desc = getattr(zoning, 'current_zoning_description', '')
                            zoning_narrative += f"This property is currently zoned as <strong>{zoning_code}</strong> ({zoning_desc}). "

                        if hasattr(zoning, 'future_land_use') and zoning.future_land_use:
                            future_use = zoning.future_land_use
                            future_desc = getattr(zoning, 'future_land_use_description', '')
                            zoning_narrative += f"The comprehensive land use plan designates this area for <strong>{future_use}</strong> ({future_desc}). "

                    # Display combined header and content in single box
                    if not zoning_narrative:
                        zoning_narrative = "Zoning data is not available for this address. This may occur if the property is outside the Athens-Clarke County planning jurisdiction or if the address could not be geocoded."

                    st.markdown(f"""
                    <div style="border-left: 4px solid #10b981; padding: 1.5em; margin: 1.5em 0; background-color: #f0fdf4; border-radius: 0.5em;">
                        <h3 style="margin-top: 0; color: #065f46;">🏗️ Zoning Analysis</h3>
                        <div style="background-color: #f8fafc; padding: 1em; border-radius: 0.3em; margin-top: 1em;">
                            {zoning_narrative}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Development Probability Analysis
                    current_zoning = None
                    future_land_use = None

                    # Extract zoning data from nearby_zoning or zoning_info
                    if result.get('nearby_zoning') and hasattr(result['nearby_zoning'], 'current_parcel'):
                        parcel = result['nearby_zoning'].current_parcel
                        if parcel:
                            current_zoning = getattr(parcel, 'current_zoning', None)
                            future_land_use = getattr(parcel, 'future_land_use', None)
                    elif result.get('zoning_info'):
                        zoning = result['zoning_info']
                        current_zoning = getattr(zoning, 'current_zoning', None)
                        future_land_use = getattr(zoning, 'future_land_use', None)

                    if current_zoning and future_land_use:
                        dev_score = calculate_development_probability(current_zoning, future_land_use)
                        risk_level = classify_risk_level(dev_score)
                        interpretation = generate_development_interpretation(
                            current_zoning, future_land_use, dev_score, risk_level
                        )

                        # Color based on risk level
                        if risk_level == "Low":
                            risk_color = "#22c55e"  # Green
                            bg_color = "#f0fdf4"
                        elif risk_level == "Moderate":
                            risk_color = "#eab308"  # Yellow
                            bg_color = "#fefce8"
                        elif risk_level == "High":
                            risk_color = "#f97316"  # Orange
                            bg_color = "#fff7ed"
                        else:  # Very High
                            risk_color = "#ef4444"  # Red
                            bg_color = "#fef2f2"

                        st.markdown(f"""
                        <div style="border-left: 4px solid {risk_color}; padding: 1.5em; margin: 1.5em 0; background-color: {bg_color}; border-radius: 0.5em;">
                            <h3 style="margin-top: 0; color: #374151;">🔮 Development Probability Analysis</h3>
                            <div style="font-size: 1.2em; margin: 0.5em 0;">
                                <strong>Development Risk Score:</strong>
                                <span style="color: {risk_color}; font-weight: bold;">{dev_score}/100</span>
                                <span style="background-color: {risk_color}; color: white; padding: 0.2em 0.6em; border-radius: 0.3em; margin-left: 0.5em; font-size: 0.85em;">{risk_level}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Display interpretation with proper markdown
                        st.markdown(interpretation)

                    # AI Synthesis Section - Comprehensive property analysis
                    if result.get('synthesis'):
                        st.markdown("""
                        <div style="background-color: #faf5ff; border-left: 4px solid #8b5cf6; padding: 1.5em; margin: 1.5em 0; border-radius: 0.5em;">
                            <h3 style="margin-top: 0; color: #6d28d9;">🤖 AI Property Analysis</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        # Display the synthesis with proper markdown rendering
                        st.markdown(result['synthesis'])

                    st.markdown("---")  # Divider before data sources

                    # Skip all the old detailed visualizations - go straight to data sources
                    # (Old school metrics, crime charts, zoning details are removed)

                    if False:  # OLD CODE - keeping for reference but not executing
                        # Old detailed visualization code was here
                        pass

                    # All detailed visualizations have been replaced by the three simple AI boxes above
                    # Old visualization code has been removed

                    # DATA SOURCES SECTION BELOW

                    # (Skipping old detailed visualizations - they've been replaced by the three AI boxes above)

                    # Note: If you see this comment, the old visualization code between here and
                    # the Data Sources section should be removed. The new simplified layout only
                    # shows the three AI analysis boxes above.

                    # All old visualization code removed
                    # Jump directly to old AI Analysis section (which we'll also remove)

                    if False:  # OLD VISUALIZATION CODE - disabled completely
                        crime = result['crime_analysis']

                        try:
                            # Validate required attributes before displaying
                            missing_attrs = []

                            # Check top-level attributes
                            if not hasattr(crime, 'safety_score'):
                                missing_attrs.append('safety_score')
                            elif crime.safety_score is not None:
                                # Check safety_score sub-attributes
                                if not hasattr(crime.safety_score, 'score'):
                                    missing_attrs.append('safety_score.score')
                                if not hasattr(crime.safety_score, 'level'):
                                    missing_attrs.append('safety_score.level')

                            if not hasattr(crime, 'statistics'):
                                missing_attrs.append('statistics')
                            if not hasattr(crime, 'trends'):
                                missing_attrs.append('trends')

                            if missing_attrs:
                                st.warning(f"""
                                ⚠️ **Crime data was retrieved but some metrics are unavailable**

                                Missing: {', '.join(missing_attrs)}

                                The crime analysis may be incomplete. Try refreshing or contact support if this persists.
                                """)
                            else:
                                # Color-coded header based on safety score
                                safety_color = get_safety_color(crime.safety_score.score)
                                st.markdown(f"""
                                <div style="background-color: {safety_color}20; border-left: 4px solid {safety_color}; padding: 1em; border-radius: 0.5em; margin: 1em 0;">
                                    <h3 style="color: {safety_color}; margin: 0;">🛡️ Crime & Safety Analysis</h3>
                                </div>
                                """, unsafe_allow_html=True)

                                # Safety gauge and key metrics
                                col1, col2 = st.columns([1, 2])

                                with col1:
                                    # Safety score visual
                                    safety_html = create_safety_score_html(crime.safety_score.score, crime.safety_score.level)
                                    st.markdown(safety_html, unsafe_allow_html=True)

                                with col2:
                                    # Key statistics table
                                    stats_table = format_crime_stats_table(crime)

                                    # Overview
                                    st.markdown("**Overview:**")
                                    for key, value in stats_table['Overview'].items():
                                        st.markdown(f"• {key}: **{value}**")

                                    # Most common crime
                                    st.markdown(f"• Most Common: **{crime.statistics.most_common_crime}** ({crime.statistics.most_common_count} incidents)")

                                st.markdown("")  # Spacing

                                # Charts in tabs for better mobile experience
                                tab1, tab2, tab3 = st.tabs(["📊 By Category", "📈 Trends", "⚖️ Comparison"])

                                with tab1:
                                    category_data = create_category_chart_data(crime)
                                    # Get colors in the same order as DataFrame columns
                                    colors = get_category_colors()
                                    color_list = [colors['Violent'], colors['Property'], colors['Traffic'], colors['Other']]
                                    st.bar_chart(category_data, color=color_list)

                                    # Show percentages below chart
                                    col_a, col_b, col_c, col_d = st.columns(4)
                                    with col_a:
                                        st.metric("Violent", f"{crime.statistics.violent_percentage:.1f}%")
                                    with col_b:
                                        st.metric("Property", f"{crime.statistics.property_percentage:.1f}%")
                                    with col_c:
                                        st.metric("Traffic", f"{crime.statistics.traffic_percentage:.1f}%")
                                    with col_d:
                                        st.metric("Other", f"{crime.statistics.other_percentage:.1f}%")

                                with tab2:
                                    trend_data = create_trend_chart_data(crime)
                                    st.bar_chart(trend_data)

                                    # Show trend details
                                    trend_color = "green" if crime.trends.trend == "decreasing" else "red" if crime.trends.trend == "increasing" else "gray"
                                    trend_symbol = "📉" if crime.trends.trend == "decreasing" else "📈" if crime.trends.trend == "increasing" else "➡️"

                                    st.markdown(f"""
                                    <div style="text-align: center; padding: 1em; background: {trend_color}20; border-radius: 0.5em; margin-top: 1em;">
                                        <div style="font-size: 1.5em;">{trend_symbol}</div>
                                        <div style="font-weight: 600; color: {trend_color};">
                                            {crime.trends.trend.title()}: {crime.trends.change_percentage:+.1f}%
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                with tab3:
                                    comparison_html = create_comparison_html(crime)
                                    if comparison_html:
                                        st.markdown(comparison_html, unsafe_allow_html=True)
                                    else:
                                        st.info("Comparison data not available")

                        except (AttributeError, KeyError, TypeError) as e:
                            st.error(f"""
                            ❌ **Error displaying crime data**

                            The crime data structure may have changed or is incomplete.

                            **Technical details:** {str(e)}

                            **What you can do:**
                            - Try searching again
                            - Try a different address
                            - Check that the crime data API is accessible

                            Other sections (schools, zoning) should still be available below.
                            """)

                        # Crime summary box at end of section
                        try:
                            if hasattr(crime, 'safety_score') and crime.safety_score and \
                               hasattr(crime, 'statistics') and crime.statistics and \
                               hasattr(crime, 'trends') and crime.trends:

                                # Determine safety icon based on score
                                if crime.safety_score.score >= 80:
                                    safety_icon = "✅"
                                elif crime.safety_score.score >= 60:
                                    safety_icon = "✓"
                                else:
                                    safety_icon = "⚠️"

                                summary_text = f"""{safety_icon} **Quick Summary:** This area scored **{crime.safety_score.score}/100** for safety ({crime.safety_score.level.lower()}), with **{crime.statistics.total_incidents}** reported incidents in the past year. Crime is **{crime.trends.trend}** ({crime.trends.change_percentage:+.1f}%). Read on for what these numbers really mean."""

                                if hasattr(crime.statistics, 'violent_count') and crime.statistics.violent_count > 0:
                                    summary_text += f" • **{crime.statistics.violent_count}** violent crimes"

                                # Use success if safe, warning if concerning
                                if crime.safety_score.score >= 60:
                                    st.success(summary_text)
                                else:
                                    st.warning(summary_text)

                        except (AttributeError, KeyError, TypeError):
                            pass  # Skip summary if data incomplete

                    # OLD zoning display - disabled (now shown in the new Zoning Analysis box above)
                    if False and include_zoning:
                        try:
                            # Check if we have any zoning data
                            if not result.get('zoning_info') and not result.get('nearby_zoning'):
                                st.warning("⚠️ **Zoning data could not be retrieved for this address**")
                            else:
                                # Check if we have comprehensive nearby zoning analysis
                                nearby_zoning = result.get('nearby_zoning')

                                # Validate nearby_zoning has required attributes
                                use_nearby = False
                                if nearby_zoning is not None:
                                    required_attrs = ['current_parcel', 'nearby_parcels', 'zone_diversity_score',
                                                     'total_nearby_parcels', 'unique_zones']
                                    missing_attrs = [attr for attr in required_attrs if not hasattr(nearby_zoning, attr)]

                                    if missing_attrs:
                                        st.info(f"""
                                        ℹ️ **Nearby zoning analysis incomplete** (missing: {', '.join(missing_attrs)})

                                        Showing basic zoning information instead.
                                        """)
                                    else:
                                        use_nearby = True

                                if use_nearby:
                                    # Comprehensive nearby zoning display
                                    st.markdown("### 🏗️ Zoning & Land Use")

                                    # Current parcel info
                                    if nearby_zoning.current_parcel:
                                        col1, col2, col3 = st.columns(3)

                                        with col1:
                                            st.metric("Current Zoning", nearby_zoning.current_parcel.current_zoning)
                                            st.caption(nearby_zoning.current_parcel.current_zoning_description)

                                        with col2:
                                            if nearby_zoning.current_parcel.future_land_use:
                                                st.metric("Future Land Use", nearby_zoning.current_parcel.future_land_use)
                                                st.caption(nearby_zoning.current_parcel.future_land_use_description or "")
                                            else:
                                                st.metric("Future Land Use", "Not Available")

                                        with col3:
                                            # Show diversity score with color coding
                                            diversity_pct = nearby_zoning.zone_diversity_score * 100
                                            if nearby_zoning.zone_diversity_score < 0.03:
                                                diversity_label = "Low (Uniform)"
                                                diversity_color = "🟢"
                                            elif nearby_zoning.zone_diversity_score < 0.06:
                                                diversity_label = "Moderate (Mixed)"
                                                diversity_color = "🟡"
                                            else:
                                                diversity_label = "High (Transitional)"
                                                diversity_color = "🟠"

                                            st.metric("Area Diversity", f"{diversity_pct:.1f}%")
                                            st.caption(f"{diversity_color} {diversity_label}")

                                    # Neighborhood summary
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Parcels Analyzed", nearby_zoning.total_nearby_parcels)
                                    with col2:
                                        st.metric("Unique Zones", len(nearby_zoning.unique_zones))
                                    with col3:
                                        if nearby_zoning.residential_only:
                                            st.metric("Neighborhood Type", "Residential Only")
                                        elif nearby_zoning.mixed_use_nearby:
                                            st.metric("Neighborhood Type", "Mixed Use")
                                        else:
                                            st.metric("Neighborhood Type", "Varied")

                                    # Show concerns if any
                                    if nearby_zoning.potential_concerns:
                                        st.warning("**⚠️ Zoning Considerations:**")
                                        for concern in nearby_zoning.potential_concerns:
                                            st.write(f"• {concern}")

                                    # Warnings and notes from current parcel
                                    if nearby_zoning.current_parcel:
                                        if nearby_zoning.current_parcel.split_zoned:
                                            st.info("📋 This property has split zoning - different regulations may apply to different parts")

                                        if nearby_zoning.current_parcel.future_changed:
                                            st.info("📝 The future land use plan has been updated/changed")

                                    # Expandable detailed view
                                    with st.expander("📊 Detailed Neighborhood Zoning Analysis"):
                                        # Show zoning distribution
                                        zoning_counts = Counter(p.current_zoning for p in nearby_zoning.nearby_parcels if p.current_zoning)

                                        st.write("**Zoning Distribution (250m radius):**")
                                        for code, count in zoning_counts.most_common():
                                            pct = (count / nearby_zoning.total_nearby_parcels) * 100 if nearby_zoning.total_nearby_parcels > 0 else 0
                                            # Get description for this code
                                            description = get_zoning_code_description(code)
                                            st.write(f"- **{code}**: {description}")
                                            st.write(f"  {count} parcels ({pct:.1f}%)")

                                        # Pattern summary
                                        st.write("")
                                        st.write("**Neighborhood Patterns:**")
                                        if nearby_zoning.residential_only:
                                            st.write("✓ Residential only - all nearby parcels are residential")

                                        # Check for commercial nearby with fallback
                                        if hasattr(nearby_zoning, 'commercial_nearby') and nearby_zoning.commercial_nearby:
                                            st.write("• Commercial/mixed-use parcels present nearby")
                                        elif nearby_zoning.mixed_use_nearby:
                                            st.write("• Mixed-use parcels present nearby")

                                        # Check for industrial nearby
                                        if hasattr(nearby_zoning, 'industrial_nearby') and nearby_zoning.industrial_nearby:
                                            st.write("⚠️ Industrial zoning nearby")

                                    # Summary at end of zoning section
                                    if nearby_zoning.current_parcel:
                                        summary_parts = []
                                        summary_parts.append(f"**Current Zoning:** {nearby_zoning.current_parcel.current_zoning}")

                                        # Add diversity assessment
                                        diversity_pct = nearby_zoning.zone_diversity_score * 100
                                        if nearby_zoning.zone_diversity_score < 0.03:
                                            summary_parts.append("**Neighborhood:** Uniform")
                                        elif nearby_zoning.zone_diversity_score < 0.06:
                                            summary_parts.append("**Neighborhood:** Mixed")
                                        else:
                                            summary_parts.append("**Neighborhood:** Transitional")

                                        # Add concerns summary
                                        if nearby_zoning.potential_concerns:
                                            summary_parts.append(f"**⚠️ {len(nearby_zoning.potential_concerns)} concern(s)**")
                                        else:
                                            summary_parts.append("**✓ No concerns**")

                                        st.info(f"""📋 **Quick Summary:** {' • '.join(summary_parts)}""")

                                elif result.get('zoning_info'):
                                    # Fallback to basic zoning display
                                    zoning = result['zoning_info']

                                    st.markdown("### 🏗️ Zoning & Land Use")

                                    # Key metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Current Zoning", zoning.current_zoning)
                                    with col2:
                                        st.metric("Future Land Use", zoning.future_land_use)
                                    with col3:
                                        st.metric("Property Size", f"{zoning.acres:.2f} acres")

                                    # Descriptions
                                    st.markdown(f"**{zoning.current_zoning_description}**")
                                    st.markdown(f"**Future:** {zoning.future_land_use_description}")

                                    # Warnings and notes
                                    if zoning.split_zoned:
                                        st.warning("⚠️ This property has split zoning - different zoning designations apply to different parts of the property")

                                    if zoning.future_changed:
                                        st.info("📝 The future land use plan has been updated/changed from the original comprehensive plan")

                                    # Nearby context
                                    if zoning.nearby_zones:
                                        nearby_text = ", ".join(zoning.nearby_zones)
                                        st.markdown(f"**Nearby Zoning:** {nearby_text}")
                                        st.caption("Understanding nearby zoning helps gauge neighborhood character and development patterns")

                        except (AttributeError, KeyError, TypeError) as e:
                            st.error(f"""
                            ❌ **Error displaying zoning data**

                            The zoning data structure may have changed or is incomplete.

                            **Technical details:** {str(e)}

                            **What you can do:**
                            - Try searching again
                            - Try a different address
                            - Contact ACC Planning Department at (706) 613-3515 for official zoning information

                            Other sections (schools, crime) should still be available.
                            """)

                    # Duplicate Key Insights and AI Analysis sections removed
                    # All analysis is now shown in the three colored boxes above

                    # Data sources
                    with st.expander("📚 Data Sources & Verification"):
                        sources_text = ""

                        if include_schools:
                            sources_text += """
**School Data:**
- Assignments: Clarke County Schools Official Street Index (2024-25)
- Performance: Georgia Governor's Office of Student Achievement (GOSA 2023-24)
- Verify: [clarke.k12.ga.us/page/school-attendance-zones](https://www.clarke.k12.ga.us/page/school-attendance-zones)
"""

                        if include_crime:
                            sources_text += """
**Crime & Safety Data:**
- Source: Athens-Clarke County Police Department
- Coverage: Last 12 months within 0.5 mile radius
- View crime map: [Athens-Clarke Crime Map](https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime)
"""

                        if include_zoning:
                            sources_text += """
**Zoning & Land Use Data:**
- Source: Athens-Clarke County Planning Department GIS
- Current zoning codes and future land use comprehensive plan
- View zoning map: [Athens-Clarke GIS Portal](https://enigma.accgov.com/)
- Verify: Contact Planning Department at (706) 613-3515
"""

                        sources_text += """
**Important Notes:**
- All data from official public sources
- School zones, crime patterns, and zoning regulations can change over time
- This is for research purposes only - always verify independently
- Visit neighborhoods in person and talk to local residents
- For zoning questions, consult with the Planning Department before making property decisions
"""

                        st.markdown(sources_text)

                    # Option to see raw data
                    with st.expander("📊 View Complete Raw Data"):
                        if include_schools and result['school_info']:
                            st.markdown("**School Data:**")
                            st.text(format_complete_report(result['school_info']))

                        if include_crime and result['crime_analysis']:
                            st.markdown("**Crime Data:**")
                            st.text(format_analysis_report(result['crime_analysis']))

                        if include_zoning:
                            st.markdown("**Zoning Data:**")
                            # Show comprehensive nearby zoning report if available
                            if result.get('nearby_zoning'):
                                st.text(format_nearby_zoning_report(result['nearby_zoning']))
                            elif result.get('zoning_info'):
                                st.text(format_zoning_report(result['zoning_info']))

                except Exception as e:
                    error_str = str(e)
                    st.error(f"""
                    ❌ **Unexpected Error**

                    {error_str}

                    **What you can do:**
                    - Verify your address is in Athens-Clarke County, GA
                    - Try a simpler address format (e.g., "150 Hancock Avenue, Athens, GA")
                    - Check if the address exists on Google Maps
                    - Try selecting only one analysis type (Schools OR Crime)
                    - Test with a known working address: 150 Hancock Avenue, Athens, GA 30601

                    If the problem continues, this might be a temporary system issue. Try again in a few minutes.
                    """)

                    # Show technical details in expander for debugging
                    with st.expander("🔧 Technical Details (for debugging)"):
                        st.code(traceback.format_exc())

# Footer with disclaimer
st.markdown("""
<div class="footer">
    <p><strong>NewCo Real Estate Chatbot (Beta)</strong></p>
    <p>Powered by Claude AI • Data from Clarke County Schools, Georgia GOSA, Athens-Clarke Police, & ACC Planning Dept</p>
    <p>⚠️ <strong>Disclaimer:</strong> Data from public sources. Always verify important information independently and visit neighborhoods in person. School zones, performance data, crime statistics, and zoning regulations can change over time.</p>
    <p>Not affiliated with Clarke County School District, Georgia DOE, or Athens-Clarke County Government</p>
    <p>For research and informational purposes only • Always verify independently</p>
</div>
""", unsafe_allow_html=True)
