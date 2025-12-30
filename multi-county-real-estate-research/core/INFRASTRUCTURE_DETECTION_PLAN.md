# Infrastructure Construction Activity Detection Plan

## Overview

This module detects and quantifies **infrastructure-related construction activity** from Loudoun County building permits.

**IMPORTANT**: This is NOT about evaluating internet quality or connectivity scores. This IS about flagging construction patterns that indicate:
- Commercial tech sector investment
- Large-scale infrastructure projects
- Development pressure indicators
- Area transformation signals

**Output Style**: Quantitative facts only
- "15 fiber installations within 2 miles (last 12 months)"
- "Nearest data center: 3.2 miles"
- NO quality claims like "excellent connectivity"

---

## 1. Keyword Dictionary

### Category: DATACENTER
Primary indicator: `Structure Type == 'Data Center'` (most reliable)

Secondary keywords (in Permit Description):
- `data center` / `datacenter`
- `data hall`
- `server room`
- `colocation` / `colo facility`
- `rack installation` / `rack installations`
- `computer room`
- `iad \d+` (pattern for IAD facility names like "IAD 10", "IAD 13")

### Category: FIBER
Keywords (in Permit Description):
- `fiber optic`
- `fiber cable`
- `fiber installation`
- `fiber conduit`
- `fiber line`
- `fiber run`
- `optical fiber`
- `fios`
- `hdpe conduit` (when paired with fiber context)

Note: "conduit" alone has false positives (electrical conduit). Require fiber context.

### Category: TELECOM_TOWER
Keywords (in Permit Description):
- `antenna` / `antennas` (high signal)
- `cell tower`
- `cell site`
- `monopole`
- `lattice tower`
- `wireless tower`
- `telecommunications tower`
- `radio tower`
- `5g`
- `rru` / `rrh` / `rrus` / `rrhs` (radio equipment)
- `t-mobile` / `at&t` / `verizon` (carrier names in commercial context)

Exclude: `antenna` in residential solar/TV context (check Permit Type)

### Category: TELECOM_EQUIPMENT
Keywords (in Permit Description):
- `telecommunications`
- `telecom equipment`
- `communications cabling`
- `communication equipment`
- `network equipment` (in commercial context)

Exclude:
- `switch` (too many kitchen/electrical false positives)
- `cabinet` (too many kitchen false positives)
- `outlet` (electrical outlets)

### Category: UTILITY_INFRASTRUCTURE
Keywords (in Permit Description):
- `duct bank`
- `underground conduit` (with utility/telecom context)
- `pedestal` (utility context)
- `vault` (utility context, not bank vault)
- `manhole` (utility context)

---

## 2. Categorization Rules

### Priority Order (a permit can match multiple categories)
1. **DATACENTER**: Structure Type == 'Data Center' OR description contains datacenter keywords
2. **FIBER**: Description contains fiber-related keywords
3. **TELECOM_TOWER**: Description contains antenna/tower keywords AND Permit Type == 'Building (Commercial)'
4. **TELECOM_EQUIPMENT**: Description contains telecom keywords AND Permit Type == 'Building (Commercial)'
5. **UTILITY_INFRASTRUCTURE**: Description contains utility keywords

### Exclusion Rules
- Skip if Permit Type == 'Building (Residential)' for most telecom categories
- Skip if description contains "kitchen", "bathroom", "residential" context for switch/cabinet keywords
- Skip if Structure Type in ['Single-Family Detached', 'Single-Family Attached', 'Multi-Family']

### Boolean Flags
Each permit gets these flags:
```python
{
    'is_datacenter': bool,      # Data center construction
    'is_fiber': bool,           # Fiber optic installation
    'is_telecom_tower': bool,   # Cell tower/antenna work
    'is_telecom_equipment': bool,  # Telecom equipment installation
    'is_infrastructure': bool   # ANY of the above is True
}
```

---

## 3. Data Enhancement

### New Columns to Add
| Column | Type | Description |
|--------|------|-------------|
| `is_datacenter` | bool | Data center construction |
| `is_fiber` | bool | Fiber optic installation |
| `is_telecom_tower` | bool | Cell tower/antenna work |
| `is_telecom_equipment` | bool | Telecom equipment |
| `is_infrastructure` | bool | Any infrastructure type |
| `infrastructure_categories` | str | Comma-separated list of matched categories |

### Preserve All Original Columns
- Do NOT modify or remove any existing columns
- Output to new file: `loudoun_permits_with_infrastructure.csv`

---

## 4. Function List

### Core Detection Functions

```python
def load_infrastructure_keywords() -> dict:
    """
    Return dictionary of keyword categories.

    Returns:
        dict: {
            'datacenter': ['data center', 'data hall', ...],
            'fiber': ['fiber optic', 'fiber cable', ...],
            'telecom_tower': ['antenna', 'cell tower', ...],
            'telecom_equipment': ['telecommunications', ...],
        }
    """

def detect_infrastructure_type(description: str) -> list:
    """
    Detect infrastructure types from permit description.

    Args:
        description: Permit description string

    Returns:
        list: Categories found, e.g., ['datacenter', 'fiber']
              Empty list if no infrastructure keywords found
    """

def tag_permit(permit_row: dict) -> dict:
    """
    Tag a single permit with infrastructure flags.

    Args:
        permit_row: Dict with permit data (must have 'Permit Description',
                    'Structure Type', 'Permit Type')

    Returns:
        dict: {
            'is_datacenter': True/False,
            'is_fiber': True/False,
            'is_telecom_tower': True/False,
            'is_telecom_equipment': True/False,
            'is_infrastructure': True/False,
            'infrastructure_categories': 'datacenter,fiber' or ''
        }
    """
```

