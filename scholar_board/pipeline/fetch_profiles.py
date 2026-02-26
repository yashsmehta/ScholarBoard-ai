"""
Fetch structured researcher profiles for ScholarBoard using Gemini grounded search,
then classify each researcher as PI-level or not before writing to the database.

Flow per scholar:
  1. Grounded Gemini call — fetch bio, institution, lab_url, etc.
     (explicitly told not to fabricate; returns not_found if person unknown)
  2. Non-grounded Gemini call — classify is_pi using fetched bio + any papers on disk
  3. If is_pi=False with high/medium confidence → reject, skip DB write
  4. Normalize bio (neutral tone) → save JSON + write to SQLite

Usage:
    uv run -m scholar_board.pipeline.fetch_profiles
    uv run -m scholar_board.pipeline.fetch_profiles --limit 5
    uv run -m scholar_board.pipeline.fetch_profiles --scholar-id 0005
    uv run -m scholar_board.pipeline.fetch_profiles --scholar-name "Aaron Seitz"
    uv run -m scholar_board.pipeline.fetch_profiles --dry-run
    uv run -m scholar_board.pipeline.fetch_profiles --skip-normalize
"""

import json
import re
import argparse
import sys
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.genai import types

from scholar_board.config import (
    PAPERS_DIR,
    PROFILES_DIR,
)
from scholar_board.gemini import get_client, extract_grounding_sources, parse_json_response
from scholar_board.prompt_loader import render_prompt
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_profile, load_scholars, set_is_pi

PROFILE_SYSTEM_INSTRUCTION = (
    "You are a research analyst specializing in academic profiling. "
    "Provide comprehensive, technically precise information about scholars. "
    "Return results as structured JSON."
)

CLASSIFY_SYSTEM_INSTRUCTION = "You are a precise academic classifier."


# ── Profile fetch (grounded) ──────────────────────────────────────────────────

def build_profile_prompt(scholar_name, institution):
    """Build the grounded search prompt for researcher profile extraction."""
    return (
        f"Search online for the vision science researcher {scholar_name} "
        f"from {institution}.\n\n"
        f"This person is a vision science / neuroscience researcher. "
        f"Use this context to disambiguate from other people with the same name.\n\n"
        f"IMPORTANT: Only report information you can verify from real online sources "
        f"(faculty pages, Google Scholar, lab websites, PubMed). "
        f"Do NOT guess, infer, or fabricate any details. "
        f"If you cannot find this person online, return {{\"not_found\": true}} "
        f"and nothing else.\n\n"
        f"Find and provide the following structured information:\n"
        f"- scholar_name: Full name\n"
        f"- institution: Current institutional affiliation\n"
        f"- department: Department or school within the institution\n"
        f"- lab_name: Name of their research lab (if found online)\n"
        f"- lab_url: URL of their research lab or personal academic page (if found)\n"
        f"- main_research_area: A concise 2-5 word description of their primary research "
        f"focus (e.g. \"visual attention and perception\", \"computational neuroscience\")\n"
        f"- bio: A single paragraph (3-5 sentences) summarizing their most notable "
        f"research contributions, methodologies, and current research direction. "
        f"Be technical and precise. Write in your own words — do not copy text verbatim.\n\n"
        f"If a specific field value cannot be verified from online sources, omit it entirely.\n"
        f"Return ONLY a JSON object with the fields above, no other text."
    )


def _normalize_profile_result(parsed, scholar_name):
    """Normalize the structure of a parsed Gemini profile response."""
    if isinstance(parsed, dict):
        if "scholar_name" not in parsed:
            parsed["scholar_name"] = scholar_name
        return parsed
    return {"scholar_name": scholar_name}


