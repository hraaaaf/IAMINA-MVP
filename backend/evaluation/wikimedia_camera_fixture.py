"""Materialize provenance-checked Wikimedia camera fixtures for C24.

The source is pinned by Commons SHA-1, license and camera model. Downloaded bytes
are verified before a local C19-compatible real-camera manifest is emitted.
Network fetchers are injectable so normal tests remain fully offline.
"""

from __future__ import annotations

import hashlib
import http.client
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit


class WikimediaCameraFixtureError(ValueError):
    pass


JsonFetcher = Callable[[str], dict[str, Any]]
BytesFetcher = Callable[[str], bytes]


def _https_get(url: str, *, expected_host: str, timeout: int) -> bytes:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected_host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
    ):
        raise WikimediaCameraFixtureError("unexpected HTTPS source")
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    connection = http.client.HTTPSConnection(expected_host, timeout=timeout)
    try:
        connection.request("GET", target, headers={"User-Agent": "IAMINA-C24W/1.0"})
        response = connection.getresponse()
        if response.status != 200:
            raise WikimediaCameraFixtureError(
                f"Wikimedia returned HTTP {response.status}"
            )
        return response.read()
    finally:
        connection.close()


def _default_json_fetcher(url: str) -> dict[str, Any]:
    return json.loads(
        _https_get(url, expected_host="commons.wikimedia.org", timeout=30).decode(
            "utf-8"
        )
    )


def _default_bytes_fetcher(url: str) -> bytes:
    return _https_get(url, expected_host="upload.wikimedia.org", timeout=60)


def _metadata_map(imageinfo: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in imageinfo.get("metadata", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            value = item.get("value")
            if value is not None:
                values[item["name"]] = str(value)
    for name, raw in imageinfo.get("extmetadata", {}).items():
        if isinstance(raw, dict) and raw.get("value") is not None:
            values[name] = str(raw["value"])
    return values


def _single_imageinfo(payload: dict[str, Any]) -> dict[str, Any]:
    pages = payload.get("query", {}).get("pages", {})
    if not isinstance(pages, dict) or len(pages) != 1:
        raise WikimediaCameraFixtureError("Commons API must return exactly one page")
    page = next(iter(pages.values()))
    if not isinstance(page, dict) or page.get("missing") is not None:
        raise WikimediaCameraFixtureError("Commons file is missing")
    infos = page.get("imageinfo")
    if not isinstance(infos, list) or len(infos) != 1 or not isinstance(infos[0], dict):
        raise WikimediaCameraFixtureError("Commons imageinfo is missing or ambiguous")
    return infos[0]


def materialize_wikimedia_camera_fixture(
    spec: dict[str, Any],
    workspace: Path,
    *,
    json_fetcher: JsonFetcher = _default_json_fetcher,
    bytes_fetcher: BytesFetcher = _default_bytes_fetcher,
) -> tuple[Path, dict[str, Any]]:
    required = (
        "fixture_id",
        "commons_file",
        "expected_commons_sha1",
        "expected_license",
        "expected_camera_model",
        "locale",
        "reference_text",
        "capture_profile",
        "source_page",
    )
    for key in required:
        if not isinstance(spec.get(key), str) or not str(spec[key]).strip():
            raise WikimediaCameraFixtureError(f"{key} is required")

    params = urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|sha1|metadata|extmetadata",
            "titles": spec["commons_file"],
        }
    )
    api_url = f"https://commons.wikimedia.org/w/api.php?{params}"
    imageinfo = _single_imageinfo(json_fetcher(api_url))

    api_sha1 = str(imageinfo.get("sha1", "")).lower()
    expected_sha1 = str(spec["expected_commons_sha1"]).lower()
    if api_sha1 != expected_sha1:
        raise WikimediaCameraFixtureError("Commons SHA-1 does not match pinned provenance")

    metadata = _metadata_map(imageinfo)
    license_name = metadata.get("LicenseShortName", "")
    if str(spec["expected_license"]).lower() not in license_name.lower():
        raise WikimediaCameraFixtureError("Commons license does not match pinned license")

    camera_model = metadata.get("Model", metadata.get("CameraModel", ""))
    if str(spec["expected_camera_model"]).lower() not in camera_model.lower():
        raise WikimediaCameraFixtureError("camera model provenance is missing or changed")

    original_url = imageinfo.get("url")
    if not isinstance(original_url, str):
        raise WikimediaCameraFixtureError("Commons original URL is missing")
    parsed_original = urlsplit(original_url)
    if parsed_original.scheme != "https" or parsed_original.hostname != "upload.wikimedia.org":
        raise WikimediaCameraFixtureError("Commons original URL is unexpected")

    image_bytes = bytes_fetcher(original_url)
    downloaded_sha1 = hashlib.sha1(image_bytes, usedforsecurity=False).hexdigest()
    if downloaded_sha1 != expected_sha1:
        raise WikimediaCameraFixtureError("downloaded bytes do not match Commons SHA-1")

    suffix = Path(parsed_original.path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise WikimediaCameraFixtureError("unsupported Commons image extension")

    workspace.mkdir(parents=True, exist_ok=True)
    image_rel = Path("fixtures") / f"{spec['fixture_id']}{suffix}"
    image_path = workspace / image_rel
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(image_bytes)
    sha256 = hashlib.sha256(image_bytes).hexdigest()

    manifest = [
        {
            "fixture_id": spec["fixture_id"],
            "image_fixture": image_rel.as_posix(),
            "image_sha256": sha256,
            "source_type": "real_camera_test",
            "patient_data": False,
            "locale": spec["locale"],
            "reference_text": spec["reference_text"],
            "capture_profile": spec["capture_profile"],
            "capture_device": camera_model,
        }
    ]
    manifest_path = workspace / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    provenance = {
        "fixture_id": spec["fixture_id"],
        "commons_file": spec["commons_file"],
        "source_page": spec["source_page"],
        "commons_sha1": api_sha1,
        "sha256": sha256,
        "license": license_name,
        "camera_model": camera_model,
        "original_url": original_url,
        "ground_truth_basis": spec.get("ground_truth_basis", ""),
    }
    return manifest_path, provenance
