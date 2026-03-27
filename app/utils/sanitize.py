from __future__ import annotations

from typing import Any

import bleach

from app.utils.helpers import ensure_html_paragraph

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'blockquote', 'code', 'pre', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'span'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'span': ['class'],
}


def _sanitize_plain(value: str) -> str:
    return bleach.clean(value, tags=[], attributes={}, strip=True).strip()


def sanitize_plain_text_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_plain(value)
    if isinstance(value, dict):
        return {locale: _sanitize_plain(str(value.get(locale, ''))) for locale in ('uz', 'en')}
    return value


def sanitize_rich_text_value(value: Any) -> Any:
    if isinstance(value, str):
        return bleach.clean(ensure_html_paragraph(value), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    if isinstance(value, dict):
        return {
            locale: bleach.clean(ensure_html_paragraph(str(value.get(locale, ''))), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
            for locale in ('uz', 'en')
        }
    return value
