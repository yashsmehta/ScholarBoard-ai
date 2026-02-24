"""
Fetch recent papers for ScholarBoard researchers using Perplexity API.

Uses Perplexity's sonar-pro model with academic search mode to find
the most recent papers for each researcher. Returns title, abstract,
citations, and year.

Usage:
    python3 scripts/scholar_scraper/fetch_papers_perplexity.py
    python3 scripts/scholar_scraper/fetch_papers_perplexity.py --limit 5 --papers 5
    python3 scripts/scholar_scraper/fetch_papers_perplexity.py --scholar-id 0005
    python3 scripts/scholar_scraper/fetch_papers_perplexity.py --scholar-name "Aaron Seitz"
"""

import json
import os
import re
import time
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from scholar_board.prompt_loader import render_prompt

API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    print("Error: PERPLEXITY_API_KEY not found in .env")
    sys.exit(1)

OUTPUT_DIR = PROJECT_ROOT / "data" / "scholar_papers"

# JSON schema for structured output
PAPERS_SCHEMA = {
    "type": "object",
    "properties": {
        "scholar_name": {"type": "string"},
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "abstract": {"type": "string"},
                    "year": {"type": "string"},
                    "citations": {"type": "string"},
                    "venue": {"type": "string"},
                    "authors": {"type": "string"},
                    "last_author": {"type": "string"},
                    "url": {"type": "string"}
                },
                "required": ["title", "abstract", "year"]
            }
        }
    },
    "required": ["scholar_name", "papers"]
}


def fetch_papers(client, scholar_name, institution, num_papers=5):
    """
    Fetch recent papers for a scholar using Perplexity API.
    Uses academic search mode for better paper discovery.
    """
    prompt = render_prompt(
        "fetch_papers",
        scholar_name=scholar_name,
        institution=institution,
        num_papers=num_papers,
    )

    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research paper database. Return accurate, verified paper information. Only include papers you are confident exist. Return results as structured JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": PAPERS_SCHEMA
                }
            },
            extra_body={
                "search_mode": "academic",
                "web_search_options": {
                    "search_context_size": "high"
                }
            }
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Extract citations from response if available
        citations = []
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations

        return result, citations

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        # Try to extract JSON from the response
        content = response.choices[0].message.content
        # Try to find JSON in the response
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return result, []
            except json.JSONDecodeError:
                pass
        return None, []
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, []


def load_researchers(csv_path):
    """Load unique researchers from vss_data.csv."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    unique = df.drop_duplicates(subset='scholar_id')[
        ['scholar_id', 'scholar_name', 'scholar_institution']
    ].copy()
    unique['scholar_id'] = unique['scholar_id'].astype(str).str.zfill(4)
    return unique.to_dict('records')


def get_already_fetched(output_dir):
    """Get set of scholar_ids that already have paper data."""
    fetched = set()
    if not output_dir.exists():
        return fetched
    for fname in output_dir.iterdir():
        if fname.suffix == '.json':
            fetched.add(fname.stem.split('_')[0])
    return fetched


def save_papers(data, citations, scholar_id, scholar_name, output_dir):
    """Save fetched papers for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "papers": data.get("papers", []),
        "source_citations": citations
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Fetch recent papers for ScholarBoard researchers via Perplexity API'
    )
    parser.add_argument('--limit', type=int, default=None,
                        help='Max number of researchers to process')
    parser.add_argument('--papers', type=int, default=5,
                        help='Number of recent papers to fetch per researcher (default: 5)')
    parser.add_argument('--scholar-id', type=str, default=None,
                        help='Process only a specific scholar by ID')
    parser.add_argument('--scholar-name', type=str, default=None,
                        help='Process only a specific scholar by name')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-fetch even if data already exists')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be fetched without making API calls')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay between API calls in seconds (default: 2.0)')
    args = parser.parse_args()

    csv_path = PROJECT_ROOT / "data" / "vss_data.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    # Load researchers
    researchers = load_researchers(csv_path)
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

    # Filter by specific scholar
    if args.scholar_id:
        researchers = [r for r in researchers if r['scholar_id'] == args.scholar_id.zfill(4)]
        if not researchers:
            print(f"Scholar ID {args.scholar_id} not found")
            sys.exit(1)
    elif args.scholar_name:
        researchers = [r for r in researchers
                       if args.scholar_name.lower() in r['scholar_name'].lower()]
        if not researchers:
            print(f"No scholars matching '{args.scholar_name}'")
            sys.exit(1)

    # Skip already fetched
    if not args.no_skip:
        already = get_already_fetched(OUTPUT_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r['scholar_id'] not in already]
        if before != len(researchers):
            print(f"Skipping {before - len(researchers)} already-fetched scholars")

    # Apply limit
    if args.limit:
        researchers = researchers[:args.limit]

    print(f"Processing {len(researchers)} researchers, {args.papers} papers each\n")

    if not researchers:
        print("Nothing to do!")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would process {len(researchers)} researchers:")
        for i, r in enumerate(researchers):
            print(f"  [{i+1}] {r['scholar_name']} ({r['scholar_id']}) — {r['scholar_institution']}")
        print(f"\nNo API calls made.")
        return

    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

    success = 0
    fail = 0
    total_papers = 0

    for i, r in enumerate(researchers):
        name = r['scholar_name']
        sid = r['scholar_id']
        inst = r['scholar_institution']

        print(f"[{i+1}/{len(researchers)}] {name} ({sid}) — {inst}")

        data, citations = fetch_papers(client, name, inst, args.papers)

        if data and data.get("papers"):
            papers = data["papers"]
            save_papers(data, citations, sid, name, OUTPUT_DIR)
            total_papers += len(papers)
            success += 1
            print(f"    {len(papers)} papers saved")
            for p in papers:
                print(f"      - [{p.get('year', '?')}] {p.get('title', '?')[:80]}")
        else:
            fail += 1
            print(f"    No papers found")

        # Rate limiting
        if i < len(researchers) - 1:
            time.sleep(args.delay)

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    print(f"Total papers: {total_papers}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
