from datetime import UTC, datetime

import pytest

from artemis.operations import FeatureFlag, FeatureFlags, JobLifecycle, JobTelemetry, default_registry


def test_registry_has_complete_operational_contracts_and_disabled_external_jobs() -> None:
    registry = default_registry()

    assert {job.name for job in registry.all()} == {
        "artemis.feedback-eval-compiler",
        "artemis.improvement-proposal",
        "artemis.mission-triage",
    }
    assert registry.get("artemis.improvement-proposal").lifecycle is JobLifecycle.DISABLED
    assert registry.get("artemis.mission-triage").feature_flag == "live_data"
    with pytest.raises(KeyError, match="unregistered job"):
        registry.get("unknown")


def test_sensitive_flags_fail_closed_and_require_approval() -> None:
    assert FeatureFlags().enabled("ai") is False
    assert FeatureFlags().enabled("unregistered") is False
    with pytest.raises(ValueError, match="approval reference"):
        FeatureFlags({"email": FeatureFlag("email", enabled=True)})

    flags = FeatureFlags(
        {"ai": FeatureFlag("ai", enabled=True, approval_reference="CAB-2026-0042")}
    )
    assert flags.enabled("ai") is True
    assert flags.enabled("billing") is False


def test_telemetry_emits_correlated_structured_audit_and_metric() -> None:
    telemetry = JobTelemetry(default_registry())
    event = telemetry.record(
        "artemis.feedback-eval-compiler",
        JobLifecycle.SUCCEEDED,
        correlation_id="artemis-test-0001",
        detail={"eval_count": "3"},
        now=datetime(2026, 8, 10, 12, tzinfo=UTC),
    )

    assert telemetry.metrics[(event.job_name, "succeeded")] == 1
    assert event.as_json() == (
        '{"correlation_id":"artemis-test-0001","detail":{"eval_count":"3"},'
        '"event":"job.succeeded","job_name":"artemis.feedback-eval-compiler",'
        '"occurred_at":"2026-08-10T12:00:00+00:00","state":"succeeded"}'
    )


@pytest.mark.parametrize("key", ["secret", "TOKEN", "Password"])
def test_telemetry_rejects_sensitive_detail(key: str) -> None:
    with pytest.raises(ValueError, match="sensitive"):
        JobTelemetry(default_registry()).record(
            "artemis.feedback-eval-compiler",
            JobLifecycle.FAILED,
            correlation_id="artemis-test-0002",
            detail={key: "must-not-be-logged"},
        )
