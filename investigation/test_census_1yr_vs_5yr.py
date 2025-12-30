#!/usr/bin/env python3
"""
Compare Census ACS 1-Year vs 5-Year estimates for Loudoun County
to determine which is more appropriate for Offering Memorandum use.

Key Variables:
- DP03_0002PE: Labor Force Participation Rate (%)
- DP03_0002PM: Margin of Error for LFPR
- DP03_0033PE - DP03_0045PE: Industry sector percentages
"""

import requests
import json

CENSUS_API_KEY = "961836e086b54d1eae7dc43dcff811f5785a2d0d"

# Variables to compare
LFPR_VARS = [
    "DP03_0001E",   # Population 16+
    "DP03_0002E",   # In labor force
    "DP03_0002PE",  # LFPR %
    "DP03_0002PM",  # LFPR margin of error
    "DP03_0004PE",  # Employment-to-population ratio
    "DP03_0004PM",  # Emp-to-pop MOE
]

INDUSTRY_VARS = [
    ("DP03_0033PE", "DP03_0033PM", "Agriculture/Mining"),
    ("DP03_0034PE", "DP03_0034PM", "Construction"),
    ("DP03_0035PE", "DP03_0035PM", "Manufacturing"),
    ("DP03_0036PE", "DP03_0036PM", "Wholesale trade"),
    ("DP03_0037PE", "DP03_0037PM", "Retail trade"),
    ("DP03_0038PE", "DP03_0038PM", "Transportation/Utilities"),
    ("DP03_0039PE", "DP03_0039PM", "Information (Tech)"),
    ("DP03_0040PE", "DP03_0040PM", "Finance/Insurance/RE"),
    ("DP03_0041PE", "DP03_0041PM", "Professional/Scientific"),
    ("DP03_0042PE", "DP03_0042PM", "Education/Healthcare"),
    ("DP03_0043PE", "DP03_0043PM", "Arts/Entertainment/Food"),
    ("DP03_0044PE", "DP03_0044PM", "Other services"),
    ("DP03_0045PE", "DP03_0045PM", "Public administration"),
]

def fetch_acs_data(year, dataset, geography, geo_filter=None):
    """Fetch ACS profile data"""

    # Build variable list
    all_vars = ["NAME"] + LFPR_VARS
    for pe, pm, _ in INDUSTRY_VARS:
        all_vars.extend([pe, pm])

    base_url = f"https://api.census.gov/data/{year}/acs/{dataset}/profile"

    params = {
        "get": ",".join(all_vars),
        "for": geography,
        "key": CENSUS_API_KEY
    }

    if geo_filter:
        params["in"] = geo_filter

    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def parse_response(data, dataset_name):
    """Parse Census API response into structured dict"""
    if isinstance(data, dict) and "error" in data:
        return None

    if not isinstance(data, list) or len(data) < 2:
        return None

    headers = data[0]
    values = data[1]

    result = {"dataset": dataset_name, "name": values[0]}

    # Parse LFPR variables
    for var in LFPR_VARS:
        if var in headers:
            idx = headers.index(var)
            val = values[idx]
            try:
                result[var] = float(val) if val and val != "-888888888" else None
            except:
                result[var] = None

    # Parse industry variables
    result["industries"] = {}
    for pe, pm, name in INDUSTRY_VARS:
        if pe in headers and pm in headers:
            pe_idx = headers.index(pe)
            pm_idx = headers.index(pm)
            pe_val = values[pe_idx]
            pm_val = values[pm_idx]
            try:
                result["industries"][name] = {
                    "value": float(pe_val) if pe_val and pe_val != "-888888888" else None,
                    "moe": float(pm_val) if pm_val and pm_val != "-888888888" else None
                }
            except:
                result["industries"][name] = {"value": None, "moe": None}

    return result

