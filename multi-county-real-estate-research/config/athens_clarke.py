"""
Configuration for Athens-Clarke County, Georgia.

This documents the production Athens tool's behavior for migration.

Data Sources:
- Schools: Clarke County School District zones + Georgia GOSA
- Crime: Athens-Clarke County Open Data portal
- Zoning: ACC GIS REST API

Last Updated: November 2025
"""

from .base_config import CountyConfig

# Athens-Clarke County Configuration
ATHENS_CLARKE_CONFIG = CountyConfig(
    # ===== IDENTITY =====
    county_name="athens_clarke",
    state="GA",
    display_name="Athens-Clarke County",
    is_production_ready=True,  # Ready for January 2026 demo
    is_primary_county=False,   # Not developer's home county

    # ===== SCHOOLS =====
    school_district_name="Clarke County School District",
    school_zone_data_source="csv",  # Static CSV file
    school_zone_file_path="data/athens_clarke/school_zones.csv",  # TODO: Copy from Athens project
    school_boundary_tool_url="https://www.clarke.k12.ga.us/domain/164",

    # Georgia school performance data
    state_school_performance_source="GOSA",  # Governor's Office of Student Achievement
    state_performance_api="https://gosa.georgia.gov/",

    # ===== CRIME & SAFETY =====
    crime_data_source="api",
    crime_api_endpoint="https://opendata.accgov.com/api/crime",  # TODO: Get exact endpoint from Athens project

    # Single jurisdiction (unified government)
    has_multiple_jurisdictions=False,
    town_police_sources=None,

    # ===== ZONING & LAND USE =====
    zoning_data_source="arcgis",
    zoning_api_endpoint="https://maps.accgov.com/arcgis/rest/services/",  # TODO: Get exact endpoint from Athens project
    zoning_portal_url="https://www.accgov.com/gis",

    # No incorporated towns (unified government)
    has_incorporated_towns=False,
    incorporated_towns=[],
    town_boundaries_file=None,
    town_zoning_sources=None,

    # ===== GEOGRAPHY =====
    county_bounds={
        'min_lat': 33.8,
        'max_lat': 34.1,
        'min_lon': -83.6,
        'max_lon': -83.2
    },
    major_towns=["Athens", "Winterville", "Bogart"],  # For display only

    # ===== DATA UPDATE SCHEDULE =====
    data_update_frequency={
        'schools': 'annually',      # School zones rarely change
        'crime': 'weekly',          # Crime data updated weekly
        'zoning': 'as_amended'      # Zoning updates as ordinances change
    },

    # ===== CONTACT INFORMATION =====
    school_district_phone="(706) 357-5700",
    school_district_website="https://www.clarke.k12.ga.us/",
    police_department_contact="https://www.accgov.com/police",
    planning_department_contact="https://www.accgov.com/planning",
    planning_department_website="https://www.accgov.com/planning",

    # ===== FEATURE FLAGS =====
    has_school_data=True,
    has_crime_data=True,
    has_zoning_data=True,

    # ===== VALIDATION =====
    can_validate_locally=False,  # Developer doesn't live in Athens
    test_addresses_available=True  # But we have test addresses from development
)


def get_athens_config() -> CountyConfig:
    """Get Athens-Clarke County configuration."""
    return ATHENS_CLARKE_CONFIG


# Test addresses for validation (from Athens project development)
ATHENS_TEST_ADDRESSES = [
    "123 Main St, Athens, GA 30601",      # Downtown
    "456 Oak St, Athens, GA 30605",       # Residential
    "789 College Ave, Athens, GA 30602"   # Near UGA
    # TODO: Get actual test addresses from Athens project
]
