# Athens Home Buyer Research Assistant - Demo Guide

> **AI-powered neighborhood research combining schools and crime data for Athens-Clarke County, Georgia**

---

## 📋 Quick Start

### Running the Demo

```bash
# Set your API key
export ANTHROPIC_API_KEY='your-api-key-here'

# Launch the web interface
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🎯 What This Tool Does

The Athens Home Buyer Research Assistant combines three official data sources:
- **Clarke County Schools** - School assignments by address (2024-25)
- **Georgia GOSA** - School performance metrics (2023-24)
- **Athens-Clarke Police** - Crime statistics (last 12 months)

It uses **Claude 3 Haiku AI** to synthesize insights across these datasets and answer questions in plain English.

### Key Features

✅ **School Lookup**: Get elementary, middle, and high school assignments for any Athens address
✅ **School Performance**: CCRPI scores, graduation rates, content mastery, literacy/math proficiency
✅ **Crime Analysis**: 1-100 safety score, crime categorization, trend analysis, Athens comparison
✅ **Visual Dashboard**: Color-coded safety scores, interactive charts, mobile-responsive design
✅ **AI Synthesis**: Natural language Q&A combining both schools and safety data
✅ **Citations**: All data linked to official sources for verification

---

## 🎤 The 5-Minute Demo

### Setup (30 seconds)

**Opening Line:**
> "Let me show you how this tool helps home buyers research Athens neighborhoods. Instead of spending hours searching school ratings and crime maps separately, you can ask questions in plain English and get comprehensive analysis."

**Data Sources:**
- Clarke County Schools (official assignments)
- Georgia GOSA (state performance data)
- Athens-Clarke Police (crime statistics)

### Demo Address #1: The Ideal Family Neighborhood (2 minutes)

**Address:** `220 College Station Road, Athens, GA 30602`
**Question:** `Is this a good area for families with young kids?`
**Select:** ✅ Schools + ✅ Crime/Safety

**Profile:**
- Safety Score: **90/100** (Very Safe - Green)
- Total Crimes: **19** (87% below Athens average)
- Trend: **DECREASING -41.7%**
- Schools: Barnett Shoals | Hilsman | Cedar Shoals
- Elementary CCRPI: ~75/100

**Key Talking Points:**
1. **School Assignments**: "Here are the assigned schools with their performance data automatically retrieved"
2. **Color-Coded Safety**: "Notice the green header - instant visual feedback. 90/100 safety score."
3. **Interactive Charts**:
   - By Category: Mostly property/traffic crimes, not violent
   - Trends: Crime is decreasing 41.7%
   - Comparison: 87% LESS crime than Athens average
4. **AI Synthesis**: "The AI considers BOTH schools AND safety to answer the specific question about families with kids"
5. **Data Sources**: "Everything is cited. Users can verify themselves."

**Why This Works:**
- Extremely low crime (only 19 incidents in a year)
- Crime decreasing significantly
- Good schools across all levels
- Perfect example of ideal family neighborhood

---

### Demo Address #2: The Honest Assessment (2 minutes)

**Address:** `150 Hancock Avenue, Athens, GA 30601`
**Question:** `Is this a good area for families with young kids?`
**Select:** ✅ Schools + ✅ Crime/Safety

**Profile:**
- Safety Score: **60/100** (Safe - Yellow/Green)
- Total Crimes: **448** (199% ABOVE Athens average)
- Trend: **DECREASING -37.1%**
- Schools: Barrow | Clarke Middle | Clarke Central
- Elementary CCRPI: 75.4/100

**Key Talking Points:**
1. **Honest Numbers**: "448 crimes in the last year - that's 199% above Athens average. The tool doesn't hide this."
2. **Context Matters**: "BUT notice what it does - provides CONTEXT. This is near the UGA campus in the bar district."
3. **Crime Breakdown**: "Most crimes are alcohol-related and property crimes, not violent attacks"
4. **Positive Trend**: "Crime is DECREASING 37% - positive trajectory"
5. **Balanced AI**: "The AI says 'NOT ideal for traditional suburban families, BUT could work for those comfortable with urban living.' It even suggests better alternatives."

**Why This Works:**
- Shows tool gives HONEST assessments
- Demonstrates AI synthesis with nuance and context
- Proves we don't sugarcoat data
- Great example of urban living tradeoffs

---

### Closing (30 seconds)

**What Makes This Powerful:**
- ✅ Saves hours of research time
- ✅ Combines multiple official data sources
- ✅ Honest, balanced assessments
- ✅ Cites all sources for verification
- ✅ Accessible - just ask questions in plain English

**The Bottom Line:**
> "This is a demo showing what's possible with AI + public data. For production, you'd add more cities, more data sources (parks, transit, home prices), and possibly integrate with MLS data."

---

## 🎨 Visual Features to Highlight

### Color-Coded Safety Scores
- **Green (80-100)**: Very Safe
- **Light Green (60-79)**: Safe
- **Yellow/Orange (40-59)**: Moderate
- **Red (20-39)**: Concerning
- **Dark Red (1-19)**: High Risk

### Interactive Charts
1. **Crime by Category** - Bar chart showing Violent, Property, Traffic, Other
2. **Trend Analysis** - 6-month comparison showing increasing/decreasing patterns
3. **Athens Comparison** - Side-by-side bars: This Address vs Athens Average

### Mobile Responsive
- Tabbed interface prevents scrolling overload
- Stacked columns on small screens
- Full-width charts adapt to screen size

---

## 💡 Sample Questions for Each Demo Address

### For 220 College Station Road (Low Crime):
1. "Is this a good area for families with young kids?"
2. "How safe is this neighborhood?"
3. "What are the schools like here?"
4. "Should I buy a house here?"

### For 150 Hancock Avenue (High Crime):
1. "Is this a good area for families with young kids?" (Shows honest assessment)
2. "Should I be worried about safety here?" (Shows context)
3. "What are the schools like despite the high crime?" (Shows school data is independent)

### For 1000 Jennings Mill Road (Middle Option):
1. "What are the pros and cons of this neighborhood?"
2. "Is crime getting better or worse here?"
3. "How does this compare to other Athens neighborhoods?"

---

## ❓ Questions You Should Be Ready to Answer

### Technical Questions

**Q: What AI model powers this?**
A: Claude 3 Haiku for speed and cost-efficiency. For production, you could use Claude Sonnet for more nuanced analysis.

**Q: How fast are queries?**
A: First query: 1-2 seconds | Cached queries: <0.01 seconds (instant)

**Q: What happens if the crime API goes down?**
A: Graceful error handling. If crime data fails, it still shows school information and explains crime data is unavailable.

**Q: How do you calculate the safety score?**
A: Transparent algorithm:
- Start at 100
- Deduct for crime density (0 to -50 points)
- Deduct for violent crime % (0 to -25 points)
- Adjust for trends (-15 to +5 points)
- Final score clipped to [1-100]

### Business Questions

**Q: What would it cost to run this at scale?**
A:
- Anthropic API: ~$0.001 per query with caching
- Hosting: $10-50/month (Streamlit Cloud or AWS)
- Estimated: $0.001-0.01 per query

**Q: Can this be white-labeled for realtors?**
A: Absolutely. The tool can be:
- Branded for a realty agency
- Integrated into property listings
- Added to real estate platforms

**Q: How would you monetize this?**
A: Options:
1. SaaS for realtors ($50-200/month per agent)
2. API for property platforms (per-query pricing)
3. White-label for real estate companies
4. Freemium (more cities = premium)

### Data Questions

**Q: Why only Athens?**
A: This is a demo. Athens was chosen for accessible public data. Production would add more cities.

**Q: What about school ratings like GreatSchools?**
A: We use official Georgia GOSA data (CCRPI scores, Content Mastery). Could integrate GreatSchools ratings too.

**Q: Is the crime data real-time?**
A: From Athens Police database, updated regularly. Queries cached 24 hours, so data is at most 1 day old.

**Q: What crime data is missing?**
A: We don't have:
- Unreported crimes
- Crimes in progress
- Private security incidents
- UGA campus crimes (separate jurisdiction)

### Comparison Questions

**Q: How is this different from Zillow/Redfin?**
A: Zillow/Redfin show property prices, photos, basic school ratings, heat maps.
We add:
- AI synthesis combining ALL factors
- Natural language Q&A
- Honest tradeoff analysis
- Specific school assignments

This is complementary to Zillow, not a replacement.

### Limitation Questions

**Q: What can't this tool tell me?**
A: We don't have data on:
- Home prices / property values
- Traffic patterns / commute times
- Parks / recreation / walkability
- Restaurants / shopping / amenities
- Noise levels
- Future development plans
- Community "feel"

The AI will honestly say "I don't have that data."

---

## 🛠️ Technical Architecture

### Data Flow
```
User Input (Address + Question)
    ↓
