"""
Test suite for crime analysis module.

Tests multi-jurisdiction crime data lookup, safety scoring, and trend analysis.

Run with: python tests/test_crime.py

Last Updated: November 2025
Phase: 2 - Crime Data (Week 3)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_county_config
from core.crime_analysis import CrimeAnalysis, CrimeIncident, CrimeAnalysisResult


def test_crime_incident_dataclass():
    """Test CrimeIncident dataclass creation."""
    print("Test 1: CrimeIncident dataclass")
    print("-" * 60)

    incident = CrimeIncident(
        incident_id="2024-12345",
        incident_type="THEFT",
        date=datetime(2024, 11, 15, 14, 30),
        address="Main St, Leesburg, VA",
        lat=39.1156,
        lon=-77.5636,
        description="Larceny from vehicle",
        jurisdiction="Leesburg PD"
    )

    assert incident.incident_id == "2024-12345"
    assert incident.incident_type == "THEFT"
    assert incident.address == "Main St, Leesburg, VA"
    assert incident.jurisdiction == "Leesburg PD"

    print(f"  ✅ CrimeIncident created successfully")
    print(f"     ID: {incident.incident_id}")
    print(f"     Type: {incident.incident_type}")
    print(f"     Jurisdiction: {incident.jurisdiction}")
    print()


def test_crime_analysis_result_dataclass():
    """Test CrimeAnalysisResult dataclass creation."""
    print("Test 2: CrimeAnalysisResult dataclass")
    print("-" * 60)

    result = CrimeAnalysisResult(
        address="Ashburn, VA",
        jurisdiction_type="county",
        jurisdiction_name="Unincorporated Loudoun County",
        police_jurisdiction="Loudoun County Sheriff's Office",
        radius_miles=1.0,
        total_incidents=5,
        safety_score=85,
        safety_rating="Very Safe",
        success=True
    )

    assert result.address == "Ashburn, VA"
    assert result.jurisdiction_type == "county"
    assert result.total_incidents == 5
    assert result.safety_score == 85
    assert result.safety_rating == "Very Safe"
    assert result.success == True

    print(f"  ✅ CrimeAnalysisResult created successfully")
    print(f"     Address: {result.address}")
    print(f"     Jurisdiction: {result.jurisdiction_type}")
    print(f"     Safety Score: {result.safety_score}/100")
    print(f"     Rating: {result.safety_rating}")
    print()


def test_crime_analysis_initialization():
    """Test CrimeAnalysis class initialization."""
    print("Test 3: CrimeAnalysis initialization")
    print("-" * 60)

    # Test with Loudoun County
    loudoun_config = get_county_config("loudoun")
    analyzer = CrimeAnalysis(loudoun_config)

    assert analyzer.config == loudoun_config
    assert analyzer.config.county_name == "loudoun"
    assert analyzer.jurisdiction_detector is not None

    print(f"  ✅ CrimeAnalysis initialized successfully")
    print(f"     County: {analyzer.config.display_name}")
    print(f"     Has crime data: {analyzer.config.has_crime_data}")
    print()


def test_jurisdiction_routing_county():
    """Test crime lookup routes to county Sheriff for unincorporated areas."""
    print("Test 4: County jurisdiction routing (Ashburn)")
    print("-" * 60)

    loudoun_config = get_county_config("loudoun")
    analyzer = CrimeAnalysis(loudoun_config)

    # Ashburn is unincorporated - should route to Sheriff
    result = analyzer.get_crime_data(
        "Ashburn, VA",
        lat=39.0437,
        lon=-77.4875,
        radius_miles=1.0,
        timeframe_days=90
    )

    print(f"  Result:")
    print(f"    Address: {result.address}")
    print(f"    Jurisdiction Type: {result.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result.jurisdiction_name}")
    print(f"    Police Jurisdiction: {result.police_jurisdiction}")
    print(f"    Success: {result.success}")

    # Should be county jurisdiction
    assert result.jurisdiction_type == "county"
    assert "Sheriff" in result.police_jurisdiction or "LCSO" in result.police_jurisdiction

    # API endpoint not configured yet - expected
    if not result.success:
        print(f"    Status: {result.error_message}")
        assert "not yet implemented" in result.error_message.lower() or "not configured" in result.error_message.lower()

    print(f"  ✅ PASS - Correctly routed to county Sheriff")
    print()


def test_jurisdiction_routing_town():
    """Test crime lookup routes to town PD for incorporated towns."""
    print("Test 5: Town jurisdiction routing (Leesburg)")
    print("-" * 60)

    loudoun_config = get_county_config("loudoun")
    analyzer = CrimeAnalysis(loudoun_config)

    # Leesburg is incorporated - should route to town PD
    result = analyzer.get_crime_data(
        "Downtown Leesburg, VA",
        lat=39.1156,
        lon=-77.5636,
        radius_miles=1.0,
        timeframe_days=90
    )

    print(f"  Result:")
    print(f"    Address: {result.address}")
    print(f"    Jurisdiction Type: {result.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result.jurisdiction_name}")
    print(f"    Police Jurisdiction: {result.police_jurisdiction}")
    print(f"    Success: {result.success}")

    # Should be town jurisdiction
    assert result.jurisdiction_type == "town"
    assert "Leesburg" in result.jurisdiction_name

    # Town PD data not configured yet - expected
    if not result.success:
        print(f"    Status: {result.error_message}")
        assert result.error_message is not None

    print(f"  ✅ PASS - Correctly routed to town police")
    print()


def test_safety_score_algorithm():
    """Test safety score calculation algorithm."""
    print("Test 6: Safety score algorithm")
    print("-" * 60)

    loudoun_config = get_county_config("loudoun")
    analyzer = CrimeAnalysis(loudoun_config)

    # Test 1: No incidents = high score
    print("  Scenario 1: No incidents")
    incidents = []
    safety_data = analyzer._calculate_safety_score(incidents, 90)

    assert safety_data['score'] == 95
    assert safety_data['rating'] == 'Very Safe'
    assert safety_data['trend'] == 'stable'
    print(f"    Score: {safety_data['score']}/100 - {safety_data['rating']}")
    print(f"    ✅ Correct: No incidents = 95/100 (Very Safe)")
    print()

    # Test 2: Mix of crimes
    print("  Scenario 2: Mixed crime types")
    incidents = [
        CrimeIncident("1", "THEFT", datetime.now()),          # -2 points
        CrimeIncident("2", "VANDALISM", datetime.now()),      # -2 points
        CrimeIncident("3", "TRESPASSING", datetime.now()),    # -1 point
        CrimeIncident("4", "ASSAULT", datetime.now()),        # -5 points
    ]
    safety_data = analyzer._calculate_safety_score(incidents, 90)

    # 100 - 2 - 2 - 1 - 5 = 90
    assert safety_data['score'] == 90
    assert safety_data['rating'] == 'Very Safe'
    print(f"    Score: {safety_data['score']}/100 - {safety_data['rating']}")
    print(f"    ✅ Correct: 4 incidents = 90/100 (Very Safe)")
    print()

    # Test 3: Many violent crimes
    print("  Scenario 3: Multiple violent crimes")
    incidents = [
        CrimeIncident(str(i), "ASSAULT", datetime.now()) for i in range(10)
    ]
    safety_data = analyzer._calculate_safety_score(incidents, 90)

    # 100 - (10 * 5) = 50
    assert safety_data['score'] == 50
    assert safety_data['rating'] == 'Moderate'
    print(f"    Score: {safety_data['score']}/100 - {safety_data['rating']}")
    print(f"    ✅ Correct: 10 violent crimes = 50/100 (Moderate)")
    print()


def test_athens_backward_compatibility():
    """Test that Athens (unified government) works with crime module."""
    print("Test 7: Athens backward compatibility")
    print("-" * 60)

    athens_config = get_county_config("athens_clarke")
    analyzer = CrimeAnalysis(athens_config)

    # Athens has unified government - should always be county jurisdiction
    result = analyzer.get_crime_data(
        "Downtown Athens, GA",
        lat=33.9573,
        lon=-83.3761,
        radius_miles=1.0,
        timeframe_days=90
    )

    print(f"  Result:")
    print(f"    Address: {result.address}")
    print(f"    Jurisdiction Type: {result.jurisdiction_type}")
    print(f"    Jurisdiction Name: {result.jurisdiction_name}")
    print(f"    Police Jurisdiction: {result.police_jurisdiction}")

    # Should be county (unified government)
    assert result.jurisdiction_type == "county"
    assert "Athens" in result.police_jurisdiction or "Clarke" in result.police_jurisdiction

    print(f"  ✅ PASS - Athens unified government working")
    print()


def run_all_tests():
    """Run all crime module tests."""
    print("=" * 60)
    print("CRIME ANALYSIS MODULE TESTS")
    print("=" * 60)
    print(f"Date: November 2025")
    print(f"Phase: 2 - Crime Data (Week 3)")
    print()

    tests = [
        ("CrimeIncident dataclass", test_crime_incident_dataclass),
        ("CrimeAnalysisResult dataclass", test_crime_analysis_result_dataclass),
        ("CrimeAnalysis initialization", test_crime_analysis_initialization),
        ("County jurisdiction routing", test_jurisdiction_routing_county),
        ("Town jurisdiction routing", test_jurisdiction_routing_town),
        ("Safety score algorithm", test_safety_score_algorithm),
        ("Athens backward compatibility", test_athens_backward_compatibility),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {test_name}")
            print(f"     Error: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {test_name}")
            print(f"     Exception: {e}")
            print()
            failed += 1

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print()

    if passed == len(tests):
        print("✅ ALL TESTS PASSED")
        print()
        print("Crime analysis infrastructure:")
        print("  - Dataclasses: ✅ Working")
        print("  - Initialization: ✅ Working")
        print("  - Jurisdiction routing: ✅ Correctly routes Sheriff vs town PD")
        print("  - Safety scoring: ✅ Algorithm working")
        print("  - Athens compatibility: ✅ Backward compatible")
        print()
        print("Status:")
        print("  - Infrastructure: ✅ Complete")
        print("  - API endpoint: ⏳ Pending configuration")
        print("  - Real data: ⏳ Pending LCSO Crime Dashboard research")
        print()
        print("Next steps:")
        print("  1. Research LCSO Crime Dashboard API")
        print("  2. Configure crime_api_endpoint in config/loudoun.py")
        print("  3. Test with real crime data")
        print("  4. Validate safety scores against local knowledge")
    else:
        print("❌ SOME TESTS FAILED")
        print("Review errors above and fix issues")

    print()
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
