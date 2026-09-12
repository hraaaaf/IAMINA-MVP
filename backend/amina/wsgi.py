"""
WSGI config for the amina project.
"""
import os

from django.core.wsgi import get_wsgi_application

settings_module = "amina.vercel_settings" if os.environ.get("VERCEL") == "1" else "amina.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
