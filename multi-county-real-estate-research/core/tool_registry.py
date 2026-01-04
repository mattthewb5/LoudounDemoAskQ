"""
Tool Registry for AI Chatbot Integration

Provides centralized registry of all analysis tools available for the Loudoun County
real estate research chatbot. Includes geocoding, tool execution, and cost tracking.

Usage:
    from core.tool_registry import execute_tool, get_all_tool_names, calculate_query_cost

    # Execute a tool by name
    result = execute_tool("school_assignment", lat=39.112492, lon=-77.497378)

    # Get cost estimate before execution
    cost = calculate_query_cost(["property_valuation", "school_assignment"])
"""

import importlib
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import requests

# Ensure core module is importable
_CORE_DIR = Path(__file__).parent
_PACKAGE_DIR = _CORE_DIR.parent
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

# API Key for geocoding
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# =============================================================================
# TOOL REGISTRY - All 20 tools registered with metadata
# =============================================================================

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # Property & Valuation (2 tools)
    # -------------------------------------------------------------------------
    "property_valuation": {
        "name": "Get Property Valuation",
        "function": "core.property_valuation_orchestrator.PropertyValuationOrchestrator.analyze_property",
        "description": "Get current property value, 3-year projections, and rental estimates",
        "input_type": "address",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Full property address"}
            },
            "required": ["address"]
        },
        "api_cost": 0.10,
        "api_provider": "RentCast",
        "category": "property",
        "is_class_method": True,
        "class_name": "PropertyValuationOrchestrator"
    },
    "sales_comparables": {
        "name": "Find Sales Comparables",
        "function": "core.loudoun_sales_comparables.find_comparable_sales",
        "description": "Find recent comparable property sales within a radius",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_miles": {"type": "number", "description": "Search radius in miles", "default": 1.0}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Local Data",
        "category": "property"
    },

    # -------------------------------------------------------------------------
    # Schools & Education (2 tools)
    # -------------------------------------------------------------------------
    "school_assignment": {
        "name": "Get School Assignment",
        "function": "core.loudoun_school_assignment.find_assigned_schools",
        "description": "Find assigned elementary, middle, and high schools for a location",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Local GIS",
        "category": "schools"
    },
    "school_performance": {
        "name": "Get School Performance Analysis",
        "function": "core.loudoun_school_percentiles.get_school_context",
        "description": "Get performance metrics and percentile rankings for a school",
        "input_type": "school_name",
        "input_schema": {
            "type": "object",
            "properties": {
                "school_name": {"type": "string", "description": "Name of the school"},
                "school_type": {"type": "string", "description": "Type: elementary, middle, or high", "enum": ["elementary", "middle", "high"]}
            },
            "required": ["school_name"]
        },
        "api_cost": 0.00,
        "api_provider": "Local Data",
        "category": "schools"
    },

    # -------------------------------------------------------------------------
    # Location & Infrastructure (6 tools)
    # -------------------------------------------------------------------------
    "location_quality": {
        "name": "Analyze Location Quality",
        "function": "core.location_quality_analyzer.LocationQualityAnalyzer.analyze_location",
        "description": "Comprehensive location quality analysis including road type, airport proximity, metro access",
        "input_type": "coordinates_and_address",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "address": {"type": "string", "description": "Full property address"}
            },
            "required": ["lat", "lon", "address"]
        },
        "api_cost": 0.00,
        "api_provider": "Local Analysis",
        "category": "location",
        "is_class_method": True,
        "class_name": "LocationQualityAnalyzer"
    },
    "power_lines": {
        "name": "Analyze Power Line Proximity",
        "function": "core.loudoun_utilities_analysis.analyze_power_line_proximity",
        "description": "Check proximity to high-voltage power transmission lines",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Local GIS",
        "category": "location"
    },
    "cell_coverage": {
        "name": "Analyze Cell Tower Coverage",
        "function": "core.loudoun_cell_coverage.analyze_cell_tower_coverage",
        "description": "Analyze cellular coverage based on nearby cell towers",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "FCC Data",
        "category": "location"
    },
    "flood_zone": {
        "name": "Check Flood Zone Status",
        "function": "core.loudoun_flood_zone.check_flood_zone",
        "description": "Check FEMA flood zone designation for a location",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "FEMA GIS",
        "category": "location"
    },
    "metro_access": {
        "name": "Analyze Metro Access",
        "function": "core.loudoun_metro_analysis.analyze_metro_access",
        "description": "Analyze proximity and access to Washington Metro stations",
        "input_type": "coordinates_tuple",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "WMATA Data",
        "category": "location"
    },
    "traffic_volume": {
        "name": "Get Traffic Volume Data",
        "function": "core.loudoun_traffic_volume.LoudounTrafficVolumeAnalyzer.analyze",
        "description": "Get traffic volume data for nearby roads",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "VDOT Data",
        "category": "location",
        "is_class_method": True,
        "class_name": "LoudounTrafficVolumeAnalyzer"
    },

    # -------------------------------------------------------------------------
    # Development & Zoning (3 tools)
    # -------------------------------------------------------------------------
    "development_pressure": {
        "name": "Analyze Development Pressure",
        "function": "core.development_pressure_analyzer.DevelopmentPressureAnalyzer.analyze",
        "description": "Analyze development pressure based on nearby permits and construction activity",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Permit Data",
        "category": "development",
        "is_class_method": True,
        "class_name": "DevelopmentPressureAnalyzer"
    },
    "infrastructure_activity": {
        "name": "Detect Infrastructure Activity",
        "function": "core.infrastructure_detector.find_nearby_infrastructure",
        "description": "Detect data center and infrastructure development activity nearby",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_miles": {"type": "number", "description": "Search radius", "default": 3.0}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Permit Data",
        "category": "development"
    },
    "zoning_context": {
        "name": "Analyze Property Zoning",
        "function": "core.loudoun_zoning_analysis.analyze_property_zoning_loudoun",
        "description": "Get zoning designation and development context for a property",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "County GIS",
        "category": "development"
    },

    # -------------------------------------------------------------------------
    # Neighborhood & Community (4 tools)
    # -------------------------------------------------------------------------
    "community_lookup": {
        "name": "Lookup Community Info",
        "function": "core.loudoun_community_lookup.create_property_community_context",
        "description": "Get community and subdivision context for a property",
        "input_type": "subdivision_name",
        "input_schema": {
            "type": "object",
            "properties": {
                "subdivision_name": {"type": "string", "description": "Name of the subdivision"}
            },
            "required": ["subdivision_name"]
        },
        "api_cost": 0.00,
        "api_provider": "Local Data",
        "category": "neighborhood"
    },
    "parks_access": {
        "name": "Analyze Park Access",
        "function": "core.loudoun_parks_analysis.analyze_park_access",
        "description": "Find nearby parks and recreational facilities",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "County GIS",
        "category": "neighborhood"
    },
    "neighborhood_amenities": {
        "name": "Analyze Neighborhood Amenities",
        "function": "core.loudoun_places_analysis.get_neighborhood_amenities",
        "description": "Find nearby restaurants, shops, and amenities using Google Places",
        "input_type": "coordinates_tuple",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.02,
        "api_provider": "Google Places",
        "category": "neighborhood"
    },
    "pharmacy_access": {
        "name": "Get Pharmacy Access",
        "function": "core.loudoun_places_analysis.get_pharmacy_access",
        "description": "Find nearby pharmacies including 24-hour options",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_miles": {"type": "number", "description": "Search radius", "default": 5.0}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.01,
        "api_provider": "Google Places",
        "category": "neighborhood"
    },

    # -------------------------------------------------------------------------
    # Healthcare (1 tool)
    # -------------------------------------------------------------------------
    "healthcare_access": {
        "name": "Analyze Healthcare Access",
        "function": "core.loudoun_healthcare_analysis.analyze_healthcare_access",
        "description": "Analyze access to hospitals, urgent care, and medical facilities",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_miles": {"type": "number", "description": "Search radius", "default": 10.0}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "CMS Data",
        "category": "healthcare"
    },

    # -------------------------------------------------------------------------
    # Demographics & Economic (2 tools)
    # -------------------------------------------------------------------------
    "demographics": {
        "name": "Get Demographics",
        "function": "core.demographics_calculator.calculate_demographics",
        "description": "Get demographic data for the area including income, age, and education",
        "input_type": "coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Latitude"},
                "lon": {"type": "number", "description": "Longitude"},
                "radius_miles": {"type": "number", "description": "Analysis radius", "default": 1.0}
            },
            "required": ["lat", "lon"]
        },
        "api_cost": 0.00,
        "api_provider": "Census API",
        "category": "demographics"
    },
    "economic_indicators": {
        "name": "Get Economic Indicators",
        "function": "core.economic_indicators.get_employer_trends",
        "description": "Get economic context including major employers and job market trends",
        "input_type": "none",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "api_cost": 0.00,
        "api_provider": "BLS Data",
        "category": "economic"
    }
}


