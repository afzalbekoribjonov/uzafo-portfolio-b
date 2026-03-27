from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_admin, upload_rate_limit
from app.core.config import get_settings
from app.db.mongo import get_db
from app.schemas.media import MediaAsset, MediaCompleteRequest, MediaUploadAuthRequest, MediaUploadAuthResponse
from app.services.audit_service import write_audit
from app.services.imagekit_service import get_imagekit_service
from app.utils.helpers import make_id, now_iso

router = APIRouter(prefix='/api/media')

_ALLOWED_IMAGE = {'image/jpeg', 'image/png', 'image/webp', 'image/svg+xml', 'image/gif'}
_ALLOWED_VIDEO = {'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'}


def _resolve_resource_type(content_type: str) -> str:
    if content_type.startswith('image/'):
        return 'image'
    if content_type.startswith('video/'):
        return 'video'
    return 'raw'



def _build_folder(owner_type: str, owner_slug: str | None, role: str) -> str:
    if owner_type in {'site', 'profile', 'resume'}:
        return f'/uzafo/{owner_type}/{role}'
    if owner_slug:
        return f'/uzafo/{owner_type}/{owner_slug}/{role}'
    return f'/uzafo/{owner_type}/{role}'


@router.post('/upload-auth', response_model=MediaUploadAuthResponse, dependencies=[Depends(upload_rate_limit)])
async def upload_auth(payload: MediaUploadAuthRequest, admin=Depends(require_admin)):
    settings = get_settings()
    if not settings.imagekit_enabled:
        raise HTTPException(status_code=503, detail='ImageKit is not configured yet.')

    resource_type = _resolve_resource_type(payload.contentType)
    if resource_type == 'image':
        if payload.contentType not in _ALLOWED_IMAGE:
            raise HTTPException(status_code=400, detail='Unsupported image type.')
        if payload.sizeBytes > settings.max_image_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail='Image file is too large.')
    elif resource_type == 'video':
        if payload.contentType not in _ALLOWED_VIDEO:
            raise HTTPException(status_code=400, detail='Unsupported video type.')
        if payload.sizeBytes > settings.max_video_size_mb * 1024 * 1024:
            raise HTTPException(status_code=400, detail='Video file is too large.')
    else:
        raise HTTPException(status_code=400, detail='Only image and video uploads are allowed.')

    db = get_db()
    if payload.ownerType in {'project', 'post', 'discussion'}:
        if not payload.ownerSlug:
            raise HTTPException(status_code=400, detail='ownerSlug is required for this owner type.')
        collection_name = {'project': 'projects', 'post': 'posts', 'discussion': 'discussions'}[payload.ownerType]
        owner_doc = await getattr(db, collection_name).find_one({'slug': payload.ownerSlug})
        if not owner_doc:
            raise HTTPException(status_code=404, detail='Owner document not found.')

    imagekit = get_imagekit_service()
    auth = imagekit.get_authentication_parameters()
    folder = _build_folder(payload.ownerType, payload.ownerSlug, payload.role)
    session_id = make_id('upload')
    from datetime import datetime, timezone

    await db.upload_sessions.insert_one({
        '_id': session_id,
        'ownerType': payload.ownerType,
        'ownerSlug': payload.ownerSlug,
        'role': payload.role,
        'contentType': payload.contentType,
        'sizeBytes': payload.sizeBytes,
        'resourceType': resource_type,
        'folder': folder,
        'fileName': payload.fileName,
        'isPrivateFile': payload.isPrivateFile,
        'issuedTo': admin['_id'],
        'createdAt': now_iso(),
        'expiresAt': datetime.fromtimestamp(auth['expire'], tz=timezone.utc),
    })
    await write_audit('media.upload_auth', admin['_id'], {'sessionId': session_id, 'folder': folder})
    return MediaUploadAuthResponse(
        sessionId=session_id,
        publicKey=settings.imagekit_public_key,
        urlEndpoint=settings.imagekit_url_endpoint,
        token=auth['token'],
        signature=auth['signature'],
        expire=auth['expire'],
        fileName=payload.fileName,
        folder=folder,
        tags=[payload.ownerType, payload.role],
        isPrivateFile=payload.isPrivateFile,
    )


