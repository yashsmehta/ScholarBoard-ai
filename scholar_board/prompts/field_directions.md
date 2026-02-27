You are a senior vision science researcher synthesizing the current state of a research subfield.

Below are AI-generated summaries of recent research directions from {n_researchers} active researchers whose primary work falls under the subfield of **{subfield_name}**.

Subfield definition: {subfield_description}

---

{researcher_directions}

---

Based on these research directions, synthesize a structured field-level summary. Your job is to identify the *collective* patterns — what the field as a whole is doing — not to summarize any individual researcher.

Return a JSON object with exactly these five keys:

- "overview": A 2–3 sentence description of what this subfield studies and why it matters in the context of vision science today. Write for a scientifically literate audience (e.g., a researcher from a neighboring subfield).

- "active_research_themes": A list of 4–6 concrete themes that multiple researchers are actively pursuing right now. Each theme should be a short title (3–6 words) paired with a 2–3 sentence explanation. Format as a list of objects: [{"theme": "...", "description": "..."}]

- "open_questions": A list of 3–5 specific, unresolved scientific questions the field is grappling with. These should be genuine open problems — not vague platitudes. Format as a list of strings.

- "methods_and_approaches": A list of 3–5 methods or experimental/computational approaches that are prominent across researchers in this subfield. Each should include a short name and a 1–2 sentence description. Format as a list of objects: [{"method": "...", "description": "..."}]

- "emerging_directions": A list of 2–4 directions that appear nascent or forward-looking based on what researchers are beginning to explore. Each should be a short title paired with a 1–2 sentence explanation. Format as a list of objects: [{"direction": "...", "description": "..."}]

Return ONLY valid JSON. No markdown fences, no preamble, no commentary outside the JSON.
