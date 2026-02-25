# ScholarBoard Frontend Architecture (React + Vite + TypeScript + D3)

This document explains the new `frontend/` application for engineers who are comfortable with modern frontend systems but are new to ScholarBoard.

## Purpose

`frontend/` is the new UI shell for ScholarBoard that:

- uses `React` for layout, UI composition, and app state
- uses `TypeScript` for typed data + state contracts
- uses `Vite` for dev/build tooling
- keeps `D3` for map rendering and interactions (zoom/pan/brush/transforms)

The legacy implementation remains in `/Users/mehtay/Research/scienta-ai/ScholarBoard-ai/website/`.

## Design Principle (Most Important Rule)

React and D3 are intentionally split by ownership:

- React owns: app state, sidebar, search, filters, controls, loading/error UI
- D3 owns: SVG nodes, scales, transforms, zoom/brush behavior, tooltip positioning, map hit-testing

Do not let React render or mutate the same SVG nodes that D3 controls.

## Runtime Overview

1. `App` detects mode (`full` or `embedded`)
2. `App` loads scholar data through a typed normalization layer
3. `App` stores state in a reducer (`appReducer`)
4. `ScholarMap` creates a single long-lived D3 controller instance
5. React pushes data + interaction state into the controller
6. D3 emits hover/select callbacks back to React
7. React updates sidebar/search/filter UI and can issue imperative map commands (reset/pan)

## Directory Map

```text
frontend/
  src/
    App.tsx                     # App composition + reducer wiring
    main.tsx                    # React entrypoint
    components/
      Header.tsx                # Top bar / mode badge
      SearchPanel.tsx           # Search input + dropdown + keyboard nav
      FilterPanel.tsx           # Institution filter menu (draft/apply/clear)
      MapControls.tsx           # Reset button + usage hint overlays
      ScholarMap.tsx            # React wrapper around D3 controller (imperative island)
      Sidebar.tsx               # Scholar profile + papers + education + nearby list
    state/
      appReducer.ts             # AppState + actions + reducer transitions
    map/
      d3MapController.ts        # D3 rendering + interactions (core map engine)
      colorScale.ts             # Cluster color mapping
    lib/
      loadScholars.ts           # Source fallback + payload normalization
      appMode.ts                # mode detection (?mode=embedded / env)
      scholarMedia.ts           # avatar URL/fallback logic
    types/
      scholar.ts                # RawScholar / Scholar typed contracts
    styles/
      tokens.css                # design tokens
      app.css                   # layout + component + map styles
  public/
    embedded-scholars.json      # backend-free demo dataset
  scripts/
    generate-embedded-data.mjs  # static embedded dataset generator
```

## App State Model (`src/state/appReducer.ts`)

Central reducer state:

- `status`: `idle | loading | ready | error`
- `scholars`: normalized dataset (`Scholar[]`)
- `sourceLabel`: human-readable source used by loader
- `errorMessage`: load failure message
- `selectedScholarId`: current sidebar/map selection
- `hoveredScholarId`: hover state for map styling
- `searchQuery`: controlled input value
- `activeInstitutions`: applied filter list
- `sidebarOpen`: sidebar visibility
- `resetNonce`: increment-trigger for imperative map reset
- `panRequest`: `{ scholarId, nonce }` trigger for imperative map pan/select sync

Reducer actions are UI-oriented and explicit (`scholar_selected`, `filters_applied`, `pan_to_scholar_requested`, etc.), which keeps side effects in components instead of inside the reducer.

## Data Loading and Normalization (`src/lib/loadScholars.ts`)

### Source Resolution

Default source precedence:

1. `VITE_SCHOLARS_URL` (if set)
2. `/api/scholars`
3. `/data/scholars.json`

Embedded mode source precedence:

1. `/embedded-scholars.json`
2. then the same default source chain above

### Embedded Mode Behavior

- mode is selected via `?mode=embedded` or `VITE_FRONTEND_MODE=embedded`
- if `/embedded-scholars.json` is missing, loader falls back to live sources and samples the first `N` scholars (`VITE_EMBEDDED_SAMPLE_SIZE`, default `100`)

