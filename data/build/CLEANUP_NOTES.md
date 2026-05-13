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
