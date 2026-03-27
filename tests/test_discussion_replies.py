import importlib
import unittest
from unittest.mock import AsyncMock, patch


class FakeDiscussionsCollection:
    def __init__(self):
        self.update_calls = []

    async def update_one(self, query, update):
        self.update_calls.append((query, update))


class FakeDb:
    def __init__(self):
        self.discussions = FakeDiscussionsCollection()


class DiscussionReplyTests(unittest.IsolatedAsyncioTestCase):
    def _load_module(self):
        return importlib.import_module('app.api.routes.discussions')

    async def test_add_reply_uses_authenticated_user_and_ignores_payload_author(self):
        module = self._load_module()
        db = FakeDb()
        current_discussion = {
            'slug': 'hello-world',
            'title': 'Hello world',
            'category': 'General',
            'createdAt': '2026-03-20T10:00:00Z',
            'author': {
                'name': 'Thread Owner',
                'avatar': '/assets/avatars/uzafo-avatar.svg',
                'title': 'Member',
            },
            'summary': 'Summary',
            'content': '<p>Discussion body</p>',
            'messages': [],
        }
        payload = module.DiscussionReplyCreate.model_validate({
            'text': '<p>Live reply</p>',
            'author': {'name': 'Spoofed Name', 'badge': 'Admin'},
        })

        with (
            patch.object(module, 'get_db', return_value=db),
            patch.object(module, '_get_discussion_or_404', AsyncMock(return_value=current_discussion)),
            patch.object(module, 'write_audit', AsyncMock()) as write_audit_mock,
            patch.object(module, 'make_id', return_value='reply_123'),
            patch.object(module, 'now_iso', side_effect=['2026-03-26T11:00:00Z', '2026-03-26T11:00:01Z']),
        ):
            result = await module.add_reply(
                'hello-world',
                payload,
                user={'_id': 'user_1', 'name': 'Real Member', 'role': 'user'},
            )

        self.assertEqual(result.messages[-1].author.name, 'Real Member')
        self.assertEqual(result.messages[-1].author.badge, 'Member')
        self.assertEqual(result.messages[-1].text, '<p>Live reply</p>')
        self.assertEqual(result.messages[-1].id, 'reply_123')
        self.assertEqual(len(db.discussions.update_calls), 1)
        update_query, update_doc = db.discussions.update_calls[0]
        self.assertEqual(update_query, {'slug': 'hello-world'})
        saved_reply = update_doc['$set']['messages'][-1]
        self.assertEqual(saved_reply['author']['name'], 'Real Member')
        self.assertEqual(saved_reply['author']['badge'], 'Member')
        self.assertEqual(saved_reply['text'], '<p>Live reply</p>')
        self.assertEqual(saved_reply['id'], 'reply_123')
        self.assertEqual(update_doc['$set']['updatedAt'], '2026-03-26T11:00:01Z')
        write_audit_mock.assert_awaited_once_with(
            'discussion.reply.add',
            'user_1',
            {'slug': 'hello-world', 'replyId': 'reply_123'},
        )


if __name__ == '__main__':
    unittest.main()
