import base64

from media.vision import analyze_glucometer_image, analyze_meal_image


class FakeVisionBackend:
    name = "fake-vision"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate(
        self,
        image_b64,
        mime_type,
        *,
        system_prompt,
        user_prompt,
        purpose,
        temperature,
    ):
        self.calls.append(
            {
                "image_b64": image_b64,
                "mime_type": mime_type,
                "purpose": purpose,
                "temperature": temperature,
            }
        )
        return next(self.responses)


def _image() -> str:
    return base64.b64encode(b"synthetic-image-bytes").decode("ascii")


def test_meal_vision_uses_injected_backend_and_keeps_output_shield():
    backend = FakeVisionBackend([
        '{"foods": ["pain", " riz ", "", 7, "salade"]}'
    ])

    result = analyze_meal_image(_image(), "image/jpeg", backend=backend)

    assert result == {
        "foods": ["pain", "riz", "salade"],
        "confidence": "high",
        "fallback": False,
    }
    assert backend.calls[0]["purpose"] == "meal_vision"
    assert backend.calls[0]["temperature"] == 0.1


def test_glucometer_vision_uses_same_provider_boundary_without_semantic_change():
    backend = FakeVisionBackend([
        '{"value": 54, "unit": "mg/dL", "confidence": "high"}'
    ])

    result = analyze_glucometer_image(_image(), "image/png", backend=backend)

    assert result == {
        "value": 54.0,
        "unit": "mg/dL",
        "confidence": "high",
        "fallback": False,
    }
    assert backend.calls[0]["purpose"] == "glucometer_ocr"
    assert backend.calls[0]["temperature"] == 0.0


def test_invalid_media_is_rejected_before_any_backend_invocation():
    backend = FakeVisionBackend([])

    meal = analyze_meal_image("not-base64", "image/jpeg", backend=backend)
    meter = analyze_glucometer_image(_image(), "image/gif", backend=backend)

    assert meal["fallback"] is True
    assert meter["fallback"] is True
    assert backend.calls == []


def test_invalid_backend_payload_fails_closed():
    backend = FakeVisionBackend(["not-json", "{}"])

    meal = analyze_meal_image(_image(), "image/jpeg", backend=backend)
    meter = analyze_glucometer_image(_image(), "image/jpeg", backend=backend)

    assert meal == {"foods": [], "confidence": "low", "fallback": True}
    assert meter == {
        "value": None,
        "unit": "mg/dL",
        "confidence": "low",
        "fallback": True,
    }


def test_glucometer_unknown_or_invalid_unit_never_produces_measured_value():
    # Provider may omit units or derive one from a naked number. Missing or
    # invalid unit must never become a clinically interpretable OCR reading.
    responses = (
        '{"value": 120, "confidence": "high"}',
        '{"value": 6.5, "unit": null, "confidence": "high"}',
        '{"value": 120, "unit": "unknown", "confidence": "high"}',
        '{"value": 120, "unit": "", "confidence": "high"}',
        '{"value": null, "unit": "mg/dL", "confidence": "high"}',
        '{"value": "nan", "unit": "mg/dL", "confidence": "high"}',
        '{"value": true, "unit": "mg/dL", "confidence": "high"}',
        "[]",
    )
    backend = FakeVisionBackend(responses)
    for _ in responses:
        result = analyze_glucometer_image(_image(), "image/jpeg", backend=backend)
        assert result["value"] is None
        assert result["confidence"] == "low"
        assert result["fallback"] is True
    assert len(backend.calls) == len(responses)


def test_glucometer_explicit_units_keep_value_and_correct_unit():
    backend = FakeVisionBackend([
        '{"value": 6.5, "unit": "mmol/L", "confidence": "high"}',
        '{"value": 120, "unit": "mg/dL", "confidence": "medium"}',
    ])
    mmol = analyze_glucometer_image(_image(), "image/jpeg", backend=backend)
    mgdl = analyze_glucometer_image(_image(), "image/jpeg", backend=backend)
    assert mmol == {
        "value": 6.5,
        "unit": "mmol/L",
        "confidence": "high",
        "fallback": False,
    }
    assert mgdl == {
        "value": 120.0,
        "unit": "mg/dL",
        "confidence": "medium",
        "fallback": False,
    }
    assert all(call["purpose"] == "glucometer_ocr" for call in backend.calls)
