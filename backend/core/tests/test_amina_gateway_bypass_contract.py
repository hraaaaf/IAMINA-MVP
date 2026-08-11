from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_ai_api_does_not_reintroduce_direct_text_provider_access():
    source = (REPO_ROOT / "backend" / "ai" / "api" / "v1" / "ai.py").read_text()

    assert "from llm.factory import get_llm" not in source
    assert "get_llm()" not in source
    assert "get_gateway_llm" in source
    assert "Capability.SUMMARIZE_APPROVED_DATA" in source


def test_known_structured_formatter_exception_remains_explicitly_bounded():
    source = (
        REPO_ROOT
        / "backend"
        / "diabetes"
        / "services"
        / "clinical"
        / "engine.py"
    ).read_text()

    assert "def _format_with_llm" in source
    assert "assert_ai_egress_allowed(TEXT)" in source
    assert "sanitize_patient_visible" in source
