Find the {num_papers} most recent academic papers by {scholar_name} from {institution}.

STRICT REQUIREMENTS:
- Focus on papers where they are the **last author** (senior/corresponding author)
- Papers must be published in **2023 or later** (post-2023 only). Prioritize most recent first.
- Only include **full peer-reviewed journal articles or preprints** (e.g. Nature, Science, PNAS, PLOS, eLife, Journal of Neuroscience, bioRxiv/arXiv preprints, etc.)
- **EXCLUDE conference abstracts**: VSS abstracts, Journal of Vision (JOV) conference supplement abstracts, CCN extended abstracts, COSYNE abstracts, SfN abstracts, OHBM abstracts
- Do NOT make up or hallucinate any papers. Only include papers you can verify.

For each paper, provide:
- title: exact paper title
- abstract: Write a technical, domain-expert paraphrase of the paper's abstract. Use the same level of specialized terminology and jargon as the original — do NOT simplify for a general audience. Preserve all specific methods, model names, brain regions, metrics, and quantitative findings. Closely rephrase without copying verbatim.
- year: publication year
- citations: approximate citation count (or "0" if unknown)
- venue: journal or conference name
- authors: full author list as a comma-separated string
- url: DOI or paper URL if available

If you cannot find {num_papers} papers where they are last author, include papers where they are first author or a key contributor. Return ONLY the JSON, no other text.
