"""
Fetch structured researcher profiles for ScholarBoard using Gemini grounded search.

Uses Gemini 3 Flash Preview with Google Search grounding to extract
structured researcher profiles including bio, main research area, and lab URL.
Returns structured JSON matching the Scholar schema.

Usage:
    python3 scholar_board/profile_extractor.py
    python3 scholar_board/profile_extractor.py --limit 5
    python3 scholar_board/profile_extractor.py --scholar-id 0005
    python3 scholar_board/profile_extractor.py --scholar-name "Aaron Seitz"
    python3 scholar_board/profile_extractor.py --dry-run
    python3 scholar_board/profile_extractor.py --skip-normalize
"""

import json
import os
import re
import csv
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from scholar_board.prompt_loader import render_prompt

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) not found in environment variables")

OUTPUT_DIR = Path("data/scholar_profiles")

SYSTEM_INSTRUCTION = (
    "You are a research analyst specializing in academic profiling. "
    "Provide comprehensive, technically precise information about scholars. "
    "Return results as structured JSON."
)


def build_profile_prompt(scholar_name, institution):
    """Build the grounded search prompt for researcher profile extraction."""
    return (
        f"Search online for the vision science researcher {scholar_name} "
        f"from {institution}.\n\n"
        f"This person is a vision science / neuroscience researcher. "
        f"Use this context to disambiguate from other people with the same name.\n\n"
        f"Find and provide the following structured information:\n"
        f"- scholar_name: Full name\n"
        f"- institution: Current institutional affiliation\n"
        f"- department: Department or school within the institution\n"
        f"- lab_name: Name of their research lab (if known)\n"
        f"- lab_url: URL of their research lab or personal academic page (if found)\n"
        f"- main_research_area: A concise 2-5 word description of their primary research "
        f"focus (e.g. \"visual attention and perception\", \"computational neuroscience\")\n"
        f"- bio: A single paragraph (3-5 sentences) summarizing their most notable "
        f"research contributions, methodologies, and current research direction. "
        f"Be technical and precise. Write in your own words.\n\n"
        f"Use Google Search to check their university faculty page, Google Scholar profile, "
        f"lab website, and other academic sources.\n\n"
        f"If a specific field value is unknown, omit it rather than guessing.\n"
        f"Return ONLY a JSON object with the fields above, no other text."
    )


def parse_json_response(text, scholar_name):
    """Parse JSON from Gemini response text, handling code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    parsed = json.loads(text)

    # Normalize: ensure it's a dict with scholar_name
    if isinstance(parsed, dict):
        if "scholar_name" not in parsed:
            parsed["scholar_name"] = scholar_name
        return parsed
    return {"scholar_name": scholar_name}


def extract_grounding_sources(response):
    """Extract grounding metadata from response."""
    sources = []
    if not response.candidates:
        return sources
    candidate = response.candidates[0]
    if candidate.grounding_metadata:
        meta = candidate.grounding_metadata
        if meta.grounding_chunks:
            for chunk in meta.grounding_chunks:
                if chunk.web:
                    sources.append({
                        "title": chunk.web.title,
                        "url": chunk.web.uri,
                    })
    return sources


def query_gemini(client, scholar_name, institution, scholar_id):
    """
    Query Gemini with grounded search for structured researcher profile data.
    Returns (parsed_dict, grounding_sources) or (None, []) on failure.
    """
    prompt = build_profile_prompt(scholar_name, institution)

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        # Handle empty or RECITATION response
        if response.text is None:
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            print(f"    Empty response (finish_reason={finish_reason})")

            if str(finish_reason) == "RECITATION":
                print(f"    Retrying with shorter bio prompt...")
                return _retry_shorter_bio(client, scholar_name, institution)

            return None, []

        result = parse_json_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        text = response.text or ""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group()), []
            except json.JSONDecodeError:
                pass
        return None, []
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, []


def _retry_shorter_bio(client, scholar_name, institution):
    """Retry profile fetch with a shorter bio request to avoid RECITATION."""
    prompt = (
        f"Search online for the researcher {scholar_name} from {institution}.\n\n"
        f"Provide: scholar_name, institution, department, lab_url, main_research_area, "
        f"and bio (1-2 sentences summarizing their research, in your own words).\n\n"
        f"Return ONLY a JSON object."
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

        result = parse_json_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, []


def scholar_info_exists(scholar_id, output_dir):
    """Check if structured profile JSON already exists for a scholar."""
    for file_path in output_dir.glob(f"{scholar_id}_*.json"):
        return True
    return False


def save_profile(data, sources, scholar_id, scholar_name, output_dir):
    """Save structured profile JSON for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        **data,
        "source_citations": sources
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


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


