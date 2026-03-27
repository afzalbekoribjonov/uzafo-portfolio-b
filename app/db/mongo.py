from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _database
    settings = get_settings()
    client = AsyncIOMotorClient(
        settings.mongo_uri,
        minPoolSize=settings.mongo_min_pool_size,
        maxPoolSize=settings.mongo_max_pool_size,
        serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
        connectTimeoutMS=settings.mongo_connect_timeout_ms,
        socketTimeoutMS=settings.mongo_socket_timeout_ms,
        waitQueueTimeoutMS=settings.mongo_wait_queue_timeout_ms,
    )
    try:
        await client.admin.command('ping')
    except Exception:
        client.close()
        raise

    _client = client
    _database = client[settings.mongo_db]


async def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None



def get_db() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError('MongoDB is not connected.')
    return _database