Geocoding (lat/long lookup)
    ↓
Parallel Data Retrieval:
├─→ School Lookup (street_index.csv)
│   ├─→ School Performance (GOSA data)
│   └─→ SchoolAIAssistant
└─→ Crime Analysis (Athens PD API)
    ├─→ Safety Score Calculation
    ├─→ Trend Analysis
    ├─→ Athens Baseline Comparison
    └─→ CrimeAIAssistant
    ↓
UnifiedAIAssistant (synthesis)
    ↓
Streamlit Display (visualizations + AI response)
```

### Key Files

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Main web interface with integrated school + crime analysis |
| `unified_ai_assistant.py` | Combines school and crime assistants, synthesizes insights |
| `school_info.py` | School assignment lookup and GOSA performance data |
| `crime_analysis.py` | Crime statistics, safety scoring, trend analysis |
| `crime_visualizations.py` | Chart data structures and HTML visualizations |
| `ai_school_assistant.py` | Claude AI for school-related questions |
| `crime_ai_assistant.py` | Claude AI for crime-related questions |

### Caching Strategy
- **Athens Baseline**: Cached weekly (all crimes in Athens for comparison)
- **Address Queries**: Cached 24 hours (geocoding + crime data)
- **School Data**: Static files (updated annually)

### Dependencies
```
anthropic          # Claude AI API
requests           # HTTP requests
pandas             # Data structures for charts
streamlit          # Web interface
geopy              # Geocoding
```

---

## 🎭 Demo Tips

### Before the Demo
1. ✅ Test all 3 demo addresses beforehand
2. ✅ Have `ANTHROPIC_API_KEY` set
3. ✅ Check internet connection (needs Athens PD API)
4. ✅ Open `DEMO_SCRIPT.py` for reference
5. ✅ Clear any previous search results

### During the Demo
- **Go Slow**: Let visualizations load, let people see the charts
- **Point and Click**: Physically point to the color coding, charts, tabs
- **Read Key Quotes**: Read specific AI insights aloud
- **Emphasize Citations**: Expand "Data Sources" to show verification links
- **Show Honesty**: The high-crime example is your best feature
- **Handle Errors Gracefully**: If something fails, explain the fallback behavior

### After the Demo
- **Invite Questions**: Use the Q&A section in `DEMO_SCRIPT.py`
- **Acknowledge Limitations**: Be upfront about what it can't do
- **Discuss Scaling**: Talk about adding more cities
- **Share Vision**: Explain how this fits into larger real estate tools

---

## 🚀 Feature Highlights

### What Makes This Demo Compelling

1. **Real Data**: Not mock data - actual Athens schools and police records
2. **AI Synthesis**: Combines multiple datasets intelligently
3. **Visual Feedback**: Color coding gives instant assessment
4. **Honest Assessments**: Doesn't sugarcoat high-crime areas
5. **Transparency**: All sources cited and verifiable
6. **Fast**: Queries in 1-2 seconds (cached queries instant)
7. **Mobile Friendly**: Works on phones and tablets
8. **Natural Language**: No need to learn complex interfaces

### What Makes It Production-Ready

✅ Comprehensive error handling
✅ User-friendly error messages with suggestions
✅ Data validation and integrity checks
✅ Performance optimization (caching)
✅ 100% test pass rate (16/16 tests)
✅ Mobile-responsive design
✅ Professional styling
✅ Citations and disclaimers

---

## 📊 Test Results

**Comprehensive Test Suite**: 16/16 tests passed (100%)

- ✅ 10 diverse Athens addresses (downtown, suburban, UGA, industrial)
- ✅ 4 edge cases (invalid, outside Athens, typos, border towns)
- ✅ Data integrity verification (sums, percentages, trends)
- ✅ Performance monitoring (all queries < 10 seconds)

See `test_crime_comprehensive.py` for full test suite.

---

## ⚠️ Known Limitations

### By Design
- Only covers Athens-Clarke County (demo scope)
- No home prices / property values
- No traffic / commute data
- No walkability / amenities
- School zones from 2024-25 (may change)
- Crime data is historical (not predictive)

### Technical
- Requires internet connection (Athens PD API)
- API key needed (Anthropic Claude)
- Geocoding can fail on very new addresses
- UGA campus crimes not included (separate jurisdiction)

### Data Refresh
- School assignments: Annual (2024-25)
- School performance: Annual (2023-24)
- Crime queries: Cached 24 hours
- Athens baseline: Cached 1 week

---

## 🔮 Future Enhancements

### Short Term
- [ ] Add more Georgia cities (Atlanta, Savannah, Augusta)
- [ ] Integrate GreatSchools ratings alongside GOSA
- [ ] Add home price data (Zillow API)
- [ ] Traffic/commute data (Google Maps API)
- [ ] Park/walkability scores

### Medium Term
- [ ] Expand to multiple states
- [ ] White-label version for realty agencies
- [ ] API for property platforms
- [ ] Historical trend charts (3+ years)
- [ ] Neighborhood comparison tool

### Long Term
- [ ] ML model for predictive safety trends
- [ ] Integration with MLS data
- [ ] Community sentiment analysis (NextDoor, etc.)
- [ ] Customizable scoring weights
- [ ] Mobile native apps (iOS/Android)

---

## 📞 Support & Contact

### For Demo Questions
- Review `DEMO_SCRIPT.py` for detailed talking points
- Check this guide's Q&A section
- Test addresses beforehand to know expected results

### For Technical Issues
- Verify `ANTHROPIC_API_KEY` is set
- Check internet connection (needs Athens PD API)
- Try demo addresses first: 150 Hancock Ave, 220 College Station Rd
- Review error messages - they include troubleshooting steps

### Data Source Questions
- **School assignments**: Clarke County Schools (706) 546-7721
- **School performance**: Georgia GOSA website
- **Crime data**: Athens-Clarke Police Department

---

## 📝 Quick Reference Card

### 3 Demo Addresses

| Address | Safety | Crime Count | Trend | Use Case |
|---------|--------|-------------|-------|----------|
| 220 College Station Rd | 90/100 | 19 (-87%) | ↓ -41.7% | Ideal family |
| 1000 Jennings Mill Rd | 75/100 | 79 (-47%) | ↓ -35.4% | Middle option |
| 150 Hancock Ave | 60/100 | 448 (+199%) | ↓ -37.1% | Urban tradeoff |

### Key Commands

```bash
# Start demo
export ANTHROPIC_API_KEY='your-key'
streamlit run streamlit_app.py

# Run tests
python test_crime_comprehensive.py
python test_visualizations.py

# Test CLI
python unified_ai_assistant.py "150 Hancock Ave, Athens, GA" "Is this safe?"
```

### URLs to Bookmark
- Clarke County School Zones: https://www.clarke.k12.ga.us/page/school-attendance-zones
- Athens Crime Map: https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime
- Georgia GOSA: https://gosa.georgia.gov/

---

**Last Updated**: November 2024
**Demo Version**: 1.0
**Coverage**: Athens-Clarke County, Georgia

---

## 🎬 Ready to Demo!

You now have everything you need:
- ✅ Working application with school + crime integration
- ✅ Visual dashboard with color-coded safety scores
- ✅ 3 pre-tested demo addresses with known results
- ✅ Comprehensive demo script with talking points
- ✅ Anticipated Q&A responses
- ✅ User-friendly error messages
- ✅ "About the Data" page in the app
- ✅ 100% passing test suite

**Go show them what AI-powered neighborhood research can do!** 🚀
