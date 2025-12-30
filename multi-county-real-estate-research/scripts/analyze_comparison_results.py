#!/usr/bin/env python3
"""
Analyze RentCast vs ATTOM Comparison Results

This script analyzes the raw comparison results and generates:
- Summary statistics
- Detailed metrics
- Comparison report
- Visualizations (if matplotlib available)

Usage:
    python scripts/analyze_comparison_results.py              # Analyze and generate report
    python scripts/analyze_comparison_results.py --viz        # Also generate visualizations

Inputs:
    - diagnostic_outputs/api_comparison/raw_results.json

Outputs:
    - diagnostic_outputs/api_comparison/summary_stats.json
    - diagnostic_outputs/api_comparison/comparison_metrics.csv
    - diagnostic_outputs/api_comparison/rentcast_vs_attom_validation.md
    - diagnostic_outputs/api_comparison/*.png (if --viz)
"""

import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / 'diagnostic_outputs' / 'api_comparison'
RESULTS_FILE = OUTPUT_DIR / 'raw_results.json'
SUMMARY_FILE = OUTPUT_DIR / 'summary_stats.json'
METRICS_FILE = OUTPUT_DIR / 'comparison_metrics.csv'
REPORT_FILE = OUTPUT_DIR / 'rentcast_vs_attom_validation.md'


