from __future__ import annotations

import re
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    file_path.write_text(text.replace(old, new, 1))


def append_once(path: str, marker: str, content: str) -> None:
    file_path = Path(path)
    text = file_path.read_text()
    if marker not in text:
        file_path.write_text(text + content)


# Medical safety: multilingual refusal copy.
replace_once(
    "backend/core/medical_safety.py",
    '''def no_prescription_message(language: str = "fr") -> str:
    if language == "ar-MA":
        return (
            "Ma nqderch nbadel lik traitement, n3ti dosage dial insuline, "
            "wla n9ol tashkhis. Nqder n3awnk tfham l-ma3loumat dyalk "
            "w t7dder as2ila l-tabib."
        )
    return (
        "Je ne peux pas prescrire, modifier une dose d'insuline, arreter un traitement, "
        "ou poser un diagnostic. Je peux t'aider a organiser tes observations "
        "et preparer les bonnes questions pour ton medecin."
    )
''',
    '''def no_prescription_message(language: str = "fr") -> str:
    if language == "ar-MA":
        return (
            "Ma nqderch nbadel lik traitement, n3ti dosage dial insuline, "
            "wla n9ol tashkhis. Nqder n3awnk tfham l-ma3loumat dyalk "
            "w t7dder as2ila l-tabib."
        )
    if language == "ar":
        return (
            "لا يمكنني وصف علاج أو تعديل جرعة الأنسولين أو إيقاف دواء أو تشخيص حالة. "
            "يمكنني مساعدتك في تنظيم ملاحظاتك وتحضير أسئلة لطبيبك."
        )
    if language == "en":
        return (
            "I cannot prescribe treatment, change an insulin dose, stop medication, "
            "or diagnose a condition. I can help organize your observations and "
            "prepare questions for your clinician."
        )
    return (
        "Je ne peux pas prescrire, modifier une dose d'insuline, arreter un traitement, "
        "ou poser un diagnostic. Je peux t'aider a organiser tes observations "
        "et preparer les bonnes questions pour ton medecin."
    )
''',
)

append_once(
    "backend/core/medical_safety.py",
    "def is_treatment_prescription_request",
    r'''

# Additional multilingual output-side prescription patterns. These are defense in
# depth for generated/fallback text; input-side blocking remains authoritative.
_FORBIDDEN_PATTERNS.extend(
    [
        re.compile(
            r"\b(?:increase|decrease|reduce|double|change|adjust|stop)\b.{0,45}"
            r"\b(?:dose|insulin|medication|medicine|treatment)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:take|inject|use)\b.{0,25}\b\d+(?:[.,]\d+)?\s*(?:u|units?)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\brapid[- ]acting insulin\b", re.IGNORECASE),
        re.compile(
            r"(?:زد|زِد|نقص|خفف|ضاعف|أوقف|اوقف).{0,30}"
            r"(?:جرعة|الأنسولين|الانسولين|دواء|العلاج)"
        ),
        re.compile(r"(?:خذ|خد|حقن).{0,20}\d+(?:[.,]\d+)?\s*(?:وحدة|وحدات)"),
        re.compile(
            r"\b(?:zid|n9es|nqes|doubli|hbes|wa9ef)\b.{0,30}"
            r"\b(?:dose|insulin|insuline|dwa|traitement)\b",
            re.IGNORECASE,
        ),
    ]
)

_INSULIN_INPUT_PATTERNS.extend(
    [
        re.compile(
            r"\b(?:how much|how many)\b.{0,30}\b(?:insulin|units?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:what|which)\b.{0,15}\b(?:dose|dosage)\b.{0,25}\binsulin\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\binsulin\b.{0,30}\b(?:dose|dosage|how much|how many)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bshould i\b.{0,30}\b(?:take|inject|increase|decrease|double)\b.{0,30}\binsulin\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bch7al\b.{0,25}\binsulin(?:e)?\b", re.IGNORECASE),
    ]
)

_TREATMENT_INPUT_PATTERNS = [
    re.compile(
        r"\b(?:dois[- ]?je|je dois|est[- ]?ce que je dois|puis[- ]?je)\b.{0,45}"
        r"\b(?:arr[eê]ter|stopper|doubler|augmenter|diminuer|changer|modifier|adapter)\b.{0,45}"
        r"\b(?:traitement|m[ée]dicament|metformine|dose|insuline)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:quelle?|combien)\b.{0,25}\b(?:dose|dosage)\b.{0,35}"
        r"\b(?:m[ée]dicament|metformine|traitement)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprescri(?:s|re|vez|ption)\b.{0,40}"
        r"\b(?:moi|traitement|m[ée]dicament|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bshould i\b.{0,40}\b(?:stop|double|increase|decrease|change|adjust|skip)\b.{0,40}"
        r"\b(?:medication|medicine|treatment|metformin|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:what|which|how much)\b.{0,20}\b(?:dose|dosage)\b.{0,35}"
        r"\b(?:medication|medicine|metformin|treatment)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bprescribe\b.{0,35}\b(?:medication|medicine|treatment|dose)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:هل|واش).{0,20}(?:أوقف|اوقف|نوقف|نحبس|أضاعف|اضاعف|نضاعف|نزيد|ننقص)"
        r".{0,35}(?:الدواء|دواء|العلاج|الجرعة|جرعة)"
    ),
    re.compile(
        r"(?:ما هي|ماهي|شنو|شحال|كم).{0,20}(?:الجرعة|جرعة)"
        r".{0,25}(?:الدواء|دواء|الميتفورمين|متفورمين)"
    ),
    re.compile(
        r"\b(?:wach|wash)\b.{0,25}\b(?:nhbes|hbes|nwa9ef|nzid|n9es|nqes|ndoubli)\b"
        r".{0,35}\b(?:dwa|dose|traitement|metformin|metformine)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:chhal|ch7al)\b.{0,25}\b(?:dose|dwa|metformin|metformine)\b",
        re.IGNORECASE,
    ),
]


def is_treatment_prescription_request(text: str | None) -> bool:
    """Detect requests to prescribe, stop, change or dose a treatment."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _TREATMENT_INPUT_PATTERNS)


def sanitize_patient_visible(value, language: str = "fr"):
    """Recursively apply the no-prescription policy to visible text."""
    if isinstance(value, str):
        return apply_no_prescription_policy(value, language)
    if isinstance(value, list):
        return [sanitize_patient_visible(item, language) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_patient_visible(item, language) for item in value)
    if isinstance(value, dict):
        return {
            key: sanitize_patient_visible(item, language)
            for key, item in value.items()
        }
    return value
''',
)

