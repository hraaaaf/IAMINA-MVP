# Locale/state inventory

Generated from repository source.

## `backend/ai/api/v1/ai.py`
- L17: `4. LLM (Gemini 2.5 Flash) interprets the pivot text, responds in patient language.`
- L30: `from django.utils import timezone`
- L117: `reply_language: str = "fr"`
- L139: `unit: str                # "mg/dL" | "mmol/L"`
- L160: `patient_language = _get_patient_language(user)`
- L171: `since = timezone.now() - timedelta(days=data.days)`
- L183: `compressed = compress(kpis, report.patterns, patient_language)`
- L211: `"generated_at": timezone.now().isoformat(),`
- L236: `language = _get_patient_language(user)`
- L244: `from companion.prompts import SUMMARY_USER, SYSTEM_BASE, get_language_label`
- L262: `"generated_at": timezone.now().isoformat(),`
- L266: `since = timezone.now() - timedelta(days=days)`
- L288: `f"AVG_GLUCOSE: {kpis.avg_glucose} mg/dL" if kpis.avg_glucose else "",`
- L300: `system = SYSTEM_BASE.format(language=get_language_label(language), tone=tone_ctx.mode.value)`
- L319: `narrative = apply_no_prescription_policy(narrative, language)`
- L320: `key_insight = apply_no_prescription_policy(key_insight, language)`
- L321: `doctor_brief = apply_no_prescription_policy(doctor_brief, language)`
- L328: `"generated_at": timezone.now().isoformat(),`
- L350: `4. Call LLM → respond in patient language.`
- L353: `language = _get_patient_language(user)`
- L355: `from companion.conversation import detect_language`
- L358: `iamina = IAmina(user, language)`
- L363: `reply_language = detect_language(data.message, language)`
- L369: `"timestamp": timezone.now().isoformat(),`
- L371: `"reply_language": reply_language,`
- L397: `return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}`
- L450: `language = _get_patient_language(user)`
- L468: `refusal = no_prescription_message(language)`
- L475: `since = timezone.now() - timedelta(days=context_days)`
- L506: `iamina = IAmina(user, language)`
- L554: `def _build_iamina_system_prompt(user, kpis, report, language: str) -> str:`
- L557: `from companion.prompts import SYSTEM_BASE, get_language_label`
- L572: `system = SYSTEM_BASE.format(language=get_language_label(language), tone=tone_ctx.mode.value)`
- L591: `def _get_patient_language(user) -> str:`
- L594: `return base.preferred_language or "ar-MA"`

## `backend/ai/api/v1/voice.py`
- L30: `from django.utils import timezone`
- L57: `reply_language: str = "fr"`
- L134: `# ③ Get patient language (drives Darija / Fusha STT hint)`
- L135: `language = _get_language(user)`
- L139: `transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)`
- L159: `"timestamp": timezone.now().isoformat(),`
- L163: `from companion.conversation import detect_language`
- L166: `iamina = IAmina(user, language)`
- L168: `reply_language = detect_language(transcript, language)`
- L172: `user.id, language, len(transcript), len(reply),`
- L179: `"timestamp":        timezone.now().isoformat(),`
- L181: `"reply_language":   reply_language,`
- L213: `language = _get_language(request.user)`
- L216: `transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)`
- L226: `def _get_language(user) -> str:`
- L228: `return BasePatientProfile.objects.get(patient=user).preferred_language or "ar-MA"`
- L239: `"timestamp":       timezone.now().isoformat(),`

## `backend/amina/settings.py`
- L65: `# UnitGuard: normalises glucose units (mg/dL ↔ g/L ↔ mmol/L) on all API writes.`
- L123: `LANGUAGE_CODE = 'fr-fr'`
- L124: `TIME_ZONE = 'Europe/Paris'`

## `backend/clinical/pivot.py`
- L6: `Translates clinical metrics and patterns into an English Pivot Language.`
- L8: `IAmina uses English as a pivot language for its internal clinical reasoning`
- L10: `user's target language (FR/AR/Darija).`
- L16: `pivot_lines.append(f"AVG_GLUCOSE: {clinical_data['avg_glucose']:.1f} mg/dL")`
- L22: `pivot_lines.append(f"GLYCEMIC_VARIABILITY_SD: {clinical_data['std_dev']:.1f} mg/dL")`

## `backend/companion/advice_filter.py`
- L12: `Pattern set aligned with prompts.py LANGUAGE_LABELS vocabulary so the`
- L18: `# Sources: prompts.py LANGUAGE_LABELS + few-shot examples in CHAT_USER / REACTION_USER.`

## `backend/companion/alerts.py`
- L24: `def check_alert(entry, language: str = "fr") -> Optional[str]:`
- L40: `return alert.message_darija if language == "ar-MA" else alert.message_fr`

## `backend/companion/conversation.py`
- L6: `from companion.prompts import CHAT_USER, SYSTEM_WITH_STATE, get_language_label`
- L49: `def _get_context(patient, context_days: int, language: str = "fr") -> DomainContext:`
- L52: `return DomainContext.empty(language=language)`
- L53: `return get_domain_context(patient.id, language=language, days=context_days)`
- L57: `# Latin-script Darija keywords — detect code-switched or transliterated Moroccan Arabic`
- L111: `def detect_language(message: str, default: str) -> str:`
- L112: `"""Auto-detect Darija from message content (Arabic script OR Latin transliteration).`
- L172: `def _fallback_reply(ctx: DomainContext, language: str) -> str:`
- L173: `"""Substantive offline reply using cached KPIs — respects patient language.`
- L179: `is_ar = language in ("ar", "ar-MA")`
- L180: `is_darija = language == "ar-MA"`
- L240: `def _inject_proactive_followup(memory, language: str, patient, signal: str) -> None:`
- L242: `lang = language if language in ("ar-MA", "ar") else "fr"`
- L249: `def chat(message: str, memory, deep, llm=None, language: str = "fr", patient=None, context_days: int = 14) -> str:`
- L254: `reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR`
- L260: `reply = no_prescription_message(language)`
- L267: `# 1. Language auto-detection (handles Darija override)`
- L268: `language = detect_language(message, language)`
- L288: `_inject_proactive_followup(memory, language, patient, recent_signal)`
- L291: `ctx = _get_context(patient, context_days, language)`
- L314: `think_before_reply(safe_message, memory, deep, state, ctx, llm, language)`
- L319: `language=get_language_label(language),`
- L381: `reply = _fallback_reply(ctx, language)`
- L386: `reply = apply_no_prescription_policy(reply, language)`
- L410: `def stream_chat(message: str, memory, deep, llm=None, language: str = "fr", patient=None, context_days: int = 14):`
- L420: `reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR`
- L427: `reply = no_prescription_message(language)`
- L436: `language = detect_language(message, language)`
- L448: `ctx = _get_context(patient, context_days, language)`
- L465: `think_before_reply(safe_message, memory, deep, state, ctx, llm, language)`
- L470: `language=get_language_label(language),`
- L523: `full_reply = _fallback_reply(ctx, language)`
- L526: `full_reply = apply_no_prescription_policy(full_reply, language)`
- L544: `fallback = _fallback_reply(ctx, language)`
- L553: `full_reply = apply_no_prescription_policy(full_reply, language)`

## `backend/companion/core.py`
- L19: `def __init__(self, patient, language: str = "ar-MA"):`
- L21: `self.language = language`
- L29: `alert = _evaluate_alert(entry, self.patient.id, self.language)`
- L58: `entry, self.memory, language=self.language,`
- L68: `return summarize(self.patient, self.memory, language=self.language, days=days)`
- L79: `language=self.language, patient=self.patient, context_days=context_days,`
- L94: `language=self.language, patient=self.patient, context_days=context_days,`
- L103: `Uses a conservative heuristic: post-meal spike above 180 mg/dL is recorded`

## `backend/companion/deep_memory.py`
- L74: `from datetime import datetime, timezone`
- L76: `"timestamp": datetime.now(timezone.utc).isoformat(),`
- L143: `from datetime import datetime, timezone`
- L144: `self.last_advice_given_at = datetime.now(timezone.utc).isoformat()`
- L149: `from datetime import datetime, timedelta, timezone`
- L152: `return (datetime.now(timezone.utc) - last) < timedelta(hours=hours)`

## `backend/companion/memory.py`
- L83: `Keyword-based distress detection (FR + Darija transliteration + English).`
- L106: `# Darija (Latin transliteration — synced with _EMOTIONAL_RE)`

## `backend/companion/narrator.py`
- L4: `from companion.prompts import SUMMARY_USER, SYSTEM_BASE, get_language_label`
- L17: `def summarize(patient, memory, llm=None, language: str = "fr", days: int = 7) -> str:`
- L26: `ctx = get_domain_context(patient.id, language=language, days=days)`
- L43: `system = SYSTEM_BASE.format(language=get_language_label(language), tone=memory.current_tone)`
- L62: `return apply_no_prescription_policy(parsed["narrative"] or _FALLBACK_NARRATIVE, language)`

## `backend/companion/prompts.py`
- L15: `# Language labels — maps language codes → explicit LLM instructions`
- L18: `LANGUAGE_LABELS: dict[str, str] = {`
- L51: `def get_language_label(code: str) -> str:`
- L52: `"""Return the explicit language instruction for the LLM.`
- L53: `Falls back to the raw code if not in LANGUAGE_LABELS."""`
- L54: `return LANGUAGE_LABELS.get(code, code)`
- L62: `Langue de réponse: {language}`
- L88: `Langue de réponse: {language_instruction}`
- L99: `language_instruction="français (tutoiement, ton chaleureux)"`
- L102: `_FORMAT_LANGUAGE_INSTRUCTIONS: dict[str, str] = {`
- L113: `def get_format_system(language: str = "fr") -> str:`
- L114: `"""Return FORMAT_SYSTEM with language instruction injected for the patient's language."""`
- L115: `instruction = _FORMAT_LANGUAGE_INSTRUCTIONS.get(`
- L116: `language, _FORMAT_LANGUAGE_INSTRUCTIONS["fr"]`
- L118: `return _FORMAT_SYSTEM_BASE.format(language_instruction=instruction)`
- L173: `[TIR=72%, hypos nocturnes] → {{"narrative": "Cette semaine, tu as bien géré ta glycémie dans l'ensemble. Deux épisodes nocturnes méritent attention.", "key_insight": "Tes nuits semblent un peu agitées — une petite collation le soir pourrait`
- L220: `language: str,`
- L231: `return body.format(language=get_language_label(language), tone=tone)`

