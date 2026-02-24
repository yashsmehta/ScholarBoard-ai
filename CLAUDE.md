# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScholarBoard.ai creates interactive 2D dashboards of researchers arranged by research similarity. It uses Perplexity for researcher info/paper extraction, Gemini for parsing into structured JSON, OpenAI for embeddings, and UMAP/DBSCAN for dimensionality reduction + clustering. The current dataset is ~730 vision neuroscience researchers (VSS).

## Commands

```bash
# Install dependencies (uses uv package manager)
uv pip install -e .

# Activate virtual environment
source .venv/bin/activate

# Show pipeline status
python3 scripts/run_pipeline.py

# Build consolidated scholars.json from all data sources
python3 scripts/build_scholars_json.py

# Copy data to website
python3 scripts/run_pipeline.py --step website

# Serve the website locally (http://localhost:8000)
cd website && python3 -m http.server 8000

# Dry-run examples (no API calls)
python3 scripts/scholar_scraper/fetch_papers_perplexity.py --dry-run --limit 5
python3 scripts/parse_raw_to_json.py --dry-run --limit 5
python3 scripts/create_paper_embeddings.py --dry-run
```

## Architecture

### Prompt System (`prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`prompts/fetch_papers.md`** — Perplexity: fetch top papers (`{scholar_name}`, `{institution}`, `{num_papers}`)
- **`prompts/fetch_researcher_info.md`** — Perplexity: full researcher profile (`{scholar_name}`, `{institution}`)
- **`prompts/parse_to_json.md`** — Gemini: parse raw data → structured JSON (`{raw_profile}`, `{raw_papers}`, `{json_schema}`)
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`

### Data Schema (`scholar_board/schemas.py`)

Pydantic models defining the canonical data structure:

- **`Scholar`** — id, name, institution, department, lab_name, research_areas[], bio, education[], papers[], profile_pic, umap_projection{x,y}, cluster
- **`Paper`** — title, abstract, year, venue, citations, authors, last_author, url
- **`Education`** — degree, institution, year, field, advisor

### Data Pipeline (7 steps)

```
Papers Fetch → Profile Fetch → Parse to JSON → Embed → UMAP+DBSCAN → Build JSON → Website Copy
```

1. **`scripts/scholar_scraper/fetch_papers_perplexity.py`** — Perplexity `sonar-pro` fetches recent papers per scholar → `data/scholar_papers/*.json`
2. **`scholar_board/plex_info_extractor.py`** — Perplexity fetches researcher profiles → `data/perplexity_info/*_raw.txt`
3. **`scripts/parse_raw_to_json.py`** — Gemini Flash parses raw data into structured Scholar JSON → `data/scholars/*.json`
4. **`scripts/create_paper_embeddings.py`** — OpenAI `text-embedding-3-small` embeds paper text (fallback: VSS abstracts) → `data/scholar_embeddings.nc`
5. **`scripts/run_umap_dbscan.py`** — StandardScaler → UMAP(cosine) → DBSCAN → `data/models/*.joblib`
6. **`scripts/build_scholars_json.py`** — Merges all sources (CSV + UMAP + papers + bios + pics) → `data/scholars.json`
7. **`scripts/run_pipeline.py`** — Orchestrator: `--step <name>`, `--execute`, or status display

All pipeline scripts support `--dry-run` for safe previewing.

### Legacy Pipeline (still present)

- **`scholar_board/scholar_info_formatter.py`** — Gemini structures raw text → markdown in `data/scholar_markdown/`
- **`scholar_board/scholar_info_summerizer.py`** — Gemini generates summaries in `data/scholar_summaries/`
- **`scholar_board/create_embeddings.py`** — Original embedding script (OpenAI/Gemini/HuggingFace)
- **`scholar_board/low_dim_projection.py`** — Original UMAP/t-SNE/PCA projection

### Website (`website/`)

Static site served with `python3 -m http.server 8000` (no custom server needed).

- **`index.html`** — Header, search input, map container, sidebar
- **`js/script.js`** — D3.js v7 scatter plot (~400 lines):
  - `d3.zoom()` scroll-wheel zoom + drag pan
  - Scholar dots colored by cluster (Spectral colormap)
  - `showScholarDetails()` — sidebar with name, institution, bio, papers, education, nearby scholars
  - Instant name search (2+ chars)
  - Hover tooltips (name + institution)
  - Institution filter with counts
- **`css/styles.css`** — Responsive layout, scholar profile card, paper list, education styles

### Key Data Files

- **`data/scholars.json`** — Master dataset: keyed by scholar ID, includes id, name, institution, department, bio, papers[], profile_pic, umap_projection{x,y}, cluster
- **`data/vss_data.csv`** — Source CSV: 730 unique scholars with abstracts
- **`data/scholar_papers/*.json`** — Per-scholar paper data from Perplexity
- **`data/scholar_summaries/*_summary.txt`** — 2-3 sentence bios
- **`data/profile_pics/*.jpg`** — Profile pictures (naming: `name_XXXX.jpg`)
- **`data/scholar_embeddings.nc`** — High-dimensional embeddings (NetCDF/xarray)
- **`data/models/*.joblib`** — Trained UMAP, DBSCAN, and scaler models

## Environment

Requires a `.env` file with API keys: `PERPLEXITY_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` (or `GEMINI_API_KEY`). Python 3.10+, managed with `uv`.

## Code Conventions

- Library code in `scholar_board/` (importable module); standalone scripts in `scripts/`
- All API prompts externalized in `prompts/*.md`, loaded via `scholar_board/prompt_loader.py`
- Data schema defined with Pydantic in `scholar_board/schemas.py`
- Data artifacts in `data/` (git-ignored); website copies in `website/data/`
- Embedding data uses xarray/NetCDF; trained models use joblib
- Profile pic naming: `scholar_name_XXXX.jpg` (lowercase, underscores)
- All pipeline scripts support `--dry-run` flag