def query_gemini(client, scholar_name, institution, scholar_id):
    """Query Gemini with grounded search for structured researcher profile data.

    Returns (parsed_dict, grounding_sources) or (None, []) on failure.
    Returns ({"not_found": True}, []) if the person couldn't be found online.
    """
    prompt = build_profile_prompt(scholar_name, institution)

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PROFILE_SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        if response.text is None:
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            print(f"    Empty response (finish_reason={finish_reason})")

            if str(finish_reason) == "RECITATION":
                print(f"    Retrying with shorter bio prompt...")
                return _retry_shorter_bio(client, scholar_name, institution)

            return None, []

        parsed = parse_json_response(response.text)
        result = _normalize_profile_result(parsed, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        return None, []
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, []


def _retry_shorter_bio(client, scholar_name, institution):
    """Retry profile fetch with a shorter bio request to avoid RECITATION."""
    prompt = (
        f"Search online for the researcher {scholar_name} from {institution}.\n\n"
        f"Only report information you can verify from real sources. "
        f"If not found, return {{\"not_found\": true}}.\n\n"
        f"Provide: scholar_name, institution, department, lab_url, main_research_area, "
        f"and bio (1-2 sentences summarizing their research, in your own words).\n\n"
        f"Return ONLY a JSON object."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PROFILE_SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        if response.text is None:
            return None, []

        parsed = parse_json_response(response.text)
        result = _normalize_profile_result(parsed, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, []


# ── PI classification (non-grounded) ─────────────────────────────────────────

def _load_papers_for_scholar(scholar_id: str) -> list[dict]:
    """Load fetched papers from disk for classification context (best-effort)."""
    for fpath in PAPERS_DIR.glob(f"{scholar_id}_*.json"):
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("papers", [])
        except Exception:
            pass
    return []


def classify_pi(client, scholar_name, institution, department, bio, papers):
    """Classify whether a researcher is PI-level using the fetched profile data.

    Uses the classify_pi.md prompt with a structured JSON schema response.
    Falls back to is_pi=True (low confidence) on any error so we don't
    silently drop researchers due to API failures.

    Returns dict: {is_pi: bool, confidence: "high"|"medium"|"low", reason: str}
    """
    if papers:
        papers_summary = "\n".join(
            f"- [{p.get('year', '?')}] {p.get('title', 'Unknown')} ({p.get('venue', '?')})"
            for p in papers[:5]
        )
    else:
        papers_summary = "Not yet fetched."

    prompt = render_prompt(
        "classify_pi",
        scholar_name=scholar_name,
        institution=institution or "Unknown",
        department=department or "Unknown",
        bio=bio or "Not available.",
        papers_summary=papers_summary,
        total_citations="Unknown",
        h_index="Unknown",
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "is_pi":      {"type": "BOOLEAN", "description": "True if PI-level vision science researcher"},
            "confidence": {"type": "STRING", "enum": ["high", "medium", "low"]},
            "reason":     {"type": "STRING", "description": "1-2 sentence justification"},
        },
        "required": ["is_pi", "confidence", "reason"],
    }

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=CLASSIFY_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        if response.text is None:
            return {"is_pi": True, "confidence": "low", "reason": "Empty classification response"}

        result = parse_json_response(response.text)
        return {
            "is_pi": result.get("is_pi", True),
            "confidence": result.get("confidence", "low"),
            "reason": result.get("reason", ""),
        }
    except Exception as e:
        return {"is_pi": True, "confidence": "low", "reason": f"Classification error: {e}"}


# ── Bio normalization ─────────────────────────────────────────────────────────

def normalize_bio(client, scholar_name, bio):
    """Normalize a bio through Gemini to ensure neutral, factual tone."""
    prompt = render_prompt("normalize_bio", scholar_name=scholar_name, bio=bio)
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"    Warning: bio normalization failed ({e}), keeping original")
        return bio


# ── Save ─────────────────────────────────────────────────────────────────────

def scholar_info_exists(scholar_id, output_dir):
    """Check if a structured profile JSON already exists for a scholar."""
    for _ in output_dir.glob(f"{scholar_id}_*.json"):
        return True
    return False


def save_profile(data, sources, scholar_id, scholar_name, output_dir):
    """Save structured profile JSON for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", scholar_name).strip().replace(" ", "_")
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        **data,
        "source_citations": sources,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


# ── Per-scholar worker ────────────────────────────────────────────────────────

def _process_single_scholar(scholar_id, scholar, index, total, client,
                             output_dir, skip_normalize, print_lock):
    """Process a single scholar: fetch profile → classify PI → write is_pi → save if PI."""
    name = scholar["scholar_name"]
    inst = scholar["scholar_institution"]

    with print_lock:
        print(f"[{index}/{total}] {name} ({scholar_id}) — {inst}")

    # Step 1: grounded profile fetch
    data, sources = query_gemini(client, name, inst, scholar_id)

    if not data or data.get("not_found"):
        with print_lock:
            msg = "Not found online" if data and data.get("not_found") else "Failed to extract profile"
            print(f"    {msg} — skipping")
        return False

    # Step 2: PI classification (non-grounded, uses fetched bio + any papers on disk)
    papers = _load_papers_for_scholar(scholar_id)
    classification = classify_pi(
        client, name,
        data.get("institution", inst), data.get("department", ""),
        data.get("bio", ""), papers,
    )
    is_pi = classification["is_pi"]
    confidence = classification["confidence"]
    reason = classification["reason"]

    # Always write is_pi to DB (true or false)
    conn = get_connection()
    init_db(conn)
    ensure_scholar(conn, scholar_id, name, inst)
    set_is_pi(conn, scholar_id, is_pi)

    if not is_pi:
        conn.close()
        with print_lock:
            print(f"    REJECTED [{confidence}]: {reason}")
        return False

    with print_lock:
        print(f"    PI [{confidence}]: {reason[:80]}")

    # Step 3: normalize bio (PI only)
    if not skip_normalize and data.get("bio"):
        data["bio"] = normalize_bio(client, name, data["bio"])
        with print_lock:
            print(f"    Bio normalized")

    # Step 4: save JSON + write profile fields to DB (PI only)
    save_profile(data, sources, scholar_id, name, output_dir)
    profile_fields = {
        k: data.get(k)
        for k in ("bio", "lab_name", "lab_url", "main_research_area", "department")
        if data.get(k)
    }
    if profile_fields:
        upsert_profile(conn, scholar_id, **profile_fields)
    conn.close()

    with print_lock:
        print(f"    Saved — {data.get('main_research_area', '')}")
    return True


# ── Main orchestration ────────────────────────────────────────────────────────

def extract_scholar_info(dry_run=False, limit=None, scholar_id_filter=None,
                         scholar_name_filter=None, no_skip=False,
                         skip_normalize=False, workers=50, randomize=False):
    """Extract structured profile information for scholars via Gemini grounded search."""
    output_dir = PROFILES_DIR
    output_dir.mkdir(exist_ok=True, parents=True)

    all_scholars = load_scholars(is_pi_only=False)
    if not all_scholars:
        print("No scholars found in DB. Run the seed step first.")
        return

    print(f"Loaded {len(all_scholars)} scholars from DB")
    scholar_items = [(s["scholar_id"], s) for s in all_scholars]
    if scholar_id_filter:
        sid = scholar_id_filter.zfill(4)
        scholar_items = [(k, v) for k, v in scholar_items if k == sid]
        if not scholar_items:
            print(f"Scholar ID {scholar_id_filter} not found")
            return
    elif scholar_name_filter:
        scholar_items = [(k, v) for k, v in scholar_items
                         if scholar_name_filter.lower() in v["scholar_name"].lower()]
        if not scholar_items:
            print(f"No scholars matching '{scholar_name_filter}'")
            return

    if not no_skip:
        before = len(scholar_items)
        scholar_items = [
            (k, v) for k, v in scholar_items
            if not scholar_info_exists(k, output_dir)   # already saved as PI
            and v.get("is_pi") is not False              # already classified non-PI
        ]
        skipped = before - len(scholar_items)
        if skipped:
            print(f"Skipping {skipped} already-processed scholars")

    if randomize:
        random.shuffle(scholar_items)

    if limit:
        scholar_items = scholar_items[:limit]

    print(f"Processing {len(scholar_items)} scholars\n")

    if not scholar_items:
        print("Nothing to do!")
        return

    if dry_run:
        print(f"[DRY RUN] Would process {len(scholar_items)} scholars:")
        for i, (sid, s) in enumerate(scholar_items):
            print(f"  [{i+1}] {s['scholar_name']} ({sid}) — {s['scholar_institution']}")
        print(f"\nNo API calls made.")
        return

    print_lock = threading.Lock()
    total = len(scholar_items)

    if workers <= 1:
        client = get_client()
        success = fail = rejected = 0
        for i, (scholar_id, scholar) in enumerate(scholar_items):
            ok = _process_single_scholar(
                scholar_id, scholar, i + 1, total, client,
                output_dir, skip_normalize, print_lock,
            )
            if ok:
                success += 1
            else:
                fail += 1
    else:
        print(f"Using {workers} parallel workers\n")
        counters_lock = threading.Lock()
        counters = {"success": 0, "fail": 0}

        def worker_task(index, scholar_id, scholar):
            worker_client = get_client()
            ok = _process_single_scholar(
                scholar_id, scholar, index, total, worker_client,
                output_dir, skip_normalize, print_lock,
            )
            with counters_lock:
                if ok:
                    counters["success"] += 1
                else:
                    counters["fail"] += 1

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(worker_task, i + 1, scholar_id, scholar)
                for i, (scholar_id, scholar) in enumerate(scholar_items)
            ]
            for future in as_completed(futures):
                future.result()

        success = counters["success"]
        fail = counters["fail"]

    print(f"\n--- Summary ---")
    print(f"Saved:           {success}/{success + fail}")
    print(f"Rejected/failed: {fail}/{success + fail}")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured scholar profiles via Gemini grounded search"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be fetched without making API calls")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of scholars to process")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process only a specific scholar by ID")
    parser.add_argument("--scholar-name", type=str, default=None,
                        help="Process only a specific scholar by name")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-fetch even if data already exists")
    parser.add_argument("--skip-normalize", action="store_true",
                        help="Skip Gemini bio normalization step")
    parser.add_argument("--workers", type=int, default=50,
                        help="Number of parallel workers (default: 50)")
    parser.add_argument("--random", action="store_true",
                        help="Shuffle scholars before applying --limit (random sample)")
    args = parser.parse_args()

    extract_scholar_info(
        dry_run=args.dry_run,
        limit=args.limit,
        scholar_id_filter=args.scholar_id,
        scholar_name_filter=args.scholar_name,
        no_skip=args.no_skip,
        skip_normalize=args.skip_normalize,
        workers=args.workers,
        randomize=args.random,
    )


if __name__ == "__main__":
    main()
