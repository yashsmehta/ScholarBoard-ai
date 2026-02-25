"""
Build consolidated scholars.json from all available data sources.

Merges:
1. data/source/vss_data.csv → id, name, institution, department
2. data/build/scholars.json (current) → umap coordinates, cluster
3. data/pipeline/scholar_papers/*.json → papers
4. data/pipeline/scholar_profiles/*.json → bio, main_research_area, lab_url, department
5. data/build/profile_pics/*.jpg → profile_pic filename
6. data/pipeline/scholar_subfields.json → subfield tags
7. data/pipeline/scholar_ideas/*.json → suggested research ideas

Outputs:
- data/build/scholars/{id}.json (individual files)
- data/build/scholars.json (consolidated)

Usage:
    uv run -m scholar_board.pipeline.build
    uv run -m scholar_board.pipeline.build --no-individual  # skip individual files
"""

import csv
import json
import re
import argparse
from pathlib import Path

from scholar_board.config import (
    CSV_PATH,
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


def load_vss_csv() -> dict[str, dict]:
    """Load unique scholars from vss_data.csv."""
    scholars = {}
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("scholar_id", "").strip().strip("\"'")
            if not sid:
                continue
            if sid.isdigit():
                sid = sid.zfill(4)
            if sid in scholars:
                continue
            name = row.get("scholar_name", "").strip().strip("\"'")
            institution = row.get("scholar_institution", "").strip().strip("\"'")
            department = row.get("scholar_department", "").strip().strip("\"'")
            if department in ("N/A", "nan", ""):
                department = None
            if institution in ("N/A", "nan", ""):
                institution = None
            if name:
                scholars[sid] = {
                    "id": sid,
                    "name": name,
                    "institution": institution,
                    "department": department,
                }
    return scholars


def load_current_scholars_json() -> dict[str, dict]:
    """Load existing scholars.json for umap/cluster data."""
    if not SCHOLARS_JSON.exists():
        return {}
    with open(SCHOLARS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scholar_papers() -> dict[str, list[dict]]:
    """Load paper data from PAPERS_DIR/*.json."""
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


def load_scholar_profiles() -> dict[str, dict]:
    """Load structured profiles from PROFILES_DIR/*.json."""
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
                "bio": data.get("bio"),
                "main_research_area": data.get("main_research_area"),
                "lab_name": data.get("lab_name"),
                "lab_url": data.get("lab_url"),
                "department": data.get("department"),
            }
        except (json.JSONDecodeError, KeyError):
            continue
    return profiles


def find_profile_pics() -> dict[str, str]:
    """Find profile pic filenames for each scholar ID."""
    pics = {}
    if not PICS_DIR.exists():
        return pics
    for fpath in PICS_DIR.glob("*.jpg"):
        if fpath.name == "default_avatar.jpg":
            continue
        match = re.search(r"_(\d{4})\.jpg$", fpath.name)
        if match:
            sid = match.group(1)
            pics[sid] = fpath.name
    return pics


def load_subfield_assignments() -> dict[str, dict]:
    """Load subfield assignments from SUBFIELDS_PATH."""
    if not SUBFIELDS_PATH.exists():
        return {}
    with open(SUBFIELDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scholar_ideas() -> dict[str, dict]:
    """Load AI-generated research ideas from IDEAS_DIR/*.json."""
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
            idea = data.get("idea", {})
            if idea:
                ideas[sid] = idea
        except (json.JSONDecodeError, KeyError):
            continue
    return ideas


def build_scholars(write_individual: bool = True) -> list[Scholar]:
    """Build consolidated scholar data from all sources."""
    print("Loading data sources...")
    vss_data = load_vss_csv()
    print(f"  vss_data.csv: {len(vss_data)} unique scholars")

    current_data = load_current_scholars_json()
    print(f"  scholars.json: {len(current_data)} entries")

    papers_data = load_scholar_papers()
    print(f"  scholar_papers: {len(papers_data)} scholars with papers")

    profiles_data = load_scholar_profiles()
    print(f"  scholar_profiles: {len(profiles_data)} profiles")

    pics_data = find_profile_pics()
    print(f"  profile_pics: {len(pics_data)} profile pictures")

    subfields_data = load_subfield_assignments()
    print(f"  subfields: {len(subfields_data)} assignments")

    ideas_data = load_scholar_ideas()
    print(f"  scholar_ideas: {len(ideas_data)} ideas")

    print("\nBuilding scholar objects...")
    scholars = []
    for sid, vss in vss_data.items():
        scholar_dict = {
            "id": sid,
            "name": vss["name"],
            "institution": vss.get("institution"),
            "department": vss.get("department"),
        }

        if sid in current_data:
            cur = current_data[sid]
            umap = cur.get("umap_projection")
            if umap and isinstance(umap, dict) and "x" in umap and "y" in umap:
                scholar_dict["umap_projection"] = UMAPProjection(x=umap["x"], y=umap["y"])
            scholar_dict["cluster"] = cur.get("cluster")

        if sid in papers_data:
            scholar_dict["papers"] = [Paper(**p) for p in papers_data[sid]]

        if sid in profiles_data:
            profile = profiles_data[sid]
            if profile.get("bio"):
                scholar_dict["bio"] = profile["bio"]
            if profile.get("main_research_area"):
                scholar_dict["main_research_area"] = profile["main_research_area"]
            if profile.get("lab_name"):
                scholar_dict["lab_name"] = profile["lab_name"]
            if profile.get("lab_url"):
                scholar_dict["lab_url"] = profile["lab_url"]
            if profile.get("department"):
                scholar_dict["department"] = profile["department"]

        if sid in subfields_data:
            sf = subfields_data[sid]
            scholar_dict["primary_subfield"] = sf.get("primary_subfield")
            scholar_dict["subfields"] = [SubfieldTag(**t) for t in sf.get("subfields", [])]

        if sid in ideas_data:
            scholar_dict["suggested_idea"] = ResearchIdea(**ideas_data[sid])

        if sid in pics_data:
            scholar_dict["profile_pic"] = pics_data[sid]

        scholar = Scholar(**scholar_dict)
        scholars.append(scholar)

    print(f"\nBuilt {len(scholars)} scholars")

    with_umap = sum(1 for s in scholars if s.umap_projection is not None)
    with_papers = sum(1 for s in scholars if len(s.papers) > 0)
    with_bio = sum(1 for s in scholars if s.bio is not None)
    with_area = sum(1 for s in scholars if s.main_research_area is not None)
    with_pic = sum(1 for s in scholars if s.profile_pic is not None)
    with_subfield = sum(1 for s in scholars if s.primary_subfield is not None)
    with_idea = sum(1 for s in scholars if s.suggested_idea is not None)
    print(f"  With UMAP coords: {with_umap}")
    print(f"  With papers: {with_papers}")
    print(f"  With bio: {with_bio}")
    print(f"  With research area: {with_area}")
    print(f"  With subfield tags: {with_subfield}")
    print(f"  With research idea: {with_idea}")
    print(f"  With profile pic: {with_pic}")

    if write_individual:
        SCHOLARS_DIR.mkdir(parents=True, exist_ok=True)
        for scholar in scholars:
            fpath = SCHOLARS_DIR / f"{scholar.id}.json"
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(scholar.model_dump_json(indent=2))
        print(f"\nWrote {len(scholars)} individual files to {SCHOLARS_DIR}")

    output_path = SCHOLARS_JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    consolidated = {}
    for scholar in scholars:
        data = scholar.model_dump(mode="json")
        data = {k: v for k, v in data.items() if v is not None}
        if not data.get("papers"):
            data.pop("papers", None)
        consolidated[scholar.id] = data

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    print(f"Wrote consolidated scholars.json ({len(consolidated)} scholars)")

    return scholars


def main():
    parser = argparse.ArgumentParser(
        description="Build consolidated scholars.json from all data sources"
    )
    parser.add_argument(
        "--no-individual",
        action="store_true",
        help="Skip writing individual scholar JSON files",
    )
    args = parser.parse_args()

    build_scholars(write_individual=not args.no_individual)


if __name__ == "__main__":
    main()
