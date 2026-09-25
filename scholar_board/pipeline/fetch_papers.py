"""
Fetch recent papers for ScholarBoard researchers using Gemini grounded search.

Uses Gemini 3.8 Flash with Google Search grounding to find
the most recent papers for each researcher. Selection rules (enforced both in the
prompt and by `filter_papers` afterwards): dated on or after PAPERS_SINCE, full
papers only (published preferred, preprints allowed; conference abstracts such as
VSS/JOV-supplement/CCN are excluded), and the scholar is FIRST or LAST author.
Citation counts are
fetched separately from Google Scholar via Serper.dev.

Supports parallel execution via --workers to speed up bulk fetches.

Usage:
    uv run -m scholar_board.pipeline.fetch_papers
    uv run -m scholar_board.pipeline.fetch_papers --limit 5 --papers 5
    uv run -m scholar_board.pipeline.fetch_papers --scholar-id 0005
    uv run -m scholar_board.pipeline.fetch_papers --scholar-name "Aaron Seitz"
    uv run -m scholar_board.pipeline.fetch_papers --workers 4 --limit 20
    uv run -m scholar_board.pipeline.fetch_papers --is-pi-only --fewer-than 3   # top up thin profiles
"""

import json
import re
import argparse
import sys
import random
import threading
import time
import unicodedata
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.genai import types

from scholar_board.config import PAPERS_DIR
from scholar_board.gemini import get_client, extract_grounding_sources, parse_json_response, FLASH_MODEL
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_papers, load_scholars

SYSTEM_INSTRUCTION = (
    "You are a research paper database. Return accurate, verified paper information. "
    "Only include papers you are confident exist. Return results as structured JSON."
)

PAPERS_SINCE = date(2023, 1, 1)
# Ask for a few extra candidates so post-filtering still leaves `num_papers`.
CANDIDATE_BUFFER = 3
# Retries for transient API errors (e.g. 429 rate limits), with exponential backoff.
MAX_ATTEMPTS = 4
RETRY_BASE_SECONDS = 15
# Conference abstracts that Google Scholar indexes as if they were papers.
ABSTRACT_MARKERS = ("vision sciences society", "vss", "cognitive computational neuroscience",
                    "ccn", "cosyne", "society for neuroscience", "sfn", "ohbm",
                    "organization for human brain mapping", "abstract", "supplement",
                    "annual meeting", "poster")


def _parse_pub_date(paper: dict) -> date | None:
    """Parse publication_date (YYYY-MM-DD / YYYY-MM) or fall back to year (as Jan 1)."""
    raw = str(paper.get("publication_date") or "").strip()
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", raw)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
        try:
            return date(y, mo, d)
        except ValueError:
            return date(y, 1, 1)
    year = re.match(r"^(\d{4})", str(paper.get("year") or ""))
    return date(int(year.group(1)), 1, 1) if year else None


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def author_position(scholar_name: str, authors: str) -> str | None:
    """Return "first", "last", or None by matching the scholar's surname in the author list."""
    names = [a.strip() for a in re.split(r",|;|\band\b", _norm(authors)) if a.strip()]
    if not names:
        return None
    surname = re.split(r"[\s]+", _norm(scholar_name).strip())[-1]
    surname_parts = set(re.split(r"[\s\-]+", surname))
    def matches(author: str) -> bool:
        return surname in author or bool(surname_parts & set(re.split(r"[\s\-\.]+", author)))
    if matches(names[0]):
        return "first"
    if matches(names[-1]):
        return "last"
    return None


def _is_abstract(venue: str) -> bool:
    words = set(re.findall(r"[a-z]+", venue))
    return any((m in words) if " " not in m else (m in venue) for m in ABSTRACT_MARKERS)


def filter_papers(papers: list[dict], scholar_name: str, num_papers: int) -> list[dict]:
    """Enforce selection rules: recent, no conference abstracts, first/last author.

    Keeps the `num_papers` most recent qualifying papers, newest first, and tags
    each with `author_position`. Papers with an unparseable date are dropped.
    """
    kept = []
    for p in papers:
        pub = _parse_pub_date(p)
        if pub is None or pub < PAPERS_SINCE:
            continue
        if _is_abstract(_norm(p.get("venue") or "")):
            continue
        pos = author_position(scholar_name, p.get("authors") or "")
        if pos is None:
            continue
        kept.append({**p, "author_position": pos, "_pub": pub})
    kept.sort(key=lambda p: p["_pub"], reverse=True)
    return [{k: v for k, v in p.items() if k != "_pub"} for p in kept[:num_papers]]


