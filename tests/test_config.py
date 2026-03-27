import unittest

from pydantic import ValidationError

from app.core.config import Settings


class SettingsValidationTests(unittest.TestCase):
    def test_production_requires_custom_jwt_secret(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                APP_ENV='production',
                DEBUG=False,
                JWT_SECRET='change-me',
                ADMIN_PASSWORD='StrongPassword_123',
                ALLOWED_ORIGINS='https://uzafo.site',
            )

    def test_production_requires_custom_admin_password(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                APP_ENV='production',
                DEBUG=False,
                JWT_SECRET='super-secret-value',
                ADMIN_PASSWORD='ChangeMe_123',
                ALLOWED_ORIGINS='https://uzafo.site',
            )

    def test_production_requires_non_local_allowed_origins(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                APP_ENV='production',
                DEBUG=False,
                JWT_SECRET='super-secret-value',
                ADMIN_PASSWORD='StrongPassword_123',
                ALLOWED_ORIGINS='http://localhost:3000,http://127.0.0.1:3000',
            )

    def test_production_accepts_deployed_frontend_origins(self):
        settings = Settings(
            _env_file=None,
            APP_ENV='production',
            DEBUG=False,
            JWT_SECRET='super-secret-value',
            ADMIN_PASSWORD='StrongPassword_123',
            ALLOWED_ORIGINS='https://uzafo.site,https://www.uzafo.site',
        )

        self.assertEqual(
            settings.allowed_origins_list,
            ['https://uzafo.site', 'https://www.uzafo.site'],
        )


if __name__ == '__main__':
    unittest.main()
