from __future__ import annotations

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None
logger = logging.getLogger(__name__)


async def connect_to_mongo() -> None:
    global _client, _database
    settings = get_settings()
    last_error: Exception | None = None

    for attempt in range(1, settings.mongo_startup_attempts + 1):
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
        except Exception as error:
            client.close()
            last_error = error
            if attempt >= settings.mongo_startup_attempts:
                raise

            logger.warning(
                'MongoDB startup connection attempt %s/%s failed: %s. Retrying in %sms.',
                attempt,
                settings.mongo_startup_attempts,
                error,
                settings.mongo_startup_retry_delay_ms,
            )
            await asyncio.sleep(settings.mongo_startup_retry_delay_ms / 1000)
            continue

        _client = client
        _database = client[settings.mongo_db]
        logger.info('MongoDB connection established on attempt %s.', attempt)
        return

    if last_error is not None:
        raise last_error


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
