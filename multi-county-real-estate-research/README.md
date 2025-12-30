# Multi-County Real Estate Research Tool

**Status:** 🚧 Pre-production Development
**Architecture:** Multi-county support with configuration layer
**Purpose:** Validate multi-county approach before merging with production Athens tool

---

## 🎯 Project Goals

1. **Validate multi-county architecture** with Loudoun County, VA implementation
2. **Keep Athens production tool untouched** (frozen for January 2026 demo)
3. **Design for easy merge** - use same module names, clean abstraction
4. **Personal validation** - test with real Loudoun County addresses (researcher lives there)

---

## 🏗️ Architecture Overview

### Configuration Layer Pattern

Each county has a configuration class that encapsulates:
- Data source URLs and API endpoints
- County-specific logic (e.g., incorporated towns)
- Data parsing and transformation
- Jurisdiction detection

```python
from config import athens_clarke, loudoun

# Select county
config = loudoun.LoudounConfig()

# Get data through config
schools = config.get_schools(address)
crime = config.get_crime(address)
zoning = config.get_zoning(address)
```

### Directory Structure

```
multi-county-real-estate-research/
├── config/                  # County configurations
│   ├── base_config.py       # Abstract base class
│   ├── athens_clarke.py     # Athens-Clarke County, GA
│   └── loudoun.py           # Loudoun County, VA
├── core/                    # Shared modules (county-agnostic)
│   ├── jurisdiction_detector.py
│   ├── school_lookup.py
│   ├── crime_analysis.py
│   ├── zoning_lookup.py
│   └── unified_ai_assistant.py
├── data/                    # County-specific data files
│   ├── athens_clarke/
│   └── loudoun/
├── utils/                   # Shared utilities
├── tests/                   # Test suites
└── docs/                    # Documentation
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Anthropic API key (for AI analysis)
- Internet connection (for API calls)

### Installation

```bash
# Clone or navigate to project
cd multi-county-real-estate-research

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the App

```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit app
streamlit run streamlit_app.py
```

### Testing with Addresses

**Athens-Clarke County, GA:**
- 150 Hancock Avenue, Athens, GA 30601
- 247 Pulaski Street, Athens, GA 30601
- 120 Dearing Street, Athens, GA 30605

**Loudoun County, VA:**
- 43875 Centergate Drive, Ashburn, VA 20148 (suburban)
- 25 W Market Street, Leesburg, VA 20176 (incorporated town)
- 221 S Maple Avenue, Purcellville, VA 20132 (incorporated town)

---

## 📋 Implementation Status

### Athens-Clarke County, GA
- [x] School lookup (CCSD zones + Georgia GOSA)
- [x] Crime analysis (ACC Open Data)
- [x] Zoning lookup (ACC GIS REST API)
- [x] AI synthesis with conversational tone
- [x] UI polish (summaries, Key Insights)
- **Status:** ✅ Production-ready (copied from main project)

### Loudoun County, VA
- [ ] School lookup (LCPS zones + VA School Quality Profiles)
- [ ] Crime analysis (LCSO Dashboard / GeoHub)
- [ ] Zoning lookup (Loudoun GIS REST API)
- [ ] Incorporated town detection (7 towns)
- [ ] AI prompt customization for Virginia
- [ ] Personal validation with local addresses
- **Status:** 🚧 In Development

---

## 🔄 Relationship to Athens Production Project

**This is a SEPARATE project** - the Athens production tool at `/home/user/NewCo` remains completely untouched.

### Why Separate?

1. **Athens is production-ready** for January 2026 demo - cannot risk breaking it
2. **Multi-county architecture needs validation** before affecting production
3. **Parallel development** without merge conflicts
4. **Easy rollback** if multi-county approach doesn't work

### When to Merge?

See **[MERGE_PLAN.md](./MERGE_PLAN.md)** for detailed merge strategy.

**Merge after:**
- ✅ Loudoun County is fully implemented and tested
- ✅ Personal validation complete (living in Loudoun County)
- ✅ Athens demo (January 2026) is complete
- ✅ Confidence in new architecture

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[MERGE_PLAN.md](./MERGE_PLAN.md)** | How to merge with Athens production project |
| **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** | Design decisions and patterns |
| **[docs/adding_a_county.md](./docs/adding_a_county.md)** | Guide for adding new counties |
| **[docs/loudoun_notes.md](./docs/loudoun_notes.md)** | Loudoun-specific implementation notes |
| **[docs/implementation_phases.md](./docs/implementation_phases.md)** | Development phases and timeline |

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_addresses.py