# Central input safety.
replace_once(
    "backend/core/input_safety.py",
    "from core.medical_safety import is_insulin_prescription_request\n",
    "from core.medical_safety import (\n"
    "    is_insulin_prescription_request,\n"
    "    is_treatment_prescription_request,\n"
    ")\n",
)
replace_once(
    "backend/core/input_safety.py",
    'INSULIN_BLOCK = "INSULIN_BLOCK"\n',
    'INSULIN_BLOCK = "INSULIN_BLOCK"\nPRESCRIPTION_BLOCK = "PRESCRIPTION_BLOCK"\n',
)
replace_once(
    "backend/core/input_safety.py",
    '''    if is_insulin_prescription_request(message):
        return InputSafetyDecision(INSULIN_BLOCK, "insulin_prescription")
    return InputSafetyDecision(ALLOW)
''',
    '''    if is_insulin_prescription_request(message):
        return InputSafetyDecision(INSULIN_BLOCK, "insulin_prescription")
    if is_treatment_prescription_request(message):
        return InputSafetyDecision(PRESCRIPTION_BLOCK, "treatment_prescription")
    return InputSafetyDecision(ALLOW)
''',
)

# Conversation paths.
replace_once(
    "backend/companion/conversation.py",
    "from core.contracts.domain_context import DomainContext\n",
    "from core.contracts.domain_context import DomainContext\n"
    "from core.input_safety import (\n"
    "    INSULIN_BLOCK,\n"
    "    PRESCRIPTION_BLOCK,\n"
    "    URGENT,\n"
    "    evaluate_input_safety,\n"
    ")\n",
)
replace_once(
    "backend/companion/conversation.py",
    "    is_insulin_prescription_request,\n",
    "",
)
replace_once(
    "backend/companion/conversation.py",
    '''    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    if _is_chat_emergency(message):
        _append_turn(patient, "user", message)
        reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR
        _append_turn(patient, "assistant", reply)
        return reply

    if is_insulin_prescription_request(message):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        return reply
''',
    '''    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    decision = evaluate_input_safety(message, language)
    if decision.action == URGENT:
        _append_turn(patient, "user", message)
        reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR
        _append_turn(patient, "assistant", reply)
        return reply

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        return reply
''',
)
replace_once(
    "backend/companion/conversation.py",
    '''    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    if _is_chat_emergency(message):
        _append_turn(patient, "user", message)
        reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR
        _append_turn(patient, "assistant", reply)
        yield reply
        return

    if is_insulin_prescription_request(message):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        yield reply
        return
''',
    '''    # 0. Deterministic safety guards — must run BEFORE any LLM initialization
    decision = evaluate_input_safety(message, language)
    if decision.action == URGENT:
        _append_turn(patient, "user", message)
        reply = _CHAT_EMERGENCY_AR if language == "ar-MA" else _CHAT_EMERGENCY_FR
        _append_turn(patient, "assistant", reply)
        yield reply
        return

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        _append_turn(patient, "user", message)
        reply = no_prescription_message(language)
        _append_turn(patient, "assistant", reply)
        yield reply
        return
''',
)

