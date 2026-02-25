"""
Build consolidated scholars.json from all available data sources.

Merges:
1. data/vss_data.csv → id, name, institution, department
2. data/scholars.json (current) → umap coordinates, cluster
3. data/scholar_papers/*.json → papers
4. data/scholar_profiles/*.json → bio, main_research_area, lab_url, department
5. data/profile_pics/*.jpg → profile_pic filename

Outputs:
- data/scholars/{id}.json (individual files)
- data/scholars.json (consolidated)

Usage:
    python3 scripts/build_scholars_json.py
    python3 scripts/build_scholars_json.py --no-individual  # skip individual files
"""

import csv
import json
import re
import argparse
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scholar_board.schemas import Scholar, Paper, SubfieldTag, UMAPProjection, ResearchIdea

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_vss_csv(csv_path: Path) -> dict[str, dict]:
    """Load unique scholars from vss_data.csv."""
    scholars = {}
    with open(csv_path, "r", encoding="utf-8") as f:
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


def load_current_scholars_json(json_path: Path) -> dict[str, dict]:
    """Load existing scholars.json for umap/cluster data."""
    if not json_path.exists():
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_scholar_papers(papers_dir: Path) -> dict[str, list[dict]]:
    """Load paper data from data/scholar_papers/*.json."""
    papers_by_id = {}
    if not papers_dir.exists():
        return papers_by_id
    for fpath in papers_dir.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", fpath.stem.split("_")[0])
            papers_by_id[sid] = data.get("papers", [])
        except (json.JSONDecodeError, KeyError):
            continue
    return papers_by_id


def load_scholar_profiles(profiles_dir: Path) -> dict[str, dict]:
    """Load structured profiles from data/scholar_profiles/*.json.

    File naming: "{id}_{name}.json" (id-first) or "{name}_{id}.json" (legacy).
    Returns dict keyed by scholar_id with bio, main_research_area, lab_url, department.
    """
    profiles = {}
    if not profiles_dir.exists():
        return profiles
    for fpath in profiles_dir.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", "")
            if not sid:
                # Try extracting from filename
                stem = fpath.stem
                parts = stem.split("_")
                if parts[0].isdigit():
                    sid = parts[0].zfill(4)
                else:
                    # Legacy naming: name_XXXX
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


def find_profile_pics(pics_dir: Path) -> dict[str, str]:
    """Find profile pic filenames for each scholar ID.

    File naming: "scholar_name_XXXX.jpg" where XXXX is the 4-digit ID.
    """
    pics = {}
    if not pics_dir.exists():
        return pics
    for fpath in pics_dir.glob("*.jpg"):
        if fpath.name == "default_avatar.jpg":
            continue
        # Extract ID from filename: last part before .jpg
        match = re.search(r"_(\d{4})\.jpg$", fpath.name)
        if match:
            sid = match.group(1)
            pics[sid] = fpath.name
    return pics


def load_subfield_assignments(subfields_path: Path) -> dict[str, dict]:
    """Load subfield assignments from data/scholar_subfields.json."""
    if not subfields_path.exists():
        return {}
    with open(subfields_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scholar_ideas(ideas_dir: Path) -> dict[str, dict]:
    """Load AI-generated research ideas from data/scholar_ideas/*.json."""
    ideas = {}
    if not ideas_dir.exists():
        return ideas
    for fpath in ideas_dir.glob("*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sid = data.get("scholar_id", "")
            if not sid:
                # Extract from filename: {id}_{name}.json
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
    csv_path = DATA_DIR / "vss_data.csv"
    current_json_path = DATA_DIR / "scholars.json"
    papers_dir = DATA_DIR / "scholar_papers"
    profiles_dir = DATA_DIR / "scholar_profiles"
    pics_dir = DATA_DIR / "profile_pics"
    subfields_path = DATA_DIR / "scholar_subfields.json"
    ideas_dir = DATA_DIR / "scholar_ideas"

    # Load all data sources
    print("Loading data sources...")
    vss_data = load_vss_csv(csv_path)
    print(f"  vss_data.csv: {len(vss_data)} unique scholars")

    current_data = load_current_scholars_json(current_json_path)
    print(f"  scholars.json: {len(current_data)} entries")

    papers_data = load_scholar_papers(papers_dir)
    print(f"  scholar_papers: {len(papers_data)} scholars with papers")

    profiles_data = load_scholar_profiles(profiles_dir)
    print(f"  scholar_profiles: {len(profiles_data)} profiles")

    pics_data = find_profile_pics(pics_dir)
    print(f"  profile_pics: {len(pics_data)} profile pictures")

    subfields_data = load_subfield_assignments(subfields_path)
    print(f"  subfields: {len(subfields_data)} assignments")

    ideas_data = load_scholar_ideas(ideas_dir)
    print(f"  scholar_ideas: {len(ideas_data)} ideas")

    # Build scholars
    print("\nBuilding scholar objects...")
    scholars = []
    for sid, vss in vss_data.items():
        # Start with CSV data
        scholar_dict = {
            "id": sid,
            "name": vss["name"],
            "institution": vss.get("institution"),
            "department": vss.get("department"),
        }

        # Add umap + cluster from current scholars.json
        if sid in current_data:
            cur = current_data[sid]
            umap = cur.get("umap_projection")
            if umap and isinstance(umap, dict) and "x" in umap and "y" in umap:
                scholar_dict["umap_projection"] = UMAPProjection(
                    x=umap["x"], y=umap["y"]
                )
            scholar_dict["cluster"] = cur.get("cluster")

        # Add papers
        if sid in papers_data:
            scholar_dict["papers"] = [
                Paper(**p) for p in papers_data[sid]
            ]

        # Add profile data (bio, main_research_area, lab_url, department override)
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

        # Add subfield tags
        if sid in subfields_data:
            sf = subfields_data[sid]
            scholar_dict["primary_subfield"] = sf.get("primary_subfield")
            scholar_dict["subfields"] = [
                SubfieldTag(**t) for t in sf.get("subfields", [])
            ]

        # Add suggested research idea
        if sid in ideas_data:
            scholar_dict["suggested_idea"] = ResearchIdea(**ideas_data[sid])

        # Add profile pic
        if sid in pics_data:
            scholar_dict["profile_pic"] = pics_data[sid]

        # Validate with Pydantic
        scholar = Scholar(**scholar_dict)
        scholars.append(scholar)

    print(f"\nBuilt {len(scholars)} scholars")

    # Stats
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

    # Write individual files
    if write_individual:
        individual_dir = DATA_DIR / "scholars"
        individual_dir.mkdir(parents=True, exist_ok=True)
        for scholar in scholars:
            fpath = individual_dir / f"{scholar.id}.json"
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(scholar.model_dump_json(indent=2))
        print(f"\nWrote {len(scholars)} individual files to {individual_dir}")

    # Write consolidated JSON (keyed by ID, matching current format)
    output_path = DATA_DIR / "scholars.json"
    consolidated = {}
    for scholar in scholars:
        data = scholar.model_dump(mode="json")
        # Remove None values for cleaner output
        data = {k: v for k, v in data.items() if v is not None}
        # Remove empty lists
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
