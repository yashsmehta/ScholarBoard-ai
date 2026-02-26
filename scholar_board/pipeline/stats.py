"""
Fetch per-PI citation stats (total citations, h-index) from Google Scholar profiles.

Uses Serper.dev to find each PI's Google Scholar author profile URL, then fetches
the profile page to extract total citations and h-index directly from the profile.

This is a single HTTP request per researcher — much more accurate than summing
citations across a handful of papers.

Usage:
    uv run -m scholar_board.pipeline.stats
    uv run -m scholar_board.pipeline.stats --limit 10
    uv run -m scholar_board.pipeline.stats --scholar-id E013
    uv run -m scholar_board.pipeline.stats --scholar-name "Michael Bonner"
    uv run -m scholar_board.pipeline.stats --no-skip
    uv run -m scholar_board.pipeline.stats --workers 5
"""

import argparse
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from scholar_board.config import get_serper_api_key
from scholar_board.db import get_connection, init_db, load_scholars, upsert_scholar_stats

SERPER_SEARCH_URL = "https://google.serper.dev/search"

# Mimic a real browser to avoid Google Scholar blocking
SCHOLAR_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _scholar_profile_from_results(organic: list, name: str) -> tuple[str | None, int | None]:
    """Extract a matching Google Scholar author profile URL from Serper organic results.

    Only accepts results whose URL is a scholar.google.com/citations?user=... profile
    AND whose TITLE contains the scholar's last name (title = "Name - Google Scholar").
    Snippet is NOT used for name validation — snippets often contain other people's names.

    Returns (profile_url, total_citations_from_snippet).
    """
    last_name = name.split()[-1].lower()
    for result in organic:
        url = result.get("link", "")
        if "scholar.google.com/citations" not in url or "user=" not in url:
            continue
        title = result.get("title", "").lower()
        # Title of a GS profile is always "Firstname Lastname - Google Scholar"
        if last_name not in title:
            continue
        snippet = result.get("snippet", "")
        cited_by = None
        m = re.search(r"[Cc]ited by ([\d,]+)", snippet)
        if m:
            cited_by = int(m.group(1).replace(",", ""))
        return url, cited_by
    return None, None


def find_scholar_profile(name: str, institution: str, serper_key: str) -> tuple[str | None, int | None]:
    """Search Serper for the Google Scholar author profile URL and total citations.

    Tries queries in order from most to least specific:
      1. Name + institution (unquoted — avoids over-restrictive matching)
      2. Name + "google scholar" only

    Returns (profile_url, total_citations_from_snippet).
    total_citations_from_snippet may be None if not in the snippet.
    """
    # Build institution shortname (first 2 words, e.g. "Johns Hopkins University" → "Johns Hopkins")
    inst_short = " ".join(institution.split()[:2]) if institution else ""
    queries = [
        # Unquoted name is more flexible — finds profiles even when Google uses alternate name forms
        f"{name} {inst_short} google scholar",
        f"{name} google scholar profile citations",
    ]
    for query in queries:
        try:
            resp = requests.post(
                SERPER_SEARCH_URL,
                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                json={"q": query, "num": 5},
                timeout=15,
            )
            resp.raise_for_status()
            organic = resp.json().get("organic", [])
            url, cited_by = _scholar_profile_from_results(organic, name)
            if url:
                return url, cited_by
        except Exception as e:
            print(f"    Serper search error for {name}: {e}")
            break

    return None, None


