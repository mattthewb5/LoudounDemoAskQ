"""
Sales Comparables Analysis for Loudoun County

Provides functions to find and analyze comparable property sales
near a given location. Designed for AI tool integration.

Data sources:
- Sales: Loudoun County Commissioner of Revenue (2020-2025)
- Parcels: Loudoun County GIS parcel boundaries (for coordinates)

File locations:
- Sales: data/loudoun/sales/combined_sales.parquet
- Parcels: ../../data/loudoun/parcels/loudoun_parcels_full.parquet
"""

import hashlib
import json
import math
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

# Try to import shapely - graceful fallback if unavailable
try:
    from shapely import wkb
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    wkb = None


# Data paths - relative to this module's location
_MODULE_DIR = Path(__file__).parent.parent
_DATA_DIR = _MODULE_DIR / 'data' / 'loudoun'
_SALES_FILE = _DATA_DIR / 'sales' / 'combined_sales.parquet'
_PARCELS_FILE = _MODULE_DIR.parent / 'data' / 'loudoun' / 'parcels' / 'loudoun_parcels_full.parquet'

# Cache configuration
_CACHE_DIR = _DATA_DIR / 'cache' / 'sales_comparables'
_CACHE_TTL_DAYS = 30

# Module-level cache for joined data
_sales_with_coords_cache: Optional[pd.DataFrame] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def _get_cache_key(lat: float, lon: float, radius: float, months: int,
                   min_price: Optional[float] = None, max_price: Optional[float] = None) -> str:
    """Generate cache key from search parameters (including price filters)."""
    key_str = f"{round(lat, 3)}_{round(lon, 3)}_{radius}_{months}_{min_price}_{max_price}"
    return hashlib.md5(key_str.encode()).hexdigest()[:12]


def _load_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Load cached result if valid."""
    cache_file = _CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > _CACHE_TTL_DAYS * 86400:
            return None  # Cache expired

        with open(cache_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """Save result to cache."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = _CACHE_DIR / f"{cache_key}.json"

        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except OSError:
        pass  # Caching is optional


def load_sales_with_coordinates() -> pd.DataFrame:
    """
    Load sales data joined with parcel coordinates.

    Joins sales data with parcel boundaries to get lat/lon for each sale.
    Uses zero-padded PARID matching against LU_PIN.

    Returns:
        DataFrame with columns: PARID, RECORD DATE, PRICE, SALE VERIFICATION,
        latitude, longitude, sale_date (parsed datetime)
    """
    global _sales_with_coords_cache

    # Return cached data if available
    if _sales_with_coords_cache is not None:
        return _sales_with_coords_cache

    if not SHAPELY_AVAILABLE:
        return pd.DataFrame()

    try:
        if not _SALES_FILE.exists() or not _PARCELS_FILE.exists():
            return pd.DataFrame()

        # Load sales
        sales = pd.read_parquet(_SALES_FILE)

        # Filter to verified market sales over $100K
        sales = sales[
            (sales['SALE VERIFICATION'] == '1:MARKET SALE') &
            (sales['PRICE'] > 100000)
        ].copy()

        # Zero-pad PARID to 12 digits for matching
        sales['PARID_STR'] = sales['PARID'].astype(str).str.zfill(12)

        # Load parcels and compute centroids
        parcels = pd.read_parquet(_PARCELS_FILE)

        # Parse WKB geometry and compute centroids
        centroids = []
        for idx, row in parcels.iterrows():
            try:
                geom = wkb.loads(row['geometry'])
                centroid = geom.centroid
                centroids.append({
                    'LU_PIN': row['LU_PIN'],
                    'latitude': centroid.y,
                    'longitude': centroid.x
                })
            except Exception:
                continue

        centroids_df = pd.DataFrame(centroids)

        # Join sales with coordinates
        merged = sales.merge(
            centroids_df,
            left_on='PARID_STR',
            right_on='LU_PIN',
            how='inner'
        )

        # Parse sale date
        merged['sale_date'] = pd.to_datetime(merged['RECORD DATE'], errors='coerce')

        # Select and rename columns for clarity
        result = merged[[
            'PARID', 'RECORD DATE', 'PRICE', 'SALE VERIFICATION',
            'SALE TYPE', 'latitude', 'longitude', 'sale_date'
        ]].copy()

        # Cache result
        _sales_with_coords_cache = result
        return result

    except Exception:
        return pd.DataFrame()


