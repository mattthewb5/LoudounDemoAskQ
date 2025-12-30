#!/usr/bin/env python3
"""
Unified AI Assistant for Athens Home Buyer Research
Combines school and crime analysis for comprehensive neighborhood insights
"""

import os
from typing import Optional
from datetime import datetime
from school_info import get_school_info, CompleteSchoolInfo
from crime_analysis import analyze_crime_near_address, CrimeAnalysis
from zoning_lookup import get_zoning_info, get_nearby_zoning, ZoningInfo, NearbyZoning
from ai_school_assistant import SchoolAIAssistant
from crime_ai_assistant import CrimeAIAssistant


# School phone numbers for Clarke County Schools
SCHOOL_PHONE_NUMBERS = {
    "Oglethorpe Avenue Elementary": "(706) 546-7501",
    "Barrow Elementary": "(706) 546-7504",
    "Barnett Shoals Elementary": "(706) 546-7507",
    "Chase Street Elementary": "(706) 546-7510",
    "Cleveland Road Elementary": "(706) 546-7513",
    "Fowler Drive Elementary": "(706) 546-7516",
    "Gaines Elementary": "(706) 546-7519",
    "Howard B. Stroud Elementary": "(706) 546-7522",
    "J.J. Harris Elementary": "(706) 546-7525",
    "Timothy Road Elementary": "(706) 546-7534",
    "Whit Davis Elementary": "(706) 546-7537",
    "Winterville Elementary": "(706) 546-7540",
    "Burney-Harris-Lyons Middle": "(706) 546-7528",
    "Clarke Middle": "(706) 546-7543",
    "Coile Middle": "(706) 546-7546",
    "Hilsman Middle": "(706) 546-7531",
    "Clarke Central High": "(706) 546-7549",
    "Cedar Shoals High": "(706) 546-7552",
    "Classic City High": "(706) 546-7555",
}


def get_school_phone(school_name: str) -> str:
    """Get phone number for a school by partial name match."""
    if not school_name:
        return "(706) 546-7721"  # District office fallback
    school_name_lower = school_name.lower()
    for name, phone in SCHOOL_PHONE_NUMBERS.items():
        if name.lower() in school_name_lower or school_name_lower in name.lower():
            return phone
    return "(706) 546-7721"  # District office fallback


