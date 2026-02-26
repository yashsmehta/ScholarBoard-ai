"""
Seed the SQLite DB with all researchers from vss_data.csv + extra_researchers.csv.

Deduplication when merging extra into VSS:
  1. Exact normalized name match  → skip (definite duplicate)
  2. Fuzzy name score >= 90       → skip (very likely same person)
  3. Fuzzy name score 70–89       → Gemini decides → skip if same person
  4. Score < 70                   → insert as new

Usage:
    uv run -m scholar_board.pipeline.seed
    uv run -m scholar_board.pipeline.seed --dry-run
"""

import argparse
import csv
import re
import unicodedata

from thefuzz import fuzz
from google.genai import types

from scholar_board.config import CSV_PATH, EXTRA_RESEARCHERS_PATH
from scholar_board.db import get_connection, init_db
from scholar_board.gemini import get_client, parse_json_response


def _normalize(name: str) -> str:
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w\s]", "", name).lower().strip()


def _best_match(name: str, pool: list[dict]) -> tuple[int, dict | None]:
    """Return (score, best_matching_scholar) against a pool of {name, ...} dicts."""
    best_score, best = 0, None
    norm = _normalize(name)
    for candidate in pool:
        score = fuzz.token_sort_ratio(norm, _normalize(candidate["name"]))
        if score > best_score:
            best_score, best = score, candidate
    return best_score, best


def _gemini_same_person(name1, inst1, name2, inst2) -> bool:
    """Ask Gemini Flash whether two name/institution pairs are the same researcher."""
    try:
        response = get_client().models.generate_content(
            model="gemini-3-flash-preview",
            contents=(
                f"Are these two entries the same researcher?\n"
                f"A: {name1} — {inst1}\n"
                f"B: {name2} — {inst2}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {"same_person": {"type": "BOOLEAN"}},
                    "required": ["same_person"],
                },
            ),
        )
        return parse_json_response(response.text).get("same_person", False)
    except Exception as e:
        print(f"    Gemini timeout/error for '{name1}' vs '{name2}': {e} — treating as different")
        return False


def _load_vss() -> list[dict]:
    seen, out = set(), []
    with open(CSV_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row["scholar_id"].strip().zfill(4)
            if sid not in seen:
                seen.add(sid)
                out.append({
                    "id": sid,
                    "name": row["scholar_name"].strip(),
                    "institution": row.get("scholar_institution", "").strip(),
                    "source": "vss",
                })
    return out


def _load_extra() -> list[dict]:
    if not EXTRA_RESEARCHERS_PATH.exists():
        return []
    with open(EXTRA_RESEARCHERS_PATH, encoding="utf-8") as f:
        return [
            {
                "id": row["scholar_id"],
                "name": row["scholar_name"].strip(),
                "institution": row.get("scholar_institution", "").strip(),
                "source": "gemini",
            }
            for row in csv.DictReader(f)
        ]


def main():
    parser = argparse.ArgumentParser(description="Seed scholars DB from CSV sources")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    vss = _load_vss()
    extra = _load_extra()
    print(f"VSS:   {len(vss)} scholars")
    print(f"Extra: {len(extra)} scholars\n")

    # Deduplicate extra against VSS
    to_insert, counts = [], {"exact": 0, "fuzzy": 0, "gemini": 0}
    for r in extra:
        score, match = _best_match(r["name"], vss)

        if score == 100:
            counts["exact"] += 1
            continue

        if score >= 90:
            counts["fuzzy"] += 1
            print(f"  FUZZY  ({score:3d}) {r['name']} ≈ {match['name']}")
            continue

        if score >= 70:
            same = _gemini_same_person(r["name"], r["institution"], match["name"], match["institution"])
            if same:
                counts["gemini"] += 1
                print(f"  GEMINI ({score:3d}) {r['name']} = {match['name']}")
                continue

        to_insert.append(r)

    total = len(vss) + len(to_insert)
    print(f"\nSkipped: {counts['exact']} exact, {counts['fuzzy']} fuzzy, {counts['gemini']} Gemini-verified")
    print(f"Seeding: {len(vss)} VSS + {len(to_insert)} new extra = {total} total\n")

    if args.dry_run:
        print("[DRY RUN] No changes written.")
        return

    conn = get_connection()
    init_db(conn)

    inserted = 0
    for r in vss + to_insert:
        cur = conn.execute(
            "INSERT OR IGNORE INTO scholars (id, name, institution, source) VALUES (?, ?, ?, ?)",
            (r["id"], r["name"], r["institution"], r["source"]),
        )
        inserted += cur.rowcount

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} new scholars into DB.")


if __name__ == "__main__":
    main()
