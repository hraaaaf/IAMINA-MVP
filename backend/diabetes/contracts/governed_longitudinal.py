"""V2-D governed longitudinal multi-source intelligence contract."""
from __future__ import annotations

from dataclasses import dataclass

from diabetes.contracts.multi_source_fusion import GovernedGlucoseFusionContract


class LongitudinalContractError(ValueError):
    """Raised when longitudinal multi-source analysis is ambiguous or unsafe."""


GOVERNED_LONGITUDINAL_CONTRACT_ID = "governed-longitudinal-multisource.v1"


@dataclass(frozen=True, slots=True)
class GovernedLongitudinalContract:
    fusion_contract: GovernedGlucoseFusionContract
    contract_id: str = GOVERNED_LONGITUDINAL_CONTRACT_ID
    minimum_facts_per_population: int = 3
    minimum_distinct_days_per_population: int = 2

    def __post_init__(self) -> None:
        if not isinstance(self.fusion_contract, GovernedGlucoseFusionContract):
            raise LongitudinalContractError("fusion_contract must be governed and explicit")
        if self.contract_id != GOVERNED_LONGITUDINAL_CONTRACT_ID:
            raise LongitudinalContractError("unsupported longitudinal contract_id")
        if type(self.minimum_facts_per_population) is not int or self.minimum_facts_per_population < 1:
            raise LongitudinalContractError("minimum_facts_per_population must be a positive integer")
        if (
            type(self.minimum_distinct_days_per_population) is not int
            or self.minimum_distinct_days_per_population < 1
        ):
            raise LongitudinalContractError(
                "minimum_distinct_days_per_population must be a positive integer"
            )
