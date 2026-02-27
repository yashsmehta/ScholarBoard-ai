"""
Generate field-level research direction summaries for each vision science subfield.

For each subfield, collects the AI-generated research direction paragraphs of all
PI researchers whose primary_subfield matches, then uses Gemini 3.1 Pro (HIGH thinking)
to synthesize a structured field-level summary with five sections:
  1. Overview
  2. Active Research Themes
  3. Open Questions
  4. Methods & Approaches
  5. Emerging Directions

Output: data/build/field_directions.json (served as static data to the frontend)

Usage:
    uv run -m scholar_board.pipeline.field_directions --dry-run
    uv run -m scholar_board.pipeline.field_directions --subfield "Brain-AI Alignment"
    uv run -m scholar_board.pipeline.field_directions
"""

import json
import argparse
import sys
from pathlib import Path

from google.genai import types

from scholar_board.config import SUBFIELDS_DEF_PATH, BUILD_DIR
from scholar_board.gemini import get_client, parse_json_response
from scholar_board.db import get_connection, init_db

FIELD_DIRECTIONS_PATH = BUILD_DIR / "field_directions.json"


def load_subfield_definitions() -> list[dict]:
    with open(SUBFIELDS_DEF_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_researchers_for_subfield(subfield_name: str) -> list[dict]:
    """Load name + research_direction for all PIs whose primary_subfield matches."""
    conn = get_connection()
    init_db(conn)
    rows = conn.execute(
        """
        SELECT id, name, research_direction
        FROM scholars
        WHERE is_pi = 1
          AND primary_subfield = ?
          AND research_direction IS NOT NULL
          AND research_direction != ''
        ORDER BY id
        """,
        (subfield_name,),
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"], "direction": r["research_direction"]} for r in rows]


def build_prompt(subfield_name: str, subfield_description: str, researchers: list[dict]) -> str:
    """Build the synthesis prompt from the prompt template."""
    parts = []
    for r in researchers:
        parts.append(f"**{r['name']}**\n{r['direction']}")
    researcher_directions = "\n\n---\n\n".join(parts)

    template_path = Path(__file__).parent.parent / "prompts" / "field_directions.md"
    template = template_path.read_text(encoding="utf-8")

    return (
        template
        .replace("{subfield_name}", subfield_name)
        .replace("{subfield_description}", subfield_description)
        .replace("{n_researchers}", str(len(researchers)))
        .replace("{researcher_directions}", researcher_directions)
    )


def generate_field_summary(client, subfield_name: str, subfield_description: str,
                            researchers: list[dict]) -> dict | None:
    """Call Gemini 3.1 Pro with HIGH thinking to synthesize a field summary."""
    prompt = build_prompt(subfield_name, subfield_description, researchers)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True),
            ),
        )

        if not response.text:
            print(f"  Empty response for {subfield_name}")
            return None

        result = parse_json_response(response.text)

        # Validate required keys
        required = {"overview", "active_research_themes", "open_questions",
                    "methods_and_approaches", "emerging_directions"}
        missing = required - set(result.keys())
        if missing:
            print(f"  Warning: missing keys {missing} for {subfield_name}")

        return result

    except Exception as e:
        print(f"  Error generating summary for {subfield_name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate field-level research direction summaries for each subfield"
    )
    parser.add_argument("--subfield", type=str, default=None,
                        help="Process only a single subfield (exact name match)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--no-skip", action="store_true",
                        help="Regenerate even if output already exists")
    args = parser.parse_args()

    subfields = load_subfield_definitions()
    print(f"Loaded {len(subfields)} subfield definitions")

    if args.subfield:
        subfields = [sf for sf in subfields if sf["name"] == args.subfield]
        if not subfields:
            print(f"Subfield '{args.subfield}' not found.")
            print("Available:", ", ".join(sf["name"] for sf in load_subfield_definitions()))
            sys.exit(1)

    # Load existing output if present
    existing = {}
    if FIELD_DIRECTIONS_PATH.exists() and not args.no_skip:
        with open(FIELD_DIRECTIONS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)

    client = get_client()
    results = dict(existing)

    for sf in subfields:
        name = sf["name"]
        description = sf["description"]

        if name in results and not args.no_skip:
            print(f"[SKIP] {name} (already generated)")
            continue

        researchers = load_researchers_for_subfield(name)
        print(f"\n[{name}] — {len(researchers)} researchers with directions")

        if not researchers:
            print(f"  No researchers found, skipping")
            continue

        if args.dry_run:
            print(f"  [DRY RUN] Would call Gemini 3.1 Pro HIGH thinking")
            print(f"  Prompt preview: {len(researchers)} researcher directions")
            continue

        print(f"  Calling Gemini 3.1 Pro (HIGH thinking)...")
        summary = generate_field_summary(client, name, description, researchers)

        if summary:
            summary["subfield"] = name
            summary["n_researchers"] = len(researchers)
            results[name] = summary
            print(f"  Done — {len(summary.get('active_research_themes', []))} themes, "
                  f"{len(summary.get('open_questions', []))} questions")

            # Save after each subfield so we can resume on interruption
            BUILD_DIR.mkdir(parents=True, exist_ok=True)
            with open(FIELD_DIRECTIONS_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            print(f"  Failed to generate summary for {name}")

    if not args.dry_run:
        print(f"\nSaved {len(results)} field summaries to {FIELD_DIRECTIONS_PATH}")


if __name__ == "__main__":
    main()