## `backend/companion/reactor.py`
- L5: `from companion.prompts import REACTION_USER, SYSTEM_BASE, get_language_label`
- L19: `def react(entry, memory, llm=None, language: str = "fr", deep=None, patient=None) -> str:`
- L36: `system = SYSTEM_BASE.format(language=get_language_label(language), tone=memory.current_tone or "encouraging")`
- L60: `reply = apply_no_prescription_policy(reply, language)`

## `backend/companion/router.py`
- L50: `r'(?:glyc[eé]mie|glycemie|glucose|sucre|taux|g/l|mg/dl|dextro)\s*'`

## `backend/companion/thinker.py`
- L21: `language: str = "fr",`
- L33: `from companion.prompts import get_language_label`
- L46: `system = f"Tu es IAmina. Tu réfléchis avant de répondre. Langue: {get_language_label(language)}"`

## `backend/core/ai_egress.py`
- L22: `from django.utils import timezone`
- L177: `now = timezone.now()`
- L197: `).update(revoked_at=timezone.now())`

## `backend/core/api/v1/account.py`
- L13: `from django.utils import timezone`
- L61: `base.ai_consent_given_at = timezone.now()`

## `backend/core/companion/clinical.py`
- L24: `def _key(patient_id: int, days: int, language: str) -> str:`
- L25: `return f"companion:ctx:{patient_id}:{days}:{language}"`
- L56: `def get_domain_context(patient_id: int, language: str = "fr", days: int = 14) -> DomainContext:`
- L58: `raw = cache.get(_key(patient_id, days, language))`
- L67: `return DomainContext.empty(language=language)`
- L69: `ctx = engine.analyze(patient_id, language=language, days=days)`
- L71: `cache.set(_key(patient_id, days, language), json.dumps(asdict(ctx)), timeout=CONTEXT_TTL)`
- L78: `"""Drop cached context after a new entry (all windows + languages)."""`
- L84: `def evaluate_alert(entry, patient_id: int, language: str = "fr"):`
- L89: `return engine.evaluate_alert(entry, language=language)`

## `backend/core/contracts/alert.py`
- L18: `message: str                    # localized message for the requested language`

## `backend/core/contracts/companion_identity.py`
- L19: `unit: str                 # "mg/dL", "mmHg", …`

## `backend/core/contracts/domain_context.py`
- L11: `Data flow: module.analyze(patient_id, language) -> DomainContext -> narrate()`
- L36: `language: str`
- L37: `# BCP-47 target language for the narrative response.`
- L65: `def empty(cls, language: str = "fr") -> "DomainContext":`
- L72: `language=language,`

## `backend/core/contracts/manifest.py`
- L35: `supported_languages: list[str]`
- L36: `# BCP-47 language codes this module supports.`

## `backend/core/contracts/patient_context.py`
- L20: `language: str`
- L21: `# BCP-47 language code for the current session.`
- L25: `# ISO 3166-1 alpha-2 country code.`

## `backend/core/engine/base.py`
- L13: `def analyze(self, patient_id, language="fr", days=14):`
- L41: `language: str = "fr",`
- L53: `language:   Patient preferred_language code ('fr', 'ar-MA', 'ar').`
- L63: `language: str = "fr",`

## `backend/core/input_safety.py`
- L23: `language: str | None = None,`
- L26: `del language`

## `backend/core/llm_gateway.py`
- L88: `language: str,`
- L100: `language: BCP-47 language code for the response (e.g. "fr", "ar-MA").`
- L103: `str — narrative text in the requested language.`
- L113: `system = _build_system_prompt(companion_identity, language)`
- L126: `def _build_system_prompt(identity: CompanionIdentity, language: str) -> str:`
- L127: `"""Build the system prompt from companion identity and target language."""`
- L129: `return build_system_prompt(identity, language, tone="encouraging")`

## `backend/core/medical_safety.py`
- L40: `def no_prescription_message(language: str = "fr") -> str:`
- L41: `if language == "ar-MA":`
- L64: `def apply_no_prescription_policy(text: str, language: str = "fr") -> str:`
- L68: `return no_prescription_message(language)`

## `backend/core/middleware/triage_vital.py`
- L15: `Coverage: French, Darija transliterations, and common medical terms.`
- L27: `from django.utils import timezone`
- L51: `# Darija transliterations (common phonetic spellings — Latin script).`
- L65: `# Patients who type in actual Arabic Unicode (not Latin transliteration) must be covered.`
- L81: `# Numeric thresholds detected in natural language (regex patterns)`
- L133: `# Simple Darija indicator tokens — enough to recognise the language.`
- L134: `# Covers both Latin transliteration and Arabic Unicode script.`
- L135: `# Low-threshold: if any one token matches, reply in Darija (patient's native language).`
- L146: `# 3. LANGUAGE SELECTION`
- L156: `language when there is any signal for it.`
- L230: `"timestamp": timezone.now().isoformat(),`
- L238: `"timestamp": timezone.now().isoformat(),`
- L248: `"timestamp": timezone.now().isoformat(),`
- L294: `Pick reply language: profile preference first, else simple heuristic`
- L300: `pref = (getattr(base, "preferred_language", "") or "").lower()`

## `backend/core/migrations/0004_basepatientprofile.py`
- L22: `('preferred_language', models.CharField(`
- L23: `choices=[('fr', 'Français'), ('ar-MA', 'Darija (dialecte marocain)'), ('ar', 'Arabe classique (Fusha)')],`
- L25: `help_text='UI language preference.',`

## `backend/core/migrations/0006_copy_basepatientprofile_data.py`
- L45: `"preferred_language": pp.preferred_language,`
- L68: `pp.preferred_language = bp.preferred_language`
- L76: `"firebase_uid", "preferred_language", "ai_consent_given_at",`

## `backend/core/models/patient.py`
- L18: `auth bridge (firebase_uid), language, RGPD consent, monetisation,`
- L29: `LANGUAGE_CHOICES = [`
- L31: `('ar-MA', 'Darija (dialecte marocain)'),`
- L55: `preferred_language = models.CharField(`
- L57: `choices=LANGUAGE_CHOICES,`
- L59: `help_text="UI language preference.",`

## `backend/core/observability/logging.py`
- L33: `def emergency(condition: str, patient_id: int, kind: str, language: str) -> None:`
- L40: `"language":   language,`

## `backend/core/tests/test_ai_egress.py`
- L9: `from django.utils import timezone`
- L39: `profile.ai_consent_given_at = timezone.now()`

## `backend/core/tests/test_ai_processor_policy.py`
- L3: `from django.utils import timezone`
- L33: `ai_consent_given_at=timezone.now(),`

## `backend/core/tests/test_ai_provider_failures.py`
- L6: `from django.utils import timezone`
- L56: `"ai_consent_given_at": timezone.now(),`

## `backend/core/tests/test_ai_text_payload.py`
- L8: `from django.utils import timezone`
- L27: `ai_consent_given_at=timezone.now(),`
- L138: `"Glycémie 126 mg/dL, HbA1c 7.2 %, poids 82 kg, "`

## `backend/core/tests/test_base_engine.py`
- L63: `result = DiabetesEngine().analyze(patient_id=1, language="fr", days=14)`
- L67: `self.assertEqual(result.language, "fr")`
- L71: `entry = type("E", (), {"blood_sugar": 45.0})()  # < 54 mg/dL`
- L72: `alert = DiabetesEngine().evaluate_alert(entry, language="fr")`
- L80: `self.assertIsNone(DiabetesEngine().evaluate_alert(entry, language="fr"))`

## `backend/core/tests/test_input_safety.py`
- L43: `monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")`
- L60: `monkeypatch.setattr(ai, "_get_patient_language", lambda user: "fr")`

## `backend/core/tests/test_llm_gateway.py`
- L12: `from django.utils import timezone`
- L28: `ai_consent_given_at=timezone.now(),`
- L32: `language="fr",`
- L45: `language="fr",`
- L54: `unit="mg/dL",`

## `backend/core/tests/test_media_consent_api.py`
- L7: `from django.utils import timezone`
- L31: `profile.ai_consent_given_at = timezone.now()`
- L60: `BasePatientProfile.objects.create(patient=other, ai_consent_given_at=timezone.now())`

## `backend/core/tests/test_observability.py`
- L48: `with self.assertLogs("core.observability.events", level="WARNING") as log_ctx:`
- L92: `with self.assertLogs("amina.clinical", level="INFO") as log_ctx:`
- L100: `with self.assertLogs("amina.clinical", level="INFO") as log_ctx:`
- L106: `with self.assertLogs("amina.clinical", level="INFO") as log_ctx:`
- L112: `with self.assertLogs("amina.clinical", level="INFO") as log_ctx:`

## `backend/core/tests/test_p0_api_safety_boundaries.py`
- L72: `data=json.dumps({"blood_sugar": 5.5, "unit": "mmol/L"}),`
- L82: `self.assertEqual(normalized["unit"], "mg/dL")`
- L87: `data=json.dumps({"blood_sugar": "not-a-number", "unit": "mg/dL"}),`

## `backend/core/tests/test_p0_auth_profile_integrity.py`
- L75: `"preferred_language",`

## `backend/core/tests/test_p2_patient_split.py`
- L37: `self.assertEqual(self.base.preferred_language, "ar-MA")`
- L104: `self.assertEqual(self.profile.preferred_language, "ar-MA")`
- L119: `preferred_language="fr",`
- L128: `self.assertEqual(fetched_base.preferred_language, "fr")`

## `backend/core/tests/test_p4_narrative_engine.py`
- L7: `T3: build_system_prompt() uses get_language_label() for language mapping`
- L27: `unit="mg/dL",`
- L63: `def test_build_system_prompt_uses_language_label(diabetes_identity):`
- L64: `from companion.prompts import build_system_prompt, get_language_label`
- L67: `expected_label = get_language_label("ar-MA")`
- L72: `from companion.prompts import build_system_prompt, get_language_label`
- L75: `assert get_language_label("fr") in result`
- L95: `language="fr",`
- L104: `language="fr",`
- L106: `identity = CompanionIdentity("IAmina Test", "test companion", "mg/dL")`
- L164: `iamina = IAmina(mock_patient, language="fr")`

## `backend/core/tests/test_retention_sql.py`
- L12: `from datetime import timezone as tz`
- L15: `from django.utils import timezone`
- L31: `timezone.now() - timedelta(days=days_ago)`
- L93: `now = timezone.now()`
- L118: `now = timezone.now()`
- L145: `now = timezone.now()`
- L173: `now = timezone.now()`

## `backend/core/triage_classification.py`
- L95: `# High-precision numeric distress: 10-49 mg/dL or 300-599 mg/dL near a`

## `backend/diabetes/admin.py`
- L10: `from django.utils import timezone`
- L81: `week_ago = timezone.now() - timedelta(days=7)`
- L142: `'language',`
- L147: `list_filter = ['language', 'created_at']`

