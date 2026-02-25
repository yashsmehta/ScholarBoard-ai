# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScholarBoard.ai creates interactive 2D dashboards of researchers arranged by research similarity. The entire pipeline runs on Google Gemini models — Gemini 3 Flash Preview (grounded search for papers/profiles), Gemini 3.1 Pro Preview (research idea generation with HIGH thinking), and Gemini gemini-embedding-001 (task-specific embeddings: CLUSTERING for UMAP, SEMANTIC_SIMILARITY for subfield matching). Uses UMAP + HDBSCAN for dimensionality reduction and clustering. The current dataset is ~730 vision neuroscience researchers (VSS).

## Working Style
- When asked to implement something, proceed decisively. Do NOT ask multiple clarifying questions in sequence — make reasonable assumptions and act, then adjust if corrected.
- When verifying API keys or connections, always perform an actual live test call. Never claim something is working based only on config inspection.

## Running Code

**IMPORTANT:** Use `uv run` to execute all Python scripts. This automatically resolves the project's virtual environment. Install packages with `uv add`.

```bash
# Install Python dependencies
uv sync

# Pipeline — show status dashboard
uv run scripts/run_pipeline.py

# Pipeline — run a single step or from a step onward
uv run scripts/run_pipeline.py --step build
uv run scripts/run_pipeline.py --from embed

# Build consolidated scholars.json from all data sources
uv run scripts/build_scholars_json.py

# Frontend development (two terminals)
uv run serve.py                         # Terminal 1: data server → :8000
cd frontend && npm run dev              # Terminal 2: Vite dev server → :5173

# Dry-run examples (no API calls)
uv run scripts/scholar_scraper/fetch_papers_gemini.py --dry-run --limit 5
uv run scholar_board/profile_extractor.py --dry-run --limit 5
uv run scripts/create_paper_embeddings.py --dry-run
uv run scripts/generate_ideas.py --dry-run --limit 5
uv run scripts/download_profile_pics.py --dry-run --limit 5

# Download profile pictures (Serper.dev image search)
uv run scripts/download_profile_pics.py --test                # Test with known scholar
uv run scripts/download_profile_pics.py --skip-existing       # Only missing scholars

# Install a new package
uv add <package-name>
```

## Architecture

### Gemini Models Used

| Task | Model | Details |
|---|---|---|
| Paper fetching | `gemini-3-flash-preview` | Google Search grounding |
| Profile extraction | `gemini-3-flash-preview` | Google Search grounding |
| Bio normalization | `gemini-3-flash-preview` | Plain text generation |
| Research idea generation | `gemini-3.1-pro-preview` | HIGH thinking level |
| Paper embeddings (UMAP) | `gemini-embedding-001` | task_type=CLUSTERING, 3072 dims |
| Subfield embeddings | `gemini-embedding-001` | task_type=SEMANTIC_SIMILARITY, 3072 dims |

