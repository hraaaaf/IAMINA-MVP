"""Fail-closed manifest for zero-egress local OCR benchmark execution."""

_LOCAL_OCR_MODALITIES = {"document_ocr", "glucometer_ocr"}


class LocalOCRManifest:
    __slots__ = (
        "engine",
        "model",
        "implementation_version",
        "evidence_source",
        "verified_on",
        "review_due_on",
        "approved_modalities",
        "approved_for_synthetic_benchmark",
    )

    def __init__(
        self,
        *,
        engine: str,
        model: str,
        implementation_version: str,
        evidence_source: str,
        verified_on: object,
        review_due_on: object,
        approved_modalities: tuple[str, ...],
        approved_for_synthetic_benchmark: bool,
    ) -> None:
        self.engine = engine
        self.model = model
        self.implementation_version = implementation_version
        self.evidence_source = evidence_source
        self.verified_on = verified_on
        self.review_due_on = review_due_on
        self.approved_modalities = approved_modalities
        self.approved_for_synthetic_benchmark = approved_for_synthetic_benchmark

    def validate(self, *, today: object) -> None:
        required = {
            "engine": self.engine,
            "model": self.model,
            "implementation_version": self.implementation_version,
            "evidence_source": self.evidence_source,
        }
        missing = tuple(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError(
                "missing local OCR benchmark manifest fields: " + ", ".join(missing)
            )
        if self.verified_on > today:
            raise ValueError("local OCR evidence verification date is in the future")
        if self.review_due_on < today:
            raise ValueError("local OCR evidence is stale")
        approved = set(self.approved_modalities)
        if not approved or not approved.issubset(_LOCAL_OCR_MODALITIES):
            raise ValueError("local OCR modalities must be document/glucometer OCR only")
        if not self.approved_for_synthetic_benchmark:
            raise ValueError("local OCR engine is not approved for synthetic benchmarking")
