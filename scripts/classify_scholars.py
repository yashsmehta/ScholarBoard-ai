#!/usr/bin/env python3
"""Classify scholars as PI-level vision science researchers using Gemini Flash.

For each scholar, aggregates all available data (bio, papers, citations, institution)
and asks Gemini Flash to determine whether they are a PI-level researcher in vision
science or not (e.g. grad student, postdoc, wrong field).

Results are saved to data/scholar_classifications.csv with columns:
  scholar_id, scholar_name, is_pi, confidence, reason

Usage:
    .venv/bin/python3 scripts/classify_scholars.py
    .venv/bin/python3 scripts/classify_scholars.py --limit 20
    .venv/bin/python3 scripts/classify_scholars.py --dry-run
    .venv/bin/python3 scripts/classify_scholars.py --workers 10
"""

import argparse
import csv
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scholar_board.gemini import get_client, parse_json_response
from scholar_board.prompt_loader import render_prompt
from google.genai import types

OUTPUT_PATH = PROJECT_ROOT / "data" / "scholar_classifications.csv"
PAPERS_DIR = PROJECT_ROOT / "data" / "pipeline" / "scholar_papers"
INFO_DIR = PROJECT_ROOT / "data" / "pipeline" / "scholar_profiles"
CITATIONS_CSV = PROJECT_ROOT / "data" / "scholar_citations.csv"
VSS_CSV = PROJECT_ROOT / "data" / "source" / "vss_data.csv"


def load_vss_scholars() -> list[dict]:
    """Load unique scholars from vss_data.csv."""
    seen = set()
    scholars = []
    with open(VSS_CSV) as f:
        for row in csv.DictReader(f):
            sid = row["scholar_id"]
            if sid not in seen:
                seen.add(sid)
                scholars.append({
                    "id": sid,
                    "name": row["scholar_name"],
                    "institution": row.get("scholar_institution", ""),
                    "department": row.get("scholar_department", ""),
                })
    return scholars


def load_citations() -> dict[str, dict]:
    """Load citation data keyed by scholar_id."""
    if not CITATIONS_CSV.exists():
        return {}
    out = {}
    with open(CITATIONS_CSV) as f:
        for row in csv.DictReader(f):
            out[row["scholar_id"]] = {
                "total_citations": row.get("total_citations", ""),
                "h_index": row.get("h_index", ""),
            }
    return out


def load_papers(scholar_id: str, scholar_name: str) -> list[dict]:
    """Load fetched papers for a scholar from scholar_papers/."""
    if not PAPERS_DIR.exists():
        return []
    safe_name = scholar_name.replace(" ", "_").lower()
    # Try exact filename match first, then glob
    candidates = list(PAPERS_DIR.glob(f"{scholar_id}_*.json"))
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("papers", [])
        except Exception:
            pass
    return []


def load_bio(scholar_id: str, scholar_name: str) -> str:
    """Load bio from perplexity_info/."""
    if not INFO_DIR.exists():
        return ""
    candidates = list(INFO_DIR.glob(f"{scholar_id}_*.json"))
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("bio", "")
        except Exception:
            pass
    return ""


def format_papers_summary(papers: list[dict]) -> str:
    """Format papers list into a readable summary for the prompt."""
    if not papers:
        return "None found."
    lines = []
    for p in papers[:5]:  # cap at 5 for prompt length
        title = p.get("title", "Unknown title")
        year = p.get("year", "?")
        venue = p.get("venue", "?")
        lines.append(f"- [{year}] {title} ({venue})")
    return "\n".join(lines)


def classify_scholar(scholar: dict, citations_data: dict) -> dict:
    """Call Gemini Flash to classify a single scholar as PI or not."""
    sid = scholar["id"]
    name = scholar["name"]
    institution = scholar["institution"] or "Unknown"
    department = scholar["department"] or ""
    if department in ("N/A", "n/a"):
        department = ""

    papers = load_papers(sid, name)
    bio = load_bio(sid, name)
    cit = citations_data.get(sid, {})
    total_citations = cit.get("total_citations", "") or "Unknown"
    h_index = cit.get("h_index", "") or "Unknown"

    papers_summary = format_papers_summary(papers)

    prompt = render_prompt(
        "classify_pi",
        scholar_name=name,
        institution=institution,
        department=department or "Unknown",
        bio=bio or "Not available.",
        papers_summary=papers_summary,
        total_citations=total_citations,
        h_index=h_index,
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "is_pi":       {"type": "BOOLEAN", "description": "True if PI-level vision science researcher"},
            "confidence":  {"type": "STRING",  "enum": ["high", "medium", "low"]},
            "reason":      {"type": "STRING",  "description": "1-2 sentence justification"},
        },
        "required": ["is_pi", "confidence", "reason"],
    }

    client = get_client()
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a precise academic classifier.",
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        if response.text is None:
            return {"is_pi": None, "confidence": "low", "reason": "Empty response from Gemini"}

        result = parse_json_response(response.text)
        return {
            "is_pi": result.get("is_pi"),
            "confidence": result.get("confidence", "low"),
            "reason": result.get("reason", ""),
        }
    except Exception as e:
        return {"is_pi": None, "confidence": "low", "reason": f"Error: {e}"}


