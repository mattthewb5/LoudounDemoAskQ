"""
Base configuration class for county-specific settings.

MERGE NOTE: This is the foundation for multi-county support.
- Athens equivalent: N/A (Athens is hardcoded)
- New architecture: Configuration-driven county support
- Backward compatible: Counties can have different capabilities
- See: MERGE_PLAN.md for merge strategy

Last Updated: November 2025
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class CountyConfig:
    """
    Base configuration for a county's data sources and settings.

    This class defines all possible variations between counties.
    Not all counties will use all fields - some may be None.
    """

    # ===== IDENTITY =====
    county_name: str                    # Internal ID (e.g., "loudoun", "athens_clarke")
    state: str                          # Two-letter state code
    display_name: str                   # Human-readable name

    # Development status
    is_production_ready: bool = False   # Ready for real users?
    is_primary_county: bool = False     # Developer's home county?

    # ===== SCHOOLS =====
    school_district_name: str = ""
    school_zone_data_source: str = ""   # 'csv', 'api', 'pdf', 'manual'
    school_zone_file_path: Optional[str] = None
    school_api_endpoint: Optional[str] = None
    school_boundary_tool_url: Optional[str] = None  # For user verification

    # State-level school performance data
    state_school_performance_source: str = "unknown"  # e.g., "GOSA", "Virginia School Quality Profiles"
    state_performance_api: Optional[str] = None

    # ===== CRIME & SAFETY =====
    crime_data_source: str = ""         # 'api', 'csv', 'manual'
    crime_api_endpoint: Optional[str] = None
    crime_data_file_path: Optional[str] = None

    # Multi-jurisdiction support (for counties with towns)
    has_multiple_jurisdictions: bool = False
    town_police_sources: Optional[Dict[str, str]] = None  # {'Leesburg': 'url', ...}

    # ===== ZONING & LAND USE =====
    zoning_data_source: str = ""        # 'arcgis', 'api', 'manual'
    zoning_api_endpoint: Optional[str] = None
    zoning_portal_url: Optional[str] = None  # For user verification

    # Multi-jurisdiction zoning (for counties with incorporated towns)
    has_incorporated_towns: bool = False
    incorporated_towns: List[str] = field(default_factory=list)  # ['Leesburg', 'Purcellville', ...]
    town_boundaries_file: Optional[str] = None  # GeoJSON with town boundaries
    town_zoning_sources: Optional[Dict[str, str]] = None  # {'Leesburg': 'url', ...}

    # ===== GEOGRAPHY =====
    county_bounds: Dict[str, float] = field(default_factory=dict)  # {'min_lat': x, 'max_lat': y, ...}
    major_towns: List[str] = field(default_factory=list)  # For display/filtering

    # ===== DATA UPDATE SCHEDULE =====
    data_update_frequency: Dict[str, str] = field(default_factory=dict)  # {'schools': 'annually', ...}

    # ===== CONTACT INFORMATION (for user verification) =====
    school_district_phone: Optional[str] = None
    school_district_website: Optional[str] = None
    police_department_contact: Optional[str] = None
    planning_department_contact: Optional[str] = None
    planning_department_website: Optional[str] = None

    # ===== FEATURE FLAGS =====
    # What data is currently available?
    has_school_data: bool = False
    has_crime_data: bool = False
    has_zoning_data: bool = False

    # ===== VALIDATION =====
    # Can developer personally validate results?
    can_validate_locally: bool = False
    test_addresses_available: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure incorporated_towns is a list, not None
        if self.incorporated_towns is None:
            self.incorporated_towns = []

        # Validate that multi-jurisdiction flags match data
        if self.has_incorporated_towns and not self.incorporated_towns:
            raise ValueError(f"{self.county_name}: has_incorporated_towns=True but no towns listed")

        if self.has_multiple_jurisdictions and not self.town_police_sources:
            # This is OK - might just mean Sheriff covers everything
            pass

    def get_jurisdiction_count(self) -> int:
        """Return number of jurisdictions (1 = county only, 2+ = county + towns)."""
        if not self.has_incorporated_towns:
            return 1
        return 1 + len(self.incorporated_towns)

    def is_town_incorporated(self, town_name: str) -> bool:
        """Check if a town is incorporated (has separate zoning)."""
        return town_name in self.incorporated_towns

    def get_zoning_authority(self, is_in_town: bool, town_name: Optional[str] = None) -> str:
        """Get the zoning authority for an address."""
        if is_in_town and town_name:
            return f"Town of {town_name}"
        return f"{self.display_name}"
