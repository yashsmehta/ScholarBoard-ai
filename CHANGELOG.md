# Changelog

## Next release (in progress, 2026-09-25)

### Pipeline
- **Similar Researchers now ranked by embedding similarity**: `build` adds a `similar` field to
  every PI in `scholars.json` (top 10 `{id, score}` by cosine similarity of the full 3072-d
  embeddings, PIs only, self excluded). The sidebar shows the first 5 (falling back to
  2D map distance if the field is missing); scores are not shown yet. Methodology text updated.
- **New private `sex` field** (`scholar_board/pipeline/sex.py`, run on demand, not a map step):
  Gemini 3.8 Flash estimates each PI's sex from bio pronouns or first name (female / male /
  unknown). Stored only in the DB (`scholars.sex`) and `data/pipeline/scholar_sex.json`, and
  never shipped to the frontend. Hand fixes go in the untracked `data/source/sex_overrides.json`.
  `--stats` prints aggregate counts. `--resolve-unknown` looks up PIs the name-based pass left
  "unknown" with grounded search for explicit pronouns (Gemini gateway: `generate_text` gains
  `grounded=True`). First run: 71 unknown by name, reduced to 4 by the search, leaving
  247 female / 546 male / 4 unknown of 797 PIs (31% female among known).
- **New `countries` step**: Gemini 3.8 Flash maps each distinct PI institution to its country
  → `data/source/institution_countries.json` (tracked; 329 institutions, 35 countries,
  reviewed by hand and cross-checked against the ROR registry). `build` adds a `country` field to every scholar. Pipeline is now 13 steps.
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
- Removed Hannah Block and Hermann Bulf from the map (`is_pi = 0` via
  `data/source/pi_overrides.json`, kept in DB) and deleted their profile photos.
  Map now has 793 PIs.
- Gi-Yeul Bae: bio title Assistant → Associate Professor; private contact email updated.
- Fuat Balci (at his request): institution Koc University → University of Manitoba
  (country Canada); bio, lab link and email already pointed to Manitoba.
- Added S. P. Arun (Indian Institute of Science, Centre for Neuroscience, Visionlab@IISc; E372),
  the first PI in India. Papers hand-picked from the lab's publications page (2024+, last
  author; two 2026 preprints), bio and AI summary written from the lab site; placed with the
  saved UMAP model next to Frank Tong, Michelle Greene and Katharina Dobs. Search aliases
  "SP Arun" / "Sripati Arun".
- Added four more India-based PIs, same process (papers 2023+, first or last author; bios and
  AI summaries from their lab pages; placed with the saved UMAP model):
  - Aditya Murthy (IISc Centre for Neuroscience, Movement Control Lab; E373), next to
    Daniel Wolpert and Samuel McDougle.
  - Rajiv Soundararajan (IISc Electrical Communication Engineering; E374), perceptual image
    and video quality, next to Laurent Itti and Krista Ehinger.
  - Richa Verma (IIT Madras, Sudha Gopalakrishnan Brain Centre; E375), fetal human brain
    neuroanatomy, next to Lynne Kiorpes and Takao Hensch. Four qualifying papers; no Google
    Scholar stats (the stats step matched a different Richa Verma, cleared).
  - Sridharan Devarajan (IISc Centre for Neuroscience, Cognition Lab; E376), next to Anna
    Nobre and Freek van Ede; search alias "Devarajan Sridharan" (the order he publishes under).
  Official faculty photos used for Murthy (image search had the wrong person) and Sridharan.
  Map now has 798 PIs.
- Maryam Vaziri-Pashkam (at her request): papers replaced with her own picks — J Cogn
  Neurosci 2024, eLife 2024, J Neurosci 2023, Cerebral Cortex 2023, and the in-press Journal
  of Vision inversion-effect paper (linked to its preprint). AI summary replaced with her own
  revised text.
- Removed Frans Verstraten from the map (`is_pi = 0` via `pi_overrides.json`, kept in DB) and
  deleted the profile photo. Map now has 797 PIs.
