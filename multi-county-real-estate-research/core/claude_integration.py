"""
Claude API Integration for Loudoun County Real Estate Chatbot

Handles multi-turn conversations with Claude API including automatic tool
execution via the tool registry. Supports all 20 registered analysis tools.

Usage:
    from core.claude_integration import ClaudeChatHandler

    handler = ClaudeChatHandler()
    result = handler.chat("What schools serve 43422 Cloister Pl?")
    print(result["response_text"])
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure core module is importable
_CORE_DIR = Path(__file__).parent
_PACKAGE_DIR = _CORE_DIR.parent
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

from core.tool_registry import (
    TOOL_REGISTRY,
    execute_tool,
    geocode_address,
    calculate_query_cost,
    get_all_tool_names,
    QueryCostTracker
)

# Try to import anthropic - graceful fallback if not installed
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Anthropic = None

# Model configuration - try multiple models for compatibility
DEFAULT_MODEL = "claude-sonnet-4-5-20241022"
FALLBACK_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307"
]
MAX_TOKENS = 4096

# Token cost estimates (per million tokens) - Claude Sonnet
INPUT_COST_PER_MILLION = 3.00
OUTPUT_COST_PER_MILLION = 15.00

# Expanded tool descriptions for better Claude understanding
EXPANDED_DESCRIPTIONS = {
    "property_valuation": (
        "Get comprehensive property valuation for a Loudoun County address. "
        "Returns current estimated market value, 3-year price projections, "
        "rental income estimates, and value per square foot analysis. "
        "Uses RentCast API data combined with local sales comparables. "
        "Note: This tool has an API cost of $0.10 per call."
    ),
    "sales_comparables": (
        "Find recent comparable property sales within a specified radius. "
        "Returns details on similar homes that have sold recently including "
        "sale price, date, square footage, bedrooms, and price per square foot. "
        "Useful for understanding local market activity and supporting valuations. "
        "Default radius is 1 mile; increase for rural areas with fewer sales."
    ),
    "school_assignment": (
        "Find the assigned public schools (elementary, middle, and high school) "
        "for a location in Loudoun County, Virginia. Returns the specific LCPS "
        "schools that serve the given address based on official attendance zone "
        "boundaries. Use this when a user asks about schools, school districts, "
        "or educational options for a property."
    ),
    "school_performance": (
        "Get academic performance metrics and percentile rankings for a specific "
        "Loudoun County school. Returns SOL pass rates, state percentile rankings, "
        "and year-over-year trends. Use after getting school assignment to provide "
        "detailed performance context for each assigned school."
    ),
    "location_quality": (
        "Comprehensive location quality analysis for a property. Evaluates road type "
        "(cul-de-sac, through street, busy road), airport noise exposure, proximity "
        "to metro stations, and overall location characteristics. Provides both "
        "qualitative assessment and numerical quality scores."
    ),
    "power_lines": (
        "Check proximity to high-voltage power transmission lines. Returns distance "
        "to nearest transmission lines and assesses potential impact on property "
        "value and livability. Important for properties near utility corridors."
    ),
    "cell_coverage": (
        "Analyze cellular network coverage based on nearby cell tower locations. "
        "Returns information about carriers present, tower distances, and expected "
        "signal quality. Useful for buyers concerned about mobile connectivity."
    ),
    "flood_zone": (
        "Check FEMA flood zone designation for a location. Returns the official "
        "flood zone code (A, AE, X, etc.), risk level description, and whether "
        "flood insurance is typically required. Critical for properties near "
        "streams, rivers, or low-lying areas."
    ),
    "metro_access": (
        "Analyze proximity and access to Washington Metro Silver Line stations. "
        "Returns distance to nearest stations (Ashburn, Loudoun Gateway, etc.), "
        "estimated drive times, and commute accessibility tier. Important for "
        "commuters working in DC, Tysons, or Reston."
    ),
    "traffic_volume": (
        "Get traffic volume data for roads near a property. Returns average daily "
        "traffic counts for nearby roads, traffic level classification, and "
        "potential noise/congestion impact. Useful for properties on or near "
        "major roads like Route 7, Route 50, or Loudoun County Parkway."
    ),
    "development_pressure": (
        "Analyze development pressure and construction activity near a property. "
        "Reviews recent building permits, planned developments, and rezoning "
        "applications. Helps assess whether the area is stable, growing, or "
        "undergoing significant change."
    ),
    "infrastructure_activity": (
        "Detect data center and major infrastructure development activity nearby. "
        "Loudoun County hosts significant data center development. Returns "
        "information about planned or under-construction data centers, substations, "
        "and other infrastructure within the specified radius."
    ),
    "zoning_context": (
        "Get zoning designation and development context for a property. Returns "
        "the current zoning code, allowed uses, density limits, and any overlay "
        "districts. Also indicates development probability based on zoning vs "
        "current use analysis."
    ),
    "community_lookup": (
        "Get community and subdivision context for a property. Returns HOA "
        "information, community amenities, neighborhood character, and any "
        "special assessments or covenants. Requires the subdivision name."
    ),
    "parks_access": (
        "Find nearby parks and recreational facilities. Returns list of county "
        "and regional parks within walking/driving distance, including park "
        "amenities like trails, playgrounds, sports fields, and dog parks."
    ),
    "neighborhood_amenities": (
        "Find nearby restaurants, shops, grocery stores, and amenities using "
        "Google Places data. Returns categorized list of local businesses with "
        "ratings and distances. Note: This tool has an API cost of $0.02 per call."
    ),
    "pharmacy_access": (
        "Find nearby pharmacies including 24-hour options. Returns list of "
        "pharmacies with distances, hours, and whether they offer 24-hour service. "
        "Note: This tool has an API cost of $0.01 per call."
    ),
    "healthcare_access": (
        "Analyze access to hospitals, urgent care, and medical facilities. "
        "Returns nearest hospitals with trauma level and specialties, urgent "
        "care locations, and overall healthcare accessibility score."
    ),
    "demographics": (
        "Get demographic data for the area around a property. Returns population "
        "statistics, median household income, age distribution, education levels, "
        "and housing characteristics from Census data."
    ),
    "economic_indicators": (
        "Get economic context for Loudoun County including major employers, "
        "job market trends, unemployment rates, and industry mix. Provides "
        "county-wide economic health indicators."
    )
}


# =============================================================================
# SCHEMA CONVERTER
# =============================================================================

def convert_to_claude_tools(tool_names: Optional[List[str]] = None) -> List[Dict]:
    """
    Convert TOOL_REGISTRY entries to Claude API tool format.

    Args:
        tool_names: Specific tools to include, or None for all 20 tools

    Returns:
        List of tool dicts in Claude API format:
        [{"name": str, "description": str, "input_schema": dict}]
    """
    tools = []
    registry_items = tool_names if tool_names else list(TOOL_REGISTRY.keys())

    for tool_name in registry_items:
        if tool_name not in TOOL_REGISTRY:
            continue

        info = TOOL_REGISTRY[tool_name]

        # Use expanded description if available, otherwise use original
        description = EXPANDED_DESCRIPTIONS.get(tool_name, info["description"])

        # Build input schema with address option for coordinate-based tools
        input_schema = _build_flexible_schema(tool_name, info)

        tools.append({
            "name": tool_name,
            "description": description,
            "input_schema": input_schema
        })

    return tools


def _build_flexible_schema(tool_name: str, tool_info: Dict) -> Dict:
    """
    Build input schema that allows either address or coordinates.

    For coordinate-based tools, adds an address option so Claude can
    pass either format and we handle geocoding.
    """
    original_schema = tool_info["input_schema"].copy()
    input_type = tool_info.get("input_type", "")

    # For coordinate-based tools, add address as an alternative
    if input_type in ["coordinates", "coordinates_tuple", "coordinates_and_address"]:
        properties = original_schema.get("properties", {}).copy()

        # Add address option if not already present
        if "address" not in properties:
            properties["address"] = {
                "type": "string",
                "description": "Full property address (e.g., '43422 Cloister Pl, Leesburg, VA 20176'). Provide address OR lat/lon coordinates."
            }

        # Update lat/lon descriptions to indicate they're alternatives
        if "lat" in properties:
            properties["lat"] = {
                "type": "number",
                "description": "Latitude coordinate. Use if address not provided."
            }
        if "lon" in properties:
            properties["lon"] = {
                "type": "number",
                "description": "Longitude coordinate. Use if address not provided."
            }

        # Make required empty - we validate one or the other
        return {
            "type": "object",
            "properties": properties,
            "required": []
        }

    return original_schema


# =============================================================================
# CHAT HANDLER
# =============================================================================

class ClaudeChatHandler:
    """Handle multi-turn conversations with Claude API including tool execution."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize with Anthropic API key.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            model: Model to use (default: claude-sonnet-4-5-20241022)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.cost_tracker = QueryCostTracker()

        # Cache for geocoded addresses
        self._geocode_cache: Dict[str, Tuple[float, float, str]] = {}

    def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        available_tools: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete chat cycle with tool calling.

        Args:
            user_message: User's question
            conversation_history: Previous messages in Claude API format
            available_tools: Specific tools to make available (None = all 20)
            system_prompt: Custom system prompt (uses default if not provided)

        Returns:
            {
                "response_text": str,           # Claude's final answer
                "tools_called": List[str],      # Tools executed
                "tool_results": Dict,           # Raw tool outputs keyed by tool name
                "total_cost": float,            # Estimated API + tool cost
                "input_tokens": int,            # Total input tokens used
                "output_tokens": int,           # Total output tokens used
                "conversation_history": List,   # Updated history for next call
                "geocoded_address": Optional[Dict]  # If address was geocoded
            }
        """
        start_time = time.time()

        # Initialize tracking
        tools_called = []
        tool_results = {}
        total_input_tokens = 0
        total_output_tokens = 0
        geocoded_info = None

        # Build messages
        messages = list(conversation_history) if conversation_history else []
        messages.append({"role": "user", "content": user_message})

        # Get tools
        tools = convert_to_claude_tools(available_tools)

        # Build system prompt
        if system_prompt is None:
            system_prompt = self._build_system_prompt()

        # Initial API call with model fallback
        response = None
        last_error = None
        models_to_try = [self.model] + FALLBACK_MODELS

        for model in models_to_try:
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    tools=tools,
                    messages=messages
                )
                self.model = model  # Remember working model
                break
            except Exception as e:
                last_error = e
                if "not_found" in str(e).lower() or "404" in str(e):
                    continue  # Try next model
                else:
                    raise  # Other errors should propagate

        if response is None:
            raise last_error or Exception("No working model found")

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Process response - may need multiple rounds for tool calls
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while response.stop_reason == "tool_use" and iteration < max_iterations:
            iteration += 1

            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": self._serialize_content(response.content)
            })

            # Execute all tool calls
            tool_result_blocks = []

            for block in response.content:
                if hasattr(block, 'type') and block.type == "tool_use":
                    tool_name = block.name
                    tool_input = dict(block.input)
                    tool_use_id = block.id

                    tools_called.append(tool_name)

                    # Execute tool with geocoding if needed
                    result, geo_info = self._execute_tool_with_geocoding(
                        tool_name, tool_input
                    )

                    if geo_info:
                        geocoded_info = geo_info

                    tool_results[tool_name] = result

                    # Build tool result block
                    if result["success"]:
                        tool_result_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result["data"], default=str)
                        })
                    else:
                        tool_result_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Error: {result.get('error', 'Unknown error')}",
                            "is_error": True
                        })

            # Add tool results to messages
            messages.append({
                "role": "user",
                "content": tool_result_blocks
            })

            # Get next response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

        # Extract final text response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        # Add final response to messages
        messages.append({
            "role": "assistant",
            "content": self._serialize_content(response.content)
        })

        # Calculate costs
        api_cost = self._estimate_api_cost(total_input_tokens, total_output_tokens)
        tool_cost_info = calculate_query_cost(tools_called)
        total_cost = api_cost + tool_cost_info["total_cost"]

        # Log cost
        self.cost_tracker.log_query(
            user_message[:100],
            tools_called,
            total_cost
        )

        return {
            "response_text": response_text,
            "tools_called": tools_called,
            "tool_results": tool_results,
            "total_cost": total_cost,
            "api_cost": api_cost,
            "tool_cost": tool_cost_info["total_cost"],
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "conversation_history": messages,
            "geocoded_address": geocoded_info,
            "execution_time": time.time() - start_time
        }

    def _execute_tool_with_geocoding(
        self,
        tool_name: str,
        tool_input: Dict
    ) -> Tuple[Dict, Optional[Dict]]:
        """
        Execute a tool, handling geocoding if needed.

        Returns:
            (tool_result, geocoded_info)
        """
        geocoded_info = None

        # Check if we need to geocode
        if "address" in tool_input and "lat" not in tool_input:
            address = tool_input["address"]

            # Check cache first
            if address in self._geocode_cache:
                lat, lon, formatted = self._geocode_cache[address]
            else:
                try:
                    lat, lon, formatted = geocode_address(address)
                    self._geocode_cache[address] = (lat, lon, formatted)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Geocoding failed: {str(e)}",
                        "tool_name": tool_name
                    }, None

            tool_input["lat"] = lat
            tool_input["lon"] = lon
            geocoded_info = {
                "address": address,
                "formatted_address": formatted,
                "lat": lat,
                "lon": lon
            }

        # Execute the tool
        try:
            result = execute_tool(tool_name, **tool_input)
            return result, geocoded_info
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }, geocoded_info

    def _serialize_content(self, content) -> List[Dict]:
        """Serialize response content to JSON-compatible format."""
        serialized = []
        for block in content:
            if hasattr(block, 'type'):
                if block.type == "text":
                    serialized.append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    serialized.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": dict(block.input)
                    })
        return serialized

    def _estimate_api_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost from token usage."""
        input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
        output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION
        return input_cost + output_cost

    def _build_system_prompt(self) -> str:
        """Build the default system prompt."""
        return """You are a helpful real estate research assistant for Loudoun County, Virginia.

You have access to comprehensive property analysis tools including:
- Property valuation and sales comparables
- School assignments and performance data
- Location quality analysis (traffic, metro access, utilities)
- Zoning and development pressure analysis
- Neighborhood amenities and healthcare access
- Demographics and economic indicators

When a user asks about a property:
1. Use the appropriate tools to gather relevant information
2. Synthesize the results into a clear, helpful response
3. Highlight key findings and any concerns
4. Be specific with numbers, distances, and school names

If a user asks a follow-up question about "the property" or "this address" without specifying,
use the same coordinates from the previous tool calls.

Always be accurate and cite specific data from the tool results. If a tool fails or returns
an error, acknowledge this and explain what information is unavailable."""


