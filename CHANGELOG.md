# Changelog

## Next release (in progress, 2026-09-25)

### Pipeline
- **Gemini 3.8 Flash**: all Flash calls (paper/profile grounded search, bio normalization,
  PI classification, dedup, discovery, subfield classification) now use `gemini-3.8-flash`
  via a single `FLASH_MODEL` constant in `scholar_board/gemini.py`. Pro-model steps
  (directions, field directions) remain on `gemini-3.1-pro-preview`.
- **Removed the AI Research Ideas feature**: the `ideas` pipeline step, its prompt, the
  `ideas` DB table, and the `suggested_idea` field in `scholars.json` / frontend types.
  (The sidebar tab itself had already been removed.) Pipeline is now 12 steps.
- **Paper selection rules** (`fetch_papers`): papers from **January 2023 onward**, the PI
  must be **first or last author**, published versions preferred but full preprints allowed,
  and conference abstracts indexed by Google Scholar (VSS / JOV meeting supplements, CCN,
  COSYNE, SfN, OHBM) excluded. Rules are stated in the prompt *and* enforced in code
  (`filter_papers`), which also records each paper's `author_position`.
- `fetch_papers --fewer-than N`: re-fetch only scholars with fewer than N saved papers.
  Used to top up the 137 thin profiles (< 3 papers) rather than re-fetching everyone.
- `pics`: every candidate photo is checked by Gemini (single-person headshot, not a
  campus/group shot) and rejected if another scholar already uses the identical image;
  `--ids` replaces specific photos; failed searches fall back to the default avatar.
- `build`: profile photos for `E`-prefixed scholar IDs are now picked up.
- `subfields`: manual overrides in `data/source/subfield_overrides.json` are applied on top
  of the classifier, so hand fixes survive re-runs.

### Data
- Topped up the 134 PIs that had fewer than 3 papers (120 via Gemini 3.8 Flash, 14 via
  Claude web-search agents after repeated Vertex 429s); new papers were merged with the
  old ones so no valid paper was lost. PIs with < 3 papers: 137 → 37.
- Regenerated research directions for those PIs, re-embedded and re-projected (UMAP) all
  793 PIs, re-classified all 793 with Gemini 3.8 Flash (Theory & Computation catch-all
  152 → 105 primaries), and regenerated all 21 field-direction summaries.
- Replaced 38 stock/campus photos that were shared across multiple scholars.
- Removed 9 non-vision researchers from the map (`is_pi = 0`, kept in DB):
  Adam Green, Hamid Soltanian-Zadeh, Joseph Pare, Mette Elmose Andersen, Molly Jameson,
  Myeong-Ho Sohn, Vijay Mittal, Wataru Inoue, Keiko Tsuchiya. Map now has 792 PIs.
- Removed Daniel Baker (University of York) from the map (`is_pi = 0`, kept in DB) and
  deleted his profile photo. Map now has 791 PIs.
- Removed Uri Hasson from the map (`is_pi = 0`, kept in DB) and deleted his profile photo.
  Map now has 790 PIs.
- Emily A. Cooper moved from UC Berkeley to Dartmouth College: institution, department and
  bio updated (private contact email updated too).
- Ward van der Tempel relabelled Eye Movements (was 3D Perception) via the new
  `data/source/subfield_overrides.json`.
- Fixed name typo "Grabriel Kreiman" → "Gabriel Kreiman".
- Back-ported earlier manual corrections (names, institutions, lab URLs, de-duplicated paper
  lists) from `scholars.json` into the DB, so rebuilds no longer revert them.
- Duplicate-profile audit: no remaining duplicates among the shipped PIs.

### Frontend
- List view is now the default; the logo returns to it.
- The single "Filters" dropdown is split into **Institution** and **Field** buttons. Ticking a
  box filters immediately (no Apply step); Escape or clicking outside closes the menu.
- On phones the search box gets its own row, with the filter buttons below it.
- The profile close button is now a small round button in the card's corner.
- Thinner, lower-contrast scrollbars throughout.
- New creator headshot in the top-left header avatar.
- Phone polish: list rows show the institution under the name (long field badges truncate),
  the empty profile panel is hidden until a scholar is picked, the map hint says
  "Pinch to zoom · Drag to pan · Tap a dot" on touch screens, and header/filter buttons are
  larger tap targets.
