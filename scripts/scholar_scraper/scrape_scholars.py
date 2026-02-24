"""
Scrape Google Scholar papers for ScholarBoard-ai researchers.

Reads researchers from data/vss_data.csv and fetches their most recent papers
(title, abstract, citations) from Google Scholar using the `scholarly` library.

Usage:
    python scripts/scholar_scraper/scrape_scholars.py
    python scripts/scholar_scraper/scrape_scholars.py --limit 10 --papers 5
    python scripts/scholar_scraper/scrape_scholars.py --scholar-id 0001
    python scripts/scholar_scraper/scrape_scholars.py --scholar-name "Aaron Seitz"
"""

import time
import os
import re
import json
import argparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd
import threading
import sys
import logging

from scholarly import scholarly

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from scripts.scholar_scraper.scraper_utils import RobustScholarScraper

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_DELAY = 5


def find_scholar_profile(researcher_name):
    """Search Google Scholar for a researcher's profile using scholarly library."""
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(random.uniform(2, 5))
            search_query = scholarly.search_author(researcher_name)
            author = next(search_query, None)

            if author:
                scholar_id = author.get('scholar_id', '')
                profile_url = f"https://scholar.google.com/citations?user={scholar_id}"
                return {
                    'name': researcher_name,
                    'profile': profile_url,
                    'user_id': scholar_id,
                    'found': True
                }

            return {'name': researcher_name, 'found': False}

        except StopIteration:
            return {'name': researcher_name, 'found': False}
        except Exception as e:
            delay = RETRY_DELAY * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} for {researcher_name}: {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)

    return {'name': researcher_name, 'found': False, 'error': 'Max retries exceeded'}


def process_researcher(scraper, researcher_name, scholar_id, paper_limit=5):
    """Process a single researcher: find profile, scrape papers."""
    try:
        profile_info = find_scholar_profile(researcher_name)

        if not profile_info.get('found'):
            print(f"  Could not find Google Scholar profile for {researcher_name} ({scholar_id})")
            return None

        papers = scraper.scrape_scholar_page(
            profile_url=profile_info['profile'],
            paper_limit=paper_limit
        )

        if papers:
            # Add scholar_id to each paper
            for paper in papers:
                paper['scholar_id'] = scholar_id

        return papers

    except Exception as e:
        print(f"  Error processing {researcher_name} ({scholar_id}): {str(e)}")
        return None


def load_researchers(csv_path):
    """Load unique researchers from vss_data.csv."""
    df = pd.read_csv(csv_path)
    # Get unique scholars by scholar_id
    unique = df.drop_duplicates(subset='scholar_id')[['scholar_id', 'scholar_name', 'scholar_institution']].copy()
    unique['scholar_id'] = unique['scholar_id'].astype(str).str.zfill(4)
    return unique.to_dict('records')


def get_already_scraped(output_dir):
    """Get set of scholar_ids that have already been scraped."""
    scraped = set()
    if not os.path.exists(output_dir):
        return scraped
    for fname in os.listdir(output_dir):
        if fname.endswith('.json'):
            # filename format: {scholar_id}_{scholar_name}.json
            scraped.add(fname.split('_')[0])
    return scraped


def save_scholar_papers(papers, scholar_id, scholar_name, output_dir):
    """Save papers for a single scholar as JSON."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filename = f"{scholar_id}_{safe_name}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'scholar_id': scholar_id,
            'scholar_name': scholar_name,
            'papers': papers
        }, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(description='Scrape Google Scholar papers for ScholarBoard researchers')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max number of researchers to process (default: all)')
    parser.add_argument('--papers', type=int, default=5,
                        help='Number of most recent papers to fetch per researcher (default: 5)')
    parser.add_argument('--workers', type=int, default=2,
                        help='Number of concurrent workers (default: 2, keep low to avoid rate limits)')
    parser.add_argument('--scholar-id', type=str, default=None,
                        help='Process only a specific scholar by ID (e.g., 0001)')
    parser.add_argument('--scholar-name', type=str, default=None,
                        help='Process only a specific scholar by name (e.g., "Aaron Seitz")')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='Skip scholars that already have scraped data (default: True)')
    args = parser.parse_args()

    csv_path = os.path.join(PROJECT_ROOT, 'data', 'vss_data.csv')
    output_dir = os.path.join(PROJECT_ROOT, 'data', 'scholar_papers')

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    # Load researchers
    researchers = load_researchers(csv_path)
    print(f"\nLoaded {len(researchers)} unique researchers from vss_data.csv")

    # Filter by specific scholar if requested
    if args.scholar_id:
        researchers = [r for r in researchers if r['scholar_id'] == args.scholar_id.zfill(4)]
        if not researchers:
            print(f"Scholar ID {args.scholar_id} not found")
            sys.exit(1)
    elif args.scholar_name:
        researchers = [r for r in researchers
                       if args.scholar_name.lower() in r['scholar_name'].lower()]
        if not researchers:
            print(f"No scholars matching '{args.scholar_name}' found")
            sys.exit(1)

    # Skip already scraped
    if args.skip_existing:
        already_scraped = get_already_scraped(output_dir)
        before = len(researchers)
        researchers = [r for r in researchers if r['scholar_id'] not in already_scraped]
        if before != len(researchers):
            print(f"Skipping {before - len(researchers)} already-scraped scholars")

    # Apply limit
    if args.limit:
        researchers = researchers[:args.limit]

    print(f"Processing {len(researchers)} researchers, fetching {args.papers} papers each\n")

    if not researchers:
        print("Nothing to do!")
        return

    # Initialize scraper
    scraper = RobustScholarScraper()
    print_lock = threading.Lock()

    success_count = 0
    fail_count = 0
    total_papers = 0

    # Process researchers (sequential to be safe with rate limits, or parallel with low workers)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_researcher, scraper,
                r['scholar_name'], r['scholar_id'], args.papers
            ): r for r in researchers
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Researchers"):
            researcher = futures[future]
            try:
                papers = future.result()
                with print_lock:
                    if papers:
                        save_scholar_papers(
                            papers,
                            researcher['scholar_id'],
                            researcher['scholar_name'],
                            output_dir
                        )
                        success_count += 1
                        total_papers += len(papers)
                        print(f"  {researcher['scholar_name']} ({researcher['scholar_id']}): "
                              f"{len(papers)} papers saved")
                    else:
                        fail_count += 1
                        print(f"  {researcher['scholar_name']} ({researcher['scholar_id']}): "
                              f"no papers found")
            except Exception as e:
                with print_lock:
                    fail_count += 1
                    print(f"  Failed {researcher['scholar_name']}: {str(e)}")

    print(f"\n--- Summary ---")
    print(f"Successful: {success_count}/{success_count + fail_count}")
    print(f"Failed:     {fail_count}/{success_count + fail_count}")
    print(f"Total papers saved: {total_papers}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