- Nancy Kanwisher: AI summary rewritten in plain language, opening with the lab's framing
  and FFA/PPA/EBA before the 2025 work (physics engine, things vs stuff, language); bio
  pronoun fixed; lab link → web.mit.edu/bcs/nklab (old one was dead). Re-placed on the map
  from the new text.
- Re-placed 12 PIs whose AI summary or papers were edited after the Sep 25 map fit
  (Anderson, Ponce, Baker, Dilks, Sperling, Federico, Kar, Mudrik, Sahakyan,
  Vaziri-Pashkam, Bonner, Spelke): re-embedded from their current summary + papers and
  projected with the saved UMAP model, so every other dot stays put.
- Re-placed 38 PIs whose AI summary or papers were edited since the last map fit
  (Schütz, Facoetti, Hierlemann, Afraz, van Kemenade, Duchaine, Olman, Brainard, Merriam, Wiese, Oruc, Bisley, Steeves, Wilmer, Dobs, Bijanki, Trick, Pisella, Rutherford, Hebart, Greene, Rosenberg, Haefner, Starrfelt, Adamo, Manassi, Tadin, Cottereau, Smeets, Crawford, Bays, Ma, Solomon, Green, Ahissar, Angelucci, Feller, Staub): re-embedded from their current summary + papers and projected with the saved
  UMAP model, so every other dot stays put. Biggest moves: Bisley, Oruc, Ma, Trick, Solomon.
- Giovanni Federico: his own text now also replaces the AI summary (the sidebar shows only
  the summary, not the bio), lightly reworded to the site's "Dr. Federico studies…" style.
- Liad Mudrik (on request): AI summary replaced with the text Dr. Mudrik sent, adding theory testing,
  the neural correlates of consciousness and a meta-science database of how theories have
  been tested. Map position unchanged.
- George Sperling (on request): AI summary rewritten to lead with his lab's new
  psychophysical methods for measuring the parvocellular and magnocellular pathways (retina to
  LGN); bio and summary use "he/his lab". Map position unchanged.
- Jeroen Smeets (on request): last sentence of the AI summary replaced with his wording
  (multisensory signals and expectations in the size-weight illusion and motion sickness);
  the 2025 Perception length-judgement paper swapped for Reuten et al. (2024), "Anticipatory
  cues can mitigate car sickness on the road" (Transp Res F). Map position unchanged.
- Ipek Oruc (on request): AI summary replaced with the lab profile Dr. Oruc sent (face and
  object perception, naturalistic vision, AI for ophthalmic imaging); bio pronouns → she/her.
  Map position unchanged.
- Joshua A. Solomon (listed as "John A. Solomon", now fixed in DB and `extra_researchers.csv`):
  dropped the 2024 JoV author response, which an alumnus wrote after leaving the lab. Added three
  2024–26 first/last-author papers found via OpenAlex (numerosity adaptation, Vision Res 2026;
  plaid search asymmetry, Perception 2025; spatial summation for motion, Vision Res 2024).
  AI summary and the last sentence of the bio rewritten from these papers. Map position unchanged.
- Benoit Cottereau (on request): AI summary replaced with the text Dr. Cottereau sent (motion and
  spatial vision, adaptation to central vision loss in macular degeneration, spiking neural
  networks for event-based cameras); bio pronoun → his. Map position unchanged.
- Andreas Hierlemann (on request): AI summary replaced with his edited version, framed around
  the group (HD-MEAs, organ-on-a-chip, E/I balance in cortical circuits, conduction speeds in
  human retinal axons). Map position unchanged.
- Katharina Dobs (on request): dropped the 2024 proprioception highlight article, which the AI had
  summarized as the lab's own research. Added the faces-and-bodies integration preprint
  (bioRxiv 2026) and linked the published version of the feature-tuning paper
  (J Neurosci 2026). AI summary rewritten to lead with functional specialization in brains
  and DNNs and face-specific phenomena. Map position unchanged.
