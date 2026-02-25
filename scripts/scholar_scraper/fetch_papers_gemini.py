"""
Fetch recent papers for ScholarBoard researchers using Gemini grounded search.

Uses Gemini 3 Flash Preview with Google Search grounding to find
the most recent papers for each researcher. Returns title, abstract,
citations, and year.

Usage:
    python3 scripts/scholar_scraper/fetch_papers_gemini.py
    python3 scripts/scholar_scraper/fetch_papers_gemini.py --limit 5 --papers 5
    python3 scripts/scholar_scraper/fetch_papers_gemini.py --scholar-id 0005
    python3 scripts/scholar_scraper/fetch_papers_gemini.py --scholar-name "Aaron Seitz"
"""

import json
import os
import re
import time
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_API_KEY (or GEMINI_API_KEY) not found in .env")
    sys.exit(1)

OUTPUT_DIR = PROJECT_ROOT / "data" / "scholar_papers"

SYSTEM_INSTRUCTION = (
    "You are a research paper database. Return accurate, verified paper information. "
    "Only include papers you are confident exist. Return results as structured JSON."
)


def build_prompt(scholar_name, institution, num_papers):
    """Build the grounded search prompt for paper fetching."""
    return (
        f"Search online for the {num_papers} most recent peer-reviewed journal papers "
        f"by {scholar_name} from {institution}.\n\n"
        f"STRICT REQUIREMENTS:\n"
        f"- {scholar_name} MUST be the LAST AUTHOR (senior/corresponding author) on the paper\n"
        f"- Papers must be published in 2023 or later (post-2023 only). Prioritize most recent first.\n"
        f"- Only include full peer-reviewed journal articles or preprints (e.g. Nature, Science, "
        f"PNAS, PLOS, eLife, Journal of Neuroscience, bioRxiv/arXiv preprints, etc.)\n"
        f"- Do NOT include conference abstracts, posters, workshop papers, or short proceedings\n"
        f"- EXPLICITLY EXCLUDE: VSS abstracts, Journal of Vision (JOV) conference supplement abstracts, "
        f"CCN extended abstracts, COSYNE abstracts, SfN abstracts, OHBM abstracts\n"
        f"- Do NOT make up or hallucinate any papers. Only include papers you can verify.\n\n"
        f"Use Google Search to find real papers. Check Google Scholar, PubMed, bioRxiv, "
        f"and the researcher's lab website.\n\n"
        f"For each paper, provide:\n"
        f"- title: exact paper title\n"
        f"- abstract: Write a technical, domain-expert paraphrase of the paper's abstract. "
        f"Use the same level of specialized terminology and jargon as the original — do NOT "
        f"simplify for a general audience. Preserve all specific methods, model names, brain "
        f"regions, metrics, and quantitative findings. Closely rephrase without copying verbatim.\n"
        f"- year: publication year\n"
        f"- citations: approximate citation count (or '0' if unknown)\n"
        f"- venue: journal or conference name\n"
        f"- authors: full author list as a comma-separated string\n"
        f"- url: DOI or paper URL if available\n\n"
        f"Return a JSON object with keys \"scholar_name\" (string) and \"papers\" (array of paper objects). "
        f"Return ONLY the JSON, no other text."
    )