# =============================================================================
# GEOCODING FUNCTION
# =============================================================================

def geocode_address(address: str) -> Tuple[float, float, str]:
    """
    Convert address to coordinates using Google Maps Geocoding API.

    Args:
        address: Full street address

    Returns:
        Tuple of (latitude, longitude, formatted_address)

    Raises:
        ValueError: If geocoding fails or API key missing
    """
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "OK":
            raise ValueError(f"Geocoding failed: {data['status']}")

        if not data.get("results"):
            raise ValueError("No results found for address")

        result = data["results"][0]
        location = result["geometry"]["location"]
        formatted_address = result["formatted_address"]

        return (location["lat"], location["lng"], formatted_address)

    except requests.RequestException as e:
        raise ValueError(f"Geocoding request failed: {str(e)}")


# =============================================================================
# TOOL EXECUTOR
# =============================================================================

def execute_tool(tool_name: str, **params) -> Dict[str, Any]:
    """
    Execute a registered tool by name.

    Args:
        tool_name: Name from TOOL_REGISTRY
        **params: Either {"address": str} or {"lat": float, "lon": float} or tool-specific params

    Returns:
        Dict with keys:
            - tool_name: str
            - success: bool
            - data: Dict (tool's raw response)
            - execution_time: float (seconds)
            - cost: float
            - error: str (only if success=False)
    """
    start_time = time.time()

    # Validate tool exists
    if tool_name not in TOOL_REGISTRY:
        return {
            "tool_name": tool_name,
            "success": False,
            "data": None,
            "execution_time": time.time() - start_time,
            "cost": 0.0,
            "error": f"Unknown tool: {tool_name}. Available tools: {', '.join(TOOL_REGISTRY.keys())}"
        }

    tool_info = TOOL_REGISTRY[tool_name]

    try:
        # Handle address-to-coordinates conversion if needed
        if tool_info["input_type"] in ["coordinates", "coordinates_tuple", "coordinates_and_address"]:
            if "address" in params and "lat" not in params:
                lat, lon, formatted_addr = geocode_address(params["address"])
                params["lat"] = lat
                params["lon"] = lon
                if tool_info["input_type"] == "coordinates_and_address":
                    params["address"] = formatted_addr

        # Dynamic import and execution
        function_path = tool_info["function"]

        if tool_info.get("is_class_method"):
            # Handle class methods (need to instantiate class first)
            parts = function_path.rsplit(".", 2)
            module_path = parts[0]
            class_name = parts[1]
            method_name = parts[2]

            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            instance = cls()
            func = getattr(instance, method_name)
        else:
            # Handle regular functions
            module_path, function_name = function_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)

        # Prepare parameters based on input type
        if tool_info["input_type"] == "coordinates":
            result = func(lat=params["lat"], lon=params["lon"], **{k: v for k, v in params.items() if k not in ["lat", "lon", "address"]})
        elif tool_info["input_type"] == "coordinates_tuple":
            result = func((params["lat"], params["lon"]))
        elif tool_info["input_type"] == "coordinates_and_address":
            result = func(lat=params["lat"], lon=params["lon"], address=params["address"])
        elif tool_info["input_type"] == "address":
            result = func(address=params.get("address", ""))
        elif tool_info["input_type"] == "school_name":
            result = func(school_name=params.get("school_name", ""), school_type=params.get("school_type"))
        elif tool_info["input_type"] == "subdivision_name":
            result = func(subdivision_name=params.get("subdivision_name", ""))
        elif tool_info["input_type"] == "none":
            result = func()
        else:
            result = func(**params)

        execution_time = time.time() - start_time

        return {
            "tool_name": tool_name,
            "success": True,
            "data": result,
            "execution_time": execution_time,
            "cost": tool_info["api_cost"]
        }

    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "tool_name": tool_name,
            "success": False,
            "data": None,
            "execution_time": execution_time,
            "cost": 0.0,
            "error": str(e)
        }


