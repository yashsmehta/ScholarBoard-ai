"""
Pydantic schemas for ScholarBoard.ai structured data.

Defines the canonical data models for scholars and papers.
Used for validation in build_scholars_json.py.
"""

from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator


class Paper(BaseModel):
    title: str
    abstract: Optional[str] = None
    year: Optional[str] = None
    venue: Optional[str] = None
    citations: Optional[str] = "0"
    authors: Optional[str] = None
    url: Optional[str] = None

    @field_validator("citations", "year", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if v is None:
            return None
        return str(v)


class UMAPProjection(BaseModel):
    x: float
    y: float


class SubfieldTag(BaseModel):
    subfield: str
    score: float


class ResearchIdea(BaseModel):
    research_thread: str
    open_question: str
    title: str
    hypothesis: str
    approach: str
    scientific_impact: str
    why_now: str


class Scholar(BaseModel):
    id: str
    name: str
    institution: Optional[str] = None
    department: Optional[str] = None
    lab_name: Optional[str] = None
    lab_url: Optional[str] = None
    main_research_area: Optional[str] = None
    bio: Optional[str] = None
    papers: list[Paper] = Field(default_factory=list)
    primary_subfield: Optional[str] = None
    subfields: list[SubfieldTag] = Field(default_factory=list)
    profile_pic: Optional[str] = None
    umap_projection: Optional[UMAPProjection] = None
    suggested_idea: Optional[ResearchIdea] = None
    cluster: Optional[int] = None
