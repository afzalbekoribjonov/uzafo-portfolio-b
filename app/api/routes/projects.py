from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.schemas.project import ProjectModel
from app.services.audit_service import write_audit
from app.services.content_service import normalize_content_blocks
from app.services.media_cleanup_service import cleanup_media_for_owner
from app.utils.helpers import deep_merge, now_iso, slugify, text_value_to_plain_string

router = APIRouter(prefix='/api/projects')


async def _get_project_or_404(slug: str):
    db = get_db()
    doc = await db.projects.find_one({'slug': slug})
    if not doc:
        raise HTTPException(status_code=404, detail='Project not found.')
    doc.pop('_id', None)
    return doc


@router.get('')
async def list_projects():
    db = get_db()
    items = []
    async for doc in db.projects.find({}).sort('year', -1):
        doc.pop('_id', None)
        items.append(ProjectModel.model_validate(doc).model_dump())
    return {'items': items, 'total': len(items)}


@router.get('/{slug}', response_model=ProjectModel)
async def get_project(slug: str):
    return ProjectModel.model_validate(await _get_project_or_404(slug))


@router.post('', response_model=ProjectModel, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectModel, admin=Depends(require_admin)):
    db = get_db()
    slug = slugify(payload.slug) or slugify(text_value_to_plain_string(payload.title))
    if await db.projects.find_one({'slug': slug}):
        raise HTTPException(status_code=409, detail='Project slug already exists.')
    now = now_iso()
    doc = payload.model_dump()
    doc['slug'] = slug
    doc['content'] = normalize_content_blocks(doc.get('content'), slug)
    doc.update({'_id': slug, 'createdAt': now, 'updatedAt': now})
    await db.projects.insert_one(doc)
    await write_audit('project.create', admin['_id'], {'slug': slug})
    doc.pop('_id', None)
    return ProjectModel.model_validate(doc)


@router.patch('/{slug}', response_model=ProjectModel)
async def patch_project(slug: str, payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await _get_project_or_404(slug)
    merged = deep_merge(current, payload)
    merged['slug'] = slugify(merged.get('slug', slug)) or slug
    merged['content'] = normalize_content_blocks(merged.get('content'), merged['slug'])
    validated = ProjectModel.model_validate(merged)
    doc = validated.model_dump()
    doc['updatedAt'] = now_iso()
    await db.projects.update_one({'slug': slug}, {'$set': doc})
    await write_audit('project.patch', admin['_id'], {'slug': slug, 'fields': list(payload.keys())})
    return validated


@router.delete('/{slug}')
async def delete_project(slug: str, admin=Depends(require_admin)):
    db = get_db()
    await _get_project_or_404(slug)
    result = await db.projects.delete_one({'slug': slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Project not found.')
    await cleanup_media_for_owner('project', slug, admin['_id'])
    await write_audit('project.delete', admin['_id'], {'slug': slug})
    return {'message': 'Project deleted.'}
