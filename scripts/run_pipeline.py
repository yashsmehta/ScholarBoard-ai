"""
Pipeline orchestrator for ScholarBoard.ai

Shows pipeline status and runs steps in order.

Usage:
    python3 scripts/run_pipeline.py                  # Show status (dry run)
    python3 scripts/run_pipeline.py --step build     # Build scholars.json
    python3 scripts/run_pipeline.py --step website   # Copy to website/data/
    python3 scripts/run_pipeline.py --execute        # Run all steps
"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WEBSITE_DATA = PROJECT_ROOT / "website" / "data"

PYTHON = sys.executable

# Pipeline steps in order
STEPS = [
    {
        "name": "papers",
        "description": "Fetch papers via Gemini grounded search",
        "command": [PYTHON, "scripts/scholar_scraper/fetch_papers_gemini.py"],
        "check": lambda: len(list((DATA_DIR / "scholar_papers").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "info",
        "description": "Fetch researcher profiles via Gemini grounded search",
        "command": [PYTHON, "-m", "scholar_board.profile_extractor"],
        "check": lambda: len(list((DATA_DIR / "scholar_profiles").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "embed",
        "description": "Create paper-based embeddings",
        "command": [PYTHON, "scripts/create_paper_embeddings.py"],
        "check": lambda: 1 if (DATA_DIR / "scholar_embeddings.nc").exists() else 0,
        "total": 1,
    },
    {
        "name": "umap",
        "description": "Run UMAP + HDBSCAN clustering",
        "command": [PYTHON, "scripts/run_umap_dbscan.py"],
        "check": lambda: 1 if (DATA_DIR / "models" / "umap_model.joblib").exists() else 0,
        "total": 1,
    },
    {
        "name": "subfields",
        "description": "Assign vision science subfield labels",
        "command": [PYTHON, "scripts/assign_subfields.py"],
        "check": lambda: 1 if (DATA_DIR / "scholar_subfields.json").exists() else 0,
        "total": 1,
    },
    {
        "name": "ideas",
        "description": "Generate AI-suggested research directions",
        "command": [PYTHON, "scripts/generate_ideas.py"],
        "check": lambda: len(list((DATA_DIR / "scholar_ideas").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "build",
        "description": "Build consolidated scholars.json",
        "command": [PYTHON, "scripts/build_scholars_json.py"],
        "check": lambda: 1 if (DATA_DIR / "scholars.json").exists() else 0,
        "total": 1,
    },
    {
        "name": "website",
        "description": "Copy data to website/data/",
        "command": None,  # Custom logic
        "check": lambda: 1 if (WEBSITE_DATA / "scholars.json").exists() else 0,
        "total": 1,
    },
]


def show_status():
    """Show pipeline status."""
    print("ScholarBoard.ai Pipeline Status")
    print("=" * 60)

    for step in STEPS:
        done = step["check"]()
        total = step["total"]
        pct = (done / total * 100) if total > 0 else 0
        status = "DONE" if done >= total else f"{done}/{total}"
        bar_len = 20
        filled = int(bar_len * min(done / total, 1)) if total > 0 else 0
        bar = "#" * filled + "-" * (bar_len - filled)

        print(f"\n  {step['name']:>8}: {step['description']}")
        print(f"           [{bar}] {status} ({pct:.0f}%)")


def copy_to_website():
    """Copy data artifacts to website/data/."""
    WEBSITE_DATA.mkdir(parents=True, exist_ok=True)

    # Copy scholars.json
    src = DATA_DIR / "scholars.json"
    dst = WEBSITE_DATA / "scholars.json"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  Copied scholars.json")

    # Copy profile pics
    pics_src = DATA_DIR / "profile_pics"
    pics_dst = WEBSITE_DATA / "profile_pics"
    if pics_src.exists():
        if pics_dst.exists():
            shutil.rmtree(pics_dst)
        shutil.copytree(pics_src, pics_dst)
        count = len(list(pics_dst.glob("*.jpg"))) + len(list(pics_dst.glob("*.png")))
        print(f"  Copied {count} profile pics")

    # Copy scholar markdown
    md_src = DATA_DIR / "scholar_markdown"
    md_dst = WEBSITE_DATA / "scholar_markdown"
    if md_src.exists():
        if md_dst.exists():
            shutil.rmtree(md_dst)
        shutil.copytree(md_src, md_dst)
        count = len(list(md_dst.glob("*.md")))
        print(f"  Copied {count} markdown files")


def run_step(step_name: str):
    """Run a single pipeline step."""
    step = next((s for s in STEPS if s["name"] == step_name), None)
    if not step:
        print(f"Unknown step: {step_name}")
        print(f"Available: {', '.join(s['name'] for s in STEPS)}")
        sys.exit(1)

    print(f"\nRunning: {step['description']}")

    if step_name == "website":
        copy_to_website()
        return

    if step["command"]:
        result = subprocess.run(step["command"], cwd=PROJECT_ROOT)
        if result.returncode != 0:
            print(f"Step '{step_name}' failed with return code {result.returncode}")
            sys.exit(1)


def run_all():
    """Run all pipeline steps."""
    for step in STEPS:
        print(f"\n{'=' * 60}")
        print(f"Step: {step['name']} — {step['description']}")
        print("=" * 60)

        if step["name"] == "website":
            copy_to_website()
            continue

        if step["command"]:
            result = subprocess.run(step["command"], cwd=PROJECT_ROOT)
            if result.returncode != 0:
                print(f"\nStep '{step['name']}' failed!")
                sys.exit(1)

    print(f"\n{'=' * 60}")
    print("Pipeline complete!")
    show_status()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ScholarBoard.ai pipeline orchestrator")
    parser.add_argument("--step", type=str, default=None,
                        help="Run a specific step (papers, info, embed, umap, subfields, ideas, build, website)")
    parser.add_argument("--execute", action="store_true",
                        help="Run all pipeline steps")
    args = parser.parse_args()

    if args.step:
        run_step(args.step)
    elif args.execute:
        run_all()
    else:
        show_status()


if __name__ == "__main__":
    main()
