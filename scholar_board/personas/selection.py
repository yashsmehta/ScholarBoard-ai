from __future__ import annotations

import re
import unicodedata
from typing import Any

from .config import CANONICAL_DUPLICATE_IDS, FIRST_LAST_FILTER_IDS, NAME_CORRECTIONS, TARGET_SUBFIELD
from .utils import apply_abstract_fixups, authors_text, clean_text


def _name_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean_text(value))
    text = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.ASCII)
    return re.sub(r"\s+", " ", text).strip()


def _dedup_value(value: Any) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return clean_text(value) if isinstance(value, str) else value


def first_last_author_matches(scholar: dict[str, Any], paper: dict[str, Any]) -> bool:
    parts = clean_text(scholar.get("name")).split()
    last_name = parts[-1].lower() if parts else ""
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
def rank_by_subfield(
    scholars_by_id: dict[str, Any],
) -> tuple[list[tuple[dict[str, Any], float]], set[str], set[str]]:
    matches: list[tuple[dict[str, Any], float]] = []
    filter_kept_ids: set[str] = set()
    filter_dropped_ids: set[str] = set()

    for raw_scholar in scholars_by_id.values():
        scholar = dict(raw_scholar)
        name = scholar.get("name")
        scholar["name"] = NAME_CORRECTIONS.get(name.strip(), name) if isinstance(name, str) else name
        papers = [dict(paper) for paper in scholar.get("papers") or []]
        for paper in papers:
            paper["abstract"] = apply_abstract_fixups(paper.get("abstract"))
        scholar_id = clean_text(scholar.get("id"))
        if scholar_id in FIRST_LAST_FILTER_IDS:
            papers = [paper for paper in papers if first_last_author_matches(scholar, paper)]
            scholar["papers"] = papers
            if scholar.get("papers"):
                filter_kept_ids.add(scholar_id)
            else:
                filter_dropped_ids.add(scholar_id)
                continue
        else:
            scholar["papers"] = papers

        score = None
        for entry in scholar.get("subfields") or []:
            if entry.get("subfield") == TARGET_SUBFIELD:
                try:
                    score = float(entry.get("score"))
                except (TypeError, ValueError):
                    score = 0.0
                break
        if score is not None:
            matches.append((scholar, score))

    matches.sort(
        key=lambda item: (
            -item[1],
            -(item[0].get("total_citations") or 0),
            clean_text(item[0].get("name")),
        )
    )
    return matches, filter_kept_ids, filter_dropped_ids


def dedup_researchers(
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
            _name_key(scholar.get("name")),
            clean_text(scholar.get("institution")).lower(),
        )
        lab_citations_key = (
            _dedup_value(scholar.get("institution")),
            _dedup_value(scholar.get("lab_name")),
            _dedup_value(scholar.get("total_citations")),
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
