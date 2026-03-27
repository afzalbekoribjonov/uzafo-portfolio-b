from __future__ import annotations

from typing import Any

from app.schemas.content import ContentBlock
from app.utils.helpers import ensure_html_paragraph, make_id


def normalize_content_blocks(blocks: list[dict[str, Any]] | list[Any] | None, prefix: str) -> list[dict[str, Any]]:
    if not isinstance(blocks, list):
        return []

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(blocks):
        block = raw if isinstance(raw, dict) else {}
        block_id = block.get('id') or make_id(f'{prefix}_block')
        block_type = block.get('type', 'richText')

        if block_type == 'image':
            normalized.append({
                'id': block_id,
                'type': 'image',
                'src': str(block.get('src', '')).strip(),
                'alt': block.get('alt', ''),
                'mediaId': block.get('mediaId'),
            })
            continue

        if block_type == 'video':
            normalized.append({
                'id': block_id,
                'type': 'video',
                'src': str(block.get('src', '')).strip(),
                'caption': block.get('caption', ''),
                'mediaId': block.get('mediaId'),
            })
            continue

        if block_type == 'code':
            normalized.append({
                'id': block_id,
                'type': 'code',
                'language': str(block.get('language') or 'txt'),
                'content': block.get('content', ''),
            })
            continue

        text_value = block.get('content', '')
        if block_type == 'heading':
            text_value = ensure_html_paragraph(str(text_value)).replace('<p>', '<h2>', 1).replace('</p>', '</h2>', 1)
        elif block_type in {'paragraph', 'quote', 'richText'}:
            text_value = ensure_html_paragraph(str(text_value)) if isinstance(text_value, str) else text_value
        normalized.append({
            'id': block_id,
            'type': 'quote' if block_type == 'quote' else 'richText',
            'content': text_value,
        })

    return normalized



def estimate_reading_time(blocks: list[dict[str, Any]]) -> int:
    words = 0
    for block in blocks:
        if block.get('type') in {'image', 'video'}:
            continue
        content = block.get('content', '')
        if isinstance(content, dict):
            content = content.get('en') or content.get('uz') or ''
        content = str(content)
        words += len(content.split())
    return max(1, (words + 179) // 180)
