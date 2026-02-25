# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScholarBoard.ai creates interactive 2D dashboards of researchers arranged by research similarity. It uses Gemini 3 Flash Preview with Google Search grounding for researcher info/paper extraction (structured JSON), OpenAI for embeddings, and UMAP/DBSCAN for dimensionality reduction + clustering. The current dataset is ~730 vision neuroscience researchers (VSS).

## Working Style
- When asked to implement something, proceed decisively. Do NOT ask multiple clarifying questions in sequence — make reasonable assumptions and act, then adjust if corrected.
- When verifying API keys or connections, always perform an actual live test call. Never claim something is working based only on config inspection.

## Running Code

**IMPORTANT:** Always use the venv Python directly via `.venv/bin/python3` (NOT `source .venv/bin/activate && python3`, which may resolve to the system Python on this machine). Install packages with `uv pip install`.

```bash
# Install dependencies (uses uv package manager)
uv pip install -e .

# Run any script — always use .venv/bin/python3
.venv/bin/python3 scripts/run_pipeline.py

# Build consolidated scholars.json from all data sources
.venv/bin/python3 scripts/build_scholars_json.py

# Copy data to website
.venv/bin/python3 scripts/run_pipeline.py --step website

# Serve the website locally (http://localhost:8000)
cd website && .venv/bin/python3 -m http.server 8000

# Dry-run examples (no API calls)
.venv/bin/python3 scripts/scholar_scraper/fetch_papers_gemini.py --dry-run --limit 5
.venv/bin/python3 scholar_board/profile_extractor.py --dry-run --limit 5
.venv/bin/python3 scripts/create_paper_embeddings.py --dry-run
.venv/bin/python3 scripts/download_profile_pics.py --dry-run --limit 5

# Download profile pictures (Serper.dev image search)
.venv/bin/python3 scripts/download_profile_pics.py --test                # Test with known scholar
.venv/bin/python3 scripts/download_profile_pics.py --skip-existing       # Only scholars with default avatar

# Install a new package
uv pip install <package-name>
```

## Architecture

### Prompt System (`prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`prompts/fetch_papers.md`** — Gemini grounded search: fetch top papers (`{scholar_name}`, `{institution}`, `{num_papers}`)
- **`prompts/fetch_researcher_info.md`** — Gemini grounded search: structured researcher profile (`{scholar_name}`, `{institution}`)
- **`prompts/normalize_bio.md`** — Gemini: normalize bio tone and pronouns (`{scholar_name}`, `{bio}`)
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`

### Data Schema (`scholar_board/schemas.py`)

Pydantic models defining the canonical data structure:

- **`Scholar`** — id, name, institution, department, lab_url, main_research_area, bio, papers[], profile_pic, umap_projection{x,y}, cluster
- **`Paper`** — title, abstract, year, venue, citations, authors, url

### Data Pipeline (7 steps)

```
Papers Fetch → Profile Fetch → Embed → UMAP+DBSCAN → Build JSON → Profile Pics → Website Copy
```

1. **`scripts/scholar_scraper/fetch_papers_gemini.py`** — Gemini 3 Flash Preview with Google Search grounding fetches recent papers per scholar → `data/scholar_papers/*.json`
2. **`scholar_board/profile_extractor.py`** — Gemini grounded search fetches structured researcher profiles, then normalizes bios (neutral tone, gender-neutral language) → `data/scholar_profiles/{id}_{name}.json`. Use `--skip-normalize` to bypass bio normalization step.
3. **`scripts/create_paper_embeddings.py`** — OpenAI `text-embedding-3-large` embeds paper text (fallback: VSS abstracts) → `data/scholar_embeddings.nc`
4. **`scripts/run_umap_dbscan.py`** — UMAP(cosine) → DBSCAN → `data/models/*.joblib`
5. **`scripts/build_scholars_json.py`** — Merges all sources (CSV + UMAP + papers + profiles + pics) → `data/scholars.json`
6. **`scripts/download_profile_pics.py`** — Serper.dev Google Image Search with face/headshot queries → `data/profile_pics/*.jpg`. Supports `--skip-existing`, `--limit`, `--test`.
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
  - `showScholarDetails()` — sidebar with name, institution, lab link, bio, research area, papers, nearby scholars
  - Instant name search (2+ chars)
  - Hover tooltips (name + institution)
  - Institution filter with counts
- **`css/styles.css`** — Responsive layout, scholar profile card, paper list

### Key Data Files

- **`data/scholars.json`** — Master dataset: keyed by scholar ID, includes id, name, institution, department, lab_url, main_research_area, bio, papers[], profile_pic, umap_projection{x,y}, cluster
- **`data/vss_data.csv`** — Source CSV: 730 unique scholars with abstracts
- **`data/scholar_papers/*.json`** — Per-scholar paper data from Gemini grounded search
- **`data/scholar_profiles/*.json`** — Structured researcher profiles from Gemini grounded search (bio, main_research_area, lab_url, department)
- **`data/profile_pics/*.jpg`** — Profile pictures (naming: `name_XXXX.jpg`)
- **`data/scholar_embeddings.nc`** — High-dimensional embeddings (NetCDF/xarray)
- **`data/models/*.joblib`** — Trained UMAP, DBSCAN, and scaler models

## Environment

Requires a `.env` file with API keys: `OPENAI_API_KEY`, `GOOGLE_API_KEY` (or `GEMINI_API_KEY`), `SERPER_API_KEY` (for profile pic downloads). Python 3.10+, managed with `uv`. Virtual environment at `.venv/` — always invoke Python as `.venv/bin/python3` and install packages with `uv pip install`.

## Code Conventions

- Use direct official SDKs (e.g., `google-genai`) instead of LangChain wrappers (e.g., `langchain-google-genai`) unless explicitly asked otherwise
- Library code in `scholar_board/` (importable module); standalone scripts in `scripts/`
- All API prompts externalized in `prompts/*.md`, loaded via `scholar_board/prompt_loader.py`
- Data schema defined with Pydantic in `scholar_board/schemas.py`
- Data artifacts in `data/` (git-ignored); website copies in `website/data/`
- Embedding data uses xarray/NetCDF; trained models use joblib
- Profile pic naming: `scholar_name_XXXX.jpg` (lowercase, underscores)
- All pipeline scripts support `--dry-run` flag

## Skills & MCP
- When asked to create a Claude Code 'skill', create a SKILL.md reference documentation file under `.claude/skills/<name>/SKILL.md` — NOT an executable tool or script
- MCP config goes in `.mcp.json` at project root, NOT in `.claude/settings.json`
