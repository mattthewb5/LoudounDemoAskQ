#!/usr/bin/env python3
"""
Create sample school zone data for testing the lookup tool
This uses approximate boundaries around Athens-Clarke County schools
"""

import json
import os


def create_sample_elementary_zones():
    """Create sample elementary school zones"""
    # Based on approximate locations in Athens
    zones = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "SCHOOL_NAME": "Barrow Elementary School",
                    "SCHOOL": "Barrow Elementary",
                    "ADDRESS": "175 Hancock Avenue, Athens, GA 30601"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-83.385, 33.955],
                        [-83.365, 33.955],
                        [-83.365, 33.965],
                        [-83.385, 33.965],
                        [-83.385, 33.955]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "SCHOOL_NAME": "Chase Street Elementary School",
                    "SCHOOL": "Chase Street Elementary",
                    "ADDRESS": "1860 S Milledge Avenue, Athens, GA 30605"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-83.390, 33.950],
                        [-83.370, 33.950],
                        [-83.370, 33.960],
                        [-83.390, 33.960],
                        [-83.390, 33.950]
                    ]]
                }
            }
        ]
    }
    return zones


def create_sample_middle_zones():
    """Create sample middle school zones"""
    zones = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "SCHOOL_NAME": "Clarke Middle School",
                    "SCHOOL": "Clarke Middle",
                    "ADDRESS": "350 S Milledge Avenue, Athens, GA 30605"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-83.390, 33.950],
                        [-83.365, 33.950],
                        [-83.365, 33.970],
                        [-83.390, 33.970],
                        [-83.390, 33.950]
                    ]]
                }
            }
        ]
    }
    return zones


def create_sample_high_zones():
    """Create sample high school zones"""
    zones = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "SCHOOL_NAME": "Clarke Central High School",
                    "SCHOOL": "Clarke Central High",
                    "ADDRESS": "350 S Milledge Avenue, Athens, GA 30605"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-83.395, 33.945],
                        [-83.360, 33.945],
                        [-83.360, 33.975],
                        [-83.395, 33.975],
                        [-83.395, 33.945]
                    ]]
                }
            }
        ]
    }
    return zones


def main():
    """Create all sample zone files"""
    os.makedirs("data", exist_ok=True)

    zones = {
        "elementary_zones.geojson": create_sample_elementary_zones(),
        "middle_zones.geojson": create_sample_middle_zones(),
        "high_zones.geojson": create_sample_high_zones()
    }

    for filename, data in zones.items():
        filepath = os.path.join("data", filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Created {filepath}")
        print(f"  {len(data['features'])} school zones")

    print("\nSample data created successfully!")
    print("\n⚠  NOTE: This is SAMPLE data for demonstration only!")
    print("For actual school assignments, download real data from:")
    print("https://data-athensclarke.opendata.arcgis.com/")


if __name__ == "__main__":
    main()
