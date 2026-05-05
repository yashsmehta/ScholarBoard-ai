"""Orchestrate persona selection, top-up, rendering, and file writes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import (
    FIRST_LAST_FILTER_IDS,
    MIN_PAPERS,
    OUTPUT_DIR,
    TARGET_SUBFIELD,
    TOP_N,
    TOP_UP_MIN_PAPERS,
)
from .data import load_scholars
from .openalex import top_up_papers
from .render import render_persona
from .selection import dedup_researchers, rank_by_subfield
from .utils import clean_text, name_slug


@dataclass(frozen=True)
class TopupSummary:
    """Summary statistics for OpenAlex paper top-ups."""

    min_papers: int
    under_before: int
    attempted: int
    disambiguation_failed: int
    reached_min: int
    under_after: list[str]


@dataclass(frozen=True)
class BuildResult:
    """Summary statistics for a persona build."""

    target_subfield: str
    candidates_count: int
    dedup_dropped: int
    first_last_kept: int
    first_last_total: int
    first_last_dropped: int
    score_min: float
    score_max: float
    files_written: int
    topup_summary: TopupSummary


@dataclass
class _TopupCounters:
    under_before: int = 0
    attempted: int = 0
    disambiguation_failed: int = 0
    reached_min: int = 0
    under_after: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable counter fields."""
        if self.under_after is None:
            self.under_after = []


def _persona_path(scholar: dict[str, Any]) -> Path:
    """Return the markdown path for a scholar persona."""
    scholar_id = clean_text(scholar.get("id"))
    name = clean_text(scholar.get("name")) or "unknown_researcher"
    return OUTPUT_DIR / f"{scholar_id}_{name_slug(name)}.md"


def _maybe_top_up(scholar: dict[str, Any], counters: _TopupCounters) -> None:
    """Top up one scholar's papers when below the top-up threshold."""
    scholar_id = clean_text(scholar.get("id"))
    name = clean_text(scholar.get("name")) or "unknown_researcher"
    before_count = len(scholar.get("papers") or [])
    if before_count >= TOP_UP_MIN_PAPERS:
        return

    counters.under_before += 1
    counters.attempted += 1
    papers, fetched_count, disambiguated = top_up_papers(scholar)
    scholar["papers"] = papers
    final_count = len(papers)
    if not disambiguated:
        counters.disambiguation_failed += 1
    if final_count >= TOP_UP_MIN_PAPERS:
        counters.reached_min += 1
    else:
        counters.under_after.append(scholar_id)
    print(
        f"top-up {scholar_id} {name}: had {before_count} papers "
        f"→ fetched {fetched_count} from OpenAlex → final {final_count} papers"
    )


def _select_top_matches(
    deduped_matches: list[tuple[dict[str, Any], float]],
) -> tuple[list[tuple[dict[str, Any], float]], TopupSummary]:
    """Select top scholars after top-up and minimum-paper filtering."""
    top_matches: list[tuple[dict[str, Any], float]] = []
    counters = _TopupCounters()

    for scholar, score in deduped_matches:
        _maybe_top_up(scholar, counters)
        if len(scholar.get("papers") or []) < MIN_PAPERS:
            continue
        top_matches.append((scholar, score))
        if len(top_matches) >= TOP_N:
            break

    summary = TopupSummary(
        min_papers=TOP_UP_MIN_PAPERS,
        under_before=counters.under_before,
        attempted=counters.attempted,
        disambiguation_failed=counters.disambiguation_failed,
        reached_min=counters.reached_min,
        under_after=list(counters.under_after or []),
    )
    return top_matches, summary


def _write_personas(top_matches: list[tuple[dict[str, Any], float]]) -> int:
    """Write selected personas and remove stale markdown files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intended_paths = {_persona_path(scholar) for scholar, _score in top_matches}
    for existing_path in OUTPUT_DIR.glob("*.md"):
        if existing_path not in intended_paths:
            existing_path.unlink()

    for scholar, _score in top_matches:
        _persona_path(scholar).write_text(render_persona(scholar), encoding="utf-8")
    return len(top_matches)


def build_personas() -> BuildResult:
    """Build persona markdown files and return summary statistics."""
    matches, filter_kept_ids, filter_dropped_ids = rank_by_subfield(load_scholars())
    deduped_matches, dedup_dropped_count = dedup_researchers(matches)
    top_matches, topup_summary = _select_top_matches(deduped_matches)
    files_written = _write_personas(top_matches)

    scores = [score for _scholar, score in top_matches]
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    return BuildResult(
        target_subfield=TARGET_SUBFIELD,
        candidates_count=len(matches),
        dedup_dropped=dedup_dropped_count,
        first_last_kept=len(filter_kept_ids),
        first_last_total=len(FIRST_LAST_FILTER_IDS),
        first_last_dropped=len(filter_dropped_ids),
        score_min=min_score,
        score_max=max_score,
        files_written=files_written,
        topup_summary=topup_summary,
    )
