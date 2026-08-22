import re
import uuid
from datetime import date, datetime

from core.phi_privacy import (
    PatientIdentity,
    redact_current_patient_identifiers,
    redact_identity_values,
)


class PHIPseudonymizer:
    # Direct identifiers that can be recognized without patient calibration.
    _CIN_PATTERN = re.compile(r"(?<!\w)[A-Z]{1,2}[\s-]?\d{5,8}(?!\w)", re.IGNORECASE)
    _EMAIL_PATTERN = re.compile(
        r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])",
        re.IGNORECASE,
    )
    _MOROCCO_PHONE_PATTERN = re.compile(
        r"(?<!\w)(?:(?:\+|00)212[\s.()/-]*|0)[5-7](?:[\s.()/-]*\d){8}(?!\w)"
    )

    def __init__(self):
        # Volatile per-call map used only when a response must be re-personalized.
        self.session_map = {}
        self._first_name: str | None = None
        self._last_name: str | None = None
        self._date_of_birth: date | datetime | str | None = None
        self._email: str | None = None
        self._username: str | None = None

    def calibrate(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: date | datetime | str | None = None,
        email: str | None = None,
        username: str | None = None,
    ) -> None:
        """Set explicit patient identity values to remove in subsequent mask calls."""
        self._first_name = first_name
        self._last_name = last_name
        self._date_of_birth = date_of_birth
        self._email = email
        self._username = username

    def mask_patient_identity(self, first_name: str, raw_prompt: str) -> tuple[str, str]:
        """Replace a display name with a disposable per-call token."""
        session_token = f"PATIENT_{uuid.uuid4().hex[:8]}"
        self.session_map[session_token] = first_name
        if not first_name:
            return session_token, raw_prompt
        safe_prompt = re.sub(
            r"(?<!\w)" + re.escape(first_name) + r"(?!\w)",
            session_token,
            raw_prompt,
            flags=re.IGNORECASE,
        )
        return session_token, safe_prompt

    def mask(self, text: str) -> str:
        """Remove configured and current-patient direct identifiers before egress."""
        result = redact_identity_values(
            text,
            PatientIdentity(
                first_name=self._first_name,
                last_name=self._last_name,
                date_of_birth=self._date_of_birth,
                email=self._email,
                username=self._username,
            ),
        )
        result = self._CIN_PATTERN.sub("[REDACTED]", result)
        result = self._EMAIL_PATTERN.sub("[REDACTED]", result)
        result = self._MOROCCO_PHONE_PATTERN.sub("[REDACTED]", result)

        # Pulper and other patient endpoints run inside ai_egress_scope. This
        # closes the historical gap where callers forgot calibrate().
        return redact_current_patient_identifiers(result)

    def unmask_medical_report(self, ai_generated_report: str) -> str:
        """Restore only disposable display-name tokens created by this instance."""
        restored_report = ai_generated_report
        for token, real_name in self.session_map.items():
            restored_report = restored_report.replace(token, real_name)
        self.session_map.clear()
        return restored_report
