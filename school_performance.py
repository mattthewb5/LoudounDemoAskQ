#!/usr/bin/env python3
"""
Georgia School Performance Data
Data from GOSA (Governor's Office of Student Achievement)
"""

import csv
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TestScores:
    """Test performance metrics"""
    subject: str
    year: str
    num_tested: int
    proficient_pct: float
    distinguished_pct: float
    total_proficient_pct: float  # Proficient + Distinguished


@dataclass
class Demographics:
    """Student demographics"""
    total_enrollment: int = 0
    pct_asian: float = 0.0
    pct_black: float = 0.0
    pct_hispanic: float = 0.0
    pct_white: float = 0.0
    pct_multiracial: float = 0.0
    pct_economically_disadvantaged: float = 0.0
    pct_english_learners: float = 0.0
    pct_students_with_disabilities: float = 0.0


@dataclass
class SchoolPerformance:
    """Complete school performance data"""
    school_name: str
    district_name: str
    school_level: str  # Elementary, Middle, High

    # Test scores
    test_scores: List[TestScores] = field(default_factory=list)

    # High school specific
    graduation_rate: Optional[float] = None
    avg_sat_score: Optional[int] = None
    avg_act_score: Optional[float] = None
    hope_eligibility_pct: Optional[float] = None

    # Attendance
    chronic_absence_pct: Optional[float] = None

    # Demographics
    demographics: Optional[Demographics] = None

    # Notable info
    achievements: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)


