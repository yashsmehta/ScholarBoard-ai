"""
Compare factuality of grounded search: Perplexity sonar-pro vs Gemini 3 Flash Preview.

Fetches recent papers from a specific researcher using both APIs and outputs
results side-by-side for manual verification.

Usage:
    python3 scripts/compare_grounded_search.py
    python3 scripts/compare_grounded_search.py --name "Mick Bonner" --institution "Johns Hopkins University"
    python3 scripts/compare_grounded_search.py --papers 8
"""

import json
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from scholar_board.prompt_loader import render_prompt


# ── Shared prompt & schema ──────────────────────────────────────────────────

PAPER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "scholar_name": {"type": "STRING"},
        "papers": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "Exact paper title"},
                    "abstract": {"type": "STRING", "description": "Paper abstract or detailed summary"},
                    "year": {"type": "STRING", "description": "Publication year"},
                    "citations": {"type": "STRING", "description": "Approximate citation count"},
                    "venue": {"type": "STRING", "description": "Journal or conference name"},
                    "authors": {"type": "STRING", "description": "Full author list, comma-separated"},
                    "url": {"type": "STRING", "description": "DOI or paper URL"},
                },
                "required": ["title", "abstract", "year"],
            },
        },
    },
    "required": ["scholar_name", "papers"],
}

# Perplexity uses a slightly different JSON schema format
PERPLEXITY_SCHEMA = {
    "type": "object",
    "properties": {
        "scholar_name": {"type": "string"},
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "abstract": {"type": "string"},
                    "year": {"type": "string"},
                    "citations": {"type": "string"},
                    "venue": {"type": "string"},
                    "authors": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["title", "abstract", "year"],
            },
        },
    },
    "required": ["scholar_name", "papers"],
}

SYSTEM_INSTRUCTION = (
    "You are a research paper database. Return accurate, verified paper information. "
    "Only include papers you are confident exist. Return results as structured JSON."
)


# ── Perplexity (sonar-pro) ──────────────────────────────────────────────────

def fetch_perplexity(scholar_name, institution, num_papers):
    from openai import OpenAI

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("  [SKIP] PERPLEXITY_API_KEY not set")
        return None, None

    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    prompt = render_prompt(
        "fetch_papers",
        scholar_name=scholar_name,
        institution=institution,
        num_papers=num_papers,
    )

    print(f"  Calling Perplexity sonar-pro (academic mode)...")
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": PERPLEXITY_SCHEMA},
        },
        extra_body={
            "search_mode": "academic",
            "web_search_options": {"search_context_size": "high"},
        },
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    papers_count = len(result.get("papers", []))
    print(f"  Perplexity returned {papers_count} papers")
    if papers_count == 0:
        print(f"  [DEBUG] Raw response: {content[:500]}")

    citations = getattr(response, "citations", []) or []
    return result, citations


# ── Gemini 3 Flash Preview (grounded search) ───────────────────────────────

