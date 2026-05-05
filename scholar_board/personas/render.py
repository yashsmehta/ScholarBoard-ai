"""Render selected scholars as markdown persona files."""

from __future__ import annotations

from typing import Any

import yaml

from .utils import (
    apply_abstract_fixups,
    authors_text,
    citation_count,
    clean_text,
    normalized_for_substring,
    scalar,
)


def frontmatter_for(scholar: dict[str, Any]) -> dict[str, Any]:
    """Build YAML frontmatter fields for a scholar."""
    data: dict[str, Any] = {}
    for field in (
        "name",
        "institution",
        "department",
        "lab_name",
        "main_research_area",
        "total_citations",
        "h_index",
    ):
        value = scalar(scholar.get(field))
        if value is not None:
            data[field] = clean_text(value) if isinstance(value, str) else value
    return data


def build_subhead(scholar: dict[str, Any]) -> str:
    """Build the italicized affiliation line below a persona title."""
    area = clean_text(scholar.get("main_research_area"))
    institution = clean_text(scholar.get("institution"))
    department = clean_text(scholar.get("department"))
    lab_name = clean_text(scholar.get("lab_name"))
    if (
        department
        and institution
        and normalized_for_substring(department) in normalized_for_substring(institution)
    ):
        department = ""
    if (
        lab_name
        and department
        and normalized_for_substring(lab_name) in normalized_for_substring(department)
    ):
        lab_name = ""
    parts = [institution, department, lab_name]
    affiliation = ", ".join(part for part in parts if part)
    if area and affiliation:
        return f"*{area}* — {affiliation}."
    if area:
        return f"*{area}*."
    if affiliation:
        return f"{affiliation}."
    return ""


def sorted_papers(scholar: dict[str, Any]) -> list[dict[str, Any]]:
    """Return papers sorted newest first by year text."""
    papers = list(scholar.get("papers") or [])
    return sorted(
        papers,
        key=lambda paper: clean_text(paper.get("year")),
        reverse=True,
    )


def paper_markdown(paper: dict[str, Any]) -> str:
    """Render one paper as a markdown section."""
    year = clean_text(paper.get("year")) or "Year unknown"
    title = clean_text(paper.get("title")) or "Untitled"
    lines = [f"### {year} — {title}"]

    venue = clean_text(paper.get("venue"))
    citations = citation_count(paper.get("citations"))
    if venue and citations and citations > 0:
        lines.append(f"*{venue} · {citations} citations*")
    elif venue:
        lines.append(f"*{venue}*")

    authors = authors_text(paper.get("authors"))
    if authors:
        lines.append(f"Authors: {authors}")

    abstract = clean_text(apply_abstract_fixups(paper.get("abstract"))) or "*Abstract unavailable.*"
    lines.extend(["", abstract])
    return "\n".join(lines)


def render_persona(scholar: dict[str, Any]) -> str:
    """Render a scholar into a complete markdown persona document."""
    frontmatter = yaml.safe_dump(
        frontmatter_for(scholar),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()

    name = clean_text(scholar.get("name")) or "Unknown Researcher"
    lines = ["---", frontmatter, "---", "", f"# {name}", ""]

    subhead = build_subhead(scholar)
    if subhead:
        lines.extend([subhead, ""])

    bio = clean_text(scholar.get("bio")) or "*Bio not available.*"
    lines.extend(["## Background", "", bio, "", "## Papers"])

    for paper in sorted_papers(scholar):
        lines.extend(["", paper_markdown(paper)])

    return "\n".join(lines).rstrip() + "\n"
