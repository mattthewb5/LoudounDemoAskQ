#!/usr/bin/env python3
"""
Diagnose valuation issue for 43423 Cloister Place
Show all comparables and identify why the estimate is too low.
"""

from api_config import get_api_key
from attom_client import ATTOMClient
from comparable_analyzer import ComparableAnalyzer
from datetime import datetime

# Initialize
attom_key = get_api_key('ATTOM_API_KEY')
attom = ATTOMClient(attom_key)
analyzer = ComparableAnalyzer()

address = "43423 Cloister Place, Leesburg, VA 20176"

print("=" * 80)
print("VALUATION DIAGNOSTIC FOR 43423 CLOISTER PLACE")
print("=" * 80)

# Get subject property
print("\n1. SUBJECT PROPERTY:")
print("-" * 80)
subject = attom.get_property_detail(address)
if subject:
    print(f"Address: {subject.address}")
    print(f"Square Footage: {subject.sqft} sqft")
    print(f"Bedrooms: {subject.bedrooms}")
    print(f"Bathrooms: {subject.bathrooms}")
    print(f"Year Built: {subject.year_built}")
    print(f"Last Sale Price: ${subject.last_sale_price:,}" if subject.last_sale_price else "Last Sale Price: N/A")
    print(f"Last Sale Date: {subject.last_sale_date}" if subject.last_sale_date else "Last Sale Date: N/A")
else:
    print("ERROR: Could not fetch subject property")
    exit(1)

# Get comparables
print("\n2. ALL COMPARABLE SALES (within 0.5 miles, last 6 months):")
print("-" * 80)
comparables = attom.get_comparable_sales(address, radius_miles=0.5, months_back=6, enrich_sqft=True)

if not comparables:
    print("ERROR: No comparables found")
    exit(1)

print(f"\nFound {len(comparables)} comparable sales\n")

# Show each comparable
for i, comp in enumerate(comparables, 1):
    print(f"\n#{i} - {comp.address}")
    print(f"  Sale Price:      ${comp.sale_price:,}")
    print(f"  Sale Date:       {comp.sale_date}")

    # Parse date to calculate age
    try:
        sale_date = datetime.strptime(comp.sale_date, '%m/%d/%Y')
        months_ago = (datetime.now() - sale_date).days / 30.4
        years_ago = months_ago / 12
        if years_ago >= 1:
            print(f"  Age of Sale:     {years_ago:.1f} years ago")
        else:
            print(f"  Age of Sale:     {months_ago:.1f} months ago")
    except:
        print(f"  Age of Sale:     Unknown")

    print(f"  Square Footage:  {comp.sqft} sqft" if comp.sqft else "  Square Footage:  N/A")
    print(f"  Price per sqft:  ${comp.price_per_sqft:.2f}" if comp.price_per_sqft else "  Price per sqft:  N/A")
    print(f"  Bedrooms:        {comp.bedrooms}" if comp.bedrooms else "  Bedrooms:        N/A")
    print(f"  Bathrooms:       {comp.bathrooms}" if comp.bathrooms else "  Bathrooms:       N/A")
    print(f"  Distance:        {comp.distance_miles} miles")

    # Size difference from subject
    if comp.sqft and subject.sqft:
        size_diff_pct = ((comp.sqft - subject.sqft) / subject.sqft) * 100
        print(f"  Size vs Subject: {size_diff_pct:+.1f}%")

print("\n" + "=" * 80)
print("3. ANALYSIS BY YEAR:")
print("-" * 80)

# Group by year
comps_by_year = {}
for comp in comparables:
    try:
        sale_date = datetime.strptime(comp.sale_date, '%m/%d/%Y')
        year = sale_date.year
        if year not in comps_by_year:
            comps_by_year[year] = []
        comps_by_year[year].append(comp)
    except:
        pass

for year in sorted(comps_by_year.keys(), reverse=True):
    comps = comps_by_year[year]
    avg_price = sum(c.sale_price for c in comps) / len(comps)
    avg_ppf = sum(c.price_per_sqft for c in comps if c.price_per_sqft) / len([c for c in comps if c.price_per_sqft])
    print(f"\n{year}: {len(comps)} sales")
    print(f"  Average Price: ${avg_price:,.0f}")
    print(f"  Average $/sqft: ${avg_ppf:.2f}")
    print(f"  Price Range: ${min(c.sale_price for c in comps):,} - ${max(c.sale_price for c in comps):,}")

