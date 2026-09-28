"""
Map each PI's institution to a country, for the frontend's Country filter.

Gemini 3.8 Flash classifies institution names in batches (structured JSON output).
Results go to data/source/institution_countries.json (tracked in git), which the
build step reads. Only institutions missing from that file are sent to the model,
so re-running is cheap; edit the JSON by hand to fix a wrong country.

Usage:
    uv run -m scholar_board.pipeline.countries --dry-run   # List unmapped institutions
    uv run -m scholar_board.pipeline.countries             # Classify unmapped institutions
    uv run -m scholar_board.pipeline.countries --all       # Re-classify every institution
"""

import argparse
import json
from collections import Counter

from scholar_board.config import INSTITUTION_COUNTRIES_PATH
from scholar_board.db import load_scholars
from scholar_board.gemini import FLASH_MODEL, generate_text, get_client, parse_json_response
from scholar_board.prompt_loader import render_prompt

BATCH_SIZE = 60

RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "institution": {"type": "string"},
            "country": {"type": "string"},
        },
        "required": ["institution", "country"],
    },
}


def load_countries() -> dict[str, str]:
    if not INSTITUTION_COUNTRIES_PATH.exists():
        return {}
    with open(INSTITUTION_COUNTRIES_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_countries(countries: dict[str, str]) -> None:
    ordered = dict(sorted(countries.items(), key=lambda kv: kv[0].lower()))
    with open(INSTITUTION_COUNTRIES_PATH, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2, ensure_ascii=False)
        f.write("\n")


def classify_batch(institutions: list[str], client) -> dict[str, str]:
    prompt = render_prompt("classify_country", institutions="\n".join(f"- {i}" for i in institutions))
    text = generate_text(prompt, model=FLASH_MODEL, response_schema=RESPONSE_SCHEMA, client=client)
    if not text:
        return {}
    wanted = set(institutions)
    return {
        r["institution"]: r["country"].strip()
        for r in parse_json_response(text)
        if r.get("institution") in wanted and r.get("country", "").strip()
    }


def main():
    parser = argparse.ArgumentParser(description="Map PI institutions to countries")
    parser.add_argument("--dry-run", action="store_true", help="List unmapped institutions without API calls")
    parser.add_argument("--all", action="store_true", help="Re-classify every institution, not just unmapped ones")
    args = parser.parse_args()

    institutions = sorted({s["scholar_institution"] for s in load_scholars(is_pi_only=True)} - {""})
    countries = {} if args.all else load_countries()
    todo = [i for i in institutions if i not in countries]
    print(f"{len(institutions)} PI institutions, {len(todo)} to classify")

    if args.dry_run:
        for i in todo:
            print(f"  {i}")
        return
    if not todo:
        return

    client = get_client()
    for start in range(0, len(todo), BATCH_SIZE):
        batch = todo[start:start + BATCH_SIZE]
        result = classify_batch(batch, client)
        countries.update(result)
        print(f"  batch {start // BATCH_SIZE + 1}: {len(result)}/{len(batch)} classified")
        save_countries(countries)

    missing = [i for i in institutions if i not in countries]
    if missing:
        print(f"\nStill unmapped ({len(missing)}) — re-run or add by hand:")
        for i in missing:
            print(f"  {i}")

    counts = Counter(countries[i] for i in institutions if i in countries)
    print(f"\n{len(counts)} countries:")
    for country, n in counts.most_common():
        print(f"  {country:30s} {n} institutions")


if __name__ == "__main__":
    main()