## `backend/diabetes/api/v1/demo.py`
- L11: `from django.utils import timezone`
- L39: `{"id": "D", "name": "Gestational — Fasting Hyperglycemia","description": "Pregnant patient with fasting glucose >105 mg/dL"},`
- L76: `now = timezone.now()`

## `backend/diabetes/api/v1/imports.py`
- L26: `from django.utils import timezone as tz`
- L124: `ts = tz.make_aware(ts, tz.get_current_timezone())`

## `backend/diabetes/api/v1/kpis.py`
- L101: `target_low  — lower TIR bound in mg/dL (default 70)`
- L102: `target_high — upper TIR bound in mg/dL (default 180)`

## `backend/diabetes/api/v1/profile.py`
- L25: `_VALID_LANGUAGES = {"fr", "ar-MA", "ar"}`
- L31: `"preferred_language",`
- L54: `preferred_language: Optional[str] = None`
- L65: `@field_validator("preferred_language")`
- L67: `def validate_language(cls, v):`
- L68: `if v is not None and v not in _VALID_LANGUAGES:`
- L69: `raise ValueError(f"preferred_language must be one of {_VALID_LANGUAGES}")`
- L104: `raise ValueError("target_range_low must be between 40 and 200 mg/dL")`
- L111: `raise ValueError("target_range_high must be between 100 and 400 mg/dL")`
- L184: `"preferred_language",`
- L213: `"preferred_language",`

## `backend/diabetes/api/v1/schemas.py`
- L9: `# Physiological range accepted at the API boundary (30–600 mg/dL).`
- L21: `preferred_language: str = "ar-MA"`

## `backend/diabetes/config/stt_vocabulary.py`
- L4: `Extracted from engine.services.llm.stt._LANGUAGE_HINTS["ar-MA"].`
- L5: `Pass to media.voice.transcribe() as language_hints=AR_MA_STT_HINTS so the`
- L10: `transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)`
- L18: `"Moroccan Darija — a spoken Arabic dialect that freely mixes Moroccan Arabic, French, and "`
- L81: `"Units used: mg/dL (e.g. 120, 250) OR mmol/L (e.g. 5.5, 8.3)\n"`
- L89: `"  e.g. 'khmsa w nus' = 5.5 mmol/L\n"`
- L90: `"  e.g. 'miya w 3ashrine' = 120 mg/dL\n"`
- L91: `"  e.g. 'miyatayn w khmsa w 3ashrine' = 225 mg/dL\n\n"`

## `backend/diabetes/domain_config.py`
- L16: `# ── Routing urgency thresholds (mg/dL) ───────────────────────────────────`
- L21: `# ── Vital emergency thresholds (mg/dL) ───────────────────────────────────`
- L27: `# ── Time In Range bounds (mg/dL) ─────────────────────────────────────────`
- L36: `# ── Clinical detector thresholds (mg/dL unless noted) ───────────────────`
- L64: `unit: str = "mg/dL"`

## `backend/diabetes/management/commands/emit_inactive_events.py`
- L20: `from django.utils import timezone`
- L32: `today = timezone.localdate()  # uses settings.TIME_ZONE, consistent with __date lookup`
- L33: `cutoff = timezone.now() - timedelta(days=7)`

## `backend/diabetes/management/commands/setup_demo.py`
- L14: `from django.utils import timezone`
- L152: `now = timezone.now()`

## `backend/diabetes/manifest.py`
- L14: `supported_languages=["fr", "ar-MA", "ar"],`

## `backend/diabetes/middleware/unit_guard.py`
- L7: `1. Detect the declared unit (mg/dL | g/L | mmol/L).`
- L8: `2. Convert to the canonical internal unit (mg/dL).`
- L12: `Unit confusion (mg/dL vs g/L) is a documented source of dangerous dosing errors.`
- L33: `# Physiologically plausible blood glucose range in mg/dL`
- L38: `# Conversion factors TO mg/dL`
- L40: `"mg/dl": 1.0,`
- L42: `"g/l": 100.0,  # 1 g/L = 100 mg/dL`
- L44: `"mmol/l": 18.016,  # 1 mmol/L = 18.016 mg/dL`
- L57: `_UNIT_FIELDS = ("unit", "glucose_unit", "blood_sugar_unit")`
- L70: `Convert a glucose value to mg/dL.`
- L77: `Value in mg/dL, rounded to 1 decimal.`
- L87: `f"Unknown glucose unit: '{unit}'. Accepted: mg/dL, g/L, mmol/L."`
- L94: `f"Glucose value {converted} mg/dL (converted from {value} {unit}) is outside "`
- L95: `f"physiologically plausible range [{_MIN_GLUCOSE_MG_DL}–{_MAX_GLUCOSE_MG_DL}] mg/dL. "`
- L99: `if unit.lower() not in ("mg/dl", "mgdl"):`
- L101: `"UnitGuard: Converted %.1f %s → %.1f mg/dL",`
- L112: `Validate a value already in mg/dL for physiological plausibility.`
- L119: `f"Glucose value {value} mg/dL is outside physiologically safe range "`
- L120: `f"[{_MIN_GLUCOSE_MG_DL}–{_MAX_GLUCOSE_MG_DL}] mg/dL."`
- L231: `if declared_unit and declared_unit.lower() not in ("mg/dl", "mgdl"):`
- L241: `payload[field] = "mg/dL"`

## `backend/diabetes/migrations/0001_initial.py`
- L22: `('blood_sugar', models.DecimalField(decimal_places=2, help_text='Blood sugar level (mg/dL)', max_digits=5)),`
- L41: `('language', models.CharField(choices=[('fr', 'French'), ('ar', 'Arabic')], default='fr', max_length=2)),`

## `backend/diabetes/migrations/0002_patientprofile.py`
- L22: `('target_range_low', models.IntegerField(default=70, help_text='Lower target glucose (mg/dL)')),`
- L23: `('target_range_high', models.IntegerField(default=180, help_text='Upper target glucose (mg/dL)')),`
- L24: `('unit_preference', models.CharField(choices=[('mg_dl', 'mg/dL'), ('mmol_l', 'mmol/L')], default='mg_dl', help_text='Preferred glucose unit', max_length=6)),`

## `backend/diabetes/migrations/0007_amina_fields.py`
- L36: `name='preferred_language',`
- L37: `field=models.CharField(choices=[('fr', 'Français'), ('ar-MA', 'Darija')], default='fr', help_text='UI language preference (Flutter + future Django i18n).', max_length=8),`

## `backend/diabetes/migrations/0013_default_language_ar_ma.py`
- L15: `name='preferred_language',`
- L16: `field=models.CharField(choices=[('fr', 'Français'), ('ar-MA', 'Darija (dialecte marocain)'), ('ar', 'Arabe classique (Fusha)')], default='ar-MA', help_text='UI language preference (Flutter + future Django i18n).', max_length=8),`

## `backend/diabetes/migrations/0014_remove_daily_wellness_blood_sugar_constraint.py`
- L9: `2. Add a DB-level CheckConstraint on blood_sugar (30 ≤ value ≤ 600 mg/dL).`
- L20: `("diabetes", "0013_default_language_ar_ma"),`
- L33: `violation_error_message="Blood sugar must be between 30 and 600 mg/dL.",`

## `backend/diabetes/migrations/0015_lab_report.py`
- L24: `('fasting_glucose_mgdl', models.FloatField(blank=True, help_text='Glucose à jeun mg/dL', null=True)),`

## `backend/diabetes/migrations/0017_patientprofile_to_extension.py`
- L161: `migrations.RemoveField(model_name="diabetesprofile", name="preferred_language"),`

## `backend/diabetes/models/entry.py`
- L83: `help_text="Blood sugar level (mg/dL)"`
- L167: `violation_error_message='Blood sugar must be between 30 and 600 mg/dL.',`
- L177: `return f"{self.patient.username} - {self.effective_time.strftime('%Y-%m-%d %H:%M')} - {self.blood_sugar} mg/dL"`

## `backend/diabetes/models/lab_report.py`
- L39: `fasting_glucose_mgdl   = models.FloatField(null=True, blank=True, help_text='Glucose à jeun mg/dL')`

## `backend/diabetes/models/patient.py`
- L5: `Identity fields (firebase_uid, preferred_language, etc.) now live on`
- L43: `('mg_dl', 'mg/dL'),`
- L44: `('mmol_l', 'mmol/L'),`
- L71: `help_text="Lower target glucose (mg/dL)",`
- L76: `help_text="Upper target glucose (mg/dL)",`
- L108: `# These proxy to base_profile so callers that do profile.preferred_language`
- L128: `def preferred_language(self):`
- L129: `return self.base_profile.preferred_language`
- L131: `@preferred_language.setter`
- L132: `def preferred_language(self, value):`
- L133: `self.base_profile.preferred_language = value`
- L195: `Identity field setters (firebase_uid, preferred_language, etc.) write`

## `backend/diabetes/models/summary.py`
- L8: `LANGUAGE_CHOICES = [`
- L21: `language = models.CharField(`
- L23: `choices=LANGUAGE_CHOICES,`
- L43: `return f"{self.patient.username} - {self.created_at.strftime('%Y-%m-%d')} - {self.language}"`

## `backend/diabetes/services/clinical/alerts.py`
- L7: `- Level 2 Hypoglycemia (< 54 mg/dL)`
- L8: `- Severe Hyperglycemia (> 300 mg/dL)`
- L23: `class AlertLevel(Enum):`
- L39: `level: AlertLevel`
- L47: `# ── Thresholds (mg/dL) ──`
- L57: `level=AlertLevel.EMERGENCY,`
- L61: `"Ta glycémie est dangereusement basse (< 54 mg/dL).\n"`
- L69: `"السكر ديالك نازل بزاف (< 54 mg/dL).\n"`
- L79: `level=AlertLevel.WARNING,`
- L83: `"Ta glycémie est en dessous de 70 mg/dL.\n"`
- L90: `"السكر ديالك تحت 70 mg/dL.\n"`
- L97: `level=AlertLevel.CRITICAL,`
- L101: `"Ta glycémie dépasse 300 mg/dL.\n"`
- L109: `"السكر ديالك فوق 300 mg/dL.\n"`
- L118: `level=AlertLevel.WARNING,`
- L122: `"Ta glycémie reste élevée (> 250 mg/dL) sur plusieurs mesures consécutives.\n"`
- L128: `"السكر ديالك باقي فوق 250 mg/dL على عدة قياسات.\n"`
- L138: `level=AlertLevel.NONE,`
- L156: `logger.warning("ALERT: Hypo severe — %s mg/dL", glucose_value)`
- L165: `logger.warning("ALERT: Hyper severe — %s mg/dL", glucose_value)`

