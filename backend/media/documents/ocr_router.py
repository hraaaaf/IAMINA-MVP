"""Deterministic, evidence-gated OCR routing policy.

This module chooses a qualified lane, never a concrete provider or model. Runtime
wiring must separately prove the selected lane's implementation and processor
policy before any external egress occurs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OcrModality = Literal[
    "digital_pdf",
    "scanned_pdf",
    "document_image",
    "glucometer",
]
OcrScript = Literal["latin", "arabic", "unknown"]
OcrLane = Literal[
    "local_text_layer",
    "on_device_ocr",
    "local_ocr",
    "governed_cloud_ocr",
    "unavailable",
]


@dataclass(frozen=True, slots=True)
class OcrRequest:
    modality: OcrModality
    script: OcrScript = "unknown"
    bounded_capture: bool = False


@dataclass(frozen=True, slots=True)
class OcrCapabilities:
    local_latin_qualified: bool = False
    local_arabic_full_qualified: bool = False
    bounded_arabic_qualified: bool = False
    on_device_glucometer_qualified: bool = True
    governed_cloud_allowed: bool = False


@dataclass(frozen=True, slots=True)
class OcrRouteDecision:
    lane: OcrLane
    reason: str

    @property
    def external_egress(self) -> bool:
        return self.lane == "governed_cloud_ocr"


def choose_ocr_lane(
    request: OcrRequest,
    capabilities: OcrCapabilities,
) -> OcrRouteDecision:
    """Choose the cheapest qualified lane without silent quality downgrades."""
    if request.modality == "digital_pdf":
        return OcrRouteDecision(
            lane="local_text_layer",
            reason="digital_pdf_text_layer",
        )

    if request.modality == "glucometer":
        if capabilities.on_device_glucometer_qualified:
            return OcrRouteDecision(
                lane="on_device_ocr",
                reason="qualified_on_device_glucometer",
            )
        return _cloud_or_unavailable(capabilities, "glucometer_local_unqualified")

    if request.script == "latin":
        if capabilities.local_latin_qualified:
            return OcrRouteDecision(
                lane="local_ocr",
                reason="qualified_local_latin",
            )
        return _cloud_or_unavailable(capabilities, "latin_local_unqualified")

    if request.script == "arabic":
        if request.bounded_capture and capabilities.bounded_arabic_qualified:
            return OcrRouteDecision(
                lane="local_ocr",
                reason="qualified_bounded_arabic",
            )
        if capabilities.local_arabic_full_qualified:
            return OcrRouteDecision(
                lane="local_ocr",
                reason="qualified_local_arabic_full",
            )
        return _cloud_or_unavailable(capabilities, "arabic_local_unqualified")

    return _cloud_or_unavailable(capabilities, "script_unknown")


def _cloud_or_unavailable(
    capabilities: OcrCapabilities,
    reason: str,
) -> OcrRouteDecision:
    if capabilities.governed_cloud_allowed:
        return OcrRouteDecision(
            lane="governed_cloud_ocr",
            reason=f"{reason}_cloud_governed",
        )
    return OcrRouteDecision(
        lane="unavailable",
        reason=f"{reason}_no_qualified_lane",
    )
