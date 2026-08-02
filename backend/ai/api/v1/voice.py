"""
Voice chat endpoint — ai/ app (engine-shaped voice routes)
==========================================================
Migrated from diabetes/api/v1/voice.py in Phase 5 of engine-decomposition.

POST /api/v1/ai/voice      — Full voice-to-voice interaction pipeline
POST /api/v1/ai/transcribe — STT-only, no IAmina pipeline

Full pipeline for voice-to-voice interaction:

  ① Receive  multipart audio (Flutter record package)
  ② Validate mime type + file size
  ③ STT      Gemini Audio → transcript
  ④ Triage   detect_vital_distress(transcript)
             (TriageVitalMiddleware can't inspect multipart bodies — we run it manually)
  ⑤ Pipeline IAmina.chat(transcript) — identical to text chat
  ⑥ Respond  {transcript, reply} — Flutter handles TTS locally (free, no server cost)

Cost per 10-sec voice message (Gemini Audio):
  STT  : ~$0.000032   (250 tokens × $0.075/1M)
  Chat : ~$0.000105   (same as text pipeline)
  TTS  : $0.00        (client-side flutter_tts)
  ─────────────────────────────────────────────
  Total: ~$0.000137 / message
"""

from __future__ import annotations

import logging

from django.utils import timezone
from ninja import File, Router
from ninja.files import UploadedFile
from pydantic import BaseModel

from core.ai_egress import AUDIO, TEXT, patient_ai_egress_scope
from core.locale import resolve_patient_locale
from core.models import BasePatientProfile
from diabetes.config.stt_vocabulary import AR_MA_STT_HINTS
from media.voice import (
    MAX_AUDIO_BYTES,
    SUPPORTED_MIME_TYPES,
    TranscriptionError,
    transcribe,
)

