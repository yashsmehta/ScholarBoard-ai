"""OpenAlex lookups used to top up sparse paper lists."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Any

from .config import MAILTO, OPENALEX_BASE, TOP_UP_MIN_PAPERS
from .utils import clean_text, norm_title


AUTHOR_ID_CACHE: dict[tuple[str, str], str | None] = {}


def openalex_get(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Fetch a JSON payload from OpenAlex with minimal retry handling."""
    query = urllib.parse.urlencode({**params, "mailto": MAILTO})
    url = f"{OPENALEX_BASE}{endpoint}?{query}"
    for attempt in range(3):
        time.sleep(0.1)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or 500 <= exc.code < 600:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
            print(f"warning: OpenAlex request failed ({exc.code}) for {endpoint}", file=sys.stderr)
            return None
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 2:
                time.sleep(2**attempt)
                continue
            print(f"warning: OpenAlex request failed for {endpoint}: {exc}", file=sys.stderr)
            return None
    return None


def institution_match_score(left: Any, right: Any) -> float:
    """Score two institution strings for OpenAlex author disambiguation."""
    left_text = clean_text(left).lower()
    right_text = clean_text(right).lower()
    if not left_text or not right_text:
        return 0.0
    return SequenceMatcher(None, left_text, right_text).ratio()


def resolve_openalex_author_id(scholar: dict[str, Any]) -> str | None:
    """Resolve a scholar to an OpenAlex author id using institution matching."""
    name = clean_text(scholar.get("name"))
    institution = clean_text(scholar.get("institution"))
    cache_key = (name.lower(), institution.lower())
    if cache_key in AUTHOR_ID_CACHE:
        return AUTHOR_ID_CACHE[cache_key]

    if not name or not institution:
        AUTHOR_ID_CACHE[cache_key] = None
        return None

    data = openalex_get("/authors", {"search": name, "per-page": "25"})
    if not data:
        AUTHOR_ID_CACHE[cache_key] = None
        return None

    best_author_id: str | None = None
    best_score = 0.0
    for result in data.get("results") or []:
        candidate_institutions = [
            (result.get("last_known_institution") or {}).get("display_name")
        ]
        candidate_institutions.extend(
            (affiliation.get("institution") or {}).get("display_name")
            for affiliation in result.get("affiliations", [])
        )
        score = max(
            (
                institution_match_score(institution, candidate_institution)
                for candidate_institution in candidate_institutions
            ),
            default=0.0,
        )
        if score > best_score:
            best_score = score
            best_author_id = str(result.get("id") or "").strip().rsplit("/", 1)[-1]

    if best_score < 0.5:
        AUTHOR_ID_CACHE[cache_key] = None
        return None

    AUTHOR_ID_CACHE[cache_key] = best_author_id
    return best_author_id


def reconstruct_abstract(inv: Any) -> str:
    """Rebuild OpenAlex inverted-index abstracts into normal text."""
    if not inv:
        return ""
    max_pos = max(max(positions) for positions in inv.values())
    words = [""] * (max_pos + 1)
    for word, positions in inv.items():
        for position in positions:
            if 0 <= position <= max_pos:
                words[position] = word
    return " ".join(word for word in words if word)


def openalex_work_to_paper(work: dict[str, Any]) -> dict[str, str] | None:
    """Convert one OpenAlex work into the local paper shape."""
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    if not abstract:
        return None
    authors = ", ".join(
        clean_text((authorship.get("author") or {}).get("display_name"))
        for authorship in work.get("authorships", [])
        if authorship.get("author")
    )
    return {
        "title": work.get("title") or "",
        "abstract": abstract,
        "year": str(work.get("publication_year") or ""),
        "venue": ((work.get("primary_location") or {}).get("source") or {}).get(
            "display_name"
        )
        or "",
        "citations": str(work.get("cited_by_count") or 0),
        "authors": authors,
    }


def work_has_first_last_author(work: dict[str, Any], author_id: str) -> bool:
    """Return whether a work lists the author in first or last position."""
    for authorship in work.get("authorships", []):
        work_author_id = str((authorship.get("author") or {}).get("id") or "").rsplit(
            "/", 1
        )[-1]
        if (
            work_author_id == author_id
            and authorship.get("author_position") in {"first", "last"}
        ):
            return True
    return False


def fetch_openalex_first_last_papers(author_id: str) -> list[dict[str, str]]:
    """Fetch recent OpenAlex works where the author is first or last author."""
    data = openalex_get(
        "/works",
        {
            "filter": f"author.id:{author_id}",
            "per-page": "50",
            "sort": "publication_year:desc",
        },
    )
    if not data:
        return []
    papers = []
    for work in data.get("results") or []:
        if not work_has_first_last_author(work, author_id):
            continue
        paper = openalex_work_to_paper(work)
        if paper is not None:
            papers.append(paper)
    return papers


def top_up_papers(scholar: dict[str, Any]) -> tuple[list[dict[str, Any]], int, bool]:
    """Add OpenAlex papers until a scholar reaches the top-up threshold."""
    papers = list(scholar.get("papers") or [])
    needed = TOP_UP_MIN_PAPERS - len(papers)
    if needed <= 0:
        return papers, 0, True

    author_id = resolve_openalex_author_id(scholar)
    if not author_id:
        return papers, 0, False

    seen_titles = {norm_title(paper.get("title")) for paper in papers}
    additions: list[dict[str, Any]] = []
    for paper in fetch_openalex_first_last_papers(author_id):
        title_key = norm_title(paper.get("title"))
        if not title_key or title_key in seen_titles:
            continue
        additions.append(paper)
        seen_titles.add(title_key)
        if len(additions) >= needed:
            break

    combined = papers + additions
    combined.sort(key=lambda paper: clean_text(paper.get("year")), reverse=True)
    return combined, len(additions), True
