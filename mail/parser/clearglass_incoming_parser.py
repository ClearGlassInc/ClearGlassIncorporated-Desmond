"""Defensive RFC 5322/MIME normalization for ClearGlass Mail.

The parser is deliberately provider-agnostic and standard-library only. All
message data is treated as untrusted. The module does not render HTML, execute
attachments, access the network, or persist message content.
"""

from __future__ import annotations

import hashlib
import re
from email import policy
from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesParser
from email.utils import parseaddr
from html import unescape
from html.parser import HTMLParser
from typing import Any

PARSER_SCHEMA_VERSION = "1.1"
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_PARTS = 256
DEFAULT_MAX_HEADER_COUNT = 128
DEFAULT_MAX_HEADER_BYTES = 64 * 1024
DEFAULT_MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_TOTAL_ATTACHMENT_BYTES = 20 * 1024 * 1024
DEFAULT_MAX_PREVIEW_CHARS = 500

_WHITESPACE_RE = re.compile(r"\s+")


class _VisibleTextExtractor(HTMLParser):
    """Extract conservative visible text for previews; this is not an HTML sanitizer."""

    _IGNORED_ELEMENTS = {"script", "style", "template", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._IGNORED_ELEMENTS:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._IGNORED_ELEMENTS and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


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


def _text_from_html(html: str, *, max_chars: int) -> str:
    extractor = _VisibleTextExtractor()
    try:
        extractor.feed(html)
        extractor.close()
        text = unescape(" ".join(extractor.parts))
    except (AssertionError, ValueError):
        # Preview generation must never make an otherwise parseable message fail.
        text = re.sub(r"<[^>]*>", " ", html)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:max_chars]


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
    max_header_count: int = DEFAULT_MAX_HEADER_COUNT,
    max_header_bytes: int = DEFAULT_MAX_HEADER_BYTES,
    max_attachment_bytes: int = DEFAULT_MAX_ATTACHMENT_BYTES,
    max_total_attachment_bytes: int = DEFAULT_MAX_TOTAL_ATTACHMENT_BYTES,
    max_preview_chars: int = DEFAULT_MAX_PREVIEW_CHARS,
) -> dict[str, Any]:
    """Parse a raw message with explicit resource limits and provenance.

    Raises ``ValueError`` for messages outside the configured resource envelope.
    The original bytes are never modified; only cryptographic digests are
    retained in the normalized result.
    """
    if not isinstance(raw_email_data, bytes):
        raise TypeError("raw_email_data must be bytes")
    if max_bytes < 0 or len(raw_email_data) > max_bytes:
        raise ValueError("message exceeds configured size limit")
    if max_parts < 1 or max_header_count < 1 or max_header_bytes < 1:
        raise ValueError("resource limits must be positive")
    if max_attachment_bytes < 0 or max_total_attachment_bytes < 0:
        raise ValueError("attachment limits must be non-negative")
    if max_preview_chars < 0:
        raise ValueError("preview limit must be non-negative")

    message_sha256 = hashlib.sha256(raw_email_data).hexdigest()
    msg = BytesParser(policy=policy.default).parsebytes(raw_email_data)

    parts = list(msg.walk())
    if len(parts) > max_parts:
        raise ValueError("message exceeds configured MIME part limit")

    headers = list(msg.raw_items())
    if len(headers) > max_header_count:
        raise ValueError("message exceeds configured header count limit")
    for name, value in headers:
        encoded_size = len(name.encode("utf-8", "replace")) + len(
            value.encode("utf-8", "replace")
        )
        if encoded_size > max_header_bytes:
            raise ValueError("message contains an oversized header")

    plain_text = ""
    html_text = ""
    attachments: list[dict[str, Any]] = []
    total_attachment_bytes = 0

    for part in parts:
        if part.is_multipart():
            continue

        disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        filename = _decode_header(part.get_filename())

        if disposition == "attachment" or filename:
            payload = part.get_payload(decode=True) or b""
            if len(payload) > max_attachment_bytes:
                raise ValueError("attachment exceeds configured size limit")
            total_attachment_bytes += len(payload)
            if total_attachment_bytes > max_total_attachment_bytes:
                raise ValueError("attachments exceed configured aggregate size limit")
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

    preview = plain_text.strip()[:max_preview_chars]
    if not preview and html_text:
        preview = _text_from_html(html_text, max_chars=max_preview_chars)

    transport_headers: dict[str, list[str]] = {}
    for header_name in ("received", "authentication-results", "dkim-signature", "arc-authentication-results"):
        values = [_decode_header(value) for name, value in headers if name.lower() == header_name]
        transport_headers[header_name] = [value for value in values if value is not None]

    return {
        "schema_version": PARSER_SCHEMA_VERSION,
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
            "preview": preview,
        },
        "attachments": attachments,
        "transport_headers": transport_headers,
        "policy": {
            "content_untrusted": True,
            "html_requires_sanitization": bool(html_text),
            "attachments_require_scanning": bool(attachments),
            "attachment_bytes": total_attachment_bytes,
        },
    }


if __name__ == "__main__":
    import json
    import sys

    parsed = clearglass_incoming_parser(sys.stdin.buffer.read())
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
