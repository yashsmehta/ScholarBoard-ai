Parse the following raw researcher data into a structured JSON object matching the schema below.

## Raw Researcher Profile
{raw_profile}

## Raw Papers Data
{raw_papers}

## Target JSON Schema
{json_schema}

Instructions:
- Extract all available fields from the raw data
- For missing fields, use null
- For research_areas, extract a list of specific research topics/keywords
- For education, extract degree, institution, year, field, and advisor where available
- For papers, include title, abstract, year, venue, citations, authors, and last_author
- Ensure the bio field is a concise 2-3 sentence summary of the researcher's work
- Return ONLY valid JSON matching the schema, no other text
