"""Privacy-safe OCR route telemetry.

Only route metadata is emitted. Patient identifiers, filenames, document text,
provider payloads, and extracted content are deliberately excluded.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger("iamina.cost")

_ALLOWED_MODALITIES = frozenset(
    {"digital_pdf", "scanned_pdf", "document_image", "glucometer"}
)
_ALLOWED_SCRIPTS = frozenset({"latin", "arabic", "unknown"})
_ALLOWED_LANES = frozenset(
    {
        "local_text_layer",
        "on_device_ocr",
        "local_ocr",
        "governed_cloud_ocr",
        "unavailable",
    }
)


def record_ocr_route(
    *,
    modality: str,
    script: str,
    bounded_capture: bool,
    lane: str,
) -> None:
    """Record one content-free OCR routing decision for FRUG-2/FRUG-9 evidence."""
    if modality not in _ALLOWED_MODALITIES:
        raise ValueError(f"unsupported OCR modality: {modality}")
    if script not in _ALLOWED_SCRIPTS:
        raise ValueError(f"unsupported OCR script: {script}")
    if not isinstance(bounded_capture, bool):
        raise ValueError("bounded_capture must be bool")
    if lane not in _ALLOWED_LANES:
        raise ValueError(f"unsupported OCR lane: {lane}")

    logger.info(
        "cost_telemetry %s",
        json.dumps(
            {
                "event": "ocr_route",
                "modality": modality,
                "script": script,
                "bounded_capture": bounded_capture,
                "lane": lane,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
