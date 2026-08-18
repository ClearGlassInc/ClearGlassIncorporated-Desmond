from mail.parser.clearglass_incoming_parser import clearglass_incoming_parser


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


def test_rejects_oversized_message():
    try:
        clearglass_incoming_parser(b"x" * 10, max_bytes=9)
    except ValueError as exc:
        assert "size limit" in str(exc)
    else:
        raise AssertionError("oversized message was accepted")