class UnifiedAIAssistant:
    """
    Unified assistant that provides comprehensive neighborhood analysis
    combining schools, crime, and synthesized insights
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize unified assistant

        Args:
            api_key: Anthropic API key (will use ANTHROPIC_API_KEY env var if not provided)
        """
        if api_key is None:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set environment variable.")

        self.api_key = api_key
        self.school_assistant = SchoolAIAssistant(api_key=api_key)
        self.crime_assistant = CrimeAIAssistant(api_key=api_key)

    def get_comprehensive_analysis(
        self,
        address: str,
        question: str,
        include_schools: bool = True,
        include_crime: bool = True,
        include_zoning: bool = True,
        radius_miles: float = 0.5,
        months_back: int = 12
    ) -> dict:
        """
        Get comprehensive analysis combining schools, crime, and zoning data

        Args:
            address: Street address in Athens-Clarke County
            question: User's question about the area
            include_schools: Whether to include school analysis
            include_crime: Whether to include crime analysis
            include_zoning: Whether to include zoning information
            radius_miles: Search radius for crime data (default: 0.5 miles)
            months_back: Crime history period in months (default: 12)

        Returns:
            Dictionary with school_info, crime_analysis, zoning_info, and synthesis
        """
        result = {
            'address': address,
            'school_info': None,
            'crime_analysis': None,
            'zoning_info': None,
            'nearby_zoning': None,
            'school_response': None,
            'crime_response': None,
            'synthesis': None,
            'error': None
        }

        try:
            # Get school data if requested
            if include_schools:
                try:
                    school_info = get_school_info(address)
                    result['school_info'] = school_info

                    if school_info:
                        school_response = self.school_assistant.ask_claude_about_schools(
                            address, question
                        )
                        result['school_response'] = school_response
                except Exception as e:
                    result['error'] = f"School lookup error: {str(e)}"

            # Get crime data if requested
            if include_crime:
                try:
                    crime_analysis = analyze_crime_near_address(
                        address,
                        radius_miles=radius_miles,
                        months_back=months_back
                    )
                    result['crime_analysis'] = crime_analysis

                    if crime_analysis:
                        crime_response = self.crime_assistant.answer_crime_question(
                            address, question, radius_miles=radius_miles, months_back=months_back
                        )
                        result['crime_response'] = crime_response
                except Exception as e:
                    # Crime errors are less critical - address might not geocode
                    result['error'] = f"Crime analysis error: {str(e)}"

            # Get zoning data if requested
            if include_zoning:
                try:
                    print(f"🔍 Starting zoning lookup for: {address}")
                    # Use nearby zoning analysis for comprehensive insights
                    nearby_zoning = get_nearby_zoning(address, radius_meters=250)
                    if nearby_zoning and nearby_zoning.current_parcel:
                        # Store the basic zoning info for backward compatibility
                        result['zoning_info'] = nearby_zoning.current_parcel
                        # Also store the nearby analysis
                        result['nearby_zoning'] = nearby_zoning
                        print(f"✓ Zoning lookup successful (nearby analysis)")
                    else:
                        # Fallback to basic zoning if nearby analysis fails
                        print(f"⚠️ Nearby zoning failed, trying basic lookup...")
                        result['zoning_info'] = get_zoning_info(address)
                        if result['zoning_info']:
                            print(f"✓ Basic zoning lookup successful")
                        else:
                            print(f"❌ Basic zoning lookup failed")
                except Exception as e:
                    # Zoning errors are non-critical
                    print(f"❌ Zoning lookup error: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # Generate synthesis if we have data
            if result['school_info'] or result['crime_analysis'] or result['zoning_info']:
                print(f"📝 Generating AI synthesis...")
                print(f"   - School info: {'✓' if result['school_info'] else '✗'}")
                print(f"   - Crime analysis: {'✓' if result['crime_analysis'] else '✗'}")
                print(f"   - Zoning info: {'✓' if result['zoning_info'] else '✗'}")
                print(f"   - Nearby zoning: {'✓' if result.get('nearby_zoning') else '✗'}")

                synthesis = self._synthesize_insights(
                    address,
                    question,
                    result['school_info'],
                    result['crime_analysis'],
                    result['zoning_info'],
                    result.get('nearby_zoning')
                )
                result['synthesis'] = synthesis
                print(f"✓ AI synthesis complete")

            return result

        except Exception as e:
            result['error'] = f"Analysis error: {str(e)}"
            return result

    def _synthesize_insights(
        self,
        address: str,
        question: str,
        school_info: Optional[CompleteSchoolInfo],
        crime_analysis: Optional[CrimeAnalysis],
        zoning_info: Optional[ZoningInfo],
        nearby_zoning: Optional[NearbyZoning] = None
    ) -> str:
        """
        Synthesize insights across schools, crime, and zoning data

        Args:
            address: The address being analyzed
            question: User's original question
            school_info: School assignment and performance data (optional)
            crime_analysis: Crime statistics and safety analysis (optional)
            zoning_info: Zoning and land use information (optional)
            nearby_zoning: Nearby zoning analysis with concerns (optional)

        Returns:
            Synthesized response from Claude
        """
        # Format school data summary
        school_summary = ""
        if school_info:
            school_summary = f"""
SCHOOL ASSIGNMENTS:
- Elementary: {school_info.elementary}
- Middle: {school_info.middle}
- High: {school_info.high}

SCHOOL PERFORMANCE (where available):
"""
            # Helper function to format test scores with multi-year trends
            def format_test_scores_trend(perf, school_name: str) -> str:
                """Format test scores showing multi-year trends by subject"""
                if not perf or not perf.test_scores:
                    return f"\n{school_name}: Performance data not available\n"

                # Group scores by subject
                subjects = {}
                for score in perf.test_scores:
                    if score.subject not in subjects:
                        subjects[score.subject] = {}
                    subjects[score.subject][score.year] = score.total_proficient_pct

                if not subjects:
                    return f"\n{school_name}: Performance data not available\n"

                result = f"\n{school_name}:\n"
                for subject in sorted(subjects.keys()):
                    years_data = subjects[subject]
                    # Sort years chronologically
                    trend_parts = [f"{year}: {pct:.1f}%" for year, pct in sorted(years_data.items())]
                    result += f"- {subject}: {', '.join(trend_parts)}\n"

                return result

            if school_info.elementary_performance:
                school_summary += format_test_scores_trend(
                    school_info.elementary_performance,
                    f"Elementary School ({school_info.elementary})"
                )

            if school_info.middle_performance:
                school_summary += format_test_scores_trend(
                    school_info.middle_performance,
                    f"Middle School ({school_info.middle})"
                )

            if school_info.high_performance:
                high = school_info.high_performance
                school_summary += format_test_scores_trend(
                    high,
                    f"High School ({school_info.high})"
                )
                # Add graduation rate if available for high schools
                if high.graduation_rate:
                    school_summary += f"- Graduation Rate: {high.graduation_rate}%\n"

        # Format crime data summary
        crime_summary = ""
        if crime_analysis:
            crime_summary = f"""
CRIME & SAFETY ANALYSIS (last {crime_analysis.time_period_months} months, {crime_analysis.radius_miles} mile radius):

Safety Score: {crime_analysis.safety_score.score}/100 ({crime_analysis.safety_score.level})

Crime Statistics:
- Total Crimes: {crime_analysis.statistics.total_crimes}
- Crimes per Month: {crime_analysis.statistics.crimes_per_month:.1f}
- Violent Crimes: {crime_analysis.statistics.violent_count} ({crime_analysis.statistics.violent_percentage:.1f}%)
- Property Crimes: {crime_analysis.statistics.property_count} ({crime_analysis.statistics.property_percentage:.1f}%)

Crime Trends:
- Recent (last 6 months): {crime_analysis.trends.recent_count} crimes
- Previous (6-12 months ago): {crime_analysis.trends.previous_count} crimes
- Trend: {crime_analysis.trends.trend_description}
"""

            if crime_analysis.comparison:
                comp = crime_analysis.comparison
                crime_summary += f"""
Comparison to Athens Average:
- This Area: {comp.area_crime_count} crimes
- Athens Average: {comp.athens_average:.0f} crimes
- {comp.comparison_text}
- Assessment: {comp.relative_ranking}
"""

        # Format zoning data summary
        zoning_summary = ""
        print(f"🏗️ Formatting zoning data for AI...")
        print(f"   - zoning_info: {type(zoning_info)} - {zoning_info is not None}")
        print(f"   - nearby_zoning: {type(nearby_zoning)} - {nearby_zoning is not None}")

        if zoning_info:
            print(f"   ✓ Building zoning summary with code: {zoning_info.current_zoning}")
            zoning_summary = f"""
ZONING & LAND USE:

Current Zoning: {zoning_info.current_zoning}
- {zoning_info.current_zoning_description}

Future Land Use: {zoning_info.future_land_use}
- {zoning_info.future_land_use_description}

Property Size: {zoning_info.acres:.2f} acres ({int(zoning_info.acres * 43560)} square feet)
"""
            if zoning_info.split_zoned:
                zoning_summary += "\n⚠️  Property has split zoning\n"

            if zoning_info.future_changed:
                zoning_summary += "📝 Future land use plan has been updated/changed\n"

            # Add enhanced nearby zoning analysis if available
            if nearby_zoning:
                zoning_summary += f"""
NEIGHBORHOOD ZONING ANALYSIS (250m radius):
- Total nearby parcels: {nearby_zoning.total_nearby_parcels}
- Unique zoning types: {len(nearby_zoning.unique_zones)}
- Zone diversity score: {nearby_zoning.zone_diversity_score:.2f} (0.0=uniform, 1.0=highly diverse)
"""
                # Diversity interpretation
                if nearby_zoning.zone_diversity_score < 0.03:
                    zoning_summary += "  → Low diversity: Uniform, stable neighborhood character\n"
                elif nearby_zoning.zone_diversity_score < 0.06:
                    zoning_summary += "  → Moderate diversity: Mixed-use neighborhood\n"
                else:
                    zoning_summary += "  → High diversity: Transitional or evolving area\n"

                # Pattern flags
                if nearby_zoning.residential_only:
                    zoning_summary += "- Neighborhood character: Residential only\n"
                if nearby_zoning.commercial_nearby:
                    zoning_summary += "- Commercial/mixed-use parcels present nearby\n"
                if nearby_zoning.industrial_nearby:
                    zoning_summary += "- ⚠️  Industrial zoning nearby\n"

                # Concerns
                if nearby_zoning.potential_concerns:
                    zoning_summary += "\nPotential Zoning Concerns:\n"
                    for concern in nearby_zoning.potential_concerns:
                        zoning_summary += f"  • {concern}\n"
            elif zoning_info.nearby_zones:
                zoning_summary += f"\nNearby Zoning: {', '.join(zoning_info.nearby_zones)}\n"
        else:
            print(f"   ✗ No zoning_info provided - zoning_summary will be empty")

        print(f"   📏 Zoning summary length: {len(zoning_summary)} characters")
        if zoning_summary:
            print(f"   ✓ Zoning summary created successfully")
        else:
            print(f"   ⚠️ WARNING: Zoning summary is EMPTY - AI won't have zoning data!")

        # Create synthesis prompt with comprehensive instructions
        system_prompt = """You are a knowledgeable Athens-Clarke County real estate expert providing property analysis. You give direct, data-driven assessments without persona introductions or conversational filler. Your analysis is warm but professional, using relatable phrases that help people picture daily life."""

        user_prompt = f"""
Address: {address}
Their question: {question}

Available data:
{school_summary}

{crime_summary}

{zoning_summary}

=== OUTPUT INSTRUCTIONS ===

FORMAT RULES:
- Start your response directly with "## The Bottom Line" (no preamble, greeting, or introduction)
- No "Hey there" or "Thanks for asking" or "As a local expert..." - start immediately with the heading
- Every section heading uses ## followed by a blank line, then content
- Use markdown formatting throughout

WARM, PRACTICAL PHRASES:
Create vivid, relatable phrases that help people picture daily life in this neighborhood.
Use these examples as INSPIRATION for the style and tone, then generate YOUR OWN fresh
variations. Do not copy these verbatim - create new ones in the same spirit.

Example style for SAFETY/COMFORT (create your own like these):
- "feel comfortable letting the kids ride bikes around the neighborhood"
- "walk to the mailbox after dark without thinking twice"
- "leave packages on the porch without worry"
- "let the dog out without checking the street first"
- "go for an evening jog without mapping out 'safe routes'"
- "have the garage door open while doing yard work"
- "let your teenager walk home from a friend's house after dark"

Example style for COMMUNITY (create your own like these):
- "the kind of place where neighbors actually know each other's names"
- "wave to people on your morning walk and get a wave back"
- "the kind of street where someone notices if your trash cans sit out too long"
- "borrow a cup of sugar without feeling awkward"

Example style for SCHOOL CONCERNS (create your own like these):
- "most kids aren't hitting grade-level benchmarks"
- "you'd likely be supplementing with tutoring or considering alternatives"
- "the numbers suggest your child would need extra support outside school"

PHRASE RULES:
- Generate fresh phrases that feel natural and specific to THIS property
- Never use the same phrase twice in one analysis
- Make them practical things real people actually think about
- Vary the life situations referenced: parents, dog owners, joggers, remote workers, retirees, etc.
- These should feel like observations from someone who lives there, not marketing copy

=== SECTION STRUCTURE ===

## The Bottom Line

[3-4 sentences: Overall grade (A through F), key tradeoff, who it's for. Brief and punchy. State the grade clearly upfront.]

## What Stands Out

[2-3 sentences MAXIMUM - brief teaser of biggest positives and negatives. NO statistics, NO detailed data, NO percentages, NO specific numbers. Just identify what matters most, then say you'll break it down below.]

GOOD example: "Two things jump out immediately: the safety here is genuinely excellent, and the schools are a real weakness. I'll break down the specifics in each section below, but that's the core tradeoff you're weighing with this property."

BAD example (never do this): "Safety is great here - 87% less crime than Athens average, top 15% of neighborhoods, safety score of 80/100, just 3 incidents in 6 months. But schools are weak with only 41.4% proficiency..."

## The Safety Picture

[Full detail on safety - this is the ONLY place safety is discussed in depth. Include all safety statistics, scores, trends, and context HERE. Use warm phrases to help people picture daily life. Compare to Athens overall.]

## The Schools Story

[Full detail on schools - this is the ONLY place schools are discussed in depth. Include all proficiency rates, school names, graduation rates, CCRPI scores HERE. Explain what the numbers mean for daily life.]

=== SCHOOL PERFORMANCE TREND ANALYSIS ===

When discussing school performance, you MUST analyze the multi-year trends, not just cite current scores:

1. **Identify trends over 5 years** - Don't just cite current scores
   - Example: "Math proficiency declined from 62.5% (2018-19) to 51.6% (2023-24) - an 11-point drop"
   - Example: "English Language Arts has remained stable around 57-60% over 5 years"

2. **Comment on trajectory** - Is performance improving, declining, or stable?
   - For declining trends: Mention the concern and quantify the drop
   - For improving trends: Highlight the positive momentum
   - For stable trends: Note consistency

3. **Contextualize current performance** with historical data
   - Bad example: "Math proficiency is 51.6%"
   - Good example: "Math proficiency is currently 51.6%, down from 62.5% five years ago, showing a concerning decline"

4. **Be specific about year-over-year changes** when significant (>5 points)
   - Example: "Particularly concerning is the sharp drop during 2020-21 (likely COVID impact) with only partial recovery since"

5. **Mention recent improvements** even at struggling schools
   - Example: "While overall proficiency remains low at 35%, there's been a modest 3-point improvement over the last two years"

When you receive school data formatted like:
"English Language Arts: 2018-19: 60.5%, 2020-21: 46.8%, 2021-22: 55.2%, 2022-23: 57.6%, 2023-24: 57.1%"

You MUST analyze the TREND (started at 60.5%, dropped sharply to 46.8% during COVID, recovered to ~57% and stabilized), not just cite the current 57.1%.

## The Zoning Situation

[Full detail on zoning - codes, lot sizes, future land use, what it means practically. Will the neighborhood character change? Any development concerns?]

## Who This Is For

[Combine who thrives AND who struggles into ONE section. Be specific about buyer profiles - not "the right person" but actual descriptions like "retirees prioritizing safety over school quality" or "young professionals without school-age kids who want a quiet street." Include both who should consider this property AND who should pass.]

## Before You Decide

[3-5 specific action items tied to THIS property's data. See detailed instructions below. Must include at least one alternative neighborhood suggestion.]

## My Recommendation

[Final verdict - clear, confident statement summarizing your position. No trailing questions.]

=== STRUCTURE RULES TO AVOID REPETITION ===

- "What Stands Out" is a BRIEF teaser only (2-3 sentences). No statistics, no percentages, no specific numbers.
- All detailed safety discussion goes ONLY in "The Safety Picture"
- All detailed school discussion goes ONLY in "The Schools Story"
- Do NOT preview statistics in early sections that you'll repeat later
- Each data point should appear exactly ONCE in the entire analysis
- If you've made a point, don't restate it - reference briefly if needed ("As noted above...")

=== "BEFORE YOU DECIDE" SECTION RULES ===

Make every action item SPECIFIC to this property's data. Generic advice like "drive around the neighborhood" or "talk to neighbors" is filler. Tie each recommendation directly to what you learned about THIS address.

NEVER use generic items like:
- "Drive around the neighborhood at different times"
- "Talk to some neighbors"
- "Research the schools online"
- "Visit the area in person"
- "Check out the local amenities"

INSTEAD, create SPECIFIC items like these (tailored to the property):

Based on SCHOOL concerns:
- "Sit in on a class at [specific school name] - call the front office to arrange a visit"
- "Ask [school name] about tutoring resources that help close the proficiency gap"
- "Talk to parents at pickup time at [school] - they'll give you the unfiltered version"

Based on SAFETY data:
- "Chat with the mail carrier or UPS driver on this route - they know which streets have issues"
- "Check if this block has an active NextDoor group and browse recent posts"
- "Ask a neighbor how long they've lived here and whether safety has improved or declined"

Based on ZONING situation:
- "Pull the ACC Planning Department's 5-year capital plan for any road or rezoning projects nearby"
- "Check if any variance requests have been filed within 500 feet"
- "Look at building permits issued on adjacent parcels in the last 2 years"

=== ALTERNATIVE NEIGHBORHOOD SUGGESTIONS ===

Based on the weaknesses you identify, ALWAYS suggest specific alternative areas in the "Before You Decide" section.

If schools are weak (especially if average proficiency is below 40%):
- Suggest 2-3 nearby attendance zones with stronger performance
- Include specific school names and approximate proficiency difference
- Example: "If schools are the priority, look at neighborhoods in the Timothy Road Elementary or Whit Davis Elementary zones - proficiency rates run 15-20 points higher."
- IMPORTANT: When Clarke County schools show significant weakness (below 40% proficiency), mention Oglethorpe County Schools as an alternative. Oglethorpe County generally outperforms Clarke County academically and is just a short drive away. Frame it helpfully: "For families prioritizing education, consider exploring homes in the Oglethorpe County school district, which consistently outperforms Clarke County on state assessments. The commute to Athens is manageable, and many families make this tradeoff for stronger schools."

If safety is a concern:
- Suggest safer nearby areas with specific comparison
- Example: "For better safety numbers, the Five Points area typically sees 40% less crime than this location."

If zoning allows unwanted development:
- Suggest more protected areas
- Example: "If you want protection from higher-density development, neighborhoods with RS-40 zoning have larger minimum lots."

RULE: The "Before You Decide" section must include at least one specific "if [this weakness matters], consider [specific alternative]" recommendation.

=== ENDING RULES ===

Do NOT end with questions: "Makes sense?" / "What do you think?" / "Sound good?"
Do NOT end with offers: "Let me know if you have questions!" / "Happy to discuss!"
Do NOT end with filler: "Hope this helps!" / "Good luck with your search!"

DO end with a clear, confident final statement that summarizes your verdict.

GOOD endings:
- "The safety is too good to ignore, but those school numbers are too weak to overlook if education is a priority."
- "For the right buyer profile - and you know if that's you - this is a genuinely strong option."
- "Bottom line: exceptional safety, weak schools, stable zoning. If the school situation doesn't apply to you, this deserves serious consideration."

BAD endings:
- "Makes sense?"
- "Let me know if you have any other questions!"
- "Hope this helps with your decision!"
- "What do you think?"

=== FINAL CHECKLIST ===
Before finishing, verify:
- [ ] Started directly with "## The Bottom Line" (no intro/greeting)
- [ ] "What Stands Out" has NO statistics (just brief teaser)
- [ ] Safety stats appear ONLY in "The Safety Picture"
- [ ] School stats appear ONLY in "The Schools Story"
- [ ] School analysis discusses TRENDS over 5 years, not just current scores
- [ ] No warm phrases repeated
- [ ] "Before You Decide" has specific, non-generic action items
- [ ] "Before You Decide" includes alternative neighborhood suggestion
- [ ] Ended with confident statement (no trailing questions)
- [ ] Each data point appears only once

Base everything on the data provided. When you reference specific numbers, cite them. But interpret the data - don't just report it.
"""

        # Call Claude API
        import anthropic

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            response = message.content[0].text

            # Generate footer with school phone numbers
            today = datetime.now().strftime('%Y-%m-%d')

            # Get school phone numbers if school info available
            school_contacts = ""
            if school_info:
                elem_phone = get_school_phone(school_info.elementary)
                middle_phone = get_school_phone(school_info.middle)
                high_phone = get_school_phone(school_info.high)
                school_contacts = f"""
**Local Contacts:**
- {school_info.elementary}: {elem_phone}
- {school_info.middle}: {middle_phone}
- {school_info.high}: {high_phone}
- Clarke County School District: (706) 546-7721
"""

            footer = f"""

---

**Data Sources & Verification:**
- School Data: Clarke County Schools (2024-25) & Georgia GOSA (2023-24)
- Crime Data: Athens-Clarke County Police Department (current as of {today})
- Zoning Data: Athens-Clarke County Planning Department GIS
{school_contacts}
**Community Resources:**
- Athens-Clarke County Police (Non-Emergency): (706) 546-7021
- ACC Planning Department: (706) 613-3515

*This analysis is for informational purposes only. Always verify independently and visit in person.*
"""

            return response + footer

        except Exception as e:
            return f"Error generating synthesis: {str(e)}"


def main():
    """Test unified assistant"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python unified_ai_assistant.py <address> [question]")
        print('Example: python unified_ai_assistant.py "150 Hancock Avenue, Athens, GA" "Is this good for families?"')
        sys.exit(1)

    address = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "Is this a good neighborhood?"

    print("=" * 80)
    print("UNIFIED AI ASSISTANT TEST")
    print("=" * 80)
    print(f"Address: {address}")
    print(f"Question: {question}")
    print()

    assistant = UnifiedAIAssistant()

    result = assistant.get_comprehensive_analysis(
        address=address,
        question=question,
        include_schools=True,
        include_crime=True
    )

    if result['error']:
        print(f"❌ Error: {result['error']}")

    if result['synthesis']:
        print("\n" + "=" * 80)
        print("COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(result['synthesis'])


if __name__ == "__main__":
    main()
