"""Build markdown personas for top Brain-AI Alignment researchers."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_SCHOLARS_JSON = PROJECT_ROOT / "data" / "build" / "scholars.json"
REMOTE_SCHOLARS_JSON = "https://yashsmehta.com/scholarboard/data/build/scholars.json"
OUTPUT_DIR = PROJECT_ROOT / "personas"
TARGET_SUBFIELD = "Brain-AI Alignment"
MAX_PERSONAS = 100


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def clean_text(value: Any) -> str:
    if is_blank(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\bsubfields?\b", "research areas", text, flags=re.IGNORECASE)
    text = re.sub(r"\bprimary_subfield\b", "primary research area", text)
    text = re.sub(r"\bresearch_direction\b", "research direction", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def load_scholars() -> dict[str, Any]:
    if LOCAL_SCHOLARS_JSON.exists():
        with LOCAL_SCHOLARS_JSON.open(encoding="utf-8") as f:
            return json.load(f)

    with urllib.request.urlopen(REMOTE_SCHOLARS_JSON, timeout=60) as response:
        return json.load(response)


def brain_ai_score(scholar: dict[str, Any]) -> float | None:
    for entry in scholar.get("subfields") or []:
        if entry.get("subfield") == TARGET_SUBFIELD:
            try:
                return float(entry.get("score"))
            except (TypeError, ValueError):
                return 0.0
    return None


def name_slug(name: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower())
    return re.sub(r"_+", "_", slug).strip("_")


def scalar(value: Any) -> Any:
    if is_blank(value):
        return None
    return value


def frontmatter_for(scholar: dict[str, Any]) -> dict[str, Any]:
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


def subhead_for(scholar: dict[str, Any]) -> str:
    area = clean_text(scholar.get("main_research_area"))
    parts = [
        clean_text(scholar.get("institution")),
        clean_text(scholar.get("department")),
        clean_text(scholar.get("lab_name")),
    ]
    affiliation = ", ".join(part for part in parts if part)
    if area and affiliation:
        return f"*{area}* — {affiliation}."
    if area:
        return f"*{area}*."
    if affiliation:
        return f"{affiliation}."
    return ""


def authors_text(authors: Any) -> str:
    if is_blank(authors):
        return ""
    if isinstance(authors, list):
        return clean_text(", ".join(str(author) for author in authors if not is_blank(author)))
    return clean_text(authors)


def citation_count(value: Any) -> int | None:
    if is_blank(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def sorted_papers(scholar: dict[str, Any]) -> list[dict[str, Any]]:
    papers = list(scholar.get("papers") or [])
    return sorted(
        papers,
        key=lambda paper: clean_text(paper.get("year")),
        reverse=True,
    )


def paper_markdown(paper: dict[str, Any]) -> str:
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

    abstract = clean_text(paper.get("abstract")) or "*Abstract unavailable.*"
    lines.extend(["", abstract])
    return "\n".join(lines)


def persona_markdown(scholar: dict[str, Any]) -> str:
    frontmatter = yaml.safe_dump(
        frontmatter_for(scholar),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()

    name = clean_text(scholar.get("name")) or "Unknown Researcher"
    lines = ["---", frontmatter, "---", "", f"# {name}", ""]

    subhead = subhead_for(scholar)
    if subhead:
        lines.extend([subhead, ""])

    bio = clean_text(scholar.get("bio")) or "*Bio not available.*"
    lines.extend(["## Background", "", bio, "", "## Papers"])

    for paper in sorted_papers(scholar):
        lines.extend(["", paper_markdown(paper)])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    scholars_by_id = load_scholars()
    matches: list[tuple[dict[str, Any], float]] = []

    for scholar in scholars_by_id.values():
        score = brain_ai_score(scholar)
        if score is not None:
            matches.append((scholar, score))

    matches.sort(
        key=lambda item: (
            -item[1],
            -(item[0].get("total_citations") or 0),
            clean_text(item[0].get("name")),
        )
    )
    top_matches = matches[:MAX_PERSONAS]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for scholar, _score in top_matches:
        scholar_id = clean_text(scholar.get("id"))
        name = clean_text(scholar.get("name")) or "unknown_researcher"
        path = OUTPUT_DIR / f"{scholar_id}_{name_slug(name)}.md"
        path.write_text(persona_markdown(scholar), encoding="utf-8")

    scores = [score for _scholar, score in top_matches]
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    print(f"{TARGET_SUBFIELD} researchers found: {len(matches)}")
    print(f"Top-100 score range: {min_score:.4f}..{max_score:.4f}")
    print(f"Files written: {len(top_matches)}")
    print("Output directory: personas/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
