"""SQLite database layer for ScholarBoard.ai.

Each pipeline step writes its canonical JSON files (for human inspection)
AND upserts into this database (the queryable source of truth).

Embeddings are kept in scholar_embeddings.nc — not here.

Schema:
    scholars   — one row per researcher (id, name, institution, UMAP coords, ...)
    papers     — one row per paper, FK → scholars
    subfields  — one row per (scholar, subfield) assignment, FK → scholars
    ideas      — one row per AI-generated research idea, FK → scholars
"""

import sqlite3

from scholar_board.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection with WAL mode enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't already exist (idempotent)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scholars (
            id                 TEXT PRIMARY KEY,
            name               TEXT NOT NULL,
            institution        TEXT,
            department         TEXT,
            lab_name           TEXT,
            lab_url            TEXT,
            main_research_area TEXT,
            bio                TEXT,
            umap_x             REAL,
            umap_y             REAL,
            cluster            INTEGER,
            primary_subfield   TEXT,
            profile_pic        TEXT
        );

        CREATE TABLE IF NOT EXISTS papers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            scholar_id TEXT NOT NULL REFERENCES scholars(id),
            title      TEXT NOT NULL,
            abstract   TEXT,
            year       TEXT,
            venue      TEXT,
            citations  TEXT,
            authors    TEXT,
            url        TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_papers_scholar ON papers(scholar_id);

        CREATE TABLE IF NOT EXISTS subfields (
            scholar_id TEXT NOT NULL REFERENCES scholars(id),
            subfield   TEXT NOT NULL,
            score      REAL,
            is_primary INTEGER DEFAULT 0,
            PRIMARY KEY (scholar_id, subfield)
        );
        CREATE INDEX IF NOT EXISTS idx_subfields_scholar ON subfields(scholar_id);

        CREATE TABLE IF NOT EXISTS ideas (
            scholar_id        TEXT PRIMARY KEY REFERENCES scholars(id),
            research_thread   TEXT,
            open_question     TEXT,
            title             TEXT,
            hypothesis        TEXT,
            approach          TEXT,
            scientific_impact TEXT,
            why_now           TEXT
        );
    """)
    conn.commit()


def ensure_scholar(
    conn: sqlite3.Connection,
    id: str,
    name: str,
    institution: str | None = None,
    department: str | None = None,
) -> None:
    """Insert a base scholar record if one doesn't already exist."""
    conn.execute(
        "INSERT OR IGNORE INTO scholars (id, name, institution, department) "
        "VALUES (?, ?, ?, ?)",
        (id, name, institution, department),
    )
    conn.commit()


def upsert_profile(
    conn: sqlite3.Connection,
    scholar_id: str,
    **fields,
) -> None:
    """Update profile fields for a scholar.

    Accepted keyword args: bio, lab_name, lab_url, main_research_area, department.
    Only non-None values are written.
    """
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        return
    placeholders = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE scholars SET {placeholders} WHERE id = ?",
        (*fields.values(), scholar_id),
    )
    conn.commit()


def upsert_papers(
    conn: sqlite3.Connection,
    scholar_id: str,
    papers: list[dict],
) -> None:
    """Replace all papers for a scholar (delete + re-insert)."""
    conn.execute("DELETE FROM papers WHERE scholar_id = ?", (scholar_id,))
    conn.executemany(
        "INSERT INTO papers "
        "(scholar_id, title, abstract, year, venue, citations, authors, url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                scholar_id,
                p.get("title", ""),
                p.get("abstract"),
                p.get("year"),
                p.get("venue"),
                p.get("citations", "0"),
                p.get("authors"),
                p.get("url"),
            )
            for p in papers
        ],
    )
    conn.commit()


def upsert_subfields(
    conn: sqlite3.Connection,
    scholar_id: str,
    primary_subfield: str,
    subfields: list[dict],
) -> None:
    """Replace subfield assignments for a scholar."""
    conn.execute("DELETE FROM subfields WHERE scholar_id = ?", (scholar_id,))
    conn.execute(
        "UPDATE scholars SET primary_subfield = ? WHERE id = ?",
        (primary_subfield, scholar_id),
    )
    conn.executemany(
        "INSERT INTO subfields (scholar_id, subfield, score, is_primary) "
        "VALUES (?, ?, ?, ?)",
        [
            (
                scholar_id,
                sf["subfield"],
                sf.get("score"),
                1 if sf["subfield"] == primary_subfield else 0,
            )
            for sf in subfields
        ],
    )
    conn.commit()


def upsert_idea(
    conn: sqlite3.Connection,
    scholar_id: str,
    idea: dict,
) -> None:
    """Insert or replace a scholar's AI-generated research idea."""
    conn.execute(
        "INSERT OR REPLACE INTO ideas "
        "(scholar_id, research_thread, open_question, title, "
        "hypothesis, approach, scientific_impact, why_now) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            scholar_id,
            idea.get("research_thread"),
            idea.get("open_question"),
            idea.get("title"),
            idea.get("hypothesis"),
            idea.get("approach"),
            idea.get("scientific_impact"),
            idea.get("why_now"),
        ),
    )
    conn.commit()


def upsert_cluster(
    conn: sqlite3.Connection,
    scholar_id: str,
    umap_x: float,
    umap_y: float,
    cluster: int,
) -> None:
    """Update UMAP 2D coordinates and cluster label for a scholar."""
    conn.execute(
        "UPDATE scholars SET umap_x = ?, umap_y = ?, cluster = ? WHERE id = ?",
        (umap_x, umap_y, cluster, scholar_id),
    )
    conn.commit()


def upsert_profile_pic(
    conn: sqlite3.Connection,
    scholar_id: str,
    filename: str,
) -> None:
    """Update the profile_pic filename for a scholar."""
    conn.execute(
        "UPDATE scholars SET profile_pic = ? WHERE id = ?",
        (filename, scholar_id),
    )
    conn.commit()
