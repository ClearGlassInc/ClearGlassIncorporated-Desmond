"""Defensive RFC 5322/MIME normalization for ClearGlass Mail.

This module uses only Python's standard library. It treats all message content
as untrusted and returns normalized metadata suitable for a downstream policy
and storage layer. It does not execute attachments or render HTML.
"""

from __future__ import annotations

import hashlib
import re
from email import policy
from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesParser
from email.utils import parseaddr
from typing import Any

DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_PARTS = 256
DEFAULT_MAX_HEADER_LENGTH = 16 * 1024

_HTML_TAG_RE = re.compile(r"<[^>]*>")
_WHITESPACE_RE = re.compile(r"\s+")


def _decode_header(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(make_header(decode_header(value))).strip()
    except (LookupError, UnicodeError, ValueError):
        return value.strip()


def _address(value: str | None) -> dict[str, str | None]:
    display, address = parseaddr(value or "")
    return {"name": _decode_header(display) or None, "address": address or None}


def _text_from_html(html: str) -> str:
    text = _HTML_TAG_RE.sub(" ", html)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _body_part(part: Message) -> str:
    try:
        content = part.get_content()
    except (LookupError, UnicodeError, ValueError):
        return ""
    return content if isinstance(content, str) else ""


def clearglass_incoming_parser(
    raw_email_data: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_parts: int = DEFAULT_MAX_PARTS,
) -> dict[str, Any]:
    """Parse a raw message with explicit resource limits and provenance.

    Raises ValueError for messages outside the configured resource envelope.
    The original bytes are never modified; only their SHA-256 digest is stored.
    """
    if not isinstance(raw_email_data, bytes):
        raise TypeError("raw_email_data must be bytes")
    if len(raw_email_data) > max_bytes:
        raise ValueError("message exceeds configured size limit")

    message_sha256 = hashlib.sha256(raw_email_data).hexdigest()
    msg = BytesParser(policy=policy.default).parsebytes(raw_email_data)

    parts = list(msg.walk())
    if len(parts) > max_parts:
        raise ValueError("message exceeds configured MIME part limit")

    for name, value in msg.raw_items():
        if len(name) > DEFAULT_MAX_HEADER_LENGTH or len(value) > DEFAULT_MAX_HEADER_LENGTH:
            raise ValueError("message contains an oversized header")

    plain_text = ""
    html_text = ""
    attachments: list[dict[str, Any]] = []

    for part in parts:
        if part.is_multipart():
            continue

        disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        filename = _decode_header(part.get_filename())

        if disposition == "attachment" or filename:
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                {
                    "filename": filename,
                    "content_type": content_type,
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
            continue

        body = _body_part(part)
        if content_type == "text/plain" and not plain_text:
            plain_text = body
        elif content_type == "text/html" and not html_text:
            html_text = body

    return {
        "schema_version": "1.0",
        "message_sha256": message_sha256,
        "subject": _decode_header(msg.get("subject")),
        "from": _address(msg.get("from")),
        "to": _address(msg.get("to")),
        "cc": _address(msg.get("cc")),
        "date": msg.get("date"),
        "message_id": msg.get("message-id"),
        "body": {
            "plain": plain_text,
            "html": html_text,
            "preview": plain_text.strip() or _text_from_html(html_text),
        },
        "attachments": attachments,
        "policy": {
            "content_untrusted": True,
            "html_requires_sanitization": bool(html_text),
            "attachments_require_scanning": bool(attachments),
        },
    }


if __name__ == "__main__":
    import json
    import sys

    parsed = clearglass_incoming_parser(sys.stdin.buffer.read())
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
