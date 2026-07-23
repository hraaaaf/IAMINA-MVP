"""
URL configuration for the amina project.
"""
from django.conf import settings
from django.urls import path

from diabetes.api.main import api

urlpatterns = [
    path('api/', api.urls),
]

if settings.ENABLE_DJANGO_ADMIN:
    from django.contrib import admin
    urlpatterns.insert(0, path('admin/', admin.site.urls))
