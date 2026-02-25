# ScholarBoard.ai

Interactive 2D dashboards of researchers arranged by research similarity. Explore ~730 vision neuroscience researchers from VSS, clustered by the topics they study.

- Explore researchers and their work at a glance
- See related researchers nearby on the map
- Search for specific researchers
- View profiles with bios, papers, lab links, and AI-generated research ideas

## Pipeline

1. **Paper & Profile Extraction** — Gemini 3 Flash Preview with Google Search grounding fetches papers and structured researcher profiles
2. **Bio Normalization** — Gemini normalizes bios to neutral tone and consistent formatting
3. **Embeddings** — Gemini `gemini-embedding-001` embeds paper text (3072 dims, task-specific)
4. **Dimensionality Reduction** — UMAP (cosine metric) projects embeddings to 2D
5. **Clustering** — HDBSCAN assigns researchers to clusters, color-coded on the map
6. **Subfield Assignment** — Gemini embeddings + cosine similarity assign top subfield tags
7. **Research Ideas** — Gemini 3.1 Pro Preview generates AI-suggested research directions
8. **Profile Pictures** — Serper.dev Google Image Search downloads researcher headshots

## Setup

```bash
# Install uv if you don't have it
curl -sSf https://astral.sh/uv/install.sh | bash

# Install the package
uv pip install -e .
```

Create a `.env` file:
```
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key
```

## Usage

```bash
# Show pipeline status
.venv/bin/python3 scripts/run_pipeline.py

# Run the complete pipeline
.venv/bin/python3 scripts/run_pipeline.py --execute

# Start the data server
.venv/bin/python3 serve.py

# Start the frontend dev server (in another terminal)
cd frontend && npm run dev
```

The dashboard will be at http://localhost:5173 (Vite proxies data requests to serve.py on :8000).
