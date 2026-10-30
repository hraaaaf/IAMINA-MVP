"""
Demo scenarios endpoint — Pre-configured patient data for testing.
GET  /api/v1/demo/scenarios — Returns 8 demo scenarios (A–H)
POST /api/v1/demo/chat      — Production IAmina runtime over synthetic patient data
POST /api/v1/demo/seed      — Disabled: rejects patient-context demo injection
"""

import hashlib
from datetime import UTC, datetime
from typing import List

from django.db import transaction
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, Field

from core.models import AIUserThrottleWindow
from diabetes.api.v1.security import firebase_auth_backend
from diabetes.services.demo_runtime import reply_with_synthetic_patient

router = Router(tags=["demo"])

_DEMO_CHAT_WINDOW_SECONDS = 60
_DEMO_CHAT_MAX_REQUESTS = 10


def _authorize_demo_chat_request(request) -> str:
    raw = request.META.get("REMOTE_ADDR", "unknown")
    subject = hashlib.sha256(f"iamina-demo|{raw}".encode()).hexdigest()
    now = timezone.now()
    epoch = int(now.timestamp())
    window_epoch = epoch - (epoch % _DEMO_CHAT_WINDOW_SECONDS)
    window_start = datetime.fromtimestamp(window_epoch, tz=UTC)

    with transaction.atomic():
        row, _ = AIUserThrottleWindow.objects.get_or_create(
            subject_key=f"demo:{subject[:59]}",
            window_start=window_start,
            defaults={"request_count": 0},
        )
        row = AIUserThrottleWindow.objects.select_for_update().get(pk=row.pk)
        if row.request_count >= _DEMO_CHAT_MAX_REQUESTS:
            raise HttpError(429, "Demo chat rate limit exceeded")
        row.request_count += 1
        row.save(update_fields=("request_count", "updated_at"))
    return subject


class DemoScenarioResponse(BaseModel):
    id: str
    name: str
    description: str


class DemoChatHistoryTurn(BaseModel):
    role: str
    content: str


class DemoChatRequest(BaseModel):
    message: str
    language: str = "fr"
    session_id: str = ""
    history: List[DemoChatHistoryTurn] = Field(default_factory=list)


class DemoChatResponse(BaseModel):
    reply: str
    conversation_id: str
    timestamp: str
    is_emergency: bool = False
    reply_language: str = "fr"


class SeedResponse(BaseModel):
    created: int
    message: str


@router.get("/demo/scenarios", response=List[DemoScenarioResponse])
def list_demo_scenarios(request):
    scenarios = [
        {"id": "A", "name": "Type 1 — Hyperglycemia Risk",       "description": "Patient with postprandial spikes after high-carb meals"},
        {"id": "B", "name": "Type 2 — Stable Control",           "description": "Patient with well-controlled glucose levels"},
        {"id": "C", "name": "Type 1 — Dawn Phenomenon",          "description": "Patient with early morning spikes"},
        {"id": "D", "name": "Gestational — Fasting Hyperglycemia","description": "Pregnant patient with fasting glucose >105 mg/dL"},
        {"id": "E", "name": "Type 2 — Nocturnal Hypoglycemia",   "description": "Patient with nighttime lows after evening exercise"},
        {"id": "F", "name": "Type 1 — Stress-Induced Spikes",    "description": "Patient showing glucose correlation with stress events"},
        {"id": "G", "name": "Prediabetes — Prevention",          "description": "Pre-diabetic patient with lifestyle recommendations"},
        {"id": "H", "name": "Type 1 — Hypomania Behavior",       "description": "Patient with inconsistent logging & missed insulin"},
    ]
    return scenarios


@router.post("/demo/chat", response=DemoChatResponse)
def demo_chat(request, data: DemoChatRequest):
    """Public demo using the application runtime with synthetic logs."""
    subject = _authorize_demo_chat_request(request)
    message = data.message.strip()
    if not message:
        raise HttpError(400, "Demo message must not be empty")
    if len(message) > 1000:
        raise HttpError(400, "Demo message exceeds 1000 characters")
    session_id = data.session_id.strip()
    if len(session_id) > 128:
        raise HttpError(400, "Demo session id exceeds 128 characters")
    if len(data.history) > 20:
        raise HttpError(400, "Demo history exceeds 20 turns")

    history = [
        {"role": turn.role.strip(), "content": turn.content.strip()}
        for turn in data.history
    ]
    if sum(len(turn["content"]) for turn in history) > 6000:
        raise HttpError(400, "Demo history exceeds total size limit")

    del history
    session_subject = f"{subject}|{session_id}" if session_id else subject
    return reply_with_synthetic_patient(
        message,
        language=data.language,
        subject_key=session_subject,
    )


@router.post("/demo/seed", auth=firebase_auth_backend, response=SeedResponse)
def seed_demo_data(request):
    """D11: a real patient token must NEVER authorize synthetic clinical writes.

    This API used to inject 30 days of fabricated readings under request.user.
    Authentication is not consent to create medical history, and neither a
    "dev only" comment nor a Django DEBUG flag protects a patient record.

    Demo datasets remain available through the dedicated setup_demo management
    command and the isolated /demo/chat synthetic runtime. HTTP seeding stays
    disabled for *all* patient identities, including the demo fixture user.
    Preserve this route as an explicit 403 (rather than an accidental 404)
    so clients fail closed without mutating historical patient records.
    """
    raise HttpError(403, "Clinical demo seeding is disabled for patient accounts")