logger = logging.getLogger(__name__)
router = Router(tags=["voice"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class VoiceChatResponse(BaseModel):
    transcript: str  # what IAmina heard (shown in Flutter as subtitle)
    reply: str  # IAmina text reply (Flutter reads it via TTS)
    conversation_id: str
    timestamp: str
    is_emergency: bool = False
    reply_language: str = "fr"


class TranscribeResponse(BaseModel):
    transcript: str  # verbatim STT result — no IAmina pipeline
    confidence: str = "medium"  # "high" | "medium" | "low"


# ── MIME normalisation table ──────────────────────────────────────────────────
# Browsers and mobile OS report non-canonical types — map them to canonical ones.

_MIME_ALIASES: dict[str, str] = {
    "audio/m4a": "audio/mp4",
    "audio/x-m4a": "audio/mp4",
    "audio/mp3": "audio/mpeg",
    "audio/x-wav": "audio/wav",
    "audio/x-ogg": "audio/ogg",
    "audio/webm;codecs=opus": "audio/webm",
    "audio/webm;codecs=pcm": "audio/webm",
}

# Error messages — friendly, actionable, in French (will be TTS-read)
_ERROR_REPLIES: dict[str, str] = {
    "audio_too_large": (
        "Le fichier audio est trop grand (10 Mo max). Envoie un message plus court, stp."
    ),
    "unsupported_format": (
        "Ce format audio n'est pas pris en charge. Utilise mp4, m4a, webm ou wav."
    ),
    "transcription_failed": (
        "Je n'ai pas réussi à comprendre le message vocal. "
        "Peux-tu réessayer ou écrire ta question ?"
    ),
    "empty_transcript": ("Je n'ai rien entendu. Vérifie ton micro et réessaie."),
}


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post("/ai/voice", response=VoiceChatResponse)
@patient_ai_egress_scope("voice_chat", AUDIO, TEXT)
def voice_chat(
    request,
    audio: UploadedFile = File(...),
    context_days: int = 14,
):
    """
    POST /api/v1/ai/voice
    Content-Type: multipart/form-data

    Fields:
      audio        — audio file (mp4 / m4a / webm / wav / ogg / mpeg / flac)
      context_days — look-back window for clinical context (default 14)

    Returns:
      transcript   — what IAmina heard (display as subtitle in Flutter)
      reply        — IAmina's text reply (pass to flutter_tts for playback)
      is_emergency — if True, Flutter should display the emergency UI immediately
    """
    user = request.user

    # ① Validate MIME type
    raw_mime = (audio.content_type or "audio/mp4").split(";")[0].strip()
    mime_type = _MIME_ALIASES.get(audio.content_type or "", raw_mime)
    if mime_type not in SUPPORTED_MIME_TYPES:
        return _error(user, "unsupported_format")

    # ② Validate size
    audio_bytes = audio.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return _error(user, "audio_too_large")

    # ③ Get patient language (drives Darija / Fusha STT hint)
    language = _get_language(user)

    # ④ STT — Gemini Audio
    try:
        transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)
    except (TranscriptionError, ValueError) as exc:
        logger.warning("voice_chat: STT failed for user=%s — %s", user.id, exc)
        return _error(user, "transcription_failed")

    if not transcript:
        return _error(user, "empty_transcript")

    # ⑤ Transcript safety. STT is required before intent is known, but blocked
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
    from companion.conversation import detect_language
    from companion.core import IAmina

    iamina = IAmina(user, language)
    reply = iamina.chat(transcript, context_days=context_days)
    reply_language = detect_language(transcript, language)

    logger.info(
        "voice_chat: user=%s lang=%s transcript=%d chars reply=%d chars",
        user.id,
        language,
        len(transcript),
        len(reply),
    )

    return {
        "transcript": transcript,
        "reply": reply,
        "conversation_id": f"conv-{user.id}",
        "timestamp": timezone.now().isoformat(),
        "is_emergency": False,
        "reply_language": reply_language,
    }


# ── Transcribe-only endpoint (no IAmina pipeline) ────────────────────────────


@router.post("/ai/transcribe", response=TranscribeResponse)
@patient_ai_egress_scope("voice_transcription", AUDIO)
def transcribe_audio(
    request,
    audio: UploadedFile = File(...),
):
    """
    POST /api/v1/ai/transcribe
    Content-Type: multipart/form-data

    STT-only — no IAmina pipeline.
    Used for inline dictation on the add-log page (meal note field).

    Returns:
      transcript — verbatim transcription of the audio clip
      confidence — "high" | "medium" | "low" (length heuristic)
    """
    raw_mime = (audio.content_type or "audio/mp4").split(";")[0].strip()
    mime_type = _MIME_ALIASES.get(audio.content_type or "", raw_mime)
    if mime_type not in SUPPORTED_MIME_TYPES:
        return {"transcript": "", "confidence": "low"}

    audio_bytes = audio.read()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return {"transcript": "", "confidence": "low"}

    language = _get_language(request.user)

    try:
        transcript = transcribe(audio_bytes, mime_type, language, language_hints=AR_MA_STT_HINTS)
    except (TranscriptionError, ValueError):
        return {"transcript": "", "confidence": "low"}

    confidence = "high" if len(transcript) > 20 else "medium" if transcript else "low"
    return {"transcript": transcript, "confidence": confidence}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_language(user) -> str:
    try:
        base = BasePatientProfile.objects.get(patient=user)
    except BasePatientProfile.DoesNotExist:
        return "fr"
    resolved = resolve_patient_locale(base)
    return resolved.dialect or resolved.response_language


def _error(user, code: str) -> dict:
    """Graceful degradation — returns an IAmina reply the Flutter TTS can read."""
    return {
        "transcript": "",
        "reply": _ERROR_REPLIES.get(code, "Une erreur est survenue. Réessaie."),
        "conversation_id": f"conv-{user.id}",
        "timestamp": timezone.now().isoformat(),
        "is_emergency": False,
    }
