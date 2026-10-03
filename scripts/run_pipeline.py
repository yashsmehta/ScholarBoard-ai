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
        "icon": "1",
        "description": "Seed DB from the VSS list + extra_researchers.csv (one-time bootstrap)",
        "model": "n/a (local, fuzzy name dedup)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.seed"],
        "check": lambda: int(DB_PATH.exists() and __import__('sqlite3').connect(DB_PATH).execute("SELECT COUNT(*) FROM scholars").fetchone()[0]),
        "total": 934,
    },
    {
        "name": "profiles",
        "icon": "2",
        "description": "Profile agent for scholars not yet profiled: affiliation, photo, stats, papers, summary, topic areas",
        "model": "claude-sonnet-5-5 (headless Claude Code, subscription)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.profile_agent", "--pending"],
        "check": lambda: int(DB_PATH.exists() and __import__('sqlite3').connect(DB_PATH).execute("SELECT COUNT(*) FROM scholars WHERE is_pi IS NOT NULL").fetchone()[0]),
        "total": 934,
    },
    {
        "name": "embed",
        "icon": "3",
        "description": "Embed research direction + papers for the map (PI only; full re-embed)",
        "model": "gemini-embedding-001 (CLUSTERING)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.embed"],
        "check": lambda: 1 if (PIPELINE_DIR / "scholar_embeddings.nc").exists() else 0,
        "total": 1,
    },
    {
        "name": "umap",
        "icon": "4",
        "description": "UMAP projection — 2D layout for map (PI only; full refit)",
        "model": "n/a (local)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.cluster"],
        "check": lambda: int(DB_PATH.exists() and __import__('sqlite3').connect(DB_PATH).execute("SELECT COUNT(*) FROM scholars WHERE umap_x IS NOT NULL").fetchone()[0]),
        "total": 797,
    },
    {
        "name": "field_directions",
        "icon": "5",
        "description": "Synthesize field-level research summaries (21 topic areas)",
        "model": "gemini-3.1-pro-preview (HIGH thinking)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.field_directions"],
        "check": lambda: len(__import__('json').loads((BUILD_DIR / "field_directions.json").read_text())) if (BUILD_DIR / "field_directions.json").exists() else 0,
        "total": 21,
    },
    {
        "name": "build",
        "icon": "6",
        "description": "Consolidate all data into scholars.json (PI only)",
        "model": "n/a (local)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.build"],
        "check": lambda: 1 if (BUILD_DIR / "scholars.json").exists() else 0,
        "total": 1,
    },
    {
        "name": "search_cards",
        "icon": "7",
        "description": "AI Search keywords (up to 10 per PI) for PIs whose profile changed",
        "model": "gemini-3.8-flash (25 parallel calls)",
        "command": [PYTHON, "-m", "scholar_board.pipeline.search_cards"],
        "check": lambda: len(__import__('json').loads((BUILD_DIR / "search_cards.json").read_text())) if (BUILD_DIR / "search_cards.json").exists() else 0,
        "total": 797,
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
steps (run in order):
  seed             Seed DB from VSS CSV + extra_researchers.csv (one-time bootstrap)
  profiles         Profile agent (headless Claude Code) for every scholar not yet profiled
  embed            Embed research direction + papers for the map (Gemini CLUSTERING, 3072 dims)
  umap             UMAP 2D projection — the map layout (full refit)
  field_directions Field-level summaries per topic area (Gemini 3.1 Pro)
  build            Export scholars.json from DB (PI only)
  search_cards     AI Search keywords for new/changed PIs (Gemini Flash, 25 in parallel)

Adding a new PI (agent + placement on the existing map + build + search card, in one go):
  uv run -m scholar_board.pipeline.profile_agent --add "Full Name" --hint "Institution"
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
