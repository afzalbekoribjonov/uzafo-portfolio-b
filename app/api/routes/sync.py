from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_admin
from app.db.mongo import get_db
from app.schemas.discussion import DiscussionModel
from app.schemas.post import BlogPostModel
from app.schemas.profile import ProfileModel
from app.schemas.project import ProjectModel
from app.schemas.resume import ResumeModel
from app.services.audit_service import write_audit
from app.services.content_service import normalize_content_blocks
from app.services.media_cleanup_service import cleanup_media_for_owner
from app.utils.helpers import now_iso

router = APIRouter(prefix='/api/admin/sync')


class ProjectsSyncPayload(BaseModel):
    items: list[ProjectModel] = Field(default_factory=list)


class PostsSyncPayload(BaseModel):
    items: list[BlogPostModel] = Field(default_factory=list)


class DiscussionsSyncPayload(BaseModel):
    items: list[DiscussionModel] = Field(default_factory=list)


@router.put('/profile', response_model=ProfileModel)
async def sync_profile(payload: ProfileModel, admin=Depends(require_admin)):
    db = get_db()
    now = now_iso()
    doc = payload.model_dump()
    doc['updatedAt'] = now
    await db.profile.update_one({'_id': 'profile_main'}, {'$set': doc, '$setOnInsert': {'createdAt': now}}, upsert=True)
    await write_audit('sync.profile', admin['_id'], {'fields': list(doc.keys())})
    return ProfileModel.model_validate(doc)


@router.put('/resume', response_model=ResumeModel)
async def sync_resume(payload: ResumeModel, admin=Depends(require_admin)):
    db = get_db()
    now = now_iso()
    doc = payload.model_dump()
    doc['updatedAt'] = now
    await db.resume.update_one({'_id': 'resume_main'}, {'$set': doc, '$setOnInsert': {'createdAt': now}}, upsert=True)
    await write_audit('sync.resume', admin['_id'], {'fields': list(doc.keys())})
    return ResumeModel.model_validate(doc)


@router.put('/projects')
async def sync_projects(payload: ProjectsSyncPayload, admin=Depends(require_admin)):
    db = get_db()
    now = now_iso()
    existing = {doc['slug']: doc async for doc in db.projects.find({})}
    incoming_slugs = {item.slug for item in payload.items}
    for removed_slug in existing:
        if removed_slug not in incoming_slugs:
            await cleanup_media_for_owner('project', removed_slug, admin['_id'])
    await db.projects.delete_many({})
    docs = []
    for item in payload.items:
        doc = item.model_dump()
        previous = existing.get(doc['slug']) or {}
        doc['_id'] = doc['slug']
        doc['content'] = normalize_content_blocks(doc.get('content'), doc['slug'])
        doc['coverMediaId'] = doc.get('coverMediaId') or previous.get('coverMediaId')
        doc['createdAt'] = previous.get('createdAt', doc.get('createdAt', now))
        doc['updatedAt'] = now
        docs.append(doc)
    if docs:
        await db.projects.insert_many(docs)
    await write_audit('sync.projects', admin['_id'], {'count': len(docs)})
    return {'items': payload.items, 'total': len(payload.items)}


@router.put('/posts')
async def sync_posts(payload: PostsSyncPayload, admin=Depends(require_admin)):
    db = get_db()
    now = now_iso()
    existing = {doc['slug']: doc async for doc in db.posts.find({})}
    incoming_slugs = {item.slug for item in payload.items}
    for removed_slug in existing:
        if removed_slug not in incoming_slugs:
            await cleanup_media_for_owner('post', removed_slug, admin['_id'])
    await db.posts.delete_many({})
    docs = []
    for item in payload.items:
        doc = item.model_dump()
        previous = existing.get(doc['slug']) or {}
        doc['_id'] = doc['slug']
        doc['coverMediaId'] = doc.get('coverMediaId') or previous.get('coverMediaId')
        doc['createdAt'] = previous.get('createdAt', doc.get('createdAt', now))
        doc['updatedAt'] = now
        docs.append(doc)
    if docs:
        await db.posts.insert_many(docs)
    await write_audit('sync.posts', admin['_id'], {'count': len(docs)})
    return {'items': payload.items, 'total': len(payload.items)}


@router.put('/discussions')
async def sync_discussions(payload: DiscussionsSyncPayload, admin=Depends(require_admin)):
    db = get_db()
    now = now_iso()
    existing = {doc['slug']: doc async for doc in db.discussions.find({})}
    incoming_slugs = {item.slug for item in payload.items}
    for removed_slug in existing:
        if removed_slug not in incoming_slugs:
            await cleanup_media_for_owner('discussion', removed_slug, admin['_id'])
    await db.discussions.delete_many({})
    docs = []
    for item in payload.items:
        doc = item.model_dump()
        previous = existing.get(doc['slug']) or {}
        doc['_id'] = doc['slug']
        doc['createdAt'] = previous.get('createdAt', doc.get('createdAt', now))
        doc['updatedAt'] = now
        docs.append(doc)
    if docs:
        await db.discussions.insert_many(docs)
    await write_audit('sync.discussions', admin['_id'], {'count': len(docs)})
    return {'items': payload.items, 'total': len(payload.items)}
