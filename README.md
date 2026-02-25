# ScholarBoard.ai

> Interactive 2D map of researchers arranged by research similarity — explore who studies what, and who's nearby.

**730 vision neuroscience researchers** from VSS, embedded by their publications, clustered by topic, and visualized on an interactive scatter plot. Click any dot to see a researcher's profile, papers, subfield tags, and an AI-generated research idea.

---

## Quickstart

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) 18+ (for the frontend)
- API keys: `GOOGLE_API_KEY`, `SERPER_API_KEY`

### Install

```bash
# Clone and enter the project
git clone https://github.com/scienta-ai/ScholarBoard-ai.git
cd ScholarBoard-ai

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Configure

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key
```

### Run

```bash
# Run the data pipeline (fetches papers, builds embeddings, clusters, etc.)
uv run scripts/run_pipeline.py --execute

# Start the data server (port 8000)
uv run serve.py

# Start the frontend dev server (port 5173, proxies to data server)
cd frontend && npm run dev
```

Open **http://localhost:5173** to explore the map.

---

## Pipeline

The entire pipeline runs on **Google Gemini** models. Run `uv run scripts/run_pipeline.py` to see the status dashboard.

```
 Step   What it does                              Model
 ─────  ────────────────────────────────────────  ──────────────────────────────────
  1     Fetch papers via grounded search           Gemini 3 Flash + Google Search
  2     Fetch researcher profiles + bios           Gemini 3 Flash + Google Search
  3     Embed paper text for clustering            gemini-embedding-001 (CLUSTERING)
  4     UMAP projection + HDBSCAN clustering       local (scikit-learn)
  5     Assign subfield tags                       gemini-embedding-001 (SEMANTIC_SIMILARITY)
  6     Generate AI research directions            Gemini 3.1 Pro (HIGH thinking)
  7     Build consolidated scholars.json           local (merge all sources)
  8     Download profile pictures                  Serper.dev image search
```

```bash
# Show status dashboard
uv run scripts/run_pipeline.py

# Run everything
uv run scripts/run_pipeline.py --execute

# Run a single step
uv run scripts/run_pipeline.py --step papers

# Run from a specific step onward
uv run scripts/run_pipeline.py --from embed
```

Steps 1, 2, and 6 parallelize across researchers with `--workers 25` by default. All steps support `--dry-run`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Paper & profile extraction | Gemini 3 Flash Preview + Google Search grounding |
| Research idea generation | Gemini 3.1 Pro Preview with HIGH thinking |
| Embeddings | Gemini `gemini-embedding-001` (3072 dims, task-specific) |
| Dimensionality reduction | UMAP (cosine metric, n_neighbors=15) |
| Clustering | HDBSCAN (min_cluster_size=10) |
| Subfield matching | Cosine similarity on embedding space |
| Frontend | React + TypeScript + Vite + D3.js |
| Data server | Python HTTP server (`serve.py`) |
| Package management | uv (Python), npm (frontend) |

---

## Vision Science Subfields

Each researcher is tagged with up to 5 subfields based on semantic similarity between their papers and these definitions:

| | Subfield | | Subfield |
|---|---|---|---|
| 1 | Neural Coding & Transduction | 13 | Ensemble & Summary Statistics |
| 2 | Representational Geometry | 14 | Perceptual Learning & Plasticity |
| 3 | Brain-AI Alignment | 15 | Multisensory Integration |
| 4 | Predictive & Feedback Dynamics | 16 | Perceptual Decision-Making |
| 5 | Mid-Level Feature Synthesis | 17 | Visual Development |
| 6 | Object Recognition | 18 | Neural Decoding & Neuroimaging Methods |
| 7 | Face Perception & Social Vision | 19 | Comparative & Animal Vision |
| 8 | Scene Perception & Navigation | 20 | Motion Perception |
| 9 | Active Vision & Eye Movements | 21 | Color Vision & Appearance |
| 10 | Visuomotor Action & Grasping | 22 | Visual Search & Foraging |
| 11 | Attention & Selection | 23 | Reading & Word Recognition |
| 12 | Visual Working Memory | | |

---

## Project Structure

```
ScholarBoard-ai/
├── scholar_board/           # Python library (schemas, prompt loader, profile extractor)
├── scripts/
│   ├── run_pipeline.py      # Pipeline orchestrator with status dashboard
│   ├── scholar_scraper/     # Paper fetching (Gemini grounded search)
│   ├── create_paper_embeddings.py
│   ├── run_umap_dbscan.py
│   ├── assign_subfields.py
│   ├── generate_ideas.py
│   ├── build_scholars_json.py
│   └── download_profile_pics.py
├── prompts/                 # Externalized prompt templates (*.md)
├── frontend/                # React + TypeScript + Vite + D3.js
├── data/                    # Pipeline artifacts (git-ignored)
│   ├── source/              # Inputs: vss_data.csv, subfields.json
│   ├── pipeline/            # Intermediates: papers, profiles, embeddings, models, ideas
│   ├── build/               # Final outputs: scholars.json, profile_pics/
│   └── archive/             # Legacy data (not used by pipeline)
├── serve.py                 # Data server (localhost:8000)
├── pyproject.toml           # Python project config (uv)
└── .env                     # API keys (not committed)
```

---

## License

MIT