## `backend/diabetes/services/clinical/correlations.py`
- L7: `from django.utils import timezone`
- L48: `f"{direction_phrase} ({avg_active:.0f} vs {avg_baseline:.0f} mg/dL)."`
- L70: `since = timezone.now() - timedelta(days=window_days)`

## `backend/diabetes/services/clinical/engine.py`
- L41: `# ── Darija (ar-MA) overrides — used when patient preferred_language == "ar-MA" ──`
- L89: `evidence=f"Glycémie moyenne le matin : {avg_morning:.0f} mg/dL vs {avg_night:.0f} mg/dL la nuit.",`
- L91: `f"Vos glycémies matinales ({avg_morning:.0f} mg/dL en moyenne) sont "`
- L92: `f"significativement plus élevées que vos relevés nocturnes ({avg_night:.0f} mg/dL), "`
- L100: `f"سكّر ديالك فالصباح ({avg_morning:.0f} mg/dL) كيكون عالي بزاف "`
- L101: `f"على سكّر الليل ({avg_night:.0f} mg/dL). "`
- L133: `evidence=f"{len(hypo_after_exercise)} épisodes < 72 mg/dL les jours d'activité physique. Moyenne : {avg_hypo:.0f} mg/dL.",`
- L136: `f"(< 72 mg/dL, moyenne {avg_hypo:.0f} mg/dL) survenant les jours où vous "`
- L144: `f"(< 72 mg/dL، معدّل {avg_hypo:.0f} mg/dL) في النهار اللي درتي فيه الرياضة. "`
- L175: `evidence=f"Jours stressés : {avg_stressed:.0f} mg/dL vs jours calmes : {avg_calm:.0f} mg/dL (différence : +{delta:.0f} mg/dL).",`
- L178: `f"{avg_stressed:.0f} mg/dL, contre {avg_calm:.0f} mg/dL les jours calmes. "`
- L179: `f"Cette différence de +{delta:.0f} mg/dL est directement liée aux hormones "`
- L185: `f"في النهارات اللي كنتي فيهم مع الستريس، سكّر ديالك كان {avg_stressed:.0f} mg/dL — "`
- L186: `f"وفالنهارات الهادية كان {avg_calm:.0f} mg/dL. "`
- L187: `f"فرق +{delta:.0f} mg/dL — هاد شي من هورمونات الستريس اللي كتزعزع السكّر."`
- L236: `evidence=f"Lendemain d'une mauvaise nuit : {avg_bad:.0f} mg/dL vs bonne nuit : {avg_good:.0f} mg/dL (delta : +{delta:.0f} mg/dL).",`
- L239: `f"atteint en moyenne {avg_bad:.0f} mg/dL — soit +{delta:.0f} mg/dL de plus "`
- L240: `f"qu'après une nuit réparatrice ({avg_good:.0f} mg/dL). "`
- L246: `f"بعد ليلة ماشي مزيانة، سكّر ديالك فالصباح كيكون {avg_bad:.0f} mg/dL — "`
- L247: `f"{delta:.0f} mg/dL زيادة على ليلة مزيانة ({avg_good:.0f} mg/dL). "`
- L281: `evidence=f"Écart-type : {sd:.0f} mg/dL, CV : {cv:.0f}%. Cible recommandée : CV < 36%.",`
- L283: `f"Votre variabilité glycémique est élevée (écart-type : {sd:.0f} mg/dL, "`
- L291: `f"سكّر ديالك كيتبدّل بزاف (SD: {sd:.0f} mg/dL، CV: {cv:.0f}%). "`
- L305: `Food Sensitivity: Glucose peaks (>185 mg/dL) after specific high-carb meals.`
- L422: `higher glucose than non-fatigue days (delta > 20 mg/dL).`
- L442: `f"Jours avec fatigue : {avg_fatigue:.0f} mg/dL vs jours normaux : "`
- L443: `f"{avg_normal:.0f} mg/dL (différence : +{delta:.0f} mg/dL)."`
- L447: `f"atteint {avg_fatigue:.0f} mg/dL, contre {avg_normal:.0f} mg/dL les jours "`
- L448: `f"sans fatigue. Cette différence de +{delta:.0f} mg/dL suggère que la fatigue "`
- L459: `f"فالنهارات اللي كنتي فيهم تعبانة، سكّر ديالك كان {avg_fatigue:.0f} mg/dL — "`
- L460: `f"وفالنهارات العادية كان {avg_normal:.0f} mg/dL. "`
- L461: `f"فرق +{delta:.0f} mg/dL — التعب كيزعزع السكّر عبر الكورتيزول."`
- L473: `higher glucose vs healthy days (delta > 40 mg/dL).`
- L474: `Escalated to priority=1 when delta > 80 mg/dL (severe hyperglycemia risk).`
- L498: `f"Jours de maladie : {avg_sick:.0f} mg/dL vs jours sains : "`
- L499: `f"{avg_healthy:.0f} mg/dL (différence : +{delta:.0f} mg/dL)."`
- L503: `f"a atteint {avg_sick:.0f} mg/dL en moyenne, soit +{delta:.0f} mg/dL "`
- L504: `f"de plus que les jours sains ({avg_healthy:.0f} mg/dL). "`
- L511: `"dépasse 300 mg/dL ou si des corps cétoniques sont détectés."`
- L515: `f"فالنهارات اللي كنتي فيهم مريضة، سكّر ديالك وصل {avg_sick:.0f} mg/dL — "`
- L516: `f"+{delta:.0f} mg/dL زيادة على النهارات الصحيحة ({avg_healthy:.0f} mg/dL). "`
- L521: `"إلا السكّر فاق 300 mg/dL، هضري فوراً مع طبيب ديالك."`
- L528: `Post-meal spike: glucose rises > 60 mg/dL within 2 hours of a logged meal.`
- L571: `f"{len(spike_events)} épisodes — hausse moyenne de +{avg_rise:.0f} mg/dL "`
- L576: `f"(+{avg_rise:.0f} mg/dL en moyenne) dans les 2 heures suivant un repas. "`
- L588: `f"+{avg_rise:.0f} mg/dL في الساعتين من بعد الماكلة. "`
- L611: `def _parse_insights_json(text: str, patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:`
- L622: `return _format_fallback(patterns, language)`
- L629: `# Title: use LLM output if provided, else pick by language`
- L630: `use_darija = language == "ar-MA"`
- L642: `return result if result else _format_fallback(patterns, language)`
- L645: `def _format_with_llm(patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:`
- L647: `Language is injected so the LLM reformulates in the patient's language."""`
- L659: `# get_format_system() injects language label only.`
- L665: `response_text = provider.complete(get_format_system(language), user_prompt).content`
- L666: `return _parse_insights_json(response_text, patterns, language)`
- L669: `return _format_fallback(patterns, language)`
- L672: `def _format_fallback(patterns: list[ClinicalPattern], language: str = "fr") -> list[dict]:`
- L674: `Uses Darija strings when language == 'ar-MA' and the override is set;`
- L676: `use_darija = language == "ar-MA"`
- L694: `def run_clinical_analysis(entries, kpis: AnalyticalKPIs, language: str = "fr") -> ClinicalReport:`
- L701: `language: Patient preferred_language code (e.g. 'fr', 'ar-MA', 'ar').`
- L702: `Drives fallback text language and LLM reformulation language.`
- L737: `insights = _format_with_llm(patterns, language) if patterns else []`
- L780: `language: str = "fr",`
- L786: `from django.utils import timezone`
- L795: `return DomainContext.empty(language=language)`
- L797: `since = timezone.now() - timedelta(days=days)`
- L806: `report = run_clinical_analysis(entries, kpis, language=language)`
- L828: `language=language,`
- L839: `def evaluate_alert(self, entry, language: str = "fr") -> "DomainAlert | None":`
- L841: `from diabetes.services.clinical.alerts import AlertLevel`
- L850: `if resp.level == AlertLevel.NONE:`
- L853: `blocking = resp.level in (AlertLevel.EMERGENCY, AlertLevel.CRITICAL)`
- L854: `message = resp.message_darija if language == "ar-MA" else resp.message_fr`
- L860: `event_description=f"Glucose critique : {g} mg/dL",`

## `backend/diabetes/services/clinical/models.py`
- L12: `avg_glucose: Optional[float] = Field(None, description="Mean blood glucose in mg/dL")`
- L15: `tir_pct: Optional[float] = Field(None, ge=0, le=100, description="Time In Range (70-180 mg/dL) — target ≥ 70%")`
- L16: `tar_pct: Optional[float] = Field(None, ge=0, le=100, description="Time Above Range (> 180 mg/dL)")`
- L17: `tbr_pct: Optional[float] = Field(None, ge=0, le=100, description="Time Below Range (< 70 mg/dL)")`

## `backend/diabetes/services/clinical/prediction.py`
- L8: `from django.utils import timezone`
- L44: `since = timezone.now() - timedelta(days=21)`

## `backend/diabetes/services/clinical/semantic_compressor.py`
- L55: `f"ANALYSIS WINDOW: {kpis.days_with_data} days | {kpis.log_count} readings (all values in mg/dL).",`
- L66: `lines.append(f"  • Mean glucose: {kpis.avg_glucose} mg/dL.{gmi_note}")`
- L72: `f"  • Glycemic variability: SD={kpis.std_dev} mg/dL, CV={kpis.cv_pct}% "`
- L80: `f"  • Time In Range (70-180 mg/dL): {kpis.tir_pct}% "`
- L84: `lines.append(f"  • Time Above Range (>180 mg/dL): {kpis.tar_pct}%.")`
- L87: `lines.append(f"  • Time Below Range (<70 mg/dL): {kpis.tbr_pct}%.{hypoglycemia_flag}")`
- L131: `parts.append(f"avg glucose {kpis.avg_glucose} mg/dL")`
- L157: `patient_language: str = "fr",`
- L165: `patient_language: Patient's preferred language (fr | ar-MA).`
- L174: `# Language instruction appended so the LLM knows which language to respond in`
- L175: `language_map = {"fr": "French", "ar-MA": "Moroccan Darija (Arabic dialect)"}`
- L176: `output_lang = language_map.get(patient_language, "French")`
- L178: `f"\nOUTPUT LANGUAGE: Respond in {output_lang}. "`
- L179: `"Use empathetic, medically precise language. Never prescribe; recommend consulting the physician."`