# API sync, SSE and summaries.
replace_once(
    "backend/ai/api/v1/ai.py",
    "from core.ai_egress import IMAGE, TEXT, assert_ai_egress_allowed, patient_ai_egress_scope\n",
    "from core.ai_egress import IMAGE, TEXT, assert_ai_egress_allowed, patient_ai_egress_scope\n"
    "from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, evaluate_input_safety\n",
)
replace_once(
    "backend/ai/api/v1/ai.py",
    "    insights = _call_llm_for_summary(compressed.full_pivot_text, report.patterns)\n",
    "    from core.medical_safety import sanitize_patient_visible\n\n"
    "    insights = sanitize_patient_visible(\n"
    "        _call_llm_for_summary(compressed.full_pivot_text, report.patterns, patient_language),\n"
    "        patient_language,\n"
    "    )\n",
)
replace_once(
    "backend/ai/api/v1/ai.py",
    '''    from companion.conversation import detect_language
    from companion.core import IAmina
    try:
''',
    '''    from companion.conversation import detect_language

    decision = evaluate_input_safety(data.message, language)
    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        from core.medical_safety import no_prescription_message

        reply_language = detect_language(data.message, language)
        track(
            EVT_CHAT_MESSAGE,
            patient_id=user.id,
            props={"context_days": data.context_days, "blocked": decision.reason},
        )
        return {
            "reply": no_prescription_message(reply_language),
            "conversation_id": f"conv-{user.id}",
            "timestamp": timezone.now().isoformat(),
            "is_emergency": False,
            "reply_language": reply_language,
        }

    from companion.core import IAmina
    try:
''',
)
replace_once(
    "backend/ai/api/v1/ai.py",
    "    from core.input_safety import INSULIN_BLOCK, URGENT, evaluate_input_safety\n",
    "    from core.input_safety import (\n"
    "        INSULIN_BLOCK,\n"
    "        PRESCRIPTION_BLOCK,\n"
    "        URGENT,\n"
    "        evaluate_input_safety,\n"
    "    )\n",
)
replace_once(
    "backend/ai/api/v1/ai.py",
    "    if decision.action == INSULIN_BLOCK:\n",
    "    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):\n",
)
replace_once(
    "backend/ai/api/v1/ai.py",
    'def _call_llm_for_summary(pivot_text: str, patterns) -> list[dict]:\n',
    'def _call_llm_for_summary(\n    pivot_text: str, patterns, language: str = "fr"\n) -> list[dict]:\n',
)
replace_once(
    "backend/ai/api/v1/ai.py",
    "    return _format_with_llm(patterns)\n",
    "    return _format_with_llm(patterns, language)\n",
)

# Voice transcript safety.
replace_once(
    "backend/ai/api/v1/voice.py",
    '''    # ⑤ Triage on transcript (TriageVitalMiddleware can't see multipart bodies)
    from core.middleware.triage_vital import _pick_emergency_response, detect_vital_distress

    if detect_vital_distress(transcript):
        logger.critical(
            "TriageVital(voice): EMERGENCY — user_id=%s | snippet='%s'",
            user.id,
            transcript[:120],
        )
        return {
            **_pick_emergency_response(transcript),
            "transcript": transcript,
            "timestamp": timezone.now().isoformat(),
        }

    # ⑥ IAmina chat pipeline — identical to text chat
''',
    '''    # ⑤ Transcript safety. STT is required before intent is known, but blocked
    # content must not initialize any downstream generative chat LLM.
    from core.input_safety import (
        INSULIN_BLOCK,
        PRESCRIPTION_BLOCK,
        URGENT,
        evaluate_input_safety,
    )
    from core.medical_safety import no_prescription_message
    from core.middleware.triage_vital import _pick_emergency_response

    decision = evaluate_input_safety(transcript, language)
    if decision.action == URGENT:
        logger.critical(
            "TriageVital(voice): EMERGENCY — user_id=%s | snippet='%s'",
            user.id,
            transcript[:120],
        )
        return {
            **_pick_emergency_response(transcript),
            "transcript": transcript,
            "timestamp": timezone.now().isoformat(),
        }
    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):
        return {
            "transcript": transcript,
            "reply": no_prescription_message(language),
            "conversation_id": f"conv-{user.id}",
            "timestamp": timezone.now().isoformat(),
            "is_emergency": False,
            "reply_language": language,
        }

    # ⑥ IAmina chat pipeline — identical to text chat
''',
)

