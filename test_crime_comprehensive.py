#!/usr/bin/env python3
"""
Comprehensive test suite for Athens crime analysis system
Tests diverse addresses, edge cases, data integrity, and performance
"""

import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from crime_analysis import analyze_crime_near_address
from crime_ai_assistant import CrimeAIAssistant


# Test addresses covering diverse Athens areas
TEST_ADDRESSES = {
    "downtown_bar_district": {
        "address": "185 E Broad Street, Athens, GA 30601",
        "description": "Downtown bar district",
        "expected_profile": "high_crime",
        "zip": "30601"
    },
    "downtown_government": {
        "address": "301 E Washington Street, Athens, GA 30601",
        "description": "Downtown government center",
        "expected_profile": "moderate_crime",
        "zip": "30601"
    },
    "uga_campus_north": {
        "address": "150 Hancock Avenue, Athens, GA 30601",
        "description": "UGA campus north (student housing)",
        "expected_profile": "high_crime",
        "zip": "30601"
    },
    "uga_campus_south": {
        "address": "585 Reese Street, Athens, GA 30601",
        "description": "UGA campus south",
        "expected_profile": "high_crime",
        "zip": "30601"
    },
    "suburban_east": {
        "address": "220 College Station Road, Athens, GA 30602",
        "description": "Suburban residential (east)",
        "expected_profile": "low_crime",
        "zip": "30602"
    },
    "suburban_southeast": {
        "address": "1000 Jennings Mill Road, Athens, GA 30606",
        "description": "Suburban shopping/residential (southeast)",
        "expected_profile": "low_crime",
        "zip": "30606"
    },
    "five_points": {
        "address": "1800 S Lumpkin Street, Athens, GA 30606",
        "description": "Five Points commercial area",
        "expected_profile": "moderate_crime",
        "zip": "30606"
    },
    "industrial_west": {
        "address": "2200 West Broad Street, Athens, GA 30606",
        "description": "West Broad industrial/commercial",
        "expected_profile": "high_crime",
        "zip": "30606"
    },
    "residential_northeast": {
        "address": "265 Newton Bridge Road, Athens, GA 30607",
        "description": "Residential northeast",
        "expected_profile": "low_crime",
        "zip": "30607"
    },
    "beechwood_residential": {
        "address": "135 Beechwood Drive, Athens, GA 30605",
        "description": "Beechwood residential area",
        "expected_profile": "low_crime",
        "zip": "30605"
    }
}

# Edge case addresses
EDGE_CASES = {
    "invalid_address": {
        "address": "99999 Nonexistent Street, Athens, GA 30601",
        "description": "Invalid address",
        "should_fail": True
    },
    "outside_athens": {
        "address": "100 Peachtree Street, Atlanta, GA 30303",
        "description": "Atlanta address (outside Athens)",
        "should_fail": True
    },
    "watkinsville_border": {
        "address": "1880 Hog Mountain Road, Watkinsville, GA 30677",
        "description": "Watkinsville (border town, not Athens-Clarke)",
        "should_fail": True
    },
    "typo_address": {
        "address": "150 Hanckock Avenue, Athens, GA 30601",  # Misspelled
        "description": "Address with typo",
        "should_fail": True
    }
}


