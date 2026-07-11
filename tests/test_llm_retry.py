"""Verifica el retry con backoff ante errores transitorios del proveedor de LLM
(ej. Gemini 503 'high demand'), sin llamadas de red reales.
"""
import pytest

from backend.agents.llm import MAX_ATTEMPTS, TransientLLMError, _with_retry


class FakeTransientError(Exception):
    pass


class FakePermanentError(Exception):
    pass


def test_retries_and_recovers_from_transient_error():
    calls = {"n": 0}

    def flaky_call():
        calls["n"] += 1
        if calls["n"] < 2:
            raise FakeTransientError("503 high demand")
        return "ok"

    result = _with_retry(flaky_call, is_transient=lambda exc: isinstance(exc, FakeTransientError))
    assert result == "ok"
    assert calls["n"] == 2


def test_raises_transient_llm_error_after_exhausting_attempts():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise FakeTransientError("503 high demand")

    with pytest.raises(TransientLLMError):
        _with_retry(always_fails, is_transient=lambda exc: isinstance(exc, FakeTransientError))
    assert calls["n"] == MAX_ATTEMPTS


def test_does_not_retry_non_transient_errors():
    calls = {"n": 0}

    def bad_request():
        calls["n"] += 1
        raise FakePermanentError("404 model not found")

    with pytest.raises(FakePermanentError):
        _with_retry(bad_request, is_transient=lambda exc: isinstance(exc, FakeTransientError))
    assert calls["n"] == 1
