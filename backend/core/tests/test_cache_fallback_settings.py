from django.conf import settings


def test_redis_cache_fallback_has_bounded_network_timeouts():
    options = settings.CACHES["default"]["OPTIONS"]

    assert options["IGNORE_EXCEPTIONS"] is True
    assert 0 < options["SOCKET_CONNECT_TIMEOUT"] <= 2
    assert 0 < options["SOCKET_TIMEOUT"] <= 2