def get_handler(api_key: Optional[str] = None) -> ClaudeChatHandler:
    """Convenience function to get a ClaudeChatHandler instance."""
    return ClaudeChatHandler(api_key=api_key)


# =============================================================================
# TESTS
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Claude Integration Tests")
    print("=" * 70)

    # Test 1: Schema conversion
    print("\n[Test 1] Schema Conversion...")
    try:
        tools = convert_to_claude_tools(["school_assignment", "flood_zone"])
        print(f"  Converted {len(tools)} tools")
        for tool in tools:
            print(f"    - {tool['name']}: {len(tool['description'])} chars")
            props = list(tool['input_schema'].get('properties', {}).keys())
            print(f"      Properties: {props}")
        print("  [PASS]")
    except Exception as e:
        print(f"  [FAIL] {e}")

    # Test 2: All tools conversion
    print("\n[Test 2] Convert All 20 Tools...")
    try:
        all_tools = convert_to_claude_tools()
        print(f"  Converted {len(all_tools)} tools")

        # Check all have expanded descriptions
        short_desc = [t['name'] for t in all_tools if len(t['description']) < 100]
        if short_desc:
            print(f"  Warning: Short descriptions: {short_desc}")
        else:
            print("  All tools have expanded descriptions (100+ chars)")
        print("  [PASS]")
    except Exception as e:
        print(f"  [FAIL] {e}")

    # Test 3: Chat handler initialization
    print("\n[Test 3] Chat Handler Initialization...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [SKIP] ANTHROPIC_API_KEY not set")
    elif not ANTHROPIC_AVAILABLE:
        print("  [SKIP] anthropic package not installed")
    else:
        try:
            handler = ClaudeChatHandler()
            print(f"  Handler initialized with model: {handler.model}")
            print("  [PASS]")
        except Exception as e:
            print(f"  [FAIL] {e}")

    # Test 4: Live chat test (only if API key available)
    print("\n[Test 4] Live Chat Test...")
    if not api_key:
        print("  [SKIP] ANTHROPIC_API_KEY not set")
    elif not ANTHROPIC_AVAILABLE:
        print("  [SKIP] anthropic package not installed")
    else:
        try:
            handler = ClaudeChatHandler()

            # Use only free tools for testing
            result = handler.chat(
                "What schools serve 43422 Cloister Pl, Leesburg VA?",
                available_tools=["school_assignment"]
            )

            print(f"  Response length: {len(result['response_text'])} chars")
            print(f"  Tools called: {result['tools_called']}")
            print(f"  API cost: ${result['api_cost']:.4f}")
            print(f"  Tool cost: ${result['tool_cost']:.4f}")
            print(f"  Total cost: ${result['total_cost']:.4f}")
            print(f"  Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
            print(f"  Execution time: {result['execution_time']:.2f}s")

            if result['geocoded_address']:
                geo = result['geocoded_address']
                print(f"  Geocoded: ({geo['lat']:.6f}, {geo['lon']:.6f})")

            print(f"\n  Response preview:")
            print(f"  {result['response_text'][:300]}...")
            print("  [PASS]")

        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()

    # Test 5: Multi-tool query (only if API key available)
    print("\n[Test 5] Multi-Tool Query...")
    if not api_key:
        print("  [SKIP] ANTHROPIC_API_KEY not set")
    elif not ANTHROPIC_AVAILABLE:
        print("  [SKIP] anthropic package not installed")
    else:
        try:
            handler = ClaudeChatHandler()

            # Query that should trigger multiple tools
            result = handler.chat(
                "Tell me about schools and flood risk at 43422 Cloister Pl, Leesburg VA",
                available_tools=["school_assignment", "flood_zone"]
            )

            print(f"  Tools called: {result['tools_called']}")
            print(f"  Total cost: ${result['total_cost']:.4f}")
            print(f"  Execution time: {result['execution_time']:.2f}s")

            if len(result['tools_called']) >= 2:
                print("  Multiple tools executed!")

            print("  [PASS]")

        except Exception as e:
            print(f"  [FAIL] {e}")

    print("\n" + "=" * 70)
    print("Tests Complete")
    print("=" * 70)
