"""Shared helpers for the search agent's tools (stdlib only: they run with plain
python3 inside the agent's per-search workspace, next to meta.db)."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the workspace: meta.db, index/, tools/
WORK = ROOT / "work"
FILE_LIMIT = 27_000  # bytes per output file: one file view in agy (~29 KB) or Claude's Read


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{ROOT / 'meta.db'}?mode=ro", uri=True)
    con.execute("PRAGMA query_only = ON")
    return con


def run_select(sql: str) -> tuple[list[str], list[tuple]]:
    if not sql.lstrip().lower().startswith(("select", "with")):
        sys.exit("Only SELECT queries are allowed.")
    try:
        cur = connect().execute(sql)
    except (sqlite3.Error, sqlite3.Warning) as err:
        sys.exit(f"SQL error: {err}")
    return [d[0] for d in cur.description or []], cur.fetchall()


def write_files(prefix: str, ext: str, blocks: list[str]) -> list[str]:
    """Write blocks into work/<prefix>-NN.<ext> files of at most FILE_LIMIT bytes; return their paths."""
    WORK.mkdir(exist_ok=True)
    for old in WORK.glob(f"{prefix}-*.{ext}"):
        old.unlink()
    files, cur = [], ""
    for b in blocks:
        if cur and len((cur + b).encode()) > FILE_LIMIT:
            files.append(cur)
            cur = ""
        cur += b
    if cur:
        files.append(cur)
    paths = []
    for i, text in enumerate(files, 1):
        path = WORK / f"{prefix}-{i:02d}.{ext}"
        path.write_text(text, encoding="utf-8")
        paths.append(str(path.relative_to(ROOT)))
    return paths


def log(event: dict) -> None:
    """Trace for the search log / eval (read by rank.py after the run)."""
    WORK.mkdir(exist_ok=True)
    with open(WORK / "trace.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