def _process_single_scholar(scholar_id, scholar, index, total, client,
                            output_dir, skip_normalize, print_lock):
    """
    Process a single scholar: query Gemini, optionally normalize bio, and save.

    Returns True on success, False on failure.
    Each worker should provide its own `client` instance.
    """
    name = scholar['scholar_name']
    inst = scholar['institution']

    with print_lock:
        print(f"[{index}/{total}] {name} ({scholar_id}) — {inst}")

    data, sources = query_gemini(client, name, inst, scholar_id)

    if data:
        if not skip_normalize and data.get("bio"):
            data["bio"] = normalize_bio(client, name, data["bio"])
            with print_lock:
                print(f"    Bio normalized")
        filepath = save_profile(data, sources, scholar_id, name, output_dir)
        with print_lock:
            print(f"    Saved to {filepath}")
            area = data.get("main_research_area")
            if area:
                print(f"    Research area: {area}")
        return True
    else:
        with print_lock:
            print(f"    Failed to extract profile")
        return False


def extract_scholar_info(input_file="data/vss_data.csv", dry_run=False, limit=None,
                         scholar_id_filter=None, scholar_name_filter=None,
                         no_skip=False, skip_normalize=False,
                         workers=1):
    """
    Extract structured profile information for scholars via Gemini grounded search.
    """
    output_dir = OUTPUT_DIR
    output_dir.mkdir(exist_ok=True, parents=True)

    # Read scholars from CSV
    scholars = {}
    print(f"Reading scholars from {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'scholar_id' not in row or not row['scholar_id']:
                    continue

                scholar_id = row['scholar_id'].strip().strip('"\'')
                if not scholar_id:
                    continue

                if scholar_id.isdigit():
                    scholar_id = scholar_id.zfill(4)

                if scholar_id not in scholars:
                    scholar_name = row.get('scholar_name', '').strip().strip('"\'')
                    institution = row.get('scholar_institution', '').strip().strip('"\'')
                    department = row.get('scholar_department', '').strip().strip('"\'')

                    if (not institution or institution == 'N/A') and department and department != 'N/A':
                        institution = department

                    if not scholar_name or not institution or institution == 'N/A':
                        print(f"Skipping scholar with ID {scholar_id} due to missing name or institution")
                        continue

                    scholars[scholar_id] = {
                        'scholar_id': scholar_id,
                        'scholar_name': scholar_name,
                        'institution': institution,
                    }
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    if not scholars:
        print("No scholars found in the input file.")
        return

    print(f"Found {len(scholars)} unique scholars")

    # Filter by specific scholar
    scholar_items = list(scholars.items())
    if scholar_id_filter:
        sid = scholar_id_filter.zfill(4)
        scholar_items = [(k, v) for k, v in scholar_items if k == sid]
        if not scholar_items:
            print(f"Scholar ID {scholar_id_filter} not found")
            return
    elif scholar_name_filter:
        scholar_items = [(k, v) for k, v in scholar_items
                         if scholar_name_filter.lower() in v['scholar_name'].lower()]
        if not scholar_items:
            print(f"No scholars matching '{scholar_name_filter}'")
            return

    # Skip already fetched
    if not no_skip:
        before = len(scholar_items)
        scholar_items = [(k, v) for k, v in scholar_items
                         if not scholar_info_exists(k, output_dir)]
        skipped = before - len(scholar_items)
        if skipped:
            print(f"Skipping {skipped} already-fetched scholars")

    # Apply limit
    if limit:
        scholar_items = scholar_items[:limit]

    print(f"Processing {len(scholar_items)} scholars\n")

    if not scholar_items:
        print("Nothing to do!")
        return

    if dry_run:
        print(f"[DRY RUN] Would process {len(scholar_items)} scholars:")
        for i, (sid, s) in enumerate(scholar_items):
            print(f"  [{i+1}] {s['scholar_name']} ({sid}) — {s['institution']}")
        print(f"\nNo API calls made.")
        return

    print_lock = threading.Lock()
    total = len(scholar_items)

    if workers <= 1:
        # Sequential execution — identical to original behavior
        client = genai.Client(api_key=API_KEY)
        success = 0
        fail = 0

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
        # Parallel execution with ThreadPoolExecutor
        print(f"Using {workers} parallel workers\n")
        success_count = threading.Lock()
        counters = {"success": 0, "fail": 0}

        def worker_task(index, scholar_id, scholar):
            # Each worker creates its own client instance
            worker_client = genai.Client(api_key=API_KEY)
            ok = _process_single_scholar(
                scholar_id, scholar, index, total, worker_client,
                output_dir, skip_normalize, print_lock,
            )
            with success_count:
                if ok:
                    counters["success"] += 1
                else:
                    counters["fail"] += 1

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i, (scholar_id, scholar) in enumerate(scholar_items):
                future = executor.submit(worker_task, i + 1, scholar_id, scholar)
                futures.append(future)

            # Wait for all futures and propagate any unexpected exceptions
            for future in as_completed(futures):
                future.result()

        success = counters["success"]
        fail = counters["fail"]

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
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
    parser.add_argument("--workers", type=int, default=25,
                        help="Number of parallel workers (default: 25)")
    args = parser.parse_args()

    extract_scholar_info(
        dry_run=args.dry_run,
        limit=args.limit,
        scholar_id_filter=args.scholar_id,
        scholar_name_filter=args.scholar_name,
        no_skip=args.no_skip,
        skip_normalize=args.skip_normalize,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
