from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.schemas.profile import ProfileModel
from app.services.audit_service import write_audit
from app.utils.helpers import deep_merge, now_iso

router = APIRouter(prefix='/api/profile')


@router.get('', response_model=ProfileModel)
async def get_profile():
    db = get_db()
    doc = await db.profile.find_one({'_id': 'profile_main'})
    if not doc:
        raise HTTPException(status_code=404, detail='Profile not found.')
    doc.pop('_id', None)
    return ProfileModel.model_validate(doc)


@router.patch('', response_model=ProfileModel)
async def patch_profile(payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await db.profile.find_one({'_id': 'profile_main'}) or {'_id': 'profile_main'}
    current.pop('_id', None)
    merged = deep_merge(current, payload)
    validated = ProfileModel.model_validate(merged)
    now = now_iso()
    doc = validated.model_dump()
    doc.update({'updatedAt': now})
    await db.profile.update_one({'_id': 'profile_main'}, {'$set': doc, '$setOnInsert': {'createdAt': now}}, upsert=True)
    await write_audit('profile.patch', admin['_id'], {'fields': list(payload.keys())})
    return validated
