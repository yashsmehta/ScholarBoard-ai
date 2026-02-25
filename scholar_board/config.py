"""Shared path constants and helpers for ScholarBoard.ai.

Import from here to get consistent PROJECT_ROOT-relative paths across
all pipeline modules, along with API key accessors and common CSV helpers.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
PIPELINE_DIR = DATA_DIR / "pipeline"
BUILD_DIR = DATA_DIR / "build"

# Source inputs
CSV_PATH = SOURCE_DIR / "vss_data.csv"
EXTRA_RESEARCHERS_PATH = SOURCE_DIR / "extra_researchers.csv"
SUBFIELDS_DEF_PATH = SOURCE_DIR / "subfields.json"

# Pipeline intermediates
PAPERS_DIR = PIPELINE_DIR / "scholar_papers"
PROFILES_DIR = PIPELINE_DIR / "scholar_profiles"
IDEAS_DIR = PIPELINE_DIR / "scholar_ideas"
EMBEDDINGS_PATH = PIPELINE_DIR / "scholar_embeddings.nc"
SUBFIELDS_PATH = PIPELINE_DIR / "scholar_subfields.json"
MODELS_DIR = PIPELINE_DIR / "models"
UMAP_MODEL_PATH = MODELS_DIR / "umap_model.joblib"
HDBSCAN_MODEL_PATH = MODELS_DIR / "umap_hdbscan.joblib"
SCALER_PATH = MODELS_DIR / "scaler.joblib"

# Build outputs
SCHOLARS_JSON = BUILD_DIR / "scholars.json"
SCHOLARS_DIR = BUILD_DIR / "scholars"
PICS_DIR = BUILD_DIR / "profile_pics"

# Consolidated database
DB_PATH = DATA_DIR / "scholarboard.db"

load_dotenv(PROJECT_ROOT / ".env")


def get_gemini_api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        print("Error: GOOGLE_API_KEY (or GEMINI_API_KEY) not found in .env")
        sys.exit(1)
    return key


def get_serper_api_key() -> str | None:
    return os.getenv("SERPER_API_KEY")


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return key


def load_scholars_csv() -> list[dict]:
    """Load unique scholars from vss_data.csv (+ extra_researchers.csv if present).

    Returns a list of dicts with keys: scholar_id, scholar_name,
    scholar_institution, scholar_department (None if not present).
    Extra researchers (E-prefixed IDs) are appended after VSS scholars,
    deduplicated by name.
    """
    import pandas as pd

    df = pd.read_csv(CSV_PATH)
    cols = ["scholar_id", "scholar_name", "scholar_institution"]
    if "scholar_department" in df.columns:
        cols.append("scholar_department")
    unique = df.drop_duplicates(subset="scholar_id")[cols].copy()
    unique["scholar_id"] = unique["scholar_id"].astype(str).str.zfill(4)
    if "scholar_department" not in unique.columns:
        unique["scholar_department"] = None

    if EXTRA_RESEARCHERS_PATH.exists():
        extra = pd.read_csv(EXTRA_RESEARCHERS_PATH)
        vss_names = set(unique["scholar_name"].str.lower().str.strip())
        extra = extra[~extra["scholar_name"].str.lower().str.strip().isin(vss_names)].copy()
        if "scholar_department" not in extra.columns:
            extra["scholar_department"] = None
        unique = pd.concat(
            [unique, extra[["scholar_id", "scholar_name", "scholar_institution", "scholar_department"]]],
            ignore_index=True,
        )

    return unique.to_dict("records")


def load_paper_texts(scholar_id: str) -> str | None:
    """Load concatenated paper titles + abstracts for a scholar (top 5 papers)."""
    for fpath in PAPERS_DIR.glob(f"{scholar_id}_*.json"):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            papers = data.get("papers", [])
            if not papers:
                return None
            parts = []
            for p in papers[:5]:
                title = p.get("title", "")
                abstract = p.get("abstract", "")
                if title:
                    text = title
                    if abstract:
                        text += ". " + abstract
                    parts.append(text)
            return " ".join(parts) if parts else None
        except (json.JSONDecodeError, KeyError):
            continue
    return None
