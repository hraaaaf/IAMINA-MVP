"""D1-6 isolated Safari laboratory UI served ONLY through test URLconf.

Never include this module in production URLs. No patient data, keys, auth
tokens, private session identifiers or envelopes are returned by this view.
"""
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse

_LAB_DIR = Path(settings.BASE_DIR).parent / "frontend" / "web"
_FILES = {
    "": ("d1_safari_signed_prf_lab.html", "text/html; charset=utf-8"),
    "client.js": ("d1_safari_signed_prf_lab.js", "text/javascript; charset=utf-8"),
    "lab.css": ("d1_safari_signed_prf_lab.css", "text/css; charset=utf-8"),
    "bridge.js": ("d1_signed_prf_synthetic_research.js", "text/javascript; charset=utf-8"),
}
_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'none'; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


def safari_lab(request, asset=""):
    if (
        getattr(settings, "D1_PASSKEY_RESEARCH_ENABLED", False) is not True
        or asset not in _FILES
        or not request.user.is_authenticated
        or not request.user.is_active
        or not request.session.session_key
    ):
        return HttpResponse(status=404)
    filename, content_type = _FILES[asset]
    contents = (_LAB_DIR / filename).read_bytes()
    response = HttpResponse(contents, content_type=content_type)
    response["Cache-Control"] = "no-store"
    response["Content-Security-Policy"] = _CSP
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