# Loudoun validation (requires living in Loudoun County)
pytest tests/loudoun_validation.py
```

### Test Coverage

- Unit tests for each config class
- Integration tests for data fetching
- Address validation tests
- Jurisdiction detection tests

---

## 🛠️ Development Workflow

### Adding a New County

1. **Research data sources** (see `loudoun_county_data_sources.md` for example)
2. **Create config class** in `config/new_county.py`
3. **Implement required methods**:
   - `get_schools(address)`
   - `get_crime(address)`
   - `get_zoning(address)`
4. **Add county to UI selector** in `streamlit_app.py`
5. **Test thoroughly** with known addresses
6. **Document** county-specific quirks

See [docs/adding_a_county.md](./docs/adding_a_county.md) for detailed guide.

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions small and focused
- Use defensive programming (hasattr, try-except)

---

## 🔐 Environment Variables

Required in `.env`:

```bash
# Anthropic API for AI analysis
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Override default API endpoints
# ATHENS_CRIME_API=https://...
# LOUDOUN_GIS_API=https://...
```

---

## 📦 Dependencies

Core dependencies:
- `streamlit` - Web UI
- `anthropic` - AI analysis (Claude)
- `requests` - HTTP requests
- `shapely` - Geometry operations
- `geopy` - Geocoding
- `pandas` - Data manipulation

See [requirements.txt](./requirements.txt) for full list.

---

## 🐛 Troubleshooting

### Common Issues

**Import errors after adding new county:**
```python
# Make sure __init__.py exists in config/
touch config/__init__.py
```

**Geocoding failures:**
- Check address format (include city, state, ZIP)
- Verify API endpoints are accessible
- Check for rate limiting

**AI analysis not generating:**
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API key is valid
- Ensure sufficient token limit (4000 tokens for rich narratives)

**Module not found errors:**
- Verify you're in correct directory
- Check Python path includes project root
- Ensure virtual environment is activated

---

## 🎯 Roadmap

### Phase 1: Loudoun County MVP (Weeks 1-4)
- [ ] School lookup via LCPS API
- [ ] Crime analysis via LCSO dashboard
- [ ] Zoning lookup via Loudoun GIS
- [ ] Basic incorporated town detection
- [ ] Personal address validation

### Phase 2: Multi-Jurisdiction Support (Weeks 5-7)
- [ ] Full incorporated town support (7 towns)
- [ ] Town-specific zoning lookup
- [ ] Leesburg zoning integration
- [ ] Purcellville zoning integration

### Phase 3: Polish & Validation (Weeks 8-9)
- [ ] AI prompt customization for Loudoun
- [ ] Key Insights for Loudoun data
- [ ] Personal validation complete
- [ ] Friend/neighbor validation
- [ ] Documentation complete

### Phase 4: Merge Planning (Week 10)
- [ ] Athens demo complete (Jan 2026)
- [ ] Merge decision made
- [ ] Follow MERGE_PLAN.md strategy

---

## 🤝 Contributing

**Note:** This is a personal project for validating multi-county architecture.

If you want to add a county:
1. Fork the repository
2. Create a new branch (`feature/add-{county-name}`)
3. Follow [docs/adding_a_county.md](./docs/adding_a_county.md)
4. Submit pull request with documentation

---

## 📄 License

This project uses the same license as the Athens production tool.

---

## 🙏 Acknowledgments

- **Athens-Clarke County** - Original implementation and data sources
- **Loudoun County GIS** - Excellent open data portal
- **Loudoun County Public Schools** - School boundary tools
- **Loudoun Sheriff's Office** - Crime dashboard
- **Anthropic** - Claude AI for narrative analysis

---

## 📞 Contact

This is a personal validation project. For questions about the architecture or merge strategy, refer to the documentation in this repository.

---

**Remember:** This project exists to validate the multi-county approach. The Athens production tool remains the source of truth until the merge is complete.
