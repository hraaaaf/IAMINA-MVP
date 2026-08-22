"""FRUG-9 scale/cost scaffold with explicit evidence provenance.

This module deliberately refuses to turn missing observations into zero. It can be
used before real billing or capacity data exists, but totals and capacity claims are
only emitted when every required input for that claim is present.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

EvidenceKind = Literal["measured", "scenario"]
CapacityStatus = Literal[
    "not_assessed",
    "unresolved",
    "within_observed_limit",
    "exceeds_observed_limit",
]
SCALE_TIERS = (1_000, 10_000, 50_000, 100_000)
_ONE_MILLION = Decimal(1_000_000)


@dataclass(frozen=True, slots=True)
class EvidenceValue:
    value: Decimal
    kind: EvidenceKind
    source: str

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("FRUG-9 evidence values cannot be negative")
        if self.kind not in {"measured", "scenario"}:
            raise ValueError("FRUG-9 evidence kind must be measured or scenario")
        if not self.source.strip():
            raise ValueError("FRUG-9 evidence values require a source")


@dataclass(frozen=True, slots=True)
class ScaleUsageInputs:
    interactions_per_mau: EvidenceValue | None = None
    llm_calls_per_interaction: EvidenceValue | None = None
    llm_input_tokens_per_call: EvidenceValue | None = None
    llm_output_tokens_per_call: EvidenceValue | None = None
    cloud_ocr_pages_per_mau: EvidenceValue | None = None
    storage_gb_month_per_mau: EvidenceValue | None = None
    egress_gb_per_mau: EvidenceValue | None = None


@dataclass(frozen=True, slots=True)
class ScalePriceInputs:
    llm_input_microusd_per_million_tokens: EvidenceValue | None = None
    llm_output_microusd_per_million_tokens: EvidenceValue | None = None
    cloud_ocr_microusd_per_page: EvidenceValue | None = None
    storage_microusd_per_gb_month: EvidenceValue | None = None
    egress_microusd_per_gb: EvidenceValue | None = None
    fixed_monthly_microusd: EvidenceValue | None = None


@dataclass(frozen=True, slots=True)
class ScaleCapacityInputs:
    """Provider capacity evidence kept separate from monthly cost evidence.

    ``llm_provider_tpm_limit`` must be an observed/measured account or tier
    throttle. ``peak_llm_calls_per_minute_per_mau`` must be independently measured
    or clearly labelled as a scenario. A TPM limit alone is never extrapolated to
    MAU tiers.
    """

    llm_provider_tpm_limit: EvidenceValue | None = None
    peak_llm_calls_per_minute_per_mau: EvidenceValue | None = None


@dataclass(frozen=True, slots=True)
class ScaleTierReport:
    mau: int
    llm_input_cost_microusd: Decimal | None
    llm_output_cost_microusd: Decimal | None
    cloud_ocr_cost_microusd: Decimal | None
    storage_cost_microusd: Decimal | None
    egress_cost_microusd: Decimal | None
    fixed_cost_microusd: Decimal | None
    total_cost_microusd: Decimal | None
    cost_per_mau_microusd: Decimal | None
    unresolved_inputs: tuple[str, ...]
    evidence_kinds: tuple[EvidenceKind, ...]
    projected_peak_llm_tpm: Decimal | None
    llm_provider_tpm_limit: Decimal | None
    llm_provider_tpm_utilization_ratio: Decimal | None
    llm_provider_tpm_capacity_status: CapacityStatus
    capacity_unresolved_inputs: tuple[str, ...]

    @property
    def fully_costed(self) -> bool:
        return self.total_cost_microusd is not None

    @property
    def capacity_assessed(self) -> bool:
        return self.llm_provider_tpm_capacity_status in {
            "within_observed_limit",
            "exceeds_observed_limit",
        }


@dataclass(frozen=True, slots=True)
class ScaleCertificationScaffold:
    tiers: tuple[ScaleTierReport, ...]

    @property
    def fully_costed(self) -> bool:
        return all(tier.fully_costed for tier in self.tiers)

    @property
    def capacity_assessed(self) -> bool:
        return all(tier.capacity_assessed for tier in self.tiers)


def build_scale_scaffold(
    usage: ScaleUsageInputs,
    prices: ScalePriceInputs,
    capacity: ScaleCapacityInputs | None = None,
) -> ScaleCertificationScaffold:
    """Build canonical FRUG-9 tiers without inventing cost or capacity inputs."""
    reports = tuple(
        _build_tier(mau, usage, prices, capacity) for mau in SCALE_TIERS
    )
    return ScaleCertificationScaffold(tiers=reports)


def _build_tier(
    mau: int,
    usage: ScaleUsageInputs,
    prices: ScalePriceInputs,
    capacity: ScaleCapacityInputs | None,
) -> ScaleTierReport:
    unresolved: set[str] = set()

    llm_calls = _multiply_required(
        Decimal(mau),
        ("interactions_per_mau", usage.interactions_per_mau),
        ("llm_calls_per_interaction", usage.llm_calls_per_interaction),
        unresolved=unresolved,
    )
    llm_input_cost = _token_cost(
        llm_calls,
        usage.llm_input_tokens_per_call,
        prices.llm_input_microusd_per_million_tokens,
        token_metric_name="llm_input_tokens_per_call",
        price_metric_name="llm_input_microusd_per_million_tokens",
        unresolved=unresolved,
    )
    llm_output_cost = _token_cost(
        llm_calls,
        usage.llm_output_tokens_per_call,
        prices.llm_output_microusd_per_million_tokens,
        token_metric_name="llm_output_tokens_per_call",
        price_metric_name="llm_output_microusd_per_million_tokens",
        unresolved=unresolved,
    )
    cloud_ocr_cost = _per_mau_cost(
        mau,
        usage.cloud_ocr_pages_per_mau,
        prices.cloud_ocr_microusd_per_page,
        usage_name="cloud_ocr_pages_per_mau",
        price_name="cloud_ocr_microusd_per_page",
        unresolved=unresolved,
    )
    storage_cost = _per_mau_cost(
        mau,
        usage.storage_gb_month_per_mau,
        prices.storage_microusd_per_gb_month,
        usage_name="storage_gb_month_per_mau",
        price_name="storage_microusd_per_gb_month",
        unresolved=unresolved,
    )
    egress_cost = _per_mau_cost(
        mau,
        usage.egress_gb_per_mau,
        prices.egress_microusd_per_gb,
        usage_name="egress_gb_per_mau",
        price_name="egress_microusd_per_gb",
        unresolved=unresolved,
    )
    fixed_cost = _required_value(
        prices.fixed_monthly_microusd,
        "fixed_monthly_microusd",
        unresolved,
    )

    components = (
        llm_input_cost,
        llm_output_cost,
        cloud_ocr_cost,
        storage_cost,
        egress_cost,
        fixed_cost,
    )
    total = (
        sum(components, Decimal(0))
        if all(value is not None for value in components)
        else None
    )
    cost_per_mau = total / Decimal(mau) if total is not None else None

    (
        projected_peak_llm_tpm,
        llm_provider_tpm_limit,
        llm_provider_tpm_utilization_ratio,
        llm_provider_tpm_capacity_status,
        capacity_unresolved_inputs,
    ) = _capacity_report(mau, usage, capacity)

    evidence_kinds = tuple(
        sorted(
            {
                item.kind
                for item in _all_evidence_values(usage, prices, capacity)
                if item is not None
            }
        )
    )

    return ScaleTierReport(
        mau=mau,
        llm_input_cost_microusd=llm_input_cost,
        llm_output_cost_microusd=llm_output_cost,
        cloud_ocr_cost_microusd=cloud_ocr_cost,
        storage_cost_microusd=storage_cost,
        egress_cost_microusd=egress_cost,
        fixed_cost_microusd=fixed_cost,
        total_cost_microusd=total,
        cost_per_mau_microusd=cost_per_mau,
        unresolved_inputs=tuple(sorted(unresolved)),
        evidence_kinds=evidence_kinds,
        projected_peak_llm_tpm=projected_peak_llm_tpm,
        llm_provider_tpm_limit=llm_provider_tpm_limit,
        llm_provider_tpm_utilization_ratio=llm_provider_tpm_utilization_ratio,
        llm_provider_tpm_capacity_status=llm_provider_tpm_capacity_status,
        capacity_unresolved_inputs=capacity_unresolved_inputs,
    )


def _capacity_report(
    mau: int,
    usage: ScaleUsageInputs,
    capacity: ScaleCapacityInputs | None,
) -> tuple[
    Decimal | None,
    Decimal | None,
    Decimal | None,
    CapacityStatus,
    tuple[str, ...],
]:
    if capacity is None:
        return None, None, None, "not_assessed", ()

    unresolved: set[str] = set()
    limit = capacity.llm_provider_tpm_limit
    peak_rate = capacity.peak_llm_calls_per_minute_per_mau

    if limit is None:
        unresolved.add("llm_provider_tpm_limit")
    elif limit.value <= 0:
        raise ValueError("FRUG-9 provider TPM limit must be positive")
    elif limit.kind != "measured":
        raise ValueError("FRUG-9 provider TPM limit must use measured evidence")

    if peak_rate is None:
        unresolved.add("peak_llm_calls_per_minute_per_mau")
    if usage.llm_input_tokens_per_call is None:
        unresolved.add("llm_input_tokens_per_call")
    if usage.llm_output_tokens_per_call is None:
        unresolved.add("llm_output_tokens_per_call")

    projected = None
    if (
        peak_rate is not None
        and usage.llm_input_tokens_per_call is not None
        and usage.llm_output_tokens_per_call is not None
    ):
        tokens_per_call = (
            usage.llm_input_tokens_per_call.value
            + usage.llm_output_tokens_per_call.value
        )
        projected = Decimal(mau) * peak_rate.value * tokens_per_call

    limit_value = limit.value if limit is not None else None
    if projected is None or limit_value is None:
        return (
            projected,
            limit_value,
            None,
            "unresolved",
            tuple(sorted(unresolved)),
        )

    utilization = projected / limit_value
    status: CapacityStatus = (
        "within_observed_limit"
        if projected <= limit_value
        else "exceeds_observed_limit"
    )
    return projected, limit_value, utilization, status, tuple(sorted(unresolved))


def _all_evidence_values(
    usage: ScaleUsageInputs,
    prices: ScalePriceInputs,
    capacity: ScaleCapacityInputs | None,
) -> tuple[EvidenceValue | None, ...]:
    capacity_values: tuple[EvidenceValue | None, ...] = ()
    if capacity is not None:
        capacity_values = (
            capacity.llm_provider_tpm_limit,
            capacity.peak_llm_calls_per_minute_per_mau,
        )
    return (
        usage.interactions_per_mau,
        usage.llm_calls_per_interaction,
        usage.llm_input_tokens_per_call,
        usage.llm_output_tokens_per_call,
        usage.cloud_ocr_pages_per_mau,
        usage.storage_gb_month_per_mau,
        usage.egress_gb_per_mau,
        prices.llm_input_microusd_per_million_tokens,
        prices.llm_output_microusd_per_million_tokens,
        prices.cloud_ocr_microusd_per_page,
        prices.storage_microusd_per_gb_month,
        prices.egress_microusd_per_gb,
        prices.fixed_monthly_microusd,
        *capacity_values,
    )


def _multiply_required(
    base: Decimal,
    *named_values: tuple[str, EvidenceValue | None],
    unresolved: set[str],
) -> Decimal | None:
    result = base
    for name, item in named_values:
        if item is None:
            unresolved.add(name)
            return None
        result *= item.value
    return result


def _token_cost(
    calls: Decimal | None,
    tokens_per_call: EvidenceValue | None,
    price: EvidenceValue | None,
    *,
    token_metric_name: str,
    price_metric_name: str,
    unresolved: set[str],
) -> Decimal | None:
    if calls is None:
        return None
    if tokens_per_call is None:
        unresolved.add(token_metric_name)
    if price is None:
        unresolved.add(price_metric_name)
    if tokens_per_call is None or price is None:
        return None
    return calls * tokens_per_call.value * price.value / _ONE_MILLION


def _per_mau_cost(
    mau: int,
    usage: EvidenceValue | None,
    price: EvidenceValue | None,
    *,
    usage_name: str,
    price_name: str,
    unresolved: set[str],
) -> Decimal | None:
    if usage is None:
        unresolved.add(usage_name)
    if price is None:
        unresolved.add(price_name)
    if usage is None or price is None:
        return None
    return Decimal(mau) * usage.value * price.value


def _required_value(
    item: EvidenceValue | None,
    name: str,
    unresolved: set[str],
) -> Decimal | None:
    if item is None:
        unresolved.add(name)
        return None
    return item.value
