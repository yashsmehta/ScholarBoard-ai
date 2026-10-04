# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ScholarBoard.ai creates interactive 2D dashboards of researchers arranged by research similarity. Each PI's profile (current affiliation, lab link, photo, Google Scholar stats, the 5 most impactful 2023+ first/last/second-to-last-author papers, bio, AI research summary, VSS topic areas, country, private sex label) is built by a **headless Claude Code agent** (Sonnet 5.5, on the Claude subscription — `profile_agent`). Gemini covers `gemini-embedding-001` (CLUSTERING embeddings for the UMAP map layout), Gemini 3.1 Pro Preview (field-level summaries) and Gemini 3.8 Flash (the Agentic Search keywords). UMAP projects the embeddings to the 2D map (positions only — no HDBSCAN clustering). The dataset holds ~930 seeded researchers, of which ~800 are classified as PIs and shipped to the live map (vision science / VSS). The first-release profiles (797 PIs) were built with the earlier Gemini steps and are not re-run; the agent builds every PI added from now on.

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

# Add a new PI: agent → verify → DB → embed + place on the existing map → build → Agentic Search keywords
uv run -m scholar_board.pipeline.profile_agent --add "Full Name" --hint "Institution on file"
uv run -m scholar_board.pipeline.profile_agent --add "Full Name" --dry-run   # plan + prompt, no agent, no writes

# Run a single pipeline module directly (all support --dry-run)
uv run -m scholar_board.pipeline.embed --dry-run
uv run -m scholar_board.pipeline.search_cards --dry-run

# Frontend development (two terminals)
uv run serve.py                         # Terminal 1: data server → :8000
cd frontend && npm run dev              # Terminal 2: Vite dev server → :5173

