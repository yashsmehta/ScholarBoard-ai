#!/usr/bin/env python3
"""Fetch total citations and h-index for scholars via Serper Google Search.

Uses Google Scholar profile snippets from Serper.dev search results
to extract total citation counts and h-index for each scholar.

Saves results to data/scholar_citations.csv.

Usage:
    .venv/bin/python3 scripts/fetch_scholar_citations.py
    .venv/bin/python3 scripts/fetch_scholar_citations.py --limit 10
    .venv/bin/python3 scripts/fetch_scholar_citations.py --dry-run
    .venv/bin/python3 scripts/fetch_scholar_citations.py --workers 8
"""

import argparse
import csv
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"
CSV_PATH = PROJECT_ROOT / "data" / "vss_data.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "scholar_citations.csv"


def load_scholars():
    """Load unique scholars from vss_data.csv."""
    seen = set()
    scholars = []
    with open(CSV_PATH) as f:
        for row in csv.DictReader(f):
            sid = row["scholar_id"]
            if sid not in seen:
                seen.add(sid)
                scholars.append({
                    "id": sid,
                    "name": row["scholar_name"],
                    "institution": row.get("scholar_institution", ""),
                })
    return scholars


def parse_scholar_stats(data):
    """Parse citations and h-index from Serper search response."""
    citations = None
    h_index = None

    # Check all organic results for Google Scholar profile snippets
    for r in data.get("organic", []):
        snippet = r.get("snippet", "")
        link = r.get("link", "")

        # Prefer results from scholar.google.com
        if "scholar.google" not in link:
            continue

        # Full format: "Citations, 2887, 1552. h-index, 24, 18"
        if citations is None:
            m = re.search(r"Citations,\s*([\d,]+)", snippet)
            if m:
                citations = int(m.group(1).replace(",", ""))

        if h_index is None:
            m = re.search(r"h-index,\s*(\d+)", snippet)
            if m:
                h_index = int(m.group(1))

        # Fallback: "Cited by 2887"
        if citations is None:
            m = re.search(r"Cited by ([\d,]+)", snippet)
            if m:
                citations = int(m.group(1).replace(",", ""))

        if citations is not None:
            break

    # Also check answer box
    ab = data.get("answerBox", {})
    ab_snippet = ab.get("snippet", "")
    if ab_snippet:
        if citations is None:
            m = re.search(r"Citations\s*\n?\s*([\d,]+)", ab_snippet)
            if m:
                citations = int(m.group(1).replace(",", ""))
        if h_index is None:
            m = re.search(r"h-index\s*\n?\s*(\d+)", ab_snippet)
            if m:
                h_index = int(m.group(1))

    return citations, h_index


def fetch_scholar_stats(name, institution, api_key):
    """Fetch citations and h-index for a scholar.

    Strategy:
    1. Query "{name} google scholar h-index" — gets both metrics.
    2. Fallback: "{name} {institution} google scholar profile" — gets citations.
    """
    queries = [
        f"{name} google scholar h-index",
        f"{name} {institution} google scholar profile",
    ]

    for query in queries:
        try:
            resp = requests.post(
                SERPER_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": 5},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            citations, h_index = parse_scholar_stats(data)

            if citations is not None:
                return citations, h_index
        except Exception:
            pass
        time.sleep(0.3)

    return None, None


def _process_scholar(scholar, index, total, api_key, lock, results, counters):
    """Process a single scholar in a worker thread."""
    name = scholar["name"]
    sid = scholar["id"]
    inst = scholar["institution"]

    citations, h_index = fetch_scholar_stats(name, inst, api_key)

    with lock:
        results.append({
            "scholar_id": sid,
            "scholar_name": name,
            "institution": inst,
            "total_citations": citations if citations is not None else "",
            "h_index": h_index if h_index is not None else "",
        })
        if citations is not None:
            counters["found"] += 1
            tag = f"citations={citations}"
            if h_index is not None:
                tag += f", h={h_index}"
                counters["h_found"] += 1
        else:
            counters["missing"] += 1
            tag = "NOT FOUND"
        print(f"[{index + 1}/{total}] {name:<35} {tag}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch total citations and h-index for scholars via Serper"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max scholars to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--workers", type=int, default=5,
                        help="Number of parallel workers (default: 5)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip scholars already in output CSV")
    args = parser.parse_args()

    if not SERPER_API_KEY:
        print("Error: SERPER_API_KEY not found in .env")
        sys.exit(1)

    scholars = load_scholars()
    print(f"Loaded {len(scholars)} unique scholars")

    # Skip existing
    existing_ids = set()
    if args.skip_existing and OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            for row in csv.DictReader(f):
                existing_ids.add(row["scholar_id"])
        if existing_ids:
            scholars = [s for s in scholars if s["id"] not in existing_ids]
            print(f"Skipping {len(existing_ids)} already-fetched scholars")

    if args.limit:
        scholars = scholars[:args.limit]

    print(f"Processing {len(scholars)} scholars with {args.workers} workers\n")

    if args.dry_run:
        for i, s in enumerate(scholars):
            print(f"  [{i+1}] {s['name']} — {s['institution']}")
        print(f"\n[DRY RUN] Would fetch stats for {len(scholars)} scholars")
        return

    lock = threading.Lock()
    results = []
    counters = {"found": 0, "missing": 0, "h_found": 0}
    total = len(scholars)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                _process_scholar, s, i, total, SERPER_API_KEY, lock, results, counters
            ): s
            for i, s in enumerate(scholars)
        }
        for future in as_completed(futures):
            exc = future.exception()
            if exc is not None:
                scholar = futures[future]
                print(f"  Unexpected error for {scholar['name']}: {exc}")

    # Sort results by scholar_id
    results.sort(key=lambda r: r["scholar_id"])

    # Merge with existing data if skip-existing was used
    if existing_ids and OUTPUT_PATH.exists():
        existing_rows = []
        with open(OUTPUT_PATH) as f:
            existing_rows = list(csv.DictReader(f))
        results = existing_rows + results
        results.sort(key=lambda r: r["scholar_id"])

    # Save results
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "scholar_id", "scholar_name", "institution", "total_citations", "h_index"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n--- Summary ---")
    print(f"Found:   {counters['found']}/{total}")
    print(f"Missing: {counters['missing']}/{total}")
    print(f"H-index: {counters['h_found']}/{total}")
    print(f"Output:  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
