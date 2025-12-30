"""
Loudoun County Community Lookup Module
======================================

This module provides functionality to:
1. Match a property's subdivision to a community
2. Return community amenities and HOA information
3. Integrate with RentCast API subdivision data

Usage:
    from loudoun_community_lookup import CommunityLookup
    
    lookup = CommunityLookup()
    community = lookup.get_community_for_subdivision("BRAMBLETON SECTION 42")
    
    if community:
        print(f"Community: {community['display_name']}")
        print(f"HOA Fees: ${community['fees'].get('single_family_monthly', 'N/A')}/month")
        print(f"Pools: {community['amenities'].get('pools', 'N/A')}")
"""

import json
import re
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any


class CommunityLookup:
    """Lookup community information based on subdivision name"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the community lookup.
        
        Args:
            config_path: Path to communities.json file. If None, looks in standard locations.
        """
        self.config_path = config_path or self._find_config()
        self.communities = {}
        self._pattern_cache = {}
        self._load_communities()
    
    def _find_config(self) -> str:
        """Find the communities.json config file"""
        # Check common locations
        possible_paths = [
            Path(__file__).parent.parent / "data" / "loudoun" / "config" / "communities.json",
            Path("data/loudoun/config/communities.json"),
            Path("config/communities.json"),
            Path("communities.json"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        raise FileNotFoundError(
            "Could not find communities.json. "
            "Please provide the config_path parameter."
        )
    
    def _load_communities(self):
        """Load communities from config file"""
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        self.communities = data.get('communities', {})
        self._build_pattern_cache()
    
    def _build_pattern_cache(self):
        """Build a cache of subdivision patterns to community keys"""
        self._pattern_cache = {}
        
        for community_key, community in self.communities.items():
            patterns = community.get('subdivision_patterns', [])
            exclude_patterns = community.get('exclude_patterns', [])
            
            for pattern in patterns:
                self._pattern_cache[pattern.upper()] = {
                    'community_key': community_key,
                    'exclude_patterns': [p.upper() for p in exclude_patterns]
                }
    
    def normalize_subdivision_name(self, name: str) -> str:
        """
        Normalize a subdivision name for matching.
        
        Handles variations like:
        - "BRAMBLETON SEC 42" -> "BRAMBLETON SECTION 42"
        - "brambleton section 42" -> "BRAMBLETON SECTION 42"
        """
        if not name:
            return ""
        
        name = name.upper().strip()
        
        # Normalize common abbreviations
        replacements = {
            ' SEC ': ' SECTION ',
            ' SEC. ': ' SECTION ',
            ' PH ': ' PHASE ',
            ' PH. ': ' PHASE ',
            ' PT ': ' PART ',
            ' PT. ': ' PART ',
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name
    
    def get_community_key_for_subdivision(self, subdivision_name: str) -> Optional[str]:
        """
        Find the community key for a given subdivision name.
        
        Args:
            subdivision_name: The subdivision name from county records or RentCast API
            
        Returns:
            Community key (e.g., 'brambleton') or None if not found
        """
        if not subdivision_name:
            return None
        
        normalized = self.normalize_subdivision_name(subdivision_name)
        
        for pattern, info in self._pattern_cache.items():
            # Check if matches the pattern
            if fnmatch.fnmatch(normalized, pattern):
                # Check if excluded
                excluded = False
                for exclude_pattern in info['exclude_patterns']:
                    if fnmatch.fnmatch(normalized, exclude_pattern):
                        excluded = True
                        break
                
                if not excluded:
                    return info['community_key']
        
        return None
    
    def get_community_for_subdivision(self, subdivision_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full community information for a subdivision.
        
        Args:
            subdivision_name: The subdivision name from county records or RentCast API
            
        Returns:
            Community dict with all available information, or None if not found
        """
        community_key = self.get_community_key_for_subdivision(subdivision_name)
        
        if community_key:
            community = self.communities.get(community_key, {}).copy()
            community['_community_key'] = community_key
            community['_matched_subdivision'] = subdivision_name
            return community
        
        return None
    
    def get_community_by_key(self, community_key: str) -> Optional[Dict[str, Any]]:
        """Get community by its key directly"""
        return self.communities.get(community_key)
    
    def list_communities(self) -> List[str]:
        """List all known community keys"""
        return list(self.communities.keys())

    def get_community_key_by_display_name(self, display_name: str) -> Optional[str]:
        """
        Find community key by display name for spatial integration.

        Args:
            display_name: Display name from GIS (e.g., "River Creek")

        Returns:
            Community key (e.g., "river_creek") if found, None otherwise
        """
        if not display_name:
            return None

        # Exact match first
        for key, community in self.communities.items():
            if community.get('display_name') == display_name:
                return key

        # Case-insensitive fallback
        display_lower = display_name.lower()
        for key, community in self.communities.items():
            if community.get('display_name', '').lower() == display_lower:
                return key

        return None

    def get_community_summary(self, community_key: str) -> Dict[str, Any]:
        """
        Get a summary of community info suitable for display.
        
        Returns a cleaned-up dict with the most relevant information.
        """
        community = self.communities.get(community_key)
        if not community:
            return None
        
        amenities = community.get('amenities', {})
        fees = community.get('fees', {})
        
        # Build amenity list
        amenity_list = []
        
        if amenities.get('pools'):
            pool_count = amenities['pools']
            amenity_list.append(f"{pool_count} pool{'s' if pool_count > 1 else ''}")
        
        if amenities.get('fitness_centers'):
            amenity_list.append("Fitness center")
        
        if amenities.get('tennis_courts'):
            court_count = amenities['tennis_courts']
            amenity_list.append(f"{court_count} tennis court{'s' if court_count > 1 else ''}")
        
        if amenities.get('trails_miles'):
            amenity_list.append(f"{amenities['trails_miles']}+ miles of trails")
        elif amenities.get('trails_notes'):
            amenity_list.append("Walking trails")
        
        if amenities.get('clubhouse'):
            amenity_list.append("Clubhouse")
        
        golf = amenities.get('golf', {})
        if isinstance(golf, dict) and golf.get('on_site'):
            amenity_list.append(f"{golf.get('holes', 18)}-hole golf course")
        elif isinstance(golf, dict) and golf.get('nearby'):
            amenity_list.append(f"Golf nearby: {golf['nearby']}")
        
        if amenities.get('tot_lots'):
            amenity_list.append(f"{amenities['tot_lots']} playgrounds/tot lots")
        
        town_center = amenities.get('town_center', {})
        if isinstance(town_center, dict) and town_center.get('has_town_center'):
            amenity_list.append("Town center")
        
        # Determine monthly fee
        monthly_fee = None
        fee_type = None
        
        if fees.get('single_family_monthly'):
            monthly_fee = fees['single_family_monthly']
            fee_type = "Single Family"
        elif fees.get('hoa_monthly'):
            monthly_fee = fees['hoa_monthly']
            fee_type = "HOA"
        elif fees.get('club_monthly'):
            monthly_fee = fees['club_monthly']
            fee_type = "Club membership"
        
        return {
            'display_name': community.get('display_name', community_key),
            'location': community.get('location'),
            'community_type': community.get('community_type'),
            'hoa_website': community.get('hoa_website'),
            'management_company': community.get('management_company'),
            'total_homes': community.get('total_homes'),
            'total_acres': community.get('total_acres'),
            'monthly_fee': monthly_fee,
            'fee_type': fee_type,
            'fee_year': fees.get('fee_year'),
            'fee_includes': fees.get('includes', []),
            'amenities_list': amenity_list,
            'amenities_detail': amenities,
            'schools': community.get('schools'),
            'gated': community.get('community_type') == 'gated_golf' or 'gated' in str(amenities.get('other', [])).lower()
        }
    
    def format_for_display(self, subdivision_name: str) -> Optional[str]:
        """
        Format community information for display in the UI.
        
        Returns a formatted string suitable for the "Community & Amenities" section.
        """
        community = self.get_community_for_subdivision(subdivision_name)
        if not community:
            return None
        
        summary = self.get_community_summary(community['_community_key'])
        
        lines = []
        lines.append(f"**{summary['display_name']}**")
        
        if summary.get('monthly_fee'):
            fee_str = f"${summary['monthly_fee']:.0f}/month"
            if summary.get('fee_type') and summary['fee_type'] != 'HOA':
                fee_str += f" ({summary['fee_type']})"
            if summary.get('fee_year'):
                fee_str += f" ({summary['fee_year']})"
            lines.append(f"HOA/Dues: {fee_str}")
        
        if summary.get('hoa_website'):
            lines.append(f"Website: {summary['hoa_website']}")
        
        if summary.get('amenities_list'):
            lines.append("")
            lines.append("**Community Amenities:**")
            for amenity in summary['amenities_list']:
                lines.append(f"• {amenity}")
        
        if summary.get('gated'):
            lines.append("")
            lines.append("🔒 Gated Community")
        
        return "\n".join(lines)


def create_property_community_context(
    subdivision_name: str,
    hoa_fee_from_api: Optional[float] = None,
    lookup: CommunityLookup = None
) -> Dict[str, Any]:
    """
    Create community context for a property, combining our data with API data.
    
    This is the main integration function for the Streamlit app.
    
    Args:
        subdivision_name: Subdivision name from RentCast or county records
        hoa_fee_from_api: HOA fee from RentCast API (if available)
        lookup: CommunityLookup instance (creates new one if not provided)
        
    Returns:
        Dict with all available community context
    """
    if lookup is None:
        try:
            lookup = CommunityLookup()
        except FileNotFoundError:
            # No config file available
            return {
                'community_found': False,
                'subdivision_name': subdivision_name,
                'hoa_fee': hoa_fee_from_api
            }
    
    community = lookup.get_community_for_subdivision(subdivision_name)
    
    if community:
        summary = lookup.get_community_summary(community['_community_key'])
        
        # Prefer API fee if available and more recent
        monthly_fee = hoa_fee_from_api or summary.get('monthly_fee')
        
        return {
            'community_found': True,
            'community_key': community['_community_key'],
            'display_name': summary['display_name'],
            'location': summary.get('location'),
            'subdivision_name': subdivision_name,
            'hoa_website': summary.get('hoa_website'),
            'management_company': summary.get('management_company'),
            'monthly_fee': monthly_fee,
            'fee_source': 'API' if hoa_fee_from_api else 'Community Data',
            'fee_year': summary.get('fee_year'),
            'fee_includes': summary.get('fee_includes', []),
            'amenities': summary.get('amenities_list', []),
            'amenities_detail': summary.get('amenities_detail', {}),
            'schools': summary.get('schools'),
            'total_homes': summary.get('total_homes'),
            'total_acres': summary.get('total_acres'),
            'gated': summary.get('gated', False)
        }
    
    # No community match found - return basic info
    return {
        'community_found': False,
        'subdivision_name': subdivision_name,
        'hoa_fee': hoa_fee_from_api,
        'display_name': subdivision_name.title() if subdivision_name else None
    }


# Example usage and testing
if __name__ == '__main__':
    # Test the lookup
    print("Testing Community Lookup Module")
    print("=" * 50)
    
    try:
        lookup = CommunityLookup()
        print(f"Loaded {len(lookup.communities)} communities")
        print(f"Communities: {', '.join(lookup.list_communities())}")
        print()
        
        # Test subdivisions
        test_subdivisions = [
            "BRAMBLETON SECTION 42",
            "RIVER CREEK PHASE 2",
            "BROADLANDS SECTION 10",
            "RANDOM SUBDIVISION",
            "BIRCHWOOD AT BRAMBLETON",  # Should be excluded from main Brambleton
            None,
        ]
        
        for subdiv in test_subdivisions:
            print(f"\nTesting: {subdiv}")
            result = lookup.get_community_for_subdivision(subdiv)
            if result:
                print(f"  → Community: {result['display_name']}")
                summary = lookup.get_community_summary(result['_community_key'])
                if summary.get('monthly_fee'):
                    print(f"  → Fee: ${summary['monthly_fee']}/month")
                if summary.get('amenities_list'):
                    print(f"  → Amenities: {', '.join(summary['amenities_list'][:3])}...")
            else:
                print(f"  → No community match")
        
        print("\n" + "=" * 50)
        print("\nFormatted display for River Creek:")
        print(lookup.format_for_display("RIVER CREEK"))
        
    except FileNotFoundError as e:
        print(f"Config not found: {e}")
        print("This is expected if running outside the project directory.")
