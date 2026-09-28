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
- Kirsten Adam moved from Rice University to UC Davis (Psychology + Center for Mind and
  Brain): institution, department, bio and lab link updated (Rice lab site is gone).
  Private contact emails updated for her and Kenneth D. Miller, at their request.
- Lili Sahakyan (at her request): lab link → cmflab.pages.dev, lab renamed "Control of
  Memory & Forgetting Lab", AI summary rewritten to follow the new lab site; map position
  unchanged.
- Daniel D. Dilks (at his request): AI summary replaced with his own revised text; map
  position unchanged.
- Giovanni Federico (at his request): bio replaced with his own text, department set to
  "Department of Education, Psychology and Communication", lab name removed. Research
  direction trimmed (dropped a stray veterinary-neurology sentence) and main research area
  set to "cognitive neuroscience of technology". Removed an off-topic paper (anti-NGF therapy
  in dogs) from his list.
- Carlos Ponce (at his request): research summary replaced with his lab's own text, main
  research area set to "visual information processing", and retagged Theory & Computation
  (+ Motion, Eye Movements) instead of Object Recognition via `subfield_overrides.json`.
  His bioRxiv "Object Manifold Alignment" preprint swapped for the published Nature
  Neuroscience 2026 version (checked against his ORCID record). Lab link fixed to ponce.hms.harvard.edu.
  Bio rewritten to match the lab's summary; the ICLR/OpenReview "Functional segregation"
  preprint (not on his ORCID) replaced by PNAS 2023 "Macaques recognize features in synthetic
  images derived from ventral stream neurons".
- Added Binxu Wang (Kempner Institute, Harvard; E367). Papers hand-picked from her Google
  Scholar/lab site (2025+, first or second author, preprints included) and a hand-written AI
  summary; placed on the map with the saved UMAP model so no other positions moved. Map now
  has 791 PIs.
- Added Bria Long (UC San Diego, Visual Learning Lab; E368). Papers hand-picked from her site
  (2023+, first or last author, preprints included; CCN abstracts and workshop papers skipped)
  and a hand-written AI summary; placed on the map with the saved UMAP model, next to the
  developmental cluster (Linda Smith, Lisa Oakes, Richard Aslin). Map now has 792 PIs.
- Added Carsen Stringer (HHMI Janelia, Pachitariu + Stringer Lab; E369). Papers hand-picked
  from mouseland.github.io (2023+, first or last author, published versions only); bio and AI
  summary written from the lab site; placed with the saved UMAP model, next to Matteo
  Carandini, Kenneth Harris and Andreas Tolias. Map now has 793 PIs.
- Kohitij Kar (at his request): papers updated to published versions. Hierarchical
  optimization and facial expression preprints swapped for their Nature Communications 2026
  versions; added Reverse predictivity (Nature Machine Intelligence 2026) and MAPS
  (Communications Psychology 2026) in place of the scene-context and memorability preprints.
  AI summary rewritten around the published papers.
- Elizabeth Spelke (at her request): social-cognition work now attributed to Ashley Thomas;
  the two infant social-evaluation papers dropped and her AI summary refocused on core knowledge,
  the open cognitive assessment battery for children in low- and middle-income countries (Open
  Mind 2026) and randomized evaluations of classroom math games (PsyArXiv 2026). Social
  Perception tag removed via `subfield_overrides.json`.
- Added Ashley J. Thomas (Harvard, Thomas Lab; E370) and Moira R. Dillon (NYU, Lab for the
  Developing Mind; E371), suggested by Elizabeth Spelke. Papers hand-picked (2023+, first or
  last author, published versions), bios and AI summaries written from their lab sites,
  headshots from their own pages; placed with the saved UMAP model in the developmental
  cluster next to Spelke. Map now has 795 PIs.
- New `data/source/pi_overrides.json`: manual PI decisions that win over the `profiles`
  classifier (it had rejected Binxu Wang as a postdoc).
- Michael Bonner: AI summary (research direction) rewritten to follow the Bonner Lab
  website (bonnerlab.org), map position unchanged; new profile photo.
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
