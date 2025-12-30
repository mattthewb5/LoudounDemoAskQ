#!/usr/bin/env python3
"""
Test crime analysis with Athens-wide comparison
"""

import os
from crime_ai_assistant import CrimeAIAssistant


def main():
    """Test comparison with 3 standard addresses"""

    test_addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    question = "How safe is this neighborhood?"

    print("=" * 80)
    print("CRIME AI ASSISTANT - COMPARISON TO ATHENS AVERAGE TEST")
    print("=" * 80)
    print(f"\nQuestion: {question}")
    print(f"Testing with 3 addresses\n")

    # Initialize assistant
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ Error: ANTHROPIC_API_KEY not found")
            print("\nPlease set your ANTHROPIC_API_KEY environment variable:")
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
            return

        assistant = CrimeAIAssistant(api_key=api_key)

    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    # Test each address
    for i, address in enumerate(test_addresses, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i} of 3")
        print(f"{'='*80}")
        print(f"\nAddress: {address}")
        print(f"Question: {question}\n")
        print("-" * 80)

        try:
            answer = assistant.answer_crime_question(
                address=address,
                question=question,
                radius_miles=0.5,
                months_back=12
            )

            print("\nRESPONSE:")
            print(answer)
            print("\n" + "-" * 80)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nVerify each response includes:")
    print("  ✓ Citation with date range")
    print("  ✓ Supporting statistics")
    print("  ✓ **Comparison to Athens average**")
    print("  ✓ Relative ranking (high/low activity area)")
    print("  ✓ Trend information")
    print("  ✓ Data source with crime map link")
    print("  ✓ All required disclaimers")


if __name__ == "__main__":
    main()
