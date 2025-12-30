# NewCo - Real Estate Tools
Real Estate NewCo 2025

## Athens-Clarke County School District Lookup Tool

A comprehensive Python tool to help home buyers in Athens-Clarke County, Georgia research which school attendance zones properties belong to **AND** get detailed school performance data.

### Features

**School Assignment:**
- ✅ **Street Index Lookup**: Uses official Clarke County Schools street index for accurate assignments
- ✅ **Address Normalization**: Handles variations like "St" vs "Street", "Ave" vs "Avenue"
- ✅ **Parameter Matching**: Handles complex address ranges ("497 and below", "odd numbers only", etc.)
- ✅ **Multi-Level**: Returns Elementary, Middle, and High school assignments

**School Performance Data:**
- ✅ **Test Scores**: Georgia Milestones EOG/EOC proficiency rates by subject
- ✅ **Graduation Rates**: 4-year cohort graduation rates for high schools
- ✅ **SAT Scores**: Average SAT scores for high schools
- ✅ **Demographics**: Student enrollment, economic status, racial composition
- ✅ **Trend Analysis**: Automated identification of achievements and areas for improvement
- ✅ **Complete Reports**: Combined school assignment + performance data in one lookup

**AI Assistant:**
- 🤖 **Natural Language Q&A**: Ask questions in plain English
- 🤖 **Intelligent Analysis**: Claude AI analyzes school data and provides balanced answers
- 🤖 **Context-Aware**: Understands nuanced questions about school quality
- 🤖 **Comprehensive**: Considers test scores, demographics, and other factors

**Web Interface (NEW!):**
- 🌐 **Browser-Based**: Easy-to-use web interface powered by Streamlit
- 🌐 **Professional Design**: Clean, modern UI with responsive layout
- 🌐 **Interactive**: Real-time search with AI-powered responses
- 🌐 **Source Citations**: All answers include verifiable sources and links

### Quick Start

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install anthropic  # For AI features
pip install streamlit  # For web interface
```

This installs:
- `shapely` - For spatial/geometric operations
- `geopy` - For geocoding addresses
- `requests` - For downloading data
- `anthropic` - For AI assistant (optional)

#### 2. Data Setup

The tool uses:
- **Street Index**: Official Clarke County Schools street index (included in `data/street_index.pdf`)
- **Performance Data**: Downloaded from Georgia GOSA (Governor's Office of Student Achievement)

The street index data is already extracted and ready to use in `data/street_index.json`.

The performance data is already downloaded and stored in `data/performance/`.

#### 3. Run the Complete Lookup Tool

```bash
python3 school_info.py
```

This will show school assignments AND performance data for three test addresses.

Or look up a specific address:

```bash
python3 school_info.py "123 Main Street, Athens, GA 30601"
```

### Usage

#### Method 1: Web Interface (EASIEST - RECOMMENDED)

Use the browser-based interface for the best experience:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
streamlit run streamlit_app.py
```

The app will open in your browser. Then:
1. Enter an Athens address (e.g., "150 Hancock Avenue")
2. Ask a question (e.g., "How good are the schools?")
3. Click "Search" to get AI-powered answers with citations

See [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) for detailed instructions.

#### Method 2: Complete School Information (Python API)

Get both school assignments AND performance data:

```python
from school_info import get_school_info, format_complete_report

# Get complete information
info = get_school_info("150 Hancock Avenue, Athens, GA 30601")

# Display formatted report
print(format_complete_report(info))

# Or access data programmatically
print(f"Elementary: {info.elementary}")
print(f"Test Scores: {info.elementary_performance.test_scores}")
print(f"Demographics: {info.elementary_performance.demographics}")
```

#### Method 3: School Assignment Only

If you only need to know which schools serve an address:

```python
from street_index_lookup import lookup_school_district

assignment = lookup_school_district("150 Hancock Avenue, Athens, GA 30601")

print(f"Elementary: {assignment.elementary}")
print(f"Middle: {assignment.middle}")
print(f"High: {assignment.high}")
```

#### Method 4: School Performance Only

If you already know the school name and want performance data:

```python
from school_performance import get_school_performance, format_performance_report

perf = get_school_performance("Barrow Elementary")

print(format_performance_report(perf))

# Or access specific data
for score in perf.test_scores:
    print(f"{score.subject}: {score.total_proficient_pct}% proficient")
```

#### Method 5: AI Assistant (Command Line)

Ask questions in natural language and get intelligent AI-powered answers:

