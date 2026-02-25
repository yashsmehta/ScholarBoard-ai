"""
Pipeline status dashboard for ScholarBoard.ai.

Shows per-step completion across disk files and the SQLite database, so you
can see exactly what's done and what still needs to run.

Usage:
    uv run scripts/status.py                      # Full dashboard
    uv run scripts/status.py --pending papers     # List scholars missing papers
    uv run scripts/status.py --pending profiles   # List scholars missing profiles
    uv run scripts/status.py --pending ideas      # List scholars missing ideas
    uv run scripts/status.py --pending pics       # List scholars missing pics
"""

import json
import sqlite3
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scholar_board.config import (
    CSV_PATH,
    EXTRA_RESEARCHERS_PATH,
    PAPERS_DIR,
    PROFILES_DIR,
    IDEAS_DIR,
    EMBEDDINGS_PATH,
    UMAP_MODEL_PATH,
    SUBFIELDS_PATH,
    SCHOLARS_JSON,
    PICS_DIR,
    DB_PATH,
    load_scholars_csv,
)

# ── ANSI colors ────────────────────────────────────────────────────────────────

BOLD  = "\033[1m"
DIM   = "\033[2m"
RESET = "\033[0m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
WHITE  = "\033[97m"


# ── Helpers ────────────────────────────────────────────────────────────────────

def ids_with_files(directory: Path, glob: str, id_from: str) -> set[str]:
    """Return the set of scholar IDs that have a file in directory.

    id_from="prefix" — ID is first segment of stem: {id}_{name}.json
    id_from="suffix" — ID is last segment of stem:  {name}_{id}.jpg
    """
    if not directory.exists():
        return set()
    ids = set()
    for f in directory.glob(glob):
        stem = f.stem
        part = stem.split("_")[0] if id_from == "prefix" else stem.rsplit("_", 1)[-1]
        ids.add(part)
    return ids


