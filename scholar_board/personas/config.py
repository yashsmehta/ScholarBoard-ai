"""Configuration for Brain-AI Alignment persona generation."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SCHOLARS_JSON = PROJECT_ROOT / "data" / "build" / "scholars.json"
REMOTE_SCHOLARS_JSON = "https://yashsmehta.com/scholarboard/data/build/scholars.json"
OUTPUT_DIR = PROJECT_ROOT / "personas"

TARGET_SUBFIELD = "Brain-AI Alignment"
TOP_N = 100
MIN_PAPERS = 4
TOP_UP_MIN_PAPERS = 5

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
