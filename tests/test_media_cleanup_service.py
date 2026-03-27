import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


class FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        doc = self._docs[self._index]
        self._index += 1
        return doc


class FakeMediaAssetsCollection:
    def __init__(self, docs):
        self.docs = list(docs)
        self.find_queries = []
        self.update_calls = []

    def find(self, query):
        self.find_queries.append(query)
        matched = [
            doc for doc in self.docs
            if all(doc.get(key) == value for key, value in query.items())
        ]
        return FakeCursor(matched)

    async def update_one(self, query, update):
        self.update_calls.append((query, update))
        for doc in self.docs:
            if doc.get('_id') == query.get('_id'):
                doc.update(update['$set'])
                break


class FakeDb:
    def __init__(self, docs):
        self.media_assets = FakeMediaAssetsCollection(docs)


class DummyImageKitService:
    def __init__(self):
        self.deleted_files = []

    def delete_file(self, file_id):
        self.deleted_files.append(file_id)


class MediaCleanupServiceTests(unittest.IsolatedAsyncioTestCase):
    def _load_module(self):
        sys.modules.pop('app.services.media_cleanup_service', None)
        return importlib.import_module('app.services.media_cleanup_service')

    async def test_cleanup_media_for_owner_deletes_imagekit_files_and_marks_assets_deleted(self):
        module = self._load_module()
        db = FakeDb([
            {'_id': 'med_1', 'ownerType': 'post', 'ownerSlug': 'hello-world', 'status': 'ready', 'fileId': 'file_1'},
            {'_id': 'med_2', 'ownerType': 'post', 'ownerSlug': 'hello-world', 'status': 'ready', 'fileId': 'file_2'},
            {'_id': 'med_3', 'ownerType': 'post', 'ownerSlug': 'other-post', 'status': 'ready', 'fileId': 'file_3'},
            {'_id': 'med_4', 'ownerType': 'post', 'ownerSlug': 'hello-world', 'status': 'deleted', 'fileId': 'file_4'},
        ])
        imagekit = DummyImageKitService()

        with (
            patch.object(module, 'get_db', return_value=db),
            patch.object(module, '_get_imagekit_service', return_value=imagekit),
            patch.object(module, 'write_audit', AsyncMock()) as write_audit_mock,
            patch.object(module, 'now_iso', side_effect=['2026-03-26T10:00:00Z', '2026-03-26T10:00:01Z']),
        ):
            deleted_media_ids = await module.cleanup_media_for_owner('post', 'hello-world', actor_id='admin_1')

        self.assertEqual(deleted_media_ids, ['med_1', 'med_2'])
        self.assertEqual(imagekit.deleted_files, ['file_1', 'file_2'])
        self.assertEqual(
            db.media_assets.find_queries,
            [{'ownerType': 'post', 'ownerSlug': 'hello-world', 'status': 'ready'}],
        )
        self.assertEqual(
            db.media_assets.update_calls,
            [
                ({'_id': 'med_1'}, {'$set': {'status': 'deleted', 'updatedAt': '2026-03-26T10:00:00Z'}}),
                ({'_id': 'med_2'}, {'$set': {'status': 'deleted', 'updatedAt': '2026-03-26T10:00:01Z'}}),
            ],
        )
        write_audit_mock.assert_awaited_once_with(
            'media.owner_cleanup',
            'admin_1',
            {
                'ownerType': 'post',
                'ownerSlug': 'hello-world',
                'mediaIds': ['med_1', 'med_2'],
                'fileIds': ['file_1', 'file_2'],
            },
        )

    async def test_cleanup_media_for_owner_returns_early_when_no_ready_media_exist(self):
        module = self._load_module()
        db = FakeDb([
            {'_id': 'med_1', 'ownerType': 'project', 'ownerSlug': 'alpha', 'status': 'deleted', 'fileId': 'file_1'},
        ])

        with (
            patch.object(module, 'get_db', return_value=db),
            patch.object(module, '_get_imagekit_service') as imagekit_mock,
            patch.object(module, 'write_audit', AsyncMock()) as write_audit_mock,
        ):
            deleted_media_ids = await module.cleanup_media_for_owner('project', 'alpha', actor_id='admin_1')

        self.assertEqual(deleted_media_ids, [])
        imagekit_mock.assert_not_called()
        write_audit_mock.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
