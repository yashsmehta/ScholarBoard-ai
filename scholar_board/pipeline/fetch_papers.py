"""
Fetch recent papers for ScholarBoard researchers using Gemini grounded search.

Uses Gemini 3 Flash Preview with Google Search grounding to find
the most recent papers for each researcher. Citation counts are
fetched separately from Google Scholar via Serper.dev.

Supports parallel execution via --workers to speed up bulk fetches.

Usage:
    uv run -m scholar_board.pipeline.fetch_papers
    uv run -m scholar_board.pipeline.fetch_papers --limit 5 --papers 5
    uv run -m scholar_board.pipeline.fetch_papers --scholar-id 0005
    uv run -m scholar_board.pipeline.fetch_papers --scholar-name "Aaron Seitz"
    uv run -m scholar_board.pipeline.fetch_papers --workers 4 --limit 20
"""

import json
import re
import argparse
import sys
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.genai import types

from scholar_board.config import PAPERS_DIR
from scholar_board.gemini import get_client, extract_grounding_sources, parse_json_response
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_papers, load_scholars

SYSTEM_INSTRUCTION = (
    "You are a research paper database. Return accurate, verified paper information. "
    "Only include papers you are confident exist. Return results as structured JSON."
)


def build_prompt(scholar_name, institution, num_papers):
    """Build the grounded search prompt for paper fetching."""
    return (
        f"Search online for the {num_papers} most recent papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"STRICT REQUIREMENTS:\n"
        f"- {scholar_name} MUST be either the FIRST AUTHOR or the LAST AUTHOR on the paper. "
        f"Do NOT include papers where they are a middle author.\n"
        f"- Papers must be published in 2024 or later. Prioritize most recent first.\n"
        f"- Include: peer-reviewed journal articles, preprints (bioRxiv/arXiv), and full papers "
        f"at top-tier ML/vision/neuro conferences (NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, EMNLP, ACL, etc.)\n"
        f"- Do NOT include conference abstracts, posters, workshop papers, or short extended abstracts\n"
        f"- EXPLICITLY EXCLUDE: VSS abstracts, Journal of Vision (JOV) conference supplement abstracts, "
        f"CCN extended abstracts, COSYNE abstracts, SfN abstracts, OHBM abstracts\n"
        f"- Do NOT make up or hallucinate any papers. Only include papers you can verify.\n\n"
        f"Use Google Search to find real papers. Check Google Scholar, PubMed, bioRxiv, arXiv, "
        f"and the researcher's lab website.\n\n"
        f"For each paper, provide:\n"
        f"- title: exact paper title\n"
        f"- abstract: Write a technical, domain-expert paraphrase of the paper's abstract. "
        f"Use the same level of specialized terminology and jargon as the original — do NOT "
        f"simplify for a general audience. Preserve all specific methods, model names, brain "
        f"regions, metrics, and quantitative findings. Closely rephrase without copying verbatim.\n"
        f"- year: publication year\n"
        f"- venue: journal or conference name\n"
        f"- authors: full author list as a comma-separated string\n"
        f"- url: DOI or paper URL if available\n\n"
        f"Return a JSON object with keys \"scholar_name\" (string) and \"papers\" (array of paper objects). "
        f"If you searched thoroughly and found NO qualifying papers for this researcher, return "
        f"{{\"scholar_name\": \"{scholar_name}\", \"papers\": [], \"not_found\": true}} — "
        f"do NOT invent papers just to fill the list. "
        f"Return ONLY the JSON, no other text."
    )


def _normalize_papers_result(parsed, scholar_name):
    """Normalize the structure of a parsed Gemini papers response."""
    if isinstance(parsed, list):
        return {"scholar_name": scholar_name, "papers": parsed}
    elif isinstance(parsed, dict) and "papers" not in parsed:
        return {"scholar_name": scholar_name, "papers": [parsed]}
    return parsed


def fetch_papers(client, scholar_name, institution, num_papers=5):
    """Fetch recent papers for a scholar using Gemini grounded search.

    Returns (data, sources, status) where status is one of:
      "success"   — papers found and returned
      "not_found" — Gemini searched but found no qualifying papers
      "api_error" — transient failure (network, timeout, parse error, etc.)
    """
    prompt = build_prompt(scholar_name, institution, num_papers)

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        if response.text is None:
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            print(f"    Empty response (finish_reason={finish_reason})")

            if str(finish_reason) == "RECITATION":
                print(f"    Retrying with softer abstract prompt...")
                return _retry_without_abstract(client, scholar_name, institution, num_papers)

            return None, [], "api_error"

        parsed = parse_json_response(response.text)
        result = _normalize_papers_result(parsed, scholar_name)
        sources = extract_grounding_sources(response)

        if result.get("not_found") or not result.get("papers"):
            return result, sources, "not_found"

        return result, sources, "success"

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        return None, [], "api_error"
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, [], "api_error"