### Prompt System (`prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`prompts/fetch_papers.md`** — Gemini grounded search: fetch top papers (`{scholar_name}`, `{institution}`, `{num_papers}`)
- **`prompts/fetch_researcher_info.md`** — Gemini grounded search: structured researcher profile (`{scholar_name}`, `{institution}`)
- **`prompts/normalize_bio.md`** — Gemini: normalize bio tone and pronouns (`{scholar_name}`, `{bio}`)
- **`prompts/suggest_next_idea.md`** — Gemini 3.1 Pro: generate research idea (`{scholar_name}`, `{institution}`, `{primary_subfield}`, `{papers_text}`)
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`

### Data Schema (`scholar_board/schemas.py`)

Pydantic models defining the canonical data structure:

- **`Scholar`** — id, name, institution, department, lab_name, lab_url, main_research_area, bio, papers[], primary_subfield, subfields[], suggested_idea, profile_pic, umap_projection{x,y}, cluster
- **`Paper`** — title, abstract, year, venue, citations, authors, url
- **`SubfieldTag`** — subfield, score
- **`ResearchIdea`** — research_thread, open_question, title, hypothesis, approach, scientific_impact, why_now

### Data Pipeline (8 steps)

```
Papers → Profiles → Embed → UMAP+HDBSCAN → Subfields → Ideas → Build → Pics
```

1. **`scripts/scholar_scraper/fetch_papers_gemini.py`** — Gemini 3 Flash Preview + Google Search grounding fetches recent papers per scholar → `data/scholar_papers/*.json`. Supports `--workers 25` for parallel execution.
2. **`scholar_board/profile_extractor.py`** — Gemini 3 Flash Preview + grounded search fetches structured profiles, then normalizes bios → `data/scholar_profiles/{id}_{name}.json`. Use `--skip-normalize` to bypass bio normalization. Supports `--workers 25`.
3. **`scripts/create_paper_embeddings.py`** — Gemini `gemini-embedding-001` (task_type=CLUSTERING, 3072 dims) embeds paper text → `data/scholar_embeddings.nc`
4. **`scripts/run_umap_dbscan.py`** — UMAP(cosine, n_neighbors=15) → HDBSCAN(min_cluster_size=10, min_samples=3) → `data/models/*.joblib`
5. **`scripts/assign_subfields.py`** — Gemini `gemini-embedding-001` (task_type=SEMANTIC_SIMILARITY, 3072 dims) assigns subfield tags via cosine similarity → `data/scholar_subfields.json`. Supports `--threshold` for score-based filtering.
6. **`scripts/generate_ideas.py`** — Gemini 3.1 Pro Preview (thinking=HIGH) generates AI-suggested research directions → `data/scholar_ideas/*.json`. Supports `--workers 25`.
7. **`scripts/build_scholars_json.py`** — Merges all sources (CSV + UMAP + papers + profiles + subfields + ideas + pics) → `data/scholars.json`
8. **`scripts/download_profile_pics.py`** — Serper.dev Google Image Search with face/headshot queries → `data/profile_pics/*.jpg`. Supports `--skip-existing`, `--limit`, `--test`.

**Orchestrator:** `scripts/run_pipeline.py` — `--step <name>`, `--from <name>` (run from step onward), `--execute` (all), or status dashboard.

All pipeline scripts support `--dry-run` for safe previewing. Steps 1, 2, and 6 support `--workers N` for parallel API calls (default: 25).

### Legacy Pipeline (still present)

- **`scholar_board/scholar_info_formatter.py`** — Gemini structures raw text → markdown in `data/scholar_markdown/`
- **`scholar_board/scholar_info_summerizer.py`** — Gemini generates summaries in `data/scholar_summaries/`
- **`scholar_board/create_embeddings.py`** — Original embedding script (OpenAI/Gemini/HuggingFace)
- **`scholar_board/low_dim_projection.py`** — Original UMAP/t-SNE/PCA projection

### Frontend (`frontend/`)

React 19 + TypeScript + Vite app (3 production deps: react, react-dom, d3):

- D3.js scatter plot with zoom, pan, brush select, scholar dots colored by cluster (Spectral colormap)
- Tabbed sidebar: Profile (bio, papers, lab link, nearby scholars) + AI Research Idea (hypothesis, approach, impact)
- Live search, institution filter
- See `frontend/CLAUDE.md` for detailed architecture

### Data Server (`serve.py`)

Python HTTP server at project root serving data and API endpoints:

- `/api/scholars` — full scholars.json
- `/api/scholar/{id}` — single scholar lookup
- `/api/search` — name search and research query UMAP projection
- `/data/*` — static files (scholars.json, profile_pics/)
- Vite dev server proxies `/api`, `/data`, `/images` to this server

### Key Data Files

```
data/
├── source/                    # Inputs (never overwritten by pipeline)
│   ├── vss_data.csv           # 730 unique scholars with abstracts
│   └── subfields.json         # 23 subfield definitions
├── pipeline/                  # Intermediates (safe to delete and regenerate)
│   ├── scholar_papers/        # Per-scholar paper JSONs (step 1)
│   ├── scholar_profiles/      # Per-scholar profile JSONs (step 2)
│   ├── scholar_embeddings.nc  # 730×3072 embedding matrix (step 3)
│   ├── models/                # Trained UMAP + HDBSCAN models (step 4)
│   ├── scholar_subfields.json # Subfield tag assignments (step 5)
│   └── scholar_ideas/         # AI-generated research directions (step 6)
├── build/                     # Final assembled outputs (served by serve.py)
│   ├── scholars.json          # Master dataset loaded by the frontend
│   ├── profile_pics/          # Headshot images — name_XXXX.jpg
│   └── scholars/              # Per-scholar JSON files
└── archive/                   # Legacy/obsolete data (not used by pipeline)
```

## Environment

Requires a `.env` file with API keys: `GOOGLE_API_KEY` (or `GEMINI_API_KEY`), `SERPER_API_KEY` (for profile pic downloads). Python 3.10+, managed with `uv`. Use `uv run` to execute scripts and `uv add` to install packages.

## Code Conventions

- Use direct official SDKs (e.g., `google-genai`) instead of LangChain wrappers (e.g., `langchain-google-genai`) unless explicitly asked otherwise
- Library code in `scholar_board/` (importable module); standalone scripts in `scripts/`
- All API prompts externalized in `prompts/*.md`, loaded via `scholar_board/prompt_loader.py`
- Data schema defined with Pydantic in `scholar_board/schemas.py`
- Data artifacts in `data/` (git-ignored); structured as `source/`, `pipeline/`, `build/`, `archive/`
- Embedding data uses xarray/NetCDF; trained models use joblib
- Profile pic naming: `scholar_name_XXXX.jpg` (lowercase, underscores)
- All pipeline scripts support `--dry-run` flag

## Git & Commits
- When the user asks to "commit", "commit this", or "commit and push", invoke the `/commit` skill
- Never add `Co-Authored-By: Claude` or any AI attribution to commit messages

## Skills & MCP
- When asked to create a Claude Code 'skill', create a SKILL.md reference documentation file under `.claude/skills/<name>/SKILL.md` — NOT an executable tool or script
- MCP config goes in `.mcp.json` at project root, NOT in `.claude/settings.json`
