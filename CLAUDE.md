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

# Run a single pipeline module directly (all support --dry-run)
uv run -m scholar_board.pipeline.fetch_papers --dry-run --limit 5
uv run -m scholar_board.pipeline.fetch_profiles --dry-run --limit 5
uv run -m scholar_board.pipeline.embed --dry-run
uv run -m scholar_board.pipeline.ideas --dry-run --limit 5
uv run -m scholar_board.pipeline.pics --dry-run --limit 5

# Frontend development (two terminals)
uv run serve.py                         # Terminal 1: data server → :8000
cd frontend && npm run dev              # Terminal 2: Vite dev server → :5173

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

### Shared Infrastructure (`scholar_board/`)

- **`scholar_board/config.py`** — all path constants (`PAPERS_DIR`, `PROFILES_DIR`, `EMBEDDINGS_PATH`, `SCHOLARS_JSON`, etc.) + API key accessors (`get_gemini_api_key()`, `get_serper_api_key()`, `get_openai_api_key()`) + common helpers (`load_scholars_csv()`, `load_paper_texts()`)
- **`scholar_board/gemini.py`** — shared Gemini utilities: `get_client()`, `parse_json_response()`, `extract_grounding_sources()`, `embed_texts(task_type=...)`
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`, loads from `scholar_board/prompts/*.md`
- **`scholar_board/schemas.py`** — Pydantic models: `Scholar`, `Paper`, `SubfieldTag`, `UMAPProjection`, `ResearchIdea`

### Prompt Templates (`scholar_board/prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`normalize_bio.md`** — normalize bio tone and pronouns (`{scholar_name}`, `{bio}`)
- **`suggest_next_idea.md`** — generate research idea (`{scholar_name}`, `{institution}`, `{primary_subfield}`, `{papers_text}`)
- **`fetch_papers.md`** — reference documentation for paper-fetching prompt
- **`fetch_researcher_info.md`** — reference documentation for profile-fetching prompt

### Data Pipeline (8 steps)

```
Papers → Profiles → Embed → UMAP+HDBSCAN → Subfields → Ideas → Build → Pics
```

All pipeline steps live in `scholar_board/pipeline/` and are invoked by `scripts/run_pipeline.py` as `python -m scholar_board.pipeline.<step>`.

1. **`fetch_papers`** — Gemini 3 Flash Preview + Google Search grounding fetches recent papers per scholar → `data/pipeline/scholar_papers/*.json`. Supports `--workers 25` for parallel execution.
2. **`fetch_profiles`** — Gemini 3 Flash Preview + grounded search fetches structured profiles, then normalizes bios → `data/pipeline/scholar_profiles/{id}_{name}.json`. Use `--skip-normalize` to bypass bio normalization. Supports `--workers 25`.
3. **`embed`** — Gemini `gemini-embedding-001` (task_type=CLUSTERING, 3072 dims) embeds paper text → `data/pipeline/scholar_embeddings.nc`
4. **`cluster`** — UMAP(cosine, n_neighbors=15) → HDBSCAN(min_cluster_size=10, min_samples=3) → `data/pipeline/models/*.joblib`
5. **`subfields`** — Gemini `gemini-embedding-001` (task_type=SEMANTIC_SIMILARITY) assigns subfield tags via cosine similarity → `data/pipeline/scholar_subfields.json`
6. **`ideas`** — Gemini 3.1 Pro Preview (thinking=HIGH) generates AI-suggested research directions → `data/pipeline/scholar_ideas/*.json`. Supports `--workers 25`.
7. **`build`** — Merges all sources (CSV + UMAP + papers + profiles + subfields + ideas + pics) → `data/build/scholars.json`
8. **`pics`** — Serper.dev Google Image Search with face/headshot queries → `data/build/profile_pics/*.jpg`. Supports `--skip-existing`, `--limit`, `--test`.

**Orchestrator:** `scripts/run_pipeline.py` — `--step <name>`, `--from <name>` (run from step onward), `--execute` (all), or status dashboard.

All pipeline modules support `--dry-run` for safe previewing. Steps 1, 2, and 6 support `--workers N` for parallel API calls (default: 25).

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
└── build/                     # Final assembled outputs (served by serve.py)
    ├── scholars.json          # Master dataset loaded by the frontend
    ├── profile_pics/          # Headshot images — name_XXXX.jpg
    └── scholars/              # Per-scholar JSON files
```

## Environment

Requires a `.env` file with API keys: `GOOGLE_API_KEY` (or `GEMINI_API_KEY`), `SERPER_API_KEY` (for profile pic downloads). Python 3.10+, managed with `uv`. Use `uv run` to execute scripts and `uv add` to install packages.

## Code Conventions

- Use direct official SDKs (e.g., `google-genai`) instead of LangChain wrappers unless explicitly asked otherwise
- All pipeline logic lives in `scholar_board/pipeline/`; `scripts/` contains only the orchestrator (`run_pipeline.py`) and dev utilities
- Shared paths, API key helpers, and common functions go in `scholar_board/config.py`
- Shared Gemini utilities go in `scholar_board/gemini.py`
- All API prompts are in `scholar_board/prompts/*.md`, loaded via `scholar_board/prompt_loader.py`
- Data schema defined with Pydantic in `scholar_board/schemas.py`
- Data artifacts in `data/` (git-ignored); structured as `source/`, `pipeline/`, `build/`
- Embedding data uses xarray/NetCDF; trained models use joblib
- Profile pic naming: `scholar_name_XXXX.jpg` (lowercase, underscores)
- All pipeline modules support `--dry-run` flag

## Git & Commits
- When the user asks to "commit", "commit this", or "commit and push", invoke the `/commit` skill
- Never add `Co-Authored-By: Claude` or any AI attribution to commit messages

## Skills & MCP
- When asked to create a Claude Code 'skill', create a SKILL.md reference documentation file under `.claude/skills/<name>/SKILL.md` — NOT an executable tool or script
- MCP config goes in `.mcp.json` at project root, NOT in `.claude/settings.json`
