#!/usr/bin/env python3
"""
Example usage of the school district lookup tool
"""

from school_district_lookup import SchoolDistrictLookup, AddressNormalizer, print_school_assignment


def example_single_lookup():
    """Example: Look up a single address"""
    print("=" * 70)
    print("Example 1: Single Address Lookup")
    print("=" * 70)
    print()

    # Initialize the lookup tool
    lookup = SchoolDistrictLookup(data_dir="data")

    # Look up an address
    address = "150 Hancock Avenue, Athens, GA 30601"
    assignment = lookup.lookup_school_district(address)

    # Print results
    print_school_assignment(address, assignment)


def example_batch_lookup():
    """Example: Look up multiple addresses"""
    print("\n" + "=" * 70)
    print("Example 2: Batch Address Lookup")
    print("=" * 70)
    print()

    addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    lookup = SchoolDistrictLookup(data_dir="data")

    results = []
    for address in addresses:
        assignment = lookup.lookup_school_district(address)
        results.append((address, assignment))
        print(f"✓ Processed: {address}")

    # Print summary
    print("\n" + "=" * 70)
    print("Summary of Results")
    print("=" * 70)
    print(f"{'Address':<40} {'Elementary':<25} {'Middle':<20} {'High':<20}")
    print("-" * 105)

    for addr, assignment in results:
        short_addr = addr.split(',')[0]  # Just street address
        elem = assignment.elementary or "N/A"
        middle = assignment.middle or "N/A"
        high = assignment.high or "N/A"
        print(f"{short_addr:<40} {elem:<25} {middle:<20} {high:<20}")


def example_address_normalization():
    """Example: Show address normalization"""
    print("\n" + "=" * 70)
    print("Example 3: Address Normalization")
    print("=" * 70)
    print()

    test_addresses = [
        "123 Main St",
        "123 Main Street",
        "456 Oak Ave",
        "456 Oak Avenue",
        "789 N Elm Dr",
        "789 North Elm Drive"
    ]

    print(f"{'Original':<30} {'Normalized':<30}")
    print("-" * 60)

    for addr in test_addresses:
        normalized = AddressNormalizer.normalize(addr)
        print(f"{addr:<30} {normalized:<30}")


def example_coordinates():
    """Example: Show geocoding coordinates"""
    print("\n" + "=" * 70)
    print("Example 4: Geocoding Coordinates")
    print("=" * 70)
    print()

    addresses = [
        "150 Hancock Avenue, Athens, GA 30601",
        "585 Reese Street, Athens, GA 30601",
        "195 Hoyt Street, Athens, GA 30601"
    ]

    lookup = SchoolDistrictLookup(data_dir="data")

    print(f"{'Address':<40} {'Latitude':<15} {'Longitude':<15}")
    print("-" * 70)

    for address in addresses:
        coords = lookup.geocode_address(address)
        if coords:
            lat, lon = coords
            print(f"{address.split(',')[0]:<40} {lat:<15.6f} {lon:<15.6f}")
        else:
            print(f"{address.split(',')[0]:<40} {'Failed':<15} {'Failed':<15}")


if __name__ == "__main__":
    # Run all examples
    example_single_lookup()
    example_batch_lookup()
    example_address_normalization()
    example_coordinates()

    print("\n" + "=" * 70)
    print("All examples complete!")
    print("=" * 70)