# Clinical engine: sanitize generated and fallback insight structures.
replace_once(
    "backend/diabetes/services/clinical/engine.py",
    "from core.ai_egress import TEXT, assert_ai_egress_allowed\n",
    "from core.ai_egress import TEXT, assert_ai_egress_allowed\n"
    "from core.medical_safety import sanitize_patient_visible\n",
)
replace_once(
    "backend/diabetes/services/clinical/engine.py",
    "    return result if result else _format_fallback(patterns, language)\n",
    "    return sanitize_patient_visible(\n"
    "        result if result else _format_fallback(patterns, language),\n"
    "        language,\n"
    "    )\n",
)
replace_once(
    "backend/diabetes/services/clinical/engine.py",
    '''    return result


# ─────────────────────────────────────────────
# 5. MAIN ENGINE ENTRYPOINT
''',
    '''    return sanitize_patient_visible(result, language)


# ─────────────────────────────────────────────
# 5. MAIN ENGINE ENTRYPOINT
''',
)

# Tests.
Path("backend/core/tests/test_pilot_safety_gate.py").write_text(
    r'''from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from core.input_safety import (
    ALLOW,
    INSULIN_BLOCK,
    PRESCRIPTION_BLOCK,
    evaluate_input_safety,
)
from core.medical_safety import no_prescription_message, sanitize_patient_visible


BLOCKED_CORPUS = (
    ("Quelle dose d'insuline je dois prendre ?", INSULIN_BLOCK),
    ("How much insulin should I inject?", INSULIN_BLOCK),
    ("كم وحدة أنسولين يجب أن آخذ؟", INSULIN_BLOCK),
    ("ch7al insulin nakhod daba?", INSULIN_BLOCK),
    ("Est-ce que je dois doubler mon traitement ?", PRESCRIPTION_BLOCK),
    ("Should I stop my medication tonight?", PRESCRIPTION_BLOCK),
    ("هل أوقف الدواء اليوم؟", PRESCRIPTION_BLOCK),
    ("wach nzid dose dyal dwa?", PRESCRIPTION_BLOCK),
)


@pytest.mark.parametrize(("message", "expected"), BLOCKED_CORPUS)
def test_multilingual_therapeutic_requests_are_blocked(message, expected):
    assert evaluate_input_safety(message).action == expected


@pytest.mark.parametrize(
    "message",
    (
        "C'est quoi l'insuline ?",
        "How should insulin be stored?",
        "ما هو دور الأنسولين؟",
        "chno hiya metformine?",
    ),
)
def test_educational_questions_remain_allowed(message):
    assert evaluate_input_safety(message).action == ALLOW


def test_sync_conversation_block_never_initializes_gateway(monkeypatch):
    from companion import conversation

    monkeypatch.setattr(
        conversation,
        "get_gateway_llm",
        lambda: (_ for _ in ()).throw(AssertionError("gateway initialized")),
    )
    reply = conversation.chat(
        "Should I stop my medication tonight?",
        memory=None,
        deep=None,
        patient=None,
        language="en",
    )
    assert reply == no_prescription_message("en")


def test_stream_conversation_block_never_initializes_gateway(monkeypatch):
    from companion import conversation

    monkeypatch.setattr(
        conversation,
        "get_gateway_llm",
        lambda: (_ for _ in ()).throw(AssertionError("gateway initialized")),
    )
    chunks = list(
        conversation.stream_chat(
            "wach nzid dose dyal dwa?",
            memory=None,
            deep=None,
            patient=None,
            language="ar-MA",
        )
    )
    assert chunks == [no_prescription_message("ar-MA")]


def test_sync_api_block_never_constructs_iamina(monkeypatch):
    from ai.api.v1 import ai

    request = RequestFactory().post("/api/v1/ai/chat")
    request.user = SimpleNamespace(id=7)
    monkeypatch.setattr(ai, "_get_patient_language", lambda user: "en")
    monkeypatch.setattr(ai, "track", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "companion.core.IAmina",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("IAmina initialized")
        ),
    )

    result = ai.chat_with_amina(
        request,
        ai.ChatRequest(
            message="Should I double my medication?",
            context_days=14,
        ),
    )
    assert result["reply"] == no_prescription_message("en")


def test_voice_block_runs_stt_but_never_constructs_iamina(monkeypatch):
    from ai.api.v1 import voice

    request = RequestFactory().post("/api/v1/ai/voice")
    request.user = SimpleNamespace(id=8)
    monkeypatch.setattr(voice, "_get_language", lambda user: "fr")
    monkeypatch.setattr(
        voice,
        "transcribe",
        lambda *args, **kwargs: "Est-ce que je dois doubler mon traitement ?",
    )
    monkeypatch.setattr(
        "companion.core.IAmina",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("IAmina initialized")
        ),
    )
    audio = SimpleUploadedFile(
        "voice.wav",
        b"synthetic-audio",
        content_type="audio/wav",
    )

    result = voice.voice_chat(request, audio=audio)
    assert result["reply"] == no_prescription_message("fr")
    assert result["is_emergency"] is False


def test_recursive_sanitizer_covers_doctor_and_patient_structures():
    unsafe = {
        "narrative": "Continue à noter tes mesures.",
        "doctor_brief": "Augmente ta dose d'insuline ce soir.",
        "insights": [
            {
                "content": "Pattern post-prandial observé.",
                "action": "Take 4 units of rapid-acting insulin.",
            }
        ],
    }
    safe = sanitize_patient_visible(unsafe, "fr")
    assert safe["narrative"] == unsafe["narrative"]
    assert "Je ne peux pas prescrire" in safe["doctor_brief"]
    assert "Je ne peux pas prescrire" in safe["insights"][0]["action"]


def test_ocr_response_contracts_contain_observations_not_treatment_fields():
    from ai.api.v1.ai import GlucometerOcrResponse, MealImageResponse

    assert set(GlucometerOcrResponse.model_fields) == {
        "value",
        "unit",
        "confidence",
        "fallback",
    }
    assert set(MealImageResponse.model_fields) == {
        "foods",
        "confidence",
        "fallback",
    }
'''
)

