Find the {num_papers} most recent academic papers by {scholar_name} from {institution}.

Focus on papers where they are the **last author** (senior/corresponding author) from the **last 3 years**.

For each paper, provide:
- title: exact paper title
- abstract: the paper's abstract (full abstract if available, otherwise a detailed summary)
- year: publication year
- citations: approximate citation count (or "0" if unknown)
- venue: journal or conference name
- authors: full author list as a comma-separated string
- last_author: the last author on the paper
- url: DOI or paper URL if available

If you cannot find {num_papers} papers where they are last author, include papers where they are first author or a key contributor. Return ONLY the JSON, no other text.