# Install a new package
uv add <package-name>
```

## Architecture

### Models Used

| Task | Model | Details |
|---|---|---|
| **Per-PI profile** (affiliation, lab link, photo, Scholar stats, papers, bio, research direction, topic areas, country, sex) | `claude-sonnet-5-5` | Headless Claude Code (`claude -p`, `--safe-mode`, effort high) on the **Claude subscription** — `ANTHROPIC_API_KEY` is stripped from its env, so no API credits. Tools: Bash, Read, Write, WebSearch, WebFetch + `scholar_board/agent_tools/` |
| Agentic Search keywords (`search_cards`) | `gemini-3.8-flash` | Structured JSON, one call per PI, 25 in parallel (`generate_json()`, `FLASH_MODEL`) |
| Paper embeddings (UMAP) | `gemini-embedding-001` | task_type=CLUSTERING, 3072 dims |
| Field directions | `gemini-3.1-pro-preview` | thinking=HIGH, one summary per topic area |
| Image generation | `gemini-3.1-flash-image` | Nano Banana 2 — aspect_ratio, image_size config |

Claude's `total_cost_usd` in the agent's `result.json` is the API-equivalent value, not a charge; the real limit is the subscription's usage/concurrency.

**Gemini quick reference** (for the remaining Gemini steps): `gemini-3.1-pro-preview` supports `thinking_level` (MINIMAL/LOW/MEDIUM/HIGH; Gemini 3 uses `thinking_level`, not `thinking_budget`). Never use deprecated `gemini-2.x` models.

### Shared Infrastructure (`scholar_board/`)

- **`scholar_board/config.py`** — all path constants (`PAPERS_DIR`, `PROFILES_DIR`, `EMBEDDINGS_PATH`, `SCHOLARS_JSON`, etc.) + API key accessors (`get_gemini_api_key()`, `get_serper_api_key()`, `get_openai_api_key()`) + common helpers (`load_paper_texts()`)
- **`scholar_board/db.py`** — SQLite layer: `get_connection()`, `init_db()`, `load_scholars(is_pi_only=False/True)`, `set_is_pi()`, `ensure_scholar()`, `upsert_papers()`, `upsert_profile()`, `upsert_subfields()`, `upsert_cluster()`, `upsert_scholar_stats()`, `upsert_research_direction()`, `upsert_profile_pic()`
- **`scholar_board/gemini.py`** — **ALL Gemini API interactions MUST go through this file** — never call `client.models.*` directly from pipeline modules. Shared utilities: `get_client()`, `parse_json_response()`, `generate_json()` (structured output, `FLASH_MODEL` default), `generate_image()`, `embed_texts(task_type=...)`
- **`scholar_board/agent_tools/`** — stdlib-only helper scripts copied into each profile-agent workspace: `openalex.py` (author candidates; every 2023+ first/last/second-to-last-author work with exact position, citations/year and ABSTRACT?/ERRATUM/DUPLICATE flags; abstracts), `crossref.py` (DOI records, full author order), `gscholar.py` (Scholar profile: affiliation, homepage, All/Since citations and h-index, latest papers)
- **`scholar_board/prompt_loader.py`** — `load_prompt(name)` and `render_prompt(name, **kwargs)`, loads from `scholar_board/prompts/*.md`
- **`scholar_board/schemas.py`** — Pydantic models: `Scholar`, `Paper`, `SubfieldTag`, `UMAPProjection`

### Prompt Templates (`scholar_board/prompts/`)

All API prompts are externalized as markdown templates with `{variable}` substitution:

- **`profile_agent.md`** — the profile agent's full instructions (step sequence, paper-selection judgment, writing rules, output schema); filled with `{name}`, `{institution_hint}`, `{today}`, `{subfields}` by `profile_agent.py` (plain replace, since the template contains JSON)
- **`search_card.md`** — Agentic Search keywords: up to 10 extremely specific keywords per PI (`{bio}`, `{research_direction}`, `{papers_text}`)
- **`field_directions.md`** — synthesize collective field-level research patterns per subfield
- **`nl_search_tiered.md`** — the Agentic Search ranking agent

### Data Pipeline (7 steps)

```
Seed → Profiles (agent) → Embed → UMAP → Field Directions → Build → Search Cards
```

All pipeline steps live in `scholar_board/pipeline/` and are invoked by `scripts/run_pipeline.py` as `python -m scholar_board.pipeline.<step>`. The SQLite DB (`data/scholarboard.db`) is the **single source of truth** — all steps load scholars from DB and write back to DB. JSON files are written in parallel as human-readable artifacts.

**Dataset today:** ~930 scholars in the DB, of which **797 are PIs** (`is_pi = 1`) — only PIs are embedded, projected onto the map, and shipped to the frontend (`scholars.json`). The first-release profiles came from the retired Gemini steps (`discover`, `papers`, `profiles`, `stats`, `directions`, `subfields`, `countries`, `pics`, `sex`) plus the September 2026 per-PI refresh; they are **not** re-run.

1. **`seed`** — one-time bootstrap: merges the VSS CSV + `extra_researchers.csv` into `data/scholarboard.db` with fuzzy-name dedup (exact or score ≥ 90 → skip; 70–89 → inserted and printed for a human to check).
2. **`profiles`** (`profile_agent`) — **one headless Claude Code agent per PI** (Sonnet 5.5, subscription; workspace in `data/pipeline/agent_runs/<id>_<time>/` with prompt, `profile.json`, photo, `result.json`, `validated.json`). Sequence (prompt `profile_agent.md`): identity (Scholar profile + own site + OpenAlex ids) → current affiliation and lab link (own site > current university pages > Scholar > never OpenAlex alone; a stale personal site loses to current institution pages) and is_pi → photo (largest image on an official page naming the PI, opened and checked; never social-media avatars) → Scholar "All" citations + h-index (OpenAlex fallback) → candidates: every 2023+ first/last/second-to-last-author paper (second-to-last = often co-senior), no meeting abstracts/errata/duplicates, published version under its journal → **the 5 most impactful recent works**, a judgment weighing venue prestige, citations per year, recency and centrality (preprints compete on merit, no caps) → real abstracts read, summaries written, authors copied from Crossref → bio (research only) and research direction (from the 5 papers only) → VSS topic areas (primary + ≤2 secondary, exact names), country, sex (pronouns on a page about them, else unknown) → self-check. `profile_agent.py` then **re-verifies every paper** on OpenAlex/Crossref (exists, title matches, PI first/last/second-to-last, 2023+, not an abstract — failures are dropped), drops social-media photos, and writes DB + `scholar_papers/`, `scholar_profiles/`, `scholar_directions/`, `scholar_subfields.json`, `institution_countries.json` (only new institutions), `scholar_sex.json`, `profile_pics/` (≤400 px JPEG). New PIs are then embedded (`embed --ids`) and placed with the saved UMAP model (`umap --place`, no refit), `build` runs, and their Agentic Search keywords are generated (`search_cards`, Gemini Flash). Guards: names similar to an existing scholar are refused (`--allow-similar` to override), PIs removed at their request (`pi_overrides.json`) are never re-added, and **protected PIs** (`data/source/protected_pis.json` — profiles hand-edited at the PI's request) are never touched. Overrides still win: `pi_overrides.json`, `subfield_overrides.json`, `sex_overrides.json`. Modes: `--add NAME [--hint INST]` (repeatable, `--workers`), `--id ID` (re-run an unprotected PI), `--pending` (every scholar with `is_pi` unset — the orchestrator step), `--apply <workspace>` (re-apply a saved run), `--no-place`, `--dry-run`.
3. **`embed`** — Gemini `gemini-embedding-001` (task_type=CLUSTERING, 3072 dims) embeds each PI's **research direction + paper text** → `data/pipeline/scholar_embeddings.nc`. `--ids` embeds only those PIs and merges them into the file.
4. **`umap`** (`cluster`) — UMAP(cosine, n_neighbors=15, min_dist=0.1) projects the 3072-dim embeddings to 2D; writes `umap_x/umap_y` to DB and the trained reducer → `data/pipeline/models/umap_model.joblib`. `--place IDS` projects new PIs with the saved model instead of refitting. (No HDBSCAN — dot color is driven by the topic-area tags.)
5. **`field_directions`** — Gemini 3.1 Pro Preview (thinking=HIGH) synthesizes one field-level summary per topic area (overview, active themes, open questions, methods, emerging directions) → `data/build/field_directions.json`
6. **`build`** — Reads all data from DB (plus `institution_countries.json` for each scholar's `country`) and exports → `data/build/scholars.json` + per-scholar JSONs in `data/build/scholars/`
7. **`search_cards`** — Gemini 3.8 Flash writes each PI's Agentic Search keywords: up to 10 extremely technical, specific keywords (any mix of phenomena, methods, species, paradigms, datasets — no sentence, no fixed groups), one structured-JSON call per PI, `--workers 25` in parallel → `data/build/search_cards.json` (tracked). Each entry: `keywords`, `card` (keywords joined with `; ` — the PI's line in the Agentic Search index), `hash` (fingerprint of bio + direction + papers). Computed once and saved; re-runs only regenerate new or changed PIs (`--force` for everyone, ~5.5 min for 797). Hand-edited profiles stay ground truth: only their keywords (a derived index) are regenerated.

**Orchestrator:** `scripts/run_pipeline.py` — no args shows a status dashboard; `--step <name>` runs one step, `--from <name>` runs from a step onward, `--execute` runs all. Step names are the short names above (e.g. `profiles`, `umap`), not the module filenames. Note `embed`/`umap` as orchestrator steps do a **full** re-embed and refit (moves every dot); adding a PI never needs them.

### Frontend (`frontend/`)

React 19 + TypeScript + Vite app (3 production deps: react, react-dom, d3):

- **Map view:** D3.js scatter plot with zoom, pan, brush select, scholar dots colored by subfield
- **List view:** Alphabetical directory with avatars, institutions, and subfield badges (toggled via button next to filters)
- **Field Directions:** AI-generated summaries of research trends per subfield (full-page modal)
- **Onboarding:** 5-step welcome tour for first-time visitors (last step: Agentic Search)
- Sidebar profile: bio, papers, lab link, subfield badges, nearby scholars
- Live search, institution + country + subfield filters
- GoatCounter analytics (script in `index.html`)
- See `frontend/CLAUDE.md` for detailed architecture

### Agentic Search (`scholar_board/nlsearch/`, `server/`)

Natural-language PI search ("PIs using MEG for scene perception", "best reviewers for this abstract: …"), adapted from aos-ai's headless-agent ranker but single-pass (no filter planning):

- **Corpus** (`nlsearch/corpus.py`) — built from `scholars.json` + `search_cards.json`, no API calls: `index/part-NN.txt` (`id | name | up to 10 keywords`, no metadata; ~200 KB in shards ≤27 KB so each fits one agent file view), `meta.db` (SQLite: `pi` with institution/country/h-index/bio/direction, `paper` with titles/authors), `tools/` (the agent's helpers, stdlib-only, from `nlsearch/tools/`), and `profiles/<id>.json`.
- **Ranking** (`nlsearch/rank.py`, prompt `prompts/nl_search_tiered.md`) — one agent session per search, in a fresh temp workspace (copy of index/, tools/, meta.db), working in tiers to keep input tokens down:
  0. **Hard filter, only when the request explicitly restricts eligibility** by something meta.db records (location, institution, "not in the US"). The agent translates it with its own knowledge against the values actually in the data (`tools/sql.py` to list distinct values → `tools/filter.py "SELECT id FROM pi WHERE …"` writes only the eligible index lines). Most requests (topic, method, "like X", reviewer abstracts) skip this and never touch meta.db. Seniority and preferences are not hard filters; they are applied when ranking.
  1. Read the whole index (or the filtered lines) → shortlist up to 100 (`NL_SEARCH_SHORTLIST`).
  2. One `tools/details.py <ids>` call → read research directions + paper titles for the shortlist (plus h-index/bio or co-author SQL only when the request needs it).
  3. Rank → top 10 `{id, score, reason}`; prose/`[]` = "no matches" (off-topic or refused).
  Tools write to `work/` in the workspace and append to `work/trace.jsonl`; `search(..., trace={})` returns the filter SQL, eligible count and shortlist size, which the server logs.
  - `agy` (default): Antigravity CLI (`agy`) with a Gemini API key (`GEMINI_API_KEY`, falls back to `GOOGLE_API_KEY`; `modelProvider: "gemini"` in a dedicated `NL_SEARCH_AGY_HOME`), all tool permissions auto-approved, `gemini-3.8-flash-medium` (`NL_SEARCH_AGY_MODEL`). ~50 s, ~$0.16 per search; nearly all of the time is model thinking, not tools.
  - `claude`: headless Claude Code (Sonnet 5.5, `--safe-mode`) with only `Read` and the three `Bash(python3 tools/<tool>.py *)` commands allowed, on a Claude **subscription only** (API keys are stripped from its env). ~23 s.
  - `NL_SEARCH_AGENT_SLOTS` caps concurrent agent processes (~150 MB each). CLI: `uv run -m scholar_board.nlsearch.rank "query" [--engine claude]`.
- **Eval** (`nlsearch/eval/`) — 10 test queries (`queries.json`: topic, method, two reviewer abstracts with author exclusion, "like X", geography/seniority/negative constraints, niche) with graded 0–3 labels in `gold.json` (exhaustive Sonnet recall pass over all 796 PIs → Opus judging full profiles; spot-checked). `run_eval.py run <methods> [--rep 1 2] [--parallel 10]` (runs in parallel; Antigravity token counts need `eval/usage_proxy.py` on :8765, which tags each run's calls via a `/run/<tag>` URL prefix) then `run_eval.py report` (nDCG@10, P@10, grade-3 recall, violations, seconds, tokens split by filtered/unfiltered path, $; repeats → mean ± sd). Findings (2 repeats each): tiered agy medium 0.936±0.013 (~50 s, $0.16) ≈ agy high 0.937±0.006 (~105 s, $0.22) > Claude tiered 0.927±0.001 (~23 s, $0.41, 88K uncached input vs 137K for the old single session); retired designs: Claude map-reduce 0.927±0.018, agy single 0.924, Claude single 0.902. Tier 0 filtered exactly the 2 queries that ask for it. Seniority ("early-career") must be applied as a strong requirement using bio titles, not h-index alone. Run-to-run noise is ~±0.02, so compare methods over repeats. Labels were judged by Opus, a possible slight bias toward Claude outputs.
- **API** (`server/app.py`, FastAPI) — job-based: `POST /api/nl-search` → poll `GET /api/nl-search/{id}`; `GET /api/health`. **The server picks the engine** (users don't): Claude Code while fewer than `NL_SEARCH_CLAUDE_SLOTS` (3, the subscription's concurrency) Claude runs are active, else Antigravity; a failed Claude run is retried on Antigravity, and Claude is then paused — every search goes to Antigravity until the subscription's usage/rate-limit reset (30 min if no reset time is given; `NL_SEARCH_CLAUDE_LIMIT_COOLDOWN_S`) or for 5 min after any other error (`NL_SEARCH_CLAUDE_ERROR_COOLDOWN_S`). `/api/health` shows `claude_active` and `claude_paused_s`. Every result carries `engine`, `seconds`, and `cost_usd` (API price: Claude's `total_cost_usd`, which is what the API would charge even on a subscription; Antigravity's from its token counts × `GEMINI_PRICES` in `rank.py`, taken from ai.google.dev/gemini-api/docs/pricing, including the 2027-01-01 price change). One search at a time per IP (409 while one is queued/running), 10 concurrent agent runs, per-IP (6/10 min) and daily (300) limits, normalized-query cache (returns the original engine/time/cost), searches logged to `searches.jsonl` with engine, cost, filter and shortlist (no IPs). Local: `uv run --with-requirements server/requirements.txt uvicorn server.app:app --port 8001`.
- **Frontend** — browser-style "Directory | Agentic Search" tabs above the left pane; the Agentic Search tab shows `AskPanel` in place of the list/map (profile sidebar stays); results stay in that tab and never change what the Directory map/list shows. While a search runs, the panel shows the agent's live steps (hard filter → shortlist size, read from the tools' trace via `rank.live_steps`, returned as `steps` by `GET /api/nl-search/{id}`) and an estimated progress bar against `expected_seconds` (median of the engine's last 30 runs from `searches.jsonl`). No engine picker; under the results header it shows the engine, seconds and API cost (e.g. "Claude Code · 24 s · $0.43 API cost"). Enabled when `VITE_NL_SEARCH_API` is set (defaults to `http://localhost:8001` in dev).
- **Production** — `https://scholarboard.yashsmehta.com` on the aos-ai server (`ssh aos-prod`), a sandboxed systemd service; see `server/deployment/README.md`.

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
│   ├── extra_researchers.csv  # Additional researchers found by the (retired) discover step
│   ├── subfields.json         # 21 VSS topic-area definitions (given to the profile agent)
│   ├── protected_pis.json     # PIs hand-edited at their request — never overwritten by AI (tracked)
│   ├── pi_overrides.json / subfield_overrides.json / name_aliases.json / institution_countries.json  # tracked
├── pipeline/                  # Intermediates
│   ├── agent_runs/            # One workspace per profile-agent run (prompt, profile.json, photo, result.json)
│   ├── scholar_papers/        # Per-scholar paper JSONs
│   ├── scholar_profiles/      # Per-scholar profile JSONs
│   ├── scholar_directions/    # Per-scholar research-direction paragraphs
│   ├── scholar_embeddings.nc  # N×3072 embedding matrix (embed step)
│   ├── models/                # Trained UMAP reducer (umap step)
│   ├── scholar_subfields.json # Topic-area assignments
│   ├── scholar_sex.json       # Private sex labels (never shipped)
├── build/                     # Final assembled outputs (served by serve.py)
│   ├── scholars.json          # Master dataset loaded by the frontend
│   ├── field_directions.json  # AI-generated field-level research summaries
│   ├── search_cards.json      # Agentic Search index cards (tracked)
│   ├── profile_pics/          # Headshot images — name_XXXX.jpg
│   └── scholars/              # Per-scholar JSON files
└── scholarboard.db            # SQLite database — queryable source of truth
```

### Personas subsystem (`scholar_board/personas/`)

A standalone offshoot — **not part of the map pipeline**. It generates info-dense, one-line technical persona summaries for researchers in a single target subfield (e.g. Brain-AI Alignment), topping up sparse publication records via the OpenAlex API. Driven by `scripts/build_brain_ai_personas.py`; outputs per-scholar markdown to the top-level `personas/` directory plus `personas/index.json`. Package modules: `build.py`, `selection.py`, `openalex.py`, `render.py`, `config.py`, `utils.py`.

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

**To deploy: just `git push` this repo's `main`.** No local hook, no local clone of the website repo, no manual sync step needed. The workflow builds with `VITE_NL_SEARCH_API=https://scholarboard.yashsmehta.com`; the AI-search server pulls `main` itself every 30 min (`server/deployment/update.sh`) and rebuilds its corpus — run `search_cards` after hand edits so the cards match.

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
- **`is_pi` flag**: the profile agent decides `is_pi` (`pi_overrides.json` wins); embed, UMAP, build and search cards use `is_pi=1` only
- **Hand edits are ground truth**: when a PI sends corrections, edit their data by hand, add them to `data/source/protected_pis.json`, note it in `CHANGELOG.md`, then run `search_cards` — no AI step overwrites a protected PI
- Shared paths, API key helpers, and common functions go in `scholar_board/config.py`
- **Gemini gateway**: ALL Gemini API calls must go through `scholar_board/gemini.py` — never call `client.models.*` directly in pipeline modules. Use `embed_texts()`, `generate_image()`, etc.
- **Claude agents**: headless `claude -p` with `--safe-mode`, an explicit `--tools`/`--allowedTools` list, and `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` stripped from the env (subscription only) — same pattern in `profile_agent.py` and `nlsearch/rank.py`
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
