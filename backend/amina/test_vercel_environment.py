from __future__ import annotations

from unittest.mock import patch

from amina.vercel_environment import is_vercel_production


def test_vercel_production_is_detected() -> None:
    with patch.dict("os.environ", {"VERCEL_ENV": "production"}, clear=False):
        assert is_vercel_production() is True


def test_vercel_preview_is_not_production() -> None:
    with patch.dict("os.environ", {"VERCEL_ENV": "preview"}, clear=False):
        assert is_vercel_production() is False


def test_missing_vercel_env_is_not_production() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert is_vercel_production() is False
