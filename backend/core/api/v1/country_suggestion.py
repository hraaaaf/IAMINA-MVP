"""Return optional country suggestion without storing raw visitor IP.

Only Vercel-coarse country is used; never medical/legal eligibility.
"""
import os
import re

from ninja import Router, Schema

router = Router()

class CountrySuggestion(Schema):
    country_code: str | None
    source: str

def suggested_country_code(*, vercel: bool, header: str | None) -> str | None:
    if not vercel or header is None:
        return None
    country = header.upper()
    return country if re.fullmatch(r"[A-Z]{2}", country) and country != "ZZ" else None

@router.get("/country/suggestion", auth=None, tags=["preferences"], response=CountrySuggestion)
def country_suggestion(request):
    """Network-level IP is automatically visible to own API; no third party."""
    code = suggested_country_code(
        vercel=os.environ.get("VERCEL") == "1",
        header=request.headers.get("x-vercel-ip-country"),
    )
    return {"country_code": code, "source": "ip_estimate" if code else "unavailable"}