## `backend/diabetes/services/clinical/sql_analytics.py`
- L26: `"""Immutable KPI snapshot produced by SQL. All values are in mg/dL."""`
- L30: `tir_pct: Optional[float]           # Time In Range 70-180 mg/dL — target ≥ 70%`
- L31: `tar_pct: Optional[float]           # Time Above Range > 180 mg/dL`
- L32: `tbr_pct: Optional[float]           # Time Below Range < 70 mg/dL`
- L42: `tbr_level2_pct: Optional[float] = None  # < 54 mg/dL`
- L43: `tbr_level1_pct: Optional[float] = None  # 54–69 mg/dL`
- L44: `tar_level1_pct: Optional[float] = None  # 181–250 mg/dL`
- L45: `tar_level2_pct: Optional[float] = None  # > 250 mg/dL`
- L236: `target_low: Lower TIR bound in mg/dL.`
- L237: `target_high: Upper TIR bound in mg/dL.`
- L244: `from django.utils import timezone`
- L246: `cutoff = timezone.now() - timedelta(days=days)`
- L280: `# >250 mg/dL). LogEntry currently stores provenance but not the device`
- L342: `from django.utils import timezone`
- L344: `cutoff = timezone.now() - timedelta(days=days)`
- L417: `from django.utils import timezone`
- L419: `cutoff = timezone.now() - timedelta(days=days)`
- L531: `from django.utils import timezone`
- L533: `now = timezone.now()`
- L600: `VLow <54 mg/dL, Low 54-69, High 181-250, VHigh >250. This helper`

## `backend/diabetes/services/clinical/unit_guard.py`
- L6: `Critical for the Moroccan market where patients may use mg/dL, mmol/L or g/L.`
- L8: `Standard: mg/dL = mmol/L * 18.018`
- L13: `"""Convert mg/dL to mmol/L (Standard UK/France)."""`
- L18: `"""Convert mmol/L to mg/dL (Standard Morocco/US)."""`
- L23: `"""Convert mg/dL to g/L (Common in older French labs)."""`
- L28: `"""Convert g/L to mg/dL."""`
- L35: `if u == 'mmol/l':`
- L39: `# Default is mg/dL`

## `backend/diabetes/services/documents/extractors/spreadsheet.py`
- L29: `'historic glucose mg/dl', 'scan glucose mg/dl',`
- L30: `'glycémie historique mg/dl', 'glycémie scannée mg/dl',`
- L31: `'historic glucose mmol/l', 'scan glucose mmol/l',`
- L35: `_DEXCOM_GLUCOSE_COLS    = ['glucose value (mg/dl)', 'egv (mg/dl)']`
- L39: `'mg/dl', 'mmol/l', 'glukose', 'glucosa']`
- L103: `unit = 'mmol/L' if 'mmol' in lc else 'mg/dL'`
- L111: `return 'cgm_export', cols_lower[lc], tc, 'mg/dL'`
- L116: `unit = 'mmol/L' if 'mmol' in lc else 'mg/dL'`
- L120: `return 'unknown', None, None, 'mg/dL'`

## `backend/diabetes/services/documents/schema.py`
- L20: `original_unit:  Optional[str]  = None   # "mg/dL" | "mmol/L"`

## `backend/diabetes/services/documents/shield.py`
- L23: `_GLUCOSE_MIN   = 20.0    # mg/dL — below this is implausible (physiological min ~40)`
- L24: `_GLUCOSE_MAX   = 600.0   # mg/dL — critically high but possible`
- L27: `_CHOLESTEROL_MAX = 600.0  # mg/dL`
- L38: `f"Glycémie hors plage physiologique ({r.value_mgdl:.0f} mg/dL) — ignorée."`
- L69: `warnings.append(f"Glucose à jeun hors plage ({lab.fasting_glucose_mgdl} mg/dL) — ignoré.")`

## `backend/diabetes/services/documents/store.py`
- L24: `from django.utils import timezone as tz`
- L90: `ts = tz.make_aware(ts, tz.get_current_timezone())`

## `backend/diabetes/services/import_csv/librelink_parser.py`
- L9: `Device,Serial Number,Device Timestamp,Record Type,Historic Glucose mg/dL,Scan Glucose mg/dL,...`
- L15: `11/05/2026 08:30,150,mg/dL`
- L18: `physiological range (20-600 mg/dL) are silently dropped.`
- L58: `detected_unit:   str = "mg/dL"`
- L66: `# ── Date parsing — LibreLink uses several formats depending on locale ────────`
- L100: `# Convert mmol/L → mg/dL if needed (×18)`
- L114: `"device timestamp", "historic glucose mg/dl",`
- L115: `"horodatage de l'appareil", "glucose historique mg/dl",`
- L215: `LibreView 'Detailed' export columns (varies by language):`
- L218: `- Historic Glucose mg/dL  (Record Type 0)`
- L219: `- Scan Glucose mg/dL      (Record Type 1)`
- L220: `- Strip Glucose mg/dL     (Record Type 2)`
- L224: `hist_col = _find_col(header, "Historic Glucose mg/dL", "Glucose historique mg/dL")`
- L225: `scan_col = _find_col(header, "Scan Glucose mg/dL", "Glucose lu mg/dL")`
- L226: `strip_col = _find_col(header, "Strip Glucose mg/dL", "Glucose bandelette mg/dL")`
- L251: `v = _parse_glucose(row[col], "mg/dL")`
- L283: `# Default unit from first non-empty unit cell, else mg/dL`
- L284: `default_unit = "mg/dL"`
- L302: `result.detected_unit = "mmol/L"`

## `backend/diabetes/services/summary.py`
- L5: `from django.utils import timezone`
- L92: `entry = f"- {entry_date}: Glycémie {log.blood_sugar} mg/dL, "`
- L172: `language='fr',`
- L189: `Explication: Sur 14 jours, 5 pics hyperglycémiques (>180 mg/dL) surviennent après des dîners riches en glucides rapides (pâtes, pizza, couscous) avec une dose d'insuline ≤9 unités.`
- L193: `Explication: 2 épisodes (<70 mg/dL) surviennent en pleine nuit dans les heures suivant une activité physique en soirée sans apport glucidique post-effort.`
- L202: `language='fr',`

## `backend/diabetes/tests/test_account_rgpd.py`
- L14: `from django.utils import timezone`
- L51: `base.ai_consent_given_at = timezone.now()`
- L121: `base.ai_consent_given_at = timezone.now()`
- L182: `LogEntry.objects.create(patient=self.user, blood_sugar=120, logged_at=timezone.now())`

## `backend/diabetes/tests/test_advice_filter.py`
- L12: `from datetime import datetime, timedelta, timezone`
- L35: `return (datetime.now(timezone.utc) - last) < timedelta(hours=hours)`
- L40: `self.last_advice_given_at = datetime.now(timezone.utc).isoformat()`
- L166: `old_ts = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()`
- L185: `ts_fixed = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()`
- L249: `m.last_advice_given_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()`
- L255: `m.last_advice_given_at = (datetime.now(timezone.utc) - timedelta(hours=24, seconds=1)).isoformat()`

## `backend/diabetes/tests/test_amina_fields.py`
- L8: `P2 update: identity fields (firebase_uid, preferred_language, premium_valid_until)`
- L18: `from django.utils import timezone`
- L37: `def test_preferred_language_defaults_to_darija(self):`
- L38: `self.assertEqual(self.profile.preferred_language, 'ar-MA')`
- L40: `def test_preferred_language_accepts_darija(self):`
- L41: `self.base.preferred_language = 'ar-MA'`
- L44: `self.assertEqual(self.profile.preferred_language, 'ar-MA')`
- L64: `self.base.premium_valid_until = timezone.now() + timedelta(days=30)`
- L79: `"""DB-level CheckConstraint rejects values outside [30, 600] mg/dL."""`

## `backend/diabetes/tests/test_api.py`
- L9: `from django.utils import timezone`
- L94: `LogEntry.objects.create(patient=self.user, blood_sugar=180, logged_at=timezone.now())`
- L127: `LogEntry.objects.create(patient=self.user, blood_sugar=100, logged_at=timezone.now())`
- L128: `LogEntry.objects.create(patient=user2, blood_sugar=200, logged_at=timezone.now())`
- L155: `log = LogEntry.objects.create(patient=self.user, blood_sugar=160, logged_at=timezone.now())`
- L163: `log = LogEntry.objects.create(patient=self.user, blood_sugar=170, logged_at=timezone.now())`
- L183: `LogEntry.objects.create(patient=self.user, blood_sugar=350, logged_at=timezone.now())`
- L187: `# High glucose (350 mg/dL > 180 threshold) → TAR% must be > 0`
- L192: `LogEntry.objects.create(patient=self.user, blood_sugar=50, logged_at=timezone.now())`
- L196: `# Low glucose (50 mg/dL < 70 threshold) → TBR% must be > 0`
- L201: `LogEntry.objects.create(patient=self.user, blood_sugar=120, logged_at=timezone.now())`

## `backend/diabetes/tests/test_battelino_kpis.py`
- L11: `from datetime import datetime, timedelta, timezone`
- L26: `now = datetime.now(timezone.utc)`
- L94: `"""TBR1 covers 54-69 mg/dL exclusively. 54 belongs to TBR1, 53 to TBR2."""`
- L112: `"""TAR1 covers 181-250 mg/dL. 250 belongs to TAR1, 251 to TAR2."""`

## `backend/diabetes/tests/test_clinical_detectors.py`
- L68: `self.assertLess(_gmi(70), _gmi(154))`

## `backend/diabetes/tests/test_clinical_engine.py`
- L498: `self.assertLessEqual(report.patterns[0].priority, 2)`

## `backend/diabetes/tests/test_clinical_shield.py`
- L26: `# ADA severe hypo threshold: < 54 mg/dL`
- L69: `def test_mixed_language_forbidden_term(self):`
- L110: `54 mg/dL is the ADA severe-hypo cutoff; 400 mg/dL is the crisis-hyper cutoff.`

## `backend/diabetes/tests/test_correlations_prediction.py`
- L5: `from django.utils import timezone`
- L26: `ts = timezone.now() - timedelta(hours=hours_ago)`
- L67: `self.assertLessEqual(prediction.predicted_value, 600.0)`

## `backend/diabetes/tests/test_emit_inactive_events.py`
- L17: `from django.utils import timezone`
- L66: `timestamp=timezone.now(),`

## `backend/diabetes/tests/test_entries.py`
- L6: `- Blood-sugar range validation enforced at the API boundary (ge=30, le=600 mg/dL)`
- L15: `from django.utils import timezone`
- L56: `"""blood_sugar=25 is below the API minimum (30 mg/dL) → 422, no entry saved."""`
- L66: `"""blood_sugar=700 exceeds the API maximum (600 mg/dL) → 422, no entry saved."""`
- L80: `logged_at=timezone.now(),`
- L97: `logged_at=timezone.now(),`
- L114: `logged_at=timezone.now(),`
- L147: `self.assertLessEqual(data["page_size"], 200)`
- L159: `logged_at=timezone.now(),`

