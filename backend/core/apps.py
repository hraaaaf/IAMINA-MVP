from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Cross-cutting concerns that don't belong in the tracking app:
    audit log, future Firebase bridge, payments, global middleware.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
