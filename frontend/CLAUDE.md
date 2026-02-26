# Frontend — CLAUDE.md

React + TypeScript + Vite frontend for ScholarBoard.ai. Interactive 2D map of ~730 vision science researchers with D3.js visualization.

## Quick Start

```bash
# Install dependencies
npm install

# Start the data server (from project root, in one terminal)
.venv/bin/python3 serve.py          # → http://localhost:8000

# Start the frontend dev server (in another terminal)
npm run dev                         # → http://localhost:5173

# Type-check + production build
npm run build                       # → dist/

# Lint
npm run lint
```

Vite proxies `/api`, `/data`, `/images` to `http://localhost:8000` (the data server at project root `serve.py`).

## Architecture

**React owns UI state. D3 owns SVG rendering.** They communicate through a controller interface.

```
App.tsx (useReducer)
 ├── Header             — title bar, scholar count
 ├── SearchPanel        — live search with keyboard nav
 ├── FilterPanel        — institution + subfield filter (tabbed dropdown)
 ├── ScholarMap         — thin React wrapper around D3
 │   └── d3MapController — imperative D3 scatter plot (zoom, pan, brush, tooltips)
 ├── MapControls        — reset button, usage hint
 └── Sidebar            — tabbed: Profile | Research Idea
```

### Data Flow

1. `App.tsx` loads scholars via `loadScholars()` (fallback chain: env URL → `/api/scholars` → `/data/scholars.json`)
2. Raw JSON normalized to `Scholar[]` (snake_case → camelCase, validates required fields)
3. State managed by `appReducer` (useReducer) — selection, hover, search, filters
4. `ScholarMap` passes scholars + interaction state to `d3MapController`
5. D3 emits hover/select callbacks → React updates state → pushes back to D3

### D3 Integration Pattern

`d3MapController.ts` (~574 lines) is an imperative "island" — a closure that creates/manages the SVG. React never touches the SVG directly.

**Controller API:**
- `setData(scholars)` — update dots
- `setInteractionState({hoveredId, selectedId, activeInstitutions})` — sync visual state
- `resize()` — refit scales to container
- `resetView()` / `panToScholar(id)` — animated transitions
- `destroy()` — cleanup

**Dot layers:** Visual dots (no pointer events, styled) + invisible hit dots (larger radius for touch/click targets). Selection ring is a separate SVG circle.

### Sidebar

Two tabs, controlled by `SidebarTab` type (`'profile' | 'idea'`). Defaults to Profile, resets when a new scholar is selected.

**Profile tab:** Avatar (with fallback chain: profile pic → default avatar → initials), name, institution, department, lab link, bio, subfield badges (clickable — triggers subfield filter), recent papers (top 5), education, similar researchers (5 nearest by UMAP distance).

**Research Idea tab:** AI-generated research direction — title, research thread, open question, hypothesis, approach, scientific impact, why now. Shows empty state when no idea exists for a scholar.

## File Structure

```
src/
├── main.tsx                  — React entry point
├── App.tsx                   — Root component, state orchestration
├── components/
│   ├── Header.tsx            — Title bar (presentational)
│   ├── SearchPanel.tsx       — Search input + autocomplete dropdown
│   ├── FilterPanel.tsx       — Institution filter with draft/apply pattern
│   ├── ScholarMap.tsx        — D3 controller lifecycle bridge
│   ├── MapControls.tsx       — Reset button + auto-hiding hint
│   └── Sidebar.tsx           — Tabbed sidebar (Profile + Research Idea)
├── state/
│   └── appReducer.ts         — Central reducer (11 action types)
├── map/
│   ├── d3MapController.ts    — Core D3 visualization (~574 lines)
│   └── colorScale.ts         — Spectral colormap for clusters
├── lib/
│   ├── loadScholars.ts       — Fetch + normalize scholar data
│   ├── appMode.ts            — Full vs embedded mode detection
│   ├── scholarMedia.ts       — Profile pic URL resolution
│   └── cx.ts                 — Classname utility
├── hooks/
│   └── useClickOutside.ts    — Click-outside detection hook
├── types/
│   └── scholar.ts            — Scholar, RawScholar, Paper, Education, SubfieldTag, ResearchIdea
└── styles/
    ├── tokens.css            — Design tokens (colors, fonts, radii, shadows, borders)
    └── app.css               — All component styles (~846 lines)
```

## Key Patterns

**State management:** Single `useReducer` in App.tsx with 13 action types (discriminated union). No external state library. Derived state (visible scholars, institution counts, subfield counts) computed inline.

**Nonce pattern:** `resetNonce` and `panRequest.nonce` are incrementing counters that trigger D3 animations via useEffect dependencies. This allows re-triggering the same action (e.g., pan to same scholar twice).

**Click-outside:** Shared `useClickOutside` hook used by SearchPanel and FilterPanel.

**Subfield filter:** `activeSubfields: string[]` in state, set by `subfields_filter_applied` / `subfields_filter_cleared` actions. FilterPanel has two tabs (Institution | Subfield). Clicking a subfield badge in the sidebar dispatches `subfields_filter_applied` with that single subfield. D3 visibility is the AND of both filters via `isScholarVisible()` helper in `d3MapController.ts`.

**Class names:** `cx()` utility for conditional class composition.

**Image fallback:** ScholarAvatar tries profile pic → default avatar → initials display.

**Data normalization:** `loadScholars.ts` converts snake_case JSON keys to camelCase TypeScript fields, filters invalid entries, and normalizes `"nan"`/`"null"` strings to `undefined`.

## Styling

No CSS framework — vanilla CSS with design tokens.

**Token categories** (in `tokens.css`):
- `--font-sans/mono` — Manrope + IBM Plex Mono
- `--bg-*`, `--ink-*` — background and text colors
- `--brand-0/1/2`, `--accent` — teal brand palette + gold + red accent
- `--panel/panel-strong`, `--card-bg/card-bg-strong` — surface backgrounds
- `--border-subtle/light/medium`, `--brand-tint/brand-border` — borders
- `--shadow-1/2`, `--radius-sm/md/lg` — elevation and rounding

**Visual design:** Warm neutral background (`#faf8f5`) with teal brand accents. Glassmorphism panels (backdrop-filter blur). Dot grid pattern on map. Spectral colormap for cluster dots.

**Responsive breakpoints:** 1100px (stacked layout), 700px (mobile adjustments).

## Dependencies

3 production dependencies: `react` + `react-dom` 19.x, `d3` 7.x

Dev: TypeScript ~5.9, Vite 7.3, ESLint 9.x, Playwright 1.58

## Embedded Mode

For offline demos without a backend:

```bash
npm run generate:embedded-data   # samples 100 scholars → public/embedded-scholars.json
# Then visit http://localhost:5173/?mode=embedded
```
