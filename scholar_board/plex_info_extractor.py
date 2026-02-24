"""
Fetch structured researcher profiles for ScholarBoard using Perplexity API.

Uses Perplexity's sonar-pro model with academic search mode to extract
structured researcher profiles including bio, main research area, and lab URL.
Returns structured JSON matching the Scholar schema.

Usage:
    python3 scholar_board/plex_info_extractor.py
    python3 scholar_board/plex_info_extractor.py --limit 5
    python3 scholar_board/plex_info_extractor.py --scholar-id 0005
    python3 scholar_board/plex_info_extractor.py --scholar-name "Aaron Seitz"
    python3 scholar_board/plex_info_extractor.py --dry-run
    python3 scholar_board/plex_info_extractor.py --skip-normalize
"""

import json
import os
import re
import time
import csv
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

from scholar_board.prompt_loader import render_prompt

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

OUTPUT_DIR = Path("data/perplexity_info")

# JSON schema for structured output — maps to Scholar model fields
PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "scholar_name": {"type": "string"},
        "institution": {"type": "string"},
        "department": {"type": "string"},
        "lab_url": {"type": "string"},
        "main_research_area": {"type": "string"},
        "bio": {"type": "string"},
    },
    "required": ["scholar_name", "bio"]
}


def query_perplexity(client, scholar_name, institution, scholar_id):
    """
    Query the Perplexity API for structured researcher profile data.
    Returns (parsed_dict, citations) or (None, []) on failure.
    """
    prompt = render_prompt(
        "fetch_researcher_info",
        scholar_name=scholar_name,
        institution=institution,
    )

    try:
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": "You are a research analyst specializing in academic profiling. Provide comprehensive, technically precise information about scholars. Return results as structured JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": PROFILE_SCHEMA
                }
            },
            extra_body={
                "search_mode": "academic",
                "web_search_options": {
                    "search_context_size": "high"
                }
            }
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Extract citations from response if available
        citations = []
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations

        return result, citations

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group()), []
            except json.JSONDecodeError:
                pass
        return None, []
    except Exception as e:
        print(f"    API error for {scholar_name}: {e}")
        return None, []


def scholar_info_exists(scholar_id, output_dir):
    """Check if structured profile JSON already exists for a scholar."""
    for file_path in output_dir.glob(f"{scholar_id}_*.json"):
        return True
    return False


def save_profile(data, citations, scholar_id, scholar_name, output_dir):
    """Save structured profile JSON for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        **data,
        "source_citations": citations
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def normalize_bio(gemini_client, scholar_name, bio):
    """Normalize a bio through Gemini to ensure neutral, factual tone."""
    prompt = render_prompt("normalize_bio", scholar_name=scholar_name, bio=bio)
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"    Warning: bio normalization failed ({e}), keeping original")
        return bio


def extract_scholar_info(input_file="data/vss_data.csv", dry_run=False, limit=None,
                         scholar_id_filter=None, scholar_name_filter=None,
                         no_skip=False, delay=2.0, skip_normalize=False):
    """
    Extract structured profile information for scholars via Perplexity API.
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

    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")

    gemini_client = None
    if not skip_normalize:
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            gemini_client = genai.Client(api_key=google_key)
        else:
            print("Warning: GOOGLE_API_KEY not set, skipping bio normalization")

    success = 0
    fail = 0

    for i, (scholar_id, scholar) in enumerate(scholar_items):
        name = scholar['scholar_name']
        inst = scholar['institution']
        print(f"[{i+1}/{len(scholar_items)}] {name} ({scholar_id}) — {inst}")

        data, citations = query_perplexity(client, name, inst, scholar_id)

        if data:
            if gemini_client and data.get("bio"):
                data["bio"] = normalize_bio(gemini_client, name, data["bio"])
                print(f"    Bio normalized")
            filepath = save_profile(data, citations, scholar_id, name, output_dir)
            success += 1
            print(f"    Saved to {filepath}")
            area = data.get("main_research_area")
            if area:
                print(f"    Research area: {area}")
        else:
            fail += 1
            print(f"    Failed to extract profile")

        if i < len(scholar_items) - 1:
            time.sleep(delay)

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured scholar profiles via Perplexity API"
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
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Delay between API calls in seconds (default: 2.0)")
    parser.add_argument("--skip-normalize", action="store_true",
                        help="Skip Gemini bio normalization step")
    args = parser.parse_args()

    extract_scholar_info(
        dry_run=args.dry_run,
        limit=args.limit,
        scholar_id_filter=args.scholar_id,
        scholar_name_filter=args.scholar_name,
        no_skip=args.no_skip,
        delay=args.delay,
        skip_normalize=args.skip_normalize,
    )


if __name__ == "__main__":
    main()
