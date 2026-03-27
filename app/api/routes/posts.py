from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_optional_user, require_admin
from app.db.mongo import get_db
from app.schemas.post import BlogComment, BlogPostModel
from app.services.audit_service import write_audit
from app.services.content_service import estimate_reading_time, normalize_content_blocks
from app.services.media_cleanup_service import cleanup_media_for_owner
from app.utils.helpers import deep_merge, make_id, now_iso, slugify, text_value_to_plain_string

router = APIRouter(prefix='/api/posts')


async def _get_post_or_404(slug: str):
    db = get_db()
    doc = await db.posts.find_one({'slug': slug})
    if not doc:
        raise HTTPException(status_code=404, detail='Post not found.')
    doc.pop('_id', None)
    return doc


@router.get('')
async def list_posts():
    db = get_db()
    items = []
    async for doc in db.posts.find({}).sort('publishedAt', -1):
        doc.pop('_id', None)
        items.append(BlogPostModel.model_validate(doc).model_dump())
    return {'items': items, 'total': len(items)}


@router.get('/{slug}', response_model=BlogPostModel)
async def get_post(slug: str):
    return BlogPostModel.model_validate(await _get_post_or_404(slug))


@router.post('', response_model=BlogPostModel, status_code=status.HTTP_201_CREATED)
async def create_post(payload: BlogPostModel, admin=Depends(require_admin)):
    db = get_db()
    slug = slugify(payload.slug) or slugify(text_value_to_plain_string(payload.title))
    if await db.posts.find_one({'slug': slug}):
        raise HTTPException(status_code=409, detail='Post slug already exists.')
    now = now_iso()
    doc = payload.model_dump()
    doc['slug'] = slug
    doc['blocks'] = normalize_content_blocks(doc.get('blocks'), slug)
    doc['readingTime'] = estimate_reading_time(doc['blocks'])
    doc.update({'_id': slug, 'createdAt': now, 'updatedAt': now})
    await db.posts.insert_one(doc)
    await write_audit('post.create', admin['_id'], {'slug': slug})
    doc.pop('_id', None)
    return BlogPostModel.model_validate(doc)


@router.patch('/{slug}', response_model=BlogPostModel)
async def patch_post(slug: str, payload: dict, admin=Depends(require_admin)):
    db = get_db()
    current = await _get_post_or_404(slug)
    merged = deep_merge(current, payload)
    merged['slug'] = slugify(merged.get('slug', slug)) or slug
    merged['blocks'] = normalize_content_blocks(merged.get('blocks'), merged['slug'])
    merged['readingTime'] = estimate_reading_time(merged['blocks'])
    validated = BlogPostModel.model_validate(merged)
    doc = validated.model_dump()
    doc['updatedAt'] = now_iso()
    await db.posts.update_one({'slug': slug}, {'$set': doc})
    await write_audit('post.patch', admin['_id'], {'slug': slug, 'fields': list(payload.keys())})
    return validated


@router.delete('/{slug}')
async def delete_post(slug: str, admin=Depends(require_admin)):
    db = get_db()
    await _get_post_or_404(slug)
    result = await db.posts.delete_one({'slug': slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Post not found.')
    await cleanup_media_for_owner('post', slug, admin['_id'])
    await write_audit('post.delete', admin['_id'], {'slug': slug})
    return {'message': 'Post deleted.'}


@router.post('/{slug}/comments', response_model=BlogPostModel)
async def add_comment(slug: str, payload: dict, user=Depends(get_optional_user)):
    db = get_db()
    current = await _get_post_or_404(slug)
    comment = BlogComment(
        id=make_id('comment'),
        author=(user['name'] if user else str(payload.get('author') or 'Guest')),
        message=payload.get('message', ''),
        createdAt=now_iso(),
    ).model_dump()
    current_comments = current.get('comments', [])
    current_comments.append(comment)
    current['comments'] = current_comments
    validated = BlogPostModel.model_validate(current)
    await db.posts.update_one({'slug': slug}, {'$set': {'comments': validated.model_dump()['comments'], 'updatedAt': now_iso()}})
    await write_audit('post.comment.add', user['_id'] if user else None, {'slug': slug, 'commentId': comment['id']})
    return validated




@router.post('/{slug}/like', response_model=BlogPostModel)
async def add_like(slug: str, user=Depends(get_optional_user)):
    db = get_db()
    current = await _get_post_or_404(slug)
    current['likes'] = int(current.get('likes', 0)) + 1
    current['updatedAt'] = now_iso()
    validated = BlogPostModel.model_validate(current)
    await db.posts.update_one({'slug': slug}, {'$set': {'likes': validated.likes, 'updatedAt': current['updatedAt']}})
    await write_audit('post.like', user['_id'] if user else None, {'slug': slug})
    return validated

@router.delete('/{slug}/comments/{comment_id}')
async def delete_comment(slug: str, comment_id: str, admin=Depends(require_admin)):
    db = get_db()
    current = await _get_post_or_404(slug)
    comments = [item for item in current.get('comments', []) if item.get('id') != comment_id]
    await db.posts.update_one({'slug': slug}, {'$set': {'comments': comments, 'updatedAt': now_iso()}})
    await write_audit('post.comment.delete', admin['_id'], {'slug': slug, 'commentId': comment_id})
    return {'message': 'Comment deleted.'}
