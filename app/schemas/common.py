from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class LocalizedText(BaseModel):
    uz: str = ''
    en: str = ''


TextValue = str | LocalizedText
Locale = Literal['uz', 'en']

SlugStr = Annotated[str, Field(min_length=1, max_length=160)]


class ApiListResponse(BaseModel):
    items: list
    total: int


class MessageResponse(BaseModel):
    message: str


class TimestampedModel(BaseModel):
    createdAt: str | None = None
    updatedAt: str | None = None


class LinkItem(BaseModel):
    name: str
    href: str


class PaginationResponse(BaseModel):
    total: int


class TokenPair(BaseModel):
    accessToken: str
    accessTokenExpiresAt: str
    refreshToken: str
    refreshTokenExpiresAt: str


class AuthUser(BaseModel):
    id: str
    email: str
    name: str
    role: Literal['admin', 'user']


class ErrorResponse(BaseModel):
    detail: str
