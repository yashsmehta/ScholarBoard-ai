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
import time
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from google import genai
from google.genai import types

from scholar_board.config import (
    CSV_PATH,
    PAPERS_DIR,
    get_gemini_api_key,
    get_serper_api_key,
    load_scholars_csv,
)
from scholar_board.gemini import extract_grounding_sources
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_papers

SERPER_SCHOLAR_URL = "https://google.serper.dev/scholar"

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
        f"- {scholar_name} MUST be the LAST AUTHOR (senior/corresponding author) on the paper\n"
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
        f"Return ONLY the JSON, no other text."
    )


def _parse_papers_response(text, scholar_name):
    """Parse and normalize JSON from Gemini response for the papers endpoint."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    parsed = json.loads(text)

    if isinstance(parsed, list):
        return {"scholar_name": scholar_name, "papers": parsed}
    elif isinstance(parsed, dict) and "papers" not in parsed:
        return {"scholar_name": scholar_name, "papers": [parsed]}
    return parsed


def fetch_papers(client, scholar_name, institution, num_papers=5):
    """
    Fetch recent papers for a scholar using Gemini grounded search.
    Returns (parsed_dict, grounding_sources) or (None, []) on failure.
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

            return None, []

        result = _parse_papers_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        text = response.text or ""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, dict) and "papers" not in result:
                    result = {"scholar_name": scholar_name, "papers": [result]}
                return result, []
            except json.JSONDecodeError:
                pass
        return None, []
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, []


def _retry_without_abstract(client, scholar_name, institution, num_papers):
    """Retry paper fetch with a prompt that skips abstracts to avoid RECITATION."""
    prompt = (
        f"Search online for the {num_papers} most recent peer-reviewed journal papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"REQUIREMENTS:\n"
        f"- {scholar_name} MUST be the LAST AUTHOR (senior/corresponding author)\n"
        f"- Published in 2024 or later, most recent first\n"
        f"- Full journal articles, preprints, or top-tier conference papers only\n"
        f"- EXCLUDE: VSS abstracts, JOV conference abstracts, CCN, COSYNE, SfN, OHBM abstracts\n"
        f"- Only verified papers\n\n"
        f"For each paper provide: title, year, venue, authors, url.\n"
        f"Set abstract to an empty string.\n\n"
        f"Return a JSON object with keys \"scholar_name\" and \"papers\" array. "
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
            return None, []

        result = _parse_papers_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, []


def lookup_citations(papers, serper_key):
    """Look up citation counts from Google Scholar via Serper.dev."""
    if not serper_key:
        return papers

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
        except Exception:
            paper["citations"] = "0"

    return papers


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


def _process_scholar(researcher, index, total, num_papers, api_key, serper_key,
                     output_dir, counters_lock, counters):
    """Process a single scholar: fetch papers and save results.

    Each worker creates its own genai client to avoid thread-safety issues.
    """
    name = researcher["scholar_name"]
    sid = researcher["scholar_id"]
    inst = researcher["scholar_institution"]

    with counters_lock:
        print(f"[{index + 1}/{total}] {name} ({sid}) — {inst}")

    client = genai.Client(api_key=api_key)
    data, sources = fetch_papers(client, name, inst, num_papers)

    if data and data.get("papers"):
        papers = data["papers"]
        if serper_key:
            papers = lookup_citations(papers, serper_key)
            data["papers"] = papers
        save_papers(data, sources, sid, name, output_dir)
        conn = get_connection()
        init_db(conn)
        ensure_scholar(conn, sid, name, inst)
        upsert_papers(conn, sid, papers)
        conn.close()
        with counters_lock:
            counters["success"] += 1
            counters["total_papers"] += len(papers)
            print(f"    {len(papers)} papers saved")
            for p in papers:
                cites = p.get("citations", "0")
                print(f"      - [{p.get('year', '?')}] {p.get('title', '?')[:70]} ({cites} cites)")
    else:
        with counters_lock:
            counters["fail"] += 1
            print(f"    No papers found")


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
    parser.add_argument("--workers", type=int, default=25,
                        help="Number of parallel workers (default: 25)")
    args = parser.parse_args()

    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found")
        sys.exit(1)

    researchers = load_scholars_csv()
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

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

    api_key = get_gemini_api_key()
    serper_key = get_serper_api_key()
    counters_lock = threading.Lock()
    counters = {"success": 0, "fail": 0, "total_papers": 0}
    total = len(researchers)

    if args.workers <= 1:
        for i, r in enumerate(researchers):
            _process_scholar(r, i, total, args.papers, api_key, serper_key,
                             PAPERS_DIR, counters_lock, counters)
    else:
        print(f"Using {args.workers} parallel workers\n")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    _process_scholar, r, i, total, args.papers, api_key,
                    serper_key, PAPERS_DIR, counters_lock, counters
                ): r
                for i, r in enumerate(researchers)
            }
            for future in as_completed(futures):
                exc = future.exception()
                if exc is not None:
                    scholar = futures[future]
                    print(f"    Unexpected error for {scholar['scholar_name']}: {exc}")

    print(f"\n--- Summary ---")
    print(f"Successful: {counters['success']}/{counters['success'] + counters['fail']}")
    print(f"Failed:     {counters['fail']}/{counters['success'] + counters['fail']}")
    print(f"Total papers: {counters['total_papers']}")
    print(f"Output: {PAPERS_DIR}")


if __name__ == "__main__":
    main()
