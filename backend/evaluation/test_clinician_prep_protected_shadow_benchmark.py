import subprocess
import sys
from datetime import date

from companion.narration_envelope import verify_and_reinject_protected_narration
from diabetes.services.clinical.clinician_prep_protected_narration_verifier import (
    verify_clinician_prep_protected_narration,
)
from evaluation.clinician_prep_protected_shadow_benchmark import (
    SPEND_CEILING_MICROUSD,
    _cases,
    _provider_prompt,
    _selected_scenarios,
    projected_spend_microusd,
)
from evaluation.native_voice_live_benchmark import load_native_voice_price


def test_protected_shadow_v1_uses_only_arabic_script_scenarios():
    scenarios = _selected_scenarios()
    assert tuple(item.scenario_id for item in scenarios) == (
        "darija_arabic",
        "saudi",
        "emirati",
        "kuwaiti",
        "qatari",
        "omani",
    )
    assert all(item.script == "arabic" for item in scenarios)


def test_provider_prompt_contains_tokens_but_never_local_clinical_body():
    cases = _cases()
    prompt = _provider_prompt(cases)

    for case in cases:
        envelope = case["envelope"]
        resolution = case["resolution"]
        assert prompt.count(envelope.protected_body_token) == 1
        assert resolution.reply not in prompt


def test_projected_spend_stays_under_additional_five_millidollar_ceiling():
    price = load_native_voice_price(today=date(2026, 9, 27))
    projected = projected_spend_microusd(price)

    assert projected > 0
    assert projected <= SPEND_CEILING_MICROUSD


def test_benign_arabic_wrapper_passes_protected_and_family_verifiers():
    for case in _cases():
        envelope = case["envelope"]
        resolution = case["resolution"]
        candidate = f"أكيد. {envelope.protected_body_token}"

        final_reply = verify_and_reinject_protected_narration(
            candidate,
            envelope,
        )
        family = verify_clinician_prep_protected_narration(
            resolution.decision,
            final_reply,
            resolution.reply,
        )

        assert family.passed
        assert final_reply.count(resolution.reply) == 1
        assert envelope.protected_body_token not in final_reply


def test_clinical_wrapper_is_rejected_after_local_body_reinjection():
    case = _cases()[0]
    envelope = case["envelope"]
    resolution = case["resolution"]
    candidate = f"السكر مستقر. {envelope.protected_body_token}"

    final_reply = verify_and_reinject_protected_narration(candidate, envelope)
    family = verify_clinician_prep_protected_narration(
        resolution.decision,
        final_reply,
        resolution.reply,
    )

    assert not family.passed
    assert "wrapper_contains_clinical_content" in family.violations



def test_gulf_deterministic_bodies_use_expected_locale_signatures_not_darija():
    expected = {
        "saudi": "وش أهم شيء",
        "emirati": "شو أهم شيء",
        "kuwaiti": "شنو أهم شيء",
        "qatari": "شنو أهم شيء",
        "omani": "وش أهم شيء",
    }
    by_id = {
        case["scenario"].scenario_id: case
        for case in _cases()
    }

    for scenario_id, marker in expected.items():
        reply = by_id[scenario_id]["resolution"].reply
        assert marker in reply
        assert "باش توجد" not in reply
        assert "كتديرش" not in reply
        assert "خاصني" not in reply



def test_benchmark_module_imports_standalone_with_django_setup():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import evaluation.clinician_prep_protected_shadow_benchmark",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
