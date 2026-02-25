"""
Generate AI-suggested research directions for scholars.

For each scholar with papers, uses Gemini 3.1 Pro Preview (HIGH thinking)
to propose a novel, scientifically grounded next step in their research.

Usage:
    python3 scripts/generate_ideas.py --dry-run          # Preview
    python3 scripts/generate_ideas.py                    # Run all
    python3 scripts/generate_ideas.py --limit 5          # First 5
    python3 scripts/generate_ideas.py --scholar-id 0459  # Single scholar
    python3 scripts/generate_ideas.py --scholar-name "Bonner"  # By name
    python3 scripts/generate_ideas.py --no-skip          # Regenerate existing
    python3 scripts/generate_ideas.py --delay 2.0        # Custom delay
"""

import json
import os
import re
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from scholar_board.prompt_loader import render_prompt

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_API_KEY (or GEMINI_API_KEY) not found in .env")
    sys.exit(1)

DATA_DIR = PROJECT_ROOT / "data"
PIPELINE_DIR = DATA_DIR / "pipeline"
PAPERS_DIR = PIPELINE_DIR / "scholar_papers"
OUTPUT_DIR = PIPELINE_DIR / "scholar_ideas"
SUBFIELDS_PATH = PIPELINE_DIR / "scholar_subfields.json"

REQUIRED_FIELDS = [
    "research_thread",
    "open_question",
    "title",
    "hypothesis",
    "approach",
    "scientific_impact",
    "why_now",
]


def load_researchers(csv_path):
    """Load unique researchers from vss_data.csv."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    unique = df.drop_duplicates(subset='scholar_id')[
        ['scholar_id', 'scholar_name', 'scholar_institution']
    ].copy()
    unique['scholar_id'] = unique['scholar_id'].astype(str).str.zfill(4)
    return unique.to_dict('records')


def load_subfields(path):
    """Load scholar subfield assignments. Returns dict keyed by scholar_id."""
    if not path.exists():
        print(f"Warning: {path} not found, using fallback subfield for all scholars")
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_papers(scholar_id):
    """Load papers for a scholar from data/scholar_papers/{id}_*.json."""
    if not PAPERS_DIR.exists():
        return []
    for fname in PAPERS_DIR.iterdir():
        if fname.suffix == '.json' and fname.stem.startswith(scholar_id + '_'):
            with open(fname, 'r', encoding='utf-8') as f:
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


def parse_json_response(text):
    """Parse JSON from Gemini response, handling code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from surrounding text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise json.JSONDecodeError("No JSON object found in response", text, 0)


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
        if fname.suffix == '.json':
            generated.add(fname.stem.split('_')[0])
    return generated


def generate_idea(client, scholar_name, institution, primary_subfield, papers):
    """
    Generate a research idea for a scholar using Gemini 3.1 Pro Preview.
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

        # Validate
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
    except genai.errors.ClientError as e:
        print(f"    Gemini client error: {e}")
        return None
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return None


def save_idea(idea, scholar_id, scholar_name, output_dir):
    """Save generated idea to data/scholar_ideas/{id}_{name}.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "idea": idea,
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Generate AI-suggested research directions for ScholarBoard researchers'
    )
    parser.add_argument('--limit', type=int, default=None,
                        help='Max number of scholars to process')
    parser.add_argument('--scholar-id', type=str, default=None,
                        help='Process only a specific scholar by ID')
    parser.add_argument('--scholar-name', type=str, default=None,
                        help='Process scholar by name (case-insensitive substring match)')
    parser.add_argument('--no-skip', action='store_true',
                        help='Regenerate even if output file already exists')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without making API calls')
    parser.add_argument('--workers', type=int, default=25,
                        help='Number of parallel workers (default: 25)')
    args = parser.parse_args()

    csv_path = DATA_DIR / "source" / "vss_data.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    # Load researchers
    researchers = load_researchers(csv_path)
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

    # Load subfields
    subfields = load_subfields(SUBFIELDS_PATH)

    # Filter by specific scholar
    if args.scholar_id:
        researchers = [r for r in researchers if r['scholar_id'] == args.scholar_id.zfill(4)]
        if not researchers:
            print(f"Scholar ID {args.scholar_id} not found")
            sys.exit(1)
    elif args.scholar_name:
        researchers = [r for r in researchers
                       if args.scholar_name.lower() in r['scholar_name'].lower()]
        if not researchers:
            print(f"No scholars matching '{args.scholar_name}'")
            sys.exit(1)

    # Filter to scholars with papers
    researchers_with_papers = []
    for r in researchers:
        papers = load_papers(r['scholar_id'])
        if papers:
            r['_papers'] = papers
            researchers_with_papers.append(r)

    skipped_no_papers = len(researchers) - len(researchers_with_papers)
    if skipped_no_papers > 0:
        print(f"Skipping {skipped_no_papers} scholars with no papers")
    researchers = researchers_with_papers

    # Skip already generated
    skipped_existing = 0
    if not args.no_skip:
        already = get_already_generated(OUTPUT_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r['scholar_id'] not in already]
        skipped_existing = before - len(researchers)
        if skipped_existing > 0:
            print(f"Skipping {skipped_existing} scholars with existing ideas")

    # Apply limit
    if args.limit:
        researchers = researchers[:args.limit]

    print(f"Processing {len(researchers)} scholars\n")

    if not researchers:
        print("Nothing to do!")
        return

    if args.dry_run:
        print(f"[DRY RUN] Would process {len(researchers)} scholars:")
        for i, r in enumerate(researchers):
            subfield_info = subfields.get(r['scholar_id'], {})
            primary = subfield_info.get("primary_subfield", "Vision Science")
            num_papers = len(r['_papers'])
            print(f"  [{i+1}] {r['scholar_name']} ({r['scholar_id']}) — "
                  f"{r['scholar_institution']} — {primary} — {num_papers} papers")
        print(f"\nNo API calls made.")
        return

    # Thread-safe counters and print lock
    counter_lock = threading.Lock()
    success = 0
    fail = 0
    total = len(researchers)

    def process_scholar(index, r):
        """Worker function: creates its own client, processes one scholar."""
        nonlocal success, fail

        name = r['scholar_name']
        sid = r['scholar_id']
        inst = r['scholar_institution']
        papers = r['_papers']

        subfield_info = subfields.get(sid, {})
        primary_subfield = subfield_info.get("primary_subfield", "Vision Science")

        with counter_lock:
            print(f"[{index+1}/{total}] {name} ({sid}) — {inst} — {primary_subfield}")
            print(f"    {len(papers)} papers loaded")

        # Each worker creates its own client instance
        worker_client = genai.Client(api_key=API_KEY)

        idea = generate_idea(worker_client, name, inst, primary_subfield, papers)

        if idea:
            filepath = save_idea(idea, sid, name, OUTPUT_DIR)
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
            # Propagate any unexpected exceptions
            future.result()

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    if skipped_existing > 0:
        print(f"Skipped (existing): {skipped_existing}")
    if skipped_no_papers > 0:
        print(f"Skipped (no papers): {skipped_no_papers}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
