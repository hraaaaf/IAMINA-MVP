"""
WSGI config for the amina project.
"""
import os

from django.core.wsgi import get_wsgi_application

if os.environ.get("VERCEL") == "1":
    if os.environ.get("DJANGO_SETTINGS_MODULE") == "d1_safari_preview.settings":
        # Branch-only: do not permit this lab on production or another project.
        if not (
            os.environ.get("VERCEL_ENV") == "preview"
            and os.environ.get("VERCEL_PROJECT_ID") == "prj_tdWQOog3nBiicFGfa1hq2jua2viv"
            and os.environ.get("VERCEL_GIT_COMMIT_REF") == "research/d1-6-safari-preview-20261113"
            and os.environ.get("IAMINA_D1_SAFARI_LAB_ONLY") == "synthetic-preview-v1"
        ):
            raise RuntimeError("D1_PREVIEW_WSGI_DEPLOYMENT_DENIED")
    else:
        os.environ["DJANGO_SETTINGS_MODULE"] = "amina.vercel_settings"
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")

application = get_wsgi_application()
