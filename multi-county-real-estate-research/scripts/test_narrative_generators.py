"""
Test narrative generation functions with real data
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.loudoun_zoning_analysis import (
    characterize_building_permits,
    analyze_zone_proximity,
    generate_zoning_narrative,
    generate_permit_narrative,
    generate_nearby_zoning_narrative
)
import json

print("=" * 80)
print("NARRATIVE GENERATOR TESTING")
print("=" * 80)

# Test property: 43422 Cloister Pl, Leesburg
test_lat = 39.112492
test_lon = -77.497378

# Load translations
data_dir = project_root / 'data' / 'loudoun' / 'config'
with open(data_dir / 'zoning_translations.json') as f:
    zoning_trans_file = json.load(f)
    # Extract static translations for direct lookup
    zoning_trans = zoning_trans_file.get('static_translations', {})
with open(data_dir / 'placetype_translations.json') as f:
    place_trans_file = json.load(f)
    # Extract translations for direct lookup
    place_trans = place_trans_file.get('translations', {})

print("\n1. TESTING generate_zoning_narrative()")
print("-" * 80)

zoning_data = zoning_trans.get('PDH3', {})
place_data = place_trans.get('LJLMRN', {})  # Leesburg JLMA Residential Neighborhood
community_data = {
    'name': 'River Creek',
    'amenities': ['pool', 'tennis courts', 'clubhouse', '18-hole golf course']
}

zoning_narrative = generate_zoning_narrative(zoning_data, place_data, community_data)
print(zoning_narrative)
print(f"\nWord count: {len(zoning_narrative.split())}")
print(f"Paragraph count: {zoning_narrative.count(chr(10) + chr(10)) + 1}")

print("\n" + "=" * 80)
print("2. TESTING generate_permit_narrative()")
print("-" * 80)

permit_data = characterize_building_permits(test_lat, test_lon, radius_miles=2)

if permit_data:
    permit_narrative = generate_permit_narrative(
        permit_data,
        permit_data['recent_activity'],
        permit_data.get('property_community')
    )
    print(permit_narrative)
    print(f"\nWord count: {len(permit_narrative.split())}")
    print(f"Paragraph count: {permit_narrative.count(chr(10) + chr(10)) + 1}")

    print(f"\nData used:")
    print(f"  Total permits: {permit_data['total_permits']}")
    print(f"  Activity level: {permit_data['recent_activity']}")
    print(f"  Major projects: {len(permit_data.get('major_projects', []))}")
    print(f"  Property community: {permit_data.get('property_community')}")
else:
    print("ERROR: Could not load permit data")
    permit_narrative = ""

print("\n" + "=" * 80)
print("3. TESTING generate_nearby_zoning_narrative()")
print("-" * 80)

# Use actual zone proximity data
zone_proximity = analyze_zone_proximity(test_lat, test_lon, radius_miles=5)

translations = {
    'zoning_translations': zoning_trans,
    'placetype_translations': place_trans
}

if zone_proximity:
    zoning_context_narrative = generate_nearby_zoning_narrative(
        zone_proximity,
        'PDH3',
        translations
    )
    print(zoning_context_narrative)
    print(f"\nWord count: {len(zoning_context_narrative.split())}")
    print(f"Paragraph count: {zoning_context_narrative.count(chr(10) + chr(10)) + 1}")
    print(f"\nZones analyzed: {len(zone_proximity)}")
else:
    print("ERROR: Could not load zone proximity data")
    zoning_context_narrative = ""

print("\n" + "=" * 80)
print("QUALITY CHECKS")
print("=" * 80)

def check_quality(name, narrative):
    if not narrative:
        print(f"\n{name}: SKIPPED (no narrative)")
        return False

    checks = {
        'Has bullet points': '•' in narrative or ('\n- ' in narrative and '- ' in narrative.replace('well-', '').replace('non-', '')),
        'Has hedging words': any(word in narrative.lower() for word in ['fairly stable', 'solid option', 'depends on priorities']),
        'Too short (<100 words)': len(narrative.split()) < 100,
        'Too long (>800 words)': len(narrative.split()) > 800,
        'Generic phrases': any(phrase in narrative.lower() for phrase in ['this area is expected to', 'will likely see'])
    }

    print(f"\n{name}:")
    all_pass = True
    for check, failed in checks.items():
        status = "❌ FAIL" if failed else "✅ PASS"
        if failed:
            all_pass = False
        print(f"  {status}: {check}")

    return all_pass

all_pass = True
all_pass &= check_quality("Zoning Narrative", zoning_narrative)
all_pass &= check_quality("Permit Narrative", permit_narrative)
all_pass &= check_quality("Zoning Context Narrative", zoning_context_narrative)

print("\n" + "=" * 80)
if all_pass:
    print("✅ ALL QUALITY CHECKS PASSED")
else:
    print("⚠️ SOME QUALITY CHECKS FAILED - REVIEW OUTPUT")
print("=" * 80)
