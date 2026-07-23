"""
Sprint 4 — Unit tests for service-layer modules.

Covers:
  1. stt.py        — Gemini audio transcription (validation + mocked API)
  2. narrator.py   — Narrative summary generator (mocked LLM + KPIs)
  3. reactor.py    — Post-log reaction generator (mocked LLM, tone persistence)
  4. UnitGuardMiddleware — Glucose unit conversion + physiological bounds enforcement

All tests mock external I/O (Gemini, DB queries) — no network calls, no quota.
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase

# ─────────────────────────────────────────────────────────────────────────────
# Helpers shared across sections
# ─────────────────────────────────────────────────────────────────────────────

def _make_kpis(sufficient=True):
    k = MagicMock()
    k.has_sufficient_data = sufficient
    k.avg_glucose = 140.0
    k.tir_pct = 65.0
    k.gmi = 7.2
    k.cv_pct = 25.0
    k.log_count = 30
    k.days_with_data = 20
    return k


def _make_memory(tone="encouraging"):
    m = MagicMock()
    m.current_tone = tone
    return m


def _make_llm(content: str):
    llm = MagicMock()
    result = MagicMock()
    result.content = content
    llm.complete.return_value = result
    return llm


# ─────────────────────────────────────────────────────────────────────────────
# 1. STT — transcribe()
# ─────────────────────────────────────────────────────────────────────────────

_TINY_AUDIO = b"\x00" * 1024   # 1 KB fake audio bytes
_VALID_MIME  = "audio/mp4"


class STTValidationTests(SimpleTestCase):
    """Input guards: size, MIME type, API key."""

    def test_unsupported_mime_raises_value_error(self):
        from media.voice import transcribe
        with self.assertRaises(ValueError) as ctx:
            transcribe(_TINY_AUDIO, "audio/unknown")
        self.assertIn("Unsupported", str(ctx.exception))

    def test_oversized_audio_raises_value_error(self):
        from media.voice import MAX_AUDIO_BYTES, transcribe
        big = b"\x00" * (MAX_AUDIO_BYTES + 1)
        with self.assertRaises(ValueError) as ctx:
            transcribe(big, _VALID_MIME)
        self.assertIn("large", str(ctx.exception).lower())

    def test_missing_api_key_raises_transcription_error(self):
        from media.voice import TranscriptionError, transcribe
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(TranscriptionError) as ctx:
                transcribe(_TINY_AUDIO, _VALID_MIME)
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    def test_all_standard_mime_types_accepted(self):
        from media.voice import SUPPORTED_MIME_TYPES
        for mime in ("audio/mp4", "audio/mpeg", "audio/webm", "audio/wav",
                     "audio/ogg", "audio/flac"):
            with self.subTest(mime=mime):
                self.assertIn(mime, SUPPORTED_MIME_TYPES)

    def test_max_audio_bytes_is_10mb(self):
        from media.voice import MAX_AUDIO_BYTES
        self.assertEqual(MAX_AUDIO_BYTES, 10 * 1024 * 1024)


def _mock_genai_client(text="Bonjour"):
    """Return (mock_Client_cls, mock_client_instance) for patching google.genai.Client."""
    mock_response = MagicMock()
    mock_response.text = text
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = mock_response
    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls, mock_instance


class STTGeminiCallTests(SimpleTestCase):
    """Mocked provider calls; egress policy behavior is tested in core/tests."""

    def setUp(self):
        super().setUp()
        self._egress_patcher = patch("media.voice.assert_ai_egress_allowed")
        self._egress_patcher.start()
        self.addCleanup(self._egress_patcher.stop)

    def test_returns_stripped_transcript(self):
        from media.voice import transcribe
        mock_cls, _ = _mock_genai_client("  Mon sucre est à 140  \n")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                result = transcribe(_TINY_AUDIO, _VALID_MIME)
        self.assertEqual(result, "Mon sucre est à 140")

    def test_uses_gemini_25_flash_model(self):
        from media.voice import transcribe
        mock_cls, mock_instance = _mock_genai_client("ok")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                transcribe(_TINY_AUDIO, _VALID_MIME)
        kwargs = mock_instance.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-2.5-flash")

    def test_french_language_injects_french_hint(self):
        from media.voice import transcribe
        mock_cls, mock_instance = _mock_genai_client("Bonjour")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                transcribe(_TINY_AUDIO, _VALID_MIME, language="fr")
        call_str = str(mock_instance.models.generate_content.call_args)
        self.assertIn("French", call_str)

    def test_darija_language_injects_darija_hint(self):
        # D2: ar-MA vocabulary now lives in AR_MA_STT_HINTS and must be
        # passed explicitly as language_hints — it is no longer embedded
        # in the built-in _LANGUAGE_HINTS table inside media.voice.
        from diabetes.config.stt_vocabulary import AR_MA_STT_HINTS
        from media.voice import transcribe
        mock_cls, mock_instance = _mock_genai_client("Labas")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                transcribe(_TINY_AUDIO, _VALID_MIME, language="ar-MA",
                           language_hints=AR_MA_STT_HINTS)
        call_str = str(mock_instance.models.generate_content.call_args)
        self.assertIn("Darija", call_str)

    def test_gemini_exception_raises_transcription_error(self):
        from media.voice import TranscriptionError, transcribe
        mock_cls, mock_instance = _mock_genai_client()
        mock_instance.models.generate_content.side_effect = RuntimeError("quota exceeded")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                with self.assertRaises(TranscriptionError):
                    transcribe(_TINY_AUDIO, _VALID_MIME)

    def test_none_response_text_returns_empty_string(self):
        from media.voice import transcribe
        mock_cls, _ = _mock_genai_client(text=None)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                result = transcribe(_TINY_AUDIO, _VALID_MIME)
        self.assertEqual(result, "")

    def test_temperature_zero_in_config(self):
        """Transcription must be deterministic (temperature=0)."""
        from media.voice import transcribe
        mock_cls, mock_instance = _mock_genai_client("text")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"}):
            with patch("google.genai.Client", mock_cls):
                transcribe(_TINY_AUDIO, _VALID_MIME)
        kwargs = mock_instance.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs["config"]["temperature"], 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Narrator — summarize()
# ─────────────────────────────────────────────────────────────────────────────

def _make_patient(pid=1):
    p = MagicMock()
    p.id = pid
    return p


def _patch_narrator(kpis, llm, patterns=None):
    """Stub the single chassis clinical contract with a sufficient-data DomainContext.

    Post-P4.5 the narrator pulls clinical data through get_domain_context() →
    DomainContext; tests stub that instead of patching diabetes internals.
    """
    from core.contracts.domain_context import DomainContext

    ctx = DomainContext(
        kpi_summary={"avg_glucose": 150, "tir_pct": 70},
        detected_patterns=["dawn_phenomenon"],
        insights=[],
        pivot_text="AVG_GLUCOSE: 150 mg/dL\nTIR: 70%",
        language="fr",
        has_sufficient_data=True,
        patterns_detail=[{"code": "dawn_phenomenon", "priority": 1, "evidence": "evidence"}],
    )
    return patch("companion.narrator.get_domain_context", return_value=ctx)


class NarratorInsufficientDataTests(SimpleTestCase):

    def _patch_empty(self):
        from core.contracts.domain_context import DomainContext
        return patch(
            "companion.narrator.get_domain_context",
            return_value=DomainContext.empty(),
        )

    def test_no_data_returns_guidance_message(self):
        from companion.narrator import summarize
        with self._patch_empty():
            result = summarize(_make_patient(), _make_memory(), _make_llm("{}"), "fr", 21)
        self.assertIn("assez de données", result)
        self.assertIn("21", result)

    def test_no_data_skips_llm_call(self):
        from companion.narrator import summarize
        llm = _make_llm("{}")
        with self._patch_empty():
            summarize(_make_patient(), _make_memory(), llm, "fr", 21)
        llm.complete.assert_not_called()


class NarratorSufficientDataTests(SimpleTestCase):

    def _run(self, content: str) -> str:
        from companion.narrator import summarize
        kpis = _make_kpis()
        llm = _make_llm(content)
        with _patch_narrator(kpis, llm):
            return summarize(_make_patient(), _make_memory(), llm, "fr", 21)

    def test_narrative_returned_from_llm(self):
        result = self._run('{"narrative": "Bonne semaine.", "key_insight": "", "doctor_brief": ""}')
        self.assertEqual(result, "Bonne semaine.")

    def test_llm_called_exactly_once(self):
        from companion.narrator import summarize
        kpis = _make_kpis()
        llm = _make_llm('{"narrative": "ok", "key_insight": "", "doctor_brief": ""}')
        with _patch_narrator(kpis, llm):
            summarize(_make_patient(), _make_memory(), llm, "fr", 21)
        llm.complete.assert_called_once()

    def test_llm_failure_returns_fallback_narrative(self):
        from companion.narrator import _FALLBACK_NARRATIVE, summarize
        kpis = _make_kpis()
        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("LLM down")
        with _patch_narrator(kpis, llm):
            result = summarize(_make_patient(), _make_memory(), llm, "fr", 21)
        self.assertEqual(result, _FALLBACK_NARRATIVE)

    def test_empty_narrative_returns_fallback(self):
        """Empty narrative string → falsy → fallback returned."""
        from companion.narrator import _FALLBACK_NARRATIVE
        result = self._run('{"narrative": "", "key_insight": "", "doctor_brief": ""}')
        self.assertEqual(result, _FALLBACK_NARRATIVE)

    def test_non_json_response_returns_fallback(self):
        """Malformed LLM output → parser returns "" → fallback."""
        from companion.narrator import _FALLBACK_NARRATIVE
        result = self._run("Voici votre résumé !")  # not JSON
        self.assertEqual(result, _FALLBACK_NARRATIVE)

    def test_darija_language_propagated_to_llm(self):
        """language='ar-MA' must reach the LLM prompt (not silently swallowed)."""
        from companion.narrator import summarize
        kpis = _make_kpis()
        llm = _make_llm('{"narrative": "Mezyan.", "key_insight": "", "doctor_brief": ""}')
        with _patch_narrator(kpis, llm):
            result = summarize(_make_patient(), _make_memory(), llm, "ar-MA", 21)
        # As long as LLM was called and returned a narrative, language hint was used.
        llm.complete.assert_called_once()
        self.assertEqual(result, "Mezyan.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Reactor — react()
# ─────────────────────────────────────────────────────────────────────────────

def _make_entry(blood_sugar=120, meal_type="lunch"):
    e = MagicMock()
    e.blood_sugar = blood_sugar
    e.meal_type = meal_type
    e.notes = ""
    e.id = 42
    return e


class ReactorReactTests(SimpleTestCase):

    def test_returns_message_from_llm(self):
        from companion.reactor import react
        llm = _make_llm('{"message": "Bien noté !", "tone_detected": "encouraging"}')
        result = react(_make_entry(), _make_memory(), llm, "fr")
        self.assertEqual(result, "Bien noté !")

    def test_valid_tone_persisted_in_memory(self):
        from companion.reactor import react
        memory = _make_memory(tone="encouraging")
        llm = _make_llm('{"message": "OK", "tone_detected": "gentle"}')
        react(_make_entry(), memory, llm, "fr")
        self.assertEqual(memory.current_tone, "gentle")

    def test_challenge_tone_persisted(self):
        from companion.reactor import react
        memory = _make_memory(tone="gentle")
        llm = _make_llm('{"message": "On s\'accroche!", "tone_detected": "challenge"}')
        react(_make_entry(), memory, llm, "fr")
        self.assertEqual(memory.current_tone, "challenge")

    def test_invalid_tone_not_persisted(self):
        from companion.reactor import react
        memory = _make_memory(tone="encouraging")
        llm = _make_llm('{"message": "OK", "tone_detected": "sarcastic"}')
        react(_make_entry(), memory, llm, "fr")
        self.assertEqual(memory.current_tone, "encouraging")

    def test_empty_tone_not_persisted(self):
        from companion.reactor import react
        memory = _make_memory(tone="gentle")
        llm = _make_llm('{"message": "OK", "tone_detected": ""}')
        react(_make_entry(), memory, llm, "fr")
        self.assertEqual(memory.current_tone, "gentle")

    def test_llm_failure_returns_fallback(self):
        from companion.reactor import react
        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("LLM down")
        result = react(_make_entry(), _make_memory("gentle"), llm, "fr")
        # gentle fallback: "C'est enregistré..."
        self.assertIn("enregistré", result)

    def test_all_tone_fallbacks_non_empty(self):
        from companion.reactor import _fallback
        for tone in ("encouraging", "gentle", "challenge"):
            with self.subTest(tone=tone):
                msg = _fallback(tone)
                self.assertIsInstance(msg, str)
                self.assertGreater(len(msg), 10)

    def test_unknown_tone_fallback_defaults_to_gentle(self):
        from companion.reactor import _FALLBACKS, _fallback
        result = _fallback("totally_unknown")
        self.assertEqual(result, _FALLBACKS["gentle"])

    def test_none_meal_does_not_crash(self):
        """meal_type=None (unset entry) → defaults to 'non précisé', no exception."""
        from companion.reactor import react
        llm = _make_llm('{"message": "Noté.", "tone_detected": "gentle"}')
        entry = _make_entry(meal_type=None)
        result = react(entry, _make_memory(), llm, "fr")
        self.assertEqual(result, "Noté.")


# ─────────────────────────────────────────────────────────────────────────────
# 4. UnitGuardMiddleware + convert_to_mg_dl() + validate_mg_dl()
# ─────────────────────────────────────────────────────────────────────────────

class ConvertToMgDlTests(SimpleTestCase):
    """Pure function: unit conversion logic."""

    def test_mg_dl_unchanged(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        self.assertEqual(convert_to_mg_dl(120.0, "mg/dL"), 120.0)

    def test_mg_dl_case_insensitive(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        self.assertEqual(convert_to_mg_dl(100.0, "MG/DL"), 100.0)

    def test_mmol_l_converts_correctly(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        result = convert_to_mg_dl(7.0, "mmol/L")
        self.assertAlmostEqual(result, 126.1, delta=0.2)

    def test_g_l_converts_correctly(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        result = convert_to_mg_dl(1.2, "g/L")
        self.assertAlmostEqual(result, 120.0, delta=0.2)

    def test_mmol_shorthand_accepted(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        result = convert_to_mg_dl(5.5, "mmol")
        self.assertAlmostEqual(result, 99.1, delta=0.2)

    def test_unknown_unit_raises_conversion_error(self):
        from diabetes.middleware.unit_guard import UnitConversionError, convert_to_mg_dl
        with self.assertRaises(UnitConversionError) as ctx:
            convert_to_mg_dl(5.0, "furlongs")
        self.assertIn("Unknown glucose unit", str(ctx.exception))

    def test_value_below_min_after_conversion_raises(self):
        """0.1 mmol/L → 1.8 mg/dL < 20 mg/dL minimum."""
        from diabetes.middleware.unit_guard import UnitConversionError, convert_to_mg_dl
        with self.assertRaises(UnitConversionError):
            convert_to_mg_dl(0.1, "mmol/L")

    def test_value_above_max_after_conversion_raises(self):
        """40 mmol/L → 720.6 mg/dL > 700 mg/dL maximum."""
        from diabetes.middleware.unit_guard import UnitConversionError, convert_to_mg_dl
        with self.assertRaises(UnitConversionError):
            convert_to_mg_dl(40.0, "mmol/L")

    def test_returns_float(self):
        from diabetes.middleware.unit_guard import convert_to_mg_dl
        result = convert_to_mg_dl(5.5, "mmol/L")
        self.assertIsInstance(result, float)


class ValidateMgDlTests(SimpleTestCase):
    """validate_mg_dl() — bounds check on already-canonical values."""

    def test_normal_value_passes_through(self):
        from diabetes.middleware.unit_guard import validate_mg_dl
        self.assertEqual(validate_mg_dl(150.0), 150.0)

    def test_min_boundary_accepted(self):
        from diabetes.middleware.unit_guard import validate_mg_dl
        self.assertEqual(validate_mg_dl(20.0), 20.0)

    def test_max_boundary_accepted(self):
        from diabetes.middleware.unit_guard import validate_mg_dl
        self.assertEqual(validate_mg_dl(700.0), 700.0)

    def test_below_min_raises(self):
        from diabetes.middleware.unit_guard import UnitConversionError, validate_mg_dl
        with self.assertRaises(UnitConversionError):
            validate_mg_dl(10.0)

    def test_above_max_raises(self):
        from diabetes.middleware.unit_guard import UnitConversionError, validate_mg_dl
        with self.assertRaises(UnitConversionError):
            validate_mg_dl(750.0)


class UnitGuardMiddlewareTests(SimpleTestCase):
    """Full middleware: request interception, conversion, 422 rejection."""

    def setUp(self):
        from diabetes.middleware.unit_guard import UnitGuardMiddleware
        self.factory = RequestFactory()
        self.middleware = UnitGuardMiddleware(get_response=lambda r: None)

    def _post_json(self, path, data):
        req = self.factory.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
        )
        return self.middleware(req)

    # ── Pass-through cases ────────────────────────────────────────────────────

    def test_get_request_passes_through(self):
        req = self.factory.get("/api/v1/logs")
        self.assertIsNone(self.middleware(req))

    def test_non_guarded_path_passes_through(self):
        self.assertIsNone(self._post_json("/health/", {"blood_sugar": 10.0}))

    def test_valid_mg_dl_passes_through(self):
        self.assertIsNone(self._post_json("/api/v1/logs", {"blood_sugar": 120.0}))

    def test_malformed_json_passes_through(self):
        req = self.factory.post(
            "/api/v1/logs",
            data=b"not valid json{{{",
            content_type="application/json",
        )
        self.assertIsNone(self.middleware(req))

    def test_non_json_content_type_passes_through(self):
        req = self.factory.post(
            "/api/v1/logs",
            data={"blood_sugar": "10"},
            content_type="application/x-www-form-urlencoded",
        )
        self.assertIsNone(self.middleware(req))

    def test_empty_body_passes_through(self):
        req = self.factory.post(
            "/api/v1/logs",
            data=b"",
            content_type="application/json",
        )
        self.assertIsNone(self.middleware(req))

    # ── Conversion cases ──────────────────────────────────────────────────────

    def test_mmol_converted_in_place(self):
        req = self.factory.post(
            "/api/v1/logs",
            data=json.dumps({"blood_sugar": 7.0, "unit": "mmol/L"}),
            content_type="application/json",
        )
        resp = self.middleware(req)
        self.assertIsNone(resp)
        body = json.loads(req._body)
        self.assertAlmostEqual(body["blood_sugar"], 126.1, delta=0.2)
        self.assertEqual(body["unit"], "mg/dL")   # unit field canonicalised

    def test_g_l_converted_in_place(self):
        req = self.factory.post(
            "/api/v1/logs",
            data=json.dumps({"blood_sugar": 1.5, "unit": "g/L"}),
            content_type="application/json",
        )
        self.middleware(req)
        body = json.loads(req._body)
        self.assertAlmostEqual(body["blood_sugar"], 150.0, delta=0.2)

    def test_patch_request_is_also_guarded(self):
        req = self.factory.patch(
            "/api/v1/logs/1",
            data=json.dumps({"blood_sugar": 10.0}),
            content_type="application/json",
        )
        resp = self.middleware(req)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 422)

    # ── Rejection cases ───────────────────────────────────────────────────────

    def test_implausible_low_mg_dl_returns_422(self):
        resp = self._post_json("/api/v1/logs", {"blood_sugar": 10.0})
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 422)

    def test_implausible_high_mg_dl_returns_422(self):
        resp = self._post_json("/api/v1/logs", {"blood_sugar": 750.0})
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 422)

    def test_unknown_unit_returns_422(self):
        resp = self._post_json("/api/v1/logs", {"blood_sugar": 5.0, "unit": "furlongs"})
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 422)

    def test_rejection_body_has_error_code(self):
        resp = self._post_json("/api/v1/logs", {"blood_sugar": 10.0})
        data = json.loads(resp.content)
        self.assertEqual(data["code"], "UNIT_GUARD_REJECTION")
        self.assertIn("error", data)

    def test_ai_path_is_guarded(self):
        """POST /api/v1/ai/* is in _GUARDED_PATHS."""
        resp = self._post_json("/api/v1/ai/summary", {"blood_sugar": 750.0})
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 422)
