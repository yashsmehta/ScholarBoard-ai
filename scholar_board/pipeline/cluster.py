"""
Run UMAP dimensionality reduction + HDBSCAN clustering on scholar embeddings.

Loads embeddings from the pipeline directory, reduces to 2D with UMAP,
clusters with HDBSCAN, saves models and writes results to the database.

Usage:
    uv run -m scholar_board.pipeline.cluster --dry-run    # Preview, no changes
    uv run -m scholar_board.pipeline.cluster               # Run full pipeline
"""

import argparse
import sys

import numpy as np
import joblib

from scholar_board.config import (
    EMBEDDINGS_PATH,
    MODELS_DIR,
    UMAP_MODEL_PATH,
    HDBSCAN_MODEL_PATH,
)
from scholar_board.db import get_connection, init_db, upsert_cluster, load_scholars


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


def run_hdbscan(coords, min_cluster_size=10, min_samples=3):
    """Run HDBSCAN clustering on 2D coordinates."""
    from sklearn.cluster import HDBSCAN

    print(f"  Running HDBSCAN (min_cluster_size={min_cluster_size}, min_samples={min_samples})...")
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels = clusterer.fit_predict(coords)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  Found {n_clusters} clusters, {n_noise} noise points "
          f"({n_noise}/{len(labels)}, {n_noise/len(labels)*100:.1f}%)")

    from collections import Counter
    counts = Counter(labels)
    sizes = sorted([v for k, v in counts.items() if k != -1], reverse=True)
    if sizes:
        print(f"  Cluster sizes: min={min(sizes)}, max={max(sizes)}, median={np.median(sizes):.0f}")

    return labels, clusterer


def save_models(reducer, clusterer):
    """Save trained models."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(reducer, UMAP_MODEL_PATH)
    joblib.dump(clusterer, HDBSCAN_MODEL_PATH)
    print(f"  Saved models to {MODELS_DIR}")


def write_cluster_to_db(scholar_ids, coords, labels):
    """Write UMAP coordinates and cluster labels directly to the database."""
    conn = get_connection()
    init_db(conn)

    for i, sid in enumerate(scholar_ids):
        sid = str(sid).zfill(4) if str(sid).isdigit() else str(sid)
        upsert_cluster(conn, sid, float(coords[i, 0]), float(coords[i, 1]), int(labels[i]))

    conn.close()
    print(f"  Wrote UMAP coords + cluster for {len(scholar_ids)} scholars to DB")


def main():
    parser = argparse.ArgumentParser(
        description="Run UMAP + HDBSCAN on scholar embeddings"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making changes")
    parser.add_argument("--n-neighbors", type=int, default=15,
                        help="UMAP n_neighbors (default: 15)")
    parser.add_argument("--min-dist", type=float, default=0.1,
                        help="UMAP min_dist (default: 0.1)")
    parser.add_argument("--min-cluster-size", type=int, default=10,
                        help="HDBSCAN min_cluster_size (default: 10)")
    parser.add_argument("--min-samples", type=int, default=3,
                        help="HDBSCAN min_samples (default: 3)")
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
        print(f"  HDBSCAN: min_cluster_size={args.min_cluster_size}, min_samples={args.min_samples}")
        print(f"  On {len(scholar_ids)} scholar embeddings")
        return

    print("\nRunning UMAP...")
    coords, reducer = run_umap(
        embeddings,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
    )

    print("\nRunning HDBSCAN...")
    labels, clusterer = run_hdbscan(
        coords,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
    )

    print("\nSaving models...")
    save_models(reducer, clusterer)

    print("\nWriting to database...")
    write_cluster_to_db(scholar_ids, coords, labels)

    print("\nDone!")


if __name__ == "__main__":
    main()
