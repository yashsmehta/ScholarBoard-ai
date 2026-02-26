"""
Pipeline orchestrator for ScholarBoard.ai

Shows pipeline status and runs steps in order with live progress.

Usage:
    python3 scripts/run_pipeline.py                  # Show status dashboard
    python3 scripts/run_pipeline.py --step papers    # Run a single step
    python3 scripts/run_pipeline.py --execute        # Run all steps
    python3 scripts/run_pipeline.py --from embed     # Run from a specific step onward
"""

import subprocess
import sys
import time
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

# Import path constants from config to keep status checks in sync
import sys as _sys
_sys.path.insert(0, str(PROJECT_ROOT))
from scholar_board.config import (
    PIPELINE_DIR,
    BUILD_DIR,
    DB_PATH,
    EXTRA_RESEARCHERS_PATH,
)

# ── ANSI colors ───────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
WHITE = "\033[97m"
BG_GREEN = "\033[42m"
BG_RED = "\033[41m"
BG_YELLOW = "\033[43m"

# ── Pipeline steps ────────────────────────────────────────────────────────

STEPS = [
    {
        "name": "seed",
        "icon": "0",
        "description": "Seed DB with all researchers (VSS + extra)",
        "model": "gemini-3-flash-preview (dedup only)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.seed"],
        "check": lambda: int(DB_PATH.exists() and __import__('sqlite3').connect(DB_PATH).execute("SELECT COUNT(*) FROM scholars").fetchone()[0]),
        "total": 1091,  # ~725 VSS + ~366 extra
    },
    {
        "name": "discover",
        "icon": "0",
        "description": "Discover extra researchers via Gemini subfield search",
        "model": "gemini-3-flash-preview",
        "command": [PYTHON, "-m", "scholar_board.pipeline.fetch_extra_researchers"],
        "check": lambda: 1 if EXTRA_RESEARCHERS_PATH.exists() else 0,
        "total": 1,
    },
    {
        "name": "papers",
        "icon": "1",
        "description": "Fetch papers via Gemini grounded search",
        "model": "gemini-3-flash-preview",
        "command": [PYTHON, "-m", "scholar_board.pipeline.fetch_papers"],
        "check": lambda: len(list((PIPELINE_DIR / "scholar_papers").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "profiles",
        "icon": "2",
        "description": "Fetch researcher profiles + normalize bios",
        "model": "gemini-3-flash-preview",
        "command": [PYTHON, "-m", "scholar_board.pipeline.fetch_profiles"],
        "check": lambda: len(list((PIPELINE_DIR / "scholar_profiles").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "embed",
        "icon": "3",
        "description": "Embed paper text for clustering",
        "model": "gemini-embedding-001 (CLUSTERING)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.embed"],
        "check": lambda: 1 if (PIPELINE_DIR / "scholar_embeddings.nc").exists() else 0,
        "total": 1,
    },
    {
        "name": "umap",
        "icon": "4",
        "description": "UMAP projection + HDBSCAN clustering",
        "model": "n/a (local)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.cluster"],
        "check": lambda: 1 if (PIPELINE_DIR / "models" / "umap_model.joblib").exists() else 0,
        "total": 1,
    },
    {
        "name": "subfields",
        "icon": "5",
        "description": "Assign subfield tags via semantic similarity",
        "model": "gemini-embedding-001 (SEMANTIC_SIMILARITY)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.subfields"],
        "check": lambda: 1 if (PIPELINE_DIR / "scholar_subfields.json").exists() else 0,
        "total": 1,
    },
    {
        "name": "ideas",
        "icon": "6",
        "description": "Generate AI research directions",
        "model": "gemini-3.1-pro-preview (HIGH thinking)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.ideas"],
        "check": lambda: len(list((PIPELINE_DIR / "scholar_ideas").glob("*.json"))),
        "total": 730,
    },
    {
        "name": "build",
        "icon": "7",
        "description": "Consolidate all data into scholars.json",
        "model": "n/a (local)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.build"],
        "check": lambda: 1 if (BUILD_DIR / "scholars.json").exists() else 0,
        "total": 1,
    },
    {
        "name": "pics",
        "icon": "8",
        "description": "Download profile pictures",
        "model": "Serper.dev image search",
        "command": [PYTHON, "-m", "scholar_board.pipeline.pics", "--skip-existing"],
        "check": lambda: len(list((BUILD_DIR / "profile_pics").glob("*.jpg"))) + len(list((BUILD_DIR / "profile_pics").glob("*.png"))),
        "total": 730,
    },
]


def get_terminal_width():
    return shutil.get_terminal_size((80, 24)).columns


def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m {int(s)}s"
    else:
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{int(h)}h {int(m)}m"


def progress_bar(done, total, width=30):
    if total == 0:
        return f"[{'?' * width}]"
    ratio = min(done / total, 1.0)
    filled = int(width * ratio)
    bar = "=" * filled
    if filled < width:
        bar += ">" + " " * (width - filled - 1)
    else:
        bar = "=" * width

    if done >= total:
        color = GREEN
    elif done > 0:
        color = YELLOW
    else:
        color = DIM

    return f"{color}[{bar}]{RESET}"


def status_label(done, total):
    if done >= total:
        return f"{GREEN}{BOLD}DONE{RESET}"
    elif done > 0:
        return f"{YELLOW}{done}/{total}{RESET}"
    else:
        return f"{DIM}pending{RESET}"


# ── Dashboard ─────────────────────────────────────────────────────────────

