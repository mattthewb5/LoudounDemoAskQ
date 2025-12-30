#!/usr/bin/env python3
"""
ATHENS HOME BUYER RESEARCH ASSISTANT - DEMO SCRIPT
===================================================

This document provides everything you need for a successful demo.
"""

# ============================================================================
# PART 1: THE THREE DEMO ADDRESSES
# ============================================================================

"""
Address A: THE IDEAL FAMILY NEIGHBORHOOD
=========================================
Address: 220 College Station Road, Athens, GA 30602
Story: "Sarah & Mike, young family with 2 kids looking for safety and good schools"

PROFILE:
- Schools: Barnett Shoals (Elementary) | Hilsman (Middle) | Cedar Shoals (High)
- Elementary CCRPI: ~75/100
- Safety Score: 90/100 (Very Safe)
- Total Crimes (12 months): 19
- Violent Crime: 15.8%
- Trend: DECREASING -41.7%
- vs Athens Average: -87% (Low activity area)

KEY SELLING POINTS:
✓ Extremely low crime (only 19 incidents in a year!)
✓ Crime decreasing significantly
✓ Suburban, family-friendly area
✓ Well below Athens average for crime
✓ Good schools for all levels

DEMO QUESTIONS:
1. "Is this a good area for families with young kids?"
   → Expected: Positive response highlighting safety + schools

2. "How safe is this neighborhood?"
   → Expected: 90/100 score, low crime stats, decreasing trend

3. "What are the schools like here?"
   → Expected: Barnett Shoals, Hilsman, Cedar Shoals assignments with performance data

INTERESTING INSIGHTS TO HIGHLIGHT:
- Only 1.6 crimes per month (extremely low)
- Crime dropped 41.7% year-over-year (positive trend)
- 87% less crime than Athens average (context matters!)
- Most common crime: Driving Under Influence (shows it's not violent crime)
"""

"""
Address B: THE TYPICAL MIDDLE OPTION
======================================
Address: 1000 Jennings Mill Road, Athens, GA 30606
Story: "Alex, first-time buyer on a budget, wants decent schools and reasonable safety"

PROFILE:
- Schools: Timothy (Elementary) | Clarke Middle | Clarke Central
- Safety Score: 75/100 (Safe)
- Total Crimes (12 months): 79
- Violent Crime: 22.8%
- Trend: DECREASING -35.4%
- vs Athens Average: -47% (Low activity area)

KEY SELLING POINTS:
✓ Still well below Athens average for crime
✓ Crime decreasing substantially
✓ Suburban/shopping area with amenities
✓ Good balance of safety and affordability
✓ Accessible schools

DEMO QUESTIONS:
1. "What are the pros and cons of this neighborhood?"
   → Expected: Balanced response showing moderate crime but still safe, decent schools

2. "Is crime getting better or worse here?"
   → Expected: Decreasing 35.4%, positive trajectory

3. "How does this compare to other Athens neighborhoods?"
   → Expected: 47% below Athens average, still in "low activity" category

INTERESTING INSIGHTS TO HIGHLIGHT:
- 6.6 crimes per month (moderate but manageable)
- Crime trend is positive (down 35%)
- Still safer than most of Athens
- Shows the tool identifies middle-ground options
"""

