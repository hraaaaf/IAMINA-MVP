from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evaluation.stt_fixture_manifest import FixtureManifestError, validate_manifest


def _entry(path: str, digest: str, **overrides):
    item = {
        "fixture_id": "stt_fr_low_54_quiet_01",
        "audio_fixture": path,
        "audio_sha256": digest,
        "source_type": "human_test_speaker",
        "locale": "fr",
        "reference_transcript": "Ma glycémie est à 54, je me sens étourdi.",
        "critical_tokens": ["54"],
        "required_concepts": ["low_glucose", "dizziness"],
        "capture_profile": "quiet_room",
        "sample_rate_hz": 16000,
        "channels": 1,
        "encoding": "wav_pcm_s16le",
        "duration_ms": 1800,
        "consent_recorded": True,
        "patient_data": False,
        "created_on": "2026-08-18",
        "review_status": "human_checked",
    }
    item.update(overrides)
    return item


def _write_manifest(tmp_path: Path, entries: list[dict]) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return manifest


def test_valid_manifest_accepts_integrity_pinned_human_fixture(tmp_path):
    audio = tmp_path / "fixtures" / "clip.wav"
    audio.parent.mkdir()
    audio.write_bytes(b"RIFF-controlled-test-audio")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    manifest = _write_manifest(tmp_path, [_entry("fixtures/clip.wav", digest)])

    validated = validate_manifest(manifest, tmp_path)

    assert len(validated) == 1
    assert validated[0]["audio_sha256"] == digest


def test_rejects_patient_data_or_missing_human_consent(tmp_path):
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"audio")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()

    for override, message in (
        ({"patient_data": True}, "patient_data"),
        ({"consent_recorded": False}, "consent_recorded"),
    ):
        manifest = _write_manifest(tmp_path, [_entry("clip.wav", digest, **override)])
        with pytest.raises(FixtureManifestError, match=message):
            validate_manifest(manifest, tmp_path)


def test_rejects_tampered_traversal_and_duplicate_audio(tmp_path):
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"audio-one")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()

    tampered = _write_manifest(tmp_path, [_entry("clip.wav", "0" * 64)])
    with pytest.raises(FixtureManifestError, match="SHA-256 mismatch"):
        validate_manifest(tampered, tmp_path)

    traversal = _write_manifest(tmp_path, [_entry("../clip.wav", digest)])
    with pytest.raises(FixtureManifestError, match="repository-relative"):
        validate_manifest(traversal, tmp_path)

    duplicate = _write_manifest(
        tmp_path,
        [
            _entry("clip.wav", digest),
            _entry("clip.wav", digest, fixture_id="stt_fr_low_54_noise_02"),
        ],
    )
    with pytest.raises(FixtureManifestError, match="duplicate audio content"):
        validate_manifest(duplicate, tmp_path)


def test_synthetic_tts_does_not_require_human_consent(tmp_path):
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"synthetic-audio")
    digest = hashlib.sha256(audio.read_bytes()).hexdigest()
    manifest = _write_manifest(
        tmp_path,
        [
            _entry(
                "clip.wav",
                digest,
                source_type="synthetic_tts",
                consent_recorded=False,
            )
        ],
    )

    assert validate_manifest(manifest, tmp_path)[0]["source_type"] == "synthetic_tts"
