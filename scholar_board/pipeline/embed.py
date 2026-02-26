"""
Create paper-based embeddings for scholars.

For each scholar, concatenates title + abstract of their papers.
Scholars without papers are skipped.
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
from scholar_board.db import load_scholars


def build_embedding_pairs() -> list[tuple[str, str]]:
    """Build (scholar_id, text) pairs for embedding from paper data."""
    scholars = load_scholars(is_pi_only=True)
    results = []
    paper_count = 0
    skip_count = 0

    for s in sorted(scholars, key=lambda x: x["scholar_id"]):
        sid = s["scholar_id"]
        paper_text = load_paper_texts(sid)
        if paper_text:
            results.append((sid, paper_text))
            paper_count += 1
        else:
            skip_count += 1

    print(f"  From papers: {paper_count}")
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