Path("backend/diabetes/tests/test_pilot_summary_safety.py").write_text(
    r'''import json

from diabetes.services.clinical.engine import (
    ClinicalPattern,
    _format_fallback,
    _parse_insights_json,
)


def _pattern() -> ClinicalPattern:
    return ClinicalPattern(
        code="SYNTHETIC",
        priority=1,
        icon="shield",
        title="Synthetic pattern",
        evidence="Synthetic evidence",
        fallback_content="Observation only.",
        fallback_action="Prends 10 unités avant le repas.",
    )


def test_fallback_summary_action_is_sanitized():
    insights = _format_fallback([_pattern()], "fr")
    assert "Je ne peux pas prescrire" in insights[0]["action"]


def test_llm_formatted_summary_action_is_sanitized():
    payload = json.dumps(
        [
            {
                "code": "SYNTHETIC",
                "title": "Synthetic",
                "content": "Observation only.",
                "action": "Increase your insulin dose tonight.",
            }
        ]
    )
    insights = _parse_insights_json(payload, [_pattern()], "en")
    assert "I cannot prescribe treatment" in insights[0]["action"]
'''
)

Path("docs/architecture/PILOT_SAFETY_CERTIFICATION.md").write_text(
    """# Pilot Safety Certification Contract

## Scope

This gate certifies deterministic refusal and non-bypass behavior for treatment,
prescription and insulin-dose requests before a generative chat LLM is initialized.

## Certified paths

- synchronous patient chat;
- SSE chat;
- voice chat after transcription;
- patient summary insight cards;
- doctor-facing structured text;
- OCR response schemas.

## Voice boundary

Audio transcription necessarily occurs before transcript intent is known. A blocked
transcript may not initialize any downstream generative conversation LLM. This is
reported separately from the STT operation and must not be described as zero total
AI egress.

## Required evidence

1. Multilingual corpus routes to a deterministic refusal.
2. Educational medication questions remain allowed.
3. Blocked sync and streaming requests do not initialize the LLM gateway.
4. Blocked voice transcripts do not initialize IAmina conversation generation.
5. Generated and template summary structures are recursively sanitized.
6. OCR endpoints expose observations only and no treatment recommendation field.
7. SQLite, PostgreSQL, migration drift, Ruff, import-linter, anti-bypass, Bandit,
   OpenAPI, Flutter analyze and secret hygiene are green.

## Non-claims

Automated tests do not replace native-speaker review, clinical approval, emergency
operations approval or processor/privacy approval.
"""
)
