#!/usr/bin/env python3
"""
AI-Powered Interactive CLI for Athens-Clarke County School Lookup
Combines school data with Claude AI for natural language Q&A
"""

import sys
import os
from school_info import get_school_info, format_complete_report
from ai_school_assistant import SchoolAIAssistant


def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║         🤖 AI-POWERED SCHOOL INFORMATION LOOKUP                          ║
║                Athens-Clarke County, Georgia                              ║
║                                                                           ║
║         📚 School Assignments + Performance Data + AI Assistant           ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def interactive_mode():
    """Run in interactive AI mode"""
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("=" * 75)
        print("⚠️  ANTHROPIC_API_KEY not found")
        print("=" * 75)
        print("\nTo use AI features, set your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nFalling back to basic mode (data only, no AI analysis)")
        print("=" * 75)
        print()
        use_ai = False
        assistant = None
    else:
        try:
            assistant = SchoolAIAssistant(api_key=api_key)
            use_ai = True
            print("✓ AI Assistant ready (Claude 3 Haiku)")
            print()
        except Exception as e:
            print(f"⚠️  Could not initialize AI: {e}")
            print("Falling back to basic mode")
            print()
            use_ai = False
            assistant = None

    print_banner()
    print("Welcome! Ask me anything about schools in Athens-Clarke County.")
    print("\nExamples:")
    print("  • 'What are the test scores at 150 Hancock Avenue?'")
    print("  • 'Are the schools good near 585 Reese Street?'")
    print("  • 'Tell me about 195 Hoyt Street schools'")
    print("\nCommands: 'help', 'quit'\n")

    while True:
        try:
            # Get user input
            user_input = input("💬 Your question: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using the AI School Assistant!")
                print("Always verify information with Clarke County School District.\n")
                break

            if user_input.lower() == 'help':
                print("\n" + "=" * 75)
                print("HELP - HOW TO USE")
                print("=" * 75)
                print("\nJust ask a natural language question about any Athens address!")
                print("\nExample questions:")
                print("  - What are the schools at [address]?")
                print("  - How are the test scores at [address]?")
                print("  - Tell me about school quality near [address]")
                print("  - Are the schools good at [address]?")
                print("\nThe AI will analyze real school data and provide a balanced answer.")
                print("=" * 75)
                print()
                continue

            # Try to extract address from question
            # Simple heuristic: look for street patterns
            import re

            # Look for common patterns
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)',
                r'at\s+(\d+\s+[A-Za-z\s]+)',
                r'near\s+(\d+\s+[A-Za-z\s]+)',
            ]

            address = None
            for pattern in address_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    address = match.group(0)
                    # Clean up common prefixes
                    address = re.sub(r'^(at|near)\s+', '', address, flags=re.IGNORECASE)
                    break

            if not address:
                print("\n❌ I couldn't find an address in your question.")
                print("Please include a street address, e.g., '150 Hancock Avenue'")
                print()
                continue

            # Add Athens, GA if not present
            if 'athens' not in address.lower():
                address = f"{address}, Athens, GA"

            print(f"\n🔍 Analyzing: {address}")
            print()

            if use_ai and assistant:
                # Use AI to answer
                try:
                    response = assistant.ask_claude_about_schools(address, user_input)
                    print("🤖 AI Analysis:")
                    print("-" * 75)
                    print(response)
                    print()
                except Exception as e:
                    print(f"❌ AI Error: {e}")
                    print("\nFalling back to basic data display...")
                    # Fall back to basic display
                    info = get_school_info(address)
                    if info:
                        print(format_complete_report(info))
                    else:
                        print("Address not found in database.")
            else:
                # Basic mode without AI
                info = get_school_info(address)
                if info:
                    print("📊 School Data:")
                    print("-" * 75)
                    print(f"Elementary: {info.elementary}")
                    print(f"Middle: {info.middle}")
                    print(f"High: {info.high}")
                    print("\n(For detailed analysis, set ANTHROPIC_API_KEY)")
                else:
                    print("❌ Address not found")

            print("\n" + "=" * 75 + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point"""
    if '--help' in sys.argv or '-h' in sys.argv:
        print_banner()
        print("""
USAGE:
  python3 school_lookup_ai_cli.py

FEATURES:
  • Natural language questions about schools
  • Powered by Claude AI for intelligent answers
  • Real school data from Athens-Clarke County
  • Test scores, demographics, graduation rates

REQUIREMENTS:
  • ANTHROPIC_API_KEY environment variable
  • Get your API key at https://console.anthropic.com/

EXAMPLES:
  export ANTHROPIC_API_KEY='sk-ant-...'
  python3 school_lookup_ai_cli.py

  Then ask questions like:
  - "What are the test scores at 150 Hancock Avenue?"
  - "Are the schools good near 585 Reese Street?"
  - "Tell me about school quality for 195 Hoyt Street"
""")
        return 0

    interactive_mode()
    return 0


if __name__ == "__main__":
    sys.exit(main())
