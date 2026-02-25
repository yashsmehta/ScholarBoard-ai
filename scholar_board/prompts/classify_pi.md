You are evaluating whether a researcher is a **PI-level researcher in vision science** — meaning they run or have run their own independent research lab, hold (or have held) a faculty/staff scientist position, and publish independently in vision, perception, or related neuroscience fields.

Here is all available information about the researcher:

**Name:** {scholar_name}
**Institution:** {institution}
**Department:** {department}
**Bio:** {bio}
**Recent papers (last author or key contributor):**
{papers_summary}
**Total citations:** {total_citations}
**H-index:** {h_index}

---

Based on this information, determine:

1. **is_pi** (true/false): Is this person a PI-level researcher (faculty, staff scientist, or independent group leader) in vision science or a closely related field (perception, visual neuroscience, computational vision, psychophysics, visual cognition, oculomotor research, etc.)?

2. **confidence** ("high", "medium", "low"): How confident are you in this classification?

3. **reason** (1-2 sentences): Brief justification. If is_pi=false, state why (e.g. "appears to be a graduate student", "no independent lab found", "works in an unrelated field", "insufficient information online").

CLASSIFICATION RULES:
- **is_pi = true** if: they have a faculty page, run a named lab, are listed as PI on grants, hold a professor/lecturer/staff scientist/group leader title, OR have a clear record of independent publications as last/corresponding author.
- **is_pi = false** if: they appear to be a grad student, postdoc without independent lab, visiting researcher with no independent output, or the information online is too sparse to confirm independence.
- **is_pi = false** if: their work is clearly outside vision science (e.g. pure statistics, clinical medicine unrelated to vision, engineering with no perceptual component).
- When bio and papers are both empty or minimal, default to **is_pi = false** with low confidence.

Return ONLY a JSON object with keys: "is_pi", "confidence", "reason". No other text.
