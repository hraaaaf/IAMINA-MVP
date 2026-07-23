"""
Tests for core.account_hooks — RGPD Art. 17 account deletion hook registry.

T1: A registered hook is called when run_account_delete_hooks() executes.
T2: A hook that raises an exception causes run_account_delete_hooks() to raise RuntimeError.
T3: Multiple hooks — a first hook failure does NOT prevent subsequent hooks from running;
    all hooks execute, then errors are collected and raised together.
"""
import pytest

from core import account_hooks


@pytest.fixture(autouse=True)
def reset_hooks():
    """Isolate each test: clear the global hook list before and after."""
    original = account_hooks._hooks[:]
    account_hooks._hooks.clear()
    yield
    account_hooks._hooks.clear()
    account_hooks._hooks.extend(original)


# ── T1 ──────────────────────────────────────────────────────────────────────

def test_registered_hook_is_called():
    """A hook registered via register_account_delete_hook() must be invoked."""
    calls = []

    def my_hook(patient_id: int, firebase_uid: str) -> None:
        calls.append((patient_id, firebase_uid))

    account_hooks.register_account_delete_hook(my_hook)
    account_hooks.run_account_delete_hooks(42, "uid-abc")

    assert calls == [(42, "uid-abc")]


# ── T2 ──────────────────────────────────────────────────────────────────────

def test_hook_exception_raises_runtime_error():
    """A hook that raises must cause run_account_delete_hooks() to raise RuntimeError."""

    def bad_hook(patient_id: int, firebase_uid: str) -> None:
        raise ValueError("cache unavailable")

    account_hooks.register_account_delete_hook(bad_hook)

    with pytest.raises(RuntimeError, match="Account delete hooks failed"):
        account_hooks.run_account_delete_hooks(1, "uid-xyz")


# ── T3 ──────────────────────────────────────────────────────────────────────

def test_all_hooks_run_before_error_raised():
    """
    When the first hook fails, subsequent hooks must still execute.
    All errors are collected, then raised together in a single RuntimeError.
    """
    second_called = []

    def first_hook(patient_id: int, firebase_uid: str) -> None:
        raise RuntimeError("first hook blew up")

    def second_hook(patient_id: int, firebase_uid: str) -> None:
        second_called.append(patient_id)

    account_hooks.register_account_delete_hook(first_hook)
    account_hooks.register_account_delete_hook(second_hook)

    with pytest.raises(RuntimeError) as exc_info:
        account_hooks.run_account_delete_hooks(7, "uid-multi")

    # Second hook still ran despite first failing
    assert second_called == [7]
    # RuntimeError message contains the first hook's error
    assert "first hook blew up" in str(exc_info.value)
