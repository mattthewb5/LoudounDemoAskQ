#!/usr/bin/env python3
"""
Interactive CLI for Athens-Clarke County School Lookup
User-friendly command-line interface for looking up school information
"""

import sys
from school_info import get_school_info, format_complete_report
from school_performance import format_performance_report


def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║         ATHENS-CLARKE COUNTY SCHOOL INFORMATION LOOKUP TOOL              ║
║                                                                           ║
║                    📚 School Assignments + Performance Data 📊            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information"""
    help_text = """
USAGE:
  python3 school_lookup_cli.py                    - Interactive mode
  python3 school_lookup_cli.py [ADDRESS]          - Look up specific address
  python3 school_lookup_cli.py --help             - Show this help

EXAMPLES:
  python3 school_lookup_cli.py "150 Hancock Avenue, Athens, GA 30601"
  python3 school_lookup_cli.py "585 Reese Street, Athens, GA"

FEATURES:
  ✓ School district assignments (Elementary, Middle, High)
  ✓ Test scores (Georgia Milestones)
  ✓ Graduation rates
  ✓ Student demographics
  ✓ SAT scores
  ✓ Achievement analysis

DATA SOURCES:
  - Clarke County Schools Street Index (2024-25)
  - Georgia GOSA Performance Data (2023-24)

NOTE: Always verify school assignments with Clarke County School District.
"""
    print(help_text)


def format_short_report(info) -> str:
    """Format a concise summary report"""
    lines = []

    lines.append("\n" + "=" * 75)
    lines.append(f"📍 ADDRESS: {info.address}")
    lines.append("=" * 75)

    lines.append("\n🏫 SCHOOL ASSIGNMENTS:")
    lines.append(f"   Elementary: {info.elementary}")
    lines.append(f"   Middle:     {info.middle}")
    lines.append(f"   High:       {info.high}")

    if info.street_matched:
        lines.append(f"\n   ✓ Matched: {info.street_matched}", )
        if info.parameters_matched:
            lines.append(f"     Parameters: {info.parameters_matched}")

    # Quick performance summary
    if info.elementary_performance:
        perf = info.elementary_performance
        lines.append(f"\n📊 {info.elementary.upper()} QUICK STATS:")

        if perf.test_scores:
            avg = sum(s.total_proficient_pct for s in perf.test_scores) / len(perf.test_scores)
            lines.append(f"   Average Proficiency: {avg:.1f}%")

        if perf.demographics:
            if perf.demographics.pct_economically_disadvantaged:
                lines.append(f"   Economically Disadvantaged: {perf.demographics.pct_economically_disadvantaged:.1f}%")

    if info.high_performance:
        perf = info.high_performance
        lines.append(f"\n📊 {info.high.upper()} QUICK STATS:")

        if perf.graduation_rate:
            lines.append(f"   Graduation Rate: {perf.graduation_rate:.1f}%")

        if perf.avg_sat_score and perf.avg_sat_score > 0:
            lines.append(f"   Average SAT: {perf.avg_sat_score}")

    lines.append("\n" + "=" * 75)

    return "\n".join(lines)


def lookup_address(address: str, detailed: bool = False):
    """Look up a single address and display results"""

    if not address or not address.strip():
        print("\n❌ Error: Please provide an address")
        return False

    print(f"\n🔍 Looking up: {address}")
    print("   Please wait...\n")

    try:
        info = get_school_info(address)

        if not info:
            print("=" * 75)
            print("❌ ADDRESS NOT FOUND")
            print("=" * 75)
            print(f"\nThe address '{address}' was not found in the street index.")
            print("\nPossible reasons:")
            print("  • Street is not in Athens-Clarke County")
            print("  • Street name not recognized (try different abbreviation)")
            print("  • Typo in street name")
            print("\nTips:")
            print("  • Try 'Street' instead of 'St', or vice versa")
            print("  • Include full street name (e.g., 'Hancock Avenue' not 'Hancock')")
            print("  • Make sure the address is in Athens-Clarke County, GA")
            print()
            return False

        # Display results
        if detailed:
            print(format_complete_report(info))
        else:
            print(format_short_report(info))
            print("\n💡 Tip: Run with detailed flag for full performance data")
            print("   (Type 'detail' at the prompt or use -d flag)")

        return True

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_mode():
    """Run in interactive mode"""
    print_banner()
    print("Welcome! Enter an address to look up school information.")
    print("Type 'help' for usage info, 'quit' to exit.\n")

    while True:
        try:
            # Get user input
            user_input = input("📍 Enter address (or 'quit'): ").strip()

            # Handle special commands
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using Athens-Clarke County School Lookup!")
                print("Always verify assignments with Clarke County School District.\n")
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            # Check for detail flag
            detailed = False
            if user_input.lower().startswith('detail '):
                detailed = True
                user_input = user_input[7:].strip()

            # Look up the address
            lookup_address(user_input, detailed)

            # Ask if they want details
            if not detailed:
                response = input("\n❓ View detailed performance data? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    info = get_school_info(user_input)
                    if info:
                        print(format_complete_report(info))

            print("\n" + "-" * 75 + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break


def main():
    """Main entry point"""

    # Check for help flag
    if '--help' in sys.argv or '-h' in sys.argv:
        print_banner()
        print_help()
        return 0

    # Check if address provided as argument
    if len(sys.argv) > 1:
        # Join all arguments as address
        address = ' '.join(sys.argv[1:])

        # Check for detail flag
        detailed = '-d' in sys.argv or '--detailed' in sys.argv
        if detailed:
            # Remove flags from address
            address = address.replace('-d', '').replace('--detailed', '').strip()

        print_banner()
        success = lookup_address(address, detailed)
        return 0 if success else 1
    else:
        # Run in interactive mode
        interactive_mode()
        return 0


if __name__ == "__main__":
    sys.exit(main())
