"""
Generate AI-suggested research directions for scholars.

For each scholar with papers, uses Gemini 3.1 Pro Preview (HIGH thinking)
to propose a novel, scientifically grounded next step in their research.

Usage:
    uv run -m scholar_board.pipeline.ideas --dry-run          # Preview
    uv run -m scholar_board.pipeline.ideas                    # Run all
    uv run -m scholar_board.pipeline.ideas --limit 5          # First 5
    uv run -m scholar_board.pipeline.ideas --scholar-id 0459  # Single scholar
    uv run -m scholar_board.pipeline.ideas --scholar-name "Bonner"
    uv run -m scholar_board.pipeline.ideas --no-skip          # Regenerate existing
"""

import json
import re
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.genai import errors, types

from scholar_board.config import (
    CSV_PATH,
    PAPERS_DIR,
    IDEAS_DIR,
    SUBFIELDS_PATH,
    load_scholars_csv,
)
from scholar_board.gemini import get_client, parse_json_response
from scholar_board.prompt_loader import render_prompt
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_idea

REQUIRED_FIELDS = [
    "research_thread",
    "open_question",
    "title",
    "hypothesis",
    "approach",
    "scientific_impact",
    "why_now",
]


def load_subfields(path):
    """Load scholar subfield assignments. Returns dict keyed by scholar_id."""
    if not path.exists():
        print(f"Warning: {path} not found, using fallback subfield for all scholars")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_papers(scholar_id):
    """Load papers for a scholar from PAPERS_DIR/{id}_*.json."""
    if not PAPERS_DIR.exists():
        return []
    for fname in PAPERS_DIR.iterdir():
        if fname.suffix == ".json" and fname.stem.startswith(scholar_id + "_"):
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("papers", [])
    return []


def build_papers_text(papers):
    """Build formatted text block from a list of paper dicts."""
    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "?")
        venue = p.get("venue", "")
        abstract = p.get("abstract", "")

        entry = f"Paper {i}: {title} ({year})"
        if venue:
            entry += f"\nVenue: {venue}"
        if abstract:
            entry += f"\nAbstract: {abstract}"
        lines.append(entry)
    return "\n\n".join(lines)


def validate_idea(idea):
    """Validate that all required fields are present and non-empty strings."""
    missing = []
    empty = []
    for field in REQUIRED_FIELDS:
        if field not in idea:
            missing.append(field)
        elif not isinstance(idea[field], str) or not idea[field].strip():
            empty.append(field)
    return missing, empty


def get_already_generated(output_dir):
    """Get set of scholar_ids that already have idea files."""
    generated = set()
    if not output_dir.exists():
        return generated
    for fname in output_dir.iterdir():
        if fname.suffix == ".json":
            generated.add(fname.stem.split("_")[0])
    return generated


def generate_idea(client, scholar_name, institution, primary_subfield, papers):
    """Generate a research idea for a scholar using Gemini 3.1 Pro Preview.

    Returns the parsed idea dict on success, or None on failure.
    """
    papers_text = build_papers_text(papers)
    prompt = render_prompt(
        "suggest_next_idea",
        scholar_name=scholar_name,
        institution=institution,
        primary_subfield=primary_subfield,
        papers_text=papers_text,
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.HIGH,
                ),
            ),
        )

        if response.text is None:
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            print(f"    Empty response (finish_reason={finish_reason})")
            return None

        idea = parse_json_response(response.text)

        missing, empty = validate_idea(idea)
        if missing:
            print(f"    Validation failed — missing fields: {missing}")
            return None
        if empty:
            print(f"    Validation failed — empty fields: {empty}")
            return None

        return idea

    except json.JSONDecodeError as e:
        raw = response.text if response and response.text else "(no text)"
        print(f"    JSON parse error: {e}")
        print(f"    Raw response: {raw[:200]}...")
        return None
    except errors.ClientError as e:
        print(f"    Gemini client error: {e}")
        return None
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return None


