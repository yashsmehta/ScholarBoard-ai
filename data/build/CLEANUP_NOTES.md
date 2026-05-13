# Scholar data cleanup notes

## Duplicate scholar decisions

- Merged `0177` Dirk B. Walther into `0178` Dirk Bernhardt-Walther. The surviving record keeps the published name, University of Toronto affiliation, Bernhardt-Walther Lab metadata, `0178` profile picture, and the union of unique papers from both records.
- Left `0165` David Soto and `0166` David Souto separate. Their surnames, institutions, labs, research areas, and paper lists point to distinct researchers.

## Institution aliases applied

| Original | Standardized |
|---|---|
| `MIT` | `Massachusetts Institute of Technology` |
| `NIH` | `National Institutes of Health` |
| `CNRS` | `French National Centre for Scientific Research` |

Abbreviation-only entries left unchanged because they are canonical or ambiguous in this dataset: `A*STAR`, `EPFL`, `IPM`, and `SISSA`.

## Paper deduplication

Within-scholar duplicate paper titles were removed for `0062`, `0149`, `0304`, `0634`, `0671`, and `0698`. Where duplicate objects differed, the retained record preferred the published journal/conference version over preprints and otherwise kept the more complete metadata.

## Factual corrections (round 2 — grounded)

Pass 1 triage flagged 100 candidate records in `/tmp/factcheck_candidates.json`. Pass 2 online verification produced 13 high-confidence field corrections; all were applied to `data/build/scholars.json`, and the complete proposal log is saved in `data/build/factcheck_proposals.json`.

| Scholar | Field | Original | Corrected | Source URLs |
|---|---|---|---|---|
| `0001` A. Caglar Tas | `name` | `A . Caglar Tas` | `A. Caglar Tas` | https://vpclab.weebly.com/ ; https://faculty.utk.edu/Caglar.Tas |
| `0109` Cathleen M. Moore | `lab_url` | `https://iapl.lab.uiowa.edu/` | `https://psychology.uiowa.edu/people/cathleen-moore` | https://psychology.uiowa.edu/people/cathleen-moore |
| `0128` Christopher L. Striemer | `institution` | `University of Alberta` | `MacEwan University` | https://www.macewan.ca/academics/academic-departments/psychology/our-people/profile/?profileid=striemerc ; https://sites.google.com/macewan.ca/apa-lab |
| `0128` Christopher L. Striemer | `lab_url` | `https://sites.google.com/a/macewan.ca/striemer-lab/` | `https://sites.google.com/macewan.ca/apa-lab` | https://sites.google.com/macewan.ca/apa-lab ; https://www.macewan.ca/academics/academic-departments/psychology/our-people/profile/?profileid=striemerc |
| `0145` Daniel D. Dilks | `lab_url` | `https://psychology.emory.edu/dilks-lab/` | `https://secure.web.emory.edu/psychology/dilks/main.php` | https://secure.web.emory.edu/psychology/dilks/main.php ; https://secure.web.emory.edu/psychology/dilks/people.php |
| `0197` Elissa L. Newport | `lab_url` | `https://cbpr.georgetown.edu/people/elissa-l-newport-ph-d/` | `https://ldl.georgetown.edu/home` | https://neurology.georgetown.edu/newport/ ; https://ldl.georgetown.edu/home ; https://cbpr.georgetown.edu/learning-and-developmental-plasticity/ |
| `0254` Heiko H. Schütt | `lab_url` | `https://heiko-schuett.github.io/` | `https://www.uni.lu/fhse-en/people/heiko-schutt/` | https://www.uni.lu/fhse-en/people/heiko-schutt/ ; https://orbilu.uni.lu/profile?uid=50065259 |
| `0302` Jeremy M. Wolfe | `lab_url` | `https://search.bwh.harvard.edu/` | `https://search.bwh.harvard.edu/new/` | https://search.bwh.harvard.edu/new/ ; https://eye.hms.harvard.edu/jeremywolfe |
| `0400` Lisa M. Oakes | `lab_url` | `https://infantcognition.ucdavis.edu/` | `https://oakeslab.ucdavis.edu/` | https://oakeslab.ucdavis.edu/ ; https://psychology.ucdavis.edu/research-labs/infant-cognition-lab-oakes ; https://mindbrain.ucdavis.edu/people/lisa-oakes |
| `0439` Mary Peterson | `lab_url` | `https://mapeters.wixsite.com/visualperceptionlab` | `https://petersonlab.wixsite.com/visualperceptionlab` | https://www.cogsci.arizona.edu/person/mary-peterson ; https://petersonlab.wixsite.com/visualperceptionlab |
| `0456` Michael A. Webster | `lab_url` | `https://www.unr.edu/psychology/labs/visual-perception-lab` | `https://labs.psych.unr.edu/websterlab/` | https://www.unr.edu/psychology/michael-webster ; https://labs.psych.unr.edu/websterlab/ |
| `0537` Philip J. Kellman | `lab_url` | `https://humanperceptionlab.psych.ucla.edu/` | `https://kellmanlab.psych.ucla.edu/` | https://kellmanlab.psych.ucla.edu/ ; https://www.psych.ucla.edu/faculty-page/kellman/ |
| `0695` William H. Warren | `lab_url` | `https://venlab.brown.edu/` | `https://sites.brown.edu/venlab/` | https://sites.brown.edu/venlab/ |

## Duplicate merges (round 3)

Nine user-approved merges of records that were the same person (token reversal, nicknames, name initialization, or transliteration variants). Each retired record's unique papers were unioned into the survivor; all other fields preferred the survivor's value, falling back only when missing.

| Survivor | Retired | Final name | Institution | Signals |
|---|---|---|---|---|
| `0661` | `0649` | Thomas C. Sprague | UCSB | initials → full name, same lab, shared papers |
| `0491` | `0557` | N. Apurva Ratan Murty | Georgia Institute of Technology | token containment, same Murty Lab |
| `0622` | `0103` | Simona Buetti | UIUC | token reversal, same lab |
| `0081` | `0549` | Bevil Conway | NIH | token reversal, same lab |
| `0110` | `0368` | Chai-Youn Kim | Korea University | token containment, same lab URL |
| `0279` | `0088` | Isabelle Boutet | University of Ottawa | token reversal, same SCOPE Lab |
| `E090` | `E282` | Radoslaw Martin Cichy | Freie Universität Berlin | nickname (Radek = Radoslaw), same lab URL |
| `0047` | `0367` | Anna C. Nobre | Yale University | nickname (Kia = Anna), same lab URL |
| `0456` | `0003` | Michael A. Webster | University of Nevada, Reno | token reversal, same lab |

### Trim papers to 5 most recent (round-3 survivors)

After the merges above, papers were unioned, so several survivors exceeded the 5-paper cap. Trimmed each to the 5 most recent papers (year descending, citations as tiebreaker). Author-position filtering was not changed in this pass — papers remain last-author only.

| Scholar | Before | After |
|---|---|---|
| `0661` Thomas C. Sprague | 4 | 4 |
| `0491` N. Apurva Ratan Murty | 7 | 5 |
| `0622` Simona Buetti | 4 | 4 |
| `0081` Bevil Conway | 6 | 5 |
| `0110` Chai-Youn Kim | 6 | 5 |
| `0279` Isabelle Boutet | 5 | 5 |
| `E090` Radoslaw Martin Cichy | 7 | 5 |
| `0047` Anna C. Nobre | 8 | 5 |
| `0456` Michael A. Webster | 10 | 5 |