def parse_json_response(text, scholar_name):
    """Parse JSON from Gemini response text, handling code fences and normalization."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    parsed = json.loads(text)

    # Normalize: Gemini may return a list or an object without "papers" key
    if isinstance(parsed, list):
        return {"scholar_name": scholar_name, "papers": parsed}
    elif isinstance(parsed, dict) and "papers" not in parsed:
        return {"scholar_name": scholar_name, "papers": [parsed]}
    return parsed


def extract_grounding_sources(response):
    """Extract grounding metadata (search queries and source URLs) from response."""
    sources = []
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

        # Handle RECITATION or empty response
        if response.text is None:
            finish_reason = None
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
            print(f"    Empty response (finish_reason={finish_reason})")

            if str(finish_reason) == "RECITATION":
                print(f"    Retrying with softer abstract prompt...")
                return _retry_without_abstract(client, scholar_name, institution, num_papers)

            return None, []

        result = parse_json_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources

    except json.JSONDecodeError as e:
        print(f"    JSON parse error for {scholar_name}: {e}")
        # Try to extract JSON from the response
        text = response.text or ""
        match = re.search(r'\{.*\}', text, re.DOTALL)
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
        f"- Published in 2023 or later, most recent first\n"
        f"- Full journal articles or preprints only\n"
        f"- EXCLUDE: VSS abstracts, JOV conference abstracts, CCN, COSYNE, SfN, OHBM abstracts\n"
        f"- Only verified papers\n\n"
        f"For each paper provide: title, year, venue, authors, url, citations.\n"
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

        result = parse_json_response(response.text, scholar_name)
        sources = extract_grounding_sources(response)
        return result, sources
    except Exception as e:
        print(f"    Retry also failed for {scholar_name}: {e}")
        return None, []


def load_researchers(csv_path):
    """Load unique researchers from vss_data.csv."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    unique = df.drop_duplicates(subset='scholar_id')[
        ['scholar_id', 'scholar_name', 'scholar_institution']
    ].copy()
    unique['scholar_id'] = unique['scholar_id'].astype(str).str.zfill(4)
    return unique.to_dict('records')


def get_already_fetched(output_dir):
    """Get set of scholar_ids that already have paper data."""
    fetched = set()
    if not output_dir.exists():
        return fetched
    for fname in output_dir.iterdir():
        if fname.suffix == '.json':
            fetched.add(fname.stem.split('_')[0])
    return fetched


def save_papers(data, sources, scholar_id, scholar_name, output_dir):
    """Save fetched papers for a scholar."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^\w\s-]', '', scholar_name).strip().replace(' ', '_')
    filepath = output_dir / f"{scholar_id}_{safe_name}.json"

    output = {
        "scholar_id": scholar_id,
        "scholar_name": scholar_name,
        "papers": data.get("papers", []),
        "source_citations": sources
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Fetch recent papers for ScholarBoard researchers via Gemini grounded search'
    )
    parser.add_argument('--limit', type=int, default=None,
                        help='Max number of researchers to process')
    parser.add_argument('--papers', type=int, default=5,
                        help='Number of recent papers to fetch per researcher (default: 5)')
    parser.add_argument('--scholar-id', type=str, default=None,
                        help='Process only a specific scholar by ID')
    parser.add_argument('--scholar-name', type=str, default=None,
                        help='Process only a specific scholar by name')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-fetch even if data already exists')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be fetched without making API calls')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between API calls in seconds (default: 1.0)')
    args = parser.parse_args()

    csv_path = PROJECT_ROOT / "data" / "vss_data.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        sys.exit(1)

    # Load researchers
    researchers = load_researchers(csv_path)
    print(f"Loaded {len(researchers)} unique researchers from vss_data.csv")

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

    # Skip already fetched
    if not args.no_skip:
        already = get_already_fetched(OUTPUT_DIR)
        before = len(researchers)
        researchers = [r for r in researchers if r['scholar_id'] not in already]
        if before != len(researchers):
            print(f"Skipping {before - len(researchers)} already-fetched scholars")

    # Apply limit
    if args.limit:
        researchers = researchers[:args.limit]

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

    client = genai.Client(api_key=API_KEY)

    success = 0
    fail = 0
    total_papers = 0

    for i, r in enumerate(researchers):
        name = r['scholar_name']
        sid = r['scholar_id']
        inst = r['scholar_institution']

        print(f"[{i+1}/{len(researchers)}] {name} ({sid}) — {inst}")

        data, sources = fetch_papers(client, name, inst, args.papers)

        if data and data.get("papers"):
            papers = data["papers"]
            save_papers(data, sources, sid, name, OUTPUT_DIR)
            total_papers += len(papers)
            success += 1
            print(f"    {len(papers)} papers saved")
            for p in papers:
                print(f"      - [{p.get('year', '?')}] {p.get('title', '?')[:80]}")
        else:
            fail += 1
            print(f"    No papers found")

        # Rate limiting
        if i < len(researchers) - 1:
            time.sleep(args.delay)

    print(f"\n--- Summary ---")
    print(f"Successful: {success}/{success + fail}")
    print(f"Failed:     {fail}/{success + fail}")
    print(f"Total papers: {total_papers}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
