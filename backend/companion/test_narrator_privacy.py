"""V1-03: local log-safety regression for the legacy narrator (synthetic only)."""
import logging
from types import SimpleNamespace
from unittest.mock import patch

from companion.narrator import summarize


def test_narrator_does_not_log_generated_clinical_text_or_patient_identity(caplog):
    secret_brief = "SYNTHETIC PRIVATE doctor brief 999 mg/dL"
    patient = SimpleNamespace(id=91357)
    memory = SimpleNamespace(current_tone="neutral")
    context = SimpleNamespace(
        has_sufficient_data=True,
        pivot_text="Synthetic permitted descriptive context only",
        patterns_detail=[],
    )

    class FakeLLM:
        def complete(self, _system, _user):
            return SimpleNamespace(
                content=(
                    '{"narrative":"Résumé descriptif, sans conclusion médicale.",'
                    '"key_insight":"Observation seulement.",'
                    f'"doctor_brief":"{secret_brief}"' + "}"
                )
            )

    with (
        patch("companion.narrator.get_domain_context", return_value=context),
        caplog.at_level(logging.INFO, logger="companion.narrator"),
    ):
        result = summarize(patient, memory, llm=FakeLLM(), language="fr", days=7)

    assert "Résumé descriptif" in result
    assert "doctor_brief generated" in caplog.text
    assert secret_brief not in caplog.text
    assert "91357" not in caplog.text