def main():
    print("=" * 80)
    print("Census ACS 1-Year vs 5-Year Comparison - Loudoun County, VA")
    print("=" * 80)

    results = {}

    # Fetch 1-Year data (2023)
    print("\n>>> Fetching 1-Year ACS 2023 data...")
    data_1yr = fetch_acs_data("2023", "acs1", "county:107", "state:51")
    results["1yr"] = parse_response(data_1yr, "ACS 1-Year 2023")

    if results["1yr"]:
        print(f"✓ Retrieved: {results['1yr']['name']}")
    else:
        print(f"✗ Error: {data_1yr}")

    # Fetch 5-Year data (2019-2023)
    print("\n>>> Fetching 5-Year ACS 2019-2023 data...")
    data_5yr = fetch_acs_data("2023", "acs5", "county:107", "state:51")
    results["5yr"] = parse_response(data_5yr, "ACS 5-Year 2019-2023")

    if results["5yr"]:
        print(f"✓ Retrieved: {results['5yr']['name']}")
    else:
        print(f"✗ Error: {data_5yr}")

    # Comparison table
    if results["1yr"] and results["5yr"]:
        print("\n" + "=" * 80)
        print("LABOR FORCE PARTICIPATION RATE COMPARISON")
        print("=" * 80)

        lfpr_1yr = results["1yr"].get("DP03_0002PE")
        lfpr_5yr = results["5yr"].get("DP03_0002PE")
        moe_1yr = results["1yr"].get("DP03_0002PM")
        moe_5yr = results["5yr"].get("DP03_0002PM")

        emp_1yr = results["1yr"].get("DP03_0004PE")
        emp_5yr = results["5yr"].get("DP03_0004PE")
        emp_moe_1yr = results["1yr"].get("DP03_0004PM")
        emp_moe_5yr = results["5yr"].get("DP03_0004PM")

        print(f"\n{'Metric':<35} {'1-Year (2023)':<18} {'5-Year (2019-23)':<18} {'Difference':<12}")
        print("-" * 80)

        if lfpr_1yr and lfpr_5yr:
            diff = lfpr_1yr - lfpr_5yr
            print(f"{'Labor Force Participation Rate':<35} {lfpr_1yr:>7.1f}%          {lfpr_5yr:>7.1f}%          {diff:>+6.1f}%")

        if moe_1yr and moe_5yr:
            print(f"{'  └─ Margin of Error (±)':<35} {moe_1yr:>7.1f}%          {moe_5yr:>7.1f}%")

        if emp_1yr and emp_5yr:
            diff = emp_1yr - emp_5yr
            print(f"{'Employment-to-Population Ratio':<35} {emp_1yr:>7.1f}%          {emp_5yr:>7.1f}%          {diff:>+6.1f}%")

        if emp_moe_1yr and emp_moe_5yr:
            print(f"{'  └─ Margin of Error (±)':<35} {emp_moe_1yr:>7.1f}%          {emp_moe_5yr:>7.1f}%")

        # Industry comparison
        print("\n" + "=" * 80)
        print("INDUSTRY EMPLOYMENT MIX COMPARISON")
        print("=" * 80)

        print(f"\n{'Sector':<30} {'1-Yr Value':<12} {'1-Yr MOE':<10} {'5-Yr Value':<12} {'5-Yr MOE':<10} {'Diff':<8}")
        print("-" * 80)

        industries_1yr = results["1yr"].get("industries", {})
        industries_5yr = results["5yr"].get("industries", {})

        for name in [n for _, _, n in INDUSTRY_VARS]:
            v1 = industries_1yr.get(name, {}).get("value")
            m1 = industries_1yr.get(name, {}).get("moe")
            v5 = industries_5yr.get(name, {}).get("value")
            m5 = industries_5yr.get(name, {}).get("moe")

            v1_str = f"{v1:.1f}%" if v1 is not None else "N/A"
            m1_str = f"±{m1:.1f}" if m1 is not None else "N/A"
            v5_str = f"{v5:.1f}%" if v5 is not None else "N/A"
            m5_str = f"±{m5:.1f}" if m5 is not None else "N/A"

            if v1 is not None and v5 is not None:
                diff = v1 - v5
                diff_str = f"{diff:+.1f}%"
            else:
                diff_str = "N/A"

            print(f"{name:<30} {v1_str:<12} {m1_str:<10} {v5_str:<12} {m5_str:<10} {diff_str:<8}")

        # Analysis and recommendation
        print("\n" + "=" * 80)
        print("ANALYSIS & RECOMMENDATION")
        print("=" * 80)

        # Calculate average MOE difference
        moe_ratio_sum = 0
        moe_count = 0
        for name in [n for _, _, n in INDUSTRY_VARS]:
            m1 = industries_1yr.get(name, {}).get("moe")
            m5 = industries_5yr.get(name, {}).get("moe")
            if m1 and m5 and m5 > 0:
                moe_ratio_sum += m1 / m5
                moe_count += 1

        avg_moe_ratio = moe_ratio_sum / moe_count if moe_count > 0 else 0

        print(f"""
1. DATA RECENCY:
   - 1-Year: Reflects 2023 only (most current)
   - 5-Year: Reflects 2019-2023 average (midpoint ~2021)
   - Gap: ~2 years

2. PRECISION (Margin of Error):
   - 1-Year MOE is approximately {avg_moe_ratio:.1f}x larger than 5-Year
   - Loudoun population (~430,000) supports 1-Year reliability
   - Both are statistically valid for county-level reporting

3. LFPR DIFFERENCE:
   - 1-Year ({lfpr_1yr:.1f}%) vs 5-Year ({lfpr_5yr:.1f}%) = {lfpr_1yr - lfpr_5yr if lfpr_1yr and lfpr_5yr else 'N/A':+.1f}%
   - {"Difference is within margin of error" if moe_1yr and abs(lfpr_1yr - lfpr_5yr) < moe_1yr else "Difference exceeds margin of error - meaningful change"}

4. KEY INDUSTRY DIFFERENCES:
""")

        # Find biggest industry changes
        changes = []
        for name in [n for _, _, n in INDUSTRY_VARS]:
            v1 = industries_1yr.get(name, {}).get("value")
            v5 = industries_5yr.get(name, {}).get("value")
            if v1 is not None and v5 is not None:
                changes.append((name, v1 - v5, v1, v5))

        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        for name, diff, v1, v5 in changes[:3]:
            print(f"   - {name}: {v5:.1f}% → {v1:.1f}% ({diff:+.1f}%)")

        print(f"""
5. RECOMMENDATION FOR OFFERING MEMORANDUM:

   ┌─────────────────────────────────────────────────────────────┐
   │  USE 5-YEAR ACS for baseline metrics (LFPR, Industry Mix)  │
   │  - More stable, lower margin of error                      │
   │  - Suitable for OM narrative and comparisons               │
   │                                                            │
   │  SUPPLEMENT with 1-Year ACS when available                 │
   │  - Note as "most recent" where trends are meaningful       │
   │  - Highlight if significant changes from 5-Year baseline   │
   └─────────────────────────────────────────────────────────────┘
""")

        # Save results
        output = {
            "comparison_date": "2025-12-29",
            "acs_1yr_2023": {
                "lfpr": lfpr_1yr,
                "lfpr_moe": moe_1yr,
                "emp_to_pop_ratio": emp_1yr,
                "emp_to_pop_moe": emp_moe_1yr,
                "industries": industries_1yr
            },
            "acs_5yr_2019_2023": {
                "lfpr": lfpr_5yr,
                "lfpr_moe": moe_5yr,
                "emp_to_pop_ratio": emp_5yr,
                "emp_to_pop_moe": emp_moe_5yr,
                "industries": industries_5yr
            },
            "recommendation": {
                "primary_source": "ACS 5-Year",
                "reason": "Lower margin of error, more stable for OM baseline",
                "supplemental": "ACS 1-Year for trend analysis when meaningful"
            },
            "avg_moe_ratio_1yr_to_5yr": round(avg_moe_ratio, 2)
        }

        with open("census_1yr_vs_5yr_comparison.json", "w") as f:
            json.dump(output, f, indent=2)

        print("✓ Results saved to census_1yr_vs_5yr_comparison.json")

if __name__ == "__main__":
    main()
