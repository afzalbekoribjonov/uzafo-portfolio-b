from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import TextValue
from app.utils.sanitize import sanitize_plain_text_value


class TechCategory(BaseModel):
    key: str
    title: TextValue
    items: list[str] = Field(default_factory=list)

    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, value):
        return sanitize_plain_text_value(value)


class SkillMetric(BaseModel):
    name: str
    level: int = Field(ge=0, le=100)


class TimelineItem(BaseModel):
    year: str
    title: TextValue
    description: TextValue

    @field_validator('title', 'description', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)


class StatItem(BaseModel):
    label: TextValue
    value: str

    @field_validator('label', mode='before')
    @classmethod
    def sanitize_label(cls, value):
        return sanitize_plain_text_value(value)


class UniversityInfo(BaseModel):
    name: str
    degree: TextValue

    @field_validator('degree', mode='before')
    @classmethod
    def sanitize_degree(cls, value):
        return sanitize_plain_text_value(value)


class ProfileModel(BaseModel):
    name: str
    tagline: TextValue
    summary: TextValue
    location: str
    email: EmailStr
    availability: TextValue
    university: UniversityInfo
    experienceYears: int = Field(ge=0)
    techCategories: list[TechCategory] = Field(default_factory=list)
    skillMetrics: list[SkillMetric] = Field(default_factory=list)
    timeline: list[TimelineItem] = Field(default_factory=list)
    stats: list[StatItem] = Field(default_factory=list)

    @field_validator('tagline', 'summary', 'availability', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)
