"""
Property Value Forecasting Engine
Generates short-term and long-term property value forecasts.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class Forecast:
    """Property value forecast."""
    current_value: int
    forecast_months: int
    low_estimate: int
    mid_estimate: int
    high_estimate: int
    annual_appreciation_rate: float
    confidence_score: float
    factors: List[str]


class ForecastEngine:
    """Generates property value forecasts."""

    # Historical average appreciation rates
    DEFAULT_ANNUAL_RATE = 0.04  # 4% national average
    OPTIMISTIC_RATE = 0.06      # 6% for strong markets
    PESSIMISTIC_RATE = 0.02     # 2% for slow markets

    def __init__(self):
        pass

    def generate_forecast(
        self,
        current_value: int,
        months: int = 12,
        market_trend: Optional[str] = None,
        confidence_score: float = 50.0,
        comparable_count: int = 0
    ) -> Forecast:
        """
        Generate property value forecast.

        Args:
            current_value: Current estimated property value
            months: Number of months to forecast
            market_trend: Market trend indicator ('strong', 'moderate', 'weak', None)
            confidence_score: Confidence score from comparables analysis (0-100)
            comparable_count: Number of comparable sales used

        Returns:
            Forecast object with projections
        """
        # Determine appreciation rates based on market trend
        if market_trend == 'strong':
            base_rate = self.OPTIMISTIC_RATE
            low_rate = self.DEFAULT_ANNUAL_RATE
            high_rate = self.OPTIMISTIC_RATE * 1.2
        elif market_trend == 'weak':
            base_rate = self.PESSIMISTIC_RATE
            low_rate = 0.0
            high_rate = self.DEFAULT_ANNUAL_RATE
        else:  # moderate or None
            base_rate = self.DEFAULT_ANNUAL_RATE
            low_rate = self.PESSIMISTIC_RATE
            high_rate = self.OPTIMISTIC_RATE

        # Calculate monthly rates
        monthly_low = (1 + low_rate) ** (1/12) - 1
        monthly_mid = (1 + base_rate) ** (1/12) - 1
        monthly_high = (1 + high_rate) ** (1/12) - 1

        # Project values
        low_estimate = int(current_value * ((1 + monthly_low) ** months))
        mid_estimate = int(current_value * ((1 + monthly_mid) ** months))
        high_estimate = int(current_value * ((1 + monthly_high) ** months))

        # Identify factors affecting confidence
        factors = self._identify_factors(
            market_trend,
            confidence_score,
            comparable_count,
            months
        )

        return Forecast(
            current_value=current_value,
            forecast_months=months,
            low_estimate=low_estimate,
            mid_estimate=mid_estimate,
            high_estimate=high_estimate,
            annual_appreciation_rate=base_rate,
            confidence_score=confidence_score,
            factors=factors
        )

    def _identify_factors(
        self,
        market_trend: Optional[str],
        confidence_score: float,
        comparable_count: int,
        months: int
    ) -> List[str]:
        """Identify factors affecting forecast confidence."""
        factors = []

        # Market trend factor
        if market_trend == 'strong':
            factors.append("Strong market conditions support higher appreciation")
        elif market_trend == 'weak':
            factors.append("Weak market conditions may limit appreciation")
        else:
            factors.append("Moderate market conditions assumed")

        # Data quality factor
        if confidence_score >= 70:
            factors.append("High-quality comparable sales data")
        elif confidence_score >= 40:
            factors.append("Moderate comparable sales data available")
        else:
            factors.append("Limited comparable sales data - higher uncertainty")

        # Time horizon factor
        if months <= 6:
            factors.append("Short-term forecast - more predictable")
        elif months <= 12:
            factors.append("Medium-term forecast - moderate uncertainty")
        else:
            factors.append("Long-term forecast - higher uncertainty")

        # Comparable count factor
        if comparable_count >= 5:
            factors.append(f"Good sample size ({comparable_count} comparables)")
        elif comparable_count >= 3:
            factors.append(f"Adequate comparables ({comparable_count} sales)")
        else:
            factors.append(f"Limited comparables ({comparable_count} sales) - less reliable")

        return factors

    def format_forecast_report(self, forecast: Forecast) -> str:
        """Format forecast report for display."""
        # Calculate appreciation amounts
        low_change = forecast.low_estimate - forecast.current_value
        mid_change = forecast.mid_estimate - forecast.current_value
        high_change = forecast.high_estimate - forecast.current_value

        # Calculate percentages
        low_pct = (low_change / forecast.current_value) * 100
        mid_pct = (mid_change / forecast.current_value) * 100
        high_pct = (high_change / forecast.current_value) * 100

        lines = [
            "",
            "=" * 70,
            f"{forecast.forecast_months}-MONTH VALUE FORECAST",
            "=" * 70,
            f"Current Estimated Value: ${forecast.current_value:,}",
            f"Base Appreciation Rate: {forecast.annual_appreciation_rate * 100:.1f}% annually",
            "",
            "Projected Value Range:",
            f"  Low Estimate:  ${forecast.low_estimate:,}  (+${low_change:,}, +{low_pct:.1f}%)",
            f"  Mid Estimate:  ${forecast.mid_estimate:,}  (+${mid_change:,}, +{mid_pct:.1f}%)",
            f"  High Estimate: ${forecast.high_estimate:,}  (+${high_change:,}, +{high_pct:.1f}%)",
            "",
            f"Forecast Confidence: {forecast.confidence_score:.1f}/100",
            "",
            "Key Factors:",
        ]

        for factor in forecast.factors:
            lines.append(f"  • {factor}")

        lines.extend([
            "",
            "⚠ Disclaimer: This forecast is based on historical trends and current",
            "  market data. Actual values may vary significantly due to market",
            "  conditions, property improvements, or economic factors.",
            "=" * 70
        ])

        return "\n".join(lines)

    def generate_multi_period_forecast(
        self,
        current_value: int,
        periods: List[int] = [3, 6, 12],
        **kwargs
    ) -> List[Forecast]:
        """
        Generate forecasts for multiple time periods.

        Args:
            current_value: Current estimated value
            periods: List of month periods to forecast
            **kwargs: Additional arguments passed to generate_forecast()

        Returns:
            List of Forecast objects
        """
        forecasts = []
        for months in periods:
            forecast = self.generate_forecast(
                current_value=current_value,
                months=months,
                **kwargs
            )
            forecasts.append(forecast)
        return forecasts


if __name__ == '__main__':
    # Test forecast engine
    engine = ForecastEngine()

    # Generate 12-month forecast
    test_value = 1439000
    forecast = engine.generate_forecast(
        current_value=test_value,
        months=12,
        market_trend='moderate',
        confidence_score=65.0,
        comparable_count=10
    )

    print(engine.format_forecast_report(forecast))

    # Multi-period forecast
    print("\n" + "=" * 70)
    print("MULTI-PERIOD FORECASTS")
    print("=" * 70)

    forecasts = engine.generate_multi_period_forecast(
        current_value=test_value,
        periods=[3, 6, 12],
        market_trend='moderate',
        confidence_score=65.0,
        comparable_count=10
    )

    for f in forecasts:
        mid_change = f.mid_estimate - f.current_value
        mid_pct = (mid_change / f.current_value) * 100
        print(f"\n{f.forecast_months} months: ${f.mid_estimate:,} (+{mid_pct:.1f}%)")
        print(f"  Range: ${f.low_estimate:,} - ${f.high_estimate:,}")
