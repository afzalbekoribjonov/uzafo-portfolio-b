from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mongo import get_db
from app.utils.helpers import now_iso

SEED_DIR = Path(__file__).resolve().parent.parent / 'seed_data'


async def ensure_indexes() -> None:
    db = get_db()
    await db.users.create_index('email', unique=True)
    await db.projects.create_index('slug', unique=True)
    await db.posts.create_index('slug', unique=True)
    await db.discussions.create_index('slug', unique=True)
    await db.refresh_tokens.create_index('expiresAt', expireAfterSeconds=0)
    await db.upload_sessions.create_index('expiresAt', expireAfterSeconds=0)
    await db.media_assets.create_index([('ownerType', 1), ('ownerSlug', 1), ('role', 1)])


async def seed_initial_data() -> None:
    settings = get_settings()
    db = get_db()
    now = now_iso()

    admin = await db.users.find_one({'email': settings.admin_email.lower()})
    if not admin:
        await db.users.insert_one({
            '_id': 'user_admin',
            'id': 'user_admin',
            'name': settings.admin_name,
            'email': settings.admin_email.lower(),
            'role': 'admin',
            'passwordHash': hash_password(settings.admin_password),
            'isActive': True,
            'createdAt': now,
            'updatedAt': now,
        })

    if not settings.seed_demo_data:
        return

    async def seed_singleton(collection_name: str, doc_id: str, file_name: str):
        coll = getattr(db, collection_name)
        exists = await coll.find_one({'_id': doc_id})
        if exists:
            return
        data = json.loads((SEED_DIR / file_name).read_text(encoding='utf-8'))
        data['_id'] = doc_id
        data['createdAt'] = now
        data['updatedAt'] = now
        await coll.insert_one(data)

    async def seed_list(collection_name: str, file_name: str):
        coll = getattr(db, collection_name)
        if await coll.count_documents({}) > 0:
            return
        items = json.loads((SEED_DIR / file_name).read_text(encoding='utf-8'))
        for item in items:
            item['_id'] = item.get('slug') or item.get('id')
            item['createdAt'] = item.get('createdAt', now)
            item['updatedAt'] = item.get('updatedAt', now)
        if items:
            await coll.insert_many(items)

    await seed_singleton('profile', 'profile_main', 'profile.json')
    await seed_singleton('resume', 'resume_main', 'resume.json')
    await seed_singleton('site', 'site_main', 'site.json')
    await seed_list('projects', 'projects.json')
    await seed_list('posts', 'blog-posts.json')
    await seed_list('discussions', 'discussions.json')

    # Optionally keep mock frontend users in a helper collection for the admin tab.
    if await db.mock_users.count_documents({}) == 0:
        items = json.loads((SEED_DIR / 'users.json').read_text(encoding='utf-8'))
        for item in items:
            item['_id'] = item.get('id')
        if items:
            await db.mock_users.insert_many(items)