- Curtis L. Baker Jr. (on request): bio and AI summary rewritten from the UBC Vision Cluster
  profile, now led by human psychophysics (neurophysiology wrapping up); magnocellular paper
  updated to its Journal of Vision 2026 version and J Neurosci 2023 paper added. Map position
  unchanged.
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
- Anne B. Sereno: new profile photo (supplied by her).
- Brian A. Anderson (at his request): AI summary rewritten from text on his lab website;
  bio pronoun updated to match. Map position unchanged.
- Institution clean-up (330 → 327 distinct): merged "SISSA" and "International School for
  Advanced Studies"; University of Toronto Mississauga / Scarborough folded into "University of
  Toronto" and Hunter College into "City University of New York" (campus/college kept in the
  department field); "DEBCOM" typo → DEVCOM. Fixed wrong affiliations: Alessandro Farini
  (National University, US → CNR-INO, Italy), Philipp Sterzer (Charité → University of Basel,
  lab link updated), Andrea Benucci (RIKEN → Queen Mary University of London).
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
- Alex S. Baldwin (on request): photo replaced with the portrait from his own McGill page (old one was a different person). Map position unchanged.
- Alexander Schütz (on request): profile broadened beyond the five most recent papers; added three representative papers found via Crossref/OpenAlex (Schütz et al. 2008 Nat Neurosci, smooth pursuit sensitivity; Schütz et al. 2012 PNAS, salience and value; Schütz et al. 2011 J Vis, eye movements and perception review). AI summary rewritten to cover the earlier eye-movement work as well as recent metacognition work. Map position unchanged; a larger publication window in the map itself is not implemented.
- Andrea Facoetti (on request): AI summary replaced with the lab profile Dr. Facoetti sent (attention and perception in learning and neurodevelopment, dyslexia, autism, AVG training).
- Arash Afraz (on request): removed the incorrect spatial-frequency sentence from the AI summary, replaced with his wording, and dropped "also".
- Benjamin Balas (on request): removed from the map, search and profile pics at his request (2026-09-28); recorded as an opt-out so rebuilds and outreach do not re-add him.
- Added Tyler Bonnen (University of Pennsylvania, Psychology; E377), new lab starting Fall 2026.
  Five 2023+ first-author papers hand-picked and checked on Crossref/OpenAlex (multi-view 3D
  shape perception, hippocampal data augmentation, NeurIPS 2024 multiview benchmark, Cognition
  2025 perirhinal paper, eLife 2023 lesion paper); bio and AI summary written from his Penn
  faculty page and personal site, headshot from the Penn page; country United States; subfield
  from the classifier (Theory & Computation, plus Object Recognition and 3D Perception). Placed
  with the saved UMAP model (no refit, other dots unchanged) beside Kriegeskorte, Layton and
  Schrimpf. Map now has 797 PIs.
