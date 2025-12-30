#!/usr/bin/env python3
"""
Test zoning integration with unified AI assistant
"""

from unified_ai_assistant import UnifiedAIAssistant
from zoning_lookup import get_zoning_info, format_zoning_report
import os


def test_zoning_only():
    """Test just the zoning lookup"""
    print("=" * 80)
    print("TEST 1: ZONING LOOKUP ONLY")
    print("=" * 80)
    print()

    test_address = "150 Hancock Avenue, Athens, GA 30601"
    print(f"Testing address: {test_address}")
    print()

    zoning_info = get_zoning_info(test_address)

    if zoning_info:
        print(format_zoning_report(zoning_info))
    else:
        print("❌ Failed to get zoning info")

    print()


def test_unified_with_zoning():
    """Test unified assistant with zoning integrated"""
    print("=" * 80)
    print("TEST 2: UNIFIED ASSISTANT WITH ZONING")
    print("=" * 80)
    print()

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - skipping AI synthesis test")
        print("   Testing data retrieval only...")
        print()

    test_address = "1398 W Hancock Avenue, Athens, GA 30606"
    test_question = "Is this a good area for families with young kids?"

    print(f"Address: {test_address}")
    print(f"Question: {test_question}")
    print()

    try:
        if api_key:
            assistant = UnifiedAIAssistant(api_key=api_key)

            # Get comprehensive analysis with zoning
            result = assistant.get_comprehensive_analysis(
                address=test_address,
                question=test_question,
                include_schools=True,
                include_crime=True,
                include_zoning=True,
                radius_miles=0.5,
                months_back=12
            )

            print("-" * 80)
            print("RESULTS:")
            print("-" * 80)
            print()

            if result['error']:
                print(f"❌ Error: {result['error']}")
                print()

            if result['school_info']:
                print("✅ School Info: Found")
                print(f"   Elementary: {result['school_info'].elementary}")
                print(f"   Middle: {result['school_info'].middle}")
                print(f"   High: {result['school_info'].high}")
                print()

            if result['crime_analysis']:
                print("✅ Crime Analysis: Found")
                print(f"   Safety Score: {result['crime_analysis'].safety_score.score}/100")
                print(f"   Total Crimes: {result['crime_analysis'].statistics.total_crimes}")
                print()

            if result['zoning_info']:
                print("✅ Zoning Info: Found")
                print(f"   Current Zoning: {result['zoning_info'].current_zoning}")
                print(f"   Description: {result['zoning_info'].current_zoning_description}")
                print(f"   Future Land Use: {result['zoning_info'].future_land_use}")
                print(f"   Property Size: {result['zoning_info'].acres:.2f} acres")
                print()
            else:
                print("❌ Zoning Info: Not found")
                print()

            if result['synthesis']:
                print("✅ AI Synthesis: Generated")
                print()
                print("-" * 80)
                print("AI SYNTHESIS:")
                print("-" * 80)
                print()
                print(result['synthesis'])
                print()
            else:
                print("⚠️  AI Synthesis: Not generated")
                print()

        else:
            # Test without AI
            print("Testing data retrieval without AI synthesis...")
            print()

            from school_info import get_school_info
            from crime_analysis import analyze_crime_near_address

            print("1. School Lookup:")
            school_info = get_school_info(test_address)
            if school_info:
                print(f"   ✅ {school_info.elementary}, {school_info.middle}, {school_info.high}")
            else:
                print("   ❌ Failed")
            print()

            print("2. Crime Analysis:")
            crime_analysis = analyze_crime_near_address(test_address, 0.5, 12)
            if crime_analysis:
                print(f"   ✅ Safety Score: {crime_analysis.safety_score.score}/100")
            else:
                print("   ❌ Failed")
            print()

            print("3. Zoning Lookup:")
            zoning_info = get_zoning_info(test_address)
            if zoning_info:
                print(f"   ✅ {zoning_info.current_zoning}: {zoning_info.current_zoning_description}")
            else:
                print("   ❌ Failed")
            print()

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    test_zoning_only()
    print()
    print()
    test_unified_with_zoning()

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
