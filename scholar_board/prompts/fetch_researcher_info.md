Extract a structured research profile for {scholar_name} from {institution}.

Provide accurate, verified information for the following fields:

- **scholar_name**: Full name
- **institution**: Current institutional affiliation
- **department**: Department or school within the institution
- **lab_url**: URL of their research lab or personal academic page (if known)
- **main_research_area**: A concise 2-5 word description of their primary research focus (e.g. "visual attention and perception", "computational neuroscience")
- **bio**: A single paragraph (3-5 sentences) summarizing their most notable research contributions, methodologies, and current research direction. Be technical and precise.

IMPORTANT:
- Only include information you can verify from online sources (faculty pages, lab websites, Google Scholar, PubMed).
- If a specific field value is unknown or unverifiable, omit it — do NOT guess or invent details.
- **If you cannot find any verified information about this person online, return exactly:** {{"scholar_name": "{scholar_name}", "not_found": true}}
- Do NOT fabricate a bio, department, or lab URL for someone you cannot find online.

Return ONLY the JSON, no other text.
