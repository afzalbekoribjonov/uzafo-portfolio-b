from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TextValue
from app.schemas.content import ContentBlock
from app.utils.sanitize import sanitize_plain_text_value


class ProjectMetric(BaseModel):
    label: TextValue
    value: str

    @field_validator('label', mode='before')
    @classmethod
    def sanitize_label(cls, value):
        return sanitize_plain_text_value(value)


class ProjectLink(BaseModel):
    id: str
    label: str
    href: str


class ProjectModel(BaseModel):
    slug: str
    title: TextValue
    excerpt: TextValue
    description: TextValue
    year: str
    status: TextValue
    cover: str = ''
    coverMediaId: str | None = None
    tags: list[str] = Field(default_factory=list)
    metrics: list[ProjectMetric] = Field(default_factory=list)
    links: list[ProjectLink] = Field(default_factory=list)
    content: list[ContentBlock] = Field(default_factory=list)

    @field_validator('title', 'excerpt', 'description', 'status', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)
