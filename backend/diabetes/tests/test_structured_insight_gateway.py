from types import SimpleNamespace

from core.contracts.capabilities import Capability
from diabetes.services.clinical import engine


def _pattern() -> engine.ClinicalPattern:
    return engine.ClinicalPattern(
        code="TEST_PATTERN",
        priority=2,
        icon="activity",
        title="Observation test",
        evidence="Evidence déterministe de test.",
        fallback_content="Observation de secours.",
        fallback_action="À discuter avec votre médecin.",
    )


def test_structured_formatter_uses_deterministic_pattern_capability(monkeypatch):
    calls = []

    class FakeGateway:
        def complete(self, system, user, capability):
            calls.append((system, user, capability))
            return SimpleNamespace(
                content=(
                    '[{"code":"TEST_PATTERN","title":"Observation test",'
                    '"content":"Observation reformulée.",'
                    '"action":"À discuter avec votre médecin."}]'
                )
            )

    monkeypatch.setattr(engine, "get_gateway_llm", lambda: FakeGateway())

    result = engine._format_with_llm([_pattern()], language="fr")

    assert len(calls) == 1
    assert calls[0][2] is Capability.SURFACE_DETERMINISTIC_PATTERN
    assert result[0]["code"] == "TEST_PATTERN"
    assert result[0]["content"] == "Observation reformulée."


def test_structured_formatter_preserves_template_fallback_on_gateway_failure(monkeypatch):
    class FailingGateway:
        def complete(self, system, user, capability):
            raise RuntimeError("synthetic provider failure")

    monkeypatch.setattr(engine, "get_gateway_llm", lambda: FailingGateway())

    result = engine._format_with_llm([_pattern()], language="fr")

    assert result[0]["code"] == "TEST_PATTERN"
    assert result[0]["content"] == "Observation de secours."
