from functools import lru_cache
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = 'change-me'
DEFAULT_ADMIN_PASSWORD = 'ChangeMe_123'
LOCAL_ALLOWED_ORIGINS = {
    'http://localhost:3000',
    'http://127.0.0.1:3000',
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='UZAFO Portfolio API', alias='APP_NAME')
    app_env: str = Field(default='development', alias='APP_ENV')
    
    
    debug: bool = Field(default=False, alias='DEBUG')
    api_prefix: str = Field(default='/api', alias='API_PREFIX')

    mongo_uri: str = Field(default='mongodb://localhost:27017', alias='MONGO_URI')
    mongo_db: str = Field(default='uzafo_portfolio', alias='MONGO_DB')
    mongo_min_pool_size: int = Field(default=1, alias='MONGO_MIN_POOL_SIZE', ge=0)
    mongo_max_pool_size: int = Field(default=20, alias='MONGO_MAX_POOL_SIZE', ge=1)
    mongo_server_selection_timeout_ms: int = Field(default=5000, alias='MONGO_SERVER_SELECTION_TIMEOUT_MS', ge=1)
    mongo_connect_timeout_ms: int = Field(default=10000, alias='MONGO_CONNECT_TIMEOUT_MS', ge=1)
    mongo_socket_timeout_ms: int = Field(default=10000, alias='MONGO_SOCKET_TIMEOUT_MS', ge=1)
    mongo_wait_queue_timeout_ms: int = Field(default=5000, alias='MONGO_WAIT_QUEUE_TIMEOUT_MS', ge=1)

    jwt_secret: str = Field(default=DEFAULT_JWT_SECRET, alias='JWT_SECRET')
    jwt_algorithm: str = Field(default='HS256', alias='JWT_ALGORITHM')
    access_token_ttl_minutes: int = Field(default=30, alias='ACCESS_TOKEN_TTL_MINUTES')
    refresh_token_ttl_days: int = Field(default=3650, alias='REFRESH_TOKEN_TTL_DAYS')

    admin_name: str = Field(default='Afzalbek Oribjonov', alias='ADMIN_NAME')
    admin_email: str = Field(default='orifjonov0916@gmail.com', alias='ADMIN_EMAIL')
    admin_password: str = Field(default=DEFAULT_ADMIN_PASSWORD, alias='ADMIN_PASSWORD')

    allowed_origins: str = Field(default='http://localhost:3000', alias='ALLOWED_ORIGINS')
    rate_limit_storage: str = Field(default='memory', alias='RATE_LIMIT_STORAGE')
    seed_demo_data: bool = Field(default=False, alias='SEED_DEMO_DATA')

    imagekit_public_key: str = Field(default='', alias='IMAGEKIT_PUBLIC_KEY')
    imagekit_private_key: str = Field(default='', alias='IMAGEKIT_PRIVATE_KEY')
    imagekit_url_endpoint: str = Field(default='', alias='IMAGEKIT_URL_ENDPOINT')
    imagekit_webhook_secret: str = Field(default='', alias='IMAGEKIT_WEBHOOK_SECRET')
    upload_auth_ttl_seconds: int = Field(default=600, alias='UPLOAD_AUTH_TTL_SECONDS')

    max_image_size_mb: int = Field(default=10, alias='MAX_IMAGE_SIZE_MB')
    max_video_size_mb: int = Field(default=100, alias='MAX_VIDEO_SIZE_MB')

    @property
    def allowed_origins_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_origins.split(',') if item.strip()]

    @property
    def imagekit_enabled(self) -> bool:
        return bool(self.imagekit_public_key and self.imagekit_private_key and self.imagekit_url_endpoint)

    @model_validator(mode='after')
    def validate_production_settings(self) -> 'Settings':
        if self.app_env.lower() != 'production':
            return self

        errors: list[str] = []
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            errors.append('JWT_SECRET must be overridden in production.')
        if self.admin_password == DEFAULT_ADMIN_PASSWORD:
            errors.append('ADMIN_PASSWORD must be overridden in production.')

        origins = self.allowed_origins_list
        if not origins:
            errors.append('ALLOWED_ORIGINS must not be empty in production.')
        elif all(origin in LOCAL_ALLOWED_ORIGINS for origin in origins):
            errors.append('ALLOWED_ORIGINS must include your deployed frontend origin in production.')

        if errors:
            raise ValueError(' '.join(errors))

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
