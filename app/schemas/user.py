from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserDoc(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal['admin', 'user'] = 'user'
    passwordHash: str
    isActive: bool = True
    createdAt: str
    updatedAt: str


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Literal['admin', 'user'] = 'user'