def _process_scholar(scholar, index, total, citations_data, lock, results, counters):
    """Worker function for a single scholar."""
    name = scholar["name"]
    sid = scholar["id"]

    classification = classify_scholar(scholar, citations_data)
    is_pi = classification["is_pi"]
    confidence = classification["confidence"]
    reason = classification["reason"]

    row = {
        "scholar_id": sid,
        "scholar_name": name,
        "institution": scholar["institution"],
        "is_pi": str(is_pi) if is_pi is not None else "",
        "confidence": confidence,
        "reason": reason,
    }

    with lock:
        results.append(row)
        if is_pi is True:
            counters["pi"] += 1
            tag = f"PI [{confidence}]"
        elif is_pi is False:
            counters["not_pi"] += 1
            tag = f"NOT PI [{confidence}] — {reason[:60]}"
        else:
            counters["unknown"] += 1
            tag = f"UNKNOWN"
        print(f"[{index + 1}/{total}] {name:<35} {tag}")


def main():
    parser = argparse.ArgumentParser(
        description="Classify scholars as PI-level vision science researchers"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Max scholars to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--workers", type=int, default=10,
                        help="Number of parallel workers (default: 10)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip scholars already classified")
    args = parser.parse_args()

    scholars = load_vss_scholars()
    citations_data = load_citations()
    print(f"Loaded {len(scholars)} scholars, {len(citations_data)} with citation data")

    # Skip already classified
    existing_ids = set()
    if args.skip_existing and OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            for row in csv.DictReader(f):
                existing_ids.add(row["scholar_id"])
        if existing_ids:
            scholars = [s for s in scholars if s["id"] not in existing_ids]
            print(f"Skipping {len(existing_ids)} already-classified scholars")

    if args.limit:
        scholars = scholars[:args.limit]

    print(f"Classifying {len(scholars)} scholars with {args.workers} workers\n")

    if args.dry_run:
        for i, s in enumerate(scholars[:10]):
            cit = citations_data.get(s["id"], {})
            papers = load_papers(s["id"], s["name"])
            bio = load_bio(s["id"], s["name"])
            print(f"  [{i+1}] {s['name']}")
            print(f"       inst={s['institution'][:50]}")
            print(f"       citations={cit.get('total_citations','?')}, h={cit.get('h_index','?')}")
            print(f"       papers={len(papers)}, bio={'yes' if bio else 'no'}")
        print(f"\n[DRY RUN] Would classify {len(scholars)} scholars.")
        return

    lock = threading.Lock()
    results = []
    counters = {"pi": 0, "not_pi": 0, "unknown": 0}
    total = len(scholars)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                _process_scholar, s, i, total, citations_data, lock, results, counters
            ): s
            for i, s in enumerate(scholars)
        }
        for future in as_completed(futures):
            exc = future.exception()
            if exc is not None:
                scholar = futures[future]
                print(f"  Unexpected error for {scholar['name']}: {exc}")

    # Sort by scholar_id and merge with existing
    results.sort(key=lambda r: r["scholar_id"])

    if existing_ids and OUTPUT_PATH.exists():
        existing_rows = list(csv.DictReader(open(OUTPUT_PATH)))
        id_to_row = {r["scholar_id"]: r for r in existing_rows}
        for r in results:
            id_to_row[r["scholar_id"]] = r
        results = sorted(id_to_row.values(), key=lambda r: r["scholar_id"])

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "scholar_id", "scholar_name", "institution", "is_pi", "confidence", "reason"
        ])
        writer.writeheader()
        writer.writerows(results)

    total_classified = counters["pi"] + counters["not_pi"] + counters["unknown"]
    print(f"\n--- Summary ---")
    print(f"PI:       {counters['pi']}/{total_classified}")
    print(f"Not PI:   {counters['not_pi']}/{total_classified}")
    print(f"Unknown:  {counters['unknown']}/{total_classified}")
    print(f"Output:   {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
