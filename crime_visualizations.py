#!/usr/bin/env python3
"""
Crime Data Visualizations
Creates data structures for crime analysis display in Streamlit
"""

import pandas as pd
from typing import Optional, Dict, Tuple
from crime_analysis import CrimeAnalysis


def get_safety_color(score: int) -> str:
    """
    Get color based on safety score

    Args:
        score: Safety score (1-100)

    Returns:
        Hex color string
    """
    if score >= 80:
        return "#10b981"  # Green - Very Safe
    elif score >= 60:
        return "#84cc16"  # Light green - Safe
    elif score >= 40:
        return "#f59e0b"  # Yellow/Orange - Moderate
    elif score >= 20:
        return "#ef4444"  # Red - Concerning
    else:
        return "#dc2626"  # Dark red - High Risk


def get_category_colors() -> Dict[str, str]:
    """Get color mapping for crime categories"""
    return {
        'Violent': '#ef4444',    # Red
        'Property': '#f59e0b',   # Orange
        'Traffic': '#3b82f6',    # Blue
        'Other': '#6b7280'       # Gray
    }


def create_category_chart_data(analysis: CrimeAnalysis) -> pd.DataFrame:
    """
    Create DataFrame for category bar chart

    Args:
        analysis: Crime analysis object

    Returns:
        Pandas DataFrame ready for Streamlit charting
        Each category is a column so we can assign colors
    """
    stats = analysis.statistics

    # Create DataFrame with each category as a separate column
    # This allows us to assign different colors to each category
    data = {
        'Violent': [stats.violent_count],
        'Property': [stats.property_count],
        'Traffic': [stats.traffic_count],
        'Other': [stats.other_count]
    }

    df = pd.DataFrame(data)
    return df


def create_trend_chart_data(analysis: CrimeAnalysis) -> pd.DataFrame:
    """
    Create DataFrame for trend comparison chart

    Args:
        analysis: Crime analysis object

    Returns:
        Pandas DataFrame ready for Streamlit charting
    """
    trends = analysis.trends

    data = {
        'Period': ['Previous\n6 Months', 'Recent\n6 Months'],
        'Crimes': [trends.previous_count, trends.recent_count]
    }

    df = pd.DataFrame(data)
    df = df.set_index('Period')
    return df


def create_comparison_chart_data(analysis: CrimeAnalysis) -> Optional[pd.DataFrame]:
    """
    Create DataFrame for comparison to Athens average

    Args:
        analysis: Crime analysis object

    Returns:
        Pandas DataFrame or None if no comparison data
    """
    if not analysis.comparison:
        return None

    comp = analysis.comparison

    data = {
        'Location': ['This Address', 'Athens Average'],
        'Crimes': [comp.area_crime_count, comp.athens_average]
    }

    df = pd.DataFrame(data)
    df = df.set_index('Location')
    return df


def format_crime_stats_table(analysis: CrimeAnalysis) -> Dict[str, Dict[str, str]]:
    """
    Format crime statistics into a clean table structure

    Args:
        analysis: Crime analysis object

    Returns:
        Dictionary with formatted stats
    """
    stats = analysis.statistics
    trends = analysis.trends

    return {
        'Overview': {
            'Total Crimes': f"{stats.total_crimes}",
            'Crimes per Month': f"{stats.crimes_per_month:.1f}",
            'Time Period': f"{analysis.time_period_months} months",
            'Search Radius': f"{analysis.radius_miles} miles"
        },
        'Categories': {
            'Violent Crimes': f"{stats.violent_count} ({stats.violent_percentage:.1f}%)",
            'Property Crimes': f"{stats.property_count} ({stats.property_percentage:.1f}%)",
            'Traffic Offenses': f"{stats.traffic_count} ({stats.traffic_percentage:.1f}%)",
            'Other': f"{stats.other_count} ({stats.other_percentage:.1f}%)"
        },
        'Trends': {
            'Recent (6 months)': f"{trends.recent_count} crimes",
            'Previous (6-12 months)': f"{trends.previous_count} crimes",
            'Change': f"{trends.change_count:+d} crimes ({trends.change_percentage:+.1f}%)",
            'Trend': trends.trend.title()
        }
    }