## `backend/diabetes/tests/test_gri.py`
- L95: `self.assertLessEqual(result, 100.0)`
- L247: `# Evidence must mention the mg/dL values`
- L248: `self.assertIn("mg/dL", result.evidence)`
- L313: `self.assertIn("mg/dL", result.evidence)`

## `backend/diabetes/tests/test_iamina_core.py`
- L64: `self.assertLessEqual(len(memory.last_concern), 100)`

## `backend/diabetes/tests/test_iamina_state.py`
- L52: `language="fr",`
- L103: `self.assertLessEqual(state.satisfaction, 1.0)`
- L111: `self.assertLessEqual(state.satisfaction, 1.0)`
- L156: `self.assertLessEqual(state.concern_level, 1.0)`
- L215: `self.assertLessEqual(state.engagement, 1.0)`
- L392: `language="français",`

## `backend/diabetes/tests/test_librelink_parser.py`
- L20: `"Device","Serial Number","Horodatage de l'appareil","Record Type","Glucose historique mg/dL","Glucose lu mg/dL","Strip Glucose mg/dL"`
- L30: `11-05-2026 08:00,120,mg/dL`
- L31: `11-05-2026 09:00,145,mg/dL`
- L32: `11-05-2026 10:00,168,mg/dL`
- L37: `11-05-2026 08:00,7.5,mmol/L`
- L38: `11-05-2026 09:00,9.0,mmol/L`
- L43: `11-05-2026 08:00,150,mg/dL`
- L44: `11-05-2026 09:00,9999,mg/dL`
- L45: `11-05-2026 10:00,5,mg/dL`
- L46: `11-05-2026 11:00,200,mg/dL`
- L90: `# ── mmol/L conversion ─────────────────────────────────────────────────────────`
- L97: `# 7.5 mmol/L × 18 = 135 mg/dL`
- L102: `self.assertEqual(r.detected_unit, "mmol/L")`
- L183: `"NOT_A_DATE,120,mg/dL\n"`
- L184: `"11-05-2026 08:00,150,mg/dL\n"`
- L195: `"11-05-2026 08:00,120,mg/dL\n"`
- L197: `"11-05-2026 09:00,145,mg/dL\n"`

## `backend/diabetes/tests/test_ninja_crud.py`
- L15: `from django.utils import timezone`
- L42: `return LogEntry.objects.create(patient=user, blood_sugar=Decimal(bg), logged_at=timezone.now())`

## `backend/diabetes/tests/test_onboarding.py`
- L6: `update language, unit preference, and glucose target bounds.`
- L9: `- preferred_language must be one of {"fr", "ar-MA", "ar"}`
- L41: `"""PATCH /api/v1/profile — language, unit, and target-range validation."""`
- L48: `"""PATCH with valid preferred_language='fr' → 200, language persisted."""`
- L51: `data={"preferred_language": "fr"},`
- L56: `self.assertEqual(data["preferred_language"], "fr")`
- L58: `self.assertEqual(self.alice.base_profile.preferred_language, "fr")`
- L61: `"""PATCH with unsupported preferred_language='zh' → 422 (not in allowed set)."""`
- L64: `data={"preferred_language": "zh"},`
- L70: `"""PATCH with target_range_high=999 exceeds the 400 mg/dL ceiling → 422."""`
- L88: `"""PATCH with target_range_low=10 is below the 40 mg/dL floor → 422."""`

## `backend/diabetes/tests/test_p0_clinical_analytics_integrity.py`
- L7: `from django.utils import timezone`
- L45: `ts = timezone.now() - timedelta(days=1)`

## `backend/diabetes/tests/test_phase6_intelligence.py`
- L3: `from companion.prompts import LANGUAGE_LABELS, get_language_label`
- L12: `Unit tests for Unit Guard, Clinical Shield, and Prompt Language Layer.`
- L16: `builds English Pivot Text inline. Tests for prompt language injection are`
- L21: `# mg/dL -> mmol/L`
- L25: `# mmol/L -> mg/dL`
- L28: `# mg/dL -> g/L`
- L60: `def test_language_labels_completeness(self):`
- L61: `"""Verify all supported language codes produce non-empty instructions."""`
- L63: `label = get_language_label(code)`
- L64: `self.assertTrue(label, f"Language label for '{code}' must not be empty")`
- L67: `def test_language_label_fallback(self):`
- L68: `"""Unknown language codes fall back to the raw code (no crash)."""`
- L70: `result = get_language_label(unknown)`
- L74: `"""ar-MA label must contain Darija markers in Arabic script (not Latin transliteration)."""`
- L75: `label = LANGUAGE_LABELS["ar-MA"]`
- L82: `label = LANGUAGE_LABELS["ar"]`

## `backend/diabetes/tests/test_sidebar.py`
- L4: `Rewritten from SidebarImportLinkTests (Django template views removed).`
- L13: `from django.utils import timezone`
- L33: `class SidebarImportLinkTests(TestCase):`
- L48: `logged_at=timezone.now(),`
- L53: `logged_at=timezone.now(),`

## `backend/diabetes/tests/test_sprint2_modules.py`
- L14: `from django.utils import timezone`
- L127: `self.assertLessEqual(len(result.replace("[", "").replace("]", "")), 200)`
- L165: `now = timezone.now()`
- L187: `e.effective_time = timezone.now() + timedelta(hours=hours_offset)`
- L205: `from datetime import datetime, timezone`
- L209: `base = datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc)`
- L232: `base = timezone.now()`

## `backend/diabetes/tests/test_sprint4_services.py`
- L134: `def test_french_language_injects_french_hint(self):`
- L139: `transcribe(_TINY_AUDIO, _VALID_MIME, language="fr")`
- L143: `def test_darija_language_injects_darija_hint(self):`
- L145: `# passed explicitly as language_hints — it is no longer embedded`
- L146: `# in the built-in _LANGUAGE_HINTS table inside media.voice.`
- L152: `transcribe(_TINY_AUDIO, _VALID_MIME, language="ar-MA",`
- L153: `language_hints=AR_MA_STT_HINTS)`
- L207: `pivot_text="AVG_GLUCOSE: 150 mg/dL\nTIR: 70%",`
- L208: `language="fr",`
- L281: `def test_darija_language_propagated_to_llm(self):`
- L282: `"""language='ar-MA' must reach the LLM prompt (not silently swallowed)."""`
- L288: `# As long as LLM was called and returned a narrative, language hint was used.`
- L381: `self.assertEqual(convert_to_mg_dl(120.0, "mg/dL"), 120.0)`
- L385: `self.assertEqual(convert_to_mg_dl(100.0, "MG/DL"), 100.0)`
- L389: `result = convert_to_mg_dl(7.0, "mmol/L")`
- L409: `"""0.1 mmol/L → 1.8 mg/dL < 20 mg/dL minimum."""`
- L412: `convert_to_mg_dl(0.1, "mmol/L")`
- L415: `"""40 mmol/L → 720.6 mg/dL > 700 mg/dL maximum."""`
- L418: `convert_to_mg_dl(40.0, "mmol/L")`
- L422: `result = convert_to_mg_dl(5.5, "mmol/L")`
- L509: `data=json.dumps({"blood_sugar": 7.0, "unit": "mmol/L"}),`
- L516: `self.assertEqual(body["unit"], "mg/dL")   # unit field canonicalised`

## `backend/diabetes/tests/test_sql_analytics.py`
- L24: `from django.utils import timezone`
- L40: `ts = timezone.now() - timedelta(days=days_ago)`
- L195: `logged_at=timezone.now() - timedelta(days=30),`
- L209: `logged_at=timezone.now() - timedelta(days=20),`
- L226: `self.assertLess(kpis_narrow.tir_pct, 100.0)`
- L250: `logged_at=timezone.now() - timedelta(days=1),`

## `backend/diabetes/tests/test_triage_vital.py`
- L7: `2. _pick_emergency_response() — language selection (FR vs Darija)`

## `backend/diabetes/tests/test_ui_wiring.py`
- L15: `from django.utils import timezone`
- L49: `patient=self.alice, blood_sugar=Decimal("110"), logged_at=timezone.now()`
- L52: `patient=bob, blood_sugar=Decimal("240"), logged_at=timezone.now()`
- L84: `patient=self.alice, blood_sugar=Decimal("110"), logged_at=timezone.now()`
- L87: `patient=self.bob, blood_sugar=Decimal("240"), logged_at=timezone.now()`
- L101: `now = timezone.now()`

## `backend/evals/golden_cases/v1.json`
- L6: `"message": "Je tremble et j'ai 45 mg/dL.",`

## `backend/media/documents/pulper.py`
- L90: `- Convert mmol/L to mg/dL: multiply by 18.018`

## `backend/media/vision.py`
- L201: `"{\"value\": <number or null>, \"unit\": \"<mg/dL or mmol/L>\", \"confidence\": \"<high/medium/low>\"}\n\n"`
- L204: `"- unit: exactly \"mg/dL\" or \"mmol/L\" based on what is shown on the display.\n"`
- L205: `"  If unit is not visible: guess from value magnitude (>30 → mg/dL, ≤30 → mmol/L).\n"`
- L217: `{"value": float|None, "unit": "mg/dL"|"mmol/L", "confidence": str, "fallback": bool}`
- L259: `unit       = parsed.get("unit", "mg/dL")`
- L262: `if unit not in ("mg/dL", "mmol/L"):`
- L263: `unit = "mg/dL"`
- L281: `return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}`

## `backend/media/voice.py`
- L7: `Language support:`
- L9: `ar-MA → Moroccan Darija (dialect + French code-switching)`
- L12: `D2 extension: accepts language_hints: dict | None = None.`
- L13: `- When provided, language_hints overrides the built-in hint lookup.`
- L46: `# Built-in language hints for fr and ar (ar-MA removed — lives in stt_vocabulary.py)`
- L47: `_LANGUAGE_HINTS: dict[str, str] = {`
- L54: `"Transcribe the audio EXACTLY as spoken, preserving the original language and dialect. "`
- L61: `"Transcribe this audio. The speaker uses {language_hint}. "`
- L78: `language: str = "fr",`
- L79: `language_hints: dict | None = None,`
- L87: `language:       Patient preferred_language code — drives the language hint`
- L89: `language_hints: Optional override dict {lang_code: hint_str}.`
- L91: `_LANGUAGE_HINTS table for the hint lookup.`
- L114: `# Resolve language hint — caller-supplied dict takes precedence`
- L115: `hints_table = language_hints if language_hints is not None else _LANGUAGE_HINTS`
- L116: `language_hint = hints_table.get(language, "French or Arabic")`
- L117: `user_prompt   = _STT_USER_TEMPLATE.format(language_hint=language_hint)`
- L156: `len(audio_bytes), mime_type, language, len(transcript),`
- L163: `logger.exception("STT: transcription failed (lang=%s)", language)`