def show_status():
    w = get_terminal_width()
    header = " ScholarBoard.ai Pipeline "
    pad = max(0, (w - len(header)) // 2)

    print()
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")
    print(f"{CYAN}{BOLD}{' ' * pad}{header}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")
    print()

    total_done = 0
    total_total = 0

    for step in STEPS:
        done = step["check"]()
        total = step["total"]
        total_done += min(done, total)
        total_total += total

        bar = progress_bar(done, total, width=25)
        label = status_label(done, total)
        pct = (done / total * 100) if total > 0 else 0

        print(f"  {BOLD}{WHITE}{step['icon']}.{RESET} {BOLD}{step['description']:<45}{RESET}")
        print(f"     {bar}  {label}  {DIM}({pct:.0f}%){RESET}")
        print(f"     {DIM}{step['model']}{RESET}")
        print()

    # Overall progress
    overall_pct = (total_done / total_total * 100) if total_total > 0 else 0
    overall_bar = progress_bar(total_done, total_total, width=40)
    print(f"  {BOLD}Overall:{RESET} {overall_bar} {overall_pct:.0f}%")
    print()


# ── Step execution ────────────────────────────────────────────────────────

def print_step_header(step, index, total_steps):
    w = get_terminal_width()
    print()
    print(f"{CYAN}{'─' * w}{RESET}")
    print(f"  {BOLD}{WHITE}[{index}/{total_steps}] {step['description']}{RESET}")
    print(f"  {DIM}Model: {step['model']}{RESET}")
    print(f"  {DIM}Command: {' '.join(step['command'][-1:])}{RESET}")
    print(f"{CYAN}{'─' * w}{RESET}")
    print()


def print_step_result(step, elapsed, success):
    done = step["check"]()
    total = step["total"]
    bar = progress_bar(done, total, width=20)

    if success:
        icon = f"{GREEN}{BOLD}OK{RESET}"
    else:
        icon = f"{RED}{BOLD}FAIL{RESET}"

    print()
    print(f"  {icon}  {bar}  {status_label(done, total)}  {DIM}({format_time(elapsed)}){RESET}")
    print()


def run_step(step_name: str):
    step = next((s for s in STEPS if s["name"] == step_name), None)
    if not step:
        print(f"{RED}Unknown step: {step_name}{RESET}")
        print(f"Available: {', '.join(s['name'] for s in STEPS)}")
        sys.exit(1)

    idx = STEPS.index(step) + 1
    print_step_header(step, idx, len(STEPS))

    start = time.time()
    result = subprocess.run(step["command"], cwd=PROJECT_ROOT)
    elapsed = time.time() - start

    success = result.returncode == 0
    print_step_result(step, elapsed, success)

    if not success:
        print(f"{RED}{BOLD}Step '{step_name}' failed with exit code {result.returncode}{RESET}")
        sys.exit(1)


def run_from(start_step: str):
    start_idx = None
    for i, step in enumerate(STEPS):
        if step["name"] == start_step:
            start_idx = i
            break
    if start_idx is None:
        print(f"{RED}Unknown step: {start_step}{RESET}")
        print(f"Available: {', '.join(s['name'] for s in STEPS)}")
        sys.exit(1)

    steps_to_run = STEPS[start_idx:]
    run_steps(steps_to_run)


def run_all():
    run_steps(STEPS)


def run_steps(steps):
    w = get_terminal_width()
    n = len(steps)

    print()
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")
    print(f"{CYAN}{BOLD}  ScholarBoard.ai Pipeline — Running {n} step{'s' if n != 1 else ''}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")

    pipeline_start = time.time()
    step_times = []

    for i, step in enumerate(steps):
        global_idx = STEPS.index(step) + 1
        print_step_header(step, global_idx, len(STEPS))

        start = time.time()
        result = subprocess.run(step["command"], cwd=PROJECT_ROOT)
        elapsed = time.time() - start
        step_times.append((step, elapsed, result.returncode == 0))

        success = result.returncode == 0
        print_step_result(step, elapsed, success)

        if not success:
            print(f"{RED}{BOLD}Pipeline stopped at step '{step['name']}'{RESET}")
            print_summary(step_times, time.time() - pipeline_start)
            sys.exit(1)

    print_summary(step_times, time.time() - pipeline_start)
    print()
    show_status()


def print_summary(step_times, total_elapsed):
    w = get_terminal_width()
    print()
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")
    print(f"  {BOLD}Pipeline Summary{RESET}")
    print(f"{CYAN}{'─' * w}{RESET}")

    for step, elapsed, success in step_times:
        icon = f"{GREEN}OK{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {icon}  {step['description']:<45} {DIM}{format_time(elapsed):>8}{RESET}")

    print(f"{CYAN}{'─' * w}{RESET}")
    print(f"  {BOLD}Total time: {format_time(total_elapsed)}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * w}{RESET}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ScholarBoard.ai pipeline orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
steps:
  seed       Seed DB with all researchers (VSS + extra, deduplicated)
  discover   Discover extra researchers via Gemini subfield search
  papers     Fetch papers via Gemini grounded search
  profiles   Fetch researcher profiles + normalize bios
  embed      Embed paper text (Gemini CLUSTERING)
  umap       UMAP projection + HDBSCAN clustering
  subfields  Assign subfield tags (Gemini SEMANTIC_SIMILARITY)
  ideas      Generate AI research directions (Gemini 3.1 Pro)
  build      Consolidate all data into scholars.json
  pics       Download profile pictures (Serper.dev)
""",
    )
    parser.add_argument("--step", type=str, default=None, metavar="NAME",
                        help="Run a single step")
    parser.add_argument("--from", type=str, default=None, dest="from_step", metavar="NAME",
                        help="Run from a specific step onward")
    parser.add_argument("--execute", action="store_true",
                        help="Run all pipeline steps")
    args = parser.parse_args()

    if args.step:
        run_step(args.step)
    elif args.from_step:
        run_from(args.from_step)
    elif args.execute:
        run_all()
    else:
        show_status()


if __name__ == "__main__":
    main()