# =============================================================================
# COST TRACKING
# =============================================================================

def calculate_query_cost(tool_names: List[str]) -> Dict[str, Any]:
    """
    Estimate total API cost for multiple tools.

    Args:
        tool_names: List of tool names to calculate cost for

    Returns:
        Dict with:
            - total_cost: float
            - breakdown: Dict[tool_name, cost]
            - free_tools: List[str]
            - paid_tools: List[str]
    """
    breakdown = {}
    free_tools = []
    paid_tools = []
    total_cost = 0.0

    for tool_name in tool_names:
        if tool_name in TOOL_REGISTRY:
            cost = TOOL_REGISTRY[tool_name]["api_cost"]
            breakdown[tool_name] = cost
            total_cost += cost

            if cost > 0:
                paid_tools.append(tool_name)
            else:
                free_tools.append(tool_name)
        else:
            breakdown[tool_name] = 0.0
            free_tools.append(tool_name)

    return {
        "total_cost": total_cost,
        "breakdown": breakdown,
        "free_tools": free_tools,
        "paid_tools": paid_tools
    }


class QueryCostTracker:
    """Log API costs to file (hidden from users)."""

    def __init__(self, log_file: str = None):
        if log_file is None:
            # Default path relative to this module
            base_dir = Path(__file__).parent.parent
            log_file = str(base_dir / "data" / "loudoun" / "cache" / "query_costs.log")

        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_query(self, query: str, tools_called: List[str], total_cost: float) -> None:
        """
        Append query cost to log file.

        Format: timestamp | query | tools | cost
        """
        timestamp = datetime.now().isoformat()
        tools_str = ",".join(tools_called)

        # Sanitize query (remove newlines, truncate)
        clean_query = query.replace("\n", " ").replace("|", "-")[:100]

        log_line = f"{timestamp}|{clean_query}|{tools_str}|{total_cost:.4f}\n"

        with open(self.log_file, "a") as f:
            f.write(log_line)

    def get_total_cost_today(self) -> float:
        """Parse log file for today's total cost."""
        if not self.log_file.exists():
            return 0.0

        today = datetime.now().date().isoformat()
        total = 0.0

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        if timestamp.startswith(today):
                            try:
                                total += float(parts[3])
                            except ValueError:
                                continue
        except Exception:
            return 0.0

        return total

    def get_total_cost_all_time(self) -> float:
        """Get total cost across all time."""
        if not self.log_file.exists():
            return 0.0

        total = 0.0

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 4:
                        try:
                            total += float(parts[3])
                        except ValueError:
                            continue
        except Exception:
            return 0.0

        return total


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tools_by_category(category: str) -> List[str]:
    """
    Return list of tool names in a category.

    Args:
        category: One of "property", "schools", "location", "development",
                  "neighborhood", "healthcare", "demographics", "economic"

    Returns:
        List of tool names in the category
    """
    return [
        name for name, info in TOOL_REGISTRY.items()
        if info.get("category") == category
    ]


