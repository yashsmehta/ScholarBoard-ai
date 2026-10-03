"""Build the on-disk corpus the NL-search agent works over.

Layout (all public data, derived from scholars.json + search_cards.json):

    <corpus>/index/part-NN.txt     tier 1: one line per PI, `id | name | up to 10 search
                                   keywords` — no metadata
    <corpus>/meta.db               SQLite: pi (institution, country, h-index, …)
                                   and paper (titles, authors) — for hard filters
    <corpus>/tools/*.py            the agent's helpers: sql.py (inspect
                                   metadata), filter.py (index lines of only
                                   the PIs a query selects), details.py (tier 2:
                                   research direction + paper titles)
    <corpus>/profiles/<id>.json    full profile per PI (CLI display, health)

Each search copies index/, tools/ and meta.db into a fresh workspace (see
rank.py), so the agent's outputs never touch the corpus. Shards are capped at
FILE_LIMIT so each fits one file view (agy shows ~29 KB per view).

The build is atomic (written to a sibling dir, then swapped in) so a running
search server never sees a half-written corpus.

Usage:
    uv run -m scholar_board.nlsearch.corpus                     # → data/build/search_corpus
    uv run -m scholar_board.nlsearch.corpus --out /var/lib/scholarboard/corpus
"""

import argparse
import json
import shutil
import sqlite3
from pathlib import Path

from scholar_board.config import SCHOLARS_JSON, SEARCH_CARDS_PATH, SEARCH_CORPUS_DIR

TOOLS_DIR = Path(__file__).parent / "tools"
FILE_LIMIT = 27_000


def _clean(x) -> str:
    return " ".join(str(x or "").replace("|", "/").split())


def index_line(s: dict, entry: dict) -> str:
    """`id | name | keywords`; falls back to area + paper titles."""
    text = entry.get("card") or "; ".join(
        x for x in [s.get("main_research_area"), *(p.get("title", "") for p in s.get("papers") or [])] if x)
    return " | ".join([s["id"], _clean(s.get("name")), _clean(text)])


def write_meta_db(path: Path, rows: list[dict], cards: dict) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE pi (id TEXT PRIMARY KEY, name TEXT, institution TEXT, department TEXT, country TEXT,
                         lab_name TEXT, h_index INTEGER, total_citations INTEGER, subfields TEXT,
                         bio TEXT, index_line TEXT, direction TEXT);
        CREATE TABLE paper (pi_id TEXT, title TEXT, year INTEGER, venue TEXT, authors TEXT);
    """)
    con.executemany("INSERT INTO pi VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [(
        s["id"], s.get("name"), s.get("institution"), s.get("department"), s.get("country"), s.get("lab_name"),
        s.get("h_index"), s.get("total_citations"), "; ".join(t["subfield"] for t in s.get("subfields") or []), s.get("bio"),
        index_line(s, cards.get(s["id"]) or {}), s.get("research_direction")) for s in rows])
    con.executemany("INSERT INTO paper VALUES (?,?,?,?,?)", [
        (s["id"], p.get("title"), p.get("year"), p.get("venue"),
         ", ".join(p["authors"]) if isinstance(p.get("authors"), list) else p.get("authors"))
        for s in rows for p in s.get("papers") or []])
    con.commit()
    con.close()


def profile_doc(s: dict) -> dict:
    return {
        "id": s["id"],
        "name": s.get("name", ""),
        "institution": s.get("institution", ""),
        "department": s.get("department", ""),
        "country": s.get("country", ""),
        "lab_name": s.get("lab_name", ""),
        "h_index": s.get("h_index"),
        "total_citations": s.get("total_citations"),
        "subfields": [t["subfield"] for t in (s.get("subfields") or [])],
        "main_research_area": s.get("main_research_area", ""),
        "bio": s.get("bio", ""),
        "research_direction": s.get("research_direction", ""),
        "recent_papers": [
            {k: p.get(k) for k in ("title", "year", "venue", "authors", "abstract")}
            for p in (s.get("papers") or [])
        ],
    }


def build_corpus(out_dir: Path = SEARCH_CORPUS_DIR,
                 scholars_path: Path = SCHOLARS_JSON,
                 cards_path: Path = SEARCH_CARDS_PATH) -> int:
    """Write the corpus to out_dir atomically. Returns the number of PIs."""
    scholars = json.loads(scholars_path.read_text(encoding="utf-8"))
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.exists() else {}

    out_dir = Path(out_dir)
    staging = out_dir.with_name(out_dir.name + ".staging")
    shutil.rmtree(staging, ignore_errors=True)
    (staging / "index").mkdir(parents=True)
    (staging / "profiles").mkdir()

    rows = sorted(scholars.values(), key=lambda s: s["id"])
    shards: list[list[str]] = [[]]
    size = 0
    for s in rows:
        line = index_line(s, cards.get(s["id"]) or {}) + "\n"
        n = len(line.encode("utf-8"))
        if shards[-1] and size + n > FILE_LIMIT:
            shards.append([])
            size = 0
        shards[-1].append(line)
        size += n
    for i, lines in enumerate(shards, 1):
        (staging / "index" / f"part-{i:02d}.txt").write_text("".join(lines), encoding="utf-8")
    write_meta_db(staging / "meta.db", rows, cards)
    shutil.copytree(TOOLS_DIR, staging / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    for s in rows:
        (staging / "profiles" / f"{s['id']}.json").write_text(
            json.dumps(profile_doc(s), indent=1, ensure_ascii=False), encoding="utf-8")

    # Swap: rename old aside, move staging in, then delete old.
    old = out_dir.with_name(out_dir.name + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if out_dir.exists():
        out_dir.rename(old)
    staging.rename(out_dir)
    shutil.rmtree(old, ignore_errors=True)

    missing = sum(1 for s in rows if not (cards.get(s["id"]) or {}).get("card"))
    if missing:
        print(f"Warning: {missing} PIs have no search keywords (using area + paper titles); "
              "run `uv run -m scholar_board.pipeline.search_cards`")
    return len(rows)


def corpus_ids(corpus_dir: Path) -> set[str]:
    return {p.stem for p in (Path(corpus_dir) / "profiles").glob("*.json")}


def main():
    parser = argparse.ArgumentParser(description="Build the NL-search agent corpus")
    parser.add_argument("--out", type=Path, default=SEARCH_CORPUS_DIR)
    args = parser.parse_args()
    n = build_corpus(args.out)
    print(f"Wrote corpus for {n} PIs → {args.out}")


if __name__ == "__main__":
    main()
