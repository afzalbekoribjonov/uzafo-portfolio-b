from __future__ import annotations

import html
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

UZBEK_APOSTROPHE_CHARS = "'`´ʻʼ‘’"
UZBEK_O_PATTERN = re.compile(rf"o[{re.escape(UZBEK_APOSTROPHE_CHARS)}]")
UZBEK_G_PATTERN = re.compile(rf"g[{re.escape(UZBEK_APOSTROPHE_CHARS)}]")
UZBEK_APOSTROPHE_PATTERN = re.compile(rf"[{re.escape(UZBEK_APOSTROPHE_CHARS)}]")
NON_SLUG_PATTERN = re.compile(r"[^a-z0-9\s-]")
WHITESPACE_PATTERN = re.compile(r"\s+")
DASH_PATTERN = re.compile(r"-+")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()



def make_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex}'



def slugify(value: str) -> str:
    normalized = value.lower().strip()
    normalized = UZBEK_O_PATTERN.sub('o', normalized)
    normalized = UZBEK_G_PATTERN.sub('g', normalized)
    normalized = UZBEK_APOSTROPHE_PATTERN.sub('', normalized)
    normalized = NON_SLUG_PATTERN.sub('', normalized)
    normalized = WHITESPACE_PATTERN.sub('-', normalized)
    return DASH_PATTERN.sub('-', normalized).strip('-')



def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged



def ensure_html_paragraph(value: str) -> str:
    if re.search(r'<[^>]+>', value):
        return value
    return f'<p>{html.escape(value)}</p>'



def is_data_url(value: str) -> bool:
    return value.startswith('data:')



def coalesce_text(value: Any, fallback: str = '') -> Any:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        uz = value.get('uz') if isinstance(value.get('uz'), str) else None
        en = value.get('en') if isinstance(value.get('en'), str) else None
        if uz is not None or en is not None:
            return {'uz': uz or en or fallback, 'en': en or uz or fallback}
    if value is None:
        return fallback
    return str(value)


def text_value_to_plain_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get('en') or value.get('uz') or '')
    if hasattr(value, 'en') or hasattr(value, 'uz'):
        return str(getattr(value, 'en', '') or getattr(value, 'uz', '') or '')
    return str(value)
