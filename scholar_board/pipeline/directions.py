"""
Generate "Current Research Direction" paragraphs for scholars.

For each PI with papers, uses Gemini 3 Flash Preview to synthesize a concise
paragraph describing the researcher's current research trajectory.

Usage:
    uv run -m scholar_board.pipeline.directions --dry-run          # Preview
    uv run -m scholar_board.pipeline.directions                    # Run all
    uv run -m scholar_board.pipeline.directions --limit 5          # First 5
    uv run -m scholar_board.pipeline.directions --scholar-id 0459  # Single scholar
    uv run -m scholar_board.pipeline.directions --scholar-name "Bonner"
    uv run -m scholar_board.pipeline.directions --no-skip          # Regenerate existing
"""

import json
import re
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from scholar_board.config import PAPERS_DIR, DIRECTIONS_DIR
from scholar_board.gemini import get_client, generate_text
from scholar_board.prompt_loader import render_prompt
from scholar_board.db import (
    get_connection,
    init_db,
    ensure_scholar,
    upsert_research_direction,
    load_scholars,
)


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


def get_already_generated(output_dir):
    """Get set of scholar_ids that already have direction files."""
    generated = set()
    if not output_dir.exists():
        return generated
    for fname in output_dir.iterdir():
        if fname.suffix == ".json":
            generated.add(fname.stem.split("_")[0])
    return generated


def generate_direction(client, scholar_name, institution, papers):
    """Generate a research direction paragraph using Gemini 3.1 Pro Preview with thinking.

    Returns the text string on success, or None on failure.
    """
    papers_text = build_papers_text(papers)
    prompt = render_prompt(
        "research_direction",
        scholar_name=scholar_name,
        institution=institution,
        papers_text=papers_text,
    )

    try:
        text = generate_text(
            prompt,
            model="gemini-3.1-pro-preview",
            thinking=True,
            client=client,
        )

        if not text:
            print(f"    Empty response")
            return None

        # Strip any markdown code fences the model might add
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        if len(text) < 50:
            print(f"    Response too short ({len(text)} chars)")
            return None

        return text

    except Exception as e:
        print(f"    Error: {e}")
        return None


def save_direction(direction_text, scholar_id, scholar_name, output_dir):
    """Save generated direction to DIRECTIONS_DIR/{id}_{name}.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\s-]", "", scholar_name).strip().replace(" ", "_")
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "research_direction": direction_text,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Generate current research direction paragraphs for ScholarBoard researchers"
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

    researchers = load_scholars(is_pi_only=True)
    print(f"Loaded {len(researchers)} PI researchers from DB")

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
        already = get_already_generated(DIRECTIONS_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r["scholar_id"] not in already]
        skipped_existing = before - len(researchers)
        if skipped_existing > 0:
            print(f"Skipping {skipped_existing} scholars with existing directions")

    if args.limit:
        researchers = researchers[: args.limit]

    print(f"Processing {len(researchers)} scholars\n")

    if not researchers:
        print("Nothing to do!")
        return

    if args.dry_run:
        print(f"[DRY RUN] Would process {len(researchers)} scholars:")
        for i, r in enumerate(researchers):
            num_papers = len(r["_papers"])
            print(f"  [{i+1}] {r['scholar_name']} ({r['scholar_id']}) — "
                  f"{r['scholar_institution']} — {num_papers} papers")
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

        with counter_lock:
            print(f"[{index+1}/{total}] {name} ({sid}) — {inst}")
            print(f"    {len(papers)} papers loaded")

        worker_client = get_client()
        direction_text = generate_direction(worker_client, name, inst, papers)

        if direction_text:
            filepath = save_direction(direction_text, sid, name, DIRECTIONS_DIR)
            conn = get_connection()
            init_db(conn)
            ensure_scholar(conn, sid, name, inst)
            upsert_research_direction(conn, sid, direction_text)
            conn.close()
            with counter_lock:
                success += 1
                print(f"    [{index+1}/{total}] Saved: {filepath.name}")
                preview = direction_text[:80] + "..." if len(direction_text) > 80 else direction_text
                print(f"    [{index+1}/{total}] Preview: {preview}")
        else:
            with counter_lock:
                fail += 1
                print(f"    [{index+1}/{total}] Failed to generate direction")

        return direction_text is not None

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
    print(f"Output: {DIRECTIONS_DIR}")


if __name__ == "__main__":
    main()
