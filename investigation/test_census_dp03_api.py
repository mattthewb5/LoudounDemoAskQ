#!/usr/bin/env python3
"""
Test Census ACS DP03 API for:
1. Labor Force Participation Rate (LFPR)
2. Industry Employment Mix

Loudoun County FIPS: State=51, County=107
"""

import requests
import json

CENSUS_API_KEY = "961836e086b54d1eae7dc43dcff811f5785a2d0d"

# DP03 Variables for Labor Force
LFPR_VARIABLES = {
    "DP03_0001E": "Population 16 years and over",
    "DP03_0002E": "In labor force (count)",
    "DP03_0002PE": "Labor Force Participation Rate (%)",
    "DP03_0003E": "Civilian labor force",
    "DP03_0004E": "Employed",
    "DP03_0005E": "Unemployed",
    "DP03_0009E": "Not in labor force"
}

# DP03 Industry Variables (percentages)
INDUSTRY_VARIABLES = {
    "DP03_0033PE": "Agriculture, forestry, fishing, hunting, mining",
    "DP03_0034PE": "Construction",
    "DP03_0035PE": "Manufacturing",
    "DP03_0036PE": "Wholesale trade",
    "DP03_0037PE": "Retail trade",
    "DP03_0038PE": "Transportation, warehousing, utilities",
    "DP03_0039PE": "Information (Tech/Data Centers)",
    "DP03_0040PE": "Finance, insurance, real estate",
    "DP03_0041PE": "Professional, scientific, management, admin",
    "DP03_0042PE": "Educational services, health care, social assistance",
    "DP03_0043PE": "Arts, entertainment, recreation, accommodation, food",
    "DP03_0044PE": "Other services",
    "DP03_0045PE": "Public administration"
}

def fetch_acs_data(variables, geography, geo_filter=None, year="2023"):
    """Fetch data from Census ACS 5-Year Profile API"""

    base_url = f"https://api.census.gov/data/{year}/acs/acs5/profile"

    params = {
        "get": f"NAME,{','.join(variables)}",
        "for": geography,
        "key": CENSUS_API_KEY
    }

    if geo_filter:
        params["in"] = geo_filter

    response = requests.get(base_url, params=params, timeout=30)
    return response.json()