- Bianca M. van Kemenade (on request; also flagged by Martin Hebart): photo replaced with her own portrait from bvankemenade.com (old one was Elena Azanon). Paper list replaced with the five papers she sent (iScience 2026, Transl Psychiatry 2025, Schizophr Bull 2024, NeuroImage 2022, Hum Brain Mapp 2022; each DOI checked against Crossref/OpenAlex); AI summary broadened to cover all five, including the clinical work. Map position unchanged.
- Brad Duchaine (on request): AI summary replaced with the text Dr. Duchaine sent (PMO, developmental prosopagnosia, behavioral testing and neuroimaging, neural-network models for DP research). Map position unchanged.
- Cheryl Olman (on request): removed two papers that were not hers (a Naselaris eLife paper and a bioRxiv item whose DOI belongs to another group), replaced the bioRxiv orientation-tuned surround suppression preprint with the published PNAS version, corrected two DOIs, added two verified papers, and rewrote the last sentence of the AI summary.
- David Brainard (on request): lab link fixed to color.psych.upenn.edu (old one was dead); bioRxiv midget-RGC mosaic preprint replaced with its published Journal of Computational Neuroscience 2026 version. Map position unchanged.
- Elisha Merriam (on request): photo removed (it showed Denis Schluppeck; no verifiable NIMH headshot found), papers rebuilt from verified first/last-author work, bio and AI summary rewritten with the EEG, head-tilt and coordinate-transform claims dropped.
- Holger Wiese (on request): AI summary replaced with the text Prof. Wiese sent (EEG/ERP stages of face identity processing, N170, N250r and familiarity effects, face learning, individual differences). Map position unchanged.
- James Bisley (on request): photo removed (it showed someone else; he has no photo online), papers rebuilt from his Google Scholar profile (the five AI-listed papers were not his), bio and AI summary rewritten from verified work and the UCLA profile.
- Jennifer Steeves (on request): added four verified TMS papers (Mullin & Steeves 2011 J Cogn Neurosci and 2013 J Neurosci; Solomon-Harris et al. 2016 Brain Res; Stoby et al. 2022 Brain Behav); AI summary broadened to lead with TMS/TMS-fMRI work alongside enucleation plasticity and crossmodal work. Map position unchanged. Last-name sort in the country view not built.
- Jeremy Wilmer (on request): AI summary replaced with the two-paragraph ISWYM Lab description he sent, research keywords refocused on graph interpretation and data visualization, and the Star Mean preprint title corrected to match its linked OSF record.
- Kelly Bijanki (on request): AI summary and bio reframed to lead with affective neuroscience, intracranial electrophysiology and neuromodulation (DBS for depression), with facial emotion processing as one component; research area relabelled 'affective neuroscience and neuromodulation'. Papers unchanged. Map position unchanged.
- Lana M. Trick (on request): removed "Concurrently" from the dual-task sentence of the AI summary. Map position unchanged.
- Laure Pisella (on request): AI summary replaced with the corrected text Dr. Pisella sent (spatial cueing and pointing hypometria, gaze-contingent masking and attentional field, juggling, Posterior Cortical Atrophy); dyslexia sentence dropped. Map position unchanged.
- Laurence Harris (on request): bio notes Professor Emeritus and not taking students or postdocs
- Mel Rutherford (on request): AI summary replaced with the paragraph Dr. Rutherford sent (social perception and cognition across development, autism); pronouns corrected to he/him in bio and summary.
- Martin N. Hebart (on request): primary institution → Justus Liebig University Giessen (country mapping already present). AI summary broadened beyond the five latest papers to include his most-cited vision work (THINGS database and THINGS-data, behavior-derived object dimensions and their cortical maps, DNN-human alignment); paper list now mixes the influential 2020-24 papers with two 2025 ones. Bianca van Kemenade's photo also corrected (see her entry). Map position unchanged.
- Martin Szinte (on request, via Rolfs): photo replaced with the official INT (Institut de Neurosciences de la Timone) member-page photo; the old one was a different person. Map position unchanged.
- Michael Crognale (on request): bio notes retirement as of July 1 and continued consulting
- Michelle Greene (on request): AI summary and bio rewritten conservatively from her verified papers; unsupported claims (brain-guided CNN goal modeling, scale/viewpoint invariance from 'visual diet', efficient-coding funding) removed.
- Monica Rosenberg (on request): appended a sentence on her lab's developmental work to the AI summary.
- Ralf Haefner (on request): removed Csikor et al. (2025, Nat Commun), a paper he is not an author of (Crossref lists Csikor, Meszena, Ocsai, Orban), and the V1/V2 top-down feedback claim built on it; added Liu, Pletenev, Haefner & Snyder (2026, Science) on task learning and V4 redundancy, which the first/last-author filter missed because senior authorship was shared. AI summary updated. Map position unchanged.
- Randi Starrfelt (on request): removed the 2024 Cortex item with the wrong DOI (10.1016/j.cortex.2024.03.010 is an unrelated Lega-lab paper; the topographical-processing summary claim went with it) and the 2024 Cortex commentary to make room; added Robotham et al. (2023, Brain Commun) and Munk et al. (2023, Cortex) on visual deficits after posterior stroke; AI summary rewritten to include acquired brain injury. Map position unchanged.
- Richard A. Abrams (on request): photo replaced (the old one was a different person; new one from the WashU Psychological & Brain Sciences faculty page, matching the picture he sent) and lab link → http://rabrams.net/. Map position unchanged.
- Sami Yousif (on request): affiliation corrected from UNC Chapel Hill to The Ohio State University (Department of Psychology)
- Stephen Adamo (on request): AI summary replaced with the two paragraphs Dr. Adamo sent (attention and rare/multiple-target search, cancer detection in 2D mammography and 3D tomosynthesis, expertise and AI decision support); photo replaced with the University of Arizona faculty headshot; lab link → ADAMO Lab site. Map position unchanged.
- Yoshiyuki Ueda (on request): personal/lab link fixed to his IFoHS member page. Map position unchanged.
- Mauro Manassi (on request): visual crowding added to the AI summary (lead research line, with uncrowding and grouping) and three crowding papers added (Schwetlick et al. 2025 J Vis; Manassi & Whitney 2018 Curr Biol; Manassi, Sayim & Herzog 2013 J Vis). Also fixed the list: dropped the 2025 QJEP 'Faces displaying dominance and trustworthiness...' entry (Crossref lists Sharma, Jalalian, Caughey, Golubickis, Macrae; he is not an author) and its dot-probe summary claim, corrected the Visual Cognition 2024 DOI, and swapped the PsyArXiv trustworthiness preprint for its published BMC Biol 2026 version. Map position unchanged.
- Duje Tadin (on request): AI summary replaced with the recent-research version Dr. Tadin sent (spatial suppression in MT/V5, autism and schizophrenia, vision restoration after occipital stroke, optical adaptation, VR); previous summary was based on a single paper. Map position unchanged.
- J. Douglas Crawford (on request): AI summary's recent-work passage replaced with the text Dr. Crawford sent (egocentric/allocentric integration, fMRI + graph theory, transsaccadic constancy, FEF recording scales, and current cortico-cerebellar eye-hand coordination work); opening sentence kept. Map position unchanged.
- Paul Bays (on request): AI summary now attributes the work to his lab ("Dr Bays' lab has...").
- Wei Ji Ma (on request): profile rebuilt around common themes (probabilistic population codes and uncertainty in vision, resource-based visual working memory, confidence and attention-dependent uncertainty) rather than a summary of recent papers; the recent list (planning, procrastination, cognitive-science proceedings, representation review) replaced with influential vision-relevant papers plus his recent Nat Neurosci and Sci Adv papers. His suggestion to weight journal impact factor / citations more heavily is recorded as feedback, not an adopted scoring policy. Map position unchanged.
- C. Shawn Green (on request): removed Pasqualotto et al. (GALA 2025 / LNCS 2026, multidimensional probabilistic DDA), a paper he is not an author of (Crossref: Pasqualotto, Fanourakis, Menestrina, Nahum, Bavelier), and the dropout / dynamic-difficulty claim built on it; added Cochrane, Lu & Green (2024, J Cogn Enhanc) on perceptual learning as a continuous function of time-on-task. AI summary updated. Map position unchanged.
- Merav Ahissar (on request): AI summary replaced with the three-paragraph description Dr. Ahissar sent (perception as sensory traces plus accumulated knowledge, two-tone discrimination, dyslexia and autism dynamics).
- Joshua I. Gold (on request): photo replaced (old one was a different person); new one from the Gold Lab people page. Map position unchanged.
- Alessandra Angelucci (on request): appended a sentence on corticocortical feedback projections to the AI summary.
- Marla Feller (on request): AI summary now opens with her retinal waves work (cellular mechanisms and role in visual system development) and keeps the direction-selective circuit work. Map position unchanged.
- Adrian Staub (on request): AI summary replaced with the edited version Dr. Staub sent (reading and eye movements, missed text errors, predictability, agreement attraction).
- SueYeon Chung (on request): institution New York University → Harvard University (country United States); department cleared until confirmed. Map position unchanged.
- Ruth Rosenholtz (on request): AI summary no longer ties visual search asymmetries to peripheral vision; real-world applications now also cover perception for driving and peripheral vision for action. Map position unchanged.
- Shinsuke Shimojo (on request): AI summary replaced with his lightly revised version (adds psychophysics, team flow, and magnetoreception–vision interaction). Map position unchanged.
- Timothy Vickery (audit): removed a 2017 paper mislabeled as 2024 (fabricated venue and DOI) and added Lebed, Scanlon & Vickery (APP, 2023); AI summary regenerated from the corrected papers. Map position unchanged.
- **Profile audit of all PIs** (Crossref DOI check of every paper plus a web check by agents, each fix re-verified by a second agent): 170 fabricated, mislabeled, pre-2023 or conference-abstract papers removed, 98 middle-author papers removed (kept where a profile would otherwise be left with two or fewer), 437 papers corrected (mostly Semantic Scholar links replaced by DOIs, some wrong years/venues), 19 verified papers added. Profile fixes: institution for 5 PIs, 4 name spellings, 3 lab URLs. Hand-edited AI summaries untouched. No PI is without a paper from 2022 or later, so nobody was removed from the map. Map positions unchanged.
- **AI summaries rewritten for 719 PIs** (Claude Sonnet 5.5 agents, from each PI's corrected papers; same prompt rules as `research_direction.md` plus a clearer, more intuitive style for a technical audience). The 78 hand-edited summaries were left as they are. Map positions unchanged (embeddings not re-run).
- **Thin profiles filled in**: for the 84 PIs with one or two papers, an online search (Crossref, OpenAlex, lab pages) found 79 more verified first- or last-author papers for 42 of them (each checked by a second agent; 47 PIs still have two or fewer, nothing further qualifying); their AI summaries were rewritten. **Map regenerated**: embeddings re-run on the new summaries and papers and UMAP re-fit, so all dot positions and `similar` lists changed (nearest-neighbour subfield agreement 39.6% → 40.5%).
- **Subfields reassigned for all 797 PIs** by Claude agents from each PI's AI summary and latest papers (one primary plus up to two secondary of the 21 VSS topic areas; the 3 manual overrides still win). 196 primary subfields changed. The per-subfield Field Directions summaries were not regenerated.
- Nihong Chen (on request): institution Tsinghua University → South China Normal University (School of Psychology; country China); old Tsinghua lab name and link cleared; bio updated; added the 2026 bioRxiv perceptual-learning working-memory paper and the 2025 Science China Technological Sciences review (first author); AI summary rewritten. Map position unchanged.
- List view: removed the sort-by toggle; the directory always sorts by first name.

### Frontend
- Deep links: selecting a scholar sets `#/scholar/<id>` in the URL and opening such a link selects
  and centers them (works on the static GitHub Pages build). Map hit targets keep a constant
  on-screen size when zoomed, so neighbours of a selected scholar can be hovered and clicked.
  The list view sorts by last name by default, with a first-name toggle.
- **Control bar regrouped**: the List | Map switch now sits beside the search box as a
  segmented control (soft tinted thumb that slides, label colour in sync with it); the
  Institution, Country and Field filters share one card on the right. All three groups use
  the same compact 40px surface in a warm near-white (translucent, soft shadow) so it sits on
  the page rather than popping out; filter menus and search results use an opaque version of
  the same tone. The search is now a single field (no box-in-a-box) with results floating
  below it. When the panel is too narrow the filters drop to a second
  row sized to match the first (container query); on phones search + switch share row one and
  the filters fill row two.
  In list view a band behind the cards stops scrolling rows from showing between them.
- **Country filter** next to Institution and Field: multi-select dropdown with counts
  (United States 411, Canada 67, United Kingdom 54, …); filters both the map and the list view.
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
