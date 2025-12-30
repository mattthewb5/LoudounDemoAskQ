#!/usr/bin/env python3
"""
Direct test of user's address through the unified assistant
Mimics exactly what Streamlit is doing
"""

from unified_ai_assistant import UnifiedAIAssistant
import os

def test_streamlit_flow():
    """Test exactly what Streamlit does"""

    # User's input
    address_input = "1398 Hancock Avenue W, Athens, GA 30606"
    question_input = "Is this a good area for families?"
    include_schools = True
    include_crime = True

    # Mimic Streamlit's address processing
    full_address = address_input
    if 'athens' not in address_input.lower():
        full_address = f"{address_input}, Athens, GA"

    print("=" * 80)
    print("TESTING STREAMLIT FLOW WITH USER'S ADDRESS")
    print("=" * 80)
    print()
    print(f"Original input: {address_input}")
    print(f"Full address: {full_address}")
    print(f"Include schools: {include_schools}")
    print(f"Include crime: {include_crime}")
    print()

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - AI responses will fail")
        print("   But address lookup should still work")
        print()

    # Initialize unified assistant
    try:
        if api_key:
            assistant = UnifiedAIAssistant(api_key=api_key)
        else:
            print("Skipping unified assistant (no API key)")
            print("Testing components directly...")
            print()

            # Test school lookup directly
            print("-" * 80)
            print("TESTING SCHOOL LOOKUP")
            print("-" * 80)
            from school_info import get_school_info
            try:
                school_info = get_school_info(full_address)
                if school_info:
                    print(f"✅ School lookup SUCCESS")
                    print(f"   Elementary: {school_info.elementary}")
                    print(f"   Middle: {school_info.middle}")
                    print(f"   High: {school_info.high}")
                else:
                    print(f"❌ School lookup returned None")
            except Exception as e:
                print(f"❌ School lookup ERROR: {e}")

            print()

            # Test crime lookup directly
            print("-" * 80)
            print("TESTING CRIME LOOKUP")
            print("-" * 80)
            from crime_analysis import analyze_crime_near_address
            try:
                crime_analysis = analyze_crime_near_address(full_address, radius_miles=0.5, months_back=12)
                if crime_analysis:
                    print(f"✅ Crime analysis SUCCESS")
                    print(f"   Safety Score: {crime_analysis.safety_score.score}/100")
                    print(f"   Total Crimes: {crime_analysis.statistics.total_crimes}")
                else:
                    print(f"❌ Crime analysis returned None")
            except Exception as e:
                print(f"❌ Crime analysis ERROR: {e}")

            return

    except ValueError as e:
        print(f"❌ Cannot initialize assistant: {e}")
        return

    # Call the same method Streamlit calls
    print("-" * 80)
    print("CALLING get_comprehensive_analysis()")
    print("-" * 80)
    print()

    result = assistant.get_comprehensive_analysis(
        address=full_address,
        question=question_input,
        include_schools=include_schools,
        include_crime=include_crime,
        radius_miles=0.5,
        months_back=12
    )

    # Display results
    print("RESULTS:")
    print("-" * 80)

    if result['error']:
        print(f"❌ ERROR: {result['error']}")
        print()

    if result['school_info']:
        print(f"✅ School Info: Found")
        print(f"   Elementary: {result['school_info'].elementary}")
        print(f"   Middle: {result['school_info'].middle}")
        print(f"   High: {result['school_info'].high}")
    else:
        print(f"❌ School Info: None")

    print()

    if result['crime_analysis']:
        print(f"✅ Crime Analysis: Found")
        print(f"   Safety Score: {result['crime_analysis'].safety_score.score}/100")
        print(f"   Total Crimes: {result['crime_analysis'].statistics.total_crimes}")
    else:
        print(f"❌ Crime Analysis: None")

    print()

    if result['synthesis']:
        print(f"✅ Synthesis: Generated")
        print(f"   Length: {len(result['synthesis'])} chars")
    else:
        print(f"❌ Synthesis: None")

    print()
    print("=" * 80)

if __name__ == "__main__":
    test_streamlit_flow()