def get_all_tool_names() -> List[str]:
    """Return all registered tool names."""
    return list(TOOL_REGISTRY.keys())


def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Return full metadata for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Tool metadata dict or None if not found
    """
    return TOOL_REGISTRY.get(tool_name)


def validate_tool_exists(tool_name: str) -> bool:
    """Check if tool_name is registered."""
    return tool_name in TOOL_REGISTRY


def get_all_categories() -> List[str]:
    """Return list of all unique categories."""
    return list(set(info["category"] for info in TOOL_REGISTRY.values()))


def get_free_tools() -> List[str]:
    """Return list of tools with no API cost."""
    return [name for name, info in TOOL_REGISTRY.items() if info["api_cost"] == 0.0]


def get_paid_tools() -> List[str]:
    """Return list of tools with API costs."""
    return [name for name, info in TOOL_REGISTRY.items() if info["api_cost"] > 0.0]


def get_tool_summary() -> Dict[str, Any]:
    """Get summary of all registered tools."""
    categories = {}
    for name, info in TOOL_REGISTRY.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": name,
            "display_name": info["name"],
            "cost": info["api_cost"]
        })

    return {
        "total_tools": len(TOOL_REGISTRY),
        "categories": categories,
        "free_count": len(get_free_tools()),
        "paid_count": len(get_paid_tools())
    }


# =============================================================================
# TESTS
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Tool Registry Tests")
    print("=" * 60)

    # Test 1: Geocoding (requires API key)
    print("\n[Test 1] Geocoding...")
    if GOOGLE_MAPS_API_KEY:
        try:
            lat, lon, addr = geocode_address("43422 Cloister Pl, Leesburg, VA 20176")
            print(f"  ✓ Geocoded: ({lat:.6f}, {lon:.6f})")
            print(f"    Address: {addr}")
        except Exception as e:
            print(f"  ✗ Geocoding failed: {e}")
    else:
        print("  ⊘ Skipped (GOOGLE_MAPS_API_KEY not set)")

    # Test 2: Execute free tool (school_assignment)
    print("\n[Test 2] Execute tool (school_assignment)...")
    try:
        result = execute_tool("school_assignment", lat=39.112492, lon=-77.497378)
        if result["success"]:
            print(f"  ✓ Success: execution_time={result['execution_time']:.3f}s, cost=${result['cost']:.2f}")
            if result["data"]:
                schools = result["data"]
                if isinstance(schools, dict):
                    for level, school in schools.items():
                        print(f"    {level}: {school}")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Test 3: Cost calculation
    print("\n[Test 3] Cost calculation...")
    try:
        cost = calculate_query_cost(["property_valuation", "school_assignment", "neighborhood_amenities"])
        print(f"  ✓ Total cost: ${cost['total_cost']:.2f}")
        print(f"    Free tools: {cost['free_tools']}")
        print(f"    Paid tools: {cost['paid_tools']}")
        print(f"    Breakdown: {cost['breakdown']}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Test 4: Helper functions
    print("\n[Test 4] Helper functions...")
    try:
        all_tools = get_all_tool_names()
        print(f"  ✓ Total tools registered: {len(all_tools)}")

        school_tools = get_tools_by_category("schools")
        print(f"  ✓ School tools: {school_tools}")

        categories = get_all_categories()
        print(f"  ✓ Categories: {categories}")

        exists = validate_tool_exists("school_assignment")
        print(f"  ✓ validate_tool_exists('school_assignment'): {exists}")

        not_exists = validate_tool_exists("fake_tool")
        print(f"  ✓ validate_tool_exists('fake_tool'): {not_exists}")

        free = get_free_tools()
        paid = get_paid_tools()
        print(f"  ✓ Free tools: {len(free)}, Paid tools: {len(paid)}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Test 5: Cost tracker
    print("\n[Test 5] QueryCostTracker...")
    try:
        tracker = QueryCostTracker()
        tracker.log_query("Test query for schools", ["school_assignment"], 0.0)
        today_cost = tracker.get_total_cost_today()
        print(f"  ✓ Logged test query, today's cost: ${today_cost:.4f}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

    # Summary
    print("\n" + "=" * 60)
    summary = get_tool_summary()
    print(f"Tool Registry Summary: {summary['total_tools']} tools")
    print(f"  Free: {summary['free_count']}, Paid: {summary['paid_count']}")
    for cat, tools in summary['categories'].items():
        print(f"  {cat}: {len(tools)} tools")
    print("=" * 60)
