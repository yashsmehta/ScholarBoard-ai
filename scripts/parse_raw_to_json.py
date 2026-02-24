"""
Parse raw Perplexity profile + paper data into structured scholar JSON.

Reads raw text profiles from data/perplexity_info/ and paper JSON from
data/scholar_papers/, then uses Gemini Flash to parse them into the
canonical Scholar schema.

Usage:
    python3 scripts/parse_raw_to_json.py --dry-run          # Preview what would be parsed
    python3 scripts/parse_raw_to_json.py --limit 5           # Parse first 5
    python3 scripts/parse_raw_to_json.py --scholar-id 0005   # Parse one scholar
"""

import json
import os
import re
import time
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from scholar_board.prompt_loader import render_prompt
from scholar_board.schemas import Scholar

DATA_DIR = PROJECT_ROOT / "data"
PROFILES_DIR = DATA_DIR / "perplexity_info"
PAPERS_DIR = DATA_DIR / "scholar_papers"
OUTPUT_DIR = DATA_DIR / "scholars"


def get_schema_json() -> str:
    """Get the JSON schema string from the Scholar Pydantic model."""
    return json.dumps(Scholar.model_json_schema(), indent=2)


def load_raw_profile(scholar_id: str) -> str | None:
    """Load raw Perplexity profile text for a scholar."""
    for fpath in PROFILES_DIR.glob(f"*_{scholar_id}_raw.txt"):
        return fpath.read_text(encoding="utf-8")
    return None


def load_raw_papers(scholar_id: str) -> str | None:
    """Load raw paper JSON for a scholar."""
    for fpath in PAPERS_DIR.glob(f"{scholar_id}_*.json"):
        return fpath.read_text(encoding="utf-8")
    return None


def parse_with_gemini(raw_profile: str, raw_papers: str, schema_json: str) -> dict:
    """Use Gemini Flash to parse raw data into structured JSON."""
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = render_prompt(
        "parse_to_json",
        raw_profile=raw_profile or "(no profile data available)",
        raw_papers=raw_papers or "(no papers data available)",
        json_schema=schema_json,
    )

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Extract JSON from markdown code blocks if present
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        text = json_match.group(1).strip()

    return json.loads(text)


def get_scholars_to_process() -> list[dict]:
    """Get list of scholars with raw data available."""
    import csv

    csv_path = DATA_DIR / "vss_data.csv"
    scholars = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("scholar_id", "").strip().strip("\"'")
            if not sid or sid in scholars:
                continue
            if sid.isdigit():
                sid = sid.zfill(4)
            scholars[sid] = {
                "id": sid,
                "name": row.get("scholar_name", "").strip(),
                "institution": row.get("scholar_institution", "").strip(),
            }

    # Filter to those with at least a profile or papers
    result = []
    for sid, info in scholars.items():
        has_profile = load_raw_profile(sid) is not None
        has_papers = load_raw_papers(sid) is not None
        if has_profile or has_papers:
            info["has_profile"] = has_profile
            info["has_papers"] = has_papers
            result.append(info)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Parse raw Perplexity data into structured scholar JSON"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be parsed without making API calls")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of scholars to process")
    parser.add_argument("--scholar-id", type=str, default=None,
                        help="Process a specific scholar by ID")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls (default: 1.0)")
    args = parser.parse_args()

    scholars = get_scholars_to_process()
    print(f"Found {len(scholars)} scholars with raw data")

    if args.scholar_id:
        sid = args.scholar_id.zfill(4)
        scholars = [s for s in scholars if s["id"] == sid]
        if not scholars:
            print(f"Scholar ID {sid} not found or has no raw data")
            sys.exit(1)

    # Skip already parsed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = {f.stem for f in OUTPUT_DIR.glob("*.json")}
    before = len(scholars)
    scholars = [s for s in scholars if s["id"] not in existing]
    if before != len(scholars):
        print(f"Skipping {before - len(scholars)} already-parsed scholars")

    if args.limit:
        scholars = scholars[: args.limit]

    print(f"Processing {len(scholars)} scholars\n")

    if not scholars:
        print("Nothing to do!")
        return

    if args.dry_run:
        for i, s in enumerate(scholars):
            prof = "profile" if s.get("has_profile") else "no profile"
            pap = "papers" if s.get("has_papers") else "no papers"
            print(f"  [{i+1}] {s['name']} ({s['id']}) — {prof}, {pap}")
        print(f"\n[DRY RUN] No API calls made.")
        return

    schema_json = get_schema_json()
    success = 0
    fail = 0

    for i, s in enumerate(scholars):
        print(f"[{i+1}/{len(scholars)}] {s['name']} ({s['id']})")
        raw_profile = load_raw_profile(s["id"])
        raw_papers = load_raw_papers(s["id"])

        try:
            result = parse_with_gemini(raw_profile, raw_papers, schema_json)
            # Ensure ID is set
            result["id"] = s["id"]

            # Validate with Pydantic
            scholar = Scholar(**result)
            outpath = OUTPUT_DIR / f"{s['id']}.json"
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(scholar.model_dump_json(indent=2))
            success += 1
            print(f"    Saved to {outpath}")
        except Exception as e:
            fail += 1
            print(f"    Error: {e}")

        if i < len(scholars) - 1:
            time.sleep(args.delay)

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
