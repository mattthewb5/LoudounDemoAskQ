#!/usr/bin/env python3
"""
ATTOM API Data Diagnostic
Shows raw JSON responses from ATTOM API endpoints.
"""

import json
import requests
from api_config import get_api_key


def print_json(data, title):
    """Pretty print JSON data."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(json.dumps(data, indent=2))
    print("=" * 80)


def analyze_fields(data, path=""):
    """Recursively analyze which fields have data vs null."""
    results = {'with_data': [], 'null_or_empty': []}

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            if value is None or value == "" or value == {}:
                results['null_or_empty'].append(current_path)
            elif isinstance(value, (dict, list)):
                sub_results = analyze_fields(value, current_path)
                results['with_data'].extend(sub_results['with_data'])
                results['null_or_empty'].extend(sub_results['null_or_empty'])
            else:
                results['with_data'].append(f"{current_path} = {value}")

    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            sub_results = analyze_fields(item, current_path)
            results['with_data'].extend(sub_results['with_data'])
            results['null_or_empty'].extend(sub_results['null_or_empty'])

    return results


def test_endpoint(session, endpoint, params, name):
    """Test an ATTOM API endpoint and show results."""
    print(f"\n{'#' * 80}")
    print(f"# Testing: {name}")
    print(f"# Endpoint: {endpoint}")
    print(f"# Params: {params}")
    print(f"{'#' * 80}")

    try:
        url = f"https://api.gateway.attomdata.com/propertyapi/v1.0.0/{endpoint}"
        response = session.get(url, params=params)

        print(f"\nHTTP Status: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'x-ratelimit-remaining', 'x-ratelimit-limit']:
                print(f"  {key}: {value}")

        if response.status_code == 200:
            data = response.json()
            print_json(data, f"RAW JSON RESPONSE - {name}")

            # Analyze fields
            print(f"\n{'-' * 80}")
            print("FIELD ANALYSIS")
            print(f"{'-' * 80}")

            analysis = analyze_fields(data)

            print(f"\nFields WITH DATA ({len(analysis['with_data'])}):")
            for field in analysis['with_data'][:30]:  # Show first 30
                print(f"  ✓ {field}")
            if len(analysis['with_data']) > 30:
                print(f"  ... and {len(analysis['with_data']) - 30} more")

            print(f"\nFields that are NULL/EMPTY ({len(analysis['null_or_empty'])}):")
            for field in analysis['null_or_empty'][:20]:  # Show first 20
                print(f"  ✗ {field}")
            if len(analysis['null_or_empty']) > 20:
                print(f"  ... and {len(analysis['null_or_empty']) - 20} more")

            # Check specifically for sqft-related fields
            sqft_fields = [f for f in analysis['with_data'] if 'size' in f.lower() or 'sqft' in f.lower() or 'area' in f.lower()]
            if sqft_fields:
                print(f"\n⚠️  SIZE-RELATED FIELDS FOUND:")
                for field in sqft_fields:
                    print(f"  • {field}")
            else:
                print(f"\n❌ NO SIZE-RELATED FIELDS FOUND (livingsize, sqft, area, etc.)")

            return data

        elif response.status_code == 401:
            print(f"\n❌ AUTHENTICATION FAILED")
            print(f"Response: {response.text}")
            return None

        elif response.status_code == 403:
            print(f"\n❌ FORBIDDEN - This endpoint may not be included in your subscription")
            print(f"Response: {response.text}")
            return None

        else:
            print(f"\n❌ ERROR - Status {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        return None


def main():
    """Run ATTOM API diagnostics."""

    # Load API key
    api_key = get_api_key('ATTOM_API_KEY')
    if not api_key:
        print("❌ ERROR: ATTOM_API_KEY not found in config")
        return

    # Create session
    session = requests.Session()
    session.headers.update({
        'apikey': api_key,
        'Accept': 'application/json'
    })

    # Test address
    address = "43500 Tuckaway Pl, Leesburg, VA 20176"

    print(f"\n{'=' * 80}")
    print(f"ATTOM API DATA DIAGNOSTIC")
    print(f"{'=' * 80}")
    print(f"Target Property: {address}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"{'=' * 80}")

    # Test different endpoints
    endpoints = [
        {
            'name': 'Property Detail',
            'endpoint': 'property/detail',
            'params': {'address': address}
        },
        {
            'name': 'Property Basic Profile',
            'endpoint': 'property/basicprofile',
            'params': {'address': address}
        },
        {
            'name': 'Property Expanded Profile',
            'endpoint': 'property/expandedprofile',
            'params': {'address': address}
        },
        {
            'name': 'Assessment Detail',
            'endpoint': 'assessment/detail',
            'params': {'address': address}
        },
        {
            'name': 'AVM (Automated Valuation Model)',
            'endpoint': 'avm',
            'params': {'address': address}
        }
    ]

    results = {}
    for ep in endpoints:
        result = test_endpoint(session, ep['endpoint'], ep['params'], ep['name'])
        results[ep['name']] = result

    # Summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    print(f"\nEndpoint Access:")
    for name, result in results.items():
        if result is not None:
            status = result.get('status', {})
            code = status.get('code', 'unknown')
            msg = status.get('msg', 'No message')
            print(f"  {'✓' if code == 0 else '✗'} {name}: code={code}, msg={msg}")
        else:
            print(f"  ✗ {name}: Failed to retrieve data")

    print(f"\n{'=' * 80}")
    print("SQFT DATA AVAILABILITY SUMMARY")
    print(f"{'=' * 80}")

    sqft_found = False
    for name, result in results.items():
        if result:
            # Check for building.size.livingsize
            try:
                props = result.get('property', [])
                if props:
                    prop = props[0]
                    building = prop.get('building', {})
                    size = building.get('size', {})
                    livingsize = size.get('livingsize')

                    if livingsize:
                        print(f"  ✓ {name}: Living size = {livingsize} sqft")
                        sqft_found = True
                    else:
                        print(f"  ✗ {name}: No living size data")
            except Exception as e:
                print(f"  ✗ {name}: Error checking for sqft - {e}")

    if not sqft_found:
        print(f"\n❌ CONCLUSION: No square footage data available from ATTOM for this property")
        print(f"   This is likely a DATA AVAILABILITY issue, not an endpoint or subscription issue.")
        print(f"   ATTOM does not have building size information for properties in this area.")
    else:
        print(f"\n✓ CONCLUSION: Square footage data IS available from ATTOM!")

    print(f"\n{'=' * 80}\n")


if __name__ == '__main__':
    main()
