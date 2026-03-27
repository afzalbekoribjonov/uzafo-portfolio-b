from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TextValue
from app.schemas.content import ContentBlock
from app.utils.sanitize import sanitize_plain_text_value


class PostAuthor(BaseModel):
    name: str
    role: TextValue

    @field_validator('role', mode='before')
    @classmethod
    def sanitize_role(cls, value):
        return sanitize_plain_text_value(value)


class BlogComment(BaseModel):
    id: str
    author: str
    message: TextValue
    createdAt: str | None = None

    @field_validator('message', mode='before')
    @classmethod
    def sanitize_message(cls, value):
        return sanitize_plain_text_value(value)


class BlogPostModel(BaseModel):
    slug: str
    title: TextValue
    excerpt: TextValue
    cover: str = ''
    coverMediaId: str | None = None
    publishedAt: str
    author: PostAuthor
    readingTime: int = Field(ge=1, default=1)
    likes: int = Field(ge=0, default=0)
    dislikes: int = Field(ge=0, default=0)
    featured: bool = False
    blocks: list[ContentBlock] = Field(default_factory=list)
    comments: list[BlogComment] = Field(default_factory=list)

    @field_validator('title', 'excerpt', mode='before')
    @classmethod
    def sanitize_text_fields(cls, value):
        return sanitize_plain_text_value(value)
