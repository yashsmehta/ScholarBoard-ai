You are an expert in vision science. Classify a researcher into the Vision Sciences Society (VSS) topic areas based on their profile and publications.

## The {n_subfields} VSS topic areas

{subfields_block}

## Researcher

**Name:** {scholar_name}
**Institution:** {institution}
**Stated research area:** {main_research_area}

**Bio:**
{bio}

**Current research direction:**
{research_direction}

**Recent papers:**
{papers_text}

## Task

Decide which topic area best captures the **center of gravity** of this researcher's work — what they are primarily known for and spend most of their effort on, not every topic they have ever touched.

- Choose exactly ONE `primary` topic area — the single best fit.
- Optionally add up to TWO `secondary` topic areas that are clearly substantial in their work. Omit secondaries entirely if the researcher is narrowly focused; do not pad the list.
- Use the topic names **exactly** as written above. Never invent a topic.
- Distinguish mechanism from application: e.g. biological motion studied as a *motion* mechanism → Motion, but studied to read social intent → Social Perception. Computational/modeling researchers (deep nets, RSA, encoding models, Bayesian theory) → Theory & Computation.

Return JSON with this shape:
{{"primary": "<topic name>", "secondary": ["<topic name>", ...], "reasoning": "<one sentence>"}}