## `frontend/README.md`
- L41: `- Locale is more than one language code: country, UI language, response language, dialect, script/transliteration, units, time zone, and emergency jurisdiction must remain separable.`
- L42: `- Location may suggest locale choices; it must not silently determine them.`
- L43: `- RTL and Arabic-script behavior must be tested for enabled pilot locales.`

## `frontend/analysis_options.yaml`
- L32: `# https://dart.dev/guides/language/analysis-options`

## `frontend/l10n.yaml`
- L5: `synthetic-locale: false`

## `frontend/lib/core/clinical/glucose_ocr_shield.dart`
- L10: `//       – mg/dL numeric (most EU/MA devices)`
- L11: `//       – mmol/L numeric (UK/CA devices) → converted to mg/dL`
- L12: `//       – "HI"  → glucometer saturated above measurable range (> ~600 mg/dL)`
- L13: `//       – "LO"  → glucometer below measurable range (< ~20 mg/dL)`
- L14: `//   • Physiological bounds: 20–600 mg/dL (outside = rejected)`
- L22: `/// Glucose value in mg/dL. Null when nothing valid was detected.`
- L33: `/// Glucometer displayed "HI" — glucose above measurable range (≳ 600 mg/dL).`
- L36: `/// Glucometer displayed "LO" — glucose below measurable range (≲ 20 mg/dL).`
- L39: `/// True if the glucometer unit was detected as mmol/L`
- L40: `/// and [value] has already been converted to mg/dL (× 18).`
- L76: `/// Detects mmol/L unit anywhere in the OCR text.`
- L91: `/// mmol/L readings: e.g. "6.5", "13.2", "3.8"`
- L120: `// ── mmol/L path ───────────────────────────────────────────────────────────`
- L125: `// ── mg/dL path (default) ─────────────────────────────────────────────────`

## `frontend/lib/core/utils/glucose_formatter.dart`
- L7: `/// [valueMgDl] : Valeur brute en mg/dL (stockage standard).`
- L8: `/// [unit] : "mg/dL" ou "mmol/L".`
- L10: `if (unit.toLowerCase() == 'mmol/l') {`
- L12: `return '${mmolValue.toStringAsFixed(1)} mmol/L';`
- L14: `return '${valueMgDl.toStringAsFixed(0)} mg/dL';`
- L19: `if (unit.toLowerCase() == 'mmol/l') {`
- L29: `return unit.toLowerCase() == 'mmol/l' ? [4.0, 10.0] : [70.0, 180.0];`
- L38: `final padding = range > 0 ? range * 0.1 : (unit.toLowerCase() == 'mmol/l' ? 1.0 : 20.0);`

## `frontend/lib/data/drift/database.dart`
- L40: `TextColumn get preferredLanguage => text().withDefault(const Constant('fr'))();`
- L45: `TextColumn get unitPreference => text().withDefault(const Constant('mg/dL'))();`
- L217: `// Add realistic noise: ±25 mg/dL normal, occasional spikes`
- L265: `unitPreference: const Value('mg/dL'),`

## `frontend/lib/data/drift/database.g.dart`
- L1094: `static const VerificationMeta _preferredLanguageMeta = const VerificationMeta(`
- L1095: `'preferredLanguage',`
- L1098: `late final GeneratedColumn<String> preferredLanguage =`
- L1100: `'preferred_language',`
- L1163: `defaultValue: const Constant('mg/dL'),`
- L1191: `preferredLanguage,`
- L1218: `if (data.containsKey('preferred_language')) {`
- L1220: `_preferredLanguageMeta,`
- L1221: `preferredLanguage.isAcceptableOrUnknown(`
- L1222: `data['preferred_language']!,`
- L1223: `_preferredLanguageMeta,`
- L1299: `preferredLanguage: attachedDatabase.typeMapping.read(`
- L1301: `data['${effectivePrefix}preferred_language'],`
- L1343: `final String preferredLanguage;`
- L1358: `required this.preferredLanguage,`
- L1371: `map['preferred_language'] = Variable<String>(preferredLanguage);`
- L1391: `preferredLanguage: Value(preferredLanguage),`
- L1415: `preferredLanguage: serializer.fromJson<String>(json['preferredLanguage']),`
- L1432: `'preferredLanguage': serializer.toJson<String>(preferredLanguage),`
- L1445: `String? preferredLanguage,`
- L1455: `preferredLanguage: preferredLanguage ?? this.preferredLanguage,`
- L1469: `preferredLanguage: data.preferredLanguage.present`
- L1470: `? data.preferredLanguage.value`
- L1471: `: this.preferredLanguage,`
- L1496: `..write('preferredLanguage: $preferredLanguage, ')`
- L1511: `preferredLanguage,`
- L1525: `other.preferredLanguage == this.preferredLanguage &&`
- L1537: `final Value<String> preferredLanguage;`
- L1547: `this.preferredLanguage = const Value.absent(),`
- L1558: `this.preferredLanguage = const Value.absent(),`
- L1569: `Expression<String>? preferredLanguage,`
- L1580: `if (preferredLanguage != null) 'preferred_language': preferredLanguage,`
- L1593: `Value<String>? preferredLanguage,`
- L1604: `preferredLanguage: preferredLanguage ?? this.preferredLanguage,`
- L1621: `if (preferredLanguage.present) {`
- L1622: `map['preferred_language'] = Variable<String>(preferredLanguage.value);`
- L1652: `..write('preferredLanguage: $preferredLanguage, ')`
- L2522: `Value<String> preferredLanguage,`
- L2534: `Value<String> preferredLanguage,`
- L2558: `ColumnFilters<String> get preferredLanguage => $composableBuilder(`
- L2559: `column: $table.preferredLanguage,`
- L2613: `ColumnOrderings<String> get preferredLanguage => $composableBuilder(`
- L2614: `column: $table.preferredLanguage,`
- L2666: `GeneratedColumn<String> get preferredLanguage => $composableBuilder(`
- L2667: `column: $table.preferredLanguage,`
- L2741: `Value<String> preferredLanguage = const Value.absent(),`
- L2751: `preferredLanguage: preferredLanguage,`
- L2763: `Value<String> preferredLanguage = const Value.absent(),`
- L2773: `preferredLanguage: preferredLanguage,`

## `frontend/lib/data/models/ai_models.dart`
- L157: `final String replyLanguage;`
- L164: `this.replyLanguage = 'fr',`
- L173: `replyLanguage: json['reply_language'] as String? ?? 'fr',`
- L207: `final String unit;          // "mg/dL" | "mmol/L"`
- L222: `unit:       json['unit']       as String? ?? 'mg/dL',`
- L235: `final String replyLanguage;`
- L243: `this.replyLanguage = 'fr',`
- L253: `replyLanguage:  json['reply_language']  as String? ?? 'fr',`

## `frontend/lib/features/auth/onboarding_chat_screen.dart`
- L27: `'unit': 'mg/dL',`
- L106: `await _addBotMessage("Très bien. Quels sont tes objectifs glycémiques (en mg/dL) ? On utilise classiquement 70–180.");`
- L119: `{'id': 'mg/dL',  'label': 'mg/dL  (standard France/Maroc)'},`
- L120: `{'id': 'mmol/L', 'label': 'mmol/L  (UK, Canada, international)'},`
- L147: `preferredLanguage: const drift.Value('fr'),`

## `frontend/lib/features/dashboard/clinical_engine.dart`
- L11: `/// Standard ADA range: 70–180 mg/dL.`
- L27: `/// Time Above Range (TAR) - Very High (> 250 mg/dL) — offline fallback.`
- L44: `/// Time Below Range (TBR) - Very Low (< 54 mg/dL) — offline fallback.`
- L53: `/// ADA 2023 Formula: GMI(%) = 3.31 + 0.02392 × mean_glucose_mg/dL.`

## `frontend/lib/features/dashboard/dashboard_screen.dart`
- L129: `final unit = _cachedUnit ?? 'mg/dL';`
- L130: `final val = unit == 'mmol/L'`
- L131: `? '${(latest.bloodSugar / 18.0).toStringAsFixed(1)} mmol/L'`
- L132: `: '${latest.bloodSugar.toInt()} mg/dL';`
- L167: `final unit   = profile?.unitPreference ?? 'mg/dL';`