class TestResult:
    """Store test results"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details = {}
        self.time_elapsed = 0.0
        self.warnings = []

    def __str__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"{status} - {self.test_name}: {self.message} ({self.time_elapsed:.2f}s)"


class CrimeTestSuite:
    """Comprehensive test suite for crime analysis"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 80)
        print("COMPREHENSIVE CRIME ANALYSIS TEST SUITE")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test 1: Diverse address testing
        print("\n" + "=" * 80)
        print("TEST SECTION 1: DIVERSE ADDRESS TESTING (10 addresses)")
        print("=" * 80)
        self.test_diverse_addresses()

        # Test 2: Edge cases
        print("\n" + "=" * 80)
        print("TEST SECTION 2: EDGE CASE TESTING")
        print("=" * 80)
        self.test_edge_cases()

        # Test 3: Data integrity
        print("\n" + "=" * 80)
        print("TEST SECTION 3: DATA INTEGRITY VERIFICATION")
        print("=" * 80)
        self.test_data_integrity()

        # Generate final report
        print("\n" + "=" * 80)
        print("FINAL TEST REPORT")
        print("=" * 80)
        self.generate_report()

    def test_diverse_addresses(self):
        """Test diverse Athens addresses"""
        for key, addr_info in TEST_ADDRESSES.items():
            result = TestResult(f"Address Test: {addr_info['description']}")
            start_time = time.time()

            try:
                print(f"\nTesting: {addr_info['description']}")
                print(f"Address: {addr_info['address']}")
                print("-" * 80)

                analysis = analyze_crime_near_address(
                    addr_info['address'],
                    radius_miles=0.5,
                    months_back=12
                )

                result.time_elapsed = time.time() - start_time

                if analysis:
                    # Verify basic data
                    crimes = analysis.statistics.total_crimes
                    score = analysis.safety_score.score
                    level = analysis.safety_score.level

                    print(f"✓ Retrieved {crimes} crimes")
                    print(f"✓ Safety score: {score}/100 ({level})")
                    print(f"✓ Query time: {result.time_elapsed:.2f}s")

                    # Store details
                    result.details = {
                        'crimes': crimes,
                        'score': score,
                        'level': level,
                        'violent_pct': analysis.statistics.violent_percentage,
                        'trend': analysis.trends.trend,
                        'comparison': analysis.comparison.relative_ranking if analysis.comparison else None
                    }

                    # Verify categorization
                    if not self._verify_categorization(analysis, result):
                        result.warnings.append("Categorization issue detected")

                    # Verify statistics sum
                    if not self._verify_statistics_sum(analysis, result):
                        result.warnings.append("Statistics don't sum correctly")

                    # Check if score makes sense for expected profile
                    if not self._verify_score_matches_profile(score, addr_info['expected_profile'], result):
                        result.warnings.append(f"Score {score} unexpected for {addr_info['expected_profile']}")

                    # Performance check
                    if result.time_elapsed > 10:
                        result.warnings.append(f"Slow query: {result.time_elapsed:.2f}s")

                    result.passed = True
                    result.message = f"Success: {crimes} crimes, score {score}/100"

                else:
                    result.passed = False
                    result.message = "Failed to retrieve analysis"

            except Exception as e:
                result.time_elapsed = time.time() - start_time
                result.passed = False
                result.message = f"Exception: {str(e)}"
                print(f"✗ ERROR: {e}")

            self.results.append(result)
            self._update_counters(result)

    def test_edge_cases(self):
        """Test edge cases that should fail gracefully"""
        for key, case_info in EDGE_CASES.items():
            result = TestResult(f"Edge Case: {case_info['description']}")
            start_time = time.time()

            try:
                print(f"\nTesting: {case_info['description']}")
                print(f"Address: {case_info['address']}")
                print(f"Expected: Should fail gracefully")
                print("-" * 80)

                analysis = analyze_crime_near_address(
                    case_info['address'],
                    radius_miles=0.5,
                    months_back=12
                )

                result.time_elapsed = time.time() - start_time

                if case_info['should_fail']:
                    # Should have failed but didn't
                    result.passed = False
                    result.message = "Expected failure but succeeded"
                    print(f"✗ UNEXPECTED: Query succeeded when it should have failed")
                else:
                    result.passed = True
                    result.message = "Succeeded as expected"
                    print(f"✓ Query succeeded as expected")

            except ValueError as e:
                result.time_elapsed = time.time() - start_time
                if case_info['should_fail']:
                    # Expected failure
                    result.passed = True
                    result.message = f"Failed gracefully: {str(e)[:60]}"
                    print(f"✓ Failed gracefully: {str(e)}")
                else:
                    result.passed = False
                    result.message = f"Unexpected failure: {str(e)}"
                    print(f"✗ Unexpected failure: {e}")

            except Exception as e:
                result.time_elapsed = time.time() - start_time
                result.passed = False
                result.message = f"Unexpected exception: {type(e).__name__}"
                print(f"✗ Unexpected exception: {e}")

            self.results.append(result)
            self._update_counters(result)

    def test_data_integrity(self):
        """Test data integrity with spot checks"""
        # Pick a few addresses for detailed verification
        test_addresses = [
            "220 College Station Road, Athens, GA 30602",  # Low crime
            "150 Hancock Avenue, Athens, GA 30601",  # High crime
        ]

        for addr in test_addresses:
            result = TestResult(f"Data Integrity: {addr}")
            start_time = time.time()

            try:
                print(f"\nVerifying data integrity for: {addr}")
                print("-" * 80)

                analysis = analyze_crime_near_address(addr, radius_miles=0.5, months_back=12)
                result.time_elapsed = time.time() - start_time

                if not analysis:
                    result.passed = False
                    result.message = "Failed to get analysis"
                    continue

                # Test 1: Category percentages sum to ~100%
                total_pct = (analysis.statistics.violent_percentage +
                           analysis.statistics.property_percentage +
                           analysis.statistics.traffic_percentage +
                           analysis.statistics.other_percentage)

                pct_check = abs(total_pct - 100.0) < 0.1
                print(f"✓ Category percentages sum to {total_pct:.1f}% (should be ~100%): {'PASS' if pct_check else 'FAIL'}")

                # Test 2: Category counts sum to total
                total_count = (analysis.statistics.violent_count +
                             analysis.statistics.property_count +
                             analysis.statistics.traffic_count +
                             analysis.statistics.other_count)

                count_check = total_count == analysis.statistics.total_crimes
                print(f"✓ Category counts sum to {total_count} (total: {analysis.statistics.total_crimes}): {'PASS' if count_check else 'FAIL'}")

                # Test 3: Trend counts sum correctly
                trend_total = analysis.trends.recent_count + analysis.trends.previous_count
                trend_check = trend_total <= analysis.statistics.total_crimes  # May be less due to date filtering
                print(f"✓ Trend counts ({trend_total}) <= total crimes: {'PASS' if trend_check else 'FAIL'}")

                # Test 4: Safety score in valid range
                score_check = 1 <= analysis.safety_score.score <= 100
                print(f"✓ Safety score {analysis.safety_score.score} in range [1-100]: {'PASS' if score_check else 'FAIL'}")

                # Test 5: Comparison data makes sense
                if analysis.comparison:
                    comp = analysis.comparison
                    diff_check = abs(comp.difference_count - (comp.area_crime_count - comp.athens_average)) < 0.1
                    print(f"✓ Comparison difference calculated correctly: {'PASS' if diff_check else 'FAIL'}")
                else:
                    diff_check = True  # No comparison data, skip

                all_checks = pct_check and count_check and trend_check and score_check and diff_check

                result.passed = all_checks
                result.message = "All integrity checks passed" if all_checks else "Some integrity checks failed"
                result.details = {
                    'percentage_sum': total_pct,
                    'count_sum_correct': count_check,
                    'trend_check': trend_check,
                    'score_valid': score_check,
                    'comparison_check': diff_check
                }

            except Exception as e:
                result.time_elapsed = time.time() - start_time
                result.passed = False
                result.message = f"Exception during integrity check: {str(e)}"
                print(f"✗ ERROR: {e}")

            self.results.append(result)
            self._update_counters(result)

    def _verify_categorization(self, analysis, result: TestResult) -> bool:
        """Verify crime categorization is logical (spot check)"""
        # All categories should be non-negative
        stats = analysis.statistics
        if any([stats.violent_count < 0, stats.property_count < 0,
                stats.traffic_count < 0, stats.other_count < 0]):
            return False
        return True

    def _verify_statistics_sum(self, analysis, result: TestResult) -> bool:
        """Verify statistics add up correctly"""
        stats = analysis.statistics
        total_from_categories = (stats.violent_count + stats.property_count +
                                stats.traffic_count + stats.other_count)
        return total_from_categories == stats.total_crimes

    def _verify_score_matches_profile(self, score: int, expected_profile: str, result: TestResult) -> bool:
        """Verify safety score roughly matches expected crime profile"""
        # This is a soft check - we expect general patterns but allow variation
        if expected_profile == "low_crime":
            # Low crime should generally score 60-100
            return score >= 50  # Allow some flexibility
        elif expected_profile == "high_crime":
            # High crime should generally score 20-70
            return score <= 80  # Allow some flexibility
        else:  # moderate_crime
            # Moderate should be in middle range
            return 30 <= score <= 90  # Wide range for moderate

    def _update_counters(self, result: TestResult):
        """Update test counters"""
        self.total_tests += 1
        if result.passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def generate_report(self):
        """Generate final test report"""
        print(f"\nTotal Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"Failed: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        print()

        # Performance summary
        print("\nPERFORMANCE SUMMARY:")
        print("-" * 80)
        times = [r.time_elapsed for r in self.results if r.time_elapsed > 0]
        if times:
            print(f"Average query time: {sum(times)/len(times):.2f}s")
            print(f"Fastest query: {min(times):.2f}s")
            print(f"Slowest query: {max(times):.2f}s")
        print()

        # Failed tests detail
        if self.failed_tests > 0:
            print("\nFAILED TESTS DETAIL:")
            print("-" * 80)
            for result in self.results:
                if not result.passed:
                    print(f"✗ {result.test_name}")
                    print(f"  Message: {result.message}")
                    print()

        # Warnings
        warnings = [r for r in self.results if r.warnings]
        if warnings:
            print("\nWARNINGS:")
            print("-" * 80)
            for result in warnings:
                print(f"⚠  {result.test_name}")
                for warning in result.warnings:
                    print(f"   - {warning}")
            print()

        # Address profile summary
        print("\nADDRESS PROFILE SUMMARY:")
        print("-" * 80)
        print(f"{'Area':<40} {'Crimes':<10} {'Score':<12} {'Level':<15} {'Time':<8}")
        print("-" * 80)

        for result in self.results:
            if 'Address Test' in result.test_name and result.passed:
                area = result.test_name.replace('Address Test: ', '')
                details = result.details
                print(f"{area:<40} {details['crimes']:<10} {details['score']:<12} {details['level']:<15} {result.time_elapsed:.2f}s")

        print()
        print("=" * 80)
        print("TEST SUITE COMPLETE")
        print("=" * 80)


def main():
    """Run comprehensive test suite"""
    suite = CrimeTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()
