from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_optional_user, login_rate_limit, register_rate_limit
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.db.mongo import get_db
from app.schemas.auth import LoginResponse, LogoutRequest, RefreshRequest
from app.schemas.common import AuthUser, MessageResponse
from app.schemas.user import UserCreate, UserLogin
from app.services.audit_service import write_audit
from app.utils.helpers import make_id, now_iso

router = APIRouter(prefix='/api/auth')


@router.post('/register', response_model=LoginResponse, dependencies=[Depends(register_rate_limit)])
async def register(payload: UserCreate):
    db = get_db()
    email = payload.email.lower()
    if await db.users.find_one({'email': email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already exists.')

    now = now_iso()
    user_id = make_id('user')
    user_doc = {
        '_id': user_id,
        'id': user_id,
        'name': payload.name,
        'email': email,
        'role': 'user',
        'passwordHash': hash_password(payload.password),
        'isActive': True,
        'createdAt': now,
        'updatedAt': now,
    }
    await db.users.insert_one(user_doc)

    access_token, access_expires = create_access_token(user_id, 'user')
    refresh_token, refresh_jti, refresh_expires = create_refresh_token(user_id)
    await db.refresh_tokens.insert_one({
        '_id': refresh_jti,
        'userId': user_id,
        'expiresAt': refresh_expires,
        'createdAt': now,
    })
    await write_audit('auth.register', user_id, {'email': email})
    return LoginResponse(
        accessToken=access_token,
        accessTokenExpiresAt=access_expires.isoformat(),
        refreshToken=refresh_token,
        refreshTokenExpiresAt=refresh_expires.isoformat(),
        user=AuthUser(id=user_id, email=email, name=payload.name, role='user'),
    )


@router.post('/login', response_model=LoginResponse, dependencies=[Depends(login_rate_limit)])
async def login(payload: UserLogin):
    db = get_db()
    email = payload.email.lower()
    user = await db.users.find_one({'email': email, 'isActive': True})
    if not user or not verify_password(payload.password, user['passwordHash']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password.')

    access_token, access_expires = create_access_token(user['_id'], user['role'])
    refresh_token, refresh_jti, refresh_expires = create_refresh_token(user['_id'])
    await db.refresh_tokens.insert_one({
        '_id': refresh_jti,
        'userId': user['_id'],
        'expiresAt': refresh_expires,
        'createdAt': now_iso(),
    })
    await write_audit('auth.login', user['_id'], {'email': email})
    return LoginResponse(
        accessToken=access_token,
        accessTokenExpiresAt=access_expires.isoformat(),
        refreshToken=refresh_token,
        refreshTokenExpiresAt=refresh_expires.isoformat(),
        user=AuthUser(id=user['_id'], email=user['email'], name=user['name'], role=user['role']),
    )


@router.post('/refresh', response_model=LoginResponse)
async def refresh_token(payload: RefreshRequest):
    db = get_db()
    try:
        token_payload = decode_token(payload.refreshToken, expected_type='refresh')
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token.') from exc

    stored = await db.refresh_tokens.find_one({'_id': token_payload['jti'], 'userId': token_payload['sub']})
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Refresh token not found.')

    user = await db.users.find_one({'_id': token_payload['sub'], 'isActive': True})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found.')

    await db.refresh_tokens.delete_one({'_id': token_payload['jti']})
    access_token, access_expires = create_access_token(user['_id'], user['role'])
    refresh_token, refresh_jti, refresh_expires = create_refresh_token(user['_id'])
    await db.refresh_tokens.insert_one({
        '_id': refresh_jti,
        'userId': user['_id'],
        'expiresAt': refresh_expires,
        'createdAt': now_iso(),
    })
    return LoginResponse(
        accessToken=access_token,
        accessTokenExpiresAt=access_expires.isoformat(),
        refreshToken=refresh_token,
        refreshTokenExpiresAt=refresh_expires.isoformat(),
        user=AuthUser(id=user['_id'], email=user['email'], name=user['name'], role=user['role']),
    )


@router.post('/logout', response_model=MessageResponse)
async def logout(payload: LogoutRequest):
    db = get_db()
    try:
        token_payload = decode_token(payload.refreshToken, expected_type='refresh')
    except Exception:
        return MessageResponse(message='Logged out.')
    await db.refresh_tokens.delete_one({'_id': token_payload['jti']})
    return MessageResponse(message='Logged out.')


@router.get('/me', response_model=AuthUser)
async def me(user=Depends(get_optional_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required.')
    return AuthUser(id=user['_id'], email=user['email'], name=user['name'], role=user['role'])
