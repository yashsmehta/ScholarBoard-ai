# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScholarBoard.ai creates interactive 2D dashboards of researchers arranged by research similarity. The entire pipeline runs on Google Gemini models — Gemini 3 Flash Preview (grounded search for papers/profiles), Gemini 3.1 Pro Preview (research idea generation with HIGH thinking), and Gemini gemini-embedding-001 (CLUSTERING embeddings for the UMAP map layout). Subfield/topic-area assignment is done by an LLM classifier (Gemini 3 Flash), not embeddings. Uses UMAP to project the clustering embeddings down to the 2D map layout (positions only — no HDBSCAN clustering). The dataset holds ~930 seeded researchers, of which ~810 are classified as PIs and shipped to the live map (vision science / VSS).

**Live site:** https://yashsmehta.com/scholarboard/
**Analytics:** https://scholarboard.goatcounter.com (GoatCounter — privacy-friendly, no cookies)

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

**ALWAYS use Gemini 3 generation models** (`gemini-3-flash-preview` or `gemini-3.1-pro-preview`). Never use deprecated `gemini-2.0-flash`, `gemini-2.5-flash`, or `gemini-2.5-pro` — these are older generations.

| Task | Model | Details |
|---|---|---|
| Paper fetching | `gemini-3-flash-preview` | Google Search grounding |
| Profile extraction | `gemini-3-flash-preview` | Google Search grounding |
| Bio normalization | `gemini-3-flash-preview` | Plain generation |
| Scholar classification | `gemini-3-flash-preview` | Structured JSON output |
| Research idea generation | `gemini-3.1-pro-preview` | thinking_level=HIGH |
| Paper embeddings (UMAP) | `gemini-embedding-001` | task_type=CLUSTERING, 3072 dims |
| Subfield / topic-area assignment | `gemini-3-flash-preview` | LLM classifier, structured JSON output (enum-constrained) |
| Image generation | `gemini-3.1-flash-image-preview` | Nano Banana 2 — aspect_ratio, image_size config |

**Gemini 3 model quick reference:**
- `gemini-3-flash-preview` — fast/cheap, free tier, best for bulk tasks, grounding, classification
- `gemini-3.1-pro-preview` — most capable, best for complex reasoning; supports `thinking_level` (MINIMAL/LOW/MEDIUM/HIGH)
- Thinking: Gemini 3 uses `thinking_level` (not `thinking_budget`); cannot disable on Pro models
- Structured output: use `response_mime_type="application/json"` + `response_schema={...}` for reliable JSON
- Grounding: `tools=[types.Tool(google_search=types.GoogleSearch())]` — billed via Vertex AI GCP credits (no monthly cap)

### Shared Infrastructure (`scholar_board/`)