def create_safety_score_html(score: int, level: str) -> str:
    """
    Create HTML/CSS visualization for safety score

    Args:
        score: Safety score (1-100)
        level: Safety level text

    Returns:
        HTML string with styled gauge
    """
    color = get_safety_color(score)

    html = f'<div style="text-align: center; padding: 2em; background: linear-gradient(135deg, {color}20 0%, {color}10 100%); border-radius: 1em; border: 2px solid {color};">' \
           f'<div style="font-size: 4em; font-weight: bold; color: {color}; margin-bottom: 0.2em;">{score}</div>' \
           f'<div style="font-size: 1.2em; color: #64748b; margin-bottom: 0.5em;">out of 100</div>' \
           f'<div style="font-size: 1.5em; font-weight: 600; color: {color};">{level}</div>' \
           f'<div style="margin-top: 1.5em; background: #e2e8f0; height: 20px; border-radius: 10px; overflow: hidden;">' \
           f'<div style="width: {score}%; height: 100%; background: {color}; transition: width 0.3s;"></div>' \
           f'</div>' \
           f'</div>'

    return html


def create_comparison_html(analysis: CrimeAnalysis) -> Optional[str]:
    """
    Create HTML visualization for Athens comparison

    Args:
        analysis: Crime analysis object

    Returns:
        HTML string or None if no comparison data
    """
    if not analysis.comparison:
        return None

    comp = analysis.comparison

    # Determine color based on ranking
    if "Very high" in comp.relative_ranking or "High activity" in comp.relative_ranking:
        color = '#ef4444'  # Red
    elif "Low activity" in comp.relative_ranking:
        color = '#10b981'  # Green
    else:
        color = '#f59e0b'  # Yellow

    # Calculate bar widths
    max_crimes = max(comp.area_crime_count, comp.athens_average)
    address_width = (comp.area_crime_count / max_crimes) * 100
    athens_width = (comp.athens_average / max_crimes) * 100

    html = f'<div style="padding: 1.5em; background: white; border-radius: 0.5em; border: 1px solid #e2e8f0;">' \
           f'<div style="font-size: 1.2em; font-weight: 600; margin-bottom: 1em; color: #334155;">Comparison to Athens Average</div>' \
           f'<div style="margin-bottom: 1.5em;">' \
           f'<div style="display: flex; justify-content: space-between; margin-bottom: 0.5em;">' \
           f'<span style="color: #64748b;">This Address</span>' \
           f'<span style="font-weight: 600; color: {color};">{comp.area_crime_count} crimes</span>' \
           f'</div>' \
           f'<div style="background: #e2e8f0; height: 30px; border-radius: 5px; overflow: hidden;">' \
           f'<div style="width: {address_width}%; height: 100%; background: {color};"></div>' \
           f'</div>' \
           f'</div>' \
           f'<div style="margin-bottom: 1.5em;">' \
           f'<div style="display: flex; justify-content: space-between; margin-bottom: 0.5em;">' \
           f'<span style="color: #64748b;">Athens Average</span>' \
           f'<span style="font-weight: 600; color: #6b7280;">{comp.athens_average:.0f} crimes</span>' \
           f'</div>' \
           f'<div style="background: #e2e8f0; height: 30px; border-radius: 5px; overflow: hidden;">' \
           f'<div style="width: {athens_width}%; height: 100%; background: #6b7280;"></div>' \
           f'</div>' \
           f'</div>' \
           f'<div style="text-align: center; padding: 1em; background: {color}20; border-radius: 0.5em; border-left: 4px solid {color};">' \
           f'<div style="font-size: 1.1em; font-weight: 600; color: {color};">{comp.difference_percentage:+.0f}% vs average</div>' \
           f'<div style="color: #64748b; margin-top: 0.5em;">{comp.relative_ranking}</div>' \
           f'</div>' \
           f'</div>'

    return html
