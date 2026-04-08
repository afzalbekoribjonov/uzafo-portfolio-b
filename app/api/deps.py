from __future__ import annotations

from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.rate_limit import limit_request
from app.core.security import decode_token
from app.db.mongo import get_db

async def get_optional_user(authorization: str | None = Header(default=None)) -> dict[str, Any] | None:
    if not authorization or not authorization.startswith('Bearer '):
        return None
    token = authorization.removeprefix('Bearer ').strip()
    try:
        payload = decode_token(token, expected_type='access')
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid access token.') from exc
    db = get_db()
    user = await db.users.find_one({'_id': payload['sub'], 'isActive': True})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found.')
    return user




async def require_user(user: dict[str, Any] | None = Depends(get_optional_user)) -> dict[str, Any]:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
    return user


async def require_admin(user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    if user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin access required.')
    return user


async def login_rate_limit(request: Request) -> None:
    await limit_request(request, scope='login', limit=5, per_seconds=60)


async def register_rate_limit(request: Request) -> None:
    await limit_request(request, scope='register', limit=5, per_seconds=60)


async def upload_rate_limit(request: Request) -> None:
    await limit_request(request, scope='upload_auth', limit=20, per_seconds=60)
