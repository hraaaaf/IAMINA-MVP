"""Bounded live-network probe for protected internal narration.

The probe uses deterministic synthetic CLINICIAN_PREP resolutions only. It exercises
the exact token-only provider path used by active staff runtime while sending no patient
identity, clinical body, facts, history, or patient message to the provider.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from django.utils import timezone

from companion.narration_envelope import (
    build_shadow_envelope,
    verify_and_reinject_protected_narration,
)
from companion.protected_provider_shadow import (
    build_protected_provider_shadow_request,
    generate_protected_provider_shadow_candidate,
)
from core.contracts.truth import TruthKind
from diabetes.services.clinical.clinician_prep_decision import (
    resolve_clinician_prep_from_brief,
)
from diabetes.services.clinical.clinician_prep_protected_narration_verifier import (
    verify_clinician_prep_protected_narration,
)
from diabetes.services.clinical.consultation_brief_contract import (
    ConsultationBriefEnvelope,
    ConsultationComparisonBasis,
    ConsultationEvidenceItem,
    ConsultationNextStep,
)

PROVIDER = "groq"
MODEL = "openai/gpt-oss-120b"
MAX_CALLS = 3
_NETWORK_AUTH_ENV = "PROTECTED_SHADOW_INTERNAL_LIVE_NETWORK_AUTHORIZED"


@dataclass(frozen=True, slots=True)
class ProbeCase:
    case_id: str
    language: str
    prefer_latin_script: bool = False


CASES = (
    ProbeCase("fr-default", "fr"),
    ProbeCase("darija-arabic", "ar-MA"),
    ProbeCase("darija-latin", "ar-MA", prefer_latin_script=True),
)


def _resolution(language: str):
    end = timezone.now()
    brief = ConsultationBriefEnvelope(
        window_start=end - timedelta(days=14),
        window_end=end,
        comparison_basis=ConsultationComparisonBasis.CURRENT_SNAPSHOT,
        items=(
            ConsultationEvidenceItem(
                key="recorded_glucose.latest_mg_dl",
                value=142.0,
                unit="mg/dL",
                truth_kind=TruthKind.OBSERVED_FACT,
                source="synthetic.protected-live-probe",
                source_version="protected-internal-live-probe.v1",
                allowed_next_step=ConsultationNextStep.MONITOR,
            ),
        ),
    )
    resolution = resolve_clinician_prep_from_brief(
        "Aide-moi à préparer les questions pour mon médecin.",
        brief,
        language=language,
    )
    if resolution is None:
        raise RuntimeError("synthetic clinician-prep resolution unavailable")
    return resolution


def run_probe(*, output_path: Path) -> dict[str, object]:
    if len(CASES) > MAX_CALLS:
        raise RuntimeError("protected internal-live probe exceeds hard call ceiling")
    if os.environ.get(_NETWORK_AUTH_ENV, "").lower() != "true":
        raise RuntimeError("protected internal-live network probe is not explicitly authorized")
    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise RuntimeError("missing GROQ_API_KEY probe credential")

    results: list[dict[str, object]] = []
    all_passed = True

    for case in CASES:
        resolution = _resolution(case.language)
        envelope = build_shadow_envelope(
            resolution,
            language=case.language,
            prefer_latin_script=case.prefer_latin_script,
        )
        request = build_protected_provider_shadow_request(envelope)
        prompt = request.user_prompt()
        if resolution.reply in prompt:
            raise RuntimeError("clinical body leaked before provider call")
        if "142" in prompt or "mg/dL" in prompt:
            raise RuntimeError("clinical value leaked before provider call")

        try:
            candidate = generate_protected_provider_shadow_candidate(
                envelope,
                internal_authorized=True,
            )
            if candidate is None:
                raise RuntimeError("internal-live provider path returned no candidate")
            reinjected = verify_and_reinject_protected_narration(candidate, envelope)
            semantic = verify_clinician_prep_protected_narration(
                resolution.decision,
                reinjected,
                resolution.reply,
            )
            passed = bool(semantic.passed)
            violations = list(semantic.violations)
            scrubbed_candidate = candidate.replace(
                envelope.protected_body_token,
                "<PROTECTED_BODY_TOKEN>",
            )
        except Exception as exc:
            passed = False
            violations = [type(exc).__name__]
            scrubbed_candidate = None

        all_passed = all_passed and passed
        results.append(
            {
                "case_id": case.case_id,
                "locale": request.locale,
                "script": request.script,
                "payload_fields": [
                    "locale",
                    "script",
                    "protected_body_token",
                ],
                "patient_data": False,
                "clinical_body_sent": False,
                "clinical_value_sent": False,
                "candidate_scrubbed": scrubbed_candidate,
                "passed": passed,
                "violations": violations,
            }
        )

    report: dict[str, object] = {
        "provider": PROVIDER,
        "model": MODEL,
        "mode": "protected_internal_live_token_only",
        "synthetic_network_probe": True,
        "patient_data": False,
        "planned_calls": len(CASES),
        "hard_call_ceiling": MAX_CALLS,
        "machine_passed": all_passed and len(results) == len(CASES),
        "results": results,
        "proof_boundaries": {
            "real_patient_boundary_proven_by_separate_local_audit": True,
            "real_patient_network_egress_performed": False,
            "patient_visible_output_changed": False,
            "groq_patient_processor_governance_approved": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(output_path=args.output)
    print(
        json.dumps(
            {
                "machine_passed": report["machine_passed"],
                "planned_calls": report["planned_calls"],
                "patient_data": report["patient_data"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["machine_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
