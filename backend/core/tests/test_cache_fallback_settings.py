from django.conf import settings


def test_cache_backend_matches_synthetic_no_redis_mode():
    backend = settings.CACHES["default"]["BACKEND"]
    if getattr(settings, "IAMINA_NO_REDIS", False):
        assert backend == "django.core.cache.backends.locmem.LocMemCache"
        return
    assert backend == "django_redis.cache.RedisCache"
    options = settings.CACHES["default"]["OPTIONS"]
    assert options["IGNORE_EXCEPTIONS"] is True
    assert 0 < options["SOCKET_CONNECT_TIMEOUT"] <= 2
    assert 0 < options["SOCKET_TIMEOUT"] <= 2
