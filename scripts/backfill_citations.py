"""
Backfill citation counts for all saved papers using Serper Google Scholar.

Reads every paper JSON in data/pipeline/scholar_papers/, re-runs the Serper
citation lookup for papers with citations == "0", and updates both the JSON
file and the DB.

Usage:
    uv run scripts/backfill_citations.py
    uv run scripts/backfill_citations.py --limit 10   # test on first 10 files
"""

import argparse
import json
import time

import requests

from scholar_board.config import PAPERS_DIR, get_serper_api_key
from scholar_board.db import get_connection, init_db, upsert_papers

SERPER_SCHOLAR_URL = "https://google.serper.dev/scholar"


def lookup_citations(papers: list[dict], serper_key: str) -> list[dict]:
    """Look up citation counts from Google Scholar via Serper.dev."""
    for paper in papers:
        title = paper.get("title", "")
        if not title:
            continue
        try:
            resp = requests.post(
                SERPER_SCHOLAR_URL,
                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                json={"q": f"allintitle:{title}", "num": 1},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("organic", [])
            if results:
                paper["citations"] = str(results[0].get("citedBy", 0))
            else:
                paper["citations"] = "0"
            time.sleep(0.2)
        except Exception as e:
            print(f"      Serper error for '{title[:50]}': {e}")
            paper["citations"] = "0"
    return papers


def main():
    parser = argparse.ArgumentParser(description="Backfill citation counts via Serper")
    parser.add_argument("--limit", type=int, default=None, help="Max files to process")
    args = parser.parse_args()

    serper_key = get_serper_api_key()
    if not serper_key:
        print("Error: SERPER_API_KEY not set in .env")
        return

    files = sorted(PAPERS_DIR.glob("*.json"))
    if args.limit:
        files = files[: args.limit]

    print(f"Processing {len(files)} paper files...\n")

    updated_count = 0
    skipped_count = 0

    for fpath in files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  Skip {fpath.name}: {e}")
            continue

        papers = data.get("papers", [])
        if not papers:
            skipped_count += 1
            continue

        # Only process papers with citations == "0" or missing
        papers_to_update = [
            p for p in papers if not p.get("citations") or p.get("citations") == "0"
        ]
        if not papers_to_update:
            skipped_count += 1
            continue

        scholar_id = data.get("scholar_id", fpath.stem.split("_")[0])
        scholar_name = data.get("scholar_name", "")
        print(f"  {scholar_name} ({scholar_id}) — {len(papers_to_update)}/{len(papers)} papers to look up")

        # Re-run lookup only on the zero-citation papers (update in-place)
        lookup_citations(papers_to_update, serper_key)

        # Show results
        for p in papers_to_update:
            cites = p.get("citations", "0")
            if cites != "0":
                print(f"    ✓ {p['title'][:60]} → {cites} cites")

        # Save updated JSON
        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Update DB
        conn = get_connection()
        init_db(conn)
        upsert_papers(conn, scholar_id, papers)
        conn.close()

        updated_count += 1

    print(f"\n--- Done ---")
    print(f"Updated: {updated_count} files")
    print(f"Skipped: {skipped_count} files (no papers or all citations already non-zero)")


if __name__ == "__main__":
    main()