### Normalization Guarantees

`loadScholars()` converts heterogeneous legacy payloads into `Scholar[]`:

- accepts both array payloads and object maps (`Record<string, RawScholar>`)
- drops invalid rows (missing `name` or UMAP coordinates)
- normalizes `"nan"` / `"null"` strings to `undefined`
- maps raw fields to typed frontend fields (e.g. `profile_pic -> profilePic`, `research_areas -> researchAreas`)

This keeps the rest of the UI free of ad-hoc data cleanup.

## React Shell (`src/App.tsx`)

`App.tsx` is the composition root. It is responsible for:

- mode detection (`detectFrontendMode()`)
- async data loading + error handling
- deriving:
  - `visibleScholars` (institution-filtered search pool)
  - `selectedScholar`
  - institution counts for filter UI
- wiring component callbacks to reducer actions
- issuing map commands indirectly via `resetNonce` / `panRequest`

Important behavior:

- Search selections pan to the scholar (`selectScholar(..., { pan: true })`)
- Dot clicks select without forced pan (current map position preserved)
- Sidebar "Similar Researchers" selects + pans

## D3 Integration Pattern (`src/components/ScholarMap.tsx`)

`ScholarMap.tsx` is a thin React wrapper around an imperative D3 controller.

Key implementation details:

- creates the D3 controller once (`useEffect(..., [])`)
- stores controller instance in a `ref`
- uses callback refs (`hoverHandlerRef`, `selectHandlerRef`) so the D3 controller stays mounted while React callbacks remain fresh
- pushes updates incrementally:
  - `setData(scholars)`
  - `setInteractionState(...)`
  - `resetView()` on `resetNonce`
  - `panToScholar()` on `panRequest.nonce`
- uses `ResizeObserver` to call `controller.resize()`

This avoids the previous bug class where recreating the D3 controller on hover/selection caused broken interactions.

## D3 Map Controller (`src/map/d3MapController.ts`)

This is the core interaction engine. It manages:

- SVG creation
- scale computation from UMAP coordinates
- dot rendering
- hit targets for reliable pointer/mouse selection
- hover + selection styling
- tooltip rendering/positioning
- zoom/pan (`d3.zoom`)
- box zoom (`d3.brush` with `Shift` modifier mode)
- imperative commands (`resetView`, `panToScholar`)

### Internal Layers

The controller creates multiple SVG groups:

- `ringLayer`: selection ring (visual emphasis)
- `dotLayer`: visible scholar dots
- `hitLayer`: invisible, larger click/hover targets (interaction reliability)
- `brushLayer`: rectangle selection overlay for box zoom

The visible dots and hit targets are separate on purpose:

- visible dots stay small and aesthetically correct
- hit targets improve click reliability, especially in Chrome

### Interaction Model

#### Zoom / Pan

- uses `d3.zoom()`
- scroll wheel zoom enabled
- drag pan enabled unless box-zoom modifier is active
- custom double-click zoom (`dblclick.zoom` disabled, custom handler installed)

#### Box Zoom (`Shift+drag`)

- enabled only while `Shift` is held (`boxZoomModifierActive`)
- implemented with `d3.brush()`
- brush key modifiers are disabled (`.keyModifiers(false)`) so D3 does not reinterpret `Shift`
- brush layer is hidden and pointer-disabled unless active

#### Selection / Hover

- D3 emits `onHoverScholarId` and `onSelectScholarId` callbacks
- React stores selection/hover state and re-sends it back for styling
- selection ring is updated from React-controlled `selectedScholarId`

#### Cross-Browser Click Reliability (Chrome)

The controller uses multiple safeguards because browser event behavior differed (Safari vs Chrome):

- pointer event path (`pointerdown` / `pointerup`)
- mouse event fallback path (`mousedown` / `mouseup`)
- SVG-level fallback hit-testing for near-clicks
- deduped selection commits (`commitSelection`) to avoid duplicate selects from overlapping paths

