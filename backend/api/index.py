"""D1-6 Preview entrypoint: refuses ANY non-preview or non-lab deployment.

This file exists ONLY on the unmerged research/d1-6-safari-preview branch.
No fallback to the clinical URLconf is allowed.
"""
import os

EXPECTED_BRANCH = "research/d1-6-safari-preview-20261113"
EXPECTED_PROJECT = "prj_tdWQOog3nBiicFGfa1hq2jua2viv"

if (
    os.environ.get("VERCEL") != "1"
    or os.environ.get("VERCEL_ENV") != "preview"
    or os.environ.get("VERCEL_GIT_COMMIT_REF") != EXPECTED_BRANCH
    or os.environ.get("VERCEL_PROJECT_ID") != EXPECTED_PROJECT
    or os.environ.get("IAMINA_D1_SAFARI_LAB_ONLY") != "synthetic-preview-v1"
):
    raise RuntimeError("D1_PREVIEW_DEPLOYMENT_NOT_AUTHORIZED")

os.environ["DJANGO_SETTINGS_MODULE"] = "d1_safari_preview.settings"
from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
