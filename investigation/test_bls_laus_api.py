#!/usr/bin/env python3
"""
BLS LAUS (Local Area Unemployment Statistics) API
for Loudoun County, VA labor force data.

Enhanced with:
- Year-over-Year (YoY) comparisons
- 12-month moving averages
- Trend analysis
- Explicit dating for OM use

LAUS Series ID Format for Counties:
LAUCN + [STATE FIPS 2-digit] + [COUNTY FIPS 3-digit] + 0000000 + [MEASURE CODE]

Loudoun County FIPS: State=51 (Virginia), County=107

Measure Codes:
03 = Unemployment Rate
04 = Unemployment (count)
05 = Employment (count)
06 = Labor Force (count)

NOTE: BLS county-level LAUS data is NOT seasonally adjusted.
Use YoY comparisons to avoid seasonal distortion.
"""

import requests
import json
from datetime import datetime

# BLS API Key
BLS_API_KEY = "2c6067bf7d374643a2d0502c39be1373"

# Loudoun County Series IDs
SERIES_IDS = {
    "labor_force": "LAUCN511070000000006",
    "employment": "LAUCN511070000000005",
    "unemployment": "LAUCN511070000000004",
    "unemployment_rate": "LAUCN511070000000003"
}

# Virginia State Series IDs (for comparison)
VA_SERIES_IDS = {
    "labor_force": "LASST510000000000006",
    "unemployment_rate": "LASST510000000000003"
}

def fetch_bls_data(series_ids, start_year="2022", end_year="2024"):
    """Fetch data from BLS API v2"""

    headers = {'Content-type': 'application/json'}
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": BLS_API_KEY
    })

    response = requests.post(
        'https://api.bls.gov/publicAPI/v2/timeseries/data/',
        data=data,
        headers=headers,
        timeout=30
    )

    return response.json()

def parse_series_data(series_data):
    """Parse BLS series data into chronological list"""
    data_points = []
    for point in series_data.get('data', []):
        year = int(point.get('year', 0))
        period = point.get('period', 'M00')
        month = int(period[1:]) if period.startswith('M') else 0

        if month > 0:  # Skip annual averages (M13)
            try:
                value = float(point.get('value', 0))
            except:
                value = 0

            data_points.append({
                'year': year,
                'month': month,
                'period_name': point.get('periodName', ''),
                'value': value,
                'date_key': f"{year}-{month:02d}"
            })

    # Sort chronologically (oldest first)
    data_points.sort(key=lambda x: (x['year'], x['month']))
    return data_points

def calculate_yoy_change(current, prior):
    """Calculate year-over-year percentage change"""
    if prior and prior > 0:
        return ((current - prior) / prior) * 100
    return None

def calculate_moving_average(data_points, window=12):
    """Calculate moving average for most recent N months"""
    if len(data_points) < window:
        return None
    recent = data_points[-window:]
    return sum(p['value'] for p in recent) / window

def determine_trend(data_points, window=6):
    """Determine trend direction based on recent data"""
    if len(data_points) < window:
        return "insufficient_data"

    recent = data_points[-window:]
    first_half_avg = sum(p['value'] for p in recent[:3]) / 3
    second_half_avg = sum(p['value'] for p in recent[3:]) / 3

    pct_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0

    if pct_change > 1:
        return "growing"
    elif pct_change < -1:
        return "declining"
    else:
        return "stable"

