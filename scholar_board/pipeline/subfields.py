"""
Assign vision science subfield labels to scholars using embedding similarity.

Embeds subfield descriptions and scholar paper texts with
Gemini gemini-embedding-001 (task_type=SEMANTIC_SIMILARITY, 3072 dims),
then assigns each scholar their top matching subfields via cosine similarity.

Usage:
    uv run -m scholar_board.pipeline.subfields --dry-run          # Preview
    uv run -m scholar_board.pipeline.subfields                    # Run
    uv run -m scholar_board.pipeline.subfields --top 3            # Assign top 3 (default: 4)
"""

import json
import argparse
import sys

import numpy as np

from scholar_board.config import (
    CSV_PATH,
    PAPERS_DIR,
    SUBFIELDS_DEF_PATH,
    SUBFIELDS_PATH,
    load_paper_texts,
    load_scholars_csv,
)
from scholar_board.gemini import embed_texts
from scholar_board.db import get_connection, init_db, ensure_scholar, upsert_subfields


def load_subfields():
    """Load subfield definitions from data/source/subfields.json."""
    with open(SUBFIELDS_DEF_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_paper_texts():
    """Load paper texts for all scholars that have them."""
    scholars = load_scholars_csv()
    pairs = []
    for s in sorted(scholars, key=lambda x: x["scholar_id"]):
        sid = s["scholar_id"]
        text = load_paper_texts(sid)
        if text:
            pairs.append((sid, text))
    return pairs


def cosine_similarity(a, b):
    """Cosine similarity: (N, D) x (M, D) -> (N, M)."""
    a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a_norm @ b_norm.T


def assign_subfields(scholar_ids, scholar_embeddings, subfield_embeddings, subfields,
                     top_k=4, margin=0.01):
    """Assign subfield labels to each scholar based on cosine similarity.

    Uses a relative threshold: always keeps the primary subfield plus any
    additional subfields whose score is within `margin` of the top score,
    up to `top_k` total.
    """
    sim_matrix = cosine_similarity(scholar_embeddings, subfield_embeddings)
    subfield_names = [sf["name"] for sf in subfields]
    assignments = {}
    tag_counts = []

    for i, sid in enumerate(scholar_ids):
        sid_padded = str(sid).zfill(4) if str(sid).isdigit() else str(sid)
        scores = sim_matrix[i]
        top_indices = np.argsort(scores)[::-1]
        top_score = float(scores[top_indices[0]])

        tags = []
        for idx in top_indices:
            score = float(scores[idx])
            if len(tags) == 0 or (score >= top_score - margin and len(tags) < top_k):
                tags.append({"subfield": subfield_names[idx], "score": round(score, 4)})
            else:
                break

        tag_counts.append(len(tags))
        assignments[sid_padded] = {
            "primary_subfield": tags[0]["subfield"],
            "subfields": tags,
        }

    counts = np.array(tag_counts)
    print(f"  Tags per scholar: min={counts.min()}, max={counts.max()}, "
          f"mean={counts.mean():.1f}, median={np.median(counts):.0f}")

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
    parser.add_argument("--top", type=int, default=4,
                        help="Max subfield tags per scholar (default: 4)")
    parser.add_argument("--margin", type=float, default=0.01,
                        help="Max score drop from top subfield to keep a subtopic (default: 0.01)")
    args = parser.parse_args()

    if not SUBFIELDS_DEF_PATH.exists():
        print(f"Error: Subfield definitions not found at {SUBFIELDS_DEF_PATH}")
        sys.exit(1)

    print("Loading subfield definitions...")
    subfields = load_subfields()
    print(f"  {len(subfields)} subfields defined")

    print("\nLoading scholar paper texts...")
    pairs = load_all_paper_texts()
    print(f"  {len(pairs)} scholars with paper text")

    if not pairs:
        print("Error: No scholars have paper data. Run fetch_papers step first.")
        sys.exit(1)

    scholar_ids = [sid for sid, _ in pairs]
    scholar_texts = [text for _, text in pairs]
    subfield_texts = [f"{sf['name']}: {sf['description']}" for sf in subfields]

    if args.dry_run:
        print(f"\n[DRY RUN] Would embed with Gemini (SEMANTIC_SIMILARITY):")
        print(f"  - {len(subfield_texts)} subfield descriptions")
        print(f"  - {len(scholar_texts)} scholar paper texts")
        print(f"  Then assign up to {args.top} subfields per scholar (margin={args.margin})")
        return

    print(f"\nEmbedding {len(subfield_texts)} subfield descriptions...")
    subfield_embeddings = embed_texts(subfield_texts, task_type="SEMANTIC_SIMILARITY")
    print(f"  Shape: {subfield_embeddings.shape}")

    print(f"\nEmbedding {len(scholar_texts)} scholar paper texts...")
    scholar_embeddings = embed_texts(scholar_texts, task_type="SEMANTIC_SIMILARITY")
    print(f"  Shape: {scholar_embeddings.shape}")

    print(f"\nAssigning subfield labels (top {args.top}, margin={args.margin})...")
    assignments = assign_subfields(
        scholar_ids, scholar_embeddings, subfield_embeddings,
        subfields, top_k=args.top, margin=args.margin,
    )

    SUBFIELDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBFIELDS_PATH, "w", encoding="utf-8") as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved subfield assignments to {SUBFIELDS_PATH}")

    print("Writing subfield assignments to database...")
    csv_lookup = {s["scholar_id"]: s for s in load_scholars_csv()}
    conn = get_connection()
    init_db(conn)
    for sid, assignment in assignments.items():
        if sid in csv_lookup:
            s = csv_lookup[sid]
            ensure_scholar(conn, sid, s["scholar_name"], s.get("scholar_institution"))
        upsert_subfields(conn, sid, assignment["primary_subfield"], assignment.get("subfields", []))
    conn.close()
    print(f"  Wrote {len(assignments)} scholars to DB")

    print_summary(assignments, subfields)

    print(f"\nExample assignments:")
    for sid, a in list(assignments.items())[:5]:
        tags = ", ".join(f"{t['subfield']} ({t['score']:.3f})" for t in a["subfields"])
        print(f"  {sid}: {tags}")


if __name__ == "__main__":
    main()