def query_db(db_path: Path) -> dict | None:
    """Return a dict of status counts from the SQLite database, or None if missing."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    try:
        r = {}
        def q(sql):
            return conn.execute(sql).fetchone()[0]
        r["scholars"]           = q("SELECT COUNT(*) FROM scholars")
        r["scholars_with_bio"]  = q("SELECT COUNT(*) FROM scholars WHERE bio IS NOT NULL")
        r["scholars_with_umap"] = q("SELECT COUNT(*) FROM scholars WHERE umap_x IS NOT NULL")
        r["scholars_subfield"]  = q("SELECT COUNT(*) FROM scholars WHERE primary_subfield IS NOT NULL")
        r["papers_rows"]        = q("SELECT COUNT(*) FROM papers")
        r["papers_scholars"]    = q("SELECT COUNT(DISTINCT scholar_id) FROM papers")
        r["subfields_rows"]     = q("SELECT COUNT(*) FROM subfields")
        r["ideas_rows"]         = q("SELECT COUNT(*) FROM ideas")
        return r
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def bar(done: int, total: int, width: int = 22) -> str:
    if total == 0:
        return f"{DIM}[{'?' * width}]{RESET}"
    ratio = min(done / total, 1.0)
    filled = int(width * ratio)
    b = "█" * filled + "░" * (width - filled)
    color = GREEN if done >= total else (YELLOW if done > 0 else DIM)
    return f"{color}[{b}]{RESET}"


def pct_str(done: int, total: int) -> str:
    if total == 0:
        return f"{DIM}  —{RESET}"
    p = int(done / total * 100)
    color = GREEN if p == 100 else (YELLOW if p > 0 else DIM)
    return f"{color}{p:>3}%{RESET}"


# ── Dashboard ──────────────────────────────────────────────────────────────────

def show_dashboard():
    all_scholars = load_scholars_csv()
    total = len(all_scholars)

    vss_count   = sum(1 for s in all_scholars if not str(s["scholar_id"]).startswith("E"))
    extra_count = total - vss_count

    # Per-scholar completion sets
    papers_ids   = ids_with_files(PAPERS_DIR,   "*.json", "prefix")
    profiles_ids = ids_with_files(PROFILES_DIR, "*.json", "prefix")
    ideas_ids    = ids_with_files(IDEAS_DIR,     "*.json", "prefix")
    pics_ids     = ids_with_files(PICS_DIR, "*.jpg", "suffix") | ids_with_files(PICS_DIR, "*.png", "suffix")

    # Subfields: per-scholar JSON (keyed by scholar_id)
    subfields_ids: set[str] = set()
    if SUBFIELDS_PATH.exists():
        with open(SUBFIELDS_PATH) as f:
            subfields_ids = set(json.load(f).keys())

    db = query_db(DB_PATH)

    W = 70
    print()
    print(f"{CYAN}{BOLD}{'═' * W}{RESET}")
    print(f"{CYAN}{BOLD}  ScholarBoard.ai — Pipeline Status{RESET}")
    print(f"{CYAN}{BOLD}{'═' * W}{RESET}")
    print()

    # ── Researcher totals ──
    print(f"  {BOLD}Researchers{RESET}")
    vss_ok = f"{GREEN}✓{RESET}" if CSV_PATH.exists() else f"{RED}✗{RESET}"
    print(f"    {vss_ok} VSS      {vss_count:>4}  {DIM}vss_data.csv{RESET}")
    if EXTRA_RESEARCHERS_PATH.exists():
        print(f"    {GREEN}✓{RESET} Extra    {extra_count:>4}  {DIM}extra_researchers.csv{RESET}")
    else:
        print(f"    {DIM}— Extra       0  not generated yet  →  uv run scripts/run_pipeline.py --step discover{RESET}")
    print(f"    {'─' * 30}")
    print(f"    {BOLD}Total    {total:>4}{RESET}")
    print()

    # ── Step rows ──
    HDR = f"  {'#':<3}  {'Description':<32}  {'Files':>9}  {'DB':>7}  {'':>28}  {'':>4}"
    print(f"{BOLD}{HDR}{RESET}")
    print(f"  {DIM}{'─' * 66}{RESET}")

    def row(num, desc, done, step_total, db_val):
        """Print one pipeline step row."""
        # Files column: "N/total" for per-scholar, "✓" / "✗" for binary
        if step_total == 1:
            files_col = f"{GREEN}✓{RESET}      " if done else f"{RED}✗{RESET}      "
        else:
            files_col = f"{done:>{len(str(step_total))}}/{step_total}"

        # DB column
        db_col = f"{db_val:>7}" if db_val is not None else f"{DIM}{'—':>7}{RESET}"

        b = bar(done, step_total)
        p = pct_str(done, step_total)
        print(f"  {BOLD}{num}{RESET}    {desc:<32}  {files_col:>9}  {db_col}  {b}  {p}")

    row("0", "Discover extra researchers",
        1 if EXTRA_RESEARCHERS_PATH.exists() else 0, 1, None)

    row("1", "Fetch papers",
        len(papers_ids), total,
        db["papers_scholars"] if db else None)

    row("2", "Fetch profiles",
        len(profiles_ids), total,
        db["scholars_with_bio"] if db else None)

    row("3", "Embed paper text",
        1 if EMBEDDINGS_PATH.exists() else 0, 1, None)

    row("4", "UMAP + HDBSCAN clustering",
        1 if UMAP_MODEL_PATH.exists() else 0, 1,
        db["scholars_with_umap"] if db else None)

    row("5", "Assign subfield tags",
        len(subfields_ids), total,
        db["scholars_subfield"] if db else None)

    row("6", "Generate research ideas",
        len(ideas_ids), total,
        db["ideas_rows"] if db else None)

    row("7", "Build scholars.json",
        1 if SCHOLARS_JSON.exists() else 0, 1, None)

    row("8", "Download profile pics",
        len(pics_ids), total, None)

    print()

    # ── DB summary ──
    if db:
        print(f"  {BOLD}SQLite Database{RESET}  {DIM}{DB_PATH.relative_to(PROJECT_ROOT)}{RESET}")
        print(f"    {'Table':<12}  {'Rows':>6}  {'Detail'}")
        print(f"    {DIM}{'─' * 42}{RESET}")
        print(f"    {'scholars':<12}  {db['scholars']:>6}  "
              f"{DIM}bio: {db['scholars_with_bio']}, umap: {db['scholars_with_umap']}, subfield: {db['scholars_subfield']}{RESET}")
        print(f"    {'papers':<12}  {db['papers_rows']:>6}  {DIM}across {db['papers_scholars']} scholars{RESET}")
        print(f"    {'subfields':<12}  {db['subfields_rows']:>6}")
        print(f"    {'ideas':<12}  {db['ideas_rows']:>6}")
    else:
        print(f"  {DIM}SQLite Database  not found — will be created on first pipeline run{RESET}")

    print()

    # ── Pending summary ──
    all_ids = {str(s["scholar_id"]) for s in all_scholars}
    pending = {
        "papers":   all_ids - papers_ids,
        "profiles": all_ids - profiles_ids,
        "subfields": all_ids - subfields_ids,
        "ideas":    all_ids - ideas_ids,
        "pics":     all_ids - pics_ids,
    }

    if any(pending.values()):
        print(f"  {BOLD}Pending  {DIM}(use --pending <step> to list scholar names){RESET}")
        for step_name, p_ids in pending.items():
            if p_ids:
                cmd = f"uv run scripts/run_pipeline.py --step {step_name}" if step_name != "subfields" else "uv run scripts/run_pipeline.py --step subfields"
                print(f"    {YELLOW}{step_name:<12}{RESET}  {len(p_ids):>4} scholars  {DIM}→  {cmd}{RESET}")
        print()
    else:
        print(f"  {GREEN}{BOLD}All per-scholar steps complete!{RESET}")
        print()


# ── Pending list ───────────────────────────────────────────────────────────────

def show_pending(step_name: str):
    PER_SCHOLAR_STEPS = {
        "papers":   (PAPERS_DIR,   "*.json", "prefix"),
        "profiles": (PROFILES_DIR, "*.json", "prefix"),
        "ideas":    (IDEAS_DIR,    "*.json", "prefix"),
        "pics":     (PICS_DIR,     "*.jpg",  "suffix"),
    }

    # Subfields needs special handling (JSON dict, not directory)
    if step_name == "subfields":
        all_scholars = load_scholars_csv()
        all_ids = {str(s["scholar_id"]): s for s in all_scholars}
        done_ids: set[str] = set()
        if SUBFIELDS_PATH.exists():
            with open(SUBFIELDS_PATH) as f:
                done_ids = set(json.load(f).keys())
        pending_ids = sorted(set(all_ids) - done_ids)
        _print_pending_list("subfields", pending_ids, all_ids, len(all_scholars))
        return

    if step_name not in PER_SCHOLAR_STEPS:
        valid = ", ".join(list(PER_SCHOLAR_STEPS) + ["subfields"])
        print(f"Unknown step '{step_name}'. Valid options: {valid}")
        sys.exit(1)

    all_scholars = load_scholars_csv()
    id_to_scholar = {str(s["scholar_id"]): s for s in all_scholars}

    directory, glob, id_from = PER_SCHOLAR_STEPS[step_name]
    done_ids = ids_with_files(directory, glob, id_from)
    if step_name == "pics":
        done_ids |= ids_with_files(directory, "*.png", id_from)

    pending_ids = sorted(set(id_to_scholar) - done_ids)
    _print_pending_list(step_name, pending_ids, id_to_scholar, len(all_scholars))


def _print_pending_list(step_name, pending_ids, id_to_scholar, total):
    print()
    print(f"  {BOLD}Pending for '{step_name}':{RESET}  "
          f"{YELLOW}{len(pending_ids)}{RESET} / {total} scholars remaining")
    print()
    if not pending_ids:
        print(f"  {GREEN}Nothing pending — step is complete.{RESET}")
    else:
        print(f"  {'ID':<8}  {'Name':<35}  Institution")
        print(f"  {DIM}{'─' * 72}{RESET}")
        for sid in pending_ids:
            s = id_to_scholar.get(sid, {})
            name = s.get("scholar_name", "?")
            inst = s.get("scholar_institution", "?")
            print(f"  {DIM}{sid:<8}{RESET}  {name:<35}  {DIM}{inst}{RESET}")
    print()
    print(f"  To run:  {CYAN}uv run scripts/run_pipeline.py --step {step_name}{RESET}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ScholarBoard.ai pipeline status dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  uv run scripts/status.py                    show full dashboard
  uv run scripts/status.py --pending papers   list scholars missing papers
  uv run scripts/status.py --pending ideas    list scholars missing ideas
""",
    )
    parser.add_argument(
        "--pending", type=str, default=None, metavar="STEP",
        help="List scholars pending for STEP (papers, profiles, subfields, ideas, pics)",
    )
    args = parser.parse_args()

    if args.pending:
        show_pending(args.pending)
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
