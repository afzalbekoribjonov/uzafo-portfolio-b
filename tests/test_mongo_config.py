import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


class DummyMotorClient:
    def __init__(self, uri, **kwargs):
        self.uri = uri
        self.kwargs = kwargs
        self.closed = False
        self.databases = {}
        self.pinged = False
        self.admin = self.Admin(self)

    class Admin:
        def __init__(self, parent):
            self.parent = parent

        async def command(self, name):
            if name != 'ping':
                raise AssertionError(f'Unexpected admin command: {name}')
            self.parent.pinged = True
            return {'ok': 1}

    def __getitem__(self, name):
        database = {'name': name}
        self.databases[name] = database
        return database

    def close(self):
        self.closed = True


class MongoConfigTests(unittest.IsolatedAsyncioTestCase):
    def _load_module(self):
        module = importlib.import_module('app.db.mongo')
        module._client = None
        module._database = None
        return module

    async def test_connect_to_mongo_uses_pool_and_timeout_settings(self):
        module = self._load_module()
        settings = SimpleNamespace(
            mongo_uri='mongodb://localhost:27017',
            mongo_db='uzafo_test',
            mongo_min_pool_size=2,
            mongo_max_pool_size=25,
            mongo_server_selection_timeout_ms=4000,
            mongo_connect_timeout_ms=9000,
            mongo_socket_timeout_ms=15000,
            mongo_wait_queue_timeout_ms=3000,
            mongo_startup_attempts=1,
            mongo_startup_retry_delay_ms=0,
        )

        with (
            patch.object(module, 'get_settings', return_value=settings),
            patch.object(module, 'AsyncIOMotorClient', DummyMotorClient),
        ):
            await module.connect_to_mongo()
            client = module._client
            database = module.get_db()
            await module.close_mongo_connection()

        self.assertIsNotNone(client)
        self.assertEqual(client.uri, 'mongodb://localhost:27017')
        self.assertEqual(
            client.kwargs,
            {
                'minPoolSize': 2,
                'maxPoolSize': 25,
                'serverSelectionTimeoutMS': 4000,
                'connectTimeoutMS': 9000,
                'socketTimeoutMS': 15000,
                'waitQueueTimeoutMS': 3000,
            },
        )
        self.assertTrue(client.pinged)
        self.assertEqual(database, {'name': 'uzafo_test'})
        self.assertTrue(client.closed)
        self.assertIsNone(module._client)
        self.assertIsNone(module._database)

    async def test_connect_to_mongo_retries_after_transient_failure(self):
        module = self._load_module()
        settings = SimpleNamespace(
            mongo_uri='mongodb://localhost:27017',
            mongo_db='uzafo_test',
            mongo_min_pool_size=1,
            mongo_max_pool_size=20,
            mongo_server_selection_timeout_ms=5000,
            mongo_connect_timeout_ms=10000,
            mongo_socket_timeout_ms=10000,
            mongo_wait_queue_timeout_ms=5000,
            mongo_startup_attempts=3,
            mongo_startup_retry_delay_ms=1,
        )

        first_client = DummyMotorClient(settings.mongo_uri)
        second_client = DummyMotorClient(settings.mongo_uri)
        first_client.admin.command = AsyncMock(side_effect=RuntimeError('dns timeout'))
        second_client.admin.command = AsyncMock(return_value={'ok': 1})

        sleep_mock = AsyncMock()

        with (
            patch.object(module, 'get_settings', return_value=settings),
            patch.object(module, 'AsyncIOMotorClient', side_effect=[first_client, second_client]),
            patch.object(module.asyncio, 'sleep', sleep_mock),
        ):
            await module.connect_to_mongo()
            client = module._client
            database = module.get_db()
            await module.close_mongo_connection()

        self.assertIs(client, second_client)
        self.assertEqual(database, {'name': 'uzafo_test'})
        self.assertTrue(first_client.closed)
        self.assertTrue(second_client.closed)
        sleep_mock.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
