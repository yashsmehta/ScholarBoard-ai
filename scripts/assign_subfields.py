"""
Assign vision science subfield labels to scholars using embedding similarity.

Embeds 20 predefined subfield descriptions and scholar paper texts with
Gemini gemini-embedding-001 (task_type=SEMANTIC_SIMILARITY, 3072 dims),
then assigns each scholar their top matching subfields via cosine similarity.

Usage:
    python3 scripts/assign_subfields.py --dry-run          # Preview
    python3 scripts/assign_subfields.py                    # Run
    python3 scripts/assign_subfields.py --top 3            # Assign top 3 (default)
"""

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
SUBFIELDS_PATH = DATA_DIR / "subfields.json"
OUTPUT_PATH = DATA_DIR / "scholar_subfields.json"

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072


def load_subfields():
    """Load subfield definitions from data/subfields.json."""
    with open(SUBFIELDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_paper_texts_for_scholar(scholar_id: str) -> str | None:
    """Load concatenated paper titles + abstracts for a scholar."""
    for fpath in PAPERS_DIR.glob(f"{scholar_id}_*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            papers = data.get("papers", [])
            if not papers:
                return None
            parts = []
            for p in papers[:5]:
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


def load_all_paper_texts():
    """Load paper texts for all scholars that have them."""
    import csv

    csv_path = DATA_DIR / "vss_data.csv"
    scholar_ids = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        seen = set()
        for row in reader:
            sid = row.get("scholar_id", "").strip().strip("\"'")
            if not sid:
                continue
            if sid.isdigit():
                sid = sid.zfill(4)
            if sid not in seen:
                seen.add(sid)
                scholar_ids.append(sid)

    pairs = []
    for sid in sorted(scholar_ids):
        text = load_paper_texts_for_scholar(sid)
        if text:
            pairs.append((sid, text))

    return pairs


def embed_texts(texts: list[str], task_type: str = "SEMANTIC_SIMILARITY",
                batch_size: int = 100) -> np.ndarray:
    """Embed texts using Gemini API with specified task type."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) not found in environment")

    client = genai.Client(api_key=api_key)
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"    Batch {i // batch_size + 1} ({len(batch)} texts)...")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIM,
            ),
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    return np.array(all_embeddings)


# ── Core logic ─────────────────────────────────────────────────────────────

def cosine_similarity(a, b):
    """Cosine similarity: (N, D) x (M, D) -> (N, M)."""
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a_norm @ b_norm.T


def assign_subfields(scholar_ids, scholar_embeddings, subfield_embeddings, subfields, top_k=3):
    """Assign top-k subfield labels to each scholar based on cosine similarity."""
    sim_matrix = cosine_similarity(scholar_embeddings, subfield_embeddings)
    subfield_names = [sf["name"] for sf in subfields]
    assignments = {}

    for i, sid in enumerate(scholar_ids):
        sid_padded = str(sid).zfill(4) if str(sid).isdigit() else str(sid)

        scores = sim_matrix[i]
        top_indices = np.argsort(scores)[::-1][:top_k]

        tags = []
        for idx in top_indices:
            tags.append({
                "subfield": subfield_names[idx],
                "score": round(float(scores[idx]), 4),
            })

        assignments[sid_padded] = {
            "primary_subfield": tags[0]["subfield"],
            "subfields": tags,
        }

    return assignments


def print_summary(assignments, subfields):
    """Print distribution of primary subfield assignments."""
    from collections import Counter

    primary_counts = Counter(a["primary_subfield"] for a in assignments.values())

    print(f"\nPrimary subfield distribution ({len(assignments)} scholars):")
    for sf in subfields:
        count = primary_counts.get(sf["name"], 0)
        bar = "#" * (count // 2)
        print(f"  {sf['name']:40s} {count:4d}  {bar}")


def main():
    parser = argparse.ArgumentParser(
        description="Assign vision science subfield labels to scholars via embedding similarity"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without making API calls")
    parser.add_argument("--top", type=int, default=3,
                        help="Number of top subfield tags per scholar (default: 3)")
    args = parser.parse_args()

    # Load subfield definitions
    print("Loading subfield definitions...")
    subfields = load_subfields()
    print(f"  {len(subfields)} subfields defined")

    # Load scholar paper texts
    print("\nLoading scholar paper texts...")
    pairs = load_all_paper_texts()
    print(f"  {len(pairs)} scholars with paper text")

    if not pairs:
        print("Error: No scholars have paper data. Run fetch_papers_gemini.py first.")
        sys.exit(1)

    scholar_ids = [sid for sid, _ in pairs]
    scholar_texts = [text for _, text in pairs]
    subfield_texts = [f"{sf['name']}: {sf['description']}" for sf in subfields]

    if args.dry_run:
        print(f"\n[DRY RUN] Would embed with Gemini (SEMANTIC_SIMILARITY):")
        print(f"  - {len(subfield_texts)} subfield descriptions")
        print(f"  - {len(scholar_texts)} scholar paper texts")
        print(f"  Then assign top-{args.top} subfields per scholar")
        return

    print(f"\nEmbedding {len(subfield_texts)} subfield descriptions (SEMANTIC_SIMILARITY)...")
    subfield_embeddings = embed_texts(subfield_texts)
    print(f"  Shape: {subfield_embeddings.shape}")

    print(f"\nEmbedding {len(scholar_texts)} scholar paper texts (SEMANTIC_SIMILARITY)...")
    scholar_embeddings = embed_texts(scholar_texts)
    print(f"  Shape: {scholar_embeddings.shape}")

    # Assign subfields
    print("\nAssigning subfield labels...")
    assignments = assign_subfields(
        scholar_ids, scholar_embeddings, subfield_embeddings,
        subfields, top_k=args.top
    )

    # Save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved subfield assignments to {OUTPUT_PATH}")

    print_summary(assignments, subfields)

    # Examples
    print(f"\nExample assignments:")
    for sid, a in list(assignments.items())[:5]:
        tags = ", ".join(f"{t['subfield']} ({t['score']:.3f})" for t in a["subfields"])
        print(f"  {sid}: {tags}")


if __name__ == "__main__":
    main()
