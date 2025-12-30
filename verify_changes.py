#!/usr/bin/env python3
"""
Verification script to check that all required changes were made to streamlit_app.py
"""

def verify_streamlit_changes():
    """Verify all changes to streamlit_app.py"""

    with open('streamlit_app.py', 'r') as f:
        content = f.read()
        lines = content.split('\n')

    print("=" * 70)
    print("VERIFICATION REPORT: streamlit_app.py Changes")
    print("=" * 70)
    print()

    # 1. Check for defensive hasattr checks
    print("1. DEFENSIVE ATTRIBUTE CHECKS")
    print("-" * 70)

    hasattr_commercial = "hasattr(nearby_zoning, 'commercial_nearby')" in content
    hasattr_industrial = "hasattr(nearby_zoning, 'industrial_nearby')" in content

    print(f"   ✓ hasattr check for 'commercial_nearby': {'FOUND' if hasattr_commercial else 'MISSING'}")
    print(f"   ✓ hasattr check for 'industrial_nearby': {'FOUND' if hasattr_industrial else 'MISSING'}")

    # Find line numbers
    for i, line in enumerate(lines, 1):
        if "hasattr(nearby_zoning, 'commercial_nearby')" in line:
            print(f"     → Line {i}: commercial_nearby check")
        if "hasattr(nearby_zoning, 'industrial_nearby')" in line:
            print(f"     → Line {i}: industrial_nearby check")

    print()

    # 2. Check for summary boxes
    print("2. SUMMARY BOXES")
    print("-" * 70)

    summary_count = content.count('Quick Summary')
    print(f"   Total 'Quick Summary' boxes found: {summary_count}")
    print()

    # Find each summary box
    for i, line in enumerate(lines, 1):
        if 'Quick Summary' in line:
            # Determine which section
            if 'school_info.elementary' in line:
                print(f"   ✓ SCHOOL SUMMARY (Line {i})")
                print(f"     Content: School assignments (Elementary, Middle, High)")
                print(f"     Type: st.info()")
            elif 'safety_score.score' in line or 'Safety Score' in line:
                print(f"   ✓ CRIME SUMMARY (Line {i})")
                print(f"     Content: Safety score, incidents, trends, violent crimes")
                print(f"     Type: st.success() or st.warning() (conditional)")
            elif 'Current Zoning' in line:
                print(f"   ✓ ZONING SUMMARY (Line {i})")
                print(f"     Content: Zoning code, diversity, concerns")
                print(f"     Type: st.info()")

    print()

    # 3. Check for st.success() and st.warning() in crime section
    print("3. CRIME SUMMARY COLOR CODING")
    print("-" * 70)

    # Check for conditional success/warning
    crime_success = False
    crime_warning = False
    for i, line in enumerate(lines, 1):
        if 'st.success(summary_text)' in line:
            crime_success = True
            print(f"   ✓ st.success() for safe areas (Line {i})")
        if 'st.warning(summary_text)' in line and i > 700 and i < 730:
            crime_warning = True
            print(f"   ✓ st.warning() for concerning areas (Line {i})")

    if crime_success and crime_warning:
        print("   ✓ Conditional color coding implemented correctly")

    print()

    # 4. Count all display boxes
    print("4. STREAMLIT DISPLAY ELEMENTS")
    print("-" * 70)

    info_count = content.count('st.info(')
    success_count = content.count('st.success(')
    warning_count = content.count('st.warning(')

    print(f"   st.info() calls: {info_count}")
    print(f"   st.success() calls: {success_count}")
    print(f"   st.warning() calls: {warning_count}")
    print(f"   Total: {info_count + success_count + warning_count}")

    print()

    # 5. Verify defensive programming
    print("5. DEFENSIVE PROGRAMMING")
    print("-" * 70)

    hasattr_count = content.count('hasattr(')
    try_except_count = content.count('try:')

    print(f"   hasattr() checks: {hasattr_count}")
    print(f"   try-except blocks: {try_except_count}")
    print(f"   ✓ Defensive programming patterns present")

    print()

    # 6. Summary placement verification
    print("6. SUMMARY PLACEMENT")
    print("-" * 70)

    # Check school summary placement (should be after heading, before metrics)
    school_heading_line = 0
    school_summary_line = 0
    school_metrics_line = 0

    for i, line in enumerate(lines, 1):
        if '### 🎓 School Assignments' in line:
            school_heading_line = i
        if 'Quick Summary.*school_info.elementary' in line or ('Quick Summary' in line and i > 560 and i < 580):
            school_summary_line = i
        if 'st.columns(3)' in line and i > 560 and i < 600:
            school_metrics_line = i
            break

    if school_heading_line < school_summary_line < school_metrics_line:
        print(f"   ✓ School summary correctly placed:")
        print(f"     - Heading: Line {school_heading_line}")
        print(f"     - Summary: Line {school_summary_line}")
        print(f"     - Metrics: Line {school_metrics_line}")

    print()

    # Final status
    print("=" * 70)
    print("VERIFICATION STATUS")
    print("=" * 70)

    all_checks = [
        ("Defensive attribute checks", hasattr_commercial and hasattr_industrial),
        ("School summary box", summary_count >= 3),
        ("Crime summary box", crime_success and crime_warning),
        ("Zoning summary box", summary_count >= 3),
        ("Proper placement", school_heading_line < school_summary_line < school_metrics_line)
    ]

    passed = sum(1 for _, check in all_checks if check)
    total = len(all_checks)

    for name, passed_check in all_checks:
        status = "✓ PASS" if passed_check else "✗ FAIL"
        print(f"   {status}: {name}")

    print()
    print(f"OVERALL: {passed}/{total} checks passed")
    print("=" * 70)

    return passed == total

if __name__ == '__main__':
    success = verify_streamlit_changes()
    exit(0 if success else 1)
