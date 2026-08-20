from django.conf import settings


def test_cost_logger_is_explicit_info_console_without_global_verbosity_change():
    config = settings.LOGGING

    assert config["disable_existing_loggers"] is False
    assert config["loggers"]["iamina.cost"] == {
        "handlers": ["iamina_cost_console"],
        "level": "INFO",
        "propagate": False,
    }
    assert config["handlers"]["iamina_cost_console"] == {
        "class": "logging.StreamHandler",
        "level": "INFO",
    }
    assert "root" not in config
