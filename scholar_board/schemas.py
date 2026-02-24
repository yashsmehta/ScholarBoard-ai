"""
Pydantic schemas for ScholarBoard.ai structured data.

Defines the canonical data models for scholars, papers, and education.
Used for validation in build_scholars_json.py and parse_raw_to_json.py.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Paper(BaseModel):
    title: str
    abstract: Optional[str] = None
    year: Optional[str] = None
    venue: Optional[str] = None
    citations: Optional[int] = 0
    authors: Optional[str] = None
    last_author: Optional[str] = None
    url: Optional[str] = None


class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    field: Optional[str] = None
    advisor: Optional[str] = None


class UMAPProjection(BaseModel):
    x: float
    y: float


class Scholar(BaseModel):
    id: str
    name: str
    institution: Optional[str] = None
    department: Optional[str] = None
    lab_name: Optional[str] = None
    research_areas: list[str] = Field(default_factory=list)
    bio: Optional[str] = None
    education: list[Education] = Field(default_factory=list)
    papers: list[Paper] = Field(default_factory=list)
    profile_pic: Optional[str] = None
    umap_projection: Optional[UMAPProjection] = None
    cluster: Optional[int] = None
