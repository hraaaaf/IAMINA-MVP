"""D1 Safari Preview isolated URLconf: no patient routes."""
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from ninja import NinjaAPI

from amina.vercel_session_auth import SessionAuth
from core.api.v1.d1_passkey_research import router
from d1_safari_preview.views import lab_asset, start_synthetic_session


def csrf_probe(request):
    response = JsonResponse({"csrf_token": get_token(request), "patient_ready": False})
    response["Cache-Control"] = "no-store"
    return response


api = NinjaAPI(urls_namespace="d1_safari_preview_only")
api.add_router("/v1", router, auth=SessionAuth())

urlpatterns = [
    path("csrf/", csrf_probe),
    path("d1-research/safari/", lab_asset),
    path("d1-research/safari/<str:asset>", lab_asset),
    path("d1-research/lab/start", start_synthetic_session),
    path("api/", api.urls),
]
