import importlib
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class DummyImageKit:
    instances_created = 0

    def __init__(self, public_key=None, private_key=None, url_endpoint=None, transformation_position=None, options=None):
        type(self).instances_created += 1
        self.init_kwargs = {
            'public_key': public_key,
            'private_key': private_key,
            'url_endpoint': url_endpoint,
            'transformation_position': transformation_position,
            'options': options,
        }
        self.auth_calls = 0
        self.url_calls = []
        self.deleted_files = []

    def get_authentication_parameters(self):
        self.auth_calls += 1
        return {'token': 'token-123', 'expire': 1234567890, 'signature': 'sig-123'}

    def url(self, options):
        self.url_calls.append(options)
        return 'https://ik.example.com/generated-url'

    def delete_file(self, file_id):
        self.deleted_files.append(file_id)


class ExplodingImageKit:
    def __init__(self, *args, **kwargs):
        raise AssertionError('ImageKit SDK should not be initialized when config is incomplete.')


class ImageKitServiceTests(unittest.TestCase):
    def _load_service_module(self, imagekit_class):
        if hasattr(imagekit_class, 'instances_created'):
            imagekit_class.instances_created = 0
        fake_imagekit = types.ModuleType('imagekitio')
        fake_imagekit.ImageKit = imagekit_class
        sys.modules.pop('app.services.imagekit_service', None)
        with patch.dict(sys.modules, {'imagekitio': fake_imagekit}):
            return importlib.import_module('app.services.imagekit_service')

    def test_service_uses_sdk_constructor_and_methods(self):
        module = self._load_service_module(DummyImageKit)
        settings = SimpleNamespace(
            imagekit_public_key='public-key',
            imagekit_private_key='private-key',
            imagekit_url_endpoint='https://ik.example.com',
            imagekit_enabled=True,
        )

        with patch.object(module, 'get_settings', return_value=settings):
            service = module.ImageKitService()
            auth = service.get_authentication_parameters()
            url = service.build_url(
                'https://example.com/source.jpg',
                transformation=[{'width': 300}, {'height': 200}],
                signed=True,
                expires_in=120,
            )
            service.delete_file('file_123')

        self.assertTrue(service.enabled)
        self.assertEqual(
            service.client.init_kwargs,
            {
                'public_key': 'public-key',
                'private_key': 'private-key',
                'url_endpoint': 'https://ik.example.com',
                'transformation_position': None,
                'options': None,
            },
        )
        self.assertEqual(auth, {'token': 'token-123', 'expire': 1234567890, 'signature': 'sig-123'})
        self.assertEqual(url, 'https://ik.example.com/generated-url')
        self.assertEqual(
            service.client.url_calls,
            [
                {
                    'src': 'https://example.com/source.jpg',
                    'transformation': [{'width': 300}, {'height': 200}],
                    'signed': True,
                    'expire_seconds': 120,
                }
            ],
        )
        self.assertEqual(service.client.deleted_files, ['file_123'])
        self.assertEqual(DummyImageKit.instances_created, 1)

    def test_cached_getter_reuses_single_service_instance(self):
        module = self._load_service_module(DummyImageKit)
        settings = SimpleNamespace(
            imagekit_public_key='public-key',
            imagekit_private_key='private-key',
            imagekit_url_endpoint='https://ik.example.com',
            imagekit_enabled=True,
        )

        with patch.object(module, 'get_settings', return_value=settings):
            module.get_imagekit_service.cache_clear()
            first = module.get_imagekit_service()
            second = module.get_imagekit_service()
            module.get_imagekit_service.cache_clear()

        self.assertIs(first, second)
        self.assertIs(first.client, second.client)
        self.assertEqual(DummyImageKit.instances_created, 1)

    def test_service_stays_disabled_without_full_imagekit_config(self):
        module = self._load_service_module(ExplodingImageKit)
        settings = SimpleNamespace(
            imagekit_public_key='',
            imagekit_private_key='private-key',
            imagekit_url_endpoint='',
            imagekit_enabled=False,
        )

        with patch.object(module, 'get_settings', return_value=settings):
            service = module.ImageKitService()

        self.assertFalse(service.enabled)
        self.assertIsNone(service.client)
        self.assertEqual(service.build_url('https://example.com/fallback.jpg'), 'https://example.com/fallback.jpg')
        with self.assertRaises(RuntimeError):
            service.get_authentication_parameters()


if __name__ == '__main__':
    unittest.main()
