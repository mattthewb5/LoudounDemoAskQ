"""
HOA Amenity Scraper

Extracts amenity information from public HOA website pages.
Does NOT require authentication - scrapes public marketing pages only.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import logging
import time

logger = logging.getLogger(__name__)


class HOAAmenityScraper:
    """Scrapes public amenity information from HOA websites."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.request_delay = 1.5  # Seconds between requests

    def scrape_url(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Fetch and parse a URL."""
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers=self.headers,
                allow_redirects=True
            )
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            logger.warning(f"Status {response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_amenities(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract amenity information from parsed HTML.

        Returns dict with amenity counts and boolean flags.
        """
        if not soup:
            return {}

        text = soup.get_text().lower()

        amenities = {}

        # Pools
        pool_count = self._count_amenity(text, ['pool', 'swimming'])
        amenities['pools'] = pool_count
        amenities['has_pool'] = pool_count > 0

        # Tennis courts
        tennis_patterns = [r'(\d+)\s*tennis\s*court', r'tennis.*?(\d+)\s*court']
        tennis_count = self._extract_count(text, tennis_patterns)
        if tennis_count is None:
            tennis_count = 1 if 'tennis' in text and 'court' in text else 0
        amenities['tennis_courts'] = tennis_count
        amenities['has_tennis'] = tennis_count > 0 or 'tennis' in text

        # Clubhouse
        amenities['has_clubhouse'] = any(
            word in text for word in ['clubhouse', 'club house', 'community center']
        )

        # Fitness center
        amenities['has_fitness'] = any(
            word in text for word in ['fitness', 'gym', 'exercise room', 'workout']
        )

        # Trails
        trail_patterns = [r'(\d+)\s*mile.*?trail', r'trail.*?(\d+)\s*mile']
        trail_miles = self._extract_count(text, trail_patterns)
        amenities['trail_miles'] = trail_miles
        amenities['has_trails'] = trail_miles is not None or 'trail' in text

        # Playgrounds / Tot lots
        playground_count = self._count_amenity(text, ['playground', 'tot lot'])
        amenities['playgrounds'] = playground_count
        amenities['has_playground'] = playground_count > 0 or 'playground' in text

        # Basketball
        amenities['has_basketball'] = 'basketball' in text

        # Dog park
        amenities['has_dog_park'] = 'dog park' in text or 'pet area' in text

        # Pickleball (increasingly popular)
        amenities['has_pickleball'] = 'pickleball' in text

        return amenities

    def extract_hoa_fees(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract HOA fee information if publicly listed."""
        if not soup:
            return None

        text = soup.get_text()

        # Common fee patterns
        fee_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?month',
            r'monthly.*?\$(\d+(?:,\d{3})*)',
            r'dues.*?\$(\d+(?:,\d{3})*)',
            r'\$(\d+(?:,\d{3})*)\s*(?:per\s+)?annual',
        ]

        for pattern in fee_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))

                    # Determine if monthly or annual
                    if 'month' in pattern:
                        return {'monthly': amount, 'frequency': 'monthly'}
                    elif 'annual' in pattern:
                        return {'annual': amount, 'frequency': 'annual'}
                    else:
                        # Guess based on amount
                        if amount < 500:
                            return {'monthly': amount, 'frequency': 'monthly'}
                        else:
                            return {'annual': amount, 'frequency': 'annual'}
                except ValueError:
                    continue

        return None

    def _count_amenity(self, text: str, keywords: List[str]) -> int:
        """Count mentions of an amenity type."""
        count = 0
        for keyword in keywords:
            # Look for patterns like "2 pools", "3 swimming pools", etc.
            # Only match small numbers (1-20) to avoid capturing years
            patterns = [
                rf'(\d{{1,2}})\s*{keyword}',  # "2 pools", "10 tennis courts"
            ]
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        val = int(matches[0])
                        if val <= 20:  # Filter out year numbers like 2020, 2025
                            count = max(count, val)
                    except ValueError:
                        pass

        # If no count found but keyword exists, assume 1
        if count == 0:
            if any(keyword in text for keyword in keywords):
                count = 1

        return count

    def _extract_count(self, text: str, patterns: List[str]) -> Optional[int]:
        """Extract a numeric count from text using regex patterns."""
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        return None

    def find_amenity_pages(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Find links to amenity-related pages."""
        if not soup:
            return []

        keywords = [
            'amenity', 'amenities', 'facility', 'facilities',
            'pool', 'recreation', 'about', 'community', 'feature'
        ]

        links = soup.find_all('a', href=True)
        amenity_urls = set()

        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip().lower()

            if any(kw in text or kw in href.lower() for kw in keywords):
                full_url = urljoin(base_url, href)
                # Only same domain
                if base_url.split('/')[2] in full_url:
                    amenity_urls.add(full_url)

        return list(amenity_urls)

    def scrape_community(
        self,
        community_name: str,
        base_url: str,
        additional_urls: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape amenity data for a community.

        Args:
            community_name: Name of community
            base_url: Main HOA website URL
            additional_urls: Additional URLs to scrape (amenity pages, etc.)

        Returns:
            Combined amenity data from all pages
        """
        urls_to_scrape = [base_url]
        if additional_urls:
            urls_to_scrape.extend(additional_urls)

        # First, get the base page and find more amenity pages
        base_soup = self.scrape_url(base_url)
        if base_soup:
            discovered_urls = self.find_amenity_pages(base_url, base_soup)
            for url in discovered_urls[:5]:  # Limit to 5 additional pages
                if url not in urls_to_scrape:
                    urls_to_scrape.append(url)

        combined_amenities = {}
        combined_fees = None
        urls_scraped = []

        for url in urls_to_scrape:
            soup = self.scrape_url(url)
            if soup:
                urls_scraped.append(url)

                # Extract amenities
                amenities = self.extract_amenities(soup)

                # Merge with existing (taking max counts, OR for booleans)
                for key, value in amenities.items():
                    if key not in combined_amenities:
                        combined_amenities[key] = value
                    elif isinstance(value, int):
                        combined_amenities[key] = max(combined_amenities[key], value)
                    elif isinstance(value, bool):
                        combined_amenities[key] = combined_amenities[key] or value

                # Extract fees (take first found)
                if not combined_fees:
                    combined_fees = self.extract_hoa_fees(soup)

            time.sleep(self.request_delay)

        result = {
            'community': community_name,
            'amenities': combined_amenities,
            'fees': combined_fees,
            'source': 'public_website',
            'base_url': base_url,
            'urls_scraped': urls_scraped
        }

        return result


def scrape_multiple_communities(
    communities: List[Dict[str, str]],
    delay: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Scrape multiple communities.

    Args:
        communities: List of dicts with 'name' and 'url' keys
        delay: Delay between communities (seconds)

    Returns:
        List of scraping results
    """
    scraper = HOAAmenityScraper()
    results = []

    for i, comm in enumerate(communities):
        print(f"[{i+1}/{len(communities)}] Scraping {comm['name']}...")

        result = scraper.scrape_community(comm['name'], comm['url'])
        results.append(result)

        # Summary
        amenities = result.get('amenities', {})
        amenity_count = sum(1 for k, v in amenities.items() if v and k.startswith('has_'))
        print(f"  → Found {amenity_count} amenity types")

        if i < len(communities) - 1:
            time.sleep(delay)

    return results


if __name__ == "__main__":
    # Test with a known site
    print("Testing HOA Amenity Scraper")
    print("=" * 50)

    scraper = HOAAmenityScraper()
    result = scraper.scrape_community(
        "Test Community",
        "https://potomacstation.org"
    )

    print(f"\nAmenities found:")
    for k, v in result['amenities'].items():
        if v:
            print(f"  {k}: {v}")

    if result['fees']:
        print(f"\nFees: {result['fees']}")
