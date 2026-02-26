"""
Build consolidated scholars.json from the SQLite database.

On first run (or with --backfill), reads existing pipeline JSON files into the
database, then exports.  On subsequent runs the DB is already current because
each pipeline step upserts into it directly, so this is a fast SELECT + write.

Usage:
    uv run -m scholar_board.pipeline.build              # export DB → scholars.json
    uv run -m scholar_board.pipeline.build --backfill   # seed DB from JSON files, then export
    uv run -m scholar_board.pipeline.build --no-individual  # skip per-scholar JSON files
"""

import json
import re
import argparse

from scholar_board.config import (
    PAPERS_DIR,
    PROFILES_DIR,
    PICS_DIR,
    SUBFIELDS_PATH,
    IDEAS_DIR,
    SCHOLARS_JSON,
    SCHOLARS_DIR,
    BUILD_DIR,
)
from scholar_board.schemas import Scholar, Paper, SubfieldTag, UMAPProjection, ResearchIdea
from scholar_board.db import (
    get_connection,
    init_db,
    ensure_scholar,
    upsert_papers,
    upsert_profile,
    upsert_cluster,
    upsert_subfields,
    upsert_idea,
    upsert_profile_pic,
    load_scholars,
)


# ── helpers re-used from the old build (needed for backfill) ──────────────


def _load_scholar_papers() -> dict[str, list[dict]]:
    papers_by_id = {}
    if not PAPERS_DIR.exists():
        return papers_by_id
    for fpath in PAPERS_DIR.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", fpath.stem.split("_")[0])
            papers_by_id[sid] = data.get("papers", [])
        except (json.JSONDecodeError, KeyError):
            continue
    return papers_by_id


def _load_scholar_profiles() -> dict[str, dict]:
    profiles = {}
    if not PROFILES_DIR.exists():
        return profiles
    for fpath in PROFILES_DIR.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", "")
            if not sid:
                stem = fpath.stem
                parts = stem.split("_")
                if parts[0].isdigit():
                    sid = parts[0].zfill(4)
                else:
                    match = re.search(r"_(\d{3,4})$", stem)
                    if match:
                        sid = match.group(1).zfill(4)
            if not sid:
                continue
            sid = sid.zfill(4) if sid.isdigit() else sid
            profiles[sid] = {
                k: data.get(k)
                for k in ("bio", "main_research_area", "lab_name", "lab_url", "department")
            }
        except (json.JSONDecodeError, KeyError):
            continue
    return profiles


def _find_profile_pics() -> dict[str, str]:
    pics = {}
    if not PICS_DIR.exists():
        return pics
    for fpath in PICS_DIR.glob("*.jpg"):
        if fpath.name == "default_avatar.jpg":
            continue
        match = re.search(r"_(\d{4})\.jpg$", fpath.name)
        if match:
            pics[match.group(1)] = fpath.name
    return pics


