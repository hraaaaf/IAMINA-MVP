from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evaluation.wikimedia_camera_fixture import (
    WikimediaCameraFixtureError,
    materialize_wikimedia_camera_fixture,
)


def _spec(image_bytes: bytes) -> dict[str, str]:
    return {
        "fixture_id": "camera_01",
        "commons_file": "File:Fixture.jpg",
        "expected_commons_sha1": hashlib.sha1(image_bytes).hexdigest(),
        "expected_license": "CC BY-SA 3.0",
        "expected_camera_model": "DMC-FT3",
        "locale": "ar-EG",
        "reference_text": "أقصى سرعة 90 80 70 60",
        "capture_profile": "outdoor_road_sign_daylight",
        "source_page": "https://commons.wikimedia.org/wiki/File:Fixture.jpg",
        "ground_truth_basis": "controlled test metadata",
    }


def _payload(
    spec: dict[str, str],
    *,
    license_name: str = "CC BY-SA 3.0",
    camera_model: str = "DMC-FT3",
) -> dict[str, object]:
    return {
        "query": {
            "pages": {
                "1": {
                    "pageid": 1,
                    "title": spec["commons_file"],
                    "imageinfo": [
                        {
                            "sha1": spec["expected_commons_sha1"],
                            "url": "https://upload.wikimedia.org/wikipedia/commons/a/a0/fixture.jpg",
                            "metadata": [
                                {"name": "Model", "value": camera_model},
                            ],
                            "extmetadata": {
                                "LicenseShortName": {"value": license_name},
                            },
                        }
                    ],
                }
            }
        }
    }


def test_materializer_emits_real_camera_manifest_and_provenance(tmp_path: Path):
    image_bytes = b"camera-fixture-bytes"
    spec = _spec(image_bytes)

    manifest_path, provenance = materialize_wikimedia_camera_fixture(
        spec,
        tmp_path,
        json_fetcher=lambda _: _payload(spec),
        bytes_fetcher=lambda _: image_bytes,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == [
        {
            "fixture_id": "camera_01",
            "image_fixture": "fixtures/camera_01.jpg",
            "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "source_type": "real_camera_test",
            "patient_data": False,
            "locale": "ar-EG",
            "reference_text": "أقصى سرعة 90 80 70 60",
            "capture_profile": "outdoor_road_sign_daylight",
            "capture_device": "DMC-FT3",
        }
    ]
    assert provenance["commons_sha1"] == spec["expected_commons_sha1"]
    assert provenance["license"] == "CC BY-SA 3.0"
    assert provenance["camera_model"] == "DMC-FT3"


def test_materializer_rejects_changed_commons_sha1(tmp_path: Path):
    image_bytes = b"camera-fixture-bytes"
    spec = _spec(image_bytes)
    payload = _payload(spec)
    payload["query"]["pages"]["1"]["imageinfo"][0]["sha1"] = "0" * 40

    with pytest.raises(WikimediaCameraFixtureError, match="SHA-1"):
        materialize_wikimedia_camera_fixture(
            spec,
            tmp_path,
            json_fetcher=lambda _: payload,
            bytes_fetcher=lambda _: image_bytes,
        )


def test_materializer_rejects_license_or_camera_drift(tmp_path: Path):
    image_bytes = b"camera-fixture-bytes"
    spec = _spec(image_bytes)

    with pytest.raises(WikimediaCameraFixtureError, match="license"):
        materialize_wikimedia_camera_fixture(
            spec,
            tmp_path,
            json_fetcher=lambda _: _payload(spec, license_name="Public domain"),
            bytes_fetcher=lambda _: image_bytes,
        )

    with pytest.raises(WikimediaCameraFixtureError, match="camera model"):
        materialize_wikimedia_camera_fixture(
            spec,
            tmp_path,
            json_fetcher=lambda _: _payload(spec, camera_model="unknown"),
            bytes_fetcher=lambda _: image_bytes,
        )


def test_materializer_rejects_downloaded_byte_drift(tmp_path: Path):
    image_bytes = b"camera-fixture-bytes"
    spec = _spec(image_bytes)

    with pytest.raises(WikimediaCameraFixtureError, match="downloaded bytes"):
        materialize_wikimedia_camera_fixture(
            spec,
            tmp_path,
            json_fetcher=lambda _: _payload(spec),
            bytes_fetcher=lambda _: b"tampered",
        )
