"""
Create embeddings for scholars from research direction + paper text.

For each PI scholar with papers, concatenates:
  1. AI-distilled research direction (from the directions step) — a
     terminology-rich summary of current work
  2. Paper titles + abstracts

The research direction gives a clean, focused signal while papers provide
specific topical detail.  Together they produce richer UMAP layouts than
papers alone.

Embeds with Gemini gemini-embedding-001 (task_type=CLUSTERING, 3072 dims).

Usage:
    uv run -m scholar_board.pipeline.embed --dry-run     # Preview, no API calls
    uv run -m scholar_board.pipeline.embed               # Generate embeddings
    uv run -m scholar_board.pipeline.embed --limit 10    # Process first 10
"""

import argparse
import sys

import numpy as np

from scholar_board.config import (
    EMBEDDINGS_PATH,
    load_paper_texts,
)
from scholar_board.gemini import embed_texts
from scholar_board.db import get_connection, init_db, load_scholars


def _load_research_directions() -> dict[str, str]:
    """Load research direction text from the DB, keyed by scholar ID."""
    conn = get_connection()
    init_db(conn)
    rows = conn.execute(
        "SELECT id, research_direction FROM scholars "
        "WHERE is_pi = 1 AND research_direction IS NOT NULL"
    ).fetchall()
    conn.close()
    return {
        r["id"]: r["research_direction"]
        for r in rows
        if r["research_direction"] and r["research_direction"].strip()
    }


def build_embedding_pairs() -> list[tuple[str, str]]:
    """Build (scholar_id, text) pairs for embedding from research direction + papers."""
    scholars = load_scholars(is_pi_only=True)
    directions = _load_research_directions()
    results = []
    direction_count = 0
    paper_count = 0
    skip_count = 0

    for s in sorted(scholars, key=lambda x: x["scholar_id"]):
        sid = s["scholar_id"]
        direction = directions.get(sid)
        paper_text = load_paper_texts(sid)

        if not paper_text:
            skip_count += 1
            continue

        paper_count += 1
        parts = []
        if direction:
            parts.append(direction)
            direction_count += 1
        parts.append(paper_text)
        results.append((sid, " ".join(parts)))

    print(f"  With research direction: {direction_count}")
    print(f"  With papers: {paper_count}")
    print(f"  Skipped (no papers): {skip_count}")
    return results


def save_embeddings(scholar_ids: list[str], embeddings: np.ndarray):
    """Save embeddings to NetCDF format using xarray."""
    import xarray as xr

    ds = xr.Dataset(
        {"embedding": (["scholar_id", "dim"], embeddings)},
        coords={
            "scholar_id": scholar_ids,
            "dim": list(range(embeddings.shape[1])),
        },
    )
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(EMBEDDINGS_PATH)
    print(f"Saved embeddings to {EMBEDDINGS_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Create paper-based embeddings for scholars"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max scholars to process")
    args = parser.parse_args()

    print("Building embedding texts...")
    pairs = build_embedding_pairs()
    print(f"\nTotal: {len(pairs)} scholars with text to embed")

    if args.limit:
        pairs = pairs[: args.limit]
        print(f"Limiting to {args.limit}")

    if not pairs:
        print("Nothing to embed!")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would embed {len(pairs)} scholars")
        for sid, text in pairs[:5]:
            print(f"  {sid}: {text[:100]}...")
        if len(pairs) > 5:
            print(f"  ... and {len(pairs) - 5} more")
        return

    print(f"\nEmbedding {len(pairs)} scholars...")
    scholar_ids = [sid for sid, _ in pairs]
    texts = [text for _, text in pairs]
    embeddings = embed_texts(texts, task_type="CLUSTERING")

    print(f"\nEmbedding shape: {embeddings.shape}")
    save_embeddings(scholar_ids, embeddings)


if __name__ == "__main__":
    main()
