from typing import Optional

from pydantic import BaseModel, Field


class ClinicalKPIs(BaseModel):
    """
    Pydantic model for clinical KPIs (Phase 6).
    Replaces the legacy AnalyticalKPIs dataclass with strict validation
    and JSON serialization support.
    """
    avg_glucose: Optional[float] = Field(None, description="Mean blood glucose in mg/dL")
    std_dev: Optional[float] = Field(None, description="Standard deviation (variability proxy)")
    cv_pct: Optional[float] = Field(None, ge=0, le=200, description="Coefficient of Variation (%) — target ≤ 36%")
    tir_pct: Optional[float] = Field(None, ge=0, le=100, description="Time In Range (70-180 mg/dL) — target ≥ 70%")
    tar_pct: Optional[float] = Field(None, ge=0, le=100, description="Time Above Range (> 180 mg/dL)")
    tbr_pct: Optional[float] = Field(None, ge=0, le=100, description="Time Below Range (< 70 mg/dL)")
    gmi: Optional[float] = Field(None, description="Estimated HbA1c (ADA formula) %")
    log_count: int = Field(0, ge=0, description="Number of entries analysed")
    days_with_data: int = Field(0, ge=0, description="Distinct calendar days with data")

    @property
    def has_sufficient_data(self) -> bool:
        """Minimum 5 entries required for meaningful KPI computation."""
        return self.log_count >= 5

    @property
    def is_stable(self) -> bool:
        """CV ≤ 36% is the ADA threshold for glycemic stability."""
        return self.cv_pct is not None and self.cv_pct <= 36.0