class SchoolPerformanceDB:
    """Database of school performance data"""

    def __init__(self, data_dir: str = "data/performance"):
        self.data_dir = data_dir
        self.schools = {}  # {school_name: SchoolPerformance}
        self._load_data()

    def _load_data(self):
        """Load all performance data from CSV files"""
        print("Loading school performance data...")

        # Load test scores (EOG and EOC)
        self._load_test_scores()

        # Load demographics
        self._load_demographics()

        # Load graduation rates
        self._load_graduation_rates()

        # Load SAT scores
        self._load_sat_scores()

        # Load ACT scores
        self._load_act_scores()

        # Load HOPE eligibility
        self._load_hope_eligibility()

        # Load attendance/chronic absence data
        self._load_attendance()

        # Analyze and add achievements/concerns
        self._analyze_performance()

        print(f"Loaded data for {len(self.schools)} schools")

    def _normalize_school_name(self, name: str) -> str:
        """Normalize school name for lookup"""
        # Remove "Elementary School", "Middle School", "High School" suffixes
        # to allow flexible matching
        normalized = name.lower().strip()

        # Standardize common name variations
        name_variations = {
            'johnnie l. burks': 'johnnie lay burks',
            'johnnie l burks': 'johnnie lay burks',
            'bettye h. holston': 'bettye henderson holston',
            'bettye h holston': 'bettye henderson holston',
            'elementary c': 'cleveland road',
            'b-h-l': 'burney-harris-lyons',
            'bhl': 'burney-harris-lyons',
        }

        for variant, standard in name_variations.items():
            if variant in normalized:
                normalized = normalized.replace(variant, standard)

        # Standardize common variations
        # Note: Order matters - check longer strings first
        replacements = [
            (' elementary school', ''),
            (' middle school', ''),
            (' high school', ''),
            (' elem school', ''),
            (' elementary', ''),
            (' middle', ''),
            (' high', ''),
            (' elem', ''),
            (' ms', ''),
            (' hs', ''),
            (' school', ''),
        ]

        for old, new in replacements:
            if old in normalized:
                normalized = normalized.replace(old, new)

        return normalized.strip()

    def _get_historical_name_mappings(self):
        """Map renamed schools to their historical names for data continuity.

        Returns tuple of:
        - dict mapping old normalized names to new normalized names
        - dict mapping new normalized names to current display names
        This allows loading historical data under the current school names.
        """
        # Map old names to new normalized names
        name_mappings = {
            # Schools renamed between 2022-23 and 2023-24
            'chase street': 'johnnie lay burks',
            'alps road': 'bettye henderson holston',
        }
        # Map new normalized names to current display names
        display_names = {
            'johnnie lay burks': 'Johnnie Lay Burks Elementary School',
            'bettye henderson holston': 'Bettye Henderson Holston Elementary School',
        }
        return name_mappings, display_names

    def _load_test_scores(self):
        """Load Georgia Milestones test scores from consolidated files (2018-19 through 2023-24)"""
        # Use consolidated files which contain all years (2018-19, 2020-21, 2021-22, 2022-23, 2023-24)
        # Note: 2019-20 data not available (COVID year)
        test_files = ['eog_scores_consolidated.csv', 'eoc_scores_consolidated.csv']

        # Get historical name mappings for renamed schools
        historical_mappings, display_names = self._get_historical_name_mappings()

        for test_file in test_files:
            filepath = os.path.join(self.data_dir, test_file)
            if not os.path.exists(filepath):
                continue

            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter for Clarke County and "All Students" subgroup
                    if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                        continue
                    if row['SUBGROUP_NAME'] != 'All Students':
                        continue
                    # Filter for ALL GRADES (or accept empty which means all grades in consolidated files)
                    acdmc_lvl = row.get('ACDMC_LVL', '')
                    if acdmc_lvl and acdmc_lvl != 'ALL GRADES':
                        continue

                    school_name = row['INSTN_NAME']
                    normalized_name = self._normalize_school_name(school_name)

                    # Map old school names to new names for renamed schools
                    # This allows historical data to be combined under current school names
                    if normalized_name in historical_mappings:
                        normalized_name = historical_mappings[normalized_name]
                        # Use the current display name for renamed schools
                        school_name = display_names.get(normalized_name, school_name)

                    # Initialize school if not exists
                    if normalized_name not in self.schools:
                        level = self._determine_school_level(school_name)
                        self.schools[normalized_name] = SchoolPerformance(
                            school_name=school_name,
                            district_name=row['SCHOOL_DSTRCT_NM'],
                            school_level=level
                        )

                    # Add test score
                    try:
                        prof_pct = float(row['PROFICIENT_PCT']) if row['PROFICIENT_PCT'] not in ['', 'TFS'] else 0.0
                        dist_pct = float(row['DISTINGUISHED_PCT']) if row['DISTINGUISHED_PCT'] not in ['', 'TFS'] else 0.0
                        num_tested = int(float(row['NUM_TESTED_CNT'])) if row['NUM_TESTED_CNT'] not in ['', 'TFS'] else 0

                        score = TestScores(
                            subject=row['TEST_CMPNT_TYP_NM'],
                            year=row['LONG_SCHOOL_YEAR'],
                            num_tested=num_tested,
                            proficient_pct=prof_pct,
                            distinguished_pct=dist_pct,
                            total_proficient_pct=prof_pct + dist_pct
                        )

                        self.schools[normalized_name].test_scores.append(score)
                    except (ValueError, KeyError):
                        continue

    def _load_demographics(self):
        """Load enrollment demographics"""
        filepath = os.path.join(self.data_dir, 'enrollment_2023-24.csv')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue
                if row['DETAIL_LVL_DESC'] != 'School':
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                # Parse demographics
                try:
                    demo = Demographics()

                    # Percentages
                    demo.pct_asian = float(row.get('ENROLL_PCT_ASIAN', 0) or 0)
                    demo.pct_black = float(row.get('ENROLL_PCT_BLACK', 0) or 0)
                    demo.pct_hispanic = float(row.get('ENROLL_PCT_HISPANIC', 0) or 0)
                    demo.pct_white = float(row.get('ENROLL_PCT_WHITE', 0) or 0)
                    demo.pct_multiracial = float(row.get('ENROLL_PCT_MULTI', 0) or 0)
                    demo.pct_economically_disadvantaged = float(row.get('ENROLL_PCT_ED', 0) or 0)
                    demo.pct_english_learners = float(row.get('ENROLL_PCT_EL', 0) or 0)
                    demo.pct_students_with_disabilities = float(row.get('ENROLL_PCT_SWD', 0) or 0)

                    # Total enrollment
                    demo.total_enrollment = int(float(row.get('ENROLL_TOTAL', 0) or 0))

                    self.schools[normalized_name].demographics = demo
                except (ValueError, KeyError):
                    continue

    def _load_graduation_rates(self):
        """Load high school graduation rates from consolidated file"""
        # Try consolidated file first, fall back to single-year file
        filepath = os.path.join(self.data_dir, 'graduation_rates_consolidated.csv')
        if not os.path.exists(filepath):
            filepath = os.path.join(self.data_dir, 'graduation_2023-24.csv')
            if not os.path.exists(filepath):
                return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Track most recent year per school
            school_grad_rates = {}  # {normalized_name: (year, rate)}

            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue
                if row.get('DETAIL_LVL_DESC', 'School') != 'School':
                    continue
                if row.get('LABEL_LVL_1_DESC', '') != 'Grad Rate -ALL Students':
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                try:
                    # Use PROGRAM_PERCENT for consolidated, PROGRAM_RATE for single-year
                    grad_rate = float(row.get('PROGRAM_PERCENT') or row.get('PROGRAM_RATE') or 0)
                    year = row.get('LONG_SCHOOL_YEAR', '2023-24')

                    # Keep the most recent year's data
                    if normalized_name not in school_grad_rates or year > school_grad_rates[normalized_name][0]:
                        school_grad_rates[normalized_name] = (year, grad_rate)
                except (ValueError, KeyError):
                    continue

            # Apply the most recent graduation rates
            for normalized_name, (year, grad_rate) in school_grad_rates.items():
                self.schools[normalized_name].graduation_rate = grad_rate

    def _load_sat_scores(self):
        """Load SAT scores for high schools from consolidated file"""
        # Try consolidated file first, fall back to single-year file
        filepath = os.path.join(self.data_dir, 'sat_scores_consolidated.csv')
        if not os.path.exists(filepath):
            filepath = os.path.join(self.data_dir, 'sat_2023-24.csv')
            if not os.path.exists(filepath):
                return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Track most recent year per school
            school_sat_scores = {}  # {normalized_name: (year, score)}

            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue
                if row.get('SUBGRP_DESC', row.get('SUBGRP_DESC', '')) != 'All Students':
                    continue
                # Look for combined/total score
                test_type = row.get('TEST_CMPNT_TYP_CD', '')
                if test_type not in ['SAT_TOTAL', 'Combined Test Score']:
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                try:
                    # Use INSTN_AVG_SCORE_VAL for consolidated, AVG_SCORE for single-year
                    avg_score = int(float(row.get('INSTN_AVG_SCORE_VAL') or row.get('AVG_SCORE') or 0))
                    year = row.get('LONG_SCHOOL_YEAR', '2023-24')

                    # Keep the most recent year's data
                    if normalized_name not in school_sat_scores or year > school_sat_scores[normalized_name][0]:
                        school_sat_scores[normalized_name] = (year, avg_score)
                except (ValueError, KeyError):
                    continue

            # Apply the most recent SAT scores
            for normalized_name, (year, avg_score) in school_sat_scores.items():
                self.schools[normalized_name].avg_sat_score = avg_score

    def _load_act_scores(self):
        """Load ACT scores for high schools from consolidated file"""
        filepath = os.path.join(self.data_dir, 'act_scores_consolidated.csv')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Track most recent year per school
            school_act_scores = {}  # {normalized_name: (year, score)}

            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue
                if row.get('SUBGRP_DESC', '') != 'All Students':
                    continue
                # Look for composite score
                if row.get('TEST_CMPNT_TYP_CD', '') != 'Composite':
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                try:
                    avg_score = float(row.get('INSTN_AVG_SCORE_VAL') or 0)
                    year = row.get('LONG_SCHOOL_YEAR', '2023-24')

                    # Keep the most recent year's data
                    if normalized_name not in school_act_scores or year > school_act_scores[normalized_name][0]:
                        school_act_scores[normalized_name] = (year, avg_score)
                except (ValueError, KeyError):
                    continue

            # Apply the most recent ACT scores
            for normalized_name, (year, avg_score) in school_act_scores.items():
                self.schools[normalized_name].avg_act_score = avg_score

    def _load_hope_eligibility(self):
        """Load HOPE scholarship eligibility rates from consolidated file"""
        filepath = os.path.join(self.data_dir, 'hope_eligibility_consolidated.csv')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Track most recent year per school
            school_hope = {}  # {normalized_name: (year, pct)}

            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                try:
                    hope_pct = float(row.get('HOPE_ELIGIBLE_PCT') or 0)
                    year = row.get('LONG_SCHOOL_YEAR', '2023-24')

                    # Keep the most recent year's data
                    if normalized_name not in school_hope or year > school_hope[normalized_name][0]:
                        school_hope[normalized_name] = (year, hope_pct)
                except (ValueError, KeyError):
                    continue

            # Apply the most recent HOPE eligibility rates
            for normalized_name, (year, hope_pct) in school_hope.items():
                self.schools[normalized_name].hope_eligibility_pct = hope_pct

    def _load_attendance(self):
        """Load chronic absence rates from consolidated file"""
        filepath = os.path.join(self.data_dir, 'attendance_consolidated.csv')
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            # Track most recent year per school
            school_attendance = {}  # {normalized_name: (year, chronic_absence_pct)}

            for row in reader:
                if row['SCHOOL_DSTRCT_NM'] != 'Clarke County':
                    continue
                if row.get('DETAIL_LVL_DESC', 'School') != 'School':
                    continue

                school_name = row['INSTN_NAME']
                normalized_name = self._normalize_school_name(school_name)

                if normalized_name not in self.schools:
                    continue

                try:
                    chronic_pct = float(row.get('CHRONIC_ABSENT_PERC_ALL') or 0)
                    year = row.get('LONG_SCHOOL_YEAR', '2023-24')

                    # Keep the most recent year's data
                    if normalized_name not in school_attendance or year > school_attendance[normalized_name][0]:
                        school_attendance[normalized_name] = (year, chronic_pct)
                except (ValueError, KeyError):
                    continue

            # Apply the most recent chronic absence rates
            for normalized_name, (year, chronic_pct) in school_attendance.items():
                self.schools[normalized_name].chronic_absence_pct = chronic_pct

    def _determine_school_level(self, school_name: str) -> str:
        """Determine if school is Elementary, Middle, or High"""
        name_lower = school_name.lower()
        if 'elementary' in name_lower or 'elem' in name_lower:
            return 'Elementary'
        elif 'middle' in name_lower or ' ms' in name_lower:
            return 'Middle'
        elif 'high' in name_lower or ' hs' in name_lower:
            return 'High'
        return 'Unknown'

    def _analyze_performance(self):
        """Analyze performance and add achievements/concerns"""
        for school in self.schools.values():
            # Analyze test scores
            if school.test_scores:
                avg_proficiency = sum(s.total_proficient_pct for s in school.test_scores) / len(school.test_scores)

                if avg_proficiency >= 70:
                    school.achievements.append(f"High academic performance: {avg_proficiency:.1f}% proficient or above")
                elif avg_proficiency < 40:
                    school.concerns.append(f"Below average proficiency: {avg_proficiency:.1f}% proficient or above")

                # Check for specific subjects
                for score in school.test_scores:
                    if score.total_proficient_pct >= 75:
                        school.achievements.append(f"Strong {score.subject} scores: {score.total_proficient_pct:.1f}%")
                    elif score.total_proficient_pct < 35:
                        school.concerns.append(f"Low {score.subject} proficiency: {score.total_proficient_pct:.1f}%")

            # Analyze graduation rate (high schools)
            if school.graduation_rate:
                if school.graduation_rate >= 90:
                    school.achievements.append(f"Excellent graduation rate: {school.graduation_rate:.1f}%")
                elif school.graduation_rate < 75:
                    school.concerns.append(f"Low graduation rate: {school.graduation_rate:.1f}%")

            # Analyze SAT scores (high schools)
            if school.avg_sat_score:
                if school.avg_sat_score >= 1100:
                    school.achievements.append(f"Above average SAT: {school.avg_sat_score}")
                elif school.avg_sat_score < 950:
                    school.concerns.append(f"Below average SAT: {school.avg_sat_score}")

            # Analyze ACT scores (high schools)
            if school.avg_act_score:
                if school.avg_act_score >= 22:
                    school.achievements.append(f"Above average ACT: {school.avg_act_score:.1f}")
                elif school.avg_act_score < 18:
                    school.concerns.append(f"Below average ACT: {school.avg_act_score:.1f}")

            # Analyze HOPE eligibility (high schools)
            if school.hope_eligibility_pct:
                if school.hope_eligibility_pct >= 50:
                    school.achievements.append(f"High HOPE eligibility: {school.hope_eligibility_pct:.1f}%")
                elif school.hope_eligibility_pct < 30:
                    school.concerns.append(f"Low HOPE eligibility: {school.hope_eligibility_pct:.1f}%")

            # Analyze chronic absence
            if school.chronic_absence_pct:
                if school.chronic_absence_pct <= 10:
                    school.achievements.append(f"Low chronic absence: {school.chronic_absence_pct:.1f}%")
                elif school.chronic_absence_pct >= 25:
                    school.concerns.append(f"High chronic absence: {school.chronic_absence_pct:.1f}%")

    def get_school_performance(self, school_name: str) -> Optional[SchoolPerformance]:
        """
        Get performance data for a school

        Args:
            school_name: Name of the school (flexible matching)

        Returns:
            SchoolPerformance object or None if not found
        """
        normalized = self._normalize_school_name(school_name)
        return self.schools.get(normalized)

    def list_schools(self) -> List[str]:
        """List all schools in the database"""
        return [school.school_name for school in self.schools.values()]


