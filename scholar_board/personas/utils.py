from __future__ import annotations

import re
from typing import Any

from .config import ABSTRACT_FIXUPS


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def clean_text(value: Any) -> str:
    if _blank(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\bsubfields?\b", "research areas", text, flags=re.IGNORECASE)
    text = re.sub(r"\bprimary_subfield\b", "primary research area", text)
    text = re.sub(r"\bresearch_direction\b", "research direction", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def apply_abstract_fixups(abstract: Any) -> Any:
    if not isinstance(abstract, str):
        return abstract
    for find, replace in ABSTRACT_FIXUPS:
        abstract = abstract.replace(find, replace)
    return abstract


def authors_text(authors: Any) -> str:
    if _blank(authors):
        return ""
    if isinstance(authors, list):
        return clean_text(", ".join(str(author) for author in authors if not _blank(author)))
    return clean_text(authors)
