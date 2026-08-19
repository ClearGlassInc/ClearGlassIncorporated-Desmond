import pytest

from clearglassinc_sdk.retry import NO_RETRY, RetryPolicy, is_retryable


@pytest.mark.parametrize(
    "message",
    ["503 service unavailable", "Connection reset", "RateLimitError", "request timed out", "overloaded"],
)
def test_transient_errors_are_retryable(message):
    assert is_retryable(RuntimeError(message))


@pytest.mark.parametrize(
    "message",
    ["401 authentication failed", "invalid request", "404 not found", "permission denied"],
)
def test_terminal_errors_are_not_retryable(message):
    assert not is_retryable(RuntimeError(message))


def test_unknown_errors_are_not_retried_by_default():
    assert not is_retryable(ValueError("something entirely unexpected"))


def test_delay_grows_exponentially_and_is_capped():
    policy = RetryPolicy(base_delay=1.0, max_delay=4.0, jitter=False)
    assert policy.delay_for(1) == 1.0
    assert policy.delay_for(2) == 2.0
    assert policy.delay_for(3) == 4.0
    assert policy.delay_for(9) == 4.0  # capped


def test_jitter_keeps_delay_within_half_of_the_raw_value():
    policy = RetryPolicy(base_delay=2.0, max_delay=10.0, jitter=True)
    for _ in range(20):
        assert 1.0 <= policy.delay_for(1) <= 2.0


def test_call_retries_transient_failures_then_succeeds():
    policy = RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("503 service unavailable")
        return "ok"

    assert policy.call(flaky) == "ok"
    assert calls["n"] == 3


def test_call_gives_up_after_max_attempts():
    policy = RetryPolicy(max_attempts=2, base_delay=0.001, jitter=False)
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise RuntimeError("503 service unavailable")

    with pytest.raises(RuntimeError):
        policy.call(always_fails)
    assert calls["n"] == 2


def test_call_does_not_retry_terminal_errors():
    policy = RetryPolicy(max_attempts=5, base_delay=0.001, jitter=False)
    calls = {"n": 0}

    def auth_failure():
        calls["n"] += 1
        raise RuntimeError("401 authentication failed")

    with pytest.raises(RuntimeError):
        policy.call(auth_failure)
    assert calls["n"] == 1


def test_no_retry_policy_calls_once():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise RuntimeError("503 service unavailable")

    with pytest.raises(RuntimeError):
        NO_RETRY.call(always_fails)
    assert calls["n"] == 1


async def test_acall_retries_transient_failures():
    policy = RetryPolicy(max_attempts=3, base_delay=0.001, jitter=False)
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("connection reset")
        return "ok"

    assert await policy.acall(flaky) == "ok"
    assert calls["n"] == 2
