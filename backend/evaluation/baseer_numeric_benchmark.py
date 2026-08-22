"""Baseer OCR adapter for the pinned Misraj numeric-safety benchmark.

Benchmark-only. The model is loaded from a pinned Hugging Face revision and
must not emit raw OCR or ground-truth text into the evidence artifact.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from evaluation.misraj_numeric_benchmark import run_misraj_numeric_benchmark

BASEER_MODEL = "AbdoTarek/Baseer-OCR-V1.0"
BASEER_MODEL_REVISION = "511458b8aaecac37fe403bb1f9aaa24761af0c10"
BASEER_PROMPT = (
    "Extract ALL visible text from this Arabic document image. "
    "Preserve the original reading order and every number exactly. "
    "Do not explain or summarize. Return only the extracted text."
)
_BENCHMARK_NAME = "c32-misraj-baseer-ocr-exact-numeric-safety"

ModelFactory = Callable[[], tuple[Any, Any]]
OCRCallable = Callable[[bytes], str]


def _engine_config() -> dict[str, object]:
    return {
        "model": BASEER_MODEL,
        "model_revision": BASEER_MODEL_REVISION,
        "model_sha256": os.getenv("C32_MODEL_SHA256"),
        "base_model_family": "qwen2-vl-2b",
        "device": "cpu",
        "dtype": "bfloat16",
        "max_pixels": 1536 * 28 * 28,
        "full_page": True,
        "prompt_contract": "extract-only-preserve-numbers",
    }


def _with_engine_metadata(result: dict[str, object]) -> dict[str, object]:
    result["benchmark"] = _BENCHMARK_NAME
    result["engine"] = "baseer-ocr-v1.0"
    result["engine_config"] = _engine_config()
    return result


def baseer_runtime_error_evidence(*, phase: str, exc: BaseException) -> dict[str, object]:
    """Return privacy-safe evidence for a benchmark runtime failure."""
    if phase not in {"fixture_load", "model_init", "benchmark"}:
        raise ValueError("invalid C32 execution phase")
    return _with_engine_metadata({
        "execution_outcome": "runtime_error",
        "execution_phase": phase,
        "runtime_error_type": type(exc).__name__,
        "raw_ground_truth_emitted": False,
        "raw_ocr_text_emitted": False,
        "real_camera_claim": False,
        "iamina_patient_data": False,
        "provider_api": False,
        "paid_inference": False,
    })


def _default_model_factory() -> tuple[Any, Any]:
    model_dir = os.getenv("C32_BASEER_MODEL_DIR")
    if not model_dir:
        raise RuntimeError("C32 requires C32_BASEER_MODEL_DIR")
    path = Path(model_dir)
    if not path.is_dir():
        raise RuntimeError("C32 pinned Baseer model directory is missing")

    import torch
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    processor = AutoProcessor.from_pretrained(
        path,
        revision=BASEER_MODEL_REVISION,
        local_files_only=True,
        min_pixels=256 * 28 * 28,
        max_pixels=1536 * 28 * 28,
    )
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        path,
        revision=BASEER_MODEL_REVISION,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        local_files_only=True,
        attn_implementation="eager",
    ).eval()
    return model, processor


def make_baseer_callable(*, model_factory: ModelFactory = _default_model_factory) -> OCRCallable:
    model, processor = model_factory()

    def ocr(image_bytes: bytes) -> str:
        import torch
        from qwen_vl_utils import process_vision_info

        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": normalized},
                    {"type": "text", "text": BASEER_PROMPT},
                ],
            }]
            prompt = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, _ = process_vision_info(messages)
            inputs = processor(
                text=[prompt],
                images=image_inputs,
                padding=True,
                return_tensors="pt",
            ).to(model.device)

        with torch.inference_mode():
            generated = model.generate(
                **inputs, max_new_tokens=2048, do_sample=False, use_cache=True
            )
        trimmed = [
            output[len(input_ids):]
            for input_ids, output in zip(inputs.input_ids, generated)
        ]
        decoded = processor.batch_decode(
            trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        if len(decoded) != 1 or not decoded[0].strip():
            raise ValueError("Baseer must return one non-empty OCR result")
        return decoded[0].strip()

    return ocr


def run_baseer_numeric_benchmark(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    ocr_callable: OCRCallable | None = None,
) -> dict[str, object]:
    result = run_misraj_numeric_benchmark(
        payload,
        source,
        ocr_callable=ocr_callable or make_baseer_callable(),
    )
    return _with_engine_metadata(result)


def run_baseer_numeric_benchmark_diagnostic(
    payload: dict[str, Any],
    source: dict[str, Any],
    *,
    ocr_callable: OCRCallable | None = None,
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, object]:
    if ocr_callable is None:
        try:
            ocr_callable = make_baseer_callable(model_factory=model_factory)
        except Exception as exc:
            return baseer_runtime_error_evidence(phase="model_init", exc=exc)

    try:
        result = run_baseer_numeric_benchmark(
            payload, source, ocr_callable=ocr_callable
        )
    except Exception as exc:
        return baseer_runtime_error_evidence(phase="benchmark", exc=exc)

    result["execution_outcome"] = (
        "pass" if result["numeric_safety_floor_passed"] else "verdict_reject"
    )
    result["execution_phase"] = "complete"
    result["runtime_error_type"] = None
    return result