def find_comparable_sales(
    lat: float,
    lon: float,
    radius_miles: float = 1.0,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    months_back: int = 12,
    verified_only: bool = True,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Find comparable property sales near a location.

    Args:
        lat: Property latitude (WGS84)
        lon: Property longitude (WGS84)
        radius_miles: Search radius in miles (default 1.0)
        min_price: Minimum sale price filter (optional)
        max_price: Maximum sale price filter (optional)
        months_back: How many months of sales history (default 12)
        verified_only: Only include verified market sales (default True)
        limit: Maximum number of comparables to return (default 20)

    Returns:
        Dict with:
        - available: bool
        - total_found: int (total sales in radius/timeframe)
        - comparables: list of sale records with distance
        - statistics: dict with median_price, price_range, date_range
        - map_data: list of {lat, lon, price, date} for visualization
        - summary: text summary
        - data_source: source attribution
    """
    # Check cache first
    cache_key = _get_cache_key(lat, lon, radius_miles, months_back, min_price, max_price)
    cached = _load_from_cache(cache_key)
    if cached:
        cached['from_cache'] = True
        return cached

    # Load data
    sales_df = load_sales_with_coordinates()

    if sales_df.empty:
        return {
            'available': False,
            'total_found': 0,
            'comparables': [],
            'statistics': None,
            'map_data': [],
            'summary': 'Sales comparables data is not available.',
            'data_source': None,
            'error': 'Could not load sales data'
        }

    # Filter by date
    cutoff_date = datetime.now() - timedelta(days=months_back * 30)
    filtered = sales_df[sales_df['sale_date'] >= cutoff_date].copy()

    if filtered.empty:
        return {
            'available': True,
            'total_found': 0,
            'comparables': [],
            'statistics': None,
            'map_data': [],
            'summary': f'No sales found in the past {months_back} months.',
            'data_source': 'Loudoun County Commissioner of Revenue'
        }

    # Calculate distance to each sale
    filtered['distance_miles'] = filtered.apply(
        lambda row: haversine_distance(lat, lon, row['latitude'], row['longitude']),
        axis=1
    )

    # Filter by radius
    nearby = filtered[filtered['distance_miles'] <= radius_miles].copy()

    # Apply price filters
    if min_price is not None:
        nearby = nearby[nearby['PRICE'] >= min_price]
    if max_price is not None:
        nearby = nearby[nearby['PRICE'] <= max_price]

    # Sort by distance
    nearby = nearby.sort_values('distance_miles')

    total_found = len(nearby)

    if total_found == 0:
        result = {
            'available': True,
            'total_found': 0,
            'comparables': [],
            'statistics': None,
            'map_data': [],
            'summary': f'No comparable sales found within {radius_miles} miles in the past {months_back} months.',
            'data_source': 'Loudoun County Commissioner of Revenue',
            'from_cache': False
        }
        _save_to_cache(cache_key, result)
        return result

    # Build comparables list
    comparables = []
    for _, row in nearby.head(limit).iterrows():
        comparables.append({
            'parid': str(row['PARID']),
            'price': int(row['PRICE']),
            'sale_date': row['sale_date'].strftime('%Y-%m-%d'),
            'sale_type': row.get('SALE TYPE', 'Unknown'),
            'distance_miles': round(row['distance_miles'], 2),
            'latitude': round(row['latitude'], 6),
            'longitude': round(row['longitude'], 6)
        })

    # Calculate statistics
    prices = nearby['PRICE'].values
    dates = nearby['sale_date']

    statistics = {
        'median_price': int(nearby['PRICE'].median()),
        'mean_price': int(nearby['PRICE'].mean()),
        'min_price': int(prices.min()),
        'max_price': int(prices.max()),
        'count': total_found,
        'oldest_sale': dates.min().strftime('%Y-%m-%d'),
        'newest_sale': dates.max().strftime('%Y-%m-%d')
    }

    # Build map data (all points for visualization)
    map_data = []
    for _, row in nearby.iterrows():
        map_data.append({
            'lat': round(row['latitude'], 6),
            'lon': round(row['longitude'], 6),
            'price': int(row['PRICE']),
            'date': row['sale_date'].strftime('%Y-%m-%d')
        })

    # Generate summary
    summary_parts = [f"{total_found} comparable sales within {radius_miles} miles"]
    summary_parts.append(f"in the past {months_back} months.")
    summary_parts.append(f"Median price: ${statistics['median_price']:,}.")
    summary_parts.append(f"Range: ${statistics['min_price']:,} - ${statistics['max_price']:,}.")

    result = {
        'available': True,
        'total_found': total_found,
        'comparables': comparables,
        'statistics': statistics,
        'map_data': map_data,
        'summary': ' '.join(summary_parts),
        'data_source': 'Loudoun County Commissioner of Revenue (2020-2025)',
        'from_cache': False
    }

    _save_to_cache(cache_key, result)
    return result


def get_sales_comparables_summary(
    lat: float,
    lon: float,
    radius_miles: float = 1.0,
    months_back: int = 12
) -> str:
    """
    Get a plain-text summary of comparable sales for a location.

    Args:
        lat: Property latitude
        lon: Property longitude
        radius_miles: Search radius (default 1 mile)
        months_back: Months of history (default 12)

    Returns:
        Human-readable summary string
    """
    result = find_comparable_sales(lat, lon, radius_miles, months_back=months_back)

    if not result.get('available'):
        return "Sales comparables data is not available."

    if result['total_found'] == 0:
        return f"No comparable sales found within {radius_miles} miles in the past {months_back} months."

    lines = [f"Comparable Sales Analysis ({radius_miles} mile radius, {months_back} months):"]
    lines.append("")

    stats = result['statistics']
    lines.append(f"Total Sales: {result['total_found']}")
    lines.append(f"Median Price: ${stats['median_price']:,}")
    lines.append(f"Price Range: ${stats['min_price']:,} - ${stats['max_price']:,}")
    lines.append(f"Date Range: {stats['oldest_sale']} to {stats['newest_sale']}")
    lines.append("")

    # Show top 5 nearest comparables
    lines.append("Nearest Comparables:")
    for i, comp in enumerate(result['comparables'][:5], 1):
        lines.append(f"  {i}. ${comp['price']:,} ({comp['sale_date']}) - {comp['distance_miles']} mi")

    return "\n".join(lines)


def get_market_trends(lat: float, lon: float, radius_miles: float = 2.0) -> Dict[str, Any]:
    """
    Get market trends for an area over multiple time periods.

    Args:
        lat: Property latitude
        lon: Property longitude
        radius_miles: Search radius (default 2 miles)

    Returns:
        Dict with price trends over different periods
    """
    # Get sales for multiple periods
    periods = [6, 12, 24]
    trends = {}

    for months in periods:
        result = find_comparable_sales(lat, lon, radius_miles, months_back=months)
        if result.get('statistics'):
            trends[f'{months}_months'] = {
                'count': result['total_found'],
                'median_price': result['statistics']['median_price']
            }

    return {
        'available': len(trends) > 0,
        'trends': trends,
        'radius_miles': radius_miles,
        'data_source': 'Loudoun County Commissioner of Revenue'
    }
