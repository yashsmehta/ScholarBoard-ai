"""
Assign Vision Sciences Society (VSS) topic areas to scholars with an LLM.

For each PI, Gemini 3 Flash reads the researcher's profile (bio, stated research
area, AI-distilled research direction, and recent papers) and picks the single
best-fitting VSS topic area as `primary`, plus up to two `secondary` areas.
This replaces the earlier embedding cosine-similarity approach — a language model
judges fit directly, which handles the boundary cases (mechanism vs. application,
computational vs. empirical) far better than nearest-neighbor on embeddings.

The {primary_subfield, subfields:[{subfield, score}]} output shape is unchanged,
so build + frontend consume it exactly as before (score is a confidence weight:
1.0 primary, 0.5 secondary).

Usage:
    uv run -m scholar_board.pipeline.subfields --dry-run            # Preview
    uv run -m scholar_board.pipeline.subfields                      # Run all PIs
    uv run -m scholar_board.pipeline.subfields --limit 5            # First 5
    uv run -m scholar_board.pipeline.subfields --scholar-id 0459    # Single scholar
    uv run -m scholar_board.pipeline.subfields --workers 25         # Parallelism
"""

import json
import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from scholar_board.config import SUBFIELDS_DEF_PATH, SUBFIELDS_PATH, load_paper_texts
from scholar_board.gemini import get_client, generate_text, parse_json_response
from scholar_board.prompt_loader import render_prompt
from scholar_board.db import get_connection, init_db, upsert_subfields

SECONDARY_SCORE = 0.5
PRIMARY_SCORE = 1.0


def load_subfields() -> list[dict]:
    """Load VSS topic-area definitions from data/source/subfields.json."""
    with open(SUBFIELDS_DEF_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pi_scholars() -> list[dict]:
    """Load PI scholars with the profile fields used for classification."""
    conn = get_connection()
    init_db(conn)
    rows = conn.execute(
        "SELECT id, name, institution, main_research_area, bio, research_direction "
        "FROM scholars WHERE is_pi = 1 ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def build_response_schema(names: list[str]) -> dict:
    """JSON schema constraining primary/secondary to the exact topic names."""
    return {
        "type": "object",
        "properties": {
            "primary": {"type": "string", "enum": names},
            "secondary": {"type": "array", "items": {"type": "string", "enum": names}},
            "reasoning": {"type": "string"},
        },
        "required": ["primary"],
    }


def classify_scholar(scholar: dict, subfields: list[dict], names: set[str],
                     schema: dict, client) -> dict | None:
    """Classify one scholar into VSS topic areas. Returns assignment dict or None."""
    sid = scholar["id"]
    papers_text = load_paper_texts(sid) or "(no papers available)"

    subfields_block = "\n".join(
        f"- {sf['name']}: {sf['description']}" for sf in subfields
    )
    prompt = render_prompt(
        "classify_subfield",
        n_subfields=len(subfields),
        subfields_block=subfields_block,
        scholar_name=scholar["name"],
        institution=scholar.get("institution") or "Unknown",
        main_research_area=scholar.get("main_research_area") or "Unknown",
        bio=scholar.get("bio") or "(no bio)",
        research_direction=scholar.get("research_direction") or "(no research direction)",
        papers_text=papers_text,
    )

    try:
        text = generate_text(prompt, model="gemini-3-flash-preview",
                             response_schema=schema, client=client)
        if not text:
            return None
        result = parse_json_response(text)
    except Exception as e:
        print(f"  ERROR {sid} {scholar['name']}: {e}")
        return None

    primary = result.get("primary")
    if primary not in names:
        print(f"  SKIP {sid} {scholar['name']}: invalid primary {primary!r}")
        return None

    # Keep valid, de-duplicated secondaries (max 2), excluding the primary.
    secondary = []
    for s in result.get("secondary") or []:
        if s in names and s != primary and s not in secondary:
            secondary.append(s)
        if len(secondary) == 2:
            break

    tags = [{"subfield": primary, "score": PRIMARY_SCORE}]
    tags += [{"subfield": s, "score": SECONDARY_SCORE} for s in secondary]
    return {"primary_subfield": primary, "subfields": tags}


def print_summary(assignments: dict, subfields: list[dict]) -> None:
    """Print distribution of primary topic-area assignments."""
    primary_counts = Counter(a["primary_subfield"] for a in assignments.values())
    print(f"\nPrimary topic-area distribution ({len(assignments)} scholars):")
    for sf in sorted(subfields, key=lambda s: primary_counts.get(s["name"], 0), reverse=True):
        count = primary_counts.get(sf["name"], 0)
        print(f"  {sf['name']:32s} {count:4d}  {'#' * (count // 2)}")


def main():
    parser = argparse.ArgumentParser(
        description="Assign VSS topic areas to scholars via an LLM classifier"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    parser.add_argument("--limit", type=int, default=None, help="Only classify the first N scholars")
    parser.add_argument("--scholar-id", type=str, default=None, help="Classify a single scholar by ID")
    parser.add_argument("--workers", type=int, default=25, help="Parallel API workers (default: 25)")
    args = parser.parse_args()

    if not SUBFIELDS_DEF_PATH.exists():
        print(f"Error: Topic-area definitions not found at {SUBFIELDS_DEF_PATH}")
        sys.exit(1)

    subfields = load_subfields()
    names = {sf["name"] for sf in subfields}
    schema = build_response_schema([sf["name"] for sf in subfields])
    print(f"Loaded {len(subfields)} VSS topic areas")

    scholars = load_pi_scholars()
    if args.scholar_id:
        scholars = [s for s in scholars if s["id"] == args.scholar_id]
    if args.limit:
        scholars = scholars[: args.limit]
    print(f"Classifying {len(scholars)} PI scholars (Gemini 3 Flash, {args.workers} workers)")

    if not scholars:
        print("No scholars to classify.")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would classify each scholar into one primary + up to two secondary topics.")
        print(f"  Example scholar: {scholars[0]['name']} ({scholars[0]['id']})")
        return

    client = get_client()
    assignments: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(classify_scholar, s, subfields, names, schema, client): s
            for s in scholars
        }
        done = 0
        for fut in as_completed(futures):
            s = futures[fut]
            assignment = fut.result()
            done += 1
            if assignment:
                assignments[s["id"]] = assignment
            if done % 25 == 0 or done == len(scholars):
                print(f"  {done}/{len(scholars)} classified ({len(assignments)} ok)")

    SUBFIELDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBFIELDS_PATH, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(assignments)} assignments to {SUBFIELDS_PATH}")

    conn = get_connection()
    init_db(conn)
    for sid, a in assignments.items():
        upsert_subfields(conn, sid, a["primary_subfield"], a["subfields"])
    conn.close()
    print(f"Wrote {len(assignments)} scholars to DB")

    print_summary(assignments, subfields)

    print("\nExample assignments:")
    for sid, a in list(assignments.items())[:5]:
        tags = ", ".join(t["subfield"] for t in a["subfields"])
        print(f"  {sid}: {tags}")


if __name__ == "__main__":
    main()
