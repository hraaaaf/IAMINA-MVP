"""Explicit fail-closed contract for multi-source glucose fusion.

V2-C makes source mixing an opt-in clinical-data operation. Journal evidence,
CGM transport facts and imported readings remain distinguishable populations;
callers must name the populations they intend to combine.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FusionContractError(ValueError):
    """Raised when a caller requests an unsafe or ambiguous source fusion."""


class FusionPopulation(StrEnum):
    JOURNAL = "journal"
    CGM = "cgm"
    IMPORT = "import"


GOVERNED_GLUCOSE_FUSION_CONTRACT_ID = "journal-cgm-import-glucose.v1"
_ALLOWED_POPULATIONS = frozenset(FusionPopulation)


@dataclass(frozen=True, slots=True)
class GovernedGlucoseFusionContract:
    """Versioned permission to combine specific glucose source populations.

    The contract is intentionally narrow:
    - Journal is patient-authored manual/voice evidence only;
    - import is persisted imported LogEntry evidence;
    - CGM is normalized session-linked CGMReadingRecord evidence;
    - demo and legacy LogEntry(source="cgm") rows are never admitted;
    - at least one non-Journal population must be explicitly requested.
    """

    requested_populations: frozenset[FusionPopulation]
    contract_id: str = GOVERNED_GLUCOSE_FUSION_CONTRACT_ID
    concept: str = "glucose"
    preserve_cross_source_duplicates: bool = True

    def __post_init__(self) -> None:
        populations = frozenset(self.requested_populations)
        object.__setattr__(self, "requested_populations", populations)

        if self.contract_id != GOVERNED_GLUCOSE_FUSION_CONTRACT_ID:
            raise FusionContractError("unsupported fusion contract_id")
        if self.concept != "glucose":
            raise FusionContractError("V2-C contract only authorizes glucose fusion")
        if not populations:
            raise FusionContractError("requested_populations must not be empty")
        if not all(isinstance(item, FusionPopulation) for item in populations):
            raise FusionContractError(
                "requested_populations must contain FusionPopulation values only"
            )
        if not populations.issubset(_ALLOWED_POPULATIONS):
            raise FusionContractError("unsupported fusion population")
        if FusionPopulation.JOURNAL not in populations:
            raise FusionContractError("Journal population is required")
        if not populations.intersection({FusionPopulation.CGM, FusionPopulation.IMPORT}):
            raise FusionContractError(
                "explicit CGM and/or import population is required for multi-source fusion"
            )
        if not self.preserve_cross_source_duplicates:
            raise FusionContractError(
                "cross-source deduplication is not authorized by V2-C"
            )

    @classmethod
    def journal_with(
        cls,
        *external_populations: FusionPopulation,
    ) -> "GovernedGlucoseFusionContract":
        """Construct an explicit Journal + external-source fusion request."""
        return cls(
            requested_populations=frozenset(
                {FusionPopulation.JOURNAL, *external_populations}
            )
        )