# Global instance
_db = None

def get_school_performance(school_name: str) -> Optional[SchoolPerformance]:
    """
    Get performance data for a school

    Args:
        school_name: Name of the school

    Returns:
        SchoolPerformance object with test scores, demographics, etc.
    """
    global _db
    if _db is None:
        _db = SchoolPerformanceDB()

    return _db.get_school_performance(school_name)


def format_performance_report(perf: SchoolPerformance) -> str:
    """Format a performance report for display"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"{perf.school_name}")
    lines.append(f"{perf.district_name} - {perf.school_level} School")
    lines.append("=" * 70)

    # Test Scores
    if perf.test_scores:
        lines.append("\nACADEMIC PERFORMANCE (2023-24):")
        lines.append("-" * 70)
        for score in perf.test_scores:
            lines.append(f"  {score.subject}:")
            lines.append(f"    Proficient or Above: {score.total_proficient_pct:.1f}%")
            lines.append(f"    Students Tested: {score.num_tested}")

    # High School Metrics
    if perf.graduation_rate:
        lines.append("\nGRADUATION RATE:")
        lines.append(f"  {perf.graduation_rate:.1f}%")

    if perf.avg_sat_score and perf.avg_sat_score > 0:
        lines.append("\nSAT SCORES:")
        lines.append(f"  Average: {perf.avg_sat_score}")

    if perf.avg_act_score and perf.avg_act_score > 0:
        lines.append("\nACT SCORES:")
        lines.append(f"  Average Composite: {perf.avg_act_score:.1f}")

    if perf.hope_eligibility_pct and perf.hope_eligibility_pct > 0:
        lines.append("\nHOPE SCHOLARSHIP ELIGIBILITY:")
        lines.append(f"  {perf.hope_eligibility_pct:.1f}% of graduates")

    # Attendance
    if perf.chronic_absence_pct is not None:
        lines.append("\nATTENDANCE:")
        lines.append(f"  Chronic Absence Rate: {perf.chronic_absence_pct:.1f}%")

    # Demographics
    if perf.demographics:
        d = perf.demographics
        lines.append("\nSTUDENT DEMOGRAPHICS:")
        lines.append(f"  Total Enrollment: {d.total_enrollment}")
        lines.append(f"  Economically Disadvantaged: {d.pct_economically_disadvantaged:.1f}%")
        lines.append(f"  English Learners: {d.pct_english_learners:.1f}%")
        lines.append(f"  Students with Disabilities: {d.pct_students_with_disabilities:.1f}%")
        lines.append("\n  Racial/Ethnic Composition:")
        lines.append(f"    White: {d.pct_white:.1f}%")
        lines.append(f"    Black: {d.pct_black:.1f}%")
        lines.append(f"    Hispanic: {d.pct_hispanic:.1f}%")
        lines.append(f"    Asian: {d.pct_asian:.1f}%")
        lines.append(f"    Multiracial: {d.pct_multiracial:.1f}%")

    # Achievements
    if perf.achievements:
        lines.append("\nNOTABLE ACHIEVEMENTS:")
        for achievement in perf.achievements[:3]:  # Top 3
            lines.append(f"  ✓ {achievement}")

    # Concerns
    if perf.concerns:
        lines.append("\nAREAS FOR IMPROVEMENT:")
        for concern in perf.concerns[:3]:  # Top 3
            lines.append(f"  ! {concern}")

    lines.append("=" * 70)

    return "\n".join(lines)


if __name__ == "__main__":
    # Test the module
    print("Testing School Performance Module")
    print()

    # Test with Clarke County schools
    test_schools = [
        "Barrow Elementary",
        "Johnnie L. Burks Elementary",
        "Clarke Middle",
        "Clarke Central High"
    ]

    for school_name in test_schools:
        perf = get_school_performance(school_name)
        if perf:
            print(format_performance_report(perf))
            print()
        else:
            print(f"❌ School not found: {school_name}")
            print()
