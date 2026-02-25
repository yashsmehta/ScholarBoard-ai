"""
Validate UMAP clustering quality by checking if spatially close scholars
study similar topics.

Tests:
1. Keyword spatial coherence — scholars mentioning the same research keywords
   should be closer together on the UMAP map than random scholars.
2. Cluster thematic coherence — each HDBSCAN cluster should be dominated by
   a few research themes, not a random mix.
3. Nearest-neighbor topic overlap — a scholar's UMAP neighbors should have
   similar abstracts (measured by TF-IDF cosine similarity).
4. Known-pair spot checks — manually selected researchers from the same/different
   subfields should be near/far on the map.

Usage:
    .venv/bin/python3 scripts/validate_clustering.py
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist, pdist

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ─────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────

def load_data():
    """Load scholars.json + vss_data.csv and merge abstracts."""
    with open(DATA_DIR / "scholars.json") as f:
        scholars = json.load(f)

    df = pd.read_csv(DATA_DIR / "vss_data.csv")

    # Build id → list of abstracts mapping
    id_to_abstracts = defaultdict(list)
    id_to_name = {}
    for _, row in df.iterrows():
        sid = str(row["scholar_id"]).zfill(4)
        abstract = str(row.get("abstract", ""))
        if abstract and abstract != "nan":
            id_to_abstracts[sid].append(abstract)
        id_to_name[sid] = row["scholar_name"]

    # Build parallel arrays
    ids, names, coords, clusters, abstracts_list = [], [], [], [], []
    for sid, s in scholars.items():
        umap = s.get("umap_projection", {})
        x, y = umap.get("x"), umap.get("y")
        if x is None or y is None:
            continue
        abs_texts = id_to_abstracts.get(sid, [])
        combined = " ".join(abs_texts)
        if not combined.strip():
            continue

        ids.append(sid)
        names.append(s["name"])
        coords.append([x, y])
        clusters.append(s.get("cluster", -1))
        abstracts_list.append(combined)

    coords = np.array(coords)
    clusters = np.array(clusters)
    print(f"Loaded {len(ids)} scholars with UMAP coords + abstracts\n")
    return ids, names, coords, clusters, abstracts_list


# ─────────────────────────────────────────────
# Test 1: Keyword spatial coherence
# ─────────────────────────────────────────────

def test_keyword_coherence(names, coords, abstracts):
    """Scholars mentioning the same keyword should be closer together."""
    print("=" * 60)
    print("TEST 1: Keyword Spatial Coherence")
    print("=" * 60)
    print("Do scholars studying similar topics cluster spatially?\n")

    # Vision science keywords — spanning different subfields
    keywords = {
        "face perception":    ["face recognition", "face perception", "face processing", "facial"],
        "attention":          ["attentional", "visual attention", "selective attention", "attentional capture"],
        "motion perception":  ["motion perception", "motion direction", "optic flow", "biological motion"],
        "scene perception":   ["scene perception", "scene recognition", "scene layout", "scene context", "spatial layout"],
        "color vision":       ["color perception", "color vision", "chromatic", "color appearance"],
        "object recognition": ["object recognition", "object perception", "object category", "object representation"],
        "eye movements":      ["saccade", "saccadic", "eye movement", "fixation", "oculomotor"],
        "working memory":     ["working memory", "visual working memory", "short-term memory", "memory capacity"],
        "crowding":           ["crowding", "peripheral vision", "visual crowding"],
        "depth perception":   ["depth perception", "binocular", "stereopsis", "3d perception", "disparity"],
        "reading":            ["reading", "word recognition", "lexical", "text processing"],
        "neural coding":      ["neural coding", "neural response", "v1", "primary visual cortex", "receptive field"],
        "perceptual learning":["perceptual learning", "visual learning", "training effect"],
        "multisensory":       ["multisensory", "cross-modal", "audiovisual", "haptic"],
    }

    global_mean_dist = np.mean(pdist(coords))
    print(f"Global mean pairwise distance: {global_mean_dist:.2f}\n")

    results = []
    for topic, terms in keywords.items():
        # Find scholars whose abstracts mention any of these terms
        members = []
        for i, abstract in enumerate(abstracts):
            lower = abstract.lower()
            if any(t in lower for t in terms):
                members.append(i)

        if len(members) < 3:
            continue

        member_coords = coords[members]
        within_dist = np.mean(pdist(member_coords))
        ratio = within_dist / global_mean_dist
        results.append((topic, len(members), within_dist, ratio))

    results.sort(key=lambda x: x[3])

    print(f"{'Topic':<25s} {'N':>4s} {'Within-Dist':>12s} {'Ratio':>7s}  Interpretation")
    print("-" * 75)
    for topic, n, within, ratio in results:
        if ratio < 0.5:
            interp = "STRONG clustering"
        elif ratio < 0.7:
            interp = "Good clustering"
        elif ratio < 0.85:
            interp = "Mild clustering"
        elif ratio < 1.0:
            interp = "Weak clustering"
        else:
            interp = "No clustering"
        print(f"{topic:<25s} {n:4d} {within:12.2f} {ratio:7.2f}  {interp}")

    avg_ratio = np.mean([r[3] for r in results])
    print(f"\nAverage ratio: {avg_ratio:.2f}")
    if avg_ratio < 0.7:
        print("PASS — Topics are well-clustered spatially")
    elif avg_ratio < 0.85:
        print("OK — Some topical clustering, but not very tight")
    else:
        print("FAIL — Keyword groups are not spatially coherent")
    print()


# ─────────────────────────────────────────────
# Test 2: Cluster thematic coherence
# ─────────────────────────────────────────────

def test_cluster_themes(ids, names, coords, clusters, abstracts):
    """Each cluster should have a coherent research theme."""
    print("=" * 60)
    print("TEST 2: Cluster Thematic Coherence")
    print("=" * 60)
    print("What are the top keywords for each cluster?\n")

    from sklearn.feature_extraction.text import TfidfVectorizer

    # Fit TF-IDF on all abstracts
    vectorizer = TfidfVectorizer(
        max_features=2000,
        stop_words="english",
        min_df=3,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(abstracts)
    feature_names = vectorizer.get_feature_names_out()

    unique_clusters = sorted(set(clusters))
    for c in unique_clusters:
        if c == -1:
            continue  # Skip noise
        mask = clusters == c
        n_members = mask.sum()
        if n_members < 3:
            continue

        # Average TF-IDF scores within cluster
        cluster_tfidf = tfidf_matrix[mask].mean(axis=0)
        cluster_tfidf = np.asarray(cluster_tfidf).flatten()
        top_indices = cluster_tfidf.argsort()[-8:][::-1]
        top_keywords = [feature_names[i] for i in top_indices]

        # Show a few member names
        member_names = [names[i] for i in np.where(mask)[0][:4]]
        members_str = ", ".join(member_names)
        if n_members > 4:
            members_str += f", ... (+{n_members - 4} more)"

        print(f"Cluster {c:2d} ({n_members:3d} scholars): {', '.join(top_keywords)}")
        print(f"           Members: {members_str}")
        print()


# ─────────────────────────────────────────────
# Test 3: Nearest-neighbor abstract similarity
# ─────────────────────────────────────────────

def test_nn_similarity(names, coords, abstracts, k=10):
    """Nearest UMAP neighbors should have similar abstracts."""
    print("=" * 60)
    print("TEST 3: Nearest-Neighbor Abstract Similarity")
    print("=" * 60)
    print(f"Are UMAP k={k} nearest neighbors studying similar topics?\n")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # Compute TF-IDF similarity matrix
    vectorizer = TfidfVectorizer(
        max_features=3000,
        stop_words="english",
        min_df=2,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(abstracts)
    text_sim = cosine_similarity(tfidf_matrix)  # N x N

    # Compute UMAP distance matrix
    umap_dist = cdist(coords, coords)
    n = len(names)

    # For each scholar, get k nearest UMAP neighbors and measure text similarity
    nn_sims = []
    random_sims = []
    rng = np.random.default_rng(42)

    for i in range(n):
        # k nearest neighbors by UMAP distance (excluding self)
        dists = umap_dist[i]
        nn_idx = np.argsort(dists)[1:k+1]
        nn_sim = text_sim[i, nn_idx].mean()
        nn_sims.append(nn_sim)

        # k random neighbors for comparison
        rand_idx = rng.choice([j for j in range(n) if j != i], size=k, replace=False)
        rand_sim = text_sim[i, rand_idx].mean()
        random_sims.append(rand_sim)

    nn_mean = np.mean(nn_sims)
    rand_mean = np.mean(random_sims)
    ratio = nn_mean / rand_mean

    print(f"Mean TF-IDF similarity to {k} nearest UMAP neighbors:  {nn_mean:.4f}")
    print(f"Mean TF-IDF similarity to {k} random scholars:         {rand_mean:.4f}")
    print(f"Ratio (neighbors / random):                            {ratio:.2f}x")
    print()

    if ratio > 2.0:
        print("PASS — Neighbors are significantly more similar than random")
    elif ratio > 1.5:
        print("OK — Moderate neighbor similarity")
    else:
        print("WEAK — Neighbors are only slightly more similar than random")

    # Show a few examples: scholars whose neighbors are most/least similar
    nn_sims = np.array(nn_sims)
    print("\nBest cases (highest neighbor similarity):")
    for idx in nn_sims.argsort()[-5:][::-1]:
        nn_idx = np.argsort(umap_dist[idx])[1:4]
        neighbor_names = [names[j] for j in nn_idx]
        print(f"  {names[idx]:<30s} sim={nn_sims[idx]:.3f}  neighbors: {', '.join(neighbor_names)}")

    print("\nWorst cases (lowest neighbor similarity):")
    for idx in nn_sims.argsort()[:5]:
        nn_idx = np.argsort(umap_dist[idx])[1:4]
        neighbor_names = [names[j] for j in nn_idx]
        print(f"  {names[idx]:<30s} sim={nn_sims[idx]:.3f}  neighbors: {', '.join(neighbor_names)}")
    print()


# ─────────────────────────────────────────────
# Test 4: Known-pair spot checks
# ─────────────────────────────────────────────

def test_known_pairs(ids, names, coords, clusters, abstracts):
    """Check specific researchers we know should be near/far from each other."""
    print("=" * 60)
    print("TEST 4: Known-Pair Spot Checks")
    print("=" * 60)
    print("Checking specific researchers we expect to be near/far.\n")

    name_to_idx = {n.lower(): i for i, n in enumerate(names)}

    def find(name_fragment):
        """Find a scholar by partial name match."""
        fragment = name_fragment.lower()
        matches = [(n, i) for n, i in name_to_idx.items() if fragment in n]
        if not matches:
            return None, None
        # Prefer exact match, then shortest name
        matches.sort(key=lambda x: len(x[0]))
        return matches[0]

    def dist(idx1, idx2):
        """Euclidean distance in UMAP space."""
        return np.sqrt(np.sum((coords[idx1] - coords[idx2])**2))

    # Define test pairs: (scholar_a, scholar_b, expected_relation)
    # We need to find scholars we know are in similar/different fields
    # Let's first list all scholars and find good test cases by abstract content

    # Group scholars by research topic keywords in their abstracts
    topic_groups = {
        "face": [],
        "attention": [],
        "motion": [],
        "scene": [],
        "eye movement": [],
        "color": [],
        "working memory": [],
        "object recognition": [],
        "neural coding": [],
    }

    for i, abstract in enumerate(abstracts):
        lower = abstract.lower()
        if any(t in lower for t in ["face recognition", "face perception", "face processing"]):
            topic_groups["face"].append(i)
        if any(t in lower for t in ["visual attention", "attentional", "selective attention"]):
            topic_groups["attention"].append(i)
        if any(t in lower for t in ["motion perception", "motion direction", "optic flow"]):
            topic_groups["motion"].append(i)
        if any(t in lower for t in ["scene perception", "scene recognition", "scene layout"]):
            topic_groups["scene"].append(i)
        if any(t in lower for t in ["saccade", "saccadic", "eye movement"]):
            topic_groups["eye movement"].append(i)
        if any(t in lower for t in ["color vision", "chromatic", "color perception"]):
            topic_groups["color"].append(i)
        if any(t in lower for t in ["working memory", "visual working memory"]):
            topic_groups["working memory"].append(i)

    global_mean = np.mean(pdist(coords))

    print(f"Global mean pairwise UMAP distance: {global_mean:.2f}\n")

    # For each topic, pick the 2 closest scholars and show them as a "same-field" pair
    # Then compare to a cross-topic pair
    print("── Same-field pairs (should be CLOSE) ──")
    same_field_dists = []
    for topic, members in topic_groups.items():
        if len(members) < 2:
            continue
        # Find closest pair
        member_coords = coords[members]
        pair_dists = cdist(member_coords, member_coords)
        np.fill_diagonal(pair_dists, np.inf)
        min_i, min_j = np.unravel_index(pair_dists.argmin(), pair_dists.shape)
        d = pair_dists[min_i, min_j]
        same_field_dists.append(d)
        a, b = members[min_i], members[min_j]
        print(f"  [{topic}] {names[a]:<28s} ↔ {names[b]:<28s}  dist={d:.2f}  cluster=({clusters[a]},{clusters[b]})")

    print(f"\n── Cross-field pairs (should be FAR) ──")
    cross_dists = []
    topic_list = [k for k, v in topic_groups.items() if len(v) >= 2]
    for i in range(min(len(topic_list), 5)):
        for j in range(i + 1, min(len(topic_list), 5)):
            t1, t2 = topic_list[i], topic_list[j]
            # Pick one scholar from each topic
            a = topic_groups[t1][0]
            b = topic_groups[t2][0]
            d = dist(a, b)
            cross_dists.append(d)
            print(f"  [{t1} vs {t2}] {names[a]:<28s} ↔ {names[b]:<28s}  dist={d:.2f}")

    if same_field_dists and cross_dists:
        mean_same = np.mean(same_field_dists)
        mean_cross = np.mean(cross_dists)
        print(f"\nMean same-field distance:  {mean_same:.2f}")
        print(f"Mean cross-field distance: {mean_cross:.2f}")
        print(f"Separation ratio:          {mean_cross / mean_same:.1f}x")
        if mean_cross / mean_same > 3:
            print("PASS — Same-field pairs are much closer than cross-field pairs")
        elif mean_cross / mean_same > 2:
            print("OK — Reasonable separation between same/cross-field")
        else:
            print("WEAK — Same-field and cross-field distances are too similar")

    # Check Michael Bonner specifically
    bonner_match = find("michael bonner")
    if bonner_match[0]:
        bonner_name, bonner_idx = bonner_match
        print(f"\n── Michael Bonner neighborhood ──")
        print(f"  Position: ({coords[bonner_idx][0]:.2f}, {coords[bonner_idx][1]:.2f}), cluster={clusters[bonner_idx]}")
        dists_to_bonner = np.sqrt(np.sum((coords - coords[bonner_idx])**2, axis=1))
        nearest = np.argsort(dists_to_bonner)[1:8]
        print(f"  Nearest neighbors:")
        for idx in nearest:
            d = dists_to_bonner[idx]
            # Show first 100 chars of abstract
            snippet = abstracts[idx][:120].replace("\n", " ")
            print(f"    {names[idx]:<30s} dist={d:.2f} cl={clusters[idx]:2d}  \"{snippet}...\"")

    print()


# ─────────────────────────────────────────────
# Test 5: Silhouette score (if enough clusters)
# ─────────────────────────────────────────────

def test_silhouette(coords, clusters):
    """Compute silhouette score for the clustering."""
    print("=" * 60)
    print("TEST 5: Silhouette Score")
    print("=" * 60)

    from sklearn.metrics import silhouette_score, silhouette_samples

    # Exclude noise points for silhouette
    mask = clusters != -1
    if mask.sum() < 10:
        print("Not enough clustered points for silhouette score.\n")
        return

    score = silhouette_score(coords[mask], clusters[mask])
    print(f"Silhouette score (excluding noise): {score:.3f}")
    print(f"  Range: [-1, 1], higher = better cluster separation")

    if score > 0.5:
        print("  STRONG — Well-separated clusters")
    elif score > 0.3:
        print("  GOOD — Reasonable cluster structure")
    elif score > 0.1:
        print("  WEAK — Overlapping clusters")
    else:
        print("  POOR — No meaningful cluster structure")

    # Per-cluster silhouette
    samples = silhouette_samples(coords[mask], clusters[mask])
    clustered_labels = clusters[mask]
    print(f"\n  Per-cluster silhouette:")
    for c in sorted(set(clustered_labels)):
        c_mask = clustered_labels == c
        c_score = samples[c_mask].mean()
        print(f"    Cluster {c:2d} ({c_mask.sum():3d} members): {c_score:.3f}")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    ids, names, coords, clusters, abstracts = load_data()

    test_keyword_coherence(names, coords, abstracts)
    test_cluster_themes(ids, names, coords, clusters, abstracts)
    test_nn_similarity(names, coords, abstracts)
    test_known_pairs(ids, names, coords, clusters, abstracts)
    test_silhouette(coords, clusters)

    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
