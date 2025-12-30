#!/usr/bin/env python3
"""
Generate visualization charts for ATTOM API optimization analysis.

Creates charts showing:
1. API calls per property: Current vs Optimized
2. Cost comparison by volume
3. Savings breakdown by optimization
4. ROI timeline
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'diagnostic_outputs' / 'attom_optimization'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_calls_comparison_chart():
    """Chart 1: API calls per property - Current vs Optimized."""
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['Validation\n(Baseline)', 'Production\nMinimum', 'Production\nTypical', 'Production\nMaximum', 'After\nOptimization']
    calls = [2, 4, 8, 16, 3]
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#27ae60']

    bars = ax.bar(categories, calls, color=colors, edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for bar, call in zip(bars, calls):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                f'{call} calls', ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_ylabel('API Calls per Property', fontsize=12)
    ax.set_title('ATTOM API Calls per Property Valuation', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 20)

    # Add horizontal lines for reference
    ax.axhline(y=2, color='green', linestyle='--', alpha=0.5, label='Target (2 calls)')
    ax.axhline(y=8, color='red', linestyle='--', alpha=0.5, label='Current Typical')

    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_01_calls_comparison.png', dpi=150)
    plt.close()
    print(f"Created: chart_01_calls_comparison.png")


def create_cost_by_volume_chart():
    """Chart 2: Monthly cost by property volume."""
    fig, ax = plt.subplots(figsize=(10, 6))

    volumes = [100, 500, 1000, 5000, 10000]
    current_typical = [76, 380, 760, 3800, 7600]
    optimized = [28.5, 142.5, 285, 1425, 2850]

    x = np.arange(len(volumes))
    width = 0.35

    bars1 = ax.bar(x - width/2, current_typical, width, label='Current (Typical)', color='#e74c3c')
    bars2 = ax.bar(x + width/2, optimized, width, label='After Optimization', color='#27ae60')

    ax.set_xlabel('Properties per Month', fontsize=12)
    ax.set_ylabel('Monthly Cost ($)', fontsize=12)
    ax.set_title('ATTOM API Monthly Cost by Volume', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{v:,}' for v in volumes])
    ax.legend()

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'${height:,.0f}', ha='center', va='bottom', fontsize=9)

    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_02_cost_by_volume.png', dpi=150)
    plt.close()
    print(f"Created: chart_02_cost_by_volume.png")


def create_savings_breakdown_chart():
    """Chart 3: Savings breakdown by optimization type."""
    fig, ax = plt.subplots(figsize=(10, 6))

    optimizations = [
        'Disable Sqft\nEnrichment',
        'Use Local\nData',
        'Smart AVM\nFallback',
        'Add Caching',
        'Limit Comp\nEnrichment'
    ]
    savings_per_property = [0.475, 0.475, 0.05, 0.02, 0.35]
    annual_savings_1k = [s * 1000 * 12 for s in savings_per_property]

    colors = ['#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#e67e22']

    bars = ax.bar(optimizations, annual_savings_1k, color=colors, edgecolor='black')

    # Add value labels
    for bar, s in zip(bars, annual_savings_1k):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 100,
                f'${height:,.0f}/yr', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Annual Savings ($) at 1,000 props/month', fontsize=11)
    ax.set_title('Annual Savings by Optimization (1,000 properties/month)', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add note
    ax.text(0.5, -0.15, 'Note: Options 1 & 2 are mutually exclusive (same savings, different approach)',
            transform=ax.transAxes, ha='center', fontsize=9, style='italic')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_03_savings_breakdown.png', dpi=150)
    plt.close()
    print(f"Created: chart_03_savings_breakdown.png")


def create_cost_waterfall_chart():
    """Chart 4: Cost waterfall - where the money goes."""
    fig, ax = plt.subplots(figsize=(10, 6))

    steps = ['Property\nDetail', 'AVM/\nValuation', 'Comparable\nSearch', 'Comp\nEnrichment\n(5 avg)', 'TOTAL\n(Typical)']
    values = [0.095, 0.095, 0.095, 0.475, 0.76]
    cumulative = [0.095, 0.19, 0.285, 0.76, 0.76]

    # Create waterfall effect
    colors = ['#3498db', '#3498db', '#3498db', '#e74c3c', '#2c3e50']

    ax.bar(steps, values, color=colors, edgecolor='black')

    # Add cumulative line
    ax.plot(range(len(steps)-1), cumulative[:-1], 'ko-', markersize=8, linewidth=2)

    # Add value labels
    for i, (v, c) in enumerate(zip(values, cumulative)):
        ax.text(i, v + 0.02, f'${v:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        if i < len(steps) - 1:
            ax.text(i, c + 0.05, f'Running: ${c:.3f}', ha='center', va='bottom', fontsize=8, color='gray')

    ax.set_ylabel('Cost per Property ($)', fontsize=12)
    ax.set_title('Cost Breakdown per Property Valuation', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 0.9)
    ax.grid(axis='y', alpha=0.3)

    # Highlight the problem area
    ax.annotate('62% of cost!', xy=(3, 0.475), xytext=(3.5, 0.6),
                fontsize=11, fontweight='bold', color='#e74c3c',
                arrowprops=dict(arrowstyle='->', color='#e74c3c'))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_04_cost_waterfall.png', dpi=150)
    plt.close()
    print(f"Created: chart_04_cost_waterfall.png")


def create_roi_timeline_chart():
    """Chart 5: ROI timeline for optimization investment."""
    fig, ax = plt.subplots(figsize=(10, 6))

    months = list(range(13))
    investment = 300  # Initial developer time cost

    # Cumulative savings over time (at 1,000 props/month, $475 savings/month)
    monthly_savings = 475
    cumulative_savings = [monthly_savings * m for m in months]
    net_benefit = [s - investment for s in cumulative_savings]

    ax.fill_between(months, 0, cumulative_savings, alpha=0.3, color='green', label='Cumulative Savings')
    ax.plot(months, cumulative_savings, 'g-', linewidth=2, label='Savings')
    ax.plot(months, net_benefit, 'b-', linewidth=2, label='Net Benefit')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axhline(y=investment, color='red', linestyle='--', label=f'Initial Investment (${investment})')

    # Mark breakeven point
    breakeven = investment / monthly_savings
    ax.axvline(x=breakeven, color='orange', linestyle='--', alpha=0.7)
    ax.annotate(f'Breakeven: {breakeven:.1f} months', xy=(breakeven, 0), xytext=(2, -500),
                fontsize=10, fontweight='bold')

    ax.set_xlabel('Months', fontsize=12)
    ax.set_ylabel('Dollars ($)', fontsize=12)
    ax.set_title('ROI Timeline for ATTOM Optimization (1,000 properties/month)', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 12)
    ax.set_ylim(-500, 6000)

    # Add annotations
    ax.annotate(f'Year 1 Savings: ${12 * monthly_savings:,}', xy=(12, cumulative_savings[-1]),
                xytext=(9, 5200), fontsize=11, fontweight='bold', color='green')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_05_roi_timeline.png', dpi=150)
    plt.close()
    print(f"Created: chart_05_roi_timeline.png")


def create_comparison_summary_chart():
    """Chart 6: Before/After summary comparison."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left pie: Current cost breakdown
    labels1 = ['Property Detail\n$0.095', 'AVM\n$0.095', 'Comp Search\n$0.095', 'Comp Enrichment\n$0.475']
    sizes1 = [0.095, 0.095, 0.095, 0.475]
    colors1 = ['#3498db', '#2ecc71', '#9b59b6', '#e74c3c']
    explode1 = (0, 0, 0, 0.1)

    ax1.pie(sizes1, explode=explode1, labels=labels1, colors=colors1, autopct='%1.0f%%',
            shadow=True, startangle=90)
    ax1.set_title('CURRENT: $0.76/property', fontsize=12, fontweight='bold')

    # Right pie: Optimized cost breakdown
    labels2 = ['Property Detail\n$0.095', 'AVM\n$0.095', 'Comp Search\n$0.095']
    sizes2 = [0.095, 0.095, 0.095]
    colors2 = ['#3498db', '#2ecc71', '#9b59b6']

    ax2.pie(sizes2, labels=labels2, colors=colors2, autopct='%1.0f%%',
            shadow=True, startangle=90)
    ax2.set_title('OPTIMIZED: $0.285/property', fontsize=12, fontweight='bold')

    fig.suptitle('Cost Distribution: Before vs After Optimization', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'chart_06_comparison_summary.png', dpi=150)
    plt.close()
    print(f"Created: chart_06_comparison_summary.png")


def main():
    """Generate all charts."""
    print("=" * 60)
    print("GENERATING ATTOM OPTIMIZATION CHARTS")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    create_calls_comparison_chart()
    create_cost_by_volume_chart()
    create_savings_breakdown_chart()
    create_cost_waterfall_chart()
    create_roi_timeline_chart()
    create_comparison_summary_chart()

    print()
    print("=" * 60)
    print("ALL CHARTS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nFiles created in: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
