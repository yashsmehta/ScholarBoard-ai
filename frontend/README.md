# ScholarBoard React Frontend (Migration Scaffold)

This folder is a parallel frontend scaffold for migrating the current D3-based static UI in `website/` to:

- React
- Vite
- TypeScript
- D3 (retained for map rendering and interactions)

For a technical structure/architecture walkthrough, see `ARCHITECTURE.md`.

## Current Status

- Existing implementation remains in `../website/` (untouched).
- This app provides a typed shell, data loader, sidebar/search/filter components, and an initial D3 map controller.
- Full parity is tracked in `MIGRATION_PLAN.md`.

## Development

1. Start the existing Python server (recommended for data/API proxy):

```bash
cd website
python serve.py
```

2. In a second terminal, run the React frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api`, `/data`, and `/images` to `http://localhost:8000`.

## Data Sources

The loader tries sources in this order:

1. `VITE_SCHOLARS_URL` (if set)
2. `/api/scholars`
3. `/data/scholars.json`

You can override the source by creating `frontend/.env.local`:

```bash
VITE_SCHOLARS_URL=http://localhost:8000/api/scholars
```

## Embedded Mode (Replaces `embedded-index.html` Pattern)

Use a React mode switch instead of monkey-patching `window.fetch` in HTML.

- Query param: `?mode=embedded`
- Env flag: `VITE_FRONTEND_MODE=embedded`

Embedded mode prefers a static file at `/embedded-scholars.json` (generated in `frontend/public/`) for backend-free demos.
If that file is missing, it falls back to the normal source pipeline and samples the first `N` scholars (default `100`, configurable with `VITE_EMBEDDED_SAMPLE_SIZE`).

Regenerate the static embedded dataset:

```bash
cd frontend
npm run generate:embedded-data
```

## Migration Principle

React owns UI composition and app state. D3 owns the SVG rendering and interaction internals of the map.
