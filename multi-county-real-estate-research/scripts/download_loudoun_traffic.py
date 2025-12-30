#!/usr/bin/env python3
"""
Download VDOT Traffic Volume data for Loudoun County.

This script queries the VDOT ArcGIS Feature Service API and saves
traffic volume data as a local GeoJSON file for use by the
LoudounTrafficVolumeAnalyzer.

Data source: VDOT Bidirectional Traffic Volume
API: https://services.arcgis.com/p5v98VHDX9Atv3l7/arcgis/rest/services/VDOTTrafficVolume/FeatureServer/0
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
VDOT_API_URL = "https://services.arcgis.com/p5v98VHDX9Atv3l7/arcgis/rest/services/VDOTTrafficVolume/FeatureServer/0/query"

# Loudoun County bounding box (WGS84)
LOUDOUN_BBOX = {
    "xmin": -77.96,
    "ymin": 38.84,
    "xmax": -77.30,
    "ymax": 39.32
}

# Output configuration
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "loudoun" / "gis" / "traffic"
OUTPUT_FILE = OUTPUT_DIR / "vdot_traffic_volume.geojson"

# Fields to retrieve
OUT_FIELDS = [
    "OBJECTID",
    "ADT",
    "AAWDT",
    "ROUTE_NAME",
    "ROUTE_COMMON_NAME",
    "ROUTE_ALIAS",
    "START_LABEL",
    "END_LABEL",
    "DATA_DATE",
    "ADT_QUALITY"
]

# Minimum ADT to include (skip low-traffic local roads)
MIN_ADT = 1000


def esri_to_geojson_geometry(esri_geom):
    """
    Convert Esri JSON geometry to GeoJSON geometry.

    Args:
        esri_geom: Esri geometry object with 'paths' (polyline)

    Returns:
        GeoJSON geometry object
    """
    if not esri_geom:
        return None

    # Handle polyline (paths)
    if "paths" in esri_geom:
        paths = esri_geom["paths"]
        if len(paths) == 1:
            return {
                "type": "LineString",
                "coordinates": paths[0]
            }
        else:
            return {
                "type": "MultiLineString",
                "coordinates": paths
            }

    # Handle point
    if "x" in esri_geom and "y" in esri_geom:
        return {
            "type": "Point",
            "coordinates": [esri_geom["x"], esri_geom["y"]]
        }

    return None


def fetch_traffic_data():
    """
    Fetch traffic volume data from VDOT API with pagination.

    Uses ObjectID-based pagination since the API doesn't support resultOffset.

    Returns:
        list: List of GeoJSON features
    """
    all_features = []
    max_object_id = 0
    batch_size = 2000  # API max is 2000

    print(f"Fetching VDOT traffic data for Loudoun County...")
    print(f"Bounding box: {LOUDOUN_BBOX}")
    print(f"Minimum ADT: {MIN_ADT}")
    print()

    iteration = 0
    max_iterations = 20  # Safety limit

    while iteration < max_iterations:
        iteration += 1

        # Build where clause with ObjectID pagination
        if max_object_id > 0:
            where_clause = f"ADT >= {MIN_ADT} AND OBJECTID > {max_object_id}"
        else:
            where_clause = f"ADT >= {MIN_ADT}"

        params = {
            "where": where_clause,
            "geometry": f"{LOUDOUN_BBOX['xmin']},{LOUDOUN_BBOX['ymin']},{LOUDOUN_BBOX['xmax']},{LOUDOUN_BBOX['ymax']}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outFields": ",".join(OUT_FIELDS),
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
            "resultRecordCount": str(batch_size)
        }

        try:
            response = requests.get(VDOT_API_URL, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            break

        # Check for API errors
        if "error" in data:
            print(f"API Error: {data['error']}")
            break

        esri_features = data.get("features", [])
        if not esri_features:
            break

        # Track max ObjectID for pagination
        for esri_feat in esri_features:
            attrs = esri_feat.get("attributes", {})
            obj_id = attrs.get("OBJECTID", 0)
            if obj_id > max_object_id:
                max_object_id = obj_id

            # Convert to GeoJSON feature
            geojson_feat = {
                "type": "Feature",
                "properties": attrs,
                "geometry": esri_to_geojson_geometry(esri_feat.get("geometry"))
            }
            all_features.append(geojson_feat)

        print(f"  Batch {iteration}: {len(esri_features)} features (total: {len(all_features)}, max OID: {max_object_id})")

        # Check if we got fewer than requested (last page)
        exceeded_limit = data.get("exceededTransferLimit", False)
        if not exceeded_limit or len(esri_features) < batch_size:
            break

    return all_features


def save_geojson(features):
    """
    Save features as GeoJSON file.

    Args:
        features: List of GeoJSON features
    """
    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "name": "vdot_traffic_volume_loudoun",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "metadata": {
            "source": "VDOT Bidirectional Traffic Volume",
            "api_url": VDOT_API_URL,
            "download_date": datetime.now().isoformat(),
            "bounding_box": LOUDOUN_BBOX,
            "min_adt_filter": MIN_ADT,
            "feature_count": len(features)
        },
        "features": features
    }

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(geojson, f)

    # Get file size
    file_size = OUTPUT_FILE.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print()
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")

    return file_size


def print_sample(features):
    """Print a sample of the data structure."""
    if not features:
        return

    print()
    print("=" * 60)
    print("SAMPLE DATA STRUCTURE")
    print("=" * 60)

    # Get a high-ADT example
    sorted_features = sorted(
        features,
        key=lambda f: f.get("properties", {}).get("ADT", 0) or 0,
        reverse=True
    )

    for i, feature in enumerate(sorted_features[:3]):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        print(f"\nFeature {i+1}:")
        print(f"  Route: {props.get('ROUTE_COMMON_NAME', 'N/A')}")
        print(f"  VDOT ID: {props.get('ROUTE_NAME', 'N/A')}")
        adt = props.get('ADT')
        print(f"  ADT: {adt:,}" if adt else "  ADT: N/A")
        print(f"  From: {str(props.get('START_LABEL', 'N/A'))[:50]}")
        print(f"  To: {str(props.get('END_LABEL', 'N/A'))[:50]}")
        print(f"  Geometry type: {geom.get('type', 'N/A') if geom else 'None'}")
        if geom and geom.get('coordinates'):
            coords = geom['coordinates']
            if isinstance(coords[0], list):
                print(f"  Coordinates: {len(coords)} points")
            else:
                print(f"  Coordinates: {coords[:2]}...")


def print_summary(features):
    """Print summary statistics."""
    if not features:
        return

    print()
    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    # ADT statistics
    adts = [f["properties"].get("ADT", 0) or 0 for f in features]
    adts = [a for a in adts if a > 0]

    if adts:
        print(f"ADT Range: {min(adts):,} - {max(adts):,}")
        print(f"Average ADT: {sum(adts) // len(adts):,}")

    # Count by route type
    route_types = {}
    for f in features:
        route = f["properties"].get("ROUTE_COMMON_NAME", "Unknown")
        # Extract route prefix (VA-7, US-15, SC-xxx, etc.)
        if route:
            prefix = route.split()[0] if route else "Unknown"
            # Simplify to category
            if prefix.startswith("VA-") or prefix.startswith("SR-"):
                cat = "State Routes (VA/SR)"
            elif prefix.startswith("US-"):
                cat = "US Routes"
            elif prefix.startswith("SC-"):
                cat = "Secondary County Roads (SC)"
            elif prefix.startswith("I-"):
                cat = "Interstate"
            elif prefix.startswith("FR-"):
                cat = "Farm Roads (FR)"
            elif prefix.startswith("BUS"):
                cat = "Business Routes"
            elif prefix.startswith("OT-"):
                cat = "Other Routes (OT)"
            else:
                cat = "Named/Local Roads"
            route_types[cat] = route_types.get(cat, 0) + 1

    print()
    print("Road segments by type:")
    for cat, count in sorted(route_types.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("VDOT TRAFFIC VOLUME DOWNLOAD FOR LOUDOUN COUNTY")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch data
    features = fetch_traffic_data()

    if not features:
        print("ERROR: No features retrieved!")
        return 1

    print()
    print(f"Total features retrieved: {len(features)}")

    # Save to file
    save_geojson(features)

    # Print sample and summary
    print_sample(features)
    print_summary(features)

    print()
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
