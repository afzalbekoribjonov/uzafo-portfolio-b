from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from imagekitio import ImageKit

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ImageKitService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = (
            ImageKit(
                public_key=settings.imagekit_public_key,
                private_key=settings.imagekit_private_key,
                url_endpoint=settings.imagekit_url_endpoint,
            )
            if settings.imagekit_enabled
            else None
        )

    @property
    def enabled(self) -> bool:
        return self.settings.imagekit_enabled and self.client is not None

    def get_authentication_parameters(self) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError('ImageKit is not configured.')
        return self.client.get_authentication_parameters()

    def build_url(self, src: str, transformation: list[dict[str, Any]] | None = None, signed: bool = False, expires_in: int | None = None) -> str:
        if not self.enabled:
            return src
        options: dict[str, Any] = {
            'src': src,
        }
        if transformation:
            options['transformation'] = transformation
        if signed:
            options['signed'] = True
        if expires_in:
            options['expire_seconds'] = expires_in
        return self.client.url(options)

    def delete_file(self, file_id: str) -> None:
        if not self.enabled:
            logger.warning('ImageKit delete skipped because configuration is missing.')
            return
        # The SDK exposes file management APIs; the runtime dependency resolves the exact method.
        self.client.delete_file(file_id)


@lru_cache(maxsize=1)
def get_imagekit_service() -> ImageKitService:
    return ImageKitService()
