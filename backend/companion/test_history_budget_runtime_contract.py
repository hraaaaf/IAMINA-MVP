from companion.conversation import _HISTORY_CHAR_BUDGET


def test_runtime_history_budget_uses_certified_frug5_candidate():
    assert _HISTORY_CHAR_BUDGET == 1800