### Proximity Search Functions

```python
def find_nearby_infrastructure(
    lat: float,
    lon: float,
    permits_df: pd.DataFrame,
    radius_miles: float,
    months_back: int = 12
) -> dict:
    """
    Find infrastructure projects near a location.

    Args:
        lat: Target latitude
        lon: Target longitude
        permits_df: DataFrame with infrastructure-tagged permits
        radius_miles: Search radius in miles
        months_back: How many months back to search (default 12)

    Returns:
        dict: {
            'datacenter_count': 15,
            'datacenter_projects': [
                {'address': '...', 'distance_miles': 1.2, 'date': '2024-06',
                 'value': 45000000, 'description': '...'},
                ...
            ],
            'fiber_count': 3,
            'fiber_projects': [...],
            'telecom_tower_count': 8,
            'telecom_tower_projects': [...],
            'total_infrastructure_count': 26,
            'total_construction_value': 52500000,
            'nearest_datacenter': {'address': '...', 'distance_miles': 1.2, ...} or None,
            'nearest_fiber': {...} or None,
            'nearest_telecom_tower': {...} or None
        }
    """

def calculate_infrastructure_trends(
    permits_df: pd.DataFrame,
    area_lat: float,
    area_lon: float,
    radius_miles: float
) -> dict:
    """
    Calculate year-over-year infrastructure trends.

    Args:
        permits_df: DataFrame with infrastructure-tagged permits
        area_lat: Center latitude
        area_lon: Center longitude
        radius_miles: Search radius

    Returns:
        dict: {
            'datacenter_2024': 15,
            'datacenter_2023': 7,
            'datacenter_trend': '+114%',
            'fiber_2024': 3,
            'fiber_2023': 1,
            'fiber_trend': '+200%',
            'telecom_tower_2024': 8,
            'telecom_tower_2023': 5,
            'telecom_tower_trend': '+60%',
            'total_2024': 26,
            'total_2023': 13,
            'total_trend': '+100%'
        }
    """
```

### Utility Functions

```python
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two coordinates."""

def load_permits_with_infrastructure(filepath: str) -> pd.DataFrame:
    """Load the enhanced permits CSV with infrastructure tags."""
```

---

## 5. Output Format

### Factual Reporting Style

**DO**:
- "15 fiber installation projects within 3 miles"
- "Nearest data center: 3.2 miles ($45M construction value)"
- "+114% increase in fiber projects vs last year"
- "Total infrastructure construction value: $52.5M"

**DON'T**:
- "Excellent connectivity infrastructure"
- "Future-proof area with strong tech presence"
- "High infrastructure score: 85/100"
- Any subjective quality assessments

### Example Function Output

```python
{
    'datacenter_count': 15,
    'datacenter_projects': [
        {
            'address': '456 Data Center Dr, Ashburn, VA',
            'distance_miles': 3.2,
            'date': '2024-08',
            'value': 45000000,
            'description': 'New 3-story data center facility'
        },
        # ... more projects
    ],
    'fiber_count': 3,
    'fiber_projects': [...],
    'telecom_tower_count': 8,
    'telecom_tower_projects': [...],
    'total_infrastructure_count': 26,
    'total_construction_value': 52500000,
    'nearest_datacenter': {
        'address': '456 Data Center Dr, Ashburn, VA',
        'distance_miles': 3.2,
        'value': 45000000
    },
    'nearest_fiber': {
        'address': '123 Main St, Leesburg, VA',
        'distance_miles': 0.8,
        'value': 125000
    }
}
```

---

## 6. Data Summary (from Phase 1 Analysis)

### Permit Dataset
- **Total Permits**: 15,752
- **Date Range**: January 2024 - October 2025
- **Total Construction Value**: $7.47 billion
- **Geocoded**: 99.6% (15,689 with lat/lon)

### Infrastructure Breakdown (Initial Scan)

| Category | Count | Notes |
|----------|-------|-------|
| Data Center (Structure Type) | 332 | $5.17B total value |
| Fiber (keywords) | 2 | Explicit fiber projects |
| Conduit (keywords) | 12 | Some telecom-related |
| Telecom Tower (keywords) | 111 | Antennas, cell sites |
| Datacenter (keywords) | 189 | Overlaps with Structure Type |
| Telecom Equipment | 34 | Requires filtering |

### Top Data Center Projects
1. $1.81B - 22235 Loudoun County Pkwy (Foundation)
2. $165M - 21735 Red Rum Dr (3-story DC)
3. $157M - 44371 Gigabit Plz (NTT VA7)
4. $155M - 41785 Inclusion Ln (Core/Shell)
5. $140M - 42031 Growth Mindset Ln (IAD12)

---

## 7. Implementation Notes

### Error Handling
- Gracefully handle missing lat/lon (skip distance calculations)
- Handle empty/null descriptions (return no matches)
- Handle permits with no dates (exclude from time-based queries)
- Return empty/zero values, never crash

### Performance
- Pre-compile regex patterns for keyword matching
- Use vectorized pandas operations where possible
- Cache haversine distance calculations if repeated

### Testing
- Test address: 43500 Tuckaway Pl, Leesburg, VA 20176
- NEVER use: 43423 Cloister Pl

---

## 8. Files to Create

1. `core/infrastructure_detector.py` - Main detection module
2. `core/test_infrastructure.py` - Test script
3. `data/loudoun/building_permits/loudoun_permits_with_infrastructure.csv` - Enhanced dataset

## 9. Files NOT to Modify

- `streamlit_app.py` (Athens - PROTECTED)
- Any files in `data/athens/`
- Existing Loudoun modules until integration phase
