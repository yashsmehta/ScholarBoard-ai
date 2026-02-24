"""
Build consolidated scholars.json from all available data sources.

Merges:
1. data/vss_data.csv → id, name, institution, department
2. data/scholars.json (current) → umap coordinates, cluster
3. data/scholar_papers/*.json → papers
4. data/scholar_summaries/*_summary.txt → bio
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

from scholar_board.schemas import Scholar, Paper, UMAPProjection

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


def load_scholar_summaries(summaries_dir: Path) -> dict[str, str]:
    """Load bio summaries from data/scholar_summaries/*_summary.txt.

    File naming: "Scholar Name_XXX_summary.txt" where XXX is the ID (possibly 3 digits).
    """
    bios = {}
    if not summaries_dir.exists():
        return bios
    for fpath in summaries_dir.glob("*_summary.txt"):
        # Extract ID from filename: "Name_XXX_summary.txt"
        stem = fpath.stem  # e.g. "A . Caglar Tas_001_summary"
        # Find the last occurrence of _XXX_summary pattern
        match = re.search(r"_(\d+)_summary$", stem)
        if match:
            raw_id = match.group(1)
            sid = raw_id.zfill(4)
            text = fpath.read_text(encoding="utf-8").strip()
            if text:
                bios[sid] = text
    return bios


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


def build_scholars(write_individual: bool = True) -> list[Scholar]:
    """Build consolidated scholar data from all sources."""
    csv_path = DATA_DIR / "vss_data.csv"
    current_json_path = DATA_DIR / "scholars.json"
    papers_dir = DATA_DIR / "scholar_papers"
    summaries_dir = DATA_DIR / "scholar_summaries"
    pics_dir = DATA_DIR / "profile_pics"

    # Load all data sources
    print("Loading data sources...")
    vss_data = load_vss_csv(csv_path)
    print(f"  vss_data.csv: {len(vss_data)} unique scholars")

    current_data = load_current_scholars_json(current_json_path)
    print(f"  scholars.json: {len(current_data)} entries")

    papers_data = load_scholar_papers(papers_dir)
    print(f"  scholar_papers: {len(papers_data)} scholars with papers")

    bios_data = load_scholar_summaries(summaries_dir)
    print(f"  scholar_summaries: {len(bios_data)} bios")

    pics_data = find_profile_pics(pics_dir)
    print(f"  profile_pics: {len(pics_data)} profile pictures")

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

        # Add bio
        if sid in bios_data:
            scholar_dict["bio"] = bios_data[sid]

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
    with_pic = sum(1 for s in scholars if s.profile_pic is not None)
    print(f"  With UMAP coords: {with_umap}")
    print(f"  With papers: {with_papers}")
    print(f"  With bio: {with_bio}")
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
        # Convert empty lists to omit them
        if not data.get("research_areas"):
            data.pop("research_areas", None)
        if not data.get("education"):
            data.pop("education", None)
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
