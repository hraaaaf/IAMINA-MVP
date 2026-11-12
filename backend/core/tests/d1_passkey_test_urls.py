"""Isolated URL configuration for D1 research HTTP FUE ONLY.

NOT imported or mounted in production amina.urls/diabetes.api.main.
"""
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from ninja import NinjaAPI

from amina.vercel_session_auth import SessionAuth
from core.api.v1.d1_passkey_research import router


def csrf_probe(request):
    return JsonResponse({"csrf_token": get_token(request)})


api = NinjaAPI(urls_namespace="d1_research_http_test")
api.add_router("/v1", router, auth=SessionAuth())

urlpatterns = [
    path("csrf/", csrf_probe),
    path("api/", api.urls),
]
