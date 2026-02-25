# data/ — Directory Structure & Database Schema

All contents of `data/` are git-ignored. This file documents the layout and the SQLite database schema.

## Directory Layout

```
data/
├── source/                    # Static inputs — never overwritten by the pipeline
│   ├── vss_data.csv           # ~730 VSS scholars (scholar_id, scholar_name, scholar_institution, abstract)
│   ├── extra_researchers.csv  # Additional researchers found by the discover step (E-prefixed IDs)
│   └── subfields.json         # 23 vision science subfield definitions used for semantic matching
│
├── pipeline/                  # Pipeline intermediates — safe to delete and regenerate
│   ├── scholar_papers/        # {id}_{name}.json — papers fetched per scholar (step 1)
│   ├── scholar_profiles/      # {id}_{name}.json — structured profiles + bios (step 2)
│   ├── scholar_embeddings.nc  # N×3072 xarray/NetCDF embedding matrix (step 3)
│   ├── models/                # Trained scikit-learn models (step 4):
│   │   ├── umap_model.joblib      — fitted UMAP reducer
│   │   ├── umap_hdbscan.joblib    — fitted HDBSCAN clusterer
│   │   └── scaler.joblib          — StandardScaler for embeddings
│   ├── scholar_subfields.json # {scholar_id: [{subfield, score}, ...]} (step 5)
│   └── scholar_ideas/         # {id}_{name}.json — AI-generated research ideas (step 6)
│
├── build/                     # Final outputs served by serve.py
│   ├── scholars.json          # Master dataset — keyed by scholar_id, loaded by the frontend
│   ├── profile_pics/          # Headshot images: {name}_{id}.jpg (step 8)
│   └── scholars/              # Per-scholar JSON files (mirrors scholars.json entries)
│
└── scholarboard.db            # SQLite database — queryable source of truth (see schema below)
```

## SQLite Database (`scholarboard.db`)

The database at `data/scholarboard.db` is written by `scholar_board/db.py`. Every pipeline step that produces scholar data upserts into this DB alongside writing JSON files. The JSON files are for human inspection and reproducibility; the DB is for fast queries and cross-referencing.

Embeddings are **not** stored here — they live in `scholar_embeddings.nc`.

### Schema

#### `scholars` — one row per researcher

| Column             | Type    | Description |
|--------------------|---------|-------------|
| `id`               | TEXT PK | Zero-padded 4-digit ID (e.g. `"0042"`) for VSS scholars; `"E001"` etc. for extras |
| `name`             | TEXT    | Full name |
| `institution`      | TEXT    | University / research institute |
| `department`       | TEXT    | Department or school |
| `lab_name`         | TEXT    | Lab name (if found) |
| `lab_url`          | TEXT    | Lab or faculty page URL |
| `main_research_area` | TEXT  | Concise 2–5 word research focus |
| `bio`              | TEXT    | 3–5 sentence normalized bio |
| `umap_x`           | REAL    | UMAP x coordinate (set by cluster step) |
| `umap_y`           | REAL    | UMAP y coordinate (set by cluster step) |
| `cluster`          | INTEGER | HDBSCAN cluster label (-1 = noise) |
| `primary_subfield` | TEXT    | Top-ranked subfield tag |
| `profile_pic`      | TEXT    | Filename in `build/profile_pics/` (e.g. `"jane_doe_0042.jpg"`) |

#### `papers` — one row per paper

| Column      | Type         | Description |
|-------------|--------------|-------------|
| `id`        | INTEGER PK   | Auto-increment |
| `scholar_id`| TEXT FK      | → `scholars.id` |
| `title`     | TEXT         | Exact paper title |
| `abstract`  | TEXT         | Abstract (may be null if blocked by recitation filter) |
| `year`      | TEXT         | Publication year |
| `venue`     | TEXT         | Journal or conference name |
| `citations` | TEXT         | Citation count (stored as text) |
| `authors`   | TEXT         | Comma-separated full author list |
| `url`       | TEXT         | DOI or paper URL |

#### `subfields` — one row per (scholar, subfield) assignment

| Column      | Type       | Description |
|-------------|------------|-------------|
| `scholar_id`| TEXT FK    | → `scholars.id` |
| `subfield`  | TEXT       | Subfield name (from `subfields.json`) |
| `score`     | REAL       | Cosine similarity score |
| `is_primary`| INTEGER    | 1 if this is the scholar's top subfield, else 0 |

Composite PK: `(scholar_id, subfield)`

#### `ideas` — one row per scholar's AI-generated research idea

| Column             | Type    | Description |
|--------------------|---------|-------------|
| `scholar_id`       | TEXT PK | → `scholars.id` |
| `research_thread`  | TEXT    | Narrative connecting their past work |
| `open_question`    | TEXT    | The central unanswered question |
| `title`            | TEXT    | Short idea title |
| `hypothesis`       | TEXT    | Specific testable hypothesis |
| `approach`         | TEXT    | Experimental / computational approach |
| `scientific_impact`| TEXT    | Why it matters |
| `why_now`          | TEXT    | Why this is timely |

### Useful Queries

```sql
-- Count scholars per cluster
SELECT cluster, COUNT(*) FROM scholars GROUP BY cluster ORDER BY cluster;

-- Find all papers for a scholar by name
SELECT p.* FROM papers p
JOIN scholars s ON s.id = p.scholar_id
WHERE s.name LIKE '%Bonner%';

-- Top subfields by number of scholars
SELECT subfield, COUNT(*) as n FROM subfields
WHERE is_primary = 1 GROUP BY subfield ORDER BY n DESC;

-- Scholars with no bio yet
SELECT id, name FROM scholars WHERE bio IS NULL;

-- Scholars with umap coordinates but no papers
SELECT s.id, s.name FROM scholars s
WHERE s.umap_x IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM papers p WHERE p.scholar_id = s.id);
```

### `db.py` API

All database writes go through `scholar_board/db.py`:

- `get_connection()` — opens a WAL-mode connection with FK enforcement
- `init_db(conn)` — creates tables if they don't exist (idempotent)
- `ensure_scholar(conn, id, name, institution, department)` — INSERT OR IGNORE base row
- `upsert_profile(conn, scholar_id, **fields)` — update bio, lab_url, etc.
- `upsert_papers(conn, scholar_id, papers)` — replace all papers for a scholar
- `upsert_subfields(conn, scholar_id, primary_subfield, subfields)` — replace subfield assignments
- `upsert_idea(conn, scholar_id, idea)` — insert or replace research idea
- `upsert_cluster(conn, scholar_id, umap_x, umap_y, cluster)` — set UMAP coords + cluster
- `upsert_profile_pic(conn, scholar_id, filename)` — set profile pic filename