def save_idea(idea, scholar_id, scholar_name, output_dir):
    """Save generated idea to IDEAS_DIR/{id}_{name}.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", scholar_name).strip().replace(" ", "_")
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "idea": idea,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-suggested research directions for ScholarBoard researchers"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of scholars to process")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process only a specific scholar by ID")
    parser.add_argument("--scholar-name", type=str, default=None,
                        help="Process scholar by name (case-insensitive substring match)")
    parser.add_argument("--no-skip", action="store_true",
                        help="Regenerate even if output file already exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--workers", type=int, default=25,
                        help="Number of parallel workers (default: 25)")
    args = parser.parse_args()

    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found")
        sys.exit(1)

    researchers = load_scholars_csv()
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

    subfields = load_subfields(SUBFIELDS_PATH)

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

    researchers_with_papers = []
    for r in researchers:
        papers = load_papers(r["scholar_id"])
        if papers:
            r["_papers"] = papers
            researchers_with_papers.append(r)

    skipped_no_papers = len(researchers) - len(researchers_with_papers)
    if skipped_no_papers > 0:
        print(f"Skipping {skipped_no_papers} scholars with no papers")
    researchers = researchers_with_papers

    skipped_existing = 0
    if not args.no_skip:
        already = get_already_generated(IDEAS_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r["scholar_id"] not in already]
        skipped_existing = before - len(researchers)
        if skipped_existing > 0:
            print(f"Skipping {skipped_existing} scholars with existing ideas")

    if args.limit:
        researchers = researchers[: args.limit]

    print(f"Processing {len(researchers)} scholars\n")

    if not researchers:
        print("Nothing to do!")
        return

    if args.dry_run:
        print(f"[DRY RUN] Would process {len(researchers)} scholars:")
        for i, r in enumerate(researchers):
            subfield_info = subfields.get(r["scholar_id"], {})
            primary = subfield_info.get("primary_subfield", "Vision Science")
            num_papers = len(r["_papers"])
            print(f"  [{i+1}] {r['scholar_name']} ({r['scholar_id']}) — "
                  f"{r['scholar_institution']} — {primary} — {num_papers} papers")
        print(f"\nNo API calls made.")
        return

    counter_lock = threading.Lock()
    success = 0
    fail = 0
    total = len(researchers)

    def process_scholar(index, r):
        nonlocal success, fail

        name = r["scholar_name"]
        sid = r["scholar_id"]
        inst = r["scholar_institution"]
        papers = r["_papers"]

        subfield_info = subfields.get(sid, {})
        primary_subfield = subfield_info.get("primary_subfield", "Vision Science")

        with counter_lock:
            print(f"[{index+1}/{total}] {name} ({sid}) — {inst} — {primary_subfield}")
            print(f"    {len(papers)} papers loaded")

        worker_client = get_client()
        idea = generate_idea(worker_client, name, inst, primary_subfield, papers)

        if idea:
            filepath = save_idea(idea, sid, name, IDEAS_DIR)
            conn = get_connection()
            init_db(conn)
            ensure_scholar(conn, sid, name, inst)
            upsert_idea(conn, sid, idea)
            conn.close()
            with counter_lock:
                success += 1
                print(f"    [{index+1}/{total}] Saved: {filepath.name}")
                print(f"    [{index+1}/{total}] Title: {idea.get('title', '?')}")
        else:
            with counter_lock:
                fail += 1
                print(f"    [{index+1}/{total}] Failed to generate idea")

        return idea is not None

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_scholar, i, r): r
            for i, r in enumerate(researchers)
        }
        for future in as_completed(futures):
            future.result()

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    if skipped_existing > 0:
        print(f"Skipped (existing): {skipped_existing}")
    if skipped_no_papers > 0:
        print(f"Skipped (no papers): {skipped_no_papers}")
    print(f"Output: {IDEAS_DIR}")


if __name__ == "__main__":
    main()
