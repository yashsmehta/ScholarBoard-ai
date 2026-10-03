"""
AI Search keywords for every PI (data/build/search_cards.json).

Gemini 3.8 Flash reads each PI's bio, research direction and papers and returns up to 10
extremely technical, specific keywords — whatever best sets the PI apart: phenomena,
methods, species, paradigms, datasets. They are each PI's entry in the index the AI Search
agent reads in full to shortlist (see scholar_board/nlsearch/).

Each entry: `keywords` (list), `card` (keywords joined with "; ") and `hash` (a fingerprint
of the profile they were built from). Computed once and saved; re-runs only regenerate PIs
whose profile changed (e.g. a new PI, or a hand edit at a PI's request). One structured-JSON
call per PI, run in parallel.

Reads data/build/scholars.json (run after `build`).

Usage:
    uv run -m scholar_board.pipeline.search_cards --dry-run      # List stale entries
    uv run -m scholar_board.pipeline.search_cards                # Regenerate stale entries
    uv run -m scholar_board.pipeline.search_cards --ids 0459,E367 --force
    uv run -m scholar_board.pipeline.search_cards --force --workers 25   # Everyone
"""

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from scholar_board.config import SCHOLARS_JSON, SEARCH_CARDS_PATH
from scholar_board.gemini import generate_json, get_client
from scholar_board.prompt_loader import load_prompt

MAX_KEYWORDS = 10
MAX_ATTEMPTS = 5
RETRY_BASE_SECONDS = 5
SCHEMA = {"type": "object", "properties": {"keywords": {"type": "array", "items": {"type": "string"}}},
          "required": ["keywords"]}


def _papers_text(papers: list[dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        entry = f"{i}. {p.get('title', 'Untitled')} ({p.get('year', '?')})"
        if p.get("abstract"):
            entry += f"\n   {p['abstract']}"
        lines.append(entry)
    return "\n".join(lines) or "(none)"


def card_inputs(scholar: dict) -> dict:
    return {
        "scholar_name": scholar.get("name", ""),
        "institution": scholar.get("institution") or "unknown",
        "bio": scholar.get("bio") or "(none)",
        "research_direction": scholar.get("research_direction") or "(none)",
        "papers_text": _papers_text(scholar.get("papers") or []),
    }


def input_hash(inputs: dict) -> str:
    blob = json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def clean_keywords(raw: list) -> list[str]:
    """Keep at most 10 non-empty, de-duplicated keywords."""
    seen, out = set(), []
    for item in raw or []:
        item = " ".join(str(item).split()).strip(" ;,.")
        if item and item.lower() not in seen:
            seen.add(item.lower())
            out.append(item)
    return out[:MAX_KEYWORDS]


def generate_entry(scholar: dict, client) -> dict | None:
    """One Gemini Flash call → validated search_cards.json entry, or None."""
    inputs = card_inputs(scholar)
    prompt = (load_prompt("search_card").replace("{bio}", inputs["bio"])
              .replace("{research_direction}", inputs["research_direction"]).replace("{papers_text}", inputs["papers_text"]))
    for attempt in range(MAX_ATTEMPTS):
        try:
            result = generate_json(prompt, SCHEMA, client=client)
            break
        except Exception as e:  # noqa: BLE001 — 429s and transient errors: back off and retry
            if attempt == MAX_ATTEMPTS - 1:
                raise
            time.sleep(RETRY_BASE_SECONDS * 2 ** attempt)
    keywords = clean_keywords((result or {}).get("keywords"))
    if len(keywords) < 3:
        return None
    return {"hash": input_hash(inputs), "keywords": keywords, "card": "; ".join(keywords)}


def load_cards() -> dict:
    return json.loads(SEARCH_CARDS_PATH.read_text(encoding="utf-8")) if SEARCH_CARDS_PATH.exists() else {}


def save_cards(cards: dict) -> None:
    SEARCH_CARDS_PATH.write_text(json.dumps(dict(sorted(cards.items())), indent=1, ensure_ascii=False) + "\n",
                                 encoding="utf-8")


def update_cards(ids: list[str] | None = None, force: bool = False, workers: int = 25,
                 limit: int | None = None, dry_run: bool = False) -> list[str]:
    """Regenerate stale (or, with force, all) entries for `ids` (default: every PI). Returns failed ids."""
    scholars = json.loads(SCHOLARS_JSON.read_text(encoding="utf-8"))
    cards = {sid: c for sid, c in load_cards().items() if sid in scholars}  # drop PIs no longer on the map
    wanted = set(ids) if ids else None
    todo = [sid for sid, s in scholars.items()
            if (not wanted or sid in wanted)
            and (force or cards.get(sid, {}).get("hash") != input_hash(card_inputs(s)))]
    if limit:
        todo = todo[:limit]
    print(f"{len(scholars)} PIs, {len(cards)} entries, {len(todo)} to generate ({workers} in parallel)")
    if dry_run or not todo:
        for sid in todo[:20]:
            print(f"  would generate {sid} {scholars[sid]['name']}")
        return []

    client = get_client(timeout_s=90)
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate_entry, scholars[sid], client): sid for sid in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            sid = futures[fut]
            try:
                entry = fut.result()
            except Exception as e:  # noqa: BLE001 — report and continue
                print(f"  {sid} error: {e}")
                entry = None
            if entry:
                cards[sid] = entry
            else:
                failed.append(sid)
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}")
                save_cards(cards)  # checkpoint
    save_cards(cards)
    print(f"Wrote {len(cards)} entries → {SEARCH_CARDS_PATH}")
    if failed:
        print(f"Failed ({len(failed)}): {','.join(failed)} — re-run to retry")
    return failed


def main():
    parser = argparse.ArgumentParser(description="Generate AI Search keywords per PI with Gemini Flash")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--ids", type=str, default=None, help="Comma-separated scholar IDs")
    parser.add_argument("--force", action="store_true", help="Regenerate even if the profile is unchanged")
    parser.add_argument("--workers", type=int, default=25, help="Parallel Gemini calls")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    update_cards(args.ids.split(",") if args.ids else None, args.force, args.workers, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