"""
Address C: THE URBAN TRADEOFF
===============================
Address: 150 Hancock Avenue, Athens, GA 30601
Story: "Jordan, grad student, wants to be near UGA campus, walkable to downtown"

PROFILE:
- Schools: Barrow (Elementary) | Clarke Middle | Clarke Central
- Barrow Elementary CCRPI: 75.4/100
- Safety Score: 60/100 (Safe)
- Total Crimes (12 months): 448
- Violent Crime: 17.2%
- Trend: DECREASING -37.1%
- vs Athens Average: +199% (Very high activity area)

KEY SELLING POINTS:
✓ Walkable to UGA campus and downtown
✓ Crime is DECREASING significantly
✓ Most crime is property/alcohol-related (not violent)
✓ Urban amenities and culture
✓ The tool honestly identifies the tradeoffs

DEMO QUESTIONS:
1. "Is this a good area for families with young kids?"
   → Expected: HONEST assessment - high crime but explains context (UGA bar district)

2. "Should I be worried about safety here?"
   → Expected: Balanced - high crime numbers but decreasing, mostly non-violent

3. "What are the schools like despite the high crime?"
   → Expected: Shows Barrow Elementary has decent scores (75.4/100)

INTERESTING INSIGHTS TO HIGHLIGHT:
- This is where the tool shines: HONEST assessment
- 199% above Athens average BUT crime is decreasing 37%
- Most crime is liquor violations, property crimes (not violent attacks)
- Great example of urban living tradeoffs
- Shows the AI doesn't sugarcoat - provides balanced, factual analysis
"""

# ============================================================================
# PART 2: DEMO SCRIPT
# ============================================================================

demo_script = """
===========================================================================
DEMO SCRIPT: "AI-Powered Home Buyer Research for Athens-Clarke County"
===========================================================================

OPENING (30 seconds)
--------------------
"Let me show you how this tool helps home buyers research neighborhoods in
Athens, Georgia. Instead of spending hours searching school ratings and
crime maps separately, you can ask questions in plain English and get a
comprehensive analysis combining both."

[Pull up the Streamlit app]

"We have data from three official sources:
- Clarke County Schools for school assignments
- Georgia GOSA for school performance data
- Athens-Clarke Police Department for crime statistics

The AI synthesizes all of this and gives you actionable insights."

DEMO 1: THE IDEAL NEIGHBORHOOD (2 minutes)
-------------------------------------------
Address: 220 College Station Road, Athens, GA 30602
Question: "Is this a good area for families with young kids?"

✓ Check BOTH boxes: Schools + Crime/Safety
✓ Click Search

TALKING POINTS while loading:
"Notice I selected both school and crime analysis. The AI will look at
school quality AND neighborhood safety together, then synthesize insights."

WHEN RESULTS APPEAR:
1. School Assignments Section:
   "Here are the assigned schools: Barnett Shoals Elementary, Hilsman Middle,
    Cedar Shoals High. The tool automatically looks up their performance data."

2. Crime & Safety Section:
   [Point to the green header and 90/100 score]
   "Notice the green color-coding - that's instant visual feedback. This area
    scored 90 out of 100 for safety, which is 'Very Safe'."

   [Click through the tabs]
   "By Category: Most crimes are property or traffic - not violent
    Trends: Crime is DECREASING 41.7% - positive direction!
    Comparison: This area has 87% LESS crime than Athens average"

3. AI Synthesis:
   [Scroll to AI Analysis]
   "This is where it gets powerful. The AI synthesizes both datasets and
    answers our specific question about families with young kids."

   [Read key excerpt from synthesis]
   "Notice it considers BOTH schools AND safety, explains tradeoffs, and
    provides context. It's not just listing facts - it's giving insights."

4. Data Sources:
   [Expand "Data Sources & Verification"]
   "Everything is cited. Users can verify the data themselves. We're not
    making claims we can't back up."

DEMO 2: THE MIDDLE OPTION (1 minute)
-------------------------------------
Address: 1000 Jennings Mill Road, Athens, GA 30606
Question: "What are the pros and cons of this neighborhood?"

TALKING POINTS:
"Now let's look at a more typical middle-ground option."

WHEN RESULTS APPEAR:
"Safety score of 75/100 - still safe, but not exceptional. 79 crimes in
 the last year. Notice the AI gives a balanced assessment - it doesn't
 over-hype or dismiss. It shows this is a decent option with reasonable
 safety and accessible schools."

DEMO 3: THE HONEST ASSESSMENT (2 minutes)
------------------------------------------
Address: 150 Hancock Avenue, Athens, GA 30601
Question: "Is this a good area for families with young kids?"

TALKING POINTS:
"This is where the tool really proves its value - honest assessment."

WHEN RESULTS APPEAR:
[Point to the score: 60/100, yellow/green color]
"448 crimes in the last year - that's 199% ABOVE the Athens average.
 The tool doesn't hide this."

[Read AI synthesis excerpt]
"But notice what it does: It provides CONTEXT. This is near the UGA campus
 in the bar district. Most crimes are alcohol-related and property crimes,
 not violent attacks. Crime is DECREASING 37%."

"The AI synthesizes this and says 'NOT ideal for traditional suburban
 families, BUT could work for those comfortable with urban living.' It
 even suggests better alternatives like College Station Road."

[Point to comparison chart]
"This visualization shows the stark difference - this address vs Athens
 average. The data is clear, the assessment is honest."

ADDRESSING QUESTIONS (1 minute)
--------------------------------
Q: "What if buyers ask about something you don't have data for?"

A: "Great question. The tool currently covers school assignments, school
    performance, crime statistics, and safety trends. If someone asks about
    parks, home prices, or traffic - the AI will honestly say 'I don't have
    that data' and suggest they research those factors separately. We don't
    make up information."

Q: "How often is the data updated?"

A: "School assignments are from the 2024-25 school year, performance data
    from the 2023-24 year. Crime data is live - pulled from Athens Police
    within the last 12 months and cached for 24 hours. The Athens baseline
    refreshes weekly. We show these dates in the data sources section."

Q: "Can this work for other cities?"

A: "The architecture is designed to scale. We'd need to:
    1. Get school assignment data for the new city
    2. Connect to their police crime API (most cities have this)
    3. Adjust the baseline for that city's crime patterns

    The AI synthesis, caching, and visualization all work the same way."

CLOSING (30 seconds)
--------------------
"What makes this powerful:
✓ Saves hours of research time
✓ Combines multiple data sources
✓ Honest, balanced assessments
✓ Cites all sources for verification
✓ Accessible - just ask questions in plain English

This is a demo tool showing what's possible with AI + public data. For
production, you'd add more cities, more data sources (parks, transit, etc.),
and possibly integrate with MLS data."

[End]
"""