This preserves reliable selection without requiring the user to “click perfectly”.

#### Cursor Behavior (Visible Dot vs Hit Halo)

Hit targets are larger than visible dots, but cursor behavior is intentionally based on visible-dot geometry:

- `pointer` only when the pointer is over the visible dot radius region
- `grab` on map background
- `crosshair` in box-zoom mode

This avoids cursor flicker / misleading “clickable” cursor over the invisible hit halo.

## UI Components

### `SearchPanel.tsx`

- controlled input (`query`)
- deferred filtering (`useDeferredValue`) to reduce input lag
- min query length = 2
- max results = 10
- keyboard navigation:
  - `ArrowUp/ArrowDown`
  - `Enter` select
  - `Escape` close
- click-outside close behavior
- selecting a result updates query to the scholar name and triggers map pan+select via `App`

### `FilterPanel.tsx`

- institution filter menu with local `draft` state
- applied filters are separate from draft selections
- explicit `Apply` / `Clear All`
- click-outside close behavior
- scaffold currently renders top `80` institutions (not full search UI yet)

### `Sidebar.tsx`

- renders selected scholar profile
- sections:
  - profile meta
  - bio
  - research areas
  - recent papers
  - education
  - similar researchers
- “Similar Researchers” computed client-side by Euclidean distance in UMAP space
- clicking a nearby scholar calls `onSelectNearby` (select + animated map pan)
- avatar behavior includes image URL, default avatar fallback, and initials fallback

### `MapControls.tsx`

- reset view button
- interaction hint overlay

## Styling System (`src/styles`)

- `tokens.css`: color/spacing/radius/shadow/type tokens
- `app.css`: layout + component styling + map-specific styling

Important implementation detail:

- map overlays use `pointer-events: none` at the wrapper level and re-enable pointer events only on interactive child controls
- status strip is non-interactive
- this prevents overlays from intercepting map clicks

## Dev / Build / Demo Modes

### Local Development

```bash
cd /Users/mehtay/Research/scienta-ai/ScholarBoard-ai/frontend
npm install
npm run dev
```

Vite dev server runs on `5173` (unless overridden).

### Full Mode

- default mode
- expects backend/API or static data route available (`/api/scholars` or `/data/scholars.json`)
- Vite config proxies `/api`, `/data`, `/images` to the Python server (typically `website/serve.py`)

### Embedded Mode (Shareable Demo)

```text
http://127.0.0.1:5173/?mode=embedded
```

- uses `/embedded-scholars.json` when present
- works without the backend

Regenerate embedded dataset:

```bash
cd /Users/mehtay/Research/scienta-ai/ScholarBoard-ai/frontend
npm run generate:embedded-data
```

## Extension Guidelines (How To Change This Safely)

### Add new sidebar/search/filter UI behavior

- prefer changes in React components + reducer actions
- keep D3 unaware of non-map UI details

### Add new map interaction behavior

- implement in `d3MapController.ts`
- expose only a small callback or imperative method to React
- avoid reading React component state directly from D3

### Add new data fields

1. extend `RawScholar` / `Scholar` in `src/types/scholar.ts`
2. normalize in `src/lib/loadScholars.ts`
3. consume in UI components

### Avoid These Regressions

- recreating the D3 controller on every React render
- making overlays intercept pointer events over the map
- letting React render individual SVG dots while D3 also mutates them
- reintroducing browser-specific click assumptions (pointer-only paths)

## Current Scope / Known Gaps

This frontend is a migration scaffold with major parity already in place, but still not a final polished replacement. Known scope limitations include:

- filter UI is intentionally simplified (top 80 institutions, no institution search yet)
- some visual details may still differ from `/website/`
- advanced UX polish can continue after parity stabilization

## Related Docs

- `/Users/mehtay/Research/scienta-ai/ScholarBoard-ai/frontend/README.md` (setup + quick usage)
- `/Users/mehtay/Research/scienta-ai/ScholarBoard-ai/frontend/MIGRATION_PLAN.md` (milestones and parity tracking)

