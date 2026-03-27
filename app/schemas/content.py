from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.common import TextValue
from app.utils.sanitize import sanitize_plain_text_value, sanitize_rich_text_value


class ContentTextBlock(BaseModel):
    id: str
    type: Literal['richText', 'quote']
    content: TextValue

    @field_validator('content', mode='before')
    @classmethod
    def sanitize_content(cls, value):
        return sanitize_rich_text_value(value)


class ContentCodeBlock(BaseModel):
    id: str
    type: Literal['code']
    language: str = 'txt'
    content: TextValue

    @field_validator('content', mode='before')
    @classmethod
    def sanitize_content(cls, value):
        return sanitize_plain_text_value(value)


class ContentImageBlock(BaseModel):
    id: str
    type: Literal['image']
    src: str = ''
    alt: TextValue = ''
    mediaId: str | None = None

    @field_validator('alt', mode='before')
    @classmethod
    def sanitize_alt(cls, value):
        return sanitize_plain_text_value(value)


class ContentVideoBlock(BaseModel):
    id: str
    type: Literal['video']
    src: str = ''
    caption: TextValue = ''
    mediaId: str | None = None

    @field_validator('caption', mode='before')
    @classmethod
    def sanitize_caption(cls, value):
        return sanitize_plain_text_value(value)


ContentBlock = ContentTextBlock | ContentCodeBlock | ContentImageBlock | ContentVideoBlock
