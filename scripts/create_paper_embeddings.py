"""
Create paper-based embeddings for scholars.

For each scholar, concatenates title + abstract of their papers.
Falls back to VSS abstract from vss_data.csv if no papers available.
Embeds with OpenAI text-embedding-3-small for consistency with search_embeddings.py.

Usage:
    python3 scripts/create_paper_embeddings.py --dry-run     # Preview, no API calls
    python3 scripts/create_paper_embeddings.py               # Generate embeddings
    python3 scripts/create_paper_embeddings.py --limit 10    # Process first 10
"""

import csv
import json
import argparse
import sys
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
PAPERS_DIR = DATA_DIR / "scholar_papers"
OUTPUT_PATH = DATA_DIR / "scholar_embeddings.nc"

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def load_scholars_csv() -> dict[str, dict]:
    """Load scholars from vss_data.csv (unique by scholar_id)."""
    csv_path = DATA_DIR / "vss_data.csv"
    scholars = {}
    abstracts_by_id = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("scholar_id", "").strip().strip("\"'")
            if not sid:
                continue
            if sid.isdigit():
                sid = sid.zfill(4)

            abstract = row.get("abstract", "").strip()

            if sid not in scholars:
                scholars[sid] = {
                    "id": sid,
                    "name": row.get("scholar_name", "").strip(),
                }
                abstracts_by_id[sid] = []

            if abstract:
                abstracts_by_id[sid].append(abstract)

    return scholars, abstracts_by_id


def load_paper_texts(scholar_id: str) -> str | None:
    """Load concatenated paper titles + abstracts for a scholar."""
    for fpath in PAPERS_DIR.glob(f"{scholar_id}_*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            papers = data.get("papers", [])
            if not papers:
                return None

            parts = []
            for p in papers[:5]:  # Top 5 papers
                title = p.get("title", "")
                abstract = p.get("abstract", "")
                if title:
                    text = title
                    if abstract:
                        text += ". " + abstract
                    parts.append(text)

            return " ".join(parts) if parts else None
        except (json.JSONDecodeError, KeyError):
            continue
    return None


def build_embedding_texts(
    scholars: dict, abstracts_by_id: dict
) -> list[tuple[str, str]]:
    """Build (scholar_id, text) pairs for embedding.

    Priority: paper texts > VSS abstracts
    """
    results = []
    paper_count = 0
    abstract_count = 0
    skip_count = 0

    for sid in sorted(scholars.keys()):
        paper_text = load_paper_texts(sid)
        if paper_text:
            results.append((sid, paper_text))
            paper_count += 1
        elif abstracts_by_id.get(sid):
            # Concatenate all VSS abstracts as fallback
            text = " ".join(abstracts_by_id[sid])
            results.append((sid, text))
            abstract_count += 1
        else:
            skip_count += 1

    print(f"  From papers: {paper_count}")
    print(f"  From VSS abstracts: {abstract_count}")
    print(f"  Skipped (no text): {skip_count}")

    return results


def embed_texts(texts: list[str], batch_size: int = 100) -> np.ndarray:
    """Embed texts using OpenAI API."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")

    client = OpenAI(api_key=api_key)
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        print(f"  Embedding batch {i // batch_size + 1} ({len(batch)} texts)...")
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings)


def save_embeddings(scholar_ids: list[str], embeddings: np.ndarray):
    """Save embeddings to NetCDF format using xarray."""
    import xarray as xr

    ds = xr.Dataset(
        {
            "embedding": (["scholar_id", "dim"], embeddings),
        },
        coords={
            "scholar_id": scholar_ids,
            "dim": list(range(embeddings.shape[1])),
        },
    )
    ds.to_netcdf(OUTPUT_PATH)
    print(f"Saved embeddings to {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="Create paper-based embeddings for scholars"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without making API calls"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max scholars to process"
    )
    args = parser.parse_args()

    print("Loading scholar data...")
    scholars, abstracts_by_id = load_scholars_csv()
    print(f"  Found {len(scholars)} unique scholars\n")

    print("Building embedding texts...")
    pairs = build_embedding_texts(scholars, abstracts_by_id)
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
    embeddings = embed_texts(texts)

    print(f"\nEmbedding shape: {embeddings.shape}")
    save_embeddings(scholar_ids, embeddings)


if __name__ == "__main__":
    main()
