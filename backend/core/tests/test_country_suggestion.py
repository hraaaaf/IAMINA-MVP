from types import SimpleNamespace

from core.api.v1.country_suggestion import country_suggestion, suggested_country_code

def test_ip_country_on_vercel_is_only_optional_suggestion(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    result = country_suggestion(SimpleNamespace(headers={"x-vercel-ip-country": "MA"}))
    assert result == {"country_code": "MA", "source": "ip_estimate"}
    assert "raw_ip" not in result

def test_no_location_offline_or_without_vercel(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    result = country_suggestion(SimpleNamespace(headers={"x-vercel-ip-country": "MA"}))
    assert result == {"country_code": None, "source": "unavailable"}
    for value in (None, "", "ZZ", "FR,MA", "3", "MA\n"):
        assert suggested_country_code(vercel=True, header=value) is None

def test_country_header_never_determines_clinical_eligibility():
    assert suggested_country_code(vercel=True, header="FR") == "FR"
    assert suggested_country_code(vercel=False, header="FR") is None
