"""
Discover prominent vision science researchers via Gemini grounded search.

For each of the 23 vision science subfields, queries Gemini (with Google Search
grounding) for 20 active researchers prominent in that subfield.

Results are deduplicated against the VSS dataset and against each other, then
saved to data/source/extra_researchers.csv with IDs prefixed "E" (E001, E002, ...).

Usage:
    uv run -m scholar_board.pipeline.fetch_extra_researchers --dry-run
    uv run -m scholar_board.pipeline.fetch_extra_researchers
    uv run -m scholar_board.pipeline.fetch_extra_researchers --no-skip
"""

import csv
import json
import re
import argparse
import sys
import unicodedata
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.genai import types

from scholar_board.config import (
    EXTRA_RESEARCHERS_PATH,
    SUBFIELDS_DEF_PATH,
)
from scholar_board.gemini import get_client, parse_json_response

RESEARCHERS_PER_SUBFIELD = 20

SYSTEM_INSTRUCTION = (
    "You are an expert in vision science and visual neuroscience. "
    "Return accurate, verified information about real researchers. "
    "Return results as structured JSON."
)


def build_prompt(subfield_name, subfield_description):
    return (
        f"Search online for {RESEARCHERS_PER_SUBFIELD} currently active vision science "
        f"researchers who are prominent in the subfield of \"{subfield_name}\".\n\n"
        f"Subfield context: {subfield_description}\n\n"
        f"REQUIREMENTS:\n"
        f"- Researchers must be actively publishing in 2022 or later\n"
        f"- Must hold a primary faculty or staff scientist appointment at a university "
        f"or research institute\n"
        f"- Should be recognized leaders or strong contributors specifically in this "
        f"vision science subfield\n"
        f"- Include researchers from visual neuroscience, cognitive neuroscience, "
        f"psychophysics, and computational/AI approaches to vision — as long as their "
        f"work is directly relevant to this subfield\n"
        f"- Do NOT include retired researchers, graduate students, or postdocs as the "
        f"primary entry\n"
        f"- Use Google Search to verify they are real, active researchers\n\n"
        f"Return a JSON array of {RESEARCHERS_PER_SUBFIELD} objects, each with:\n"
        f"- \"name\": full name (first and last)\n"
        f"- \"institution\": primary university or research institute\n\n"
        f"Return ONLY the JSON array, no other text."
    )


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation and accents for deduplication."""
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^\w\s]", "", name).lower().strip()
    # Normalize whitespace
    return " ".join(name.split())



def fetch_subfield_researchers(client, subfield_name, subfield_description):
    """Query Gemini for researchers in a subfield. Returns list of {name, institution}."""
    prompt = build_prompt(subfield_name, subfield_description)

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
            print(f"    Empty response for {subfield_name}")
            return []

        parsed = parse_json_response(response.text)
        if isinstance(parsed, list):
            return parsed
        # Sometimes wrapped in an object
        if isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    return v
        return []

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {subfield_name}: {e}")
        return []
    except Exception as e:
        print(f"    API error for {subfield_name}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Discover prominent vision science researchers via Gemini grounded search"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--no-skip", action="store_true",
                        help="Re-fetch even if extra_researchers.csv already exists")
    args = parser.parse_args()

    if not SUBFIELDS_DEF_PATH.exists():
        print(f"Error: {SUBFIELDS_DEF_PATH} not found")
        sys.exit(1)

    if EXTRA_RESEARCHERS_PATH.exists() and not args.no_skip:
        print(f"extra_researchers.csv already exists ({EXTRA_RESEARCHERS_PATH})")
        print("Use --no-skip to regenerate.")
        return

    with open(SUBFIELDS_DEF_PATH, "r", encoding="utf-8") as f:
        subfields = json.load(f)

    print(f"Loaded {len(subfields)} subfields")
    print(f"Target: {RESEARCHERS_PER_SUBFIELD} researchers per subfield\n")

    if args.dry_run:
        print(f"[DRY RUN] Would query Gemini for {len(subfields)} subfields:")
        for sf in subfields:
            print(f"  {sf['id']:2d}. {sf['name']}")
        print(f"\nNo API calls made.")
        return

    print(f"Running {len(subfields)} subfield queries in parallel\n")

    # Each worker creates its own client to avoid thread-safety issues
    lock = threading.Lock()
    results_by_subfield: dict[int, list] = {}  # sf_id → list of {name, institution}

    def fetch_one(sf):
        client = get_client()
        researchers = fetch_subfield_researchers(client, sf["name"], sf["description"])
        with lock:
            print(f"  [{sf['id']:2d}/{len(subfields)}] {sf['name']} — {len(researchers)} researchers")
        return sf["id"], sf["name"], researchers

    with ThreadPoolExecutor(max_workers=len(subfields)) as executor:
        futures = {executor.submit(fetch_one, sf): sf for sf in subfields}
        for future in as_completed(futures):
            sf_id, sf_name, researchers = future.result()
            results_by_subfield[sf_id] = (sf_name, researchers)

    # Merge in subfield order, deduplicating across subfields
    seen_names: set[str] = set()
    all_researchers: list[dict] = []

    for sf in sorted(subfields, key=lambda s: s["id"]):
        sf_name, researchers = results_by_subfield.get(sf["id"], (sf["name"], []))
        added = 0
        for r in researchers:
            name = r.get("name", "").strip()
            institution = r.get("institution", "").strip()
            if not name:
                continue
            norm = normalize_name(name)
            if norm in seen_names:
                continue
            seen_names.add(norm)
            all_researchers.append({"name": name, "institution": institution, "subfield": sf_name})
            added += 1

    print(f"\nTotal unique researchers: {len(all_researchers)}")

    # Assign E-prefixed IDs
    rows = []
    for i, r in enumerate(all_researchers, 1):
        rows.append({
            "scholar_id": f"E{i:03d}",
            "scholar_name": r["name"],
            "scholar_institution": r["institution"],
            "subfield": r["subfield"],
        })

    # Save to CSV
    EXTRA_RESEARCHERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXTRA_RESEARCHERS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scholar_id", "scholar_name", "scholar_institution", "subfield"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} researchers to {EXTRA_RESEARCHERS_PATH}")

    # Preview first 10
    print("\nSample researchers:")
    for r in rows[:10]:
        print(f"  {r['scholar_id']}  {r['scholar_name']:<35}  {r['scholar_institution']}")


if __name__ == "__main__":
    main()