def load_results() -> Dict:
    """Load raw results from JSON file."""
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(f"Results file not found: {RESULTS_FILE}")

    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive comparison metrics."""
    if not results:
        return {}

    metrics = {
        'total_properties': len(results),
        'analysis_date': datetime.now().isoformat(),
    }

    # Success rates
    rc_success = sum(1 for r in results if r.get('rentcast_success'))
    attom_prop_success = sum(1 for r in results if r.get('attom_property_success'))
    attom_avm_success = sum(1 for r in results if r.get('attom_avm_success'))
    both_success = sum(1 for r in results if r.get('rentcast_success') and r.get('attom_avm_success'))

    metrics['success_rates'] = {
        'rentcast': round(rc_success / len(results) * 100, 1),
        'attom_property': round(attom_prop_success / len(results) * 100, 1),
        'attom_avm': round(attom_avm_success / len(results) * 100, 1),
        'both_have_valuation': round(both_success / len(results) * 100, 1),
        'counts': {
            'rentcast': rc_success,
            'attom_property': attom_prop_success,
            'attom_avm': attom_avm_success,
            'both': both_success
        }
    }

    # Valuation comparison
    val_diffs = [r['valuation_diff_pct'] for r in results if r.get('valuation_diff_pct') is not None]

    if val_diffs:
        abs_diffs = [abs(d) for d in val_diffs]
        sorted_abs = sorted(abs_diffs)

        metrics['valuation_comparison'] = {
            'count_with_both': len(val_diffs),
            'mean_diff_pct': round(statistics.mean(val_diffs), 2),
            'mean_abs_diff_pct': round(statistics.mean(abs_diffs), 2),
            'median_abs_diff_pct': round(statistics.median(abs_diffs), 2),
            'std_dev': round(statistics.stdev(val_diffs), 2) if len(val_diffs) > 1 else 0,
            'max_diff_pct': round(max(val_diffs), 2),
            'min_diff_pct': round(min(val_diffs), 2),
            'percentile_25': round(sorted_abs[len(sorted_abs)//4], 2) if len(sorted_abs) >= 4 else None,
            'percentile_75': round(sorted_abs[3*len(sorted_abs)//4], 2) if len(sorted_abs) >= 4 else None,
            'percentile_90': round(sorted_abs[9*len(sorted_abs)//10], 2) if len(sorted_abs) >= 10 else None,
            'within_5_pct': round(sum(1 for d in abs_diffs if d <= 5) / len(abs_diffs) * 100, 1),
            'within_10_pct': round(sum(1 for d in abs_diffs if d <= 10) / len(abs_diffs) * 100, 1),
            'within_15_pct': round(sum(1 for d in abs_diffs if d <= 15) / len(abs_diffs) * 100, 1),
            'within_20_pct': round(sum(1 for d in abs_diffs if d <= 20) / len(abs_diffs) * 100, 1),
            'over_20_pct': round(sum(1 for d in abs_diffs if d > 20) / len(abs_diffs) * 100, 1),
            'rentcast_higher_count': sum(1 for d in val_diffs if d > 0),
            'attom_higher_count': sum(1 for d in val_diffs if d < 0),
            'equal_count': sum(1 for d in val_diffs if d == 0),
        }

    # Property characteristics match rates
    beds_results = [r['beds_match'] for r in results if r.get('beds_match') is not None]
    baths_results = [r['baths_match'] for r in results if r.get('baths_match') is not None]
    year_results = [r['year_built_match'] for r in results if r.get('year_built_match') is not None]
    sqft_diffs = [r['sqft_diff_pct'] for r in results if r.get('sqft_diff_pct') is not None]

    metrics['characteristic_matches'] = {
        'bedrooms': {
            'count': len(beds_results),
            'match_rate': round(sum(beds_results) / len(beds_results) * 100, 1) if beds_results else None,
            'matches': sum(beds_results) if beds_results else 0
        },
        'bathrooms': {
            'count': len(baths_results),
            'match_rate': round(sum(baths_results) / len(baths_results) * 100, 1) if baths_results else None,
            'matches': sum(baths_results) if baths_results else 0
        },
        'year_built': {
            'count': len(year_results),
            'match_rate': round(sum(year_results) / len(year_results) * 100, 1) if year_results else None,
            'matches': sum(year_results) if year_results else 0
        },
        'sqft': {
            'count': len(sqft_diffs),
            'mean_diff_pct': round(statistics.mean(sqft_diffs), 2) if sqft_diffs else None,
            'within_5_pct': round(sum(1 for d in sqft_diffs if abs(d) <= 5) / len(sqft_diffs) * 100, 1) if sqft_diffs else None,
            'within_10_pct': round(sum(1 for d in sqft_diffs if abs(d) <= 10) / len(sqft_diffs) * 100, 1) if sqft_diffs else None
        }
    }

    # Response times
    rc_times = [r['rentcast_time_ms'] for r in results if r.get('rentcast_time_ms')]
    attom_prop_times = [r['attom_property_time_ms'] for r in results if r.get('attom_property_time_ms')]
    attom_avm_times = [r['attom_avm_time_ms'] for r in results if r.get('attom_avm_time_ms')]

    metrics['response_times_ms'] = {
        'rentcast_avg': round(statistics.mean(rc_times), 1) if rc_times else None,
        'attom_property_avg': round(statistics.mean(attom_prop_times), 1) if attom_prop_times else None,
        'attom_avm_avg': round(statistics.mean(attom_avm_times), 1) if attom_avm_times else None,
        'attom_total_avg': round(statistics.mean(attom_prop_times) + statistics.mean(attom_avm_times), 1) if attom_prop_times and attom_avm_times else None
    }

    # Geographic analysis
    cities = {}
    for r in results:
        city = r.get('city', 'Unknown')
        if city not in cities:
            cities[city] = {'total': 0, 'rc_success': 0, 'attom_success': 0, 'both': 0, 'val_diffs': []}
        cities[city]['total'] += 1
        if r.get('rentcast_success'):
            cities[city]['rc_success'] += 1
        if r.get('attom_avm_success'):
            cities[city]['attom_success'] += 1
        if r.get('rentcast_success') and r.get('attom_avm_success'):
            cities[city]['both'] += 1
        if r.get('valuation_diff_pct') is not None:
            cities[city]['val_diffs'].append(r['valuation_diff_pct'])

    metrics['by_city'] = {}
    for city, data in cities.items():
        metrics['by_city'][city] = {
            'count': data['total'],
            'rentcast_success_rate': round(data['rc_success'] / data['total'] * 100, 1),
            'attom_success_rate': round(data['attom_success'] / data['total'] * 100, 1),
            'mean_val_diff': round(statistics.mean(data['val_diffs']), 2) if data['val_diffs'] else None
        }

    return metrics


def generate_report(metrics: Dict, data: Dict) -> str:
    """Generate comprehensive markdown report."""
    is_mock = data.get('is_mock_data', False)

    report = []
    report.append("# RentCast vs ATTOM API Validation Report")
    report.append("")
    report.append(f"**Analysis Date:** {metrics['analysis_date'][:10]}")
    report.append(f"**Properties Tested:** {metrics['total_properties']}")

    if is_mock:
        report.append("")
        report.append("> ⚠️ **NOTE:** This report uses simulated data for demonstration purposes.")
        report.append("> Run the comparison script with real API keys for actual validation results.")

    report.append("")
    report.append("---")
    report.append("")

    # Executive Summary
    report.append("## Executive Summary")
    report.append("")

    sr = metrics['success_rates']
    vc = metrics.get('valuation_comparison', {})

    # Determine recommendation
    recommendation = "PARTIAL"
    confidence = "Medium"

    if vc:
        within_10 = vc.get('within_10_pct', 0)
        mean_abs_diff = vc.get('mean_abs_diff_pct', 100)

        if within_10 >= 80 and mean_abs_diff <= 8:
            recommendation = "GO"
            confidence = "High"
        elif within_10 >= 60 and mean_abs_diff <= 12:
            recommendation = "PARTIAL"
            confidence = "Medium"
        else:
            recommendation = "NO-GO"
            confidence = "High"

    report.append(f"### Recommendation: **{recommendation}**")
    report.append(f"**Confidence Level:** {confidence}")
    report.append("")

    if recommendation == "GO":
        report.append("RentCast demonstrates sufficient accuracy to replace ATTOM for most use cases.")
        report.append("Estimated monthly savings: **$2,000-2,700**")
    elif recommendation == "PARTIAL":
        report.append("RentCast is suitable for routine properties but may need ATTOM backup for complex/high-value cases.")
        report.append("Estimated monthly savings with hybrid approach: **$1,000-1,500**")
    else:
        report.append("RentCast accuracy does not meet requirements for ATTOM replacement.")
        report.append("Recommend: Keep ATTOM, focus on DIY AVM development.")

    report.append("")
    report.append("### Key Findings")
    report.append("")

    if vc:
        report.append(f"- **Valuation Agreement:** {vc.get('within_10_pct', 'N/A')}% within 10% of each other")
        report.append(f"- **Mean Absolute Difference:** {vc.get('mean_abs_diff_pct', 'N/A')}%")
        report.append(f"- **RentCast Success Rate:** {sr['rentcast']}%")
        report.append(f"- **ATTOM AVM Success Rate:** {sr['attom_avm']}%")

    report.append("")
    report.append("---")
    report.append("")

    # Detailed Results
    report.append("## Detailed Results")
    report.append("")

    # Success Rates
    report.append("### API Success Rates")
    report.append("")
    report.append("| Metric | Rate | Count |")
    report.append("|--------|------|-------|")
    report.append(f"| RentCast Value Estimate | {sr['rentcast']}% | {sr['counts']['rentcast']}/{metrics['total_properties']} |")
    report.append(f"| ATTOM Property Detail | {sr['attom_property']}% | {sr['counts']['attom_property']}/{metrics['total_properties']} |")
    report.append(f"| ATTOM AVM | {sr['attom_avm']}% | {sr['counts']['attom_avm']}/{metrics['total_properties']} |")
    report.append(f"| Both Have Valuations | {sr['both_have_valuation']}% | {sr['counts']['both']}/{metrics['total_properties']} |")
    report.append("")

    # Valuation Comparison
    if vc:
        report.append("### Valuation Comparison")
        report.append("")
        report.append(f"**Comparable Properties:** {vc['count_with_both']} (have both RentCast and ATTOM valuations)")
        report.append("")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Mean Difference (RC - ATTOM) | {vc['mean_diff_pct']:+.2f}% |")
        report.append(f"| Mean Absolute Difference | {vc['mean_abs_diff_pct']:.2f}% |")
        report.append(f"| Median Absolute Difference | {vc['median_abs_diff_pct']:.2f}% |")
        report.append(f"| Standard Deviation | {vc['std_dev']:.2f}% |")
        report.append(f"| Min Difference | {vc['min_diff_pct']:+.2f}% |")
        report.append(f"| Max Difference | {vc['max_diff_pct']:+.2f}% |")
        report.append("")

        report.append("**Agreement Distribution:**")
        report.append("")
        report.append("| Range | Percentage |")
        report.append("|-------|------------|")
        report.append(f"| Within 5% | {vc['within_5_pct']}% |")
        report.append(f"| Within 10% | {vc['within_10_pct']}% |")
        report.append(f"| Within 15% | {vc['within_15_pct']}% |")
        report.append(f"| Within 20% | {vc['within_20_pct']}% |")
        report.append(f"| Over 20% | {vc['over_20_pct']}% |")
        report.append("")

        report.append("**Direction of Difference:**")
        report.append("")
        report.append(f"- RentCast higher: {vc['rentcast_higher_count']} properties")
        report.append(f"- ATTOM higher: {vc['attom_higher_count']} properties")
        report.append("")

    # Characteristic Matches
    cm = metrics.get('characteristic_matches', {})
    if cm:
        report.append("### Property Characteristics Comparison")
        report.append("")
        report.append("| Field | Match Rate | Sample Size |")
        report.append("|-------|------------|-------------|")

        for field in ['bedrooms', 'bathrooms', 'year_built']:
            if field in cm and cm[field]['count'] > 0:
                rate = cm[field].get('match_rate', 'N/A')
                count = cm[field]['count']
                report.append(f"| {field.replace('_', ' ').title()} | {rate}% | {count} |")

        if 'sqft' in cm and cm['sqft']['count'] > 0:
            sqft = cm['sqft']
            report.append(f"| Square Footage (within 5%) | {sqft.get('within_5_pct', 'N/A')}% | {sqft['count']} |")

        report.append("")

    # Response Times
    rt = metrics.get('response_times_ms', {})
    if rt:
        report.append("### API Response Times")
        report.append("")
        report.append("| API | Average Response Time |")
        report.append("|-----|----------------------|")
        if rt.get('rentcast_avg'):
            report.append(f"| RentCast Value | {rt['rentcast_avg']:.0f} ms |")
        if rt.get('attom_property_avg'):
            report.append(f"| ATTOM Property | {rt['attom_property_avg']:.0f} ms |")
        if rt.get('attom_avm_avg'):
            report.append(f"| ATTOM AVM | {rt['attom_avm_avg']:.0f} ms |")
        if rt.get('attom_total_avg'):
            report.append(f"| ATTOM Total | {rt['attom_total_avg']:.0f} ms |")
        report.append("")

    # Geographic Analysis
    by_city = metrics.get('by_city', {})
    if by_city:
        report.append("### Results by City")
        report.append("")
        report.append("| City | Count | RC Success | ATTOM Success | Mean Diff |")
        report.append("|------|-------|------------|---------------|-----------|")

        for city in sorted(by_city.keys(), key=lambda c: by_city[c]['count'], reverse=True):
            data = by_city[city]
            diff = f"{data['mean_val_diff']:+.1f}%" if data['mean_val_diff'] is not None else "N/A"
            report.append(f"| {city} | {data['count']} | {data['rentcast_success_rate']}% | {data['attom_success_rate']}% | {diff} |")
        report.append("")

    # Cost Analysis
    report.append("---")
    report.append("")
    report.append("## Cost-Benefit Analysis")
    report.append("")
    report.append("### Current ATTOM Costs (Estimated)")
    report.append("")
    report.append("- ~$0.10-0.15 per API call")
    report.append("- 2-3 calls per property (property detail + AVM)")
    report.append("- At 1,000 properties/month: **$200-450/month**")
    report.append("- At 10,000 properties/month: **$2,000-4,500/month**")
    report.append("")
    report.append("### RentCast Costs")
    report.append("")
    report.append("- ~$0.03 per API call")
    report.append("- 1 call per property (value estimate includes all data)")
    report.append("- At 1,000 properties/month: **$30/month**")
    report.append("- At 10,000 properties/month: **$300/month**")
    report.append("")
    report.append("### Potential Savings")
    report.append("")
    report.append("| Scenario | Monthly Savings | Annual Savings |")
    report.append("|----------|-----------------|----------------|")
    report.append("| Full RentCast Migration | $1,700-4,200 | $20,400-50,400 |")
    report.append("| Hybrid (80% RentCast) | $1,360-3,360 | $16,320-40,320 |")
    report.append("| Keep ATTOM (baseline) | $0 | $0 |")
    report.append("")

    # Recommendations
    report.append("---")
    report.append("")
    report.append("## Recommendations")
    report.append("")

    if recommendation == "GO":
        report.append("### Proceed with RentCast Migration")
        report.append("")
        report.append("1. **Phase 1 (Week 1-2):** Implement RentCast as primary valuation source")
        report.append("2. **Phase 2 (Week 3-4):** Monitor accuracy, set up ATTOM fallback for failures")
        report.append("3. **Phase 3 (Week 5+):** Reduce ATTOM usage to edge cases only")
        report.append("")
    elif recommendation == "PARTIAL":
        report.append("### Implement Hybrid Strategy")
        report.append("")
        report.append("1. Use RentCast for:")
        report.append("   - Standard residential properties")
        report.append("   - Properties under $1M")
        report.append("   - Initial valuations and screening")
        report.append("")
        report.append("2. Use ATTOM for:")
        report.append("   - High-value properties ($1M+)")
        report.append("   - Commercial/mixed-use")
        report.append("   - When RentCast returns no data")
        report.append("   - Final verification on important transactions")
        report.append("")
    else:
        report.append("### Keep ATTOM, Explore Alternatives")
        report.append("")
        report.append("1. Continue using ATTOM as primary source")
        report.append("2. Negotiate volume discounts with ATTOM")
        report.append("3. Accelerate DIY AVM model development using:")
        report.append("   - Loudoun County sales data (78K records)")
        report.append("   - Tax assessment data")
        report.append("   - Machine learning models")
        report.append("")

    # Risk Assessment
    report.append("---")
    report.append("")
    report.append("## Risk Assessment")
    report.append("")
    report.append("| Risk | Likelihood | Impact | Mitigation |")
    report.append("|------|------------|--------|------------|")
    report.append("| RentCast accuracy degradation | Low | Medium | Monitor weekly, keep ATTOM backup |")
    report.append("| API rate limits | Low | Low | Implement caching, batch processing |")
    report.append("| Missing data for some properties | Medium | Low | Fallback to ATTOM or assessment data |")
    report.append("| Valuation bias in specific areas | Medium | Medium | Geographic monitoring, calibration |")
    report.append("")

    # Appendix
    report.append("---")
    report.append("")
    report.append("## Appendix")
    report.append("")
    report.append("### Methodology")
    report.append("")
    report.append(f"- **Sample Size:** {metrics['total_properties']} properties")
    report.append("- **Geographic Coverage:** Loudoun County, VA (multiple cities/towns)")
    report.append("- **Property Selection:** Stratified sample from building permits (2024-2025)")
    report.append("- **Comparison Metrics:** Valuation difference, characteristic match rates")
    report.append("")
    report.append("### Data Sources")
    report.append("")
    report.append("- RentCast API: `/v1/avm/value` endpoint")
    report.append("- ATTOM API: `/property/detail` and `/attomavm/detail` endpoints")
    report.append("- Test sample: `diagnostic_outputs/api_comparison/test_sample.csv`")
    report.append("")
    report.append("### Files Generated")
    report.append("")
    report.append("- `raw_results.json` - Complete API responses")
    report.append("- `summary_stats.json` - Summary statistics")
    report.append("- `comparison_metrics.csv` - Per-property metrics")
    report.append("- `rentcast_vs_attom_validation.md` - This report")
    report.append("")

    return "\n".join(report)


def create_visualizations(results: List[Dict], output_dir: Path):
    """Create visualization charts."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not available - skipping visualizations")
        return

    # 1. Valuation Scatter Plot
    rc_values = []
    attom_values = []
    for r in results:
        if r.get('rc_price_estimate') and r.get('attom_avm_value'):
            rc_values.append(r['rc_price_estimate'] / 1000)  # In thousands
            attom_values.append(r['attom_avm_value'] / 1000)

    if rc_values:
        plt.figure(figsize=(10, 8))
        plt.scatter(attom_values, rc_values, alpha=0.6, edgecolors='none', s=50)

        # Perfect agreement line
        max_val = max(max(rc_values), max(attom_values))
        plt.plot([0, max_val], [0, max_val], 'r--', label='Perfect Agreement', linewidth=2)

        # +/- 10% bands
        plt.fill_between([0, max_val], [0, max_val*0.9], [0, max_val*1.1],
                        alpha=0.1, color='green', label='±10% Range')

        plt.xlabel('ATTOM AVM Value ($K)', fontsize=12)
        plt.ylabel('RentCast Estimate ($K)', fontsize=12)
        plt.title('RentCast vs ATTOM Valuation Comparison', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / 'valuation_scatter.png', dpi=150)
        plt.close()
        print(f"  Created: valuation_scatter.png")

    # 2. Difference Distribution Histogram
    val_diffs = [r['valuation_diff_pct'] for r in results if r.get('valuation_diff_pct') is not None]

    if val_diffs:
        plt.figure(figsize=(10, 6))
        plt.hist(val_diffs, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
        plt.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No Difference')
        plt.axvline(x=np.mean(val_diffs), color='green', linestyle='-', linewidth=2,
                   label=f'Mean: {np.mean(val_diffs):+.1f}%')

        plt.xlabel('Valuation Difference (RentCast - ATTOM) %', fontsize=12)
        plt.ylabel('Number of Properties', fontsize=12)
        plt.title('Distribution of Valuation Differences', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / 'difference_histogram.png', dpi=150)
        plt.close()
        print(f"  Created: difference_histogram.png")

    # 3. Success Rates Bar Chart
    rc_success = sum(1 for r in results if r.get('rentcast_success'))
    attom_prop_success = sum(1 for r in results if r.get('attom_property_success'))
    attom_avm_success = sum(1 for r in results if r.get('attom_avm_success'))
    both_success = sum(1 for r in results if r.get('rentcast_success') and r.get('attom_avm_success'))

    plt.figure(figsize=(10, 6))
    categories = ['RentCast\nValue', 'ATTOM\nProperty', 'ATTOM\nAVM', 'Both\nHave Value']
    values = [
        rc_success / len(results) * 100,
        attom_prop_success / len(results) * 100,
        attom_avm_success / len(results) * 100,
        both_success / len(results) * 100
    ]
    colors = ['#2ecc71', '#3498db', '#9b59b6', '#e74c3c']

    bars = plt.bar(categories, values, color=colors, edgecolor='black')
    plt.ylabel('Success Rate (%)', fontsize=12)
    plt.title('API Success Rates', fontsize=14)
    plt.ylim(0, 100)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{val:.1f}%', ha='center', fontsize=11, fontweight='bold')

    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_dir / 'success_rates.png', dpi=150)
    plt.close()
    print(f"  Created: success_rates.png")

    # 4. Agreement Levels Pie Chart
    if val_diffs:
        abs_diffs = [abs(d) for d in val_diffs]
        within_5 = sum(1 for d in abs_diffs if d <= 5)
        within_10 = sum(1 for d in abs_diffs if 5 < d <= 10)
        within_15 = sum(1 for d in abs_diffs if 10 < d <= 15)
        within_20 = sum(1 for d in abs_diffs if 15 < d <= 20)
        over_20 = sum(1 for d in abs_diffs if d > 20)

        plt.figure(figsize=(8, 8))
        sizes = [within_5, within_10, within_15, within_20, over_20]
        labels = ['Within 5%', '5-10%', '10-15%', '15-20%', 'Over 20%']
        colors = ['#2ecc71', '#27ae60', '#f1c40f', '#e67e22', '#e74c3c']
        explode = (0.05, 0, 0, 0, 0.1)

        # Filter out zero values
        non_zero = [(s, l, c, e) for s, l, c, e in zip(sizes, labels, colors, explode) if s > 0]
        if non_zero:
            sizes, labels, colors, explode = zip(*non_zero)

            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                   autopct='%1.1f%%', shadow=True, startangle=90)
            plt.title('Valuation Agreement Distribution', fontsize=14)
            plt.tight_layout()
            plt.savefig(output_dir / 'agreement_pie.png', dpi=150)
            plt.close()
            print(f"  Created: agreement_pie.png")

    print("\nVisualizations complete!")