@router.post('/complete', response_model=MediaAsset)
async def complete_upload(payload: MediaCompleteRequest, admin=Depends(require_admin)):
    db = get_db()
    session = await db.upload_sessions.find_one({'_id': payload.sessionId, 'issuedTo': admin['_id']})
    if not session:
        raise HTTPException(status_code=404, detail='Upload session not found or expired.')

    media_id = make_id('med')
    now = now_iso()
    doc = {
        '_id': media_id,
        'id': media_id,
        'provider': 'imagekit',
        'fileId': payload.fileId,
        'filePath': payload.filePath,
        'fileName': payload.name,
        'url': payload.url,
        'thumbnailUrl': payload.thumbnailUrl,
        'resourceType': session['resourceType'],
        'mimeType': session['contentType'],
        'sizeBytes': payload.size or session['sizeBytes'],
        'width': payload.width,
        'height': payload.height,
        'duration': payload.duration,
        'folder': session['folder'],
        'tags': [session['ownerType'], session['role']],
        'ownerType': session['ownerType'],
        'ownerSlug': session.get('ownerSlug'),
        'role': session['role'],
        'isPrivate': session['isPrivateFile'],
        'createdBy': admin['_id'],
        'status': 'ready',
        'createdAt': now,
        'updatedAt': now,
    }
    await db.media_assets.insert_one(doc)

    if session['role'] == 'cover' and session['ownerType'] in {'project', 'post'} and session.get('ownerSlug'):
        collection_name = 'projects' if session['ownerType'] == 'project' else 'posts'
        await getattr(db, collection_name).update_one(
            {'slug': session['ownerSlug']},
            {'$set': {'cover': payload.url, 'coverMediaId': media_id, 'updatedAt': now}},
        )

    await db.upload_sessions.delete_one({'_id': payload.sessionId})
    await write_audit('media.complete', admin['_id'], {'mediaId': media_id, 'fileId': payload.fileId})
    doc.pop('_id', None)
    return MediaAsset.model_validate(doc)


@router.get('/{media_id}', response_model=MediaAsset)
async def get_media(media_id: str, admin=Depends(require_admin)):
    db = get_db()
    doc = await db.media_assets.find_one({'_id': media_id, 'status': 'ready'})
    if not doc:
        raise HTTPException(status_code=404, detail='Media not found.')
    doc.pop('_id', None)
    return MediaAsset.model_validate(doc)


@router.delete('/{media_id}')
async def delete_media(media_id: str, admin=Depends(require_admin)):
    db = get_db()
    doc = await db.media_assets.find_one({'_id': media_id, 'status': 'ready'})
    if not doc:
        raise HTTPException(status_code=404, detail='Media not found.')

    imagekit = get_imagekit_service()
    try:
        if doc.get('fileId'):
            imagekit.delete_file(doc['fileId'])
    except Exception:
        # DB deletion still proceeds; operator can retry cloud cleanup later.
        pass

    await db.media_assets.update_one({'_id': media_id}, {'$set': {'status': 'deleted', 'updatedAt': now_iso()}})

    if doc.get('role') == 'cover' and doc.get('ownerType') in {'project', 'post'} and doc.get('ownerSlug'):
        collection_name = 'projects' if doc['ownerType'] == 'project' else 'posts'
        await getattr(db, collection_name).update_one(
            {'slug': doc['ownerSlug'], 'coverMediaId': media_id},
            {'$set': {'cover': '', 'coverMediaId': None, 'updatedAt': now_iso()}},
        )
    await write_audit('media.delete', admin['_id'], {'mediaId': media_id, 'fileId': doc.get('fileId')})
    return {'message': 'Media deleted.'}
