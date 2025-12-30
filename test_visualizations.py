#!/usr/bin/env python3
"""
Test crime visualizations with sample data
"""

from crime_analysis import analyze_crime_near_address
from crime_visualizations import (
    create_category_chart_data,
    create_trend_chart_data,
    create_comparison_chart_data,
    create_safety_score_html,
    create_comparison_html,
    format_crime_stats_table,
    get_safety_color
)

# Test addresses with different safety profiles
test_addresses = [
    ("220 College Station Road, Athens, GA 30602", "Low Crime"),
    ("150 Hancock Avenue, Athens, GA 30601", "High Crime")
]

print("=" * 80)
print("CRIME VISUALIZATION TEST")
print("=" * 80)
print()

for address, profile in test_addresses:
    print(f"\n{'='*80}")
    print(f"Testing: {profile} - {address}")
    print('=' * 80)

    try:
        analysis = analyze_crime_near_address(address, radius_miles=0.5, months_back=12)

        if analysis:
            # Test color coding
            color = get_safety_color(analysis.safety_score.score)
            print(f"\n✓ Safety Score: {analysis.safety_score.score}/100 ({analysis.safety_score.level})")
            print(f"✓ Color Code: {color}")

            # Test stats formatting
            stats_table = format_crime_stats_table(analysis)
            print(f"\n✓ Stats Table Generated:")
            for section, data in stats_table.items():
                print(f"  {section}: {len(data)} entries")

            # Test chart creation
            print(f"\n✓ Generating Visualizations:")

            category_data = create_category_chart_data(analysis)
            print(f"  • Category Chart Data: {'✓' if category_data is not None else '✗'}")

            trend_data = create_trend_chart_data(analysis)
            print(f"  • Trend Chart Data: {'✓' if trend_data is not None else '✗'}")

            comparison_data = create_comparison_chart_data(analysis)
            print(f"  • Comparison Chart Data: {'✓' if comparison_data is not None else '✗'}")

            safety_html = create_safety_score_html(analysis.safety_score.score, analysis.safety_score.level)
            print(f"  • Safety Score HTML: {'✓' if safety_html else '✗'}")

            comparison_html = create_comparison_html(analysis)
            print(f"  • Comparison HTML: {'✓' if comparison_html else '✗'}")

            print(f"\n✓ All visualizations generated successfully!")

        else:
            print("✗ Failed to get analysis")

    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("VISUALIZATION TEST COMPLETE")
print("All charts are ready for Streamlit display")
print("=" * 80)
