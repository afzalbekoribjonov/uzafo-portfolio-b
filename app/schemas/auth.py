from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import AuthUser, TokenPair


class LoginResponse(TokenPair):
    user: AuthUser


class RefreshRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str
