"""Audit protected-shadow payload construction against a real internal patient.

This command reads real patient data locally but never authorizes a processor and never
constructs or calls a network provider. Its output is content-free.
"""
from __future__ import annotations

import json
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from companion.narration_envelope import shadow_validate_protected_resolution
from companion.protected_provider_shadow import build_protected_provider_shadow_request
from core.companion.clinical import (
    get_advice_resolution,
    get_domain_context,
    verify_protected_advice_reply,
)

_BODY_TOKEN_RE = re.compile(r"^\{\{NVB_[A-F0-9]{32}\}\}$")
_DEFAULT_TRIGGER = "Aide-moi à préparer les questions pour mon médecin."


class Command(BaseCommand):
    help = (
        "Read a real active staff patient locally and prove that the protected-shadow "
        "provider payload contains only locale/script/opaque token. No provider call occurs."
    )

    def add_arguments(self, parser):
        parser.add_argument("--patient-id", type=int, required=True)
        parser.add_argument("--language", default="fr")
        parser.add_argument(
            "--trigger",
            default=_DEFAULT_TRIGGER,
            help=(
                "Local clinician-prep trigger. Avoid putting patient-identifying or "
                "clinical content on the command line."
            ),
        )

    def handle(self, *args, **options):
        patient_id = int(options["patient_id"])
        language = str(options["language"]).strip() or "fr"
        trigger = str(options["trigger"]).strip()

        User = get_user_model()
        try:
            patient = User.objects.get(pk=patient_id)
        except User.DoesNotExist as exc:
            raise CommandError("patient does not exist") from exc

        if not patient.is_active or not patient.is_staff:
            raise CommandError("real-data boundary audit is restricted to active staff accounts")
        if not trigger:
            raise CommandError("trigger must be non-empty")

        try:
            context = get_domain_context(patient.id, language=language, days=14)
            resolution = get_advice_resolution(
                patient.id,
                trigger,
                context,
                language=language,
            )
            if resolution is None:
                raise ValueError("trigger did not resolve to governed advice")
            if resolution.decision.intent != "clinician_prep":
                raise ValueError("audit is restricted to clinician_prep")

            protected = shadow_validate_protected_resolution(
                resolution,
                language=language,
            )
            if not protected.structurally_valid:
                raise ValueError("protected local reinjection mismatch")

            verified = verify_protected_advice_reply(
                patient.id,
                resolution,
                protected.reinjected_reply,
            )
            if verified != protected.reinjected_reply:
                raise ValueError("protected module verifier changed the local reply")

            request = build_protected_provider_shadow_request(protected.envelope)
            prompt = request.user_prompt()
            expected_prompt = (
                f"locale={request.locale}\n"
                f"script={request.script}\n"
                f"protected_body_token={request.protected_body_token}"
            )
            if prompt != expected_prompt:
                raise ValueError("provider payload shape drift")
            if not _BODY_TOKEN_RE.fullmatch(request.protected_body_token):
                raise ValueError("protected body token format invalid")
            if resolution.reply and resolution.reply in prompt:
                raise ValueError("deterministic clinical body leaked into provider payload")
            if trigger in prompt:
                raise ValueError("patient/user trigger leaked into provider payload")
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        payload = {
            "status": "pass",
            "mode": "real_data_local_boundary_audit",
            "patient_scope": "active_staff_only",
            "family": "clinician_prep",
            "provider": "groq",
            "provider_call_performed": False,
            "processor_policy_bypassed": False,
            "patient_data_persisted_by_command": False,
            "payload_fields": [
                "locale",
                "script",
                "protected_body_token",
            ],
            "deterministic_body_in_provider_payload": False,
            "trigger_in_provider_payload": False,
            "local_reinjection_verified": True,
            "module_verifier_passed": True,
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