def main():
    print("=" * 70)
    print("BLS LAUS API - Loudoun County, VA")
    print("Enhanced with YoY and Moving Average Analysis")
    print("=" * 70)

    # Fetch 3 years of data (24+ months for moving averages and YoY)
    print("\n>>> Fetching Loudoun County data (2022-2024)...")
    series_list = list(SERIES_IDS.values())
    result = fetch_bls_data(series_list, "2022", "2024")

    if result.get('status') != 'REQUEST_SUCCEEDED':
        print(f"✗ API call failed: {result.get('message', 'Unknown error')}")
        return

    print("✓ API call successful!")

    # Parse data for each series
    parsed_data = {}
    for series in result.get('Results', {}).get('series', []):
        series_id = series.get('seriesID', '')

        # Identify the measure
        measure_name = None
        for name, sid in SERIES_IDS.items():
            if sid == series_id:
                measure_name = name
                break

        if measure_name:
            parsed_data[measure_name] = parse_series_data(series)

    # Process each measure
    output = {
        "fetch_date": datetime.now().strftime("%Y-%m-%d"),
        "source": "BLS Local Area Unemployment Statistics (LAUS)",
        "geography": "Loudoun County, VA (FIPS 51107)",
        "seasonal_adjustment": "Not seasonally adjusted",
        "methodology_note": "County-level LAUS data is not seasonally adjusted. Year-over-year comparisons recommended to avoid seasonal distortion.",
        "metrics": {}
    }

    print("\n" + "=" * 70)
    print("PROCESSED METRICS WITH YoY AND MOVING AVERAGE")
    print("=" * 70)

    for measure_name in ["labor_force", "employment", "unemployment", "unemployment_rate"]:
        if measure_name not in parsed_data:
            continue

        data = parsed_data[measure_name]
        if not data:
            continue

        # Get most recent value
        current = data[-1]
        current_value = current['value']
        current_date = f"{current['period_name']} {current['year']}"

        # Find same month previous year
        prior_year_value = None
        for point in data:
            if point['year'] == current['year'] - 1 and point['month'] == current['month']:
                prior_year_value = point['value']
                break

        # Calculate metrics
        yoy_change = calculate_yoy_change(current_value, prior_year_value)
        moving_avg = calculate_moving_average(data, 12)
        trend = determine_trend(data, 6)

        # Store in output
        is_rate = measure_name == "unemployment_rate"
        metric = {
            "current_value": current_value,
            "current_date": current_date,
            "prior_year_value": prior_year_value,
            "prior_year_date": f"{current['period_name']} {current['year'] - 1}" if prior_year_value else None,
            "yoy_change_pct": round(yoy_change, 2) if yoy_change else None,
            "moving_avg_12mo": round(moving_avg, 1) if moving_avg else None,
            "trend_direction": trend,
            "unit": "percent" if is_rate else "persons"
        }
        output["metrics"][measure_name] = metric

        # Display
        print(f"\n--- {measure_name.replace('_', ' ').title()} ---")

        if is_rate:
            print(f"  Current: {current_value:.1f}% ({current_date})")
            if prior_year_value:
                print(f"  Prior Year: {prior_year_value:.1f}% ({current['period_name']} {current['year'] - 1})")
                if yoy_change:
                    direction = "↑" if yoy_change > 0 else "↓" if yoy_change < 0 else "→"
                    print(f"  YoY Change: {direction} {abs(yoy_change):.1f}% points")
        else:
            print(f"  Current: {current_value:,.0f} ({current_date})")
            if prior_year_value:
                print(f"  Prior Year: {prior_year_value:,.0f} ({current['period_name']} {current['year'] - 1})")
                if yoy_change:
                    direction = "+" if yoy_change > 0 else ""
                    print(f"  YoY Change: {direction}{yoy_change:.1f}%")

        if moving_avg:
            if is_rate:
                print(f"  12-Month Avg: {moving_avg:.1f}%")
            else:
                print(f"  12-Month Avg: {moving_avg:,.0f}")

        print(f"  Trend: {trend.replace('_', ' ').title()}")

    # Fetch Virginia comparison
    print("\n" + "=" * 70)
    print("VIRGINIA STATE COMPARISON")
    print("=" * 70)

    va_result = fetch_bls_data(list(VA_SERIES_IDS.values()), "2023", "2024")
    if va_result.get('status') == 'REQUEST_SUCCEEDED':
        for series in va_result.get('Results', {}).get('series', []):
            series_id = series.get('seriesID', '')
            for name, sid in VA_SERIES_IDS.items():
                if sid == series_id:
                    data = parse_series_data(series)
                    if data:
                        current = data[-1]
                        print(f"  {name.replace('_', ' ').title()}: {current['value']:,.1f} ({current['period_name']} {current['year']})")

    # Summary for OM use
    print("\n" + "=" * 70)
    print("SUMMARY FOR OFFERING MEMORANDUM")
    print("=" * 70)

    lf = output["metrics"].get("labor_force", {})
    ur = output["metrics"].get("unemployment_rate", {})

    print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│  LOUDOUN COUNTY LABOR MARKET SNAPSHOT                              │
│  Source: BLS Local Area Unemployment Statistics                     │
│  Data as of: {lf.get('current_date', 'N/A'):<20}                              │
├─────────────────────────────────────────────────────────────────────┤
│  Labor Force:       {lf.get('current_value', 0):>10,.0f}                                  │
│    └─ YoY Change:   {'+' if (lf.get('yoy_change_pct') or 0) >= 0 else ''}{lf.get('yoy_change_pct', 0):.1f}% vs {lf.get('prior_year_date', 'N/A'):<28}│
│    └─ 12-Mo Avg:    {lf.get('moving_avg_12mo', 0):>10,.0f}                                  │
│    └─ Trend:        {lf.get('trend_direction', 'N/A').title():<20}                      │
│                                                                     │
│  Unemployment Rate: {ur.get('current_value', 0):>10.1f}%                                  │
│    └─ YoY Change:   {'+' if (ur.get('yoy_change_pct') or 0) >= 0 else ''}{ur.get('yoy_change_pct', 0):.1f} pts vs {ur.get('prior_year_date', 'N/A'):<27}│
│                                                                     │
│  ⚠ Data is NOT seasonally adjusted                                 │
│  → Use YoY comparisons for accurate trend analysis                  │
└─────────────────────────────────────────────────────────────────────┘
""")

    # Save processed output
    with open('bls_loudoun_processed.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("✓ Processed data saved to bls_loudoun_processed.json")

if __name__ == "__main__":
    main()