def fetch_gemini(scholar_name, institution, num_papers):
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("  [SKIP] GOOGLE_API_KEY / GEMINI_API_KEY not set")
        return None, None

    client = genai.Client(api_key=api_key)
    prompt = render_prompt(
        "fetch_papers",
        scholar_name=scholar_name,
        institution=institution,
        num_papers=num_papers,
    )

    # Explicitly tell Gemini to search online for papers
    # Paraphrase abstracts in scientific tone to avoid RECITATION safety blocks
    full_prompt = (
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
        f"- abstract: Write a faithful scientific paraphrase of the paper's abstract. "
        f"Preserve all key findings, methods, and conclusions. Use formal academic tone "
        f"matching the style of the original. Do not copy verbatim — closely rephrase "
        f"while retaining scientific precision and completeness.\n"
        f"- year: publication year\n"
        f"- citations: approximate citation count (or '0' if unknown)\n"
        f"- venue: journal or conference name\n"
        f"- authors: full author list as a comma-separated string\n"
        f"- url: DOI or paper URL if available\n\n"
        f"Return ONLY the JSON, no other text."
    )

    print(f"  Calling Gemini gemini-3-flash-preview (grounded search)...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    # Debug: print raw response if text is None
    if response.text is None:
        print(f"  [DEBUG] response.text is None")
        print(f"  [DEBUG] candidates: {response.candidates}")
        for candidate in response.candidates:
            print(f"  [DEBUG] finish_reason: {candidate.finish_reason}")
            if candidate.content:
                for part in candidate.content.parts:
                    print(f"  [DEBUG] part: {part}")
        return None, None

    # Parse JSON from response text (may be wrapped in markdown code block)
    text = response.text.strip()
    if text.startswith("```"):
        # Strip markdown code fence
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    parsed = json.loads(text)
    # Normalize: Gemini may return a list or an object
    if isinstance(parsed, list):
        result = {"scholar_name": scholar_name, "papers": parsed}
    elif isinstance(parsed, dict) and "papers" not in parsed:
        # Single paper object?
        result = {"scholar_name": scholar_name, "papers": [parsed]}
    else:
        result = parsed

    # Extract grounding metadata
    grounding_sources = []
    candidate = response.candidates[0]
    if candidate.grounding_metadata:
        meta = candidate.grounding_metadata
        if meta.grounding_chunks:
            for chunk in meta.grounding_chunks:
                if chunk.web:
                    grounding_sources.append({
                        "title": chunk.web.title,
                        "url": chunk.web.uri,
                    })
        if meta.web_search_queries:
            print(f"  Gemini search queries: {meta.web_search_queries}")

    return result, grounding_sources


# ── Display ─────────────────────────────────────────────────────────────────

def print_papers(label, result, sources):
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")

    if result is None:
        print("  (no results)")
        return

    papers = result.get("papers", [])
    print(f"  Found {len(papers)} papers:\n")

    for i, p in enumerate(papers, 1):
        title = p.get("title", "?")
        year = p.get("year", "?")
        venue = p.get("venue", "?")
        authors = p.get("authors", "?")
        url = p.get("url", "")
        abstract = p.get("abstract", "")

        print(f"  [{i}] {title}")
        print(f"      Year: {year}  |  Venue: {venue}")
        print(f"      Authors: {authors}")
        if url:
            print(f"      URL: {url}")
        if abstract:
            # Truncate long abstracts for display
            display_abs = abstract[:300] + "..." if len(abstract) > 300 else abstract
            print(f"      Abstract: {display_abs}")
        print()

    if sources:
        print(f"  --- Sources / Citations ---")
        for s in sources[:10]:
            if isinstance(s, dict):
                print(f"    - {s.get('title', '')}: {s.get('url', '')}")
            else:
                print(f"    - {s}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare grounded search: Perplexity sonar-pro vs Gemini 3 Flash"
    )
    parser.add_argument("--name", default="Mick Bonner", help="Scholar name")
    parser.add_argument("--institution", default="Johns Hopkins University", help="Institution")
    parser.add_argument("--papers", type=int, default=5, help="Number of papers")
    parser.add_argument("--output", type=str, default=None, help="Save JSON output to file")
    args = parser.parse_args()

    print(f"\nComparing grounded search factuality")
    print(f"Scholar: {args.name} @ {args.institution}")
    print(f"Papers requested: {args.papers}\n")
    print(f"{'-'*80}")

    # Fetch from both sources
    plex_result, plex_citations = fetch_perplexity(args.name, args.institution, args.papers)
    gemini_result, gemini_sources = fetch_gemini(args.name, args.institution, args.papers)

    # Display results
    print_papers("PERPLEXITY sonar-pro (academic mode)", plex_result, plex_citations)
    print_papers("GEMINI gemini-3-flash-preview (grounded Google Search)", gemini_result, gemini_sources)

    # Summary comparison
    print(f"\n{'='*80}")
    print(f"  COMPARISON SUMMARY")
    print(f"{'='*80}")

    plex_papers = plex_result.get("papers", []) if plex_result else []
    gem_papers = gemini_result.get("papers", []) if gemini_result else []

    print(f"  Perplexity: {len(plex_papers)} papers returned")
    print(f"  Gemini:     {len(gem_papers)} papers returned")

    # Find overlapping titles (fuzzy match by first 40 chars lowercase)
    def norm(t):
        return t.lower().strip()[:40]

    plex_titles = {norm(p["title"]) for p in plex_papers if "title" in p}
    gem_titles = {norm(p["title"]) for p in gem_papers if "title" in p}
    overlap = plex_titles & gem_titles

    print(f"  Overlapping titles (first 40 chars): {len(overlap)}")
    if overlap:
        for t in overlap:
            print(f"    - {t}...")

    # Save raw output
    if args.output:
        out = {
            "scholar_name": args.name,
            "institution": args.institution,
            "perplexity": {"papers": plex_papers, "citations": plex_citations or []},
            "gemini": {"papers": gem_papers, "sources": gemini_sources or []},
        }
        with open(args.output, "w") as f:
            json.dump(out, f, indent=2)
        print(f"\n  Saved to {args.output}")

    print()


if __name__ == "__main__":
    main()
