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
NAME_CORRECTIONS = {
    "Grabriel Kreiman": "Gabriel Kreiman",
}
ABSTRACT_FIXUPS = [
    ("commonRelational", "common relational"),
]
FIRST_LAST_FILTER_IDS = {"0356", "0462", "0691", "0724"}
CANONICAL_DUPLICATE_IDS = {
    "0557": "0491",
}


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


def apply_name_correction(name: Any) -> Any:
    if not isinstance(name, str):
        return name
    return NAME_CORRECTIONS.get(name.strip(), name)


def apply_abstract_fixups(abstract: Any) -> Any:
    if not isinstance(abstract, str):
        return abstract
    for find, replace in ABSTRACT_FIXUPS:
        abstract = abstract.replace(find, replace)
    return abstract


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


def normalized_for_substring(value: Any) -> str:
    return re.sub(r"\s+", " ", clean_text(value).lower()).strip()


def normalized_name(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean_text(value))
    text = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.ASCII)
    return re.sub(r"\s+", " ", text).strip()


def dedup_value(value: Any) -> Any:
    if is_blank(value):
        return None
    return clean_text(value) if isinstance(value, str) else value


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


def scholar_last_name(name: Any) -> str:
    parts = clean_text(name).split()
    return parts[-1].lower() if parts else ""


def first_last_author_matches(scholar: dict[str, Any], paper: dict[str, Any]) -> bool:
    last_name = scholar_last_name(scholar.get("name"))
    if not last_name:
        return False
    author_entries = [
        author.strip()
        for author in authors_text(paper.get("authors")).split(",")
        if author.strip()
    ]
    if not author_entries:
        return False
    first_author = author_entries[0].lower()
    last_author = author_entries[-1].lower()
    return last_name in first_author or last_name in last_author


def prepare_scholar(raw_scholar: dict[str, Any]) -> dict[str, Any]:
    scholar = dict(raw_scholar)
    scholar["name"] = apply_name_correction(scholar.get("name"))
    papers = [dict(paper) for paper in scholar.get("papers") or []]
    for paper in papers:
        paper["abstract"] = apply_abstract_fixups(paper.get("abstract"))
    if clean_text(scholar.get("id")) in FIRST_LAST_FILTER_IDS:
        papers = [paper for paper in papers if first_last_author_matches(scholar, paper)]
    scholar["papers"] = papers
    return scholar


def dedup_ranked_matches(
    matches: list[tuple[dict[str, Any], float]],
) -> tuple[list[tuple[dict[str, Any], float]], int]:
    deduped: list[tuple[dict[str, Any], float]] = []
    seen_name_institution: set[tuple[str, str]] = set()
    seen_lab_citations: set[tuple[Any, Any, Any]] = set()
    dropped = 0

    for scholar, score in matches:
        if clean_text(scholar.get("id")) in CANONICAL_DUPLICATE_IDS:
            dropped += 1
            continue

        name_institution_key = (
            normalized_name(scholar.get("name")),
            clean_text(scholar.get("institution")).lower(),
        )
        lab_citations_key = (
            dedup_value(scholar.get("institution")),
            dedup_value(scholar.get("lab_name")),
            dedup_value(scholar.get("total_citations")),
        )
        has_name_institution_key = all(name_institution_key)
        has_lab_citations_key = all(value is not None for value in lab_citations_key)

        if (
            has_name_institution_key
            and name_institution_key in seen_name_institution
        ) or (has_lab_citations_key and lab_citations_key in seen_lab_citations):
            dropped += 1
            continue

        deduped.append((scholar, score))
        if has_name_institution_key:
            seen_name_institution.add(name_institution_key)
        if has_lab_citations_key:
            seen_lab_citations.add(lab_citations_key)

    return deduped, dropped


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

    abstract = clean_text(apply_abstract_fixups(paper.get("abstract"))) or "*Abstract unavailable.*"
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
    filter_kept_ids: set[str] = set()
    filter_dropped_ids: set[str] = set()

    for raw_scholar in scholars_by_id.values():
        scholar = prepare_scholar(raw_scholar)
        scholar_id = clean_text(scholar.get("id"))
        if scholar_id in FIRST_LAST_FILTER_IDS:
            if scholar.get("papers"):
                filter_kept_ids.add(scholar_id)
            else:
                filter_dropped_ids.add(scholar_id)
                continue

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
    deduped_matches, dedup_dropped_count = dedup_ranked_matches(matches)
    top_matches = deduped_matches[:MAX_PERSONAS]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intended_paths = {
        OUTPUT_DIR / f"{clean_text(scholar.get('id'))}_{name_slug(clean_text(scholar.get('name')) or 'unknown_researcher')}.md"
        for scholar, _score in top_matches
    }
    for existing_path in OUTPUT_DIR.glob("*.md"):
        if existing_path not in intended_paths:
            existing_path.unlink()

    for scholar, _score in top_matches:
        scholar_id = clean_text(scholar.get("id"))
        name = clean_text(scholar.get("name")) or "unknown_researcher"
        path = OUTPUT_DIR / f"{scholar_id}_{name_slug(name)}.md"
        path.write_text(persona_markdown(scholar), encoding="utf-8")

    scores = [score for _scholar, score in top_matches]
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    print(f"{TARGET_SUBFIELD} researchers found: {len(matches)}")
    print(f"Dedup dropped: {dedup_dropped_count}")
    print(
        "First/last-author filter: "
        f"kept {len(filter_kept_ids)} of {len(FIRST_LAST_FILTER_IDS)}, "
        f"dropped {len(filter_dropped_ids)} (zero matching papers)"
    )
    print(f"Top-100 score range: {min_score:.4f}..{max_score:.4f}")
    print(f"Files written: {len(top_matches)}")
    print("Output directory: personas/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
