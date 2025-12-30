"""
Configuration for Loudoun County, Virginia.

Based on research from loudoun_county_data_sources.md

Data Sources:
- Schools: LCPS School Locator + Virginia School Quality Profiles
- Crime: LCSO Crime Dashboard (nightly updates, launched Aug 2025)
- Zoning: Loudoun County GIS + 7 incorporated town ordinances

Multi-Jurisdiction Complexity: HIGH
- 7 incorporated towns with separate zoning ordinances
- Jurisdiction detection required for accurate zoning lookup

Developer Notes:
- This is the PRIMARY COUNTY for development (developer lives here)
- Personal validation address: 43423 Cloister Pl, Leesburg, VA 22075
- Can validate all results against local knowledge

Last Updated: November 2025
"""

from .base_config import CountyConfig

# Loudoun County Configuration
LOUDOUN_CONFIG = CountyConfig(
    # ===== IDENTITY =====
    county_name="loudoun",
    state="VA",
    display_name="Loudoun County",
    is_production_ready=False,  # Under development
    is_primary_county=True,     # Developer's home county (Leesburg resident)

    # ===== SCHOOLS =====
    school_district_name="Loudoun County Public Schools (LCPS)",
    school_zone_data_source="api",  # LCPS has school locator API
    school_zone_file_path=None,
    school_api_endpoint="TODO: Research LCPS School Locator API endpoint - see docs/lcps_school_locator_research.md",
    school_boundary_tool_url="TODO: LCPS boundary tool URL from research",

    # Virginia school performance (from research report)
    state_school_performance_source="Virginia School Quality Profiles",
    state_performance_api="TODO: Find Virginia DOE API if available",

    # ===== CRIME & SAFETY =====
    crime_data_source="api",  # LCSO Crime Dashboard (launched Aug 2025)
    crime_api_endpoint="TODO: Research LCSO Crime Dashboard API endpoint - see docs/lcso_crime_dashboard_research.md",
    crime_data_file_path=None,

    # Multi-jurisdiction: Sheriff + 7 town police departments
    has_multiple_jurisdictions=True,
    town_police_sources={
        # Town police departments - most towns use LCSO, some have own PD
        'Leesburg': 'TODO: Leesburg PD Crime Data (if available)',
        'Purcellville': 'TODO: Purcellville PD Crime Data (if available)',
        'Middleburg': 'TODO: Middleburg uses LCSO or has own data?',
        'Hamilton': 'TODO: Hamilton uses LCSO',
        'Lovettsville': 'TODO: Lovettsville uses LCSO',
        'Round Hill': 'TODO: Round Hill uses LCSO',
        'Hillsboro': 'TODO: Hillsboro uses LCSO'
    },

    # ===== ZONING & LAND USE =====
    zoning_data_source="arcgis",  # Loudoun County GIS REST API
    zoning_api_endpoint="https://logis.loudoun.gov/gis/rest/services/COL/Zoning/MapServer/3/query",  # Layer 3: Current Zoning
    zoning_portal_url="https://logis.loudoun.gov/",  # Verified from research

    # 7 incorporated towns with separate zoning ordinances
    has_incorporated_towns=True,
    incorporated_towns=[
        "Leesburg",      # County seat
        "Purcellville",
        "Middleburg",
        "Hamilton",
        "Lovettsville",
        "Round Hill",
        "Hillsboro"
    ],
    town_boundaries_file="data/loudoun/town_boundaries.geojson",  # TODO: Export from GIS
    town_zoning_sources={
        # TODO: Get from loudoun_county_data_sources.md - town zoning ordinance URLs
        'Leesburg': 'TODO: Leesburg zoning ordinance URL',
        'Purcellville': 'TODO: Purcellville zoning ordinance URL',
        'Middleburg': 'TODO: Middleburg zoning ordinance URL',
        'Hamilton': 'TODO: Hamilton zoning ordinance URL',
        'Lovettsville': 'TODO: Lovettsville zoning ordinance URL',
        'Round Hill': 'TODO: Round Hill zoning ordinance URL',
        'Hillsboro': 'TODO: Hillsboro zoning ordinance URL'
    },

    # ===== GEOGRAPHY =====
    county_bounds={
        # TODO: Get exact bounds from Loudoun GIS
        'min_lat': 38.8,
        'max_lat': 39.3,
        'min_lon': -78.0,
        'max_lon': -77.3
    },
    major_towns=[
        "Leesburg",      # County seat, largest town
        "Purcellville",  # Western Loudoun
        "Ashburn",       # Eastern Loudoun (unincorporated)
        "Sterling",      # Eastern Loudoun (unincorporated)
        "Middleburg"     # Horse country
    ],

    # ===== DATA UPDATE SCHEDULE =====
    data_update_frequency={
        'schools': 'annually',      # LCPS updates zones yearly
        'crime': 'nightly',         # LCSO Dashboard updates nightly (per research)
        'zoning': 'hourly'          # County GIS updates hourly (per research)
    },

    # ===== CONTACT INFORMATION =====
    school_district_phone="(571) 252-1000",
    school_district_website="https://www.lcps.org/",
    police_department_contact="https://www.loudoun.gov/sheriff",
    planning_department_contact="https://www.loudoun.gov/planning",
    planning_department_website="https://www.loudoun.gov/planning",

    # ===== FEATURE FLAGS =====
    has_school_data=False,   # Phase 3 - Infrastructure complete, API endpoint pending
    has_crime_data=False,    # Phase 2 - Infrastructure complete, API endpoint pending
    has_zoning_data=True,    # ✅ Phase 1 complete - County GIS working!

    # ===== VALIDATION =====
    can_validate_locally=True,  # Developer lives in Loudoun County!
    test_addresses_available=True
)


def get_loudoun_config() -> CountyConfig:
    """Get Loudoun County configuration."""
    return LOUDOUN_CONFIG


# Test addresses for validation
LOUDOUN_TEST_ADDRESSES = [
    # Personal validation
    "43423 Cloister Pl, Leesburg, VA 22075",  # Developer's home address - PRIMARY TEST

    # Incorporated town addresses (different jurisdictions)
    "TODO: Leesburg downtown address",        # Town of Leesburg zoning
    "TODO: Purcellville address",             # Town of Purcellville zoning
    "TODO: Middleburg address",               # Town of Middleburg zoning

    # Unincorporated addresses (county zoning)
    "TODO: Ashburn address",                  # Eastern Loudoun, county zoning
    "TODO: Sterling address",                 # Eastern Loudoun, county zoning
    "TODO: Rural western address",            # Western Loudoun, county zoning

    # Edge cases
    "TODO: Address near town boundary",       # Test jurisdiction detection
    "TODO: Address in data center area",      # Test unique zoning (Ashburn data centers)
]

# Personal validation notes
PERSONAL_VALIDATION_NOTES = """
Developer lives at: 43423 Cloister Pl, Leesburg, VA 22075

Expected results for personal address:
- Elementary: TODO: Verify with LCPS
- Middle: TODO: Verify with LCPS
- High: TODO: Verify with LCPS (likely Tuscarora HS)
- Jurisdiction: Town of Leesburg (incorporated)
- Zoning: TODO: Verify with Town of Leesburg
- Crime: TODO: Verify safety perception matches data

This personal address will be the PRIMARY validation test for all three
data types (schools, crime, zoning). If this address returns correct data,
confidence in the entire system increases significantly.

Friends/neighbors can also validate their addresses (with permission).
"""