def _load_subfield_assignments() -> dict[str, dict]:
    if not SUBFIELDS_PATH.exists():
        return {}
    with open(SUBFIELDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_scholar_ideas() -> dict[str, dict]:
    ideas = {}
    if not IDEAS_DIR.exists():
        return ideas
    for fpath in IDEAS_DIR.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", "")
            if not sid:
                parts = fpath.stem.split("_")
                if parts[0].isdigit():
                    sid = parts[0].zfill(4)
            if not sid:
                continue
            sid = sid.zfill(4) if sid.isdigit() else sid
            if data.get("idea"):
                ideas[sid] = data["idea"]
        except (json.JSONDecodeError, KeyError):
            continue
    return ideas


# ── backfill: seed DB from existing JSON pipeline artifacts ──────────────

def backfill_db(conn) -> None:
    """Populate the DB from all existing pipeline JSON files (idempotent).

    Safe to run multiple times — all operations are upserts.
    Use this once to migrate from the old JSON-only pipeline, or whenever
    you want to repair/re-seed the database.
    """
    print("Backfilling database from pipeline JSON files...")

    all_scholars = load_scholars(is_pi_only=False)
    for s in all_scholars:
        ensure_scholar(conn, s["scholar_id"], s["scholar_name"], s.get("scholar_institution"))
    print(f"  Ensured {len(all_scholars)} scholars in DB")

    papers_data = _load_scholar_papers()
    for sid, papers in papers_data.items():
        upsert_papers(conn, sid, papers)
    print(f"  Papers: {len(papers_data)} scholars")

    profiles_data = _load_scholar_profiles()
    for sid, profile in profiles_data.items():
        fields = {k: v for k, v in profile.items() if v}
        if fields:
            upsert_profile(conn, sid, **fields)
    print(f"  Profiles: {len(profiles_data)} scholars")

    subfields_data = _load_subfield_assignments()
    for sid, assignment in subfields_data.items():
        upsert_subfields(conn, sid, assignment["primary_subfield"], assignment.get("subfields", []))
    print(f"  Subfields: {len(subfields_data)} scholars")

    ideas_data = _load_scholar_ideas()
    for sid, idea in ideas_data.items():
        upsert_idea(conn, sid, idea)
    print(f"  Ideas: {len(ideas_data)} scholars")

    pics_data = _find_profile_pics()
    for sid, filename in pics_data.items():
        upsert_profile_pic(conn, sid, filename)
    print(f"  Profile pics: {len(pics_data)} scholars")

    # UMAP + cluster — read from existing scholars.json if present
    if SCHOLARS_JSON.exists():
        with open(SCHOLARS_JSON, "r", encoding="utf-8") as f:
            existing = json.load(f)
        updated = 0
        for sid, data in existing.items():
            umap = data.get("umap_projection")
            if umap and "x" in umap and "y" in umap:
                upsert_cluster(conn, sid, umap["x"], umap["y"], data.get("cluster", -1))
                updated += 1
        if updated:
            print(f"  UMAP/cluster: {updated} scholars (from existing scholars.json)")

    print("Backfill complete.\n")


# ── export: SELECT from DB → Scholar objects → JSON ──────────────────────

def export_scholars(conn, write_individual: bool = True) -> list[Scholar]:
    """Read all data from the DB and write scholars.json (+ individual files)."""
    print("Querying database...")

    scholar_rows = conn.execute("SELECT * FROM scholars ORDER BY id").fetchall()
    print(f"  scholars: {len(scholar_rows)}")

    papers_rows = conn.execute("SELECT * FROM papers ORDER BY scholar_id, id").fetchall()
    papers_by_sid: dict[str, list] = {}
    for row in papers_rows:
        papers_by_sid.setdefault(row["scholar_id"], []).append(dict(row))
    print(f"  papers: {len(papers_rows)} across {len(papers_by_sid)} scholars")

    sf_rows = conn.execute(
        "SELECT * FROM subfields ORDER BY scholar_id, is_primary DESC, score DESC"
    ).fetchall()
    subfields_by_sid: dict[str, list] = {}
    for row in sf_rows:
        subfields_by_sid.setdefault(row["scholar_id"], []).append(dict(row))

    idea_rows = conn.execute("SELECT * FROM ideas").fetchall()
    ideas_by_sid = {row["scholar_id"]: dict(row) for row in idea_rows}
    print(f"  subfields: {len(subfields_by_sid)} scholars  |  ideas: {len(ideas_by_sid)} scholars")

    print("\nBuilding scholar objects...")
    scholars: list[Scholar] = []
    stats = {k: 0 for k in ("umap", "papers", "bio", "area", "subfield", "idea", "pic")}

    for row in scholar_rows:
        sid = row["id"]
        d: dict = {k: row[k] for k in row.keys() if row[k] is not None}

        # UMAP coords live in flat columns; convert to nested object
        if d.pop("umap_x", None) is not None:
            d["umap_projection"] = UMAPProjection(x=row["umap_x"], y=row["umap_y"])
            stats["umap"] += 1
        d.pop("umap_y", None)

        if sid in papers_by_sid:
            d["papers"] = [
                Paper(
                    title=p["title"],
                    abstract=p.get("abstract"),
                    year=p.get("year"),
                    venue=p.get("venue"),
                    citations=p.get("citations") or "0",
                    authors=p.get("authors"),
                    url=p.get("url"),
                )
                for p in papers_by_sid[sid]
            ]
            stats["papers"] += 1

        if sid in subfields_by_sid:
            d["subfields"] = [
                SubfieldTag(subfield=sf["subfield"], score=sf["score"] or 0.0)
                for sf in subfields_by_sid[sid]
            ]
            stats["subfield"] += 1

        if sid in ideas_by_sid:
            idea = ideas_by_sid[sid]
            try:
                d["suggested_idea"] = ResearchIdea(
                    research_thread=idea["research_thread"] or "",
                    open_question=idea["open_question"] or "",
                    title=idea["title"] or "",
                    hypothesis=idea["hypothesis"] or "",
                    approach=idea["approach"] or "",
                    scientific_impact=idea["scientific_impact"] or "",
                    why_now=idea["why_now"] or "",
                )
                stats["idea"] += 1
            except Exception:
                pass

        if row["bio"]:
            stats["bio"] += 1
        if row["main_research_area"]:
            stats["area"] += 1
        if row["profile_pic"]:
            stats["pic"] += 1

        try:
            scholars.append(Scholar(**d))
        except Exception as e:
            print(f"  Warning: skipping {sid} — {e}")

    print(f"\nBuilt {len(scholars)} scholars")
    print(f"  With UMAP coords:    {stats['umap']}")
    print(f"  With papers:         {stats['papers']}")
    print(f"  With bio:            {stats['bio']}")
    print(f"  With research area:  {stats['area']}")
    print(f"  With subfield tags:  {stats['subfield']}")
    print(f"  With research idea:  {stats['idea']}")
    print(f"  With profile pic:    {stats['pic']}")

    if write_individual:
        SCHOLARS_DIR.mkdir(parents=True, exist_ok=True)
        for scholar in scholars:
            fpath = SCHOLARS_DIR / f"{scholar.id}.json"
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(scholar.model_dump_json(indent=2))
        print(f"\nWrote {len(scholars)} individual files to {SCHOLARS_DIR}")

    consolidated = {}
    for scholar in scholars:
        data = scholar.model_dump(mode="json")
        data = {k: v for k, v in data.items() if v is not None}
        if not data.get("papers"):
            data.pop("papers", None)
        consolidated[scholar.id] = data

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    with open(SCHOLARS_JSON, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    print(f"Wrote {SCHOLARS_JSON} ({len(consolidated)} scholars)")

    return scholars


# ── entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Export scholarboard.db → scholars.json"
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Seed DB from existing pipeline JSON files before exporting",
    )
    parser.add_argument(
        "--no-individual",
        action="store_true",
        help="Skip writing individual scholar JSON files",
    )
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)

    if args.backfill:
        backfill_db(conn)

    export_scholars(conn, write_individual=not args.no_individual)
    conn.close()


if __name__ == "__main__":
    main()
