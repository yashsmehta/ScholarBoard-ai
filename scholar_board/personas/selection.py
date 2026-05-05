"""Ranking, filtering, and deduplication for persona candidates."""

from __future__ import annotations

from typing import Any

from .config import CANONICAL_DUPLICATE_IDS, FIRST_LAST_FILTER_IDS, TARGET_SUBFIELD
from .utils import (
    apply_abstract_fixups,
    apply_name_correction,
    authors_text,
    clean_text,
    dedup_value,
    normalized_name,
)


def brain_ai_score(scholar: dict[str, Any]) -> float | None:
    """Return a scholar's Brain-AI Alignment score when present."""
    for entry in scholar.get("subfields") or []:
        if entry.get("subfield") == TARGET_SUBFIELD:
            try:
                return float(entry.get("score"))
            except (TypeError, ValueError):
                return 0.0
    return None


def scholar_last_name(name: Any) -> str:
    """Extract a normalized last name for first/last-author filtering."""
    parts = clean_text(name).split()
    return parts[-1].lower() if parts else ""


def first_last_author_matches(scholar: dict[str, Any], paper: dict[str, Any]) -> bool:
    """Return whether the scholar appears as first or last paper author."""
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
    """Apply source-data corrections and targeted first/last-author filtering."""
    scholar = dict(raw_scholar)
    scholar["name"] = apply_name_correction(scholar.get("name"))
    papers = [dict(paper) for paper in scholar.get("papers") or []]
    for paper in papers:
        paper["abstract"] = apply_abstract_fixups(paper.get("abstract"))
    if clean_text(scholar.get("id")) in FIRST_LAST_FILTER_IDS:
        papers = [paper for paper in papers if first_last_author_matches(scholar, paper)]
    scholar["papers"] = papers
    return scholar


def rank_by_subfield(
    scholars_by_id: dict[str, Any],
) -> tuple[list[tuple[dict[str, Any], float]], set[str], set[str]]:
    """Rank all Brain-AI Alignment scholars by score and citation tiebreakers."""
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
    return matches, filter_kept_ids, filter_dropped_ids


def dedup_researchers(
    matches: list[tuple[dict[str, Any], float]],
) -> tuple[list[tuple[dict[str, Any], float]], int]:
    """Drop duplicate scholars while preserving ranked order."""
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
