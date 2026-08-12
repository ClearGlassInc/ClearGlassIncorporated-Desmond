from __future__ import annotations

from app.routers.security_reports import normalize_reports


def test_legacy_csp_report_is_privacy_minimized() -> None:
    reports = normalize_reports(
        {
            "csp-report": {
                "document-uri": "https://www.clearglassinc.com/private/path?token=secret#fragment",
                "blocked-uri": "https://cdn.example.test/library.js?customer=42",
                "effective-directive": "script-src-elem",
                "violated-directive": "script-src 'self'",
                "source-file": "https://www.clearglassinc.com/app.js?secret=yes",
                "script-sample": "doNotPersist(userToken)",
                "status-code": 200,
            }
        }
    )
    assert reports == [
        {
            "document_origin": "https://www.clearglassinc.com",
            "blocked_origin": "https://cdn.example.test",
            "effective_directive": "script-src-elem",
            "violated_directive": "script-src 'self'",
            "disposition": "",
            "status_code": 200,
        }
    ]
    serialized = repr(reports)
    assert "token" not in serialized
    assert "doNotPersist" not in serialized


def test_reporting_api_batch_is_bounded_and_ignores_other_report_types() -> None:
    payload = [
        {
            "type": "csp-violation",
            "body": {
                "documentURL": "https://www.clearglassinc.com/",
                "blockedURL": "data:",
                "effectiveDirective": "img-src",
                "statusCode": 200,
                "disposition": "report",
            },
        },
        {"type": "network-error", "body": {"url": "https://secret.invalid/path"}},
    ]
    reports = normalize_reports(payload)
    assert len(reports) == 1
    assert reports[0]["blocked_origin"] == "data"
    assert reports[0]["effective_directive"] == "img-src"


def test_csp_keywords_and_ipv6_are_normalized_without_paths() -> None:
    reports = normalize_reports(
        [
            {
                "type": "csp-violation",
                "body": {
                    "documentURL": "https://[2001:db8::7]/private?id=42",
                    "blockedURL": "inline",
                    "effectiveDirective": "style-src-attr",
                },
            }
        ]
    )
    assert reports[0]["document_origin"] == "https://[2001:db8::7]"
    assert reports[0]["blocked_origin"] == "inline"


def test_malformed_payload_has_no_reports() -> None:
    assert normalize_reports("not-an-object") == []
    assert normalize_reports([{"type": "csp-violation", "body": "wrong"}]) == []
