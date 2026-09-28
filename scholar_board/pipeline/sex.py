"""
Estimate each PI's sex (female / male / unknown) for aggregate counts.

Gemini 3.8 Flash classifies PIs in batches from their name, institution and bio
(structured JSON output). Pronouns in the bio win; otherwise the first name decides,
and ambiguous cases are left "unknown". `--resolve-unknown` then looks each "unknown" PI
up with Google Search grounding for explicit evidence (pronouns on a lab/faculty page).

Private data: results go to the DB (`scholars.sex`) and
data/pipeline/scholar_sex.json only — never to scholars.json or the frontend.
Manual fixes go in data/source/sex_overrides.json ({"<id>": "female"|"male"}; untracked,
since the repo is public) and always win over the classifier.

Not one of the 13 map-pipeline steps; run it on demand.

Usage:
    uv run -m scholar_board.pipeline.sex --dry-run   # List unclassified PIs
    uv run -m scholar_board.pipeline.sex             # Classify unclassified PIs
    uv run -m scholar_board.pipeline.sex --all       # Re-classify every PI
    uv run -m scholar_board.pipeline.sex --stats     # Print counts only
    uv run -m scholar_board.pipeline.sex --resolve-unknown   # Grounded search for "unknown" PIs
"""

import argparse
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from scholar_board.config import SEX_OVERRIDES_PATH, SEX_PATH
from scholar_board.db import get_connection, init_db, upsert_sex
from scholar_board.gemini import FLASH_MODEL, generate_text, get_client, parse_json_response
from scholar_board.prompt_loader import render_prompt

BATCH_SIZE = 50
RESOLVE_WORKERS = 8  # grounded Flash calls hit Vertex 429s above ~8 parallel workers
LABELS = ["female", "male", "unknown"]

RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "sex": {"type": "string", "enum": LABELS},
        },
        "required": ["id", "sex"],
    },
}


def load_json(path) -> dict[str, str]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_results(results: dict[str, str]) -> None:
    with open(SEX_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(results.items())), f, indent=2)
        f.write("\n")


def load_pis(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, institution, bio, sex FROM scholars WHERE is_pi = 1 ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def classify_batch(pis: list[dict], client) -> dict[str, str]:
    lines = "\n".join(
        f"- id={p['id']} | {p['name']} | {p['institution'] or ''} | bio: {(p['bio'] or '')[:400]}"
        for p in pis
    )
    text = generate_text(render_prompt("classify_sex", researchers=lines),
                         model=FLASH_MODEL, response_schema=RESPONSE_SCHEMA, client=client)
    if not text:
        return {}
    wanted = {p["id"] for p in pis}
    return {r["id"]: r["sex"] for r in parse_json_response(text)
            if r.get("id") in wanted and r.get("sex") in LABELS}


def resolve_one(p: dict, client) -> tuple[str, dict | None]:
    prompt = render_prompt("resolve_sex", scholar_name=p["name"], institution=p["institution"] or "")
    for attempt in range(4):
        try:
            text = generate_text(prompt, model=FLASH_MODEL, grounded=True, client=client)
            r = parse_json_response(text) if text else None
            return p["id"], r if isinstance(r, dict) and r.get("sex") in LABELS else None
        except Exception as e:
            if attempt == 3:
                print(f"  {p['id']} {p['name']}: {e}")
            time.sleep(2 ** attempt * 5)
    return p["id"], None


def resolve_unknown(pis: list[dict], results: dict[str, str], client) -> None:
    todo = [p for p in pis if results.get(p["id"]) == "unknown"]
    print(f"Resolving {len(todo)} unknown PIs with grounded search")
    with ThreadPoolExecutor(RESOLVE_WORKERS) as pool:
        for sid, r in pool.map(lambda p: resolve_one(p, client), todo):
            name = next(p["name"] for p in todo if p["id"] == sid)
            if r and r["sex"] != "unknown":
                results[sid] = r["sex"]
            print(f"  {sid} {name:28s} {r['sex'] if r else 'error':8s} {(r or {}).get('evidence', '')[:90]}")
    save_results(results)


def print_stats(conn) -> None:
    counts = Counter(r["sex"] or "unclassified" for r in load_pis(conn))
    total = sum(counts.values())
    print(f"\n{total} PIs on the map:")
    for label in LABELS + ["unclassified"]:
        if counts[label]:
            print(f"  {label:13s} {counts[label]:4d}  ({counts[label] / total:.1%})")
    known = counts["female"] + counts["male"]
    if known:
        print(f"  female share of known: {counts['female'] / known:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Estimate PI sex for aggregate counts (private)")
    parser.add_argument("--dry-run", action="store_true", help="List unclassified PIs without API calls")
    parser.add_argument("--all", action="store_true", help="Re-classify every PI")
    parser.add_argument("--stats", action="store_true", help="Print counts and exit")
    parser.add_argument("--resolve-unknown", action="store_true",
                        help="Look up PIs classified 'unknown' with grounded search")
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)
    if args.stats:
        print_stats(conn)
        return

    pis = load_pis(conn)
    results = {} if args.all else load_json(SEX_PATH)
    todo = [p for p in pis if p["id"] not in results]
    print(f"{len(pis)} PIs, {len(todo)} to classify")

    if args.dry_run:
        for p in todo:
            print(f"  {p['id']}  {p['name']}")
        return

    client = get_client() if todo else None
    for start in range(0, len(todo), BATCH_SIZE):
        batch = todo[start:start + BATCH_SIZE]
        result = classify_batch(batch, client)
        results.update(result)
        save_results(results)
        print(f"  batch {start // BATCH_SIZE + 1}: {len(result)}/{len(batch)} classified")
    if args.resolve_unknown:
        resolve_unknown(pis, results, client or get_client())

    overrides = load_json(SEX_OVERRIDES_PATH)
    for p in pis:
        sex = overrides.get(p["id"], results.get(p["id"]))
        if sex != p["sex"]:
            upsert_sex(conn, p["id"], sex)

    missing = [p for p in pis if p["id"] not in results and p["id"] not in overrides]
    if missing:
        print(f"\nStill unclassified ({len(missing)}) — re-run:")
        for p in missing:
            print(f"  {p['id']}  {p['name']}")
    print_stats(conn)


if __name__ == "__main__":
    main()