def fetch_stats_from_profile_page(profile_url: str, expected_last_name: str = "") -> tuple[int | None, int | None]:
    """Fetch total_citations and h_index directly from a Google Scholar profile page.

    Parses the stats table (id='gsc_rsb_st') which is in the initial HTML response.
    Validates that the page is for the expected researcher (name check).
    Returns (total_citations, h_index), either may be None if parsing fails.
    """
    try:
        resp = requests.get(
            profile_url,
            headers=SCHOLAR_PAGE_HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        html = resp.text

        # Validate this is the right person's profile
        if expected_last_name:
            name_m = re.search(r'id="gsc_prf_in"[^>]*>([^<]+)<', html)
            if name_m:
                page_name = name_m.group(1).strip().lower()
                if expected_last_name.lower() not in page_name:
                    print(f"    Profile page name mismatch: expected '{expected_last_name}', got '{page_name}'")
                    return None, None

        # The stats table contains 6 cells (3 rows × 2 columns: all-time + since YYYY)
        # Order: citations_all, citations_recent, h_all, h_recent, i10_all, i10_recent
        cells = re.findall(r'class="gsc_rsb_std"[^>]*>([\d,]+)<', html)
        if len(cells) >= 3:
            total_citations = int(cells[0].replace(",", ""))
            h_index = int(cells[2].replace(",", ""))
            return total_citations, h_index

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in (403, 429):
            print(f"    Google Scholar blocked page fetch (HTTP {e.response.status_code})")
        else:
            print(f"    HTTP error fetching profile page: {e}")
    except Exception as e:
        print(f"    Failed to parse profile page {profile_url}: {e}")

    return None, None


def get_scholars_without_stats(is_pi_only: bool = True) -> list[dict]:
    """Return scholars that have no total_citations yet."""
    conn = get_connection()
    init_db(conn)
    query = "SELECT id, name, institution FROM scholars WHERE total_citations IS NULL"
    if is_pi_only:
        query += " AND is_pi = 1"
    rows = conn.execute(query + " ORDER BY id").fetchall()
    conn.close()
    return [
        {
            "scholar_id": r["id"],
            "scholar_name": r["name"],
            "scholar_institution": r["institution"] or "",
        }
        for r in rows
    ]


def _process_scholar(
    researcher: dict,
    index: int,
    total: int,
    serper_key: str,
    page_delay: float,
    counters_lock: threading.Lock,
    counters: dict,
) -> None:
    """Look up citation stats for one scholar."""
    name = researcher["scholar_name"]
    sid = researcher["scholar_id"]
    inst = researcher["scholar_institution"]

    with counters_lock:
        print(f"[{index + 1}/{total}] {name} ({sid})")

    # Step 1: find profile URL via Serper search
    profile_url, snippet_citations = find_scholar_profile(name, inst, serper_key)

    if not profile_url:
        with counters_lock:
            counters["not_found"] += 1
            print(f"    No Google Scholar profile found")
        return

    # Step 2: fetch the actual profile page for accurate stats
    last_name = name.split()[-1]
    time.sleep(page_delay)
    total_citations, h_index = fetch_stats_from_profile_page(profile_url, last_name)

    # Fallback: use snippet citation count if page fetch didn't work
    if total_citations is None and snippet_citations is not None:
        total_citations = snippet_citations

    # Step 3: save to DB
    conn = get_connection()
    init_db(conn)
    upsert_scholar_stats(conn, sid, total_citations, h_index, profile_url)
    conn.close()

    with counters_lock:
        if total_citations is not None or h_index is not None:
            counters["success"] += 1
            cites_str = f"{total_citations:,}" if total_citations is not None else "?"
            h_str = str(h_index) if h_index is not None else "?"
            print(f"    Cited by {cites_str}, h-index {h_str}")
        else:
            counters["no_stats"] += 1
            print(f"    Profile found but stats not parseable: {profile_url}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch per-PI citation stats from Google Scholar profiles via Serper"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of researchers to process")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process only a specific scholar by ID")
    parser.add_argument("--scholar-name", type=str, default=None,
                        help="Process only a specific scholar by name")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-fetch even for scholars that already have stats")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed without making API calls")
    parser.add_argument("--workers", type=int, default=3,
                        help="Number of parallel workers (default: 3 — be polite to Google Scholar)")
    parser.add_argument("--page-delay", type=float, default=2.0,
                        help="Seconds to wait before fetching each profile page (default: 2.0)")
    parser.add_argument("--all-scholars", action="store_true",
                        help="Process all scholars, not just confirmed PIs")
    args = parser.parse_args()

    serper_key = get_serper_api_key()
    if not serper_key:
        print("Error: SERPER_API_KEY not set in .env")
        sys.exit(1)

    if args.no_skip:
        # Load all scholars (or all PIs)
        researchers = load_scholars(is_pi_only=not args.all_scholars)
        print(f"Loaded {len(researchers)} researchers from DB")
    else:
        researchers = get_scholars_without_stats(is_pi_only=not args.all_scholars)
        print(f"Found {len(researchers)} researchers without citation stats")

    if args.scholar_id:
        researchers = [r for r in researchers if r["scholar_id"] == args.scholar_id]
        if not researchers:
            print(f"Scholar ID {args.scholar_id} not found (or already has stats)")
            sys.exit(1)
    elif args.scholar_name:
        researchers = [
            r for r in researchers
            if args.scholar_name.lower() in r["scholar_name"].lower()
        ]
        if not researchers:
            print(f"No scholars matching '{args.scholar_name}' (or all already have stats)")
            sys.exit(1)

    if args.limit:
        researchers = researchers[: args.limit]

    total = len(researchers)
    print(f"Processing {total} researchers\n")

    if not researchers:
        print("Nothing to do!")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would process {total} researchers:")
        for i, r in enumerate(researchers):
            print(f"  [{i + 1}] {r['scholar_name']} ({r['scholar_id']}) — {r['scholar_institution']}")
        print("\nNo API calls made.")
        return

    counters_lock = threading.Lock()
    counters = {"success": 0, "not_found": 0, "no_stats": 0}

    if args.workers <= 1:
        for i, r in enumerate(researchers):
            _process_scholar(r, i, total, serper_key, args.page_delay, counters_lock, counters)
    else:
        print(f"Using {args.workers} parallel workers\n")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    _process_scholar, r, i, total, serper_key,
                    args.page_delay, counters_lock, counters
                ): r
                for i, r in enumerate(researchers)
            }
            for future in as_completed(futures):
                exc = future.exception()
                if exc is not None:
                    scholar = futures[future]
                    print(f"    Unexpected error for {scholar['scholar_name']}: {exc}")

    total_processed = counters["success"] + counters["not_found"] + counters["no_stats"]
    print(f"\n--- Summary ---")
    print(f"Stats fetched:     {counters['success']}/{total_processed}")
    print(f"Profile not found: {counters['not_found']}/{total_processed}")
    print(f"Page unparseable:  {counters['no_stats']}/{total_processed}")


if __name__ == "__main__":
    main()
