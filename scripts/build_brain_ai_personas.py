"""Build markdown personas for top Brain-AI Alignment researchers."""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_SCHOLARS_JSON = PROJECT_ROOT / "data" / "build" / "scholars.json"
REMOTE_SCHOLARS_JSON = "https://yashsmehta.com/scholarboard/data/build/scholars.json"
OUTPUT_DIR = PROJECT_ROOT / "personas"
TARGET_SUBFIELD = "Brain-AI Alignment"
MAX_PERSONAS = 100
OPENALEX_BASE = "https://api.openalex.org"
MAILTO = "ymehta3@jh.edu"
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
AUTHOR_ID_CACHE: dict[tuple[str, str], str | None] = {}


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


def openalex_get(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
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
    left_text = clean_text(left).lower()
    right_text = clean_text(right).lower()
    if not left_text or not right_text:
        return 0.0
    return SequenceMatcher(None, left_text, right_text).ratio()


def resolve_openalex_author_id(scholar: dict[str, Any]) -> str | None:
    name = clean_text(scholar.get("name"))
    institution = clean_text(scholar.get("institution"))
    cache_key = (name.lower(), institution.lower())
    if cache_key in AUTHOR_ID_CACHE:
        return AUTHOR_ID_CACHE[cache_key]

    if not name or not institution:
        AUTHOR_ID_CACHE[cache_key] = None
        return None

    data = openalex_get(
        "/authors",
        {
            "search": name,
            "per-page": "25",
        },
    )
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
    if not inv:
        return ""
    max_pos = max(max(positions) for positions in inv.values())
    words = [""] * (max_pos + 1)
    for word, positions in inv.items():
        for position in positions:
            if 0 <= position <= max_pos:
                words[position] = word
    return " ".join(word for word in words if word)


def norm_title(title: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def openalex_work_to_paper(work: dict[str, Any]) -> dict[str, str] | None:
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
    papers = list(scholar.get("papers") or [])
    needed = 5 - len(papers)
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
    top_up_under_before = 0
    top_up_attempted = 0
    top_up_disambiguation_failed = 0
    top_up_reached = 0
    top_up_still_under_ids: list[str] = []

    for scholar, _score in top_matches:
        scholar_id = clean_text(scholar.get("id"))
        name = clean_text(scholar.get("name")) or "unknown_researcher"
        before_count = len(scholar.get("papers") or [])
        if before_count >= 5:
            continue

        top_up_under_before += 1
        top_up_attempted += 1
        papers, fetched_count, disambiguated = top_up_papers(scholar)
        scholar["papers"] = papers
        final_count = len(papers)
        if not disambiguated:
            top_up_disambiguation_failed += 1
        if final_count >= 5:
            top_up_reached += 1
        else:
            top_up_still_under_ids.append(scholar_id)
        print(
            f"top-up {scholar_id} {name}: had {before_count} papers "
            f"→ fetched {fetched_count} from OpenAlex → final {final_count} papers"
        )

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
    print("=== Top-up summary ===")
    print(f"Scholars under 5 papers (before): {top_up_under_before}")
    print(f"Top-up attempted: {top_up_attempted}")
    print(
        "Could not disambiguate OpenAlex author: "
        f"{top_up_disambiguation_failed}"
    )
    print(f"Reached >=5 papers: {top_up_reached}")
    still_under = ", ".join(top_up_still_under_ids)
    print(
        f"Still under 5 papers (final): {len(top_up_still_under_ids)}"
        f"  (these scholars: {still_under})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
