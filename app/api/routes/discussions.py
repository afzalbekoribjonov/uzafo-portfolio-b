from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin, require_user
from app.db.mongo import get_db
from app.schemas.discussion import DiscussionMessage, DiscussionModel, DiscussionReplyCreate
from app.services.audit_service import write_audit
from app.services.media_cleanup_service import cleanup_media_for_owner
from app.utils.helpers import deep_merge, make_id, now_iso, slugify, text_value_to_plain_string

router = APIRouter(prefix='/api/discussions')


async def _get_discussion_or_404(slug: str):
    db = get_db()
    doc = await db.discussions.find_one({'slug': slug})
    if not doc:
        raise HTTPException(status_code=404, detail='Discussion not found.')
    doc.pop('_id', None)
    return doc


@router.get('')
async def list_discussions():
    db = get_db()
    items = []
    async for doc in db.discussions.find({}).sort('createdAt', -1):
        doc.pop('_id', None)
        items.append(DiscussionModel.model_validate(doc).model_dump())
    return {'items': items, 'total': len(items)}


@router.get('/{slug}', response_model=DiscussionModel)
async def get_discussion(slug: str):
    return DiscussionModel.model_validate(await _get_discussion_or_404(slug))


@router.post('', response_model=DiscussionModel, status_code=status.HTTP_201_CREATED)
async def create_discussion(payload: DiscussionModel, user=Depends(require_user)):
    db = get_db()
    slug = slugify(payload.slug) or slugify(text_value_to_plain_string(payload.title))
    if await db.discussions.find_one({'slug': slug}):
        raise HTTPException(status_code=409, detail='Discussion slug already exists.')
    now = now_iso()
    doc = payload.model_dump()
    doc['slug'] = slug
    doc['author']['name'] = user['name']
    doc['author']['title'] = 'Admin' if user['role'] == 'admin' else 'Member'
    doc.update({'_id': slug, 'createdAt': doc.get('createdAt', now), 'updatedAt': now})
    await db.discussions.insert_one(doc)
    await write_audit('discussion.create', user['_id'], {'slug': slug})
    doc.pop('_id', None)
    return DiscussionModel.model_validate(doc)


@router.patch('/{slug}', response_model=DiscussionModel)
async def patch_discussion(slug: str, payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await _get_discussion_or_404(slug)
    merged = deep_merge(current, payload)
    merged['slug'] = slugify(merged.get('slug', slug)) or slug
    validated = DiscussionModel.model_validate(merged)
    doc = validated.model_dump()
    doc['updatedAt'] = now_iso()
    await db.discussions.update_one({'slug': slug}, {'$set': doc})
    await write_audit('discussion.patch', admin['_id'], {'slug': slug, 'fields': list(payload.keys())})
    return validated


@router.delete('/{slug}')
async def delete_discussion(slug: str, admin=Depends(require_admin)):
    db = get_db()
    await _get_discussion_or_404(slug)
    result = await db.discussions.delete_one({'slug': slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Discussion not found.')
    await cleanup_media_for_owner('discussion', slug, admin['_id'])
    await write_audit('discussion.delete', admin['_id'], {'slug': slug})
    return {'message': 'Discussion deleted.'}


@router.post('/{slug}/replies', response_model=DiscussionModel)
async def add_reply(slug: str, payload: DiscussionReplyCreate, user=Depends(require_user)):
    db = get_db()
    current = await _get_discussion_or_404(slug)
    reply = DiscussionMessage(
        id=make_id('reply'),
        author={
            'name': user['name'],
            'badge': 'Admin' if user['role'] == 'admin' else 'Member',
        },
        text=payload.text,
        createdAt=now_iso(),
    ).model_dump()
    current_messages = current.get('messages', [])
    current_messages.append(reply)
    current['messages'] = current_messages
    validated = DiscussionModel.model_validate(current)
    await db.discussions.update_one({'slug': slug}, {'$set': {'messages': validated.model_dump()['messages'], 'updatedAt': now_iso()}})
    await write_audit('discussion.reply.add', user['_id'], {'slug': slug, 'replyId': reply['id']})
    return validated


@router.delete('/{slug}/replies/{reply_id}')
async def delete_reply(slug: str, reply_id: str, admin=Depends(require_admin)):
    db = get_db()
    current = await _get_discussion_or_404(slug)
    replies = [item for item in current.get('messages', []) if item.get('id') != reply_id]
    await db.discussions.update_one({'slug': slug}, {'$set': {'messages': replies, 'updatedAt': now_iso()}})
    await write_audit('discussion.reply.delete', admin['_id'], {'slug': slug, 'replyId': reply_id})
    return {'message': 'Reply deleted.'}
