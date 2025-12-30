#!/usr/bin/env python3
"""
GOSA Data Loader - Wrapper for school_performance module
Provides interface expected by streamlit_app.py
"""

from typing import Optional, Dict, Any
from school_performance import SchoolPerformanceDB, get_school_performance, SchoolPerformance


# Global instance for caching
_gosa_loader = None


def get_gosa_loader() -> SchoolPerformanceDB:
    """
    Get a SchoolPerformanceDB instance (cached)

    Returns:
        SchoolPerformanceDB instance with loaded GOSA data
    """
    global _gosa_loader
    if _gosa_loader is None:
        _gosa_loader = SchoolPerformanceDB()
    return _gosa_loader


def get_school_performance_for_analysis(school_name: str) -> Optional[Dict[str, Any]]:
    """
    Get school performance data formatted for analysis display

    Args:
        school_name: Name of the school

    Returns:
        Dictionary with performance metrics or None if not found
    """
    perf = get_school_performance(school_name)

    if perf is None:
        return None

    # Calculate average proficiency from test scores
    avg_proficiency = 0.0
    total_tested = 0
    subjects = {}
    years = {}

    if perf.test_scores:
        # Calculate overall average
        avg_proficiency = sum(s.total_proficient_pct for s in perf.test_scores) / len(perf.test_scores)
        total_tested = sum(s.num_tested for s in perf.test_scores)

        # Group by subject
        for score in perf.test_scores:
            subjects[score.subject] = score.total_proficient_pct

            # Group by year (use average across subjects for each year)
            if score.year not in years:
                years[score.year] = []
            years[score.year].append(score.total_proficient_pct)

        # Average the years
        years = {year: sum(scores) / len(scores) for year, scores in years.items()}

    # Build result dictionary
    result = {
        'avg_proficiency': avg_proficiency,
        'total_tested': total_tested,
        'subjects': subjects,
        'years': years,
        'is_high_school': perf.school_level == 'High',
        'graduation_rate': perf.graduation_rate,
        'sat_total': perf.avg_sat_score,
        'act_composite': perf.avg_act_score,
        'hope_eligibility_pct': perf.hope_eligibility_pct,
        'chronic_absence_pct': perf.chronic_absence_pct,
    }

    return result
