#!/usr/bin/env python3
"""
Comprehensive test suite for Athens-Clarke County school lookup tool
Tests with diverse addresses and edge cases
"""

from school_info import get_school_info, format_complete_report
from typing import List, Tuple
import sys


# Test addresses covering different areas and scenarios
TEST_ADDRESSES = [
    # Downtown/Historic Athens
    ("150 Hancock Avenue, Athens, GA 30601", "Historic downtown area"),
    ("585 Reese Street, Athens, GA 30601", "Near UGA campus"),
    ("195 Hoyt Street, Athens, GA 30601", "Downtown neighborhood"),

    # East Athens
    ("245 Lexington Road, Athens, GA 30605", "East Athens community"),
    ("100 Gaines School Road, Athens, GA 30605", "Near Gaines Elementary"),

    # West Athens
    ("350 Oglethorpe Avenue, Athens, GA 30606", "West side neighborhood"),
    ("220 Ruth Street, Athens, GA 30601", "West Athens area"),

    # North/Five Points
    ("425 Barber Street, Athens, GA 30601", "Five Points area"),
    ("150 Pulaski Street, Athens, GA 30601", "North downtown"),

    # Winterville area
    ("110 Winterville Road, Athens, GA 30605", "Near Winterville"),
]


def print_separator(char='=', length=80):
    """Print a separator line"""
    print(char * length)


def print_header(text):
    """Print a formatted header"""
    print_separator()
    print(f" {text}")
    print_separator()


def print_success(message):
    """Print success message"""
    print(f"✓ {message}")


def print_error(message):
    """Print error message"""
    print(f"✗ {message}")


def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")


def test_single_address(address: str, description: str = "", verbose: bool = False) -> bool:
    """
    Test a single address lookup

    Args:
        address: Full address string
        description: Optional description of the location
        verbose: If True, print full performance report

    Returns:
        True if successful, False otherwise
    """
    print_separator('-')
    print(f"\nTesting: {address}")
    if description:
        print(f"Location: {description}")
    print()

    try:
        info = get_school_info(address)

        if not info:
            print_error("Address not found in street index")
            print("\nPossible reasons:")
            print("  - Street not in Athens-Clarke County")
            print("  - Street name not recognized")
            print("  - Typo in street name")
            return False

        # Print school assignments
        print_success("School assignments found!")
        print(f"\n  Elementary: {info.elementary}")
        print(f"  Middle:     {info.middle}")
        print(f"  High:       {info.high}")

        if info.street_matched:
            print(f"\n  Matched: {info.street_matched}", end="")
            if info.parameters_matched:
                print(f" ({info.parameters_matched})", end="")
            print()

        # Check performance data availability
        perf_count = 0
        missing = []

        if info.elementary_performance:
            perf_count += 1
        else:
            missing.append("Elementary")

        if info.middle_performance:
            perf_count += 1
        else:
            missing.append("Middle")

        if info.high_performance:
            perf_count += 1
        else:
            missing.append("High")

        print(f"\n  Performance Data: {perf_count}/3 schools loaded")

        if missing:
            print_warning(f"Missing performance data for: {', '.join(missing)}")

        # Print brief performance summary if available
        if info.elementary_performance and not verbose:
            perf = info.elementary_performance
            if perf.test_scores:
                avg = sum(s.total_proficient_pct for s in perf.test_scores) / len(perf.test_scores)
                print(f"\n  {info.elementary} Performance:")
                print(f"    Average Proficiency: {avg:.1f}%")
                if perf.demographics:
                    print(f"    Enrollment: {perf.demographics.total_enrollment or 'N/A'}")
                    print(f"    Econ. Disadvantaged: {perf.demographics.pct_economically_disadvantaged:.1f}%")

        # Print full report if verbose
        if verbose:
            print("\n" + format_complete_report(info))

        print_success("Test passed!")
        return True

    except Exception as e:
        print_error(f"Error during lookup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(verbose: bool = False):
    """Run all test addresses"""
    print_header("ATHENS-CLARKE COUNTY SCHOOL LOOKUP - COMPREHENSIVE TEST SUITE")
    print(f"\nTesting {len(TEST_ADDRESSES)} addresses across Athens-Clarke County")
    print(f"Verbose mode: {'ON' if verbose else 'OFF'}")
    print()

    results = []

    for address, description in TEST_ADDRESSES:
        success = test_single_address(address, description, verbose)
        results.append((address, success))
        print()

    # Print summary
    print_separator('=')
    print_header("TEST SUMMARY")

    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed

    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed} ({100*passed/len(results):.1f}%)")
    print(f"Failed: {failed} ({100*failed/len(results):.1f}%)")
    print()

    if failed > 0:
        print("Failed addresses:")
        for address, success in results:
            if not success:
                print(f"  ✗ {address}")
        print()

    print_separator('=')

    return passed == len(results)


if __name__ == "__main__":
    # Check for verbose flag
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    # Run all tests
    success = run_all_tests(verbose=verbose)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
