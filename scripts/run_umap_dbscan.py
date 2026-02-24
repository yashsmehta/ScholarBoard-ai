"""
Run UMAP dimensionality reduction + DBSCAN clustering on scholar embeddings.

Loads embeddings from data/scholar_embeddings.nc, reduces to 2D with UMAP,
clusters with DBSCAN, saves models and updates scholars.json.

Usage:
    python3 scripts/run_umap_dbscan.py --dry-run    # Preview, no changes
    python3 scripts/run_umap_dbscan.py               # Run full pipeline
"""

import json
import argparse
import sys
from pathlib import Path

import numpy as np
import joblib
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = DATA_DIR / "models"
EMBEDDINGS_PATH = DATA_DIR / "scholar_embeddings.nc"
SCHOLARS_JSON_PATH = DATA_DIR / "scholars.json"


def load_embeddings():
    """Load embeddings from NetCDF."""
    import xarray as xr

    ds = xr.open_dataset(EMBEDDINGS_PATH)
    scholar_ids = ds.scholar_id.values.tolist()
    embeddings = ds.embedding.values
    return scholar_ids, embeddings


def run_umap(embeddings, n_neighbors=10, min_dist=0.1, metric="cosine"):
    """Run UMAP dimensionality reduction."""
    from umap import UMAP
    from sklearn.preprocessing import StandardScaler

    print(f"  Scaling embeddings (shape: {embeddings.shape})...")
    scaler = StandardScaler()
    scaled = scaler.fit_transform(embeddings)

    print(f"  Running UMAP (n_neighbors={n_neighbors}, min_dist={min_dist}, metric={metric})...")
    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=42,
    )
    coords = reducer.fit_transform(scaled)

    return coords, scaler, reducer


def run_dbscan(coords, eps=0.5, min_samples=5):
    """Run DBSCAN clustering on 2D coordinates."""
    from sklearn.cluster import DBSCAN

    print(f"  Running DBSCAN (eps={eps}, min_samples={min_samples})...")
    clusterer = DBSCAN(eps=eps, min_samples=min_samples)
    labels = clusterer.fit_predict(coords)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  Found {n_clusters} clusters, {n_noise} noise points")

    return labels, clusterer


def save_models(scaler, reducer, clusterer):
    """Save trained models."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    joblib.dump(reducer, MODELS_DIR / "umap_model.joblib")
    joblib.dump(clusterer, MODELS_DIR / "umap_dbscan.joblib")
    print(f"  Saved models to {MODELS_DIR}")


def update_scholars_json(scholar_ids, coords, labels):
    """Update scholars.json with new coordinates and cluster labels."""
    with open(SCHOLARS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for i, sid in enumerate(scholar_ids):
        if sid in data:
            data[sid]["umap_projection"] = {
                "x": float(coords[i, 0]),
                "y": float(coords[i, 1]),
            }
            data[sid]["cluster"] = int(labels[i])
            updated += 1

    with open(SCHOLARS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Updated {updated}/{len(scholar_ids)} scholars in {SCHOLARS_JSON_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Run UMAP + DBSCAN on scholar embeddings"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making changes")
    parser.add_argument("--n-neighbors", type=int, default=10,
                        help="UMAP n_neighbors (default: 10)")
    parser.add_argument("--min-dist", type=float, default=0.1,
                        help="UMAP min_dist (default: 0.1)")
    parser.add_argument("--eps", type=float, default=0.5,
                        help="DBSCAN eps (default: 0.5)")
    parser.add_argument("--min-samples", type=int, default=5,
                        help="DBSCAN min_samples (default: 5)")
    args = parser.parse_args()

    if not EMBEDDINGS_PATH.exists():
        print(f"Error: Embeddings not found at {EMBEDDINGS_PATH}")
        print("Run create_paper_embeddings.py first.")
        sys.exit(1)

    print("Loading embeddings...")
    scholar_ids, embeddings = load_embeddings()
    print(f"  Loaded {len(scholar_ids)} scholars, embedding dim {embeddings.shape[1]}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would run:")
        print(f"  UMAP: n_neighbors={args.n_neighbors}, min_dist={args.min_dist}, metric=cosine")
        print(f"  DBSCAN: eps={args.eps}, min_samples={args.min_samples}")
        print(f"  On {len(scholar_ids)} scholar embeddings")
        return

    print("\nRunning UMAP...")
    coords, scaler, reducer = run_umap(
        embeddings,
        n_neighbors=args.n_neighbors,
        min_dist=args.min_dist,
    )

    print("\nRunning DBSCAN...")
    labels, clusterer = run_dbscan(
        coords,
        eps=args.eps,
        min_samples=args.min_samples,
    )

    print("\nSaving models...")
    save_models(scaler, reducer, clusterer)

    print("\nUpdating scholars.json...")
    update_scholars_json(scholar_ids, coords, labels)

    print("\nDone!")


if __name__ == "__main__":
    main()
