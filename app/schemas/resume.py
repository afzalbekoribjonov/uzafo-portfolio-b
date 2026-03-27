from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TextValue
from app.utils.sanitize import sanitize_plain_text_value


class ResumeExperience(BaseModel):
    company: str
    role: TextValue
    period: str
    highlights: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator('role', mode='before')
    @classmethod
    def sanitize_role(cls, value):
        return sanitize_plain_text_value(value)


class ResumeEducation(BaseModel):
    institution: str
    degree: TextValue
    period: str

    @field_validator('degree', mode='before')
    @classmethod
    def sanitize_degree(cls, value):
        return sanitize_plain_text_value(value)


class ResumeAward(BaseModel):
    title: TextValue
    description: TextValue

    @field_validator('title', 'description', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)


class ResumeModel(BaseModel):
    headline: TextValue
    summary: TextValue
    experience: list[ResumeExperience] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    skills: dict[str, list[str]] = Field(default_factory=dict)
    awards: list[ResumeAward] = Field(default_factory=list)

    @field_validator('headline', 'summary', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)
