import pytest

from mail.parser.clearglass_incoming_parser import (
    PARSER_SCHEMA_VERSION,
    clearglass_incoming_parser,
)


def test_parses_plain_text_and_provenance():
    raw = (
        b"From: GitHub <noreply@github.com>\r\n"
        b"To: mail@example.test\r\n"
        b"Subject: =?utf-8?q?Export_ready?=\r\n"
        b"Message-ID: <abc@example.test>\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"Your export is ready.\r\n"
    )

    parsed = clearglass_incoming_parser(raw)

    assert parsed["schema_version"] == PARSER_SCHEMA_VERSION
    assert parsed["subject"] == "Export ready"
    assert parsed["from"]["address"] == "noreply@github.com"
    assert parsed["body"]["plain"] == "Your export is ready.\n"
    assert len(parsed["message_sha256"]) == 64
    assert parsed["policy"]["content_untrusted"] is True


def test_records_attachment_digest_without_executing_it():
    raw = (
        b"From: sender@example.test\r\n"
        b"To: mail@example.test\r\n"
        b"Subject: Attachment\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=BOUND\r\n"
        b"\r\n"
        b"--BOUND\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"hello\r\n"
        b"--BOUND\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Disposition: attachment; filename=sample.bin\r\n"
        b"Content-Transfer-Encoding: base64\r\n"
        b"\r\n"
        b"aGVsbG8=\r\n"
        b"--BOUND--\r\n"
    )

    parsed = clearglass_incoming_parser(raw)

    assert parsed["attachments"][0]["filename"] == "sample.bin"
    assert parsed["attachments"][0]["size"] == 5
    assert parsed["policy"]["attachments_require_scanning"] is True
    assert parsed["policy"]["attachment_bytes"] == 5


def test_html_preview_ignores_script_and_normalizes_text():
    raw = (
        b"From: sender@example.test\r\n"
        b"To: mail@example.test\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body>Hello &amp; welcome<script>alert('x')</script> world</body></html>"
    )

    parsed = clearglass_incoming_parser(raw)

    assert parsed["body"]["preview"] == "Hello & welcome world"
    assert parsed["policy"]["html_requires_sanitization"] is True


def test_records_transport_authentication_headers():
    raw = (
        b"From: sender@example.test\r\n"
        b"To: mail@example.test\r\n"
        b"Authentication-Results: mx.example; dkim=pass\r\n"
        b"Received: by mx.example; Tue, 18 Aug 2026 12:00:00 +0000\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"hello\r\n"
    )

    parsed = clearglass_incoming_parser(raw)

    assert parsed["transport_headers"]["authentication-results"]
    assert parsed["transport_headers"]["received"]


def test_rejects_oversized_message():
    with pytest.raises(ValueError, match="size limit"):
        clearglass_incoming_parser(b"x" * 10, max_bytes=9)


def test_rejects_oversized_attachment():
    raw = (
        b"From: sender@example.test\r\n"
        b"To: mail@example.test\r\n"
        b"Content-Type: multipart/mixed; boundary=BOUND\r\n"
        b"\r\n"
        b"--BOUND\r\n"
        b"Content-Type: application/octet-stream\r\n"
        b"Content-Disposition: attachment; filename=sample.bin\r\n"
        b"\r\n"
        b"12345\r\n"
        b"--BOUND--\r\n"
    )

    with pytest.raises(ValueError, match="attachment exceeds"):
        clearglass_incoming_parser(raw, max_attachment_bytes=4)


def test_rejects_excessive_header_count():
    headers = b"".join(f"X-Test-{index}: value\r\n".encode() for index in range(10))
    raw = headers + b"Content-Type: text/plain\r\n\r\nhello\r\n"

    with pytest.raises(ValueError, match="header count"):
        clearglass_incoming_parser(raw, max_header_count=5)


def test_rejects_invalid_resource_limits():
    with pytest.raises(ValueError, match="resource limits"):
        clearglass_incoming_parser(b"From: x@example.test\r\n\r\nhello", max_parts=0)
