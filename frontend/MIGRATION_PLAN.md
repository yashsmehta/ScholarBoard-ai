# ScholarBoard Frontend Migration Plan

This plan migrates the current `website/` frontend to `React + Vite + TypeScript` while retaining D3 for the map.

## Goals

- Preserve all current user-facing functionality
- Improve maintainability and UI consistency
- Enable faster feature iteration
- Keep the D3 interaction layer (zoom/pan/brush) for performance and control

## Non-Goals (Initial Migration)

- Rebuilding the Python data pipeline
- Replacing D3 with React-only SVG rendering
- Redesigning every visual detail before parity is reached

## Milestones

### M1: Scaffold + Typed Data Path (Current)

- Vite React TypeScript app in `frontend/`
- D3 dependency installed
- Typed scholar models and normalization
- Data loader with source fallback (`/api/scholars`, `/data/scholars.json`)
- Initial app shell (header, overlays, sidebar, controls)
- Initial D3 map controller (render dots, zoom/pan, selection/hover sync)

### M2: Core Map Interaction Parity

- Tooltip parity (positioning, boundary clamping)
- Double-click zoom parity
- Selection ring parity animation/style
- Reset view parity behavior
- Responsive resize parity

### M3: Search and Filter Parity

- Search dropdown parity (keyboard navigation, active option behavior)
- Highlight matched substrings
- Click-outside close behavior
- Filter dropdown parity (draft selection + apply/clear)
- Dot dimming + pointer-events behavior parity

### M4: Sidebar and Details Parity

- Sidebar profile layout parity
- Bio, education, papers, and links rendering
- "Similar Researchers" list parity
- Click nearby scholar to pan/select
- Fallback avatar behavior parity

### M5: D3 Advanced Interaction Parity + Cleanup

- Shift+drag box zoom (`d3.brush`) parity
- Keyboard modifier state and visual cues
- Interaction edge cases (blur, escape)
- Replace embedded demo mode `window.fetch` monkey-patch with a typed mode switch
- Integrate Vite build output with `website/serve.py`

## Feature Parity Checklist

- [x] Load and normalize scholars from existing JSON
- [x] Render clustered dots using D3
- [x] Hover highlight
- [x] Click select
- [x] Sidebar open/close (basic)
- [x] Search by scholar name (basic)
- [x] Search keyboard navigation (basic)
- [x] Institution filter apply/clear (basic)
- [x] Dot dimming for filtered-out scholars
- [x] Reset view
- [x] Double-click zoom
- [x] Tooltip parity (D3 controller tooltip)
- [x] Nearby scholars pan-to-scholar map motion parity (basic animated pan)
- [x] Shift+drag box zoom
- [x] Embedded mode replacement (`?mode=embedded` / env flag)
- [x] Full sidebar content parity (images/fallback avatar behavior)

## Architecture Rules

- React owns app state, layout, and non-map UI rendering.
- D3 owns map SVG nodes, transforms, scales, and brush/zoom internals.
- Do not let React and D3 both mutate the same SVG elements.
- Keep scholar data normalized at the loader boundary.
