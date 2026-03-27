from __future__ import annotations

import logging
from typing import Literal

from app.db.mongo import get_db
from app.services.audit_service import write_audit
from app.utils.helpers import now_iso

logger = logging.getLogger(__name__)

OwnerType = Literal['project', 'post', 'discussion']


def _get_imagekit_service():
    from app.services.imagekit_service import get_imagekit_service

    return get_imagekit_service()


async def cleanup_media_for_owner(owner_type: OwnerType, owner_slug: str, actor_id: str | None = None) -> list[str]:
    if not owner_slug:
        return []

    db = get_db()
    media_docs = [
        doc
        async for doc in db.media_assets.find({
            'ownerType': owner_type,
            'ownerSlug': owner_slug,
            'status': 'ready',
        })
    ]
    if not media_docs:
        return []

    imagekit = _get_imagekit_service()
    deleted_media_ids: list[str] = []
    deleted_file_ids: list[str] = []

    for doc in media_docs:
        file_id = doc.get('fileId')
        if file_id:
            try:
                imagekit.delete_file(file_id)
            except Exception:
                logger.warning('ImageKit cleanup failed for owner %s/%s file %s.', owner_type, owner_slug, file_id, exc_info=True)
        await db.media_assets.update_one(
            {'_id': doc['_id']},
            {'$set': {'status': 'deleted', 'updatedAt': now_iso()}},
        )
        deleted_media_ids.append(str(doc['_id']))
        if file_id:
            deleted_file_ids.append(file_id)

    if actor_id:
        await write_audit(
            'media.owner_cleanup',
            actor_id,
            {
                'ownerType': owner_type,
                'ownerSlug': owner_slug,
                'mediaIds': deleted_media_ids,
                'fileIds': deleted_file_ids,
            },
        )

    return deleted_media_ids
