from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TextValue
from app.utils.sanitize import sanitize_plain_text_value


class SocialLink(BaseModel):
    name: str
    href: str


class SiteModel(BaseModel):
    brand: str
    tagline: TextValue
    socials: list[SocialLink] = Field(default_factory=list)
    resumePdf: str
    status: TextValue

    @field_validator('tagline', 'status', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)
