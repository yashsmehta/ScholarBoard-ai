"""Shared text normalization helpers for persona generation."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from .config import ABSTRACT_FIXUPS, NAME_CORRECTIONS


def is_blank(value: Any) -> bool:
    """Return whether a value should be treated as absent."""
    return value is None or (isinstance(value, str) and not value.strip())


def clean_text(value: Any) -> str:
    """Normalize user-visible text without changing semantic content."""
    if is_blank(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\bsubfields?\b", "research areas", text, flags=re.IGNORECASE)
    text = re.sub(r"\bprimary_subfield\b", "primary research area", text)
    text = re.sub(r"\bresearch_direction\b", "research direction", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def apply_name_correction(name: Any) -> Any:
    """Apply known source-data name corrections."""
    if not isinstance(name, str):
        return name
    return NAME_CORRECTIONS.get(name.strip(), name)


def apply_abstract_fixups(abstract: Any) -> Any:
    """Apply known source-data abstract corrections."""
    if not isinstance(abstract, str):
        return abstract
    for find, replace in ABSTRACT_FIXUPS:
        abstract = abstract.replace(find, replace)
    return abstract


def name_slug(name: str) -> str:
    """Convert a scholar name into the persona filename slug."""
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name.lower())
    return re.sub(r"_+", "_", slug).strip("_")


def normalized_for_substring(value: Any) -> str:
    """Normalize text for case-insensitive containment checks."""
    return re.sub(r"\s+", " ", clean_text(value).lower()).strip()


def normalized_name(value: Any) -> str:
    """Normalize a scholar name for duplicate detection."""
    text = unicodedata.normalize("NFKD", clean_text(value))
    text = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.ASCII)
    return re.sub(r"\s+", " ", text).strip()


def dedup_value(value: Any) -> Any:
    """Normalize one field used in duplicate-detection keys."""
    if is_blank(value):
        return None
    return clean_text(value) if isinstance(value, str) else value


def scalar(value: Any) -> Any:
    """Return None for blank frontmatter fields."""
    if is_blank(value):
        return None
    return value


def authors_text(authors: Any) -> str:
    """Render paper authors into a normalized comma-separated string."""
    if is_blank(authors):
        return ""
    if isinstance(authors, list):
        return clean_text(", ".join(str(author) for author in authors if not is_blank(author)))
    return clean_text(authors)


def citation_count(value: Any) -> int | None:
    """Parse a citation count when present."""
    if is_blank(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def norm_title(title: Any) -> str:
    """Normalize a paper title for duplicate comparisons."""
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())
