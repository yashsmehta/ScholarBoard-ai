from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import FIRST_LAST_FILTER_IDS, LOCAL_SCHOLARS_JSON, MIN_PAPERS, OUTPUT_DIR, REMOTE_SCHOLARS_JSON, TARGET_SUBFIELD, TOP_N, TOP_UP_MIN_PAPERS
from .openalex import top_up_papers
from .render import render_persona
from .selection import dedup_researchers, rank_by_subfield
from .utils import clean_text


@dataclass(frozen=True)
class TopupSummary:
    min_papers: int; under_before: int; attempted: int; disambiguation_failed: int; reached_min: int; under_after: list[str]


@dataclass(frozen=True)
class BuildResult:
    target_subfield: str; candidates_count: int; dedup_dropped: int; first_last_kept: int; first_last_total: int
    first_last_dropped: int; score_min: float; score_max: float; files_written: int; topup_summary: TopupSummary


def load_scholars() -> dict[str, Any]:
    if LOCAL_SCHOLARS_JSON.exists():
        with LOCAL_SCHOLARS_JSON.open(encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(REMOTE_SCHOLARS_JSON, timeout=60) as response:
        return json.load(response)


def _persona_path(scholar: dict[str, Any]) -> Path:
    scholar_id = clean_text(scholar.get("id"))
    name = clean_text(scholar.get("name")) or "unknown_researcher"
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", ascii_name.lower())).strip("_")
    return OUTPUT_DIR / f"{scholar_id}_{slug}.md"


def _select_top_matches(
    deduped_matches: list[tuple[dict[str, Any], float]],
) -> tuple[list[tuple[dict[str, Any], float]], TopupSummary]:
    top_matches: list[tuple[dict[str, Any], float]] = []
    under_before = attempted = disambiguation_failed = reached_min = 0
    under_after: list[str] = []

    for scholar, score in deduped_matches:
        scholar_id = clean_text(scholar.get("id"))
        before_count = len(scholar.get("papers") or [])
        if before_count < TOP_UP_MIN_PAPERS:
            under_before += 1
            attempted += 1
            papers, fetched_count, disambiguated = top_up_papers(scholar)
            scholar["papers"] = papers
            final_count = len(papers)
            disambiguation_failed += 0 if disambiguated else 1
            if final_count >= TOP_UP_MIN_PAPERS:
                reached_min += 1
            else:
                under_after.append(scholar_id)
            name = clean_text(scholar.get("name")) or "unknown_researcher"
            print(
                f"top-up {scholar_id} {name}: had {before_count} papers "
                f"→ fetched {fetched_count} from OpenAlex → final {final_count} papers"
            )
        if len(scholar.get("papers") or []) < MIN_PAPERS:
            continue
        top_matches.append((scholar, score))
        if len(top_matches) >= TOP_N:
            break

    return top_matches, TopupSummary(
        min_papers=TOP_UP_MIN_PAPERS,
        under_before=under_before,
        attempted=attempted,
        disambiguation_failed=disambiguation_failed,
        reached_min=reached_min,
        under_after=under_after,
    )


def build_personas() -> BuildResult:
    matches, filter_kept_ids, filter_dropped_ids = rank_by_subfield(load_scholars())
    deduped_matches, dedup_dropped_count = dedup_researchers(matches)
    top_matches, topup_summary = _select_top_matches(deduped_matches)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intended_paths = {_persona_path(scholar) for scholar, _score in top_matches}
    for existing_path in OUTPUT_DIR.glob("*.md"):
        if existing_path not in intended_paths:
            existing_path.unlink()
    for scholar, _score in top_matches:
        _persona_path(scholar).write_text(render_persona(scholar), encoding="utf-8")

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
        files_written=len(top_matches),
        topup_summary=topup_summary,
    )