def _retry_without_abstract(client, scholar_name, institution, num_papers):
    """Retry paper fetch with a prompt that skips abstracts to avoid RECITATION."""
    prompt = (
        f"Search online for the {num_papers} most recent peer-reviewed journal papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"REQUIREMENTS:\n"
        f"- {scholar_name} MUST be either the FIRST AUTHOR or the LAST AUTHOR\n"
        f"- Published in 2024 or later, most recent first\n"
        f"- Full journal articles, preprints, or top-tier conference papers only\n"
        f"- EXCLUDE: VSS abstracts, JOV conference abstracts, CCN, COSYNE, SfN, OHBM abstracts\n"
        f"- Only verified papers\n\n"
        f"For each paper provide: title, year, venue, authors, url.\n"
        f"Set abstract to an empty string.\n\n"
        f"Return a JSON object with keys \"scholar_name\" and \"papers\" array. "
        f"If no qualifying papers found, return {{\"scholar_name\": \"{scholar_name}\", \"papers\": [], \"not_found\": true}}. "
        f"Return ONLY JSON."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        if response.text is None:
            return None, [], "api_error"

        parsed = parse_json_response(response.text)
        result = _normalize_papers_result(parsed, scholar_name)
        sources = extract_grounding_sources(response)

        if result.get("not_found") or not result.get("papers"):
            return result, sources, "not_found"

        return result, sources, "success"
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, [], "api_error"


def get_already_fetched(output_dir):
    """Get set of scholar_ids that already have paper data."""
    fetched = set()
    if not output_dir.exists():
        return fetched
    for fname in output_dir.iterdir():
        if fname.suffix == ".json":
            fetched.add(fname.stem.split("_")[0])
    return fetched


def save_papers(data, sources, scholar_id, scholar_name, output_dir):
    """Save fetched papers for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", scholar_name).strip().replace(" ", "_")
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "papers": data.get("papers", []),
        "source_citations": sources,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def _process_scholar(researcher, index, total, num_papers,
                     output_dir, counters_lock, counters):
    """Process a single scholar: fetch papers and save results.

    Each worker creates its own Gemini client to avoid thread-safety issues.
    """
    name = researcher["scholar_name"]
    sid = researcher["scholar_id"]
    inst = researcher["scholar_institution"]

    client = get_client()
    data, sources, status = fetch_papers(client, name, inst, num_papers)

    if status == "success":
        papers = data["papers"]
        save_papers(data, sources, sid, name, output_dir)
        conn = get_connection()
        init_db(conn)
        ensure_scholar(conn, sid, name, inst)
        upsert_papers(conn, sid, papers)
        conn.close()
        with counters_lock:
            counters["success"] += 1
            counters["total_papers"] += len(papers)
            print(f"[{index + 1}/{total}] {name} ({sid}) — {len(papers)} papers saved")
            for p in papers:
                print(f"      - [{p.get('year', '?')}] {p.get('title', '?')[:70]}")

    elif status == "not_found":
        # Gemini searched and explicitly found no qualifying papers — save so we skip next run
        save_papers({"scholar_name": name, "papers": [], "not_found": True}, [], sid, name, output_dir)
        with counters_lock:
            counters["not_found"] += 1
            print(f"[{index + 1}/{total}] {name} ({sid}) — no qualifying papers found")

    else:  # api_error
        with counters_lock:
            counters["api_error"] += 1
            print(f"[{index + 1}/{total}] {name} ({sid}) — API error, will retry")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch recent papers for ScholarBoard researchers via Gemini grounded search"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of researchers to process")
    parser.add_argument("--papers", type=int, default=5,
                        help="Number of recent papers to fetch per researcher (default: 5)")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process only a specific scholar by ID")
    parser.add_argument("--scholar-name", type=str, default=None,
                        help="Process only a specific scholar by name")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-fetch even if data already exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be fetched without making API calls")
    parser.add_argument("--workers", type=int, default=50,
                        help="Number of parallel workers (default: 50)")
    parser.add_argument("--random", action="store_true",
                        help="Shuffle researchers before applying --limit (random sample)")
    parser.add_argument("--is-pi-only", action="store_true",
                        help="Only fetch papers for confirmed PIs (is_pi=1 in DB)")
    args = parser.parse_args()

    researchers = load_scholars(is_pi_only=args.is_pi_only)
    print(f"Loaded {len(researchers)} researchers from DB" + (" (PIs only)" if args.is_pi_only else ""))

    if args.scholar_id:
        researchers = [r for r in researchers if r["scholar_id"] == args.scholar_id.zfill(4)]
        if not researchers:
            print(f"Scholar ID {args.scholar_id} not found")
            sys.exit(1)
    elif args.scholar_name:
        researchers = [r for r in researchers
                       if args.scholar_name.lower() in r["scholar_name"].lower()]
        if not researchers:
            print(f"No scholars matching '{args.scholar_name}'")
            sys.exit(1)

    if not args.no_skip:
        already = get_already_fetched(PAPERS_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r["scholar_id"] not in already]
        if before != len(researchers):
            print(f"Skipping {before - len(researchers)} already-fetched scholars")

    if args.random:
        random.shuffle(researchers)

    if args.limit:
        researchers = researchers[: args.limit]

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

    counters_lock = threading.Lock()
    counters = {"success": 0, "not_found": 0, "api_error": 0, "total_papers": 0}
    total = len(researchers)

    if args.workers <= 1:
        for i, r in enumerate(researchers):
            _process_scholar(r, i, total, args.papers,
                             PAPERS_DIR, counters_lock, counters)
    else:
        print(f"Using {args.workers} parallel workers\n")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    _process_scholar, r, i, total, args.papers,
                    PAPERS_DIR, counters_lock, counters
                ): r
                for i, r in enumerate(researchers)
            }
            for future in as_completed(futures):
                exc = future.exception()
                if exc is not None:
                    scholar = futures[future]
                    print(f"    Unexpected error for {scholar['scholar_name']}: {exc}")

    total = counters["success"] + counters["not_found"] + counters["api_error"]
    print(f"\n--- Summary ---")
    print(f"Papers found:   {counters['success']}/{total}  ({counters['total_papers']} papers total)")
    print(f"Not found:      {counters['not_found']}/{total}  (Gemini searched, no qualifying papers)")
    print(f"API errors:     {counters['api_error']}/{total}  (transient — will retry on next run)")
    print(f"Output: {PAPERS_DIR}")


if __name__ == "__main__":
    main()
