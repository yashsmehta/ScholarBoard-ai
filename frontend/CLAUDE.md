# Frontend — CLAUDE.md

React + TypeScript + Vite rewrite of the static `website/` dashboard. Same functionality and aesthetics, component-based architecture.

## Quick Start

```bash
# Install dependencies
npm install

# Dev server (requires Python backend on :8000 for data)
npm run dev          # → http://localhost:5173

# Type-check + production build
npm run build        # → dist/

# Lint
npm run lint
```

Vite proxies `/api`, `/data`, `/images` to `http://localhost:8000` (the Python server in `website/`).

## Architecture

**React owns UI state. D3 owns SVG rendering.** They communicate through a controller interface.

```
App.tsx (useReducer)
 ├── Header             — title bar, scholar count
 ├── SearchPanel        — live search with keyboard nav
 ├── FilterPanel        — institution filter dropdown
 ├── ScholarMap          — thin React wrapper around D3
 │   └── d3MapController — imperative D3 scatter plot (zoom, pan, brush, tooltips)
 ├── MapControls        — reset button, usage hint
 └── Sidebar            — scholar profile, papers, nearby scholars
```

### Data Flow

1. `App.tsx` loads scholars via `loadScholars()` (fallback chain: env URL → `/api/scholars` → `/data/scholars.json`)
2. Raw JSON normalized to `Scholar[]` (snake_case → camelCase, validates required fields)
3. State managed by `appReducer` (useReducer) — selection, hover, search, filters
4. `ScholarMap` passes scholars + interaction state to `d3MapController`
5. D3 emits hover/select callbacks → React updates state → pushes back to D3

### D3 Integration Pattern

`d3MapController.ts` is an imperative "island" — a closure that creates/manages the SVG. React never touches the SVG directly.

**Controller API:**
- `setData(scholars)` — update dots
- `setInteractionState({hoveredId, selectedId, activeInstitutions})` — sync visual state
- `resize()` — refit scales to container
- `resetView()` / `panToScholar(id)` — animated transitions
- `destroy()` — cleanup

**Dot layers:** Visual dots (no pointer events, styled) + invisible hit dots (larger radius for touch/click targets). Selection ring is a separate SVG circle.

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
│   └── Sidebar.tsx           — Scholar profile card, papers, nearby scholars
├── state/
│   └── appReducer.ts         — Central reducer (11 action types)
├── map/
│   ├── d3MapController.ts    — Core D3 visualization (~575 lines)
│   └── colorScale.ts         — Spectral colormap for clusters
├── lib/
│   ├── loadScholars.ts       — Fetch + normalize scholar data
│   ├── appMode.ts            — Full vs embedded mode detection
│   ├── scholarMedia.ts       — Profile pic URL resolution
│   └── cx.ts                 — Classname utility
├── hooks/
│   └── useClickOutside.ts    — Click-outside detection hook
├── types/
│   └── scholar.ts            — Scholar, RawScholar, Paper, Education types
└── styles/
    ├── tokens.css            — Design tokens (colors, fonts, radii, shadows, borders)
    └── app.css               — All component styles (~777 lines)
```

## Key Patterns

**State management:** Single `useReducer` in App.tsx. No external state library. Actions are a discriminated union (`AppAction`). Derived state (visible scholars, institution counts) computed inline.

**Nonce pattern:** `resetNonce` and `panRequest.nonce` are incrementing counters that trigger D3 animations via useEffect dependencies. This allows re-triggering the same action (e.g., pan to same scholar twice).

**Click-outside:** Shared `useClickOutside` hook used by SearchPanel and FilterPanel.

**Class names:** `cx()` utility for conditional class composition (replaces verbose filter/join pattern).

**Image fallback:** ScholarAvatar tries profile pic → default avatar → initials display.

## Styling

No CSS framework — vanilla CSS with design tokens.

**Token categories** (in `tokens.css`):
- `--font-sans/mono` — Manrope + IBM Plex Mono
- `--bg-*`, `--ink-*` — background and text colors
- `--brand-*` — teal brand palette
- `--border-subtle/light/medium` — border opacities
- `--card-bg/card-bg-strong` — card backgrounds
- `--panel/panel-strong` — glass panel backgrounds
- `--shadow-1/2`, `--radius-sm/md/lg`

**Visual design:** Warm neutral background with teal brand accents. Glassmorphism panels (backdrop-filter blur). Dot grid pattern on map. Spectral colormap for cluster dots.

**Responsive breakpoints:** 1100px (stacked layout), 700px (mobile adjustments).

## Dependencies

Only 3 production dependencies:
- `react` + `react-dom` 19.x
- `d3` 7.x

## Embedded Mode

For offline demos without a backend:

```bash
npm run generate:embedded-data   # samples 100 scholars → public/embedded-scholars.json
# Then visit http://localhost:5173/?mode=embedded
```
