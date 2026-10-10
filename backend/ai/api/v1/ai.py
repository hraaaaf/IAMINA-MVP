"""
AI endpoints — ai/ app (engine-shaped routes)
==============================================
Migrated from diabetes/api/v1/ai.py in Phase 5 of engine-decomposition.

POST /api/v1/ai/summary              — Deterministic local clinical observations (no LLM)
POST /api/v1/ai/chat                 — Contextual conversation with English Pivot Layer
GET  /api/v1/ai/doctor-brief         — Deterministic local recorded-data summary
POST /api/v1/ai/analyze-meal-image   — Gemini Vision meal recognition
POST /api/v1/ai/analyze-glucometer-image — Gemini Vision glucometer OCR (web fallback)
POST /api/v1/ai/chat/stream          — SSE streaming chat

Architecture (Analytical-First):
  1. SQL KPIs computed by sql_analytics.compute_kpis() — no Python arithmetic.
  2. Pattern detection by clinical engine rule detectors.
  3. SemanticCompressor converts KPIs + patterns → English pivot text.
  4. LLM (Groq GPT-OSS-120B) formats the governed pivot response in patient language.
  5. TriageVitalMiddleware (upstream) has already intercepted any emergency messages.
  6. UnitGuardMiddleware (upstream) has already normalised all glucose values.
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import List, Optional

from django.db.models import Q
from django.http import StreamingHttpResponse
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from core.ai_egress import IMAGE, TEXT, ai_egress_scope, patient_ai_egress_scope
from core.ai_processor_policy import AIProcessorPolicyDenied
from core.input_safety import INSULIN_BLOCK, PRESCRIPTION_BLOCK, evaluate_input_safety
from core.locale import resolve_patient_locale
from core.models import BasePatientProfile
from core.observability import EVT_CHAT_MESSAGE, EVT_SUMMARY_VIEWED, track
from diabetes.models import LogEntry
from diabetes.services.clinical.engine import run_clinical_analysis
from diabetes.services.clinical.evidence_projection import project_public_kpis
from diabetes.services.clinical.semantic_compressor import build_chat_context
from diabetes.services.clinical.sql_analytics import (
    compute_agp_profile,
    compute_daily_averages,
    compute_kpis,
)

logger = logging.getLogger(__name__)
router = Router(tags=["ai"])


# ──────────────────────────────────────────────────────────────
# 1. SCHEMAS
# ──────────────────────────────────────────────────────────────


class SummaryRequest(BaseModel):
    days: int = 21
    target_low: float = 70.0
    target_high: float = 180.0


class DoctorBriefResponse(BaseModel):
    doctor_brief: str
    narrative: str
    key_insight: str
    days: int
    generated_at: str
    has_sufficient_data: bool


class KPISchema(BaseModel):
    avg_glucose: Optional[float]
    std_dev: Optional[float]
    cv_pct: Optional[float]
    tir_pct: Optional[float]
    tar_pct: Optional[float]
    tbr_pct: Optional[float]
    gmi: Optional[float]
    log_count: int
    days_with_data: int
    gmi_confidence: Optional[str] = None  # "high" | "medium" | "low" | null
    gmi_basis: str = ""  # e.g. "47 mesures · 15j"


class InsightSchema(BaseModel):
    code: str
    priority: int
    icon: str
    title: str
    content: str
    action: str


class SummaryResponse(BaseModel):
    kpis: KPISchema
    insights: List[InsightSchema]
    daily_averages: List[dict]
    generated_at: str
    has_sufficient_data: bool
    # "fallback" for deterministic local-only narration; no external LLM call.
    # Lets Flutter distinguish the locally generated summary from remote AI.
    ai_provider: str = "groq"


class ChatRequest(BaseModel):
    message: str
    context_days: int = 14  # Look-back window for clinical context


class ChatResponse(BaseModel):
    reply: str
    response_mode: str = "standard"
    conversation_id: str
    timestamp: str
    is_emergency: bool = False
    reply_language: str = "fr"


class MealImageRequest(BaseModel):
    """Phase 11-C: meal photo sent as base64-encoded image."""

    image_base64: str
    mime_type: str = "image/jpeg"


class MealImageResponse(BaseModel):
    """
    Phase 11-C: list of identified French food names + confidence level.
    fallback=True means the LLM could not identify foods — UI shows a manual fallback.
    """

    foods: List[str]
    confidence: str  # "high" | "medium" | "low"
    fallback: bool


class GlucometerOcrResponse(BaseModel):
    """Phase 11-D: glucose value extracted from a glucometer photo (web OCR fallback)."""

    value: Optional[float]  # glucose reading; None if not detected
    unit: str  # "mg/dL" | "mmol/L"
    confidence: str  # "high" | "medium" | "low"
    fallback: bool  # True when value could not be extracted


# ──────────────────────────────────────────────────────────────
# 2. SUMMARY ENDPOINT
# ──────────────────────────────────────────────────────────────


@router.post("/ai/summary", response=SummaryResponse)
@patient_ai_egress_scope("clinical_summary", TEXT)
def get_summary(request, data: SummaryRequest):
    """
    Full Phase 6 analytical pipeline.

    Step 1: SQL computes all KPIs (never Python arithmetic).
    Step 2: Pattern detection engine runs against ORM queryset.
    Step 3: Local, deterministic presentation of evidence-qualified patterns.
    No third-party model sees patient observations or measurements.
    """
    user = request.user
    patient_language = _get_patient_language(user)

    # ── Step 1: SQL KPIs ──
    kpis = compute_kpis(
        patient_id=user.id,
        days=data.days,
        target_low=data.target_low,
        target_high=data.target_high,
    )

    # CGM row provenance is not verified wear-time; patient fields must be governed.
    public_kpis = project_public_kpis(kpis)

    # ── Step 2: Pattern detection (requires ORM entries for time-aware rules) ──
    since = timezone.now() - timedelta(days=data.days)
    entries = list(
        LogEntry.objects.filter(
            Q(logged_at__gte=since) | Q(logged_at__isnull=True, created_at__gte=since),
            patient=user,
            blood_sugar__isnull=False,
            blood_sugar__gt=0,
        ).order_by("logged_at", "created_at")
    )
    report = run_clinical_analysis(entries, kpis, language=patient_language)

    # ── Step 3: Use the local clinical engine output exactly once ──
    # V1-03: no prompt is built or passed to a model for this patient summary.
    insights = report.insights

    # ── Step 5: AGP 24h profile + daily averages for Flutter chart ──
    agp_profile = compute_agp_profile(user.id, data.days)
    daily_avgs = compute_daily_averages(user.id, data.days)

    track(EVT_SUMMARY_VIEWED, patient_id=user.id, props={"days": data.days})

    return {
        "kpis": {
            "avg_glucose": public_kpis["avg_glucose"],
            "std_dev": public_kpis["std_dev"],
            "cv_pct": public_kpis["cv_pct"],
            "tir_pct": public_kpis["tir_pct"],
            "tar_pct": public_kpis["tar_pct"],
            "tbr_pct": public_kpis["tbr_pct"],
            "gmi": public_kpis["gmi"],
            "log_count": public_kpis["log_count"],
            "days_with_data": public_kpis["days_with_data"],
            "gmi_confidence": public_kpis["gmi_confidence"],
            "gmi_basis": public_kpis["gmi_basis"],
        },
        "insights": insights,
        "daily_averages": daily_avgs,
        "agp_profile": agp_profile,
        "generated_at": timezone.now().isoformat(),
        "has_sufficient_data": kpis.has_sufficient_data,
        "ai_provider": "fallback",  # Honest local-only narration status.
    }


# ──────────────────────────────────────────────────────────────
# 2b. DOCTOR BRIEF ENDPOINT
# ──────────────────────────────────────────────────────────────


@router.get("/ai/doctor-brief", response=DoctorBriefResponse)
def get_doctor_brief(request, days: int = 14):
    """Bounded local consultation-preparation description; never invoke an LLM.

    No verified CGM interpretation, cause, prognosis, diagnosis or dose advice
    is available from raw recorded glucose rows. No third-party egress scope
    is needed because the full response stays in the authenticated backend.
    The localized wording requires specialist review before patient release.
    """
    from diabetes.services.clinical.doctor_brief_local import build_local_doctor_brief
    from diabetes.services.clinical.sql_analytics import compute_kpis

    user = request.user
    kpis = compute_kpis(patient_id=user.id, days=days)
    local = build_local_doctor_brief(
        kpis, days=days, language=_get_patient_language(user)
    )
    return {
        **local,
        "days": days,
        "generated_at": timezone.now().isoformat(),
        "has_sufficient_data": kpis.has_sufficient_data,
    }


# ──────────────────────────────────────────────────────────────
# 3. CHAT ENDPOINT
# ──────────────────────────────────────────────────────────────


@router.post("/ai/chat", response=ChatResponse)
@patient_ai_egress_scope("companion_chat", TEXT)
def chat_with_amina(request, data: ChatRequest):
    """
    Phase 6 chat with English Pivot Layer.

    Note: TriageVitalMiddleware has already screened 'data.message' upstream.
    If this view is reached, the message is NOT a medical emergency.

    Steps:
      1. Fetch minimal KPIs for context (SQL, lightweight).
      2. Compress into English pivot chat context.
      3. Build English system prompt + FR/Darija user message.
      4. Call LLM → respond in patient language.
    """
    user = request.user
    language = _get_patient_language(user)

    from companion.conversation import detect_language, is_governance_blocked_reply

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
        iamina = IAmina(user, language)
        reply = iamina.chat(data.message, context_days=data.context_days)
    except Exception:
        logger.exception("chat_with_amina: unhandled error for user=%s", user.id)
        reply = "Désolé, une erreur inattendue s'est produite. Réessaie dans quelques instants."
    reply_language = detect_language(data.message, language)
    track(EVT_CHAT_MESSAGE, patient_id=user.id, props={"context_days": data.context_days})

    return {
        "reply": reply,
        "response_mode": (
            "governance_fallback"
            if is_governance_blocked_reply(reply, data.message, language)
            else "standard"
        ),
        "conversation_id": f"conv-{user.id}",
        "timestamp": timezone.now().isoformat(),
        "is_emergency": False,
        "reply_language": reply_language,
    }


# ──────────────────────────────────────────────────────────────
# 3b. MEAL PHOTO RECOGNITION (Phase 11-C)
# ──────────────────────────────────────────────────────────────


@router.post("/ai/analyze-glucometer-image", response=GlucometerOcrResponse)
@patient_ai_egress_scope("glucometer_ocr", IMAGE)
def analyze_glucometer_image_web(request, data: MealImageRequest):
    """
    Phase 11-D — Gemini Vision glucometer OCR for web clients.

    POST /api/v1/ai/analyze-glucometer-image
    Body: { "image_base64": "<base64>", "mime_type": "image/jpeg" }

    Mobile uses on-device ML Kit (offline, faster).
    Web uses this endpoint as fallback.
    """
    from media.vision import MealVisionShield
    from media.vision import analyze_glucometer_image as _analyze_gluco

    error = MealVisionShield.validate_input(data.image_base64, data.mime_type)
    if error:
        logger.warning("analyze_glucometer_image: input rejected — %s", error)
        return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}

    try:
        return _analyze_gluco(data.image_base64, data.mime_type)
    except AIProcessorPolicyDenied:
        # Cloud image analysis is intentionally disabled for V1-03.
        # Preserve the manual glucometer-entry path without claiming OCR success.
        return {"value": None, "unit": "mg/dL", "confidence": "low", "fallback": True}


@router.post("/ai/analyze-meal-image", response=MealImageResponse)
@patient_ai_egress_scope("meal_vision", IMAGE)
def analyze_meal_image(request, data: MealImageRequest):
    """
    Phase 11-C — Gemini Vision meal recognition.

    POST /api/v1/ai/analyze-meal-image
    Body: { "image_base64": "<base64>", "mime_type": "image/jpeg" }

    Pipeline:
      1. MealVisionShield validates input (mime type, size, base64 sanity).
      2. Gemini Vision identifies visible foods (English Pivot prompt).
      3. MealVisionShield sanitises output (max 8 French food names).
      4. Flutter maps returned names to CulinaryItem chips (fuzzy match).

    No patient clinical data is sent to the LLM — only the food image.
    fallback=True in the response means Flutter must ask the user to pick manually.
    """
    from media.vision import MealVisionShield
    from media.vision import analyze_meal_image as _analyze

    error = MealVisionShield.validate_input(data.image_base64, data.mime_type)
    if error:
        # Return graceful fallback with the error embedded in foods list
        # (400 would break the Flutter error handling — use fallback instead)
        logger.warning("analyze_meal_image: input rejected — %s", error)
        return {"foods": [], "confidence": "low", "fallback": True}

    try:
        return _analyze(data.image_base64, data.mime_type)
    except AIProcessorPolicyDenied:
        # Do not turn expected privacy-policy refusal into a server error.
        return {"foods": [], "confidence": "low", "fallback": True}


# ──────────────────────────────────────────────────────────────
# 3c. STREAMING CHAT ENDPOINT (SSE)
# ──────────────────────────────────────────────────────────────


@router.post("/ai/chat/stream")
@patient_ai_egress_scope("companion_chat", TEXT)
def chat_stream(request, data: ChatRequest):
    """
    POST /api/v1/ai/chat/stream — JSON body with message and context_days.
    Returns Server-Sent Events — one `data:` line per token chunk.
    Terminal event: `data: [DONE]`
    """
    # Django-Ninja may select an earlier auth callback before SessionAuth.
    # A browser session cookie must therefore never bypass CSRF on this
    # sensitive streaming POST, even with a spoofed Authorization header.
    from django.conf import settings
    from ninja.errors import HttpError

    if request.COOKIES.get(settings.SESSION_COOKIE_NAME):
        from amina.vercel_session_auth import check_iamina_csrf

        if check_iamina_csrf(request):
            raise HttpError(403, "CSRF check Failed")

    message = data.message
    context_days = data.context_days
    from core.input_safety import (
        INSULIN_BLOCK,
        PRESCRIPTION_BLOCK,
        URGENT,
        evaluate_input_safety,
    )

    decision = evaluate_input_safety(message)
    user = request.user
    language = _get_patient_language(user)
    track(
        EVT_CHAT_MESSAGE, patient_id=user.id, props={"stream": True, "context_days": context_days}
    )

    if decision.action == URGENT:

        def _urgent_event_generator():
            emergency_msg = (
                "⚠️ Alerte : Votre glycémie semble être dans une zone critique. "
                "Veuillez suivre les protocoles d'urgence ou contacter votre médecin."
            )
            yield f"data: {json.dumps({'token': emergency_msg})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingHttpResponse(
            _urgent_event_generator(),
            content_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    if decision.action in (INSULIN_BLOCK, PRESCRIPTION_BLOCK):

        def _insulin_event_generator():
            from core.medical_safety import no_prescription_message

            refusal = no_prescription_message(language)
            yield f"data: {json.dumps({'token': refusal})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingHttpResponse(
            _insulin_event_generator(),
            content_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    # Fetch entries only for the urgency glucose check in the router
    since = timezone.now() - timedelta(days=context_days)
    entries = list(
        LogEntry.objects.filter(
            Q(logged_at__gte=since) | Q(logged_at__isnull=True, created_at__gte=since),
            patient=user,
            blood_sugar__isnull=False,
        ).order_by("logged_at", "created_at")
    )

    def _event_generator():
        try:
            from companion.core import IAmina
            from companion.router import route

            # Step 1: Route the user input
            latest_glucose = entries[-1].blood_sugar if entries else None
            route(message, latest_glucose=float(latest_glucose) if latest_glucose else None)

            # Step 3: Real streaming with sentence-level tail-hold.
            import re as _re

            from companion.advice_filter import contains_medical_advice

            _SENT_BOUNDARY = _re.compile(r"(?<=[.!?؟])\s+")

            sentence_buf = ""

            iamina = None

            def _lazy_stream(msg, ctx_days):
                nonlocal iamina
                iamina = IAmina(user, language)
                yield from iamina.stream_chat(msg, context_days=ctx_days)

            def _flush_sentence(s: str) -> bool:
                s = s.strip()
                if not s:
                    return False
                if contains_medical_advice(s) and iamina.deep.advice_given_within(24):
                    return False
                if contains_medical_advice(s):
                    iamina.deep.record_advice_given()
                    iamina.deep.save()
                return True

            for chunk in _lazy_stream(message, context_days):
                sentence_buf += chunk
                parts = _SENT_BOUNDARY.split(sentence_buf)
                if len(parts) > 1:
                    for sentence in parts[:-1]:
                        if _flush_sentence(sentence):
                            yield f"data: {json.dumps({'token': sentence + ' '})}\n\n"
                    sentence_buf = parts[-1]

            # Flush remaining tail
            if iamina is not None and _flush_sentence(sentence_buf):
                yield f"data: {json.dumps({'token': sentence_buf})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as exc:
            # Avoid exception messages and tracebacks potentially containing PHI.
            logger.error("SSE chat stream failed safely: %s", type(exc).__name__)
            yield f"data: {json.dumps({'token': 'Une erreur est survenue.'})}\n\n"
            yield "data: [DONE]\n\n"

    def _scoped_event_generator():
        """Scope each deferred next() independently, resetting before yielding SSE.

        A scope held across yield would risk cross-patient ContextVar inheritance
        when separately streaming requests are interleaved on the same worker.
        """
        stream = _event_generator()
        try:
            while True:
                with ai_egress_scope(user.id, "companion_chat", TEXT):
                    try:
                        event = next(stream)
                    except StopIteration:
                        return
                yield event
        finally:
            with ai_egress_scope(user.id, "companion_chat", TEXT):
                stream.close()

    return StreamingHttpResponse(
        _scoped_event_generator(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────────────────────
# 4. LLM HELPERS
# ──────────────────────────────────────────────────────────────


def _build_iamina_system_prompt(user, kpis, report, language: str) -> str:
    """System prompt for SSE streaming using new IAmina prompt architecture."""
    from companion.memory import IAminaMemory
    from companion.prompts import SYSTEM_BASE, get_language_label
    from companion.tone import get_tone_instruction, select_tone
    from diabetes.models import AIChatMessage

    IAminaMemory.load(user)
    tone_ctx = select_tone(tir_pct=kpis.tir_pct, cv_pct=kpis.cv_pct)
    tone_instruction = get_tone_instruction(tone_ctx)

    history_qs = AIChatMessage.objects.filter(patient=user).order_by("-created_at")[:6]
    history_text = "\n".join(f"{m.role}: {m.message}" for m in reversed(list(history_qs))) or ""
    pivot = build_chat_context(kpis, report.patterns)

    system = SYSTEM_BASE.format(language=get_language_label(language), tone=tone_ctx.mode.value)
    system += "\n" + tone_instruction
    if history_text:
        system += f"\n\n[HISTORY]\n{history_text}"
    if pivot:
        system += f"\n\n[CLINICAL_CONTEXT]\n{pivot}"
    return system


def _call_llm_for_summary(pivot_text: str, patterns, language: str = "fr") -> list[dict]:
    """Legacy compatibility helper: format locally, never forward patient pivot."""
    from diabetes.services.clinical.engine import _format_fallback

    del pivot_text
    return _format_fallback(patterns, language)


# ──────────────────────────────────────────────────────────────
# 5. UTILITY HELPERS
# ──────────────────────────────────────────────────────────────


def _get_patient_language(user) -> str:
    try:
        base = BasePatientProfile.objects.get(patient=user)
    except BasePatientProfile.DoesNotExist:
        return "fr"
    resolved = resolve_patient_locale(base)
    return resolved.dialect or resolved.response_language


def _get_patient_name(user) -> str:
    return user.get_full_name() or user.username or "Patient"
