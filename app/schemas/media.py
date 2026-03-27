from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


OwnerType = Literal['site', 'profile', 'resume', 'project', 'post', 'discussion']
RoleType = Literal['cover', 'gallery', 'content', 'avatar', 'document']
ResourceType = Literal['image', 'video', 'raw']


class MediaUploadAuthRequest(BaseModel):
    fileName: str = Field(min_length=1, max_length=200)
    contentType: str = Field(min_length=1, max_length=120)
    sizeBytes: int = Field(gt=0)
    ownerType: OwnerType
    ownerSlug: str | None = None
    role: RoleType = 'content'
    isPrivateFile: bool = False


class MediaUploadAuthResponse(BaseModel):
    sessionId: str
    publicKey: str
    urlEndpoint: str
    token: str
    signature: str
    expire: int
    fileName: str
    folder: str
    tags: list[str]
    isPrivateFile: bool


class MediaCompleteRequest(BaseModel):
    sessionId: str
    fileId: str
    filePath: str
    name: str
    url: str
    thumbnailUrl: str | None = None
    size: int = 0
    fileType: str | None = None
    height: int | None = None
    width: int | None = None
    duration: float | None = None


class MediaAsset(BaseModel):
    id: str
    provider: Literal['imagekit'] = 'imagekit'
    fileId: str
    filePath: str
    fileName: str
    url: str
    thumbnailUrl: str | None = None
    resourceType: ResourceType
    mimeType: str | None = None
    sizeBytes: int = 0
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    folder: str
    tags: list[str] = Field(default_factory=list)
    ownerType: OwnerType
    ownerSlug: str | None = None
    role: RoleType
    isPrivate: bool = False
    createdBy: str
    status: Literal['ready', 'deleted'] = 'ready'
    createdAt: str
    updatedAt: str