```python
from ai_school_assistant import ask_claude_about_schools
import os

# Set your API key
os.environ['ANTHROPIC_API_KEY'] = 'your-api-key-here'

# Ask a question
response = ask_claude_about_schools(
    address="150 Hancock Avenue, Athens, GA 30601",
    question="How good are the schools at this address?"
)

print(response)
```

**Interactive AI CLI:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
python3 school_lookup_ai_cli.py
```

Then ask questions like:
- "What are the test scores at 150 Hancock Avenue?"
- "Are the schools good near 585 Reese Street?"
- "Tell me about school quality for 195 Hoyt Street"

### How It Works

**School Assignment:**
1. **Address Parsing**: Extracts house number and street name
2. **Street Normalization**: Standardizes street names (Avenue→ave, Street→st, etc.)
3. **Index Lookup**: Searches official Clarke County Schools street index
4. **Parameter Matching**: Verifies house number matches address range rules
5. **Results**: Returns elementary, middle, and high school assignments

**Performance Data:**
1. **Data Loading**: Parses CSV files from Georgia GOSA (2023-24 school year)
2. **School Matching**: Flexible name matching handles variations
3. **Metric Extraction**: Pulls test scores, demographics, graduation rates, SAT scores
4. **Analysis**: Automatically identifies achievements and areas for improvement
5. **Reporting**: Formats comprehensive performance reports

### Test Results

The tool was tested and verified with these Athens addresses:

| Address | Elementary | Middle | High |
|---------|-----------|--------|------|
| 150 Hancock Avenue, Athens, GA 30601 | Barrow Elementary | Clarke Middle | Clarke Central High |
| 585 Reese Street, Athens, GA 30601 | Johnnie L. Burks Elementary | Clarke Middle | Clarke Central High |
| 195 Hoyt Street, Athens, GA 30601 | Barrow Elementary | Clarke Middle | Clarke Central High |

**Performance data includes:**
- Test proficiency rates (Georgia Milestones EOG/EOC)
- Student demographics and enrollment
- Graduation rates (high schools)
- SAT scores (high schools)
- Automated achievement/concern analysis

### Files

**Main Tools:**
- `streamlit_app.py` - **WEB INTERFACE**: Browser-based UI (RECOMMENDED)
- `school_info.py` - **MAIN TOOL**: Combined lookup (assignments + performance)
- `ai_school_assistant.py` - **AI ASSISTANT**: Natural language Q&A with Claude
- `school_lookup_ai_cli.py` - Interactive AI-powered CLI
- `school_lookup_cli.py` - Standard interactive CLI
- `school_performance.py` - School performance data module (test scores, demographics, etc.)
- `street_index_lookup.py` - Street index-based school assignment lookup
- `extract_full_street_index.py` - PDF parser to extract street index data
- `test_addresses.py` - Automated test suite with 10 test addresses
- `school_district_lookup.py` - Legacy GIS-based lookup tool

**Data:**
- `data/street_index.json` - Extracted street-to-school mappings (1,957 entries)
- `data/street_index.pdf` - Official Clarke County Schools street index
- `data/performance/*.csv` - Georgia GOSA school performance data (2023-24)

**Documentation:**
- `README.md` - Main documentation
- `WEB_APP_GUIDE.md` - Web interface setup and usage guide
- `TEST_RESULTS.md` - Test documentation and validation results

**Utilities:**
- `parse_street_index.py` - Street index parsing utilities
- `requirements.txt` - Python package dependencies

### Troubleshooting

**"No school zone data found"**: The GeoJSON files aren't in the `data/` directory. Follow the download instructions above.

**Geocoding Errors**: Check internet connection or verify the address is in Athens-Clarke County, GA.

**Import Errors**: Install dependencies with `pip install shapely geopy requests`

### Data Sources

- **Clarke County Schools Street Index**: https://www.clarke.k12.ga.us/page/school-attendance-zones
- **Georgia GOSA (School Performance Data)**: https://gosa.georgia.gov/dashboards-data-report-card/downloadable-data
  - Test Scores (Georgia Milestones EOG/EOC)
  - Graduation Rates
  - SAT Scores
  - Student Demographics
- **Athens-Clarke County Open Data Portal**: https://data-athensclarke.opendata.arcgis.com/

### Important Notes

⚠️ **Disclaimer**:
- School attendance zones and performance data can change year-to-year
- Performance data is from the 2023-24 school year
- Always verify school assignments with Clarke County School District official sources
- This tool is for research and informational purposes only
- Not affiliated with Clarke County School District, Athens-Clarke County government, or Georgia Department of Education
- School performance should be considered as one of many factors in housing decisions
