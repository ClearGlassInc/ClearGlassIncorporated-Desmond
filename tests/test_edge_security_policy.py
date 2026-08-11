from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "infra" / "edge" / "scripts" / "validate_policy.py"
POLICY_PATH = ROOT / "infra" / "edge" / "policies" / "baseline.json"
SCHEMA_PATH = ROOT / "infra" / "edge" / "policy.schema.json"
SAFETY_PATH = ROOT / "infra" / "edge" / "scripts" / "validate_terraform_safety.py"

spec = importlib.util.spec_from_file_location("edge_policy_validator", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

safety_spec = importlib.util.spec_from_file_location("edge_terraform_safety", SAFETY_PATH)
assert safety_spec and safety_spec.loader
safety = importlib.util.module_from_spec(safety_spec)
safety_spec.loader.exec_module(safety)


def baseline() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


class EdgePolicySafetyTests(unittest.TestCase):
    def validate_environment(self, config: dict) -> list[str]:
        errors: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "environment.tfvars.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            safety.validate_environment(path, baseline()["version"], errors)
        return errors

    def test_edge_baseline_policy_is_safe(self) -> None:
        self.assertEqual(validator.validate(baseline()), [])

    def test_geo_enforcement_cannot_be_enabled_in_baseline(self) -> None:
        policy = baseline()
        policy["defaults"]["geo_enforcement_enabled"] = True
        errors = validator.validate(policy)
        self.assertTrue(any("geo_enforcement_enabled must be false" in error for error in errors))

    def test_broad_terminal_block_is_rejected(self) -> None:
        policy = baseline()
        rule = copy.deepcopy(policy["rules"][0])
        rule.update(
            {
                "id": "test.broad-block",
                "priority": 99999,
                "scope": "all",
                "action": "block",
                "rollout_mode": "enforce",
                "category": "custom_waf",
                "description": "Unsafe broad block for regression testing only.",
                "rationale": "Regression test.",
            }
        )
        policy["rules"].append(rule)
        errors = validator.validate(policy)
        self.assertTrue(any("broad enabled block over scope=all is prohibited" in error for error in errors))

    def test_permanent_reputation_only_block_is_rejected(self) -> None:
        policy = baseline()
        rule = next(rule for rule in policy["rules"] if rule["category"] == "ip_reputation")
        rule["action"] = "block"
        rule["rollout_mode"] = "enforce"
        rule["expires_at"] = None
        errors = validator.validate(policy)
        self.assertTrue(any("reputation-only block requires expiry" in error for error in errors))

    def test_sensitive_logging_default_cannot_be_enabled(self) -> None:
        policy = baseline()
        policy["defaults"]["log_sensitive_fields"] = True
        errors = validator.validate(policy)
        self.assertTrue(any("log_sensitive_fields must be false" in error for error in errors))

    def test_schema_rejects_unknown_properties(self) -> None:
        policy = baseline()
        policy["rules"][0]["silent_bypass"] = True
        errors = validator.validate(policy)
        self.assertTrue(any("unknown property 'silent_bypass'" in error for error in errors))

    def test_required_route_rate_limits_are_present(self) -> None:
        scopes = {
            rule["scope"]
            for rule in baseline()["rules"]
            if rule["category"] == "rate_limit"
        }
        self.assertTrue(
            {"assets", "html", "login", "password-reset", "search", "forms", "api", "admin", "webhooks"}.issubset(scopes)
        )

    def test_provider_application_is_not_claimed(self) -> None:
        self.assertFalse(baseline()["defaults"]["provider_changes_applied"])

    def test_custom_waf_baseline_is_log_only(self) -> None:
        rules = [rule for rule in baseline()["rules"] if rule["category"] == "custom_waf"]
        self.assertTrue(rules)
        self.assertTrue(all(rule["action"] == "log" for rule in rules))
        self.assertTrue(all(rule["rollout_mode"] == "observe" for rule in rules))

    def test_reviewed_observe_environment_can_enable_log_only_waf(self) -> None:
        config = json.loads((ROOT / "infra" / "edge" / "environments" / "staging.tfvars.json").read_text())
        config.update(
            {
                "rollout_stage": "observe",
                "deployment_change_ticket": "CHG-1234",
                "configuration_rationale": "Enable custom WAF telemetry in staging.",
                "enable_custom_waf": True,
            }
        )
        self.assertEqual(self.validate_environment(config), [])

    def test_observe_environment_rejects_block_action(self) -> None:
        config = json.loads((ROOT / "infra" / "edge" / "environments" / "staging.tfvars.json").read_text())
        config.update(
            {
                "rollout_stage": "observe",
                "deployment_change_ticket": "CHG-1234",
                "configuration_rationale": "Regression test for terminal action guard.",
                "enable_custom_waf": True,
            }
        )
        config["custom_waf_actions"]["path_probe"] = "block"
        errors = self.validate_environment(config)
        self.assertTrue(any("observe custom WAF must be log-only" in error for error in errors))

    def test_disabled_templates_cannot_be_silently_enabled(self) -> None:
        policy = baseline()
        emergency = next(rule for rule in policy["rules"] if rule["category"] == "emergency")
        emergency["enabled"] = True
        errors = validator.validate(policy)
        self.assertTrue(any("disabled rollout cannot be enabled" in error for error in errors))

    def test_layer_allow_must_retain_managed_waf(self) -> None:
        policy = baseline()
        verified = next(rule for rule in policy["rules"] if rule["id"] == "bot.verified-crawlers")
        verified["scope"] = "all"
        verified["exceptions"] = []
        errors = validator.validate(policy)
        self.assertTrue(any("allow must be layer-scoped" in error for error in errors))

    def test_cloudflare_adapter_has_no_dns_resource(self) -> None:
        terraform = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "infra" / "edge").glob("*.tf"))
        )
        self.assertNotIn('resource "cloudflare_record"', terraform)
        self.assertNotIn('resource "cloudflare_dns_record"', terraform)

    def test_managed_waf_covers_all_configured_hosts(self) -> None:
        waf = (ROOT / "infra" / "edge" / "waf.tf").read_text(encoding="utf-8")
        self.assertGreaterEqual(waf.count("expression  = local.protected_host_scope"), 2)

    def test_webhook_rate_limit_never_uses_browser_challenge_default(self) -> None:
        variables = (ROOT / "infra" / "edge" / "variables.tf").read_text(encoding="utf-8")
        rates = (ROOT / "infra" / "edge" / "rate_limits.tf").read_text(encoding="utf-8")
        self.assertIn('lookup(var.rate_limit_actions, "webhook", "log")', rates)
        self.assertIn('lookup(var.rate_limit_actions, "webhook", "log") != "managed_challenge"', variables)

    def test_remote_state_backend_is_declared(self) -> None:
        backend = (ROOT / "infra" / "edge" / "backend.tf").read_text(encoding="utf-8")
        self.assertIn('backend "s3"', backend)

    def test_policy_schema_is_current_and_parseable(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
