from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TextValue
from app.utils.sanitize import sanitize_plain_text_value, sanitize_rich_text_value


class DiscussionMessageAuthor(BaseModel):
    name: str
    badge: TextValue

    @field_validator('badge', mode='before')
    @classmethod
    def sanitize_badge(cls, value):
        return sanitize_plain_text_value(value)


class DiscussionMessage(BaseModel):
    id: str
    author: DiscussionMessageAuthor
    text: TextValue
    createdAt: str

    @field_validator('text', mode='before')
    @classmethod
    def sanitize_text(cls, value):
        return sanitize_rich_text_value(value)


class DiscussionReplyCreate(BaseModel):
    text: TextValue

    @field_validator('text', mode='before')
    @classmethod
    def sanitize_text(cls, value):
        return sanitize_rich_text_value(value)


class DiscussionAuthor(BaseModel):
    name: str
    avatar: str
    title: TextValue

    @field_validator('title', mode='before')
    @classmethod
    def sanitize_title(cls, value):
        return sanitize_plain_text_value(value)


class DiscussionModel(BaseModel):
    slug: str
    title: TextValue
    category: TextValue
    createdAt: str
    author: DiscussionAuthor
    summary: TextValue
    content: TextValue
    messages: list[DiscussionMessage] = Field(default_factory=list)

    @field_validator('title', 'category', 'summary', mode='before')
    @classmethod
    def sanitize_plain_fields(cls, value):
        return sanitize_plain_text_value(value)

    @field_validator('content', mode='before')
    @classmethod
    def sanitize_content(cls, value):
        return sanitize_rich_text_value(value)
