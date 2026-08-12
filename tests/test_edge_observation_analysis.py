from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


security = load("edge_security_analysis", "infra/edge/scripts/analyze_security_events.py")
csp = load("edge_csp_analysis", "infra/edge/scripts/analyze_csp_reports.py")
assurance = load("edge_assurance", "infra/edge/scripts/assurance_check.py")


def event(
    rule: str,
    classification: str,
    timestamp: datetime,
    *,
    solved: bool | None = None,
    verified_bot: bool = False,
) -> dict:
    return {
        "rule": rule,
        "classification": classification,
        "timestamp": timestamp,
        "verified_bot": verified_bot,
        "challenge_solved": solved,
        "action": "log",
    }


class SecurityObservationAnalysisTests(unittest.TestCase):
    def test_insufficient_evidence_stays_log_only(self) -> None:
        now = datetime.now(timezone.utc)
        report = security.analyze([event("path_traversal_and_probe", "malicious", now)])
        self.assertEqual(report["rules"][0]["recommended_action"], "log")

    def test_low_false_positive_rule_can_be_recommended_for_challenge(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events = [
            event("suspicious_scripted_clients", "malicious", start + timedelta(days=i * 8 / 99))
            for i in range(80)
        ] + [
            event("suspicious_scripted_clients", "unknown", start + timedelta(days=i * 8 / 19))
            for i in range(20)
        ]
        report = security.analyze(events)
        self.assertEqual(report["rules"][0]["recommended_action"], "managed_challenge")

    def test_only_high_confidence_zero_fp_rule_can_reach_block_recommendation(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events = [
            event(
                "path_traversal_and_probe",
                "malicious",
                start + timedelta(days=i * 8 / 99),
                solved=False if i < 20 else None,
            )
            for i in range(100)
        ]
        report = security.analyze(events)
        self.assertEqual(report["rules"][0]["recommended_action"], "block")

    def test_verified_bot_false_positive_prevents_promotion(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        events = [
            event("path_traversal_and_probe", "malicious", start + timedelta(days=i * 8 / 99))
            for i in range(99)
        ]
        events.append(
            event(
                "path_traversal_and_probe",
                "legitimate",
                start + timedelta(days=8),
                verified_bot=True,
            )
        )
        report = security.analyze(events)
        self.assertEqual(report["rules"][0]["recommended_action"], "log")


class CspObservationAnalysisTests(unittest.TestCase):
    def test_csp_analysis_never_auto_widens_and_flags_unknown_sources(self) -> None:
        inventory = {
            "csp_sources": {"script-src": ["'self'", "https://cdn.example"]},
            "manual_review_required": [],
        }
        reports = [
            {"effective_directive": "script-src-elem", "blocked_origin": "https://cdn.example"},
            {"effective_directive": "script-src-elem", "blocked_origin": "https://unknown.example"},
        ]
        result = csp.analyze(reports, inventory)
        self.assertFalse(result["policy_widened_automatically"])
        self.assertFalse(result["enforcement_ready"])
        self.assertEqual(result["unresolved_report_count"], 1)


class EdgeAssuranceTests(unittest.TestCase):
    def test_target_rejects_non_https_or_credentialed_urls(self) -> None:
        with self.assertRaises(ValueError):
            assurance.validate_target("http://staging.example.test")
        with self.assertRaises(ValueError):
            assurance.validate_target("https://user:pass@staging.example.test")

    def test_header_assessment_requires_proxy_and_expected_csp_mode(self) -> None:
        headers = {
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
            "strict-transport-security": "max-age=31536000",
            "permissions-policy": "camera=()",
            "content-security-policy-report-only": "default-src 'self'",
            "cf-ray": "example-YYZ",
        }
        failures, warnings = assurance.assess_headers(
            headers, require_cloudflare=True, csp_mode="report-only"
        )
        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

        failures, _ = assurance.assess_headers(
            {key: value for key, value in headers.items() if key != "cf-ray"},
            require_cloudflare=True,
            csp_mode="report-only",
        )
        self.assertTrue(any("cf-ray" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
