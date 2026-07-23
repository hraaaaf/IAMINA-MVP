import re
import uuid


class PHIPseudonymizer:
    def __init__(self):
        # Dictionnaire en mémoire volatile pour la session de l'appel API
        self.session_map = {}
        self._last_name: str | None = None
        self._date_of_birth: str | None = None

    # ── CIN regex: 1-2 uppercase letters followed by 5-6 digits (Moroccan CIN) ──
    _CIN_PATTERN = re.compile(r'\b[A-Z]{1,2}[0-9]{5,6}\b')

    def calibrate(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: str | None = None,
    ) -> None:
        """
        Set patient identity fields to strip/mask in subsequent mask() calls.
        Call this once per request before calling mask().
        """
        self._first_name = first_name
        self._last_name = last_name
        self._date_of_birth = date_of_birth

    def mask_patient_identity(self, first_name: str, raw_prompt: str) -> tuple[str, str]:
        """
        Remplace l'identité par un token UUID jetable avant l'envoi à l'API LLM.
        """
        session_token = f"PATIENT_{uuid.uuid4().hex[:8]}"
        self.session_map[session_token] = first_name

        # Le prompt partagé avec Anthropic ne contient plus d'identité réelle
        safe_prompt = raw_prompt.replace(first_name, session_token)

        return session_token, safe_prompt

    def mask(self, text: str) -> str:
        """
        Strip all configured PHI from *text* and return the sanitized version.

        Strips (in order):
          1. first_name (if calibrated) — replaced with [REDACTED]
          2. last_name (if calibrated) — replaced with [REDACTED]
          3. date_of_birth (if calibrated) — replaced with [REDACTED]
          4. Moroccan CIN patterns (e.g. AB12345) — replaced with [REDACTED]
        """
        result = text

        first_name = getattr(self, '_first_name', None)
        if first_name:
            result = result.replace(first_name, '[REDACTED]')

        if self._last_name:
            result = result.replace(self._last_name, '[REDACTED]')

        if self._date_of_birth:
            result = result.replace(self._date_of_birth, '[REDACTED]')

        # Always strip CIN patterns regardless of calibration
        result = self._CIN_PATTERN.sub('[REDACTED]', result)

        return result

    def unmask_medical_report(self, ai_generated_report: str) -> str:
        """
        Restaure le prénom du patient dans le rapport reçu pour l'affichage final.
        """
        restored_report = ai_generated_report
        for token, real_name in self.session_map.items():
            restored_report = restored_report.replace(token, real_name)

        # Purge de sécurité
        self.session_map.clear()

        return restored_report
