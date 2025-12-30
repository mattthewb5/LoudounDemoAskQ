"""
Development Pressure Analyzer
Analyzes building permit activity to assess development pressure around properties.
"""

import pandas as pd
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Permit:
    """Building permit information."""
    address: str
    latitude: float
    longitude: float
    permit_type: str
    work_class: str
    construction_cost: float
    description: str
    issue_date: Optional[datetime]
    distance_miles: float = 0.0
    impact_score: int = 0


@dataclass
class DevelopmentPressure:
    """Development pressure analysis results."""
    score: float  # 0-100
    classification: str  # Very High/High/Moderate/Low
    total_permits: int
    permits_within_radius: int
    total_construction_value: float
    avg_construction_cost: float
    new_construction_ratio: float
    recent_activity_ratio: float
    top_permits: List[Permit]
    trend: str  # increasing/stable/decreasing


class DevelopmentPressureAnalyzer:
    """Analyzes building permit data to assess development pressure."""

    # Impact scores for different permit types/work classes
    IMPACT_SCORES = {
        'data center': 10,
        'datacenter': 10,
        'warehouse': 9,
        'multi-family': 9,
        'apartment': 9,
        'townhouse': 8,
        'single family': 8,
        'single-family': 8,
        'sfr': 8,
        'new construction': 8,
        'new building': 8,
        'commercial': 7,
        'retail': 7,
        'office': 7,
        'demolition': 6,
        'demo': 6,
        'addition': 5,
        'alteration': 3,
        'renovation': 3,
        'remodel': 3,
        'deck': 2,
        'pool': 2,
        'fence': 2,
        'shed': 2,
        'minor': 1
    }

    def __init__(self, permits_csv_path: str):
        """
        Initialize analyzer with permits data.

        Args:
            permits_csv_path: Path to geocoded permits CSV file
        """
        self.permits_df = self._load_permits(permits_csv_path)
        print(f"Loaded {len(self.permits_df)} building permits")

    def _load_permits(self, csv_path: str) -> pd.DataFrame:
        """Load and preprocess permits data."""
        df = pd.read_csv(csv_path)

        # Handle different possible date column names
        date_columns = ['Permit Issue Date', 'Issue Date', 'issue_date', 'IssueDate', 'Date']
        date_col = None
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break

        if date_col:
            df['issue_date'] = pd.to_datetime(df[date_col], errors='coerce')
        else:
            df['issue_date'] = None

        # Standardize column names
        column_mapping = {
            'Address': 'address',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Permit Type': 'permit_type',
            'Permit Work Class': 'work_class',
            'Estimated Construction Cost': 'construction_cost',
            'Permit Description': 'description'
        }

        # Note: If columns don't exist with exact names, try alternatives
        if 'address' not in df.columns and 'Address' not in df.columns:
            # Address column might already be lowercase
            pass

        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]

        # Ensure required columns exist
        required = ['address', 'latitude', 'longitude']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Fill missing values
        df['permit_type'] = df.get('permit_type', '').fillna('')
        df['work_class'] = df.get('work_class', '').fillna('')
        df['construction_cost'] = pd.to_numeric(df.get('construction_cost', 0), errors='coerce').fillna(0)
        df['description'] = df.get('description', '').fillna('')

        # Convert latitude and longitude to numeric
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        # Drop rows with invalid coordinates
        df = df.dropna(subset=['latitude', 'longitude'])

        return df

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in miles
        """
        R = 3959.87433  # Earth radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _calculate_impact_score(self, permit_type: str, work_class: str, description: str) -> int:
        """
        Calculate impact score for a permit.

        Args:
            permit_type: Type of permit
            work_class: Work classification
            description: Permit description

        Returns:
            Impact score (0-10)
        """
        # Combine all text fields for matching
        combined = f"{permit_type} {work_class} {description}".lower()

        # Check for matches in priority order
        for keyword, score in sorted(self.IMPACT_SCORES.items(), key=lambda x: -x[1]):
            if keyword in combined:
                return score

        return 1  # Default minimal impact

    def find_nearby_permits(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 0.5
    ) -> List[Permit]:
        """
        Find all permits within radius of a location.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            radius_miles: Search radius in miles

        Returns:
            List of Permit objects within radius
        """
        permits = []

        for _, row in self.permits_df.iterrows():
            # Calculate distance
            distance = self.haversine_distance(
                latitude, longitude,
                row['latitude'], row['longitude']
            )

            if distance <= radius_miles:
                # Calculate impact score
                impact = self._calculate_impact_score(
                    row.get('permit_type', ''),
                    row.get('work_class', ''),
                    row.get('description', '')
                )

                permit = Permit(
                    address=row['address'],
                    latitude=row['latitude'],
                    longitude=row['longitude'],
                    permit_type=row.get('permit_type', 'Unknown'),
                    work_class=row.get('work_class', 'Unknown'),
                    construction_cost=row.get('construction_cost', 0),
                    description=row.get('description', ''),
                    issue_date=row.get('issue_date'),
                    distance_miles=round(distance, 2),
                    impact_score=impact
                )
                permits.append(permit)

        # Sort by distance
        permits.sort(key=lambda p: p.distance_miles)

        return permits

    def analyze_development_pressure(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 0.5
    ) -> DevelopmentPressure:
        """
        Analyze development pressure around a location.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            radius_miles: Analysis radius in miles

        Returns:
            DevelopmentPressure analysis object
        """
        # Find nearby permits
        permits = self.find_nearby_permits(latitude, longitude, radius_miles)

        if not permits:
            return DevelopmentPressure(
                score=0.0,
                classification='Very Low',
                total_permits=len(self.permits_df),
                permits_within_radius=0,
                total_construction_value=0.0,
                avg_construction_cost=0.0,
                new_construction_ratio=0.0,
                recent_activity_ratio=0.0,
                top_permits=[],
                trend='stable'
            )

        # Calculate metrics
        total_value = sum(p.construction_cost for p in permits)
        avg_cost = total_value / len(permits) if permits else 0

        # New construction ratio (impact score >= 7)
        new_construction_count = sum(1 for p in permits if p.impact_score >= 7)
        new_construction_ratio = new_construction_count / len(permits)

        # Recent activity ratio (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        recent_permits = [
            p for p in permits
            if p.issue_date and p.issue_date >= six_months_ago
        ]
        recent_ratio = len(recent_permits) / len(permits) if permits else 0

        # Calculate Development Pressure Score (0-100)

        # Factor 1: Permit Volume (35 points)
        # 0-5 permits = 0-7 points, 6-15 = 8-20, 16-30 = 21-30, 31+ = 31-35
        if len(permits) <= 5:
            volume_score = len(permits) * 1.4
        elif len(permits) <= 15:
            volume_score = 7 + (len(permits) - 5) * 1.3
        elif len(permits) <= 30:
            volume_score = 20 + (len(permits) - 15) * 0.67
        else:
            volume_score = 30 + min((len(permits) - 30) * 0.5, 5)

        # Factor 2: High-value projects (20 points)
        # Based on average construction cost
        if avg_cost >= 1000000:
            value_score = 20
        elif avg_cost >= 500000:
            value_score = 15
        elif avg_cost >= 200000:
            value_score = 10
        elif avg_cost >= 100000:
            value_score = 5
        else:
            value_score = avg_cost / 20000  # $20k = 1 point

        # Factor 3: New construction ratio (25 points)
        construction_score = new_construction_ratio * 25

        # Factor 4: Recency (20 points)
        recency_score = recent_ratio * 20

        total_score = volume_score + value_score + construction_score + recency_score
        total_score = min(total_score, 100)  # Cap at 100

        # Classify pressure level
        if total_score >= 75:
            classification = 'Very High'
        elif total_score >= 50:
            classification = 'High'
        elif total_score >= 25:
            classification = 'Moderate'
        else:
            classification = 'Low'

        # Determine trend
        if len(permits) >= 3:
            # Compare recent 50% vs older 50%
            permits_by_date = [p for p in permits if p.issue_date]
            if permits_by_date:
                permits_by_date.sort(key=lambda p: p.issue_date)
                midpoint = len(permits_by_date) // 2
                recent_half = permits_by_date[midpoint:]
                older_half = permits_by_date[:midpoint]

                recent_avg_impact = sum(p.impact_score for p in recent_half) / len(recent_half)
                older_avg_impact = sum(p.impact_score for p in older_half) / len(older_half) if older_half else 0

                if recent_avg_impact > older_avg_impact * 1.2:
                    trend = 'increasing'
                elif recent_avg_impact < older_avg_impact * 0.8:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        # Get top 5 highest-impact permits
        top_permits = sorted(permits, key=lambda p: (p.impact_score, p.construction_cost), reverse=True)[:5]

        return DevelopmentPressure(
            score=round(total_score, 1),
            classification=classification,
            total_permits=len(self.permits_df),
            permits_within_radius=len(permits),
            total_construction_value=total_value,
            avg_construction_cost=avg_cost,
            new_construction_ratio=new_construction_ratio,
            recent_activity_ratio=recent_ratio,
            top_permits=top_permits,
            trend=trend
        )

    def format_pressure_report(self, pressure: DevelopmentPressure) -> str:
        """Format development pressure report."""
        lines = [
            "",
            "=" * 70,
            "DEVELOPMENT PRESSURE ANALYSIS",
            "=" * 70,
            f"Pressure Score: {pressure.score:.1f}/100 [{pressure.classification}]",
            f"Trend: {pressure.trend.upper()}",
            "",
            "Permit Activity:",
            f"  Total permits in database: {pressure.total_permits:,}",
            f"  Permits within radius: {pressure.permits_within_radius}",
            f"  Total construction value: ${pressure.total_construction_value:,.0f}",
            f"  Average cost per permit: ${pressure.avg_construction_cost:,.0f}",
            "",
            "Activity Composition:",
            f"  New construction ratio: {pressure.new_construction_ratio:.1%}",
            f"  Recent activity (6 months): {pressure.recent_activity_ratio:.1%}",
        ]

        if pressure.top_permits:
            lines.extend([
                "",
                "Top 5 Highest-Impact Nearby Permits:",
                "-" * 70
            ])

            for i, permit in enumerate(pressure.top_permits, 1):
                lines.append(f"\n#{i} [{permit.impact_score}/10] - {permit.address}")
                lines.append(f"  Type: {permit.work_class or permit.permit_type}")
                if permit.construction_cost > 0:
                    lines.append(f"  Cost: ${permit.construction_cost:,.0f}")
                lines.append(f"  Distance: {permit.distance_miles} miles")
                if permit.description:
                    lines.append(f"  Description: {permit.description[:80]}")

        lines.append("=" * 70)
        return "\n".join(lines)


if __name__ == '__main__':
    # Test the analyzer
    import sys

    permits_file = 'multi-county-real-estate-research/data/loudoun/building_permits/loudoun_permits_2024_2025_complete.csv'

    print("Testing Development Pressure Analyzer")
    print("=" * 70)

    try:
        analyzer = DevelopmentPressureAnalyzer(permits_file)

        # Test with 43423 Cloister Place coordinates
        test_lat = 39.112034
        test_lon = -77.497359

        print(f"\nAnalyzing development pressure at:")
        print(f"  Latitude: {test_lat}")
        print(f"  Longitude: {test_lon}")
        print(f"  Radius: 0.5 miles")

        pressure = analyzer.analyze_development_pressure(test_lat, test_lon, radius_miles=0.5)
        print(analyzer.format_pressure_report(pressure))

    except FileNotFoundError:
        print(f"\n❌ Error: Permits file not found at {permits_file}")
        print("Please ensure the geocoded permits CSV is available.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
