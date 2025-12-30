import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.hoa_amenity_scraper import HOAAmenityScraper
import json

scraper = HOAAmenityScraper()

communities = [
    'Broadlands:https://www.broadlandshoa.org',
    'Potomac Station:https://potomacstation.org',
    'Willowsford:https://www.willowsfordlife.com',
    'Brambleton:https://www.brambletonva.com',
    'One Loudoun:https://www.1lna.com',
]

results = []
for entry in communities:
    name, url = entry.split(':', 1)  # Split only on first ":"
    url = url.replace('https:', 'https:')  # Fix if double-split happened
    print(f'Scraping {name}...')
    result = scraper.scrape_community(name, url)
    results.append(result)
    print(f"  Found {len(result.get('amenities', {}))} amenity details")

# Save results
with open('scraped_amenities.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f'\n✓ Saved {len(results)} results to scraped_amenities.json')