"""
Fetch recent papers for ScholarBoard researchers using Semantic Scholar API.

Free, no auth required, returns verified paper data with titles, abstracts,
citations, venues, and authors. No CAPTCHA issues.

Disambiguation strategy: search by name, pick the author with the highest
paper count (most likely to be the established researcher at VSS).

Usage:
    python3 scripts/scholar_scraper/fetch_papers_semantic_scholar.py
    python3 scripts/scholar_scraper/fetch_papers_semantic_scholar.py --limit 10 --papers 5
    python3 scripts/scholar_scraper/fetch_papers_semantic_scholar.py --scholar-id 0005
    python3 scripts/scholar_scraper/fetch_papers_semantic_scholar.py --scholar-name "Aaron Seitz"
"""

import json
import os
import re
import time
import argparse
import sys
from pathlib import Path

import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "scholar_papers"

S2_BASE = "https://api.semanticscholar.org/graph/v1"

# Optional: set SEMANTIC_SCHOLAR_API_KEY in .env for higher rate limits
# Free tier: 100 requests/5 min. With key: 1 request/sec.
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")


def s2_headers():
    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY
    return headers


def search_author(name, max_results=10):
    """Search Semantic Scholar for an author by name."""
    r = requests.get(
        f"{S2_BASE}/author/search",
        params={"query": name, "fields": "name,affiliations,paperCount,hIndex", "limit": max_results},
        headers=s2_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def disambiguate_author(candidates, target_name, target_institution=None):
    """
    Pick the best matching author from candidates.
    Strategy: prefer highest paper count (established researchers at VSS).
    If institution is available, boost candidates whose affiliations match.
    """
    if not candidates:
        return None

    target_lower = target_name.lower().strip()
    target_parts = set(target_lower.replace(".", "").split())

    scored = []
    for c in candidates:
        score = 0
        cname = c.get("name", "").lower().strip()
        cparts = set(cname.replace(".", "").split())

        # Name overlap
        overlap = len(target_parts & cparts)
        score += overlap * 10

        # Paper count (log scale to not over-weight)
        pc = c.get("paperCount", 0) or 0
        if pc > 0:
            import math
            score += math.log(pc + 1) * 5

        # h-index
        hi = c.get("hIndex", 0) or 0
        score += hi * 0.5

        # Affiliation match
        if target_institution:
            inst_lower = target_institution.lower()
            for aff in c.get("affiliations", []):
                if any(word in aff.lower() for word in inst_lower.split() if len(word) > 3):
                    score += 20
                    break

        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None


def get_author_papers(author_id, limit=5):
    """Fetch most recent papers for an author."""
    r = requests.get(
        f"{S2_BASE}/author/{author_id}/papers",
        params={
            "fields": "title,abstract,year,citationCount,venue,authors,url,externalIds",
            "limit": limit,
            "sort": "year:desc",
        },
        headers=s2_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def format_paper(paper):
    """Format a Semantic Scholar paper into our standard format."""
    authors = [a.get("name", "") for a in paper.get("authors", [])]
    return {
        "title": paper.get("title", ""),
        "abstract": paper.get("abstract", "") or "",
        "year": str(paper.get("year", "")),
        "citations": paper.get("citationCount", 0),
        "venue": paper.get("venue", ""),
        "authors": ", ".join(authors),
        "first_author": authors[0] if authors else "",
        "last_author": authors[-1] if authors else "",
        "author_count": len(authors),
        "url": paper.get("url", ""),
        "doi": (paper.get("externalIds") or {}).get("DOI", ""),
    }


def fetch_scholar_papers(name, institution=None, num_papers=5):
    """
    Full pipeline: search author, disambiguate, fetch papers.
    Returns (papers_list, s2_author_id) or (None, None).
    """
    candidates = search_author(name)

    if not candidates:
        return None, None

    best = disambiguate_author(candidates, name, institution)
    if not best:
        return None, None

    author_id = best["authorId"]
    raw_papers = get_author_papers(author_id, limit=num_papers)
    papers = [format_paper(p) for p in raw_papers]

    return papers, author_id


def load_researchers(csv_path):
    """Load unique researchers from vss_data.csv."""
    df = pd.read_csv(csv_path)
    unique = df.drop_duplicates(subset="scholar_id")[
        ["scholar_id", "scholar_name", "scholar_institution"]
    ].copy()
    unique["scholar_id"] = unique["scholar_id"].astype(str).str.zfill(4)
    return unique.to_dict("records")


def get_already_fetched(output_dir):
    """Get set of scholar_ids that already have paper data."""
    fetched = set()
    if not output_dir.exists():
        return fetched
    for fname in output_dir.iterdir():
        if fname.suffix == ".json":
            fetched.add(fname.stem.split("_")[0])
    return fetched


def save_papers(papers, s2_author_id, scholar_id, scholar_name, output_dir):
    """Save fetched papers for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", scholar_name).strip().replace(" ", "_")
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "s2_author_id": s2_author_id,
        "papers": papers,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Fetch recent papers via Semantic Scholar API"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max researchers to process")
    parser.add_argument("--papers", type=int, default=5,
                        help="Papers per researcher (default: 5)")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process specific scholar by ID")
    parser.add_argument("--scholar-name", type=str, default=None,
                        help="Process specific scholar by name")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-fetch even if data exists")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls (default: 1.0s)")
    args = parser.parse_args()

    csv_path = PROJECT_ROOT / "data" / "vss_data.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    researchers = load_researchers(csv_path)
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

    # Filter
    if args.scholar_id:
        researchers = [r for r in researchers if r["scholar_id"] == args.scholar_id.zfill(4)]
    elif args.scholar_name:
        researchers = [r for r in researchers
                       if args.scholar_name.lower() in r["scholar_name"].lower()]

    if not researchers:
        print("No matching scholars found")
        sys.exit(1)

    # Skip existing
    if not args.no_skip:
        already = get_already_fetched(OUTPUT_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r["scholar_id"] not in already]
        if before != len(researchers):
            print(f"Skipping {before - len(researchers)} already-fetched scholars")

    if args.limit:
        researchers = researchers[: args.limit]

    print(f"Processing {len(researchers)} researchers, {args.papers} papers each\n")

    if not researchers:
        print("Nothing to do!")
        return

    success = 0
    fail = 0
    total_papers = 0

    for i, r in enumerate(researchers):
        name = r["scholar_name"]
        sid = r["scholar_id"]
        inst = r["scholar_institution"]

        print(f"[{i+1}/{len(researchers)}] {name} ({sid}) — {inst}")

        try:
            papers, s2_id = fetch_scholar_papers(name, inst, args.papers)

            if papers:
                save_papers(papers, s2_id, sid, name, OUTPUT_DIR)
                total_papers += len(papers)
                success += 1
                papers_with_abstract = sum(1 for p in papers if p.get("abstract"))
                print(f"    {len(papers)} papers ({papers_with_abstract} with abstracts), S2 id={s2_id}")
                for p in papers:
                    print(f"      - [{p['year']}] {p['title'][:75]}")
            else:
                fail += 1
                print(f"    Not found on Semantic Scholar")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"    Rate limited — waiting 60s...")
                time.sleep(60)
                # Retry once
                try:
                    papers, s2_id = fetch_scholar_papers(name, inst, args.papers)
                    if papers:
                        save_papers(papers, s2_id, sid, name, OUTPUT_DIR)
                        total_papers += len(papers)
                        success += 1
                        print(f"    {len(papers)} papers (retry)")
                    else:
                        fail += 1
                except Exception:
                    fail += 1
                    print(f"    Failed on retry")
            else:
                fail += 1
                print(f"    HTTP error: {e}")
        except Exception as e:
            fail += 1
            print(f"    Error: {e}")

        if i < len(researchers) - 1:
            time.sleep(args.delay)

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    print(f"Total papers: {total_papers}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