## `frontend/lib/features/dashboard/widgets/add_log_sheet.dart`
- L275: `final unit    = profile?.unitPreference ?? 'mg/dL';`
- L505: `final sliderMax = unit == 'mmol/L' ? 22.2 : 400.0;`
- L506: `final sliderMin = unit == 'mmol/L' ? 2.2  : 40.0;`
- L509: `final quickValues = unit == 'mmol/L'`
- L611: `final active = (_glucoseValue - v).abs() < (unit == 'mmol/L' ? 0.1 : 0.5);`
- L612: `final lbl = unit == 'mmol/L' ? v.toStringAsFixed(1) : v.toInt().toString();`
- L651: `final r = unit == 'mmol/L' ? double.parse(val.toStringAsFixed(1)) : val.roundToDouble();`
- L652: `setState(() { _glucoseValue = r; _manualController.text = unit == 'mmol/L' ? r.toStringAsFixed(1) : r.toInt().toString(); });`
- L660: `_SliderLabel(unit == 'mmol/L' ? '2.2' : '40',  color),`
- L661: `_SliderLabel(unit == 'mmol/L' ? '3.9' : '70',  color),`
- L662: `_SliderLabel(unit == 'mmol/L' ? '10' : '180',  color),`
- L663: `_SliderLabel(unit == 'mmol/L' ? '22' : '400',  color),`
- L1576: `final mgdlValue = context.read<PatientProfileData?>()?.unitPreference == 'mmol/L'`
- L1586: `? 'Une glycémie de ${mgdlValue.toInt()} mg/dL est dangereuse. Prenez 15g de glucides rapides maintenant. Confirmer quand même ?'`
- L1587: `: 'Une glycémie de ${mgdlValue.toInt()} mg/dL est très élevée. Confirmer l\'enregistrement ?'),`
- L1601: `// Mild/moderate hypoglycemia gate (54–69 mg/dL) — show pre-validated advice`
- L1611: `final unit      = profile?.unitPreference ?? 'mg/dL';`
- L1612: `final bloodSugarMgdl = unit == 'mmol/L' ? _glucoseValue * 18.0 : _glucoseValue;`
- L1641: `final displayVal = unit == 'mmol/L'`
- L1642: `? '${_glucoseValue.toStringAsFixed(1)} mmol/L'`
- L1643: `: '${bloodSugarMgdl.toInt()} mg/dL';`
- L1673: `final val = unit == 'mmol/L' ? '${(mgdl / 18.0).toStringAsFixed(1)} mmol/L' : '${mgdl.toInt()} mg/dL';`
- L1735: `// Convert to mg/dL if needed so GlucoseOcrResult is always mg/dL`
- L1736: `final mgdl = resp.unit == 'mmol/L' ? resp.value! * 18.0 : resp.value!;`
- L1741: `unitWasMmol: resp.unit == 'mmol/L',`
- L1825: `final displayValue = unit == 'mmol/L' ? accepted / 18.0 : accepted;`
- L1826: `final displayStr   = unit == 'mmol/L'`
- L2068: `// Shown when glucose is 54–69 mg/dL — immediate, fixed ADA advice.`
- L2095: `Text('${mgdl.toInt()} mg/dL · Règle 15-15 ADA', style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context))),`
- L2115: `_HypoStep('3', 'Remesurer', 'Si toujours < 70 mg/dL, répétez le cycle'),`
- L2277: `final String userUnit; // 'mg/dL' or 'mmol/L' — for display only; we always return mg/dL`
- L2294: `initial = widget.userUnit == 'mmol/L'`
- L2320: `mgdl = widget.userUnit == 'mmol/L' ? parsed * 18.0 : parsed;`
- L2322: `// High-confidence OCR — GlucoseOcrShield already output mg/dL`
- L2371: `sub   = 'Valeur trop élevée pour être mesurée (> ~600 mg/dL)';`
- L2375: `sub   = 'Valeur trop basse pour être mesurée (< ~20 mg/dL)';`
- L2458: `widget.userUnit == 'mmol/L'`
- L2479: `Text('Converti depuis mmol/L × 18',`
- L2535: `hintText: widget.userUnit == 'mmol/L' ? 'Ex : 6.5' : 'Ex : 120',`

## `frontend/lib/features/dashboard/widgets/agp_chart.dart`
- L22: `/// [hour] is 0–23.  All glucose values are in mg/dL.`
- L56: `/// Horizontal grid lines (mg/dL values).  Default: ADA clinical targets.`

## `frontend/lib/features/dashboard/widgets/hero_insight.dart`
- L25: `if (tir >= 60) return 'Votre équilibre progresse\xa0— ${tir.round()}% en cible, moyenne ${mean.round()}\xa0mg/dL.';`

## `frontend/lib/features/dashboard/widgets/hero_live.dart`
- L11: `/// Calcule la tendance réelle : delta mg/dL sur 30 min entre les 2 dernières mesures.`

## `frontend/lib/features/dashboard/widgets/kpi_gmi_card.dart`
- L68: `'Moy. ${mean.toStringAsFixed(0)} mg/dL · ${logs.length} mesures · ${daysCount}j',`

## `frontend/lib/features/documents/document_import_screen.dart`
- L532: `'${reading.valueMgdl.toStringAsFixed(0)} mg/dL',`
- L567: `_LabRow(label: 'Glucose à jeun', value: '${values.fastingGlucoseMgdl!.toStringAsFixed(0)} mg/dL'),`
- L569: `_LabRow(label: 'Cholestérol total', value: '${values.totalCholesterolMgdl!.toStringAsFixed(0)} mg/dL'),`
- L571: `_LabRow(label: 'HDL', value: '${values.hdlMgdl!.toStringAsFixed(0)} mg/dL'),`
- L573: `_LabRow(label: 'LDL', value: '${values.ldlMgdl!.toStringAsFixed(0)} mg/dL'),`
- L575: `_LabRow(label: 'Triglycérides', value: '${values.triglyceridesMgdl!.toStringAsFixed(0)} mg/dL'),`

## `frontend/lib/features/journal/ai_summary_screen.dart`
- L567: `Expanded(child: _KpiCard(label: 'TIME IN RANGE', abbr: '${tir.toStringAsFixed(0)}%', value: '${tir.toStringAsFixed(0)}%', color: tirColor, progress: tir / 100, target: '70-180 mg/dL', trend: tir >= 70 ? 1 : -1)),`

## `frontend/lib/features/journal/edit_log_screen.dart`
- L49: `final unit = profile?.unitPreference ?? 'mg/dL';`
- L50: `final displayValue = unit == 'mmol/L' ? log.bloodSugar / 18.0 : log.bloodSugar;`
- L53: `_glucoseController.text = displayValue.toStringAsFixed(unit == 'mmol/L' ? 1 : 0);`
- L67: `final unit = profile?.unitPreference ?? 'mg/dL';`
- L283: `final unit = profile?.unitPreference ?? 'mg/dL';`
- L284: `final bloodSugarMgdl = unit == 'mmol/L' ? _glucoseValue * 18.0 : _glucoseValue;`

## `frontend/lib/features/journal/journal_screen.dart`
- L24: `final unit = profile?.unitPreference ?? 'mg/dL';`

## `frontend/lib/features/journal/widgets/amina_chat_view.dart`
- L68: `/// Language mapping:`
- L69: `///   ar-MA → "ar"  (Darija — nearest TTS locale; Moroccan not available natively)`
- L74: `// Slightly slower rate — easier for medical context + dialect comprehension`
- L81: `// Try to read language from profile; fall back to French`
- L82: `final lang = await _resolveTtsLanguage();`
- L83: `await _tts.setLanguage(lang);`
- L86: `/// Returns the flutter_tts locale string for the patient's preferred language.`
- L88: `/// We check available TTS languages on this device and pick the best match,`
- L89: `/// so we never try to set a locale the engine doesn't support.`
- L90: `Future<String> _resolveTtsLanguage() async {`
- L91: `// Derive language from device locale (set when the user registered the app).`
- L92: `// PatientProfile preferred_language: "fr" → "fr-FR", "ar-MA" / "ar" → "ar".`
- L93: `final locale    = WidgetsBinding.instance.platformDispatcher.locale.toString();`
- L94: `final preferred = locale.startsWith('ar') ? 'ar' : 'fr-FR';`
- L96: `// Verify the locale is actually installed on this device/browser.`
- L98: `final available = await _tts.getLanguages as List<dynamic>? ?? [];`
- L99: `final locales   = available.map((l) => l.toString().toLowerCase()).toList();`
- L101: `if (locales.any((l) => l.startsWith(prefix))) return preferred;`
- L132: `/// Re-configure TTS language just before speaking.`
- L133: `/// [replyLanguage] comes from the backend (backend knows after detect_language).`
- L134: `/// "ar-MA" and "ar" → Arabic TTS locale; anything else → French.`
- L135: `Future<void> _speakReply(String text, {String replyLanguage = 'fr'}) async {`
- L137: `final lang = (replyLanguage == 'ar-MA' || replyLanguage == 'ar') ? 'ar' : 'fr-FR';`
- L138: `await _tts.setLanguage(lang);`
- L394: `await _speakReply(response.reply, replyLanguage: response.replyLanguage);`
- L610: `static bool _isRtl(String text) {`
- L612: `final rtl = RegExp(r'[؀-ۿݐ-ݿ֐-׿ﭐ-﷿ﹰ-﻿]');`
- L613: `final rtlCount = rtl.allMatches(text).length;`
- L614: `return rtlCount > text.length * 0.25;`
- L672: `textDirection: _isRtl(text) ? TextDirection.rtl : TextDirection.ltr,`

## `frontend/lib/features/profile/profile_screen.dart`
- L25: `String _unit = 'mg/dL';`
- L116: `['mg/dL', 'mmol/L'],`
- L117: `['mg/dL', 'mmol/L'],`
- L450: `preferredLanguage: const drift.Value('fr'),`

## `frontend/lib/l10n/app_localizations.dart`
- L18: `/// `localizationDelegates` list, and the locales they support in the app's`
- L19: `/// `supportedLocales` list. For example:`
- L26: `///   supportedLocales: AppLocalizations.supportedLocales,`
- L49: `/// locales, in an Info.plist file that is built into the application bundle.`
- L50: `/// To configure the locales supported by your app, you’ll need to edit this`
- L61: `/// locale your application supports, add a new item and select the locale`
- L63: `/// be consistent with the languages listed in the AppLocalizations.supportedLocales`
- L66: `AppLocalizations(String locale)`
- L67: `: localeName = intl.Intl.canonicalizedLocale(locale.toString());`
- L69: `final String localeName;`
- L96: `/// A list of this localizations delegate's supported locales.`
- L97: `static const List<Locale> supportedLocales = <Locale>[`
- L98: `Locale('ar'),`
- L99: `Locale('en'),`
- L100: `Locale('fr'),`
- L472: `/// **'Glucose target (mg/dL)'**`
- L703: `Future<AppLocalizations> load(Locale locale) {`
- L704: `return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));`
- L708: `bool isSupported(Locale locale) =>`
- L709: `<String>['ar', 'en', 'fr'].contains(locale.languageCode);`
- L715: `AppLocalizations lookupAppLocalizations(Locale locale) {`
- L716: `// Lookup logic when only language code is specified.`
- L717: `switch (locale.languageCode) {`
- L727: `'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '`

## `frontend/lib/l10n/app_localizations_ar.dart`
- L9: `AppLocalizationsAr([String locale = 'ar']) : super(locale);`
- L199: `String get glucoseTarget => 'الهدف الجلوكوزي (mg/dL)';`

## `frontend/lib/l10n/app_localizations_en.dart`
- L9: `AppLocalizationsEn([String locale = 'en']) : super(locale);`
- L197: `String get glucoseTarget => 'Glucose target (mg/dL)';`

## `frontend/lib/l10n/app_localizations_fr.dart`
- L9: `AppLocalizationsFr([String locale = 'fr']) : super(locale);`
- L198: `String get glucoseTarget => 'Cible glycémique (mg/dL)';`

## `frontend/lib/main.dart`
- L136: `supportedLocales: const [`
- L137: `Locale('fr'),`
- L138: `Locale('ar', 'MA'),`

## `frontend/test/features/auth/consent_screen_test.dart`
- L78: `supportedLocales: const [Locale('fr'), Locale('ar', 'MA')],`

## `frontend/test/features/chat/amina_chat_view_test.dart`
- L20: `if (call.method == 'getLanguages') return <dynamic>['fr-FR', 'ar'];`

## `frontend/test/services/consent_service_test.dart`
- L18: `preferredLanguage: const drift.Value('fr'),`