# Calculate estimate with only recent sales
print("\n" + "=" * 80)
print("4. ESTIMATE WITH RECENT SALES ONLY (2024-2025):")
print("-" * 80)

recent_comps = []
for comp in comparables:
    try:
        sale_date = datetime.strptime(comp.sale_date, '%m/%d/%Y')
        if sale_date.year >= 2024:
            recent_comps.append(comp)
    except:
        pass

if recent_comps:
    print(f"\nUsing {len(recent_comps)} sales from 2024-2025:")
    for comp in recent_comps:
        print(f"  - {comp.address}: ${comp.sale_price:,} ({comp.sale_date})")

    # Calculate size-weighted estimate with recent comps
    size_weighted = analyzer.calculate_size_weighted_estimate(recent_comps, subject.sqft)

    # Calculate median
    median_price = sorted([c.sale_price for c in recent_comps])[len(recent_comps)//2]

    print(f"\nRecent Comparables Analysis:")
    print(f"  Median Sale Price: ${median_price:,}")
    if size_weighted:
        print(f"  Size-Weighted Estimate: ${size_weighted:,.0f}")

    # Calculate average price per sqft
    ppf_values = [c.price_per_sqft for c in recent_comps if c.price_per_sqft]
    if ppf_values:
        avg_ppf = sum(ppf_values) / len(ppf_values)
        print(f"  Average $/sqft: ${avg_ppf:.2f}")
        print(f"  Applied to {subject.sqft} sqft: ${avg_ppf * subject.sqft:,.0f}")
else:
    print("\nNo sales from 2024-2025 found!")

# Current system estimate
print("\n" + "=" * 80)
print("5. CURRENT SYSTEM ESTIMATE:")
print("-" * 80)

analysis = analyzer.analyze_comparables(comparables, target_sqft=subject.sqft)
value_estimate = analyzer.estimate_value(
    analysis,
    target_sqft=subject.sqft,
    api_estimate=None,
    comparables=comparables
)

print(f"\nAll Comparables (current system):")
print(f"  Estimate: ${value_estimate['estimate']:,}")
print(f"  Confidence: {value_estimate['confidence_score']:.1f}/100")
print(f"  Method: {value_estimate['method']}")

if value_estimate.get('components'):
    print(f"\nComponents:")
    comp = value_estimate['components']
    if comp.get('size_weighted_estimate'):
        print(f"  Size-Weighted: ${comp['size_weighted_estimate']:,}")
    if comp.get('comparable_median'):
        print(f"  Comparable Median: ${comp['comparable_median']:,.0f}")
    if comp.get('price_per_sqft_estimate'):
        print(f"  Price/sqft Estimate: ${comp['price_per_sqft_estimate']:,}")

print("\n" + "=" * 80)
print("6. PROBLEM IDENTIFICATION:")
print("-" * 80)

# Check for issues
issues = []

# Check for old sales
old_sales = [c for c in comparables if datetime.strptime(c.sale_date, '%m/%d/%Y').year < 2023]
if old_sales:
    issues.append(f"⚠️  {len(old_sales)} comparables from before 2023 (outdated)")

# Check for same property
same_property = [c for c in comparables if c.address == subject.address]
if same_property:
    issues.append(f"⚠️  Subject property itself is in comparables (should be excluded or given zero weight)")

# Check if subject's last sale is recent but estimate is lower
if subject.last_sale_price and subject.last_sale_date:
    try:
        last_sale = datetime.strptime(subject.last_sale_date, '%m/%d/%Y')
        if last_sale.year >= 2023 and value_estimate['estimate'] < subject.last_sale_price:
            diff_pct = ((subject.last_sale_price - value_estimate['estimate']) / subject.last_sale_price) * 100
            issues.append(f"🚨 MAJOR ISSUE: Estimate (${value_estimate['estimate']:,}) is {diff_pct:.1f}% LOWER than 2023 sale price (${subject.last_sale_price:,})")
    except:
        pass

# Check for very old comps
very_old = [c for c in comparables if (datetime.now() - datetime.strptime(c.sale_date, '%m/%d/%Y')).days > 365*5]
if very_old:
    issues.append(f"⚠️  {len(very_old)} comparables over 5 years old")

if issues:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✓ No obvious issues detected")

print("\n" + "=" * 80)
