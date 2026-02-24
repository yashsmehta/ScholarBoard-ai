import argparse
import pandas as pd
from typing import List, Dict, Optional
from scholarly import scholarly
from urllib.parse import urlparse, parse_qs
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from ratelimit import limits, sleep_and_retry
import requests_cache
import logging
from tqdm import tqdm
import threading
from contextlib import contextmanager
import sys

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
scholarly.logger.setLevel(logging.WARNING)

# Constants
DEFAULT_PAPER_LIMIT = 5
MAX_WORKERS = 2
CALLS_PER_MINUTE = 15
CACHE_EXPIRE_AFTER = 3600 * 24 * 7
MAX_RETRIES = 7
RETRY_DELAY = 5
MAX_CONCURRENT_REQUESTS = 2

class RobustScholarScraper:
    def __init__(self):
        self.setup_optimized_settings()
        self._print_lock = threading.Lock()
        self._request_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._progress_lock = threading.Lock()
        self._current_position = 0
        self._setup_caching()
        self._setup_session()

    def _setup_caching(self):
        """Setup caching with optimized settings"""
        requests_cache.install_cache(
            'scholar_cache',
            expire_after=CACHE_EXPIRE_AFTER,
            allowable_methods=('GET', 'POST'),
            backend='sqlite',
            cache_control=True
        )

    def _setup_session(self):
        """Setup scholarly session with optimized headers"""
        if hasattr(scholarly, '_SESSION'):
            scholarly._SESSION.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })

    @sleep_and_retry
    @limits(calls=CALLS_PER_MINUTE, period=60)
    def _rate_limited_fill(self, pub) -> Optional[Dict]:
        """Rate-limited version of scholarly.fill with robust error handling"""
        for attempt in range(MAX_RETRIES):
            try:
                time.sleep(random.uniform(3, 7))
                result = scholarly.fill(pub)
                if result:
                    return result
            except Exception as e:
                delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)

        return None

    def process_publication(self, pub, author_name: str) -> Dict:
        """Process a single publication with robust error handling"""
        with self._request_semaphore:
            try:
                pub_filled = self._rate_limited_fill(pub)
                if not pub_filled:
                    return self._create_fallback_paper_data(pub, author_name)

                bib = pub_filled.get('bib', {})
                author_str = bib.get('author', '')
                authors = self.parse_authors(author_str) if isinstance(author_str, str) else author_str

                return {
                    'researcher': author_name,
                    'title': bib.get('title', ''),
                    'citations': pub_filled.get('num_citations', 0),
                    'year': bib.get('pub_year', ''),
                    'authors': ', '.join(authors) if isinstance(authors, list) else authors,
                    'first_author': authors[0] if authors else '',
                    'last_author': authors[-1] if authors else '',
                    'author_count': len(authors) if isinstance(authors, list) else 0,
                    'venue': bib.get('venue', '') or bib.get('journal', '') or bib.get('conference', ''),
                    'abstract': bib.get('abstract', ''),
                    'url': pub_filled.get('pub_url', '')
                }
            except Exception as e:
                logger.warning(f"Failed to process paper: {str(e)}")
                return self._create_fallback_paper_data(pub, author_name)

    def scrape_scholar_page(self, profile_url: str, paper_limit: int = DEFAULT_PAPER_LIMIT, year_limit: int = None) -> List[Dict]:
        """Scrape publications from a Google Scholar profile"""
        position = self.get_next_position()

        try:
            for attempt in range(MAX_RETRIES):
                try:
                    author = scholarly.search_author_id(self.extract_user_id(profile_url))
                    if not author:
                        raise Exception("Author not found")
                    author = scholarly.fill(author)
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        raise
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)

            author_name = author.get('name', 'Unknown')
            publications = author.get('publications', [])

            # Sort by year descending to get most recent first
            publications.sort(
                key=lambda p: int(p.get('bib', {}).get('pub_year', 0) or 0),
                reverse=True
            )

            if year_limit:
                publications = [
                    pub for pub in publications
                    if int(pub.get('bib', {}).get('pub_year', 0) or 0) >= year_limit
                ]
            publications = publications[:paper_limit]

            with self._print_lock:
                print(f"\n  Processing {author_name}'s publications...")
                print(f"   Fetching top {len(publications)} most recent papers")

            papers = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [
                    executor.submit(self.process_publication, pub, author_name)
                    for pub in publications
                ]

                with tqdm(
                    total=len(publications),
                    desc="   Fetching paper details",
                    position=position,
                    leave=True,
                    dynamic_ncols=True,
                    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                ) as pbar:

                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                papers.append(result)
                        except Exception as e:
                            logger.warning(f"Failed to process paper: {str(e)}")
                        finally:
                            pbar.update(1)

            with self._print_lock:
                sys.stdout.write("\033[K")
                print(f"  Done: {author_name} - {len(papers)} papers\n", flush=True)

            return papers

        except Exception as e:
            with self._print_lock:
                sys.stdout.write("\033[K")
                print(f"  Failed {profile_url}: {str(e)}\n", flush=True)
            return []

        finally:
            self.release_position(position)

    def setup_optimized_settings(self):
        """Set up optimized settings for faster scraping."""
        scholarly.set_timeout(30)
        scholarly.set_retries(MAX_RETRIES)

    def extract_user_id(self, profile_url: str) -> str:
        """Extract user ID from Google Scholar URL."""
        parsed = urlparse(profile_url)
        params = parse_qs(parsed.query)
        return params.get('user', [None])[0]

    def parse_authors(self, author_str: str) -> List[str]:
        """Parse author string into list of individual authors."""
        if not author_str:
            return []
        return [author.strip() for author in author_str.split(" and ")]

    def _create_fallback_paper_data(self, pub, author_name: str) -> Dict:
        """Create fallback paper data when full details cannot be fetched"""
        bib = pub.get('bib', {})
        return {
            'researcher': author_name,
            'title': bib.get('title', 'Unknown Title'),
            'year': bib.get('pub_year', ''),
            'venue': '',
            'citations': pub.get('num_citations', 0),
            'abstract': '',
            'url': '',
            'authors': '',
            'first_author': '',
            'last_author': '',
            'author_count': 0
        }

    def get_next_position(self):
        with self._progress_lock:
            pos = self._current_position
            self._current_position += 1
            return pos

    def release_position(self, pos):
        with self._progress_lock:
            if pos == self._current_position - 1:
                self._current_position -= 1