def build_prompt(scholar_name, institution, num_papers):
    """Build the grounded search prompt for paper fetching."""
    return (
        f"Search online for the {num_papers} most recent papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"STRICT REQUIREMENTS:\n"
        f"- {scholar_name} MUST be either the FIRST AUTHOR or the LAST AUTHOR on the paper. "
        f"Do NOT include papers where they are a middle author.\n"
        f"- Papers must be from {PAPERS_SINCE.year} or later. Return the most recent first.\n"
        f"- Prefer PUBLISHED work: peer-reviewed journal articles and full papers at top-tier "
        f"ML/vision/neuro conferences (NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, EMNLP, ACL, etc.). "
        f"Full preprints (bioRxiv, arXiv, PsyArXiv) are acceptable for recent work; if a "
        f"preprint was later published, cite the published version instead.\n"
        f"- Do NOT include conference abstracts, posters, workshop papers, or short extended abstracts, "
        f"even if Google Scholar indexes them as papers\n"
        f"- EXPLICITLY EXCLUDE: VSS abstracts, Journal of Vision (JOV) conference supplement abstracts, "
        f"CCN extended abstracts, COSYNE abstracts, SfN abstracts, OHBM abstracts\n"
        f"- Do NOT make up or hallucinate any papers. Only include papers you can verify.\n\n"
        f"Use Google Search to find real papers. Check Google Scholar, PubMed, "
        f"journal websites, and the researcher's lab website.\n\n"
        f"For each paper, provide:\n"
        f"- title: exact paper title\n"
        f"- abstract: Write a technical, domain-expert paraphrase of the paper's abstract. "
        f"Use the same level of specialized terminology and jargon as the original — do NOT "
        f"simplify for a general audience. Preserve all specific methods, model names, brain "
        f"regions, metrics, and quantitative findings. Closely rephrase without copying verbatim.\n"
        f"- year: publication year\n"
        f"- publication_date: publication date as YYYY-MM-DD (or YYYY-MM if the day is unknown)\n"
        f"- venue: journal or conference name\n"
        f"- authors: full author list in published order, as a comma-separated string\n"
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
    prompt = build_prompt(scholar_name, institution, num_papers + CANDIDATE_BUFFER)

    try:
        response = client.models.generate_content(
            model=FLASH_MODEL,
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
        result["papers"] = filter_papers(result.get("papers") or [], scholar_name, num_papers)
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
        f"Search online for the {num_papers + CANDIDATE_BUFFER} most recent papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"REQUIREMENTS:\n"
        f"- {scholar_name} MUST be either the FIRST AUTHOR or the LAST AUTHOR\n"
        f"- From {PAPERS_SINCE.year} or later, most recent first\n"
        f"- Journal articles, full preprints, or top-tier conference papers (prefer published versions)\n"
        f"- EXCLUDE: VSS abstracts, JOV conference abstracts, CCN, COSYNE, SfN, OHBM abstracts\n"
        f"- Only verified papers\n\n"
        f"For each paper provide: title, year, publication_date (YYYY-MM-DD), venue, "
        f"authors (in published order), url.\n"
        f"Set abstract to an empty string.\n\n"
        f"Return a JSON object with keys \"scholar_name\" and \"papers\" array. "
        f"If no qualifying papers found, return {{\"scholar_name\": \"{scholar_name}\", \"papers\": [], \"not_found\": true}}. "
        f"Return ONLY JSON."
    )

    try:
        response = client.models.generate_content(
            model=FLASH_MODEL,
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
        result["papers"] = filter_papers(result.get("papers") or [], scholar_name, num_papers)
        sources = extract_grounding_sources(response)

        if result.get("not_found") or not result.get("papers"):
            return result, sources, "not_found"

        return result, sources, "success"
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, [], "api_error"


def get_paper_counts(output_dir):
    """Map scholar_id -> number of saved papers (0 for not_found files)."""
    counts = {}
    if not output_dir.exists():
        return counts
    for fpath in output_dir.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                counts[fpath.stem.split("_")[0]] = len(json.load(f).get("papers") or [])
        except (json.JSONDecodeError, OSError):
            continue
    return counts


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
    for attempt in range(MAX_ATTEMPTS):
        data, sources, status = fetch_papers(client, name, inst, num_papers)
        if status != "api_error":
            break
        time.sleep(RETRY_BASE_SECONDS * 2 ** attempt + random.uniform(0, 5))

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
        # Gemini searched and explicitly found no qualifying papers — save so we skip next
        # run, but never overwrite papers we already have with an empty list.
        if get_paper_counts(output_dir).get(sid, 0) == 0:
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
    parser.add_argument("--ids", type=str, default=None,
                        help="Comma-separated scholar IDs to re-fetch (implies --no-skip)")
    parser.add_argument("--fewer-than", type=int, default=None,
                        help="Re-fetch only scholars with fewer than N saved papers (implies --no-skip)")
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

    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",")}
        researchers = [r for r in researchers if r["scholar_id"] in wanted]
    elif args.fewer_than is not None:
        counts = get_paper_counts(PAPERS_DIR)
        researchers = [r for r in researchers if counts.get(r["scholar_id"], 0) < args.fewer_than]
        print(f"Selected {len(researchers)} scholars with fewer than {args.fewer_than} saved papers")
    elif not args.no_skip:
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
