"""
Run UMAP dimensionality reduction on scholar embeddings.

Loads embeddings from the pipeline directory, reduces to 2D with UMAP,
saves the fitted model and writes coordinates to the database.

Note: Coloring is driven by subfield assignments (see subfields step),
not by clustering.

Usage:
    uv run -m scholar_board.pipeline.cluster --dry-run    # Preview, no changes
    uv run -m scholar_board.pipeline.cluster               # Run full pipeline
"""

import argparse
import sys

import joblib

from scholar_board.config import (
    EMBEDDINGS_PATH,
    MODELS_DIR,
    UMAP_MODEL_PATH,
)
from scholar_board.db import get_connection, init_db, upsert_cluster


def load_embeddings():
    """Load embeddings from NetCDF."""
    import xarray as xr

    ds = xr.open_dataset(EMBEDDINGS_PATH)
    scholar_ids = ds.scholar_id.values.tolist()
    embeddings = ds.embedding.values
    return scholar_ids, embeddings


def run_umap(embeddings, n_neighbors=15, min_dist=0.1, metric="cosine"):
    """Run UMAP dimensionality reduction."""
    from umap import UMAP

    print(f"  Running UMAP (n_neighbors={n_neighbors}, min_dist={min_dist}, metric={metric})...")
    print(f"  Input shape: {embeddings.shape}")
    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=42,
    )
    coords = reducer.fit_transform(embeddings)
    return coords, reducer


def save_model(reducer):
    """Save trained UMAP model."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(reducer, UMAP_MODEL_PATH)
    print(f"  Saved UMAP model to {UMAP_MODEL_PATH}")


def write_coords_to_db(scholar_ids, coords):
    """Write UMAP coordinates to the database (cluster set to 0 for all)."""
    conn = get_connection()
    init_db(conn)

    for i, sid in enumerate(scholar_ids):
        sid = str(sid).zfill(4) if str(sid).isdigit() else str(sid)
        upsert_cluster(conn, sid, float(coords[i, 0]), float(coords[i, 1]), 0)

    conn.close()
    print(f"  Wrote UMAP coords for {len(scholar_ids)} scholars to DB")


def main():
    parser = argparse.ArgumentParser(
        description="Run UMAP on scholar embeddings"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making changes")
    parser.add_argument("--n-neighbors", type=int, default=15,
                        help="UMAP n_neighbors (default: 15)")
    parser.add_argument("--min-dist", type=float, default=0.1,
                        help="UMAP min_dist (default: 0.1)")
    args = parser.parse_args()

    if not EMBEDDINGS_PATH.exists():
        print(f"Error: Embeddings not found at {EMBEDDINGS_PATH}")
        print("Run embed step first.")
        sys.exit(1)

    print("Loading embeddings...")
    scholar_ids, embeddings = load_embeddings()
    print(f"  Loaded {len(scholar_ids)} scholars, embedding dim {embeddings.shape[1]}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would run:")
        print(f"  UMAP: n_neighbors={args.n_neighbors}, min_dist={args.min_dist}, metric=cosine")
        print(f"  On {len(scholar_ids)} scholar embeddings")
        return

    print("\nRunning UMAP...")
    coords, reducer = run_umap(
        embeddings,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
    )

    print("\nSaving model...")
    save_model(reducer)

    print("\nWriting to database...")
    write_coords_to_db(scholar_ids, coords)

    print("\nDone!")


if __name__ == "__main__":
    main()
