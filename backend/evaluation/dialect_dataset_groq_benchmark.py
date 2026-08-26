"""Dataset-backed MENA dialect comprehension benchmark for Groq.

The benchmark downloads small public CC-BY-4.0 dialect datasets, selects a
deterministic privacy-screened sample, and asks Groq to identify the country
dialect. Raw source text is never retained in the output artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from evaluation.frug5_multilingual_quality_benchmark import (
    MODEL,
    PROVIDER,
    BenchmarkConfigurationError,
    load_controlled_price,
)
from evaluation.provider_benchmark_preflight import ProviderBenchmarkPreflight

DATASET_ID = "iamina-mena-dialect-datasets-v1"
CASES_PER_COUNTRY = 3
MAX_COMPLETION_TOKENS = 64
SPEND_CEILING_MICROUSD = 5_000

TARGETS = {
    "SA": ("ebubekr53/organic-gulf-arabic-dialect-dataset", "saudi arabia"),
    "AE": ("ebubekr53/organic-gulf-arabic-dialect-dataset", "united arab emirates"),
    "KW": ("ebubekr53/organic-gulf-arabic-dialect-dataset", "kuwait"),
    "QA": ("ebubekr53/organic-gulf-arabic-dialect-dataset", "qatar"),
    "OM": ("ebubekr53/organic-gulf-arabic-dialect-dataset", "oman"),
    "MA": ("ebubekr53/organic-maghrebi-arabic-dialect-dataset", "morocco"),
}
EXPECTED_LICENSE = "cc-by-4.0"

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_LATIN = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")
_URL_OR_EMAIL = re.compile(r"(?:https?://|www\.|@|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})", re.I)
_TIMESTAMPISH = re.compile(r"\[\s*\d{1,2}/\d{1,2}[^\]]*\]")
_SUSPICIOUS = (
    "كسم", "كس ام", "قحبة", "شرموط", "ديوث", "داعرة",
)

SYSTEM_PROMPT = (
    "Classify the Arabic dialect sample by country. "
    "Return only one ISO country code from SA, AE, KW, QA, OM, MA. "
    "Do not explain."
)


class BenchmarkConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    repo_id: str
    revision: str
    license: str
    csv_path: str
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True, slots=True)
class DialectCase:
    case_id: str
    country_code: str
    source_repo: str
    source_revision: str
    source_row_id: str
    text: str


def _http_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "IAMINA-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "IAMINA-benchmark/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def _source_snapshot(repo_id: str) -> SourceSnapshot:
    meta = _http_json(f"https://huggingface.co/api/datasets/{repo_id}")
    revision = str(meta.get("sha") or "").strip()
    card = meta.get("cardData") or {}
    license_name = str(card.get("license") or "").strip().lower()
    siblings = meta.get("siblings") or []
    csv_paths = sorted(
        str(item.get("rfilename"))
        for item in siblings
        if str(item.get("rfilename") or "").lower().endswith(".csv")
    )
    if not revision:
        raise BenchmarkConfigurationError(f"{repo_id}: missing immutable revision")
    if license_name != EXPECTED_LICENSE:
        raise BenchmarkConfigurationError(
            f"{repo_id}: expected {EXPECTED_LICENSE}, got {license_name or 'missing'}"
        )
    if not csv_paths:
        raise BenchmarkConfigurationError(f"{repo_id}: no CSV source file")
    csv_path = csv_paths[0]
    url = f"https://huggingface.co/datasets/{repo_id}/resolve/{revision}/{csv_path}"
    raw = _http_bytes(url)
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    rows = tuple({str(k): str(v or "") for k, v in row.items()} for row in reader)
    if not rows:
        raise BenchmarkConfigurationError(f"{repo_id}: empty CSV")
    return SourceSnapshot(
        repo_id=repo_id,
        revision=revision,
        license=license_name,
        csv_path=csv_path,
        rows=rows,
    )


def _privacy_screen(text: str) -> bool:
    value = " ".join(text.split()).strip()
    if len(value) < 20 or len(value) > 100:
        return False
    if len(value.split()) < 4:
        return False
    if not _ARABIC.search(value):
        return False
    if _LATIN.search(value) or _DIGIT.search(value):
        return False
    if _URL_OR_EMAIL.search(value) or _TIMESTAMPISH.search(value):
        return False
    lowered = value.casefold()
    if any(term in lowered for term in _SUSPICIOUS):
        return False
    return True


def _normalize_row_id(value: str) -> tuple[int, str]:
    try:
        return int(value), value
    except ValueError:
        return 10**12, value


def build_cases(snapshots: dict[str, SourceSnapshot]) -> tuple[DialectCase, ...]:
    cases: list[DialectCase] = []
    for country_code, (repo_id, country_label) in TARGETS.items():
        snapshot = snapshots[repo_id]
        eligible = [
            row for row in snapshot.rows
            if row.get("source_country", "").strip().casefold() == country_label
            and _privacy_screen(row.get("source_text", ""))
        ]
        eligible.sort(key=lambda row: _normalize_row_id(row.get("id", "")))
        if len(eligible) < CASES_PER_COUNTRY:
            raise BenchmarkConfigurationError(
                f"{country_code}: only {len(eligible)} privacy-safe rows available"
            )
        for index, row in enumerate(eligible[:CASES_PER_COUNTRY], start=1):
            text = " ".join(row["source_text"].split()).strip()
            cases.append(
                DialectCase(
                    case_id=f"{country_code.lower()}-{index}",
                    country_code=country_code,
                    source_repo=repo_id,
                    source_revision=snapshot.revision,
                    source_row_id=row.get("id", ""),
                    text=text,
                )
            )
    return tuple(cases)


def strict_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "mena_dialect_country",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "enum": sorted(TARGETS),
                    }
                },
                "required": ["country_code"],
                "additionalProperties": False,
            },
        },
    }


def _case_prompt(case: DialectCase) -> str:
    return json.dumps(
        {"sample": case.text, "allowed_codes": sorted(TARGETS)},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def projected_spend_microusd(price, cases: tuple[DialectCase, ...]) -> int:
    total = 0
    for case in cases:
        total += price.worst_case_microusd(
            input_tokens=len((SYSTEM_PROMPT + _case_prompt(case)).encode("utf-8")),
            output_tokens=MAX_COMPLETION_TOKENS,
        )
    return total


def _usage_row(response) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        raise BenchmarkConfigurationError("provider usage evidence missing")
    details = getattr(usage, "prompt_tokens_details", None)
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "cached_input_tokens": getattr(details, "cached_tokens", None) if details else None,
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def _invoke_case(provider, case: DialectCase):
    return provider.client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _case_prompt(case)},
        ],
        response_format=strict_response_format(),
        reasoning_effort="low",
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        timeout=provider.timeout_seconds,
    )


def run_benchmark(*, output_path: Path, today: date) -> dict[str, Any]:
    if not os.environ.get("GROQ_API_KEY", "").strip():
        raise BenchmarkConfigurationError("missing GROQ_API_KEY benchmark credential")

    unique_repos = sorted({repo_id for repo_id, _ in TARGETS.values()})
    snapshots = {repo_id: _source_snapshot(repo_id) for repo_id in unique_repos}
    cases = build_cases(snapshots)
    if len(cases) != CASES_PER_COUNTRY * len(TARGETS):
        raise BenchmarkConfigurationError("unexpected case count")

    price = load_controlled_price(today=today)
    projected = projected_spend_microusd(price, cases)
    if projected > SPEND_CEILING_MICROUSD:
        raise BenchmarkConfigurationError("projected spend exceeds explicit ceiling")

    ProviderBenchmarkPreflight(
        provider=PROVIDER,
        model=MODEL,
        modality="text",
        dataset_id=DATASET_ID,
        credential_reference="env:GROQ_API_KEY",
        pricing_evidence_reference=price.evidence_reference,
        network_authorized=os.environ.get(
            "MENA_DIALECT_DATASET_NETWORK_AUTHORIZED", ""
        ).lower() == "true",
        spend_ceiling_microusd=SPEND_CEILING_MICROUSD,
        patient_data=False,
    ).validate()

    from llm.provider_registry import build_openai_compatible_provider

    provider = build_openai_compatible_provider(PROVIDER, model=MODEL)
    rows: list[dict[str, Any]] = []
    usage_rows: list[dict[str, int | None]] = []
    actual_cost = 0
    try:
        for case in cases:
            response = _invoke_case(provider, case)
            parsed = json.loads(response.choices[0].message.content or "")
            predicted = parsed.get("country_code") if isinstance(parsed, dict) else None
            usage = _usage_row(response)
            in_tokens, out_tokens = usage["input_tokens"], usage["output_tokens"]
            if not isinstance(in_tokens, int) or not isinstance(out_tokens, int):
                raise BenchmarkConfigurationError("provider token counts missing")
            usage_rows.append(usage)
            actual_cost += price.worst_case_microusd(
                input_tokens=in_tokens,
                output_tokens=out_tokens,
            )
            rows.append(
                {
                    "case_id": case.case_id,
                    "expected_country_code": case.country_code,
                    "predicted_country_code": predicted,
                    "correct": predicted == case.country_code,
                    "source_repo": case.source_repo,
                    "source_revision": case.source_revision,
                    "source_row_id": case.source_row_id,
                    "source_text_sha256": hashlib.sha256(
                        case.text.encode("utf-8")
                    ).hexdigest(),
                }
            )
    finally:
        provider.client.close()

    by_country: dict[str, dict[str, int]] = {}
    for code in TARGETS:
        country_rows = [row for row in rows if row["expected_country_code"] == code]
        by_country[code] = {
            "correct": sum(1 for row in country_rows if row["correct"]),
            "total": len(country_rows),
        }
    correct = sum(1 for row in rows if row["correct"])
    total = len(rows)

    report = {
        "provider": PROVIDER,
        "model": MODEL,
        "dataset_id": DATASET_ID,
        "run_date": today.isoformat(),
        "patient_data": False,
        "public_external_dataset": True,
        "raw_source_text_retained": False,
        "source_license_required": EXPECTED_LICENSE,
        "source_snapshots": {
            repo_id: {
                "revision": snapshot.revision,
                "license": snapshot.license,
                "csv_path": snapshot.csv_path,
            }
            for repo_id, snapshot in snapshots.items()
        },
        "planned_calls": len(cases),
        "completed_calls": len(rows),
        "projected_max_microusd": projected,
        "actual_cost_microusd_worst_case_from_reported_usage": actual_cost,
        "provider_usage": usage_rows,
        "dialect_identification": {
            "correct": correct,
            "total": total,
            "accuracy": correct / total if total else 0.0,
            "by_country": by_country,
        },
        "proof_boundaries": {
            "objective_country_label_benchmark": True,
            "generation_naturalness_certified": False,
            "native_speaker_final_review_replaced": False,
            "patient_egress_approved": False,
            "production_cutover_authorized": False,
        },
        "case_results": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark(output_path=args.output, today=date.today())
    summary = report["dialect_identification"]
    print(json.dumps({
        "accuracy": summary["accuracy"],
        "correct": summary["correct"],
        "total": summary["total"],
        "completed_calls": report["completed_calls"],
        "actual_cost_microusd": report[
            "actual_cost_microusd_worst_case_from_reported_usage"
        ],
    }))
    per_country_ok = all(v["correct"] >= 2 for v in summary["by_country"].values())
    quality_ok = summary["correct"] >= 15 and per_country_ok
    return 0 if quality_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
