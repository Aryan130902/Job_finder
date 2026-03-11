"""
Resume Domain Models

"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from uuid import uuid4


class Skill(BaseModel):
    name: str
    category: Optional[str] = None


class Experience(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    duration: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: List[str] = Field(default_factory=list)
    bullet_points: List[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    bullet_points: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    tech_stack: Optional[str] = None


class Education(BaseModel):
    institution: str
    degree: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[str] = None
    cgpa: Optional[str] = None
    year: Optional[str] = None


class Resume(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

    skills: List[Skill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)

    raw_text: Optional[str] = None
    raw_latex: Optional[str] = None


class ResumeEmbeddingMetadata(BaseModel):
    resume_id: str
    section: str
    content_type: str
    content_id: str
