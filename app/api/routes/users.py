from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.db.mongo import get_db

router = APIRouter(prefix='/api/admin/users')


@router.get('')
async def list_users(admin=Depends(require_admin)):
    db = get_db()
    status_by_email: dict[str, str] = {}
    async for mock in db.mock_users.find({}):
        email = str(mock.get('email', '')).lower()
        status_by_email[email] = str(mock.get('status') or 'offline')

    items = []
    async for doc in db.users.find({}, {'passwordHash': 0}).sort('createdAt', -1):
        doc.pop('_id', None)
        doc['status'] = status_by_email.get(str(doc.get('email', '')).lower(), 'offline')
        items.append(doc)
    return {'items': items, 'total': len(items)}