# ============================================================================
# PART 3: QUESTIONS YOU SHOULD BE READY TO ANSWER
# ============================================================================

"""
TECHNICAL QUESTIONS:
====================

Q: What AI model powers this?
A: Claude 3 Haiku for speed and cost-efficiency. For production, you could
   use Claude Sonnet for more nuanced analysis or keep Haiku for rapid
   responses.

Q: How fast are the queries?
A: First query: 1-2 seconds (API call + geocoding)
   Cached queries: <0.01 seconds (instant)
   We cache both Athens baseline (weekly) and address queries (24 hours)

Q: What happens if the crime API goes down?
A: The tool has graceful error handling. If crime data fails, it will still
   show school information and explain that crime data is unavailable.

Q: Can you handle addresses outside Athens?
A: The tool detects addresses outside Athens-Clarke County and rejects them
   with a helpful error message. It won't try to fake data.

Q: How do you calculate the safety score?
A: Transparent algorithm (documented in code):
   - Start at 100
   - Deduct for crime density (0 to -50 points)
   - Deduct for violent crime percentage (0 to -25 points)
   - Adjust for trends (-15 to +5 points)
   - Scale is designed for U.S. expansion

BUSINESS QUESTIONS:
===================

Q: What would it cost to run this at scale?
A: Main costs:
   - Anthropic API: ~$0.001 per query with caching
   - Hosting: $10-50/month (Streamlit Cloud or AWS)
   - No database needed (uses public APIs)
   Estimated: $0.001-0.01 per query depending on caching hit rate

Q: Can this be white-labeled for realtors?
A: Absolutely. The tool is designed to be embeddable. You could:
   - Brand it for a realty agency
   - Integrate it into property listing pages
   - Add it to a real estate platform

Q: What about liability?
A: Strong disclaimers throughout:
   - "For research purposes only"
   - "Always verify independently"
   - "Visit neighborhoods in person"
   - All data cited to official sources
   We don't give legal or financial advice

Q: How would you monetize this?
A: Options:
   1. SaaS for realtors ($50-200/month per agent)
   2. API for property platforms (per-query pricing)
   3. White-label for real estate companies
   4. Free tool with premium features (more cities, more data)

DATA QUESTIONS:
===============

Q: Why only Athens?
A: This is a demo. Athens was chosen because:
   - Accessible public data (police API, school data)
   - Medium-sized city (good test case)
   - Shows the concept works
   Production would add more cities

Q: What about school ratings like GreatSchools?
A: We use official Georgia GOSA data (Content Mastery, CCRPI scores).
   Could integrate GreatSchools ratings, but wanted to show official
   government data works well.

Q: Is the crime data real-time?
A: It's from the official Athens Police database, updated regularly.
   We cache queries for 24 hours, so data is at most 1 day old.

Q: What crime data is missing?
A: We don't have:
   - Unreported crimes
   - Crimes in progress
   - Private security incidents
   - Crimes on UGA campus (separate jurisdiction)
   We're transparent about these limitations

COMPARISON QUESTIONS:
=====================

Q: How is this different from Zillow/Redfin?
A: Zillow/Redfin show you:
   - Property prices, photos, listings
   - School ratings (GreatSchools)
   - Crime heat maps

   We add:
   - AI synthesis combining ALL factors
   - Natural language Q&A
   - Honest tradeoff analysis
   - Specific school assignments (not just ratings)

   This is complementary to Zillow, not a replacement

Q: Can I get this for my city?
A: If your city has:
   - Publicly available school assignment data
   - Crime API (most cities do via ArcGIS or similar)
   Then yes, it can be adapted in 2-3 days

LIMITATION QUESTIONS:
=====================

Q: What can't this tool tell me?
A: We don't have data on:
   - Home prices / property values
   - Traffic patterns / commute times
   - Parks / recreation
   - Restaurants / shopping
   - Noise levels
   - Future development plans
   - Community "feel"

   The AI will honestly say "I don't have that data"

Q: What if someone asks about a future address?
A: If it's new construction not in the school assignment database yet,
   the tool will fail gracefully and suggest contacting the school district.

Q: Can it predict future crime?
A: NO. It shows trends (increasing/decreasing) but explicitly does NOT
   make predictions. The AI is instructed to never speculate about the future.
"""

# ============================================================================
# BONUS: HANDLING DIFFICULT QUESTIONS DURING DEMO
# ============================================================================

"""
"What if the AI is wrong?"
→ "The AI doesn't invent data - it only uses official sources. If there's an
   error in the underlying data (school assignment wrong, crime record incorrect),
   we show data sources so users can verify and report issues to the authorities."

"Can this be gamed by realtors?"
→ "All data comes from official government sources, not user input. A realtor
   can't manipulate the crime statistics or school ratings. The tool is read-only."

"What about privacy?"
→ "We don't store user queries. No personal information is collected. All data
   is aggregated public information. Crime data doesn't include victim names or
   exact addresses (just approximate locations)."

"This seems biased toward certain neighborhoods"
→ "The tool reports factual data: crime statistics and school performance from
   official sources. If that data shows disparities, that's a reflection of
   underlying inequities, not bias in the tool. We're transparent about methodology."

"Why should I trust AI for something this important?"
→ "Good question. The AI is a research assistant, not a decision-maker. It:
   - Shows all sources
   - Provides citations
   - Encourages verification
   - Recommends visiting neighborhoods in person
   Think of it as a faster way to access public data, with helpful synthesis."
"""

print(__doc__)
print(demo_script)