def save_metrics_csv(results: List[Dict], output_file: Path):
    """Save detailed metrics to CSV."""
    if not results:
        return

    # Define columns
    columns = [
        'sample_id', 'address', 'city',
        'rentcast_success', 'attom_avm_success',
        'rc_price_estimate', 'attom_avm_value', 'valuation_diff_pct',
        'rc_bedrooms', 'attom_bedrooms', 'beds_match',
        'rc_bathrooms', 'attom_bathrooms', 'baths_match',
        'rc_sqft', 'attom_sqft', 'sqft_diff_pct',
        'rc_year_built', 'attom_year_built', 'year_built_match'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze RentCast vs ATTOM comparison results')
    parser.add_argument('--viz', action='store_true', help='Generate visualizations')
    args = parser.parse_args()

    print("=" * 60)
    print("RentCast vs ATTOM Comparison Analysis")
    print("=" * 60)

    # Load results
    try:
        data = load_results()
        results = data.get('results', [])
        print(f"\nLoaded {len(results)} comparison results")

        if data.get('is_mock_data'):
            print("⚠️  NOTE: Analyzing simulated/mock data")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Run the comparison script first to generate results.")
        return

    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculate_metrics(results)

    # Save summary JSON
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"  Saved: {SUMMARY_FILE}")

    # Save detailed CSV
    save_metrics_csv(results, METRICS_FILE)
    print(f"  Saved: {METRICS_FILE}")

    # Generate report
    print("\nGenerating report...")
    report = generate_report(metrics, data)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Saved: {REPORT_FILE}")

    # Generate visualizations
    if args.viz:
        print("\nGenerating visualizations...")
        create_visualizations(results, OUTPUT_DIR)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    sr = metrics['success_rates']
    print(f"\nAPI Success Rates:")
    print(f"  RentCast:        {sr['rentcast']}%")
    print(f"  ATTOM AVM:       {sr['attom_avm']}%")
    print(f"  Both Available:  {sr['both_have_valuation']}%")

    vc = metrics.get('valuation_comparison', {})
    if vc:
        print(f"\nValuation Comparison ({vc['count_with_both']} properties):")
        print(f"  Mean Difference:     {vc['mean_diff_pct']:+.2f}%")
        print(f"  Mean Absolute Diff:  {vc['mean_abs_diff_pct']:.2f}%")
        print(f"  Within 10%:          {vc['within_10_pct']}%")
        print(f"  Over 20%:            {vc['over_20_pct']}%")

    cm = metrics.get('characteristic_matches', {})
    if cm:
        print(f"\nCharacteristic Match Rates:")
        for field in ['bedrooms', 'bathrooms', 'year_built']:
            if field in cm and cm[field].get('match_rate'):
                print(f"  {field.title()}: {cm[field]['match_rate']}%")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
