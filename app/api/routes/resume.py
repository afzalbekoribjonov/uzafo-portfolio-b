from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.schemas.resume import ResumeModel
from app.services.audit_service import write_audit
from app.utils.helpers import deep_merge, now_iso

router = APIRouter(prefix='/api/resume')


@router.get('', response_model=ResumeModel)
async def get_resume():
    db = get_db()
    doc = await db.resume.find_one({'_id': 'resume_main'})
    if not doc:
        raise HTTPException(status_code=404, detail='Resume not found.')
    doc.pop('_id', None)
    return ResumeModel.model_validate(doc)


@router.patch('', response_model=ResumeModel)
async def patch_resume(payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await db.resume.find_one({'_id': 'resume_main'}) or {'_id': 'resume_main'}
    current.pop('_id', None)
    merged = deep_merge(current, payload)
    validated = ResumeModel.model_validate(merged)
    now = now_iso()
    doc = validated.model_dump()
    doc.update({'updatedAt': now})
    await db.resume.update_one({'_id': 'resume_main'}, {'$set': doc, '$setOnInsert': {'createdAt': now}}, upsert=True)
    await write_audit('resume.patch', admin['_id'], {'fields': list(payload.keys())})
    return validated
