from __future__ import annotations

from typing import Any

from app.db.mongo import get_db
from app.utils.helpers import make_id, now_iso


async def write_audit(action: str, actor_id: str | None, payload: dict[str, Any]) -> None:
    db = get_db()
    await db.audit_logs.insert_one({
        '_id': make_id('audit'),
        'action': action,
        'actorId': actor_id,
        'payload': payload,
        'createdAt': now_iso(),
    })