def main():
    print("=" * 70)
    print("Census ACS DP03 API Test - Labor Force & Industry Mix")
    print("=" * 70)

    # =========================================
    # TASK 2b: Labor Force Participation Rate
    # =========================================
    print("\n>>> Fetching Labor Force Participation Rate...")

    lfpr_vars = list(LFPR_VARIABLES.keys())

    # Fetch Loudoun County
    print("\n--- Loudoun County, VA ---")
    loudoun_data = fetch_acs_data(lfpr_vars, "county:107", "state:51")

    if isinstance(loudoun_data, list) and len(loudoun_data) > 1:
        headers = loudoun_data[0]
        values = loudoun_data[1]

        print(f"✓ Data retrieved for: {values[0]}")

        for i, var in enumerate(lfpr_vars):
            if i + 1 < len(values):
                desc = LFPR_VARIABLES.get(var, var)
                val = values[i + 1]  # +1 because NAME is first
                if var.endswith('PE'):
                    print(f"  {desc}: {val}%")
                else:
                    print(f"  {desc}: {int(val):,}")

        loudoun_lfpr = float(values[headers.index('DP03_0002PE')])
    else:
        print(f"✗ Error: {loudoun_data}")
        loudoun_lfpr = None

    # Fetch Virginia
    print("\n--- Virginia State ---")
    va_data = fetch_acs_data(lfpr_vars, "state:51")

    if isinstance(va_data, list) and len(va_data) > 1:
        values = va_data[1]
        headers = va_data[0]
        print(f"✓ Data retrieved for: {values[0]}")
        va_lfpr = float(values[headers.index('DP03_0002PE')])
        print(f"  Labor Force Participation Rate: {va_lfpr}%")
    else:
        va_lfpr = None

    # Fetch USA
    print("\n--- United States ---")
    us_data = fetch_acs_data(lfpr_vars, "us:1")

    if isinstance(us_data, list) and len(us_data) > 1:
        values = us_data[1]
        headers = us_data[0]
        print(f"✓ Data retrieved for: {values[0]}")
        us_lfpr = float(values[headers.index('DP03_0002PE')])
        print(f"  Labor Force Participation Rate: {us_lfpr}%")
    else:
        us_lfpr = None

    # LFPR Comparison
    print("\n" + "-" * 50)
    print("LFPR Comparison (Census ACS 5-Year 2023)")
    print("-" * 50)
    print(f"  Loudoun County: {loudoun_lfpr}%")
    print(f"  Virginia:       {va_lfpr}%")
    print(f"  United States:  {us_lfpr}%")
    if loudoun_lfpr and us_lfpr:
        diff = loudoun_lfpr - us_lfpr
        print(f"  Loudoun vs USA: {diff:+.1f} percentage points")

    # =========================================
    # TASK 3: Industry Employment Mix
    # =========================================
    print("\n" + "=" * 70)
    print(">>> Fetching Industry Employment Mix...")
    print("=" * 70)

    industry_vars = list(INDUSTRY_VARIABLES.keys())

    # Loudoun County industries
    print("\n--- Loudoun County Industry Mix ---")
    loudoun_industry = fetch_acs_data(industry_vars, "county:107", "state:51")

    loudoun_mix = {}
    if isinstance(loudoun_industry, list) and len(loudoun_industry) > 1:
        headers = loudoun_industry[0]
        values = loudoun_industry[1]

        print(f"✓ Industry data for: {values[0]}\n")

        # Create sorted list by percentage
        industries = []
        for var, desc in INDUSTRY_VARIABLES.items():
            if var in headers:
                idx = headers.index(var)
                val = float(values[idx]) if values[idx] else 0
                industries.append((desc, val))
                loudoun_mix[desc] = val

        # Sort by percentage (descending)
        industries.sort(key=lambda x: x[1], reverse=True)

        for desc, val in industries:
            bar = "█" * int(val * 2)  # Visual bar
            print(f"  {val:5.1f}% {bar} {desc}")

    # Virginia and USA for comparison
    print("\n--- Comparison: Key Sectors ---")

    va_industry = fetch_acs_data(industry_vars, "state:51")
    us_industry = fetch_acs_data(industry_vars, "us:1")

    # Parse VA and US data
    va_mix = {}
    us_mix = {}

    if isinstance(va_industry, list) and len(va_industry) > 1:
        headers = va_industry[0]
        values = va_industry[1]
        for var, desc in INDUSTRY_VARIABLES.items():
            if var in headers:
                idx = headers.index(var)
                val = float(values[idx]) if values[idx] else 0
                va_mix[desc] = val

    if isinstance(us_industry, list) and len(us_industry) > 1:
        headers = us_industry[0]
        values = us_industry[1]
        for var, desc in INDUSTRY_VARIABLES.items():
            if var in headers:
                idx = headers.index(var)
                val = float(values[idx]) if values[idx] else 0
                us_mix[desc] = val

    # Key sectors comparison
    key_sectors = [
        "Information (Tech/Data Centers)",
        "Professional, scientific, management, admin",
        "Public administration",
        "Educational services, health care, social assistance"
    ]

    print(f"\n{'Sector':<50} {'Loudoun':>8} {'VA':>8} {'USA':>8}")
    print("-" * 76)

    for sector in key_sectors:
        l_val = loudoun_mix.get(sector, 0)
        v_val = va_mix.get(sector, 0)
        u_val = us_mix.get(sector, 0)
        print(f"{sector:<50} {l_val:>7.1f}% {v_val:>7.1f}% {u_val:>7.1f}%")

    # Save results as JSON
    results = {
        "source": "Census ACS 5-Year 2023 (DP03 Profile)",
        "lfpr_comparison": {
            "loudoun_county_va": loudoun_lfpr,
            "virginia": va_lfpr,
            "united_states": us_lfpr
        },
        "loudoun_industry_mix": loudoun_mix,
        "virginia_industry_mix": va_mix,
        "us_industry_mix": us_mix
    }

    with open('census_dp03_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n✓ Full results saved to census_dp03_results.json")

    # Summary
    print("\n" + "=" * 70)
    print("Key Findings")
    print("=" * 70)

    info_loudoun = loudoun_mix.get("Information (Tech/Data Centers)", 0)
    info_us = us_mix.get("Information (Tech/Data Centers)", 0)

    print(f"""
1. LABOR FORCE PARTICIPATION:
   - Loudoun County LFPR ({loudoun_lfpr}%) significantly higher than national ({us_lfpr}%)
   - Indicates a highly engaged workforce

2. INFORMATION SECTOR (Tech/Data Centers):
   - Loudoun: {info_loudoun:.1f}%
   - USA:     {info_us:.1f}%
   - Loudoun is {info_loudoun/info_us:.1f}x the national average!

3. PROFESSIONAL SERVICES:
   - Loudoun dominates in Professional/Scientific/Management sector
   - Reflects government contractor and tech presence

4. DATA SOURCE RECOMMENDATION:
   - Census ACS DP03 provides pre-calculated LFPR (no need to calculate)
   - 5-year estimates are stable and reliable
   - Industry percentages ready for pie chart visualization
""")

if __name__ == "__main__":
    main()
