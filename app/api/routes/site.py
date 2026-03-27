from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.schemas.site import SiteModel
from app.services.audit_service import write_audit
from app.utils.helpers import deep_merge, now_iso

router = APIRouter(prefix='/api/site')


@router.get('', response_model=SiteModel)
async def get_site():
    db = get_db()
    doc = await db.site.find_one({'_id': 'site_main'})
    if not doc:
        raise HTTPException(status_code=404, detail='Site data not found.')
    doc.pop('_id', None)
    return SiteModel.model_validate(doc)


@router.patch('', response_model=SiteModel)
async def patch_site(payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await db.site.find_one({'_id': 'site_main'}) or {'_id': 'site_main'}
    current.pop('_id', None)
    merged = deep_merge(current, payload)
    validated = SiteModel.model_validate(merged)
    now = now_iso()
    doc = validated.model_dump()
    doc.update({'updatedAt': now})
    await db.site.update_one({'_id': 'site_main'}, {'$set': doc, '$setOnInsert': {'createdAt': now}}, upsert=True)
    await write_audit('site.patch', admin['_id'], {'fields': list(payload.keys())})
    return validated