- **`scholar_board/config.py`** — all path constants (`PAPERS_DIR`, `PROFILES_DIR`, `EMBEDDINGS_PATH`, `SCHOLARS_JSON`, etc.) + API key accessors (`get_gemini_api_key()`, `get_serper_api_key()`, `get_openai_api_key()`) + common helpers (`load_paper_texts()`)
- **`scholar_board/db.py`** — SQLite layer: `get_connection()`, `init_db()`, `load_scholars(is_pi_only=False/True)`, `set_is_pi()`, `ensure_scholar()`, `upsert_papers()`, `upsert_profile()`, `upsert_subfields()`, `upsert_idea()`, `upsert_cluster()`, `upsert_scholar_stats()`, `upsert_research_direction()`, `upsert_profile_pic()`
- **`scholar_board/gemini.py`** — **ALL Gemini API interactions MUST go through this file** — never call `client.models.*` directly from pipeline modules. Shared utilities: `get_client()`, `parse_json_response()`, `extract_grounding_sources()`, `generate_text()`, `generate_image()`, `embed_texts(task_type=...)`
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`, loads from `scholar_board/prompts/*.md`
- **`scholar_board/schemas.py`** — Pydantic models: `Scholar`, `Paper`, `SubfieldTag`, `UMAPProjection`, `ResearchIdea`

### Prompt Templates (`scholar_board/prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`normalize_bio.md`** — normalize bio tone and pronouns (`{scholar_name}`, `{bio}`)
- **`suggest_next_idea.md`** — generate research idea (`{scholar_name}`, `{institution}`, `{primary_subfield}`, `{papers_text}`)
- **`fetch_papers.md`** — reference documentation for paper-fetching prompt
- **`fetch_researcher_info.md`** — reference documentation for profile-fetching prompt
- **`field_directions.md`** — synthesize collective field-level research patterns per subfield

### Data Pipeline (13 steps)

```
Discover → Seed → Papers → Profiles → Stats → Directions → Embed → UMAP → Subfields → Field Directions → Ideas → Build → Pics
```

All pipeline steps live in `scholar_board/pipeline/` and are invoked by `scripts/run_pipeline.py` as `python -m scholar_board.pipeline.<step>`. The SQLite DB (`data/scholarboard.db`) is the **single source of truth** — all steps load scholars from DB and write back to DB. JSON files are written in parallel as human-readable artifacts.

**Dataset today:** ~930 scholars in the DB, of which **~810 are classified PIs**. Steps 0–3 run on ALL scholars; steps 4–12 (stats onward) filter to `is_pi = 1`, so only PIs are embedded, projected onto the map, and shipped to the frontend (`scholars.json`).

0. **`discover`** (`fetch_extra_researchers`) — Gemini 3 Flash Preview queries each of the 21 VSS topic areas for active researchers in parallel (ThreadPoolExecutor), writes new entries to `data/source/extra_researchers.csv` (E-prefixed IDs). Run this before `seed`.
1. **`seed`** — Merges VSS CSV + `extra_researchers.csv` into `data/scholarboard.db` with 3-stage deduplication: (1) exact name match, (2) fuzzy score ≥ 90, (3) Gemini Flash decides for 70–89 borderline cases. All subsequent steps read from this DB.
2. **`fetch_papers`** (`papers`) — Gemini 3 Flash Preview + Google Search grounding fetches recent papers per scholar → `data/pipeline/scholar_papers/*.json` + DB. Runs on ALL scholars. Supports `--workers 25`.
3. **`fetch_profiles`** (`profiles`) — Gemini 3 Flash Preview + grounded search fetches structured profiles, then classifies each scholar as PI or not (`is_pi` column in DB), then normalizes bios for PIs → `data/pipeline/scholar_profiles/{id}_{name}.json`. Supports `--workers 25`.

   *── steps below run on PIs only (`is_pi = 1`) ──*
4. **`stats`** — Serper.dev locates each PI's Google Scholar profile and scrapes total citations + h-index → DB (`total_citations`, `h_index`). Supports `--workers`.
5. **`directions`** — Gemini 3.1 Pro Preview (thinking) distills a concise "current research direction" paragraph per PI from their papers → `data/pipeline/scholar_directions/*.json` + DB (`research_direction`). Supports `--workers 25`.
6. **`embed`** — Gemini `gemini-embedding-001` (task_type=CLUSTERING, 3072 dims) embeds each PI's **research direction + paper text** → `data/pipeline/scholar_embeddings.nc`
7. **`cluster`** (`umap`) — UMAP(cosine, n_neighbors=15, min_dist=0.1) projects the 3072-dim embeddings to 2D; writes `umap_x/umap_y` to DB and the trained reducer → `data/pipeline/models/umap_model.joblib`. (No HDBSCAN — dot color is driven by the LLM subfield tags, not cluster labels.)
8. **`subfields`** — Gemini 3 Flash Preview reads each PI's profile + papers and classifies them into the 21 VSS topic areas (one primary + up to two secondary), via enum-constrained structured JSON output → `data/pipeline/scholar_subfields.json` + DB. Supports `--workers 25`.
9. **`field_directions`** — Gemini 3.1 Pro Preview (thinking=HIGH) synthesizes one field-level summary per subfield (overview, active themes, open questions, methods, emerging directions) → `data/build/field_directions.json`
10. **`ideas`** — Gemini 3.1 Pro Preview (thinking=HIGH) generates an AI-suggested research direction per PI → `data/pipeline/scholar_ideas/*.json` + DB. Supports `--workers 25`.
11. **`build`** — Reads all data from DB and exports → `data/build/scholars.json` + per-scholar JSONs in `data/build/scholars/`
12. **`pics`** — Serper.dev Google Image Search with face/headshot queries → `data/build/profile_pics/*.jpg`. Supports `--skip-existing`, `--limit`, `--test`.

**Orchestrator:** `scripts/run_pipeline.py` — no args shows a status dashboard; `--step <name>` runs one step, `--from <name>` runs from a step onward, `--execute` runs all. Step names are the short names above (e.g. `discover`, `papers`, `umap`), not the module filenames.

All pipeline modules support `--dry-run` for safe previewing. The per-scholar API steps (`papers`, `profiles`, `stats`, `directions`, `ideas`) support `--workers N` for parallel calls (default: 25).

### Frontend (`frontend/`)

React 19 + TypeScript + Vite app (3 production deps: react, react-dom, d3):

- **Map view:** D3.js scatter plot with zoom, pan, brush select, scholar dots colored by subfield
- **List view:** Alphabetical directory with avatars, institutions, and subfield badges (toggled via button next to filters)
- **Field Directions:** AI-generated summaries of research trends per subfield (full-page modal)
- **Onboarding:** 4-step welcome tour for first-time visitors
- Tabbed sidebar: Profile (bio, papers, lab link, nearby scholars) + AI Research Idea (hypothesis, approach, impact)
- Live search, institution + subfield filters
- GoatCounter analytics (script in `index.html`)
- See `frontend/CLAUDE.md` for detailed architecture

### Data Server (`serve.py`)

Python HTTP server at project root serving data and API endpoints:

- `/api/scholars` — full scholars.json
- `/api/scholar/{id}` — single scholar lookup
- `/api/search` — name search and research query UMAP projection
- `/data/*` — static files (scholars.json, profile_pics/)
- Vite dev server proxies `/api`, `/data`, `/images` to this server

### Key Data Files

See `data/CLAUDE.md` for full data directory documentation including the SQLite schema.

```
data/
├── source/                    # Inputs (never overwritten by pipeline)
│   ├── vss_data.csv           # ~730 VSS scholars with abstracts
│   ├── extra_researchers.csv  # Additional researchers found by discover step
│   └── subfields.json         # 21 VSS topic-area definitions
├── pipeline/                  # Intermediates (safe to delete and regenerate)
│   ├── scholar_papers/        # Per-scholar paper JSONs (papers step)
│   ├── scholar_profiles/      # Per-scholar profile JSONs (profiles step)
│   ├── scholar_directions/    # Per-scholar research-direction paragraphs (directions step)
│   ├── scholar_embeddings.nc  # N×3072 embedding matrix (embed step)
│   ├── models/                # Trained UMAP reducer (umap step)
│   ├── scholar_subfields.json # Subfield tag assignments (subfields step)
│   └── scholar_ideas/         # AI-generated research ideas (ideas step)
├── build/                     # Final assembled outputs (served by serve.py)
│   ├── scholars.json          # Master dataset loaded by the frontend
│   ├── field_directions.json  # AI-generated field-level research summaries
│   ├── profile_pics/          # Headshot images — name_XXXX.jpg
│   └── scholars/              # Per-scholar JSON files
└── scholarboard.db            # SQLite database — queryable source of truth
```

### Personas subsystem (`scholar_board/personas/`)

A standalone offshoot — **not part of the 13-step map pipeline**. It generates info-dense, one-line technical persona summaries for researchers in a single target subfield (e.g. Brain-AI Alignment), topping up sparse publication records via the OpenAlex API. Driven by `scripts/build_brain_ai_personas.py`; outputs per-scholar markdown to the top-level `personas/` directory plus `personas/index.json`. Package modules: `build.py`, `selection.py`, `openalex.py`, `render.py`, `config.py`, `utils.py`.

## Environment

All Gemini API calls go through **Vertex AI** using GCP credits — never the free AI Studio tier. This avoids all quota limits. Required `.env` vars:

```
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=gen-lang-client-0905516452
GOOGLE_CLOUD_LOCATION=global
SERPER_API_KEY=...       # for profile pic downloads
GOOGLE_API_KEY=...       # kept as fallback only; not used when Vertex AI is active
```

Authentication: `gcloud auth application-default login` must be run once (credentials stored at `~/.config/gcloud/application_default_credentials.json`). The `get_client()` function in `scholar_board/gemini.py` automatically detects `GOOGLE_GENAI_USE_VERTEXAI=True` and uses ADC instead of the API key.

Python 3.10+, managed with `uv`. Use `uv run` to execute scripts and `uv add` to install packages.

## Deployment

The site is deployed as a static build to a Jekyll-based GitHub Pages site (`yashsmehta.github.io`).

### Automatic deploy via GitHub Actions

The workflow at `.github/workflows/deploy-scholarboard.yml` runs on every push to `main` that touches `frontend/**`, `data/build/**`, or the workflow file itself. It:
1. Builds the frontend with `VITE_BASE=/scholarboard/`
2. Clones the website repo via the `WEBSITE_DEPLOY_KEY` SSH deploy key (into `$RUNNER_TEMP/website` to avoid clashing with the local `website/` screenshots dir)
3. Rsyncs `frontend/dist/*` + `data/build/scholars.json`, `field_directions.json`, and `profile_pics/` into `scholarboard/` in the website repo
4. Commits and pushes to `master` of `yashsmehta.github.io` — that push triggers Jekyll → `gh-pages` deploy

**To deploy: just `git push` this repo's `main`.** No local hook, no local clone of the website repo, no manual sync step needed.

Manual trigger: `workflow_dispatch` is enabled, so you can also run the workflow from the GitHub Actions tab.

### Important

- **Never edit `scholarboard/` files directly in the website repo** — the workflow overwrites them on next deploy
- The `WEBSITE_DEPLOY_KEY` secret in this repo holds the SSH private key with write access to `yashsmehta.github.io`
- `website/` (local) contains screenshot PNGs used for documentation (field directions, onboarding steps, list view) — unrelated to deployment
- Data-only changes (e.g. cleanups to `data/build/scholars.json`) still trigger a redeploy because `data/build/**` is in the workflow's `paths` filter

## Code Conventions

- Use direct official SDKs (e.g., `google-genai`) instead of LangChain wrappers unless explicitly asked otherwise
- All pipeline logic lives in `scholar_board/pipeline/`; `scripts/` contains only the orchestrator (`run_pipeline.py`)
- **DB-first**: all pipeline steps load scholars via `load_scholars(is_pi_only=...)` from `scholar_board/db.py` — never from CSV directly
- **`is_pi` flag**: `fetch_profiles` classifies every scholar and writes `is_pi` to DB; steps 3–8 (embed through pics) filter to `is_pi=1` only
- Shared paths, API key helpers, and common functions go in `scholar_board/config.py`
- **Gemini gateway**: ALL Gemini API calls must go through `scholar_board/gemini.py` — never call `client.models.*` directly in pipeline modules. Use `generate_text()`, `generate_image()`, `embed_texts()`, etc.
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
