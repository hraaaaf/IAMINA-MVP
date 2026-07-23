class UnitGuard:
    """
    Unit Guard (Phase 6)
    ===================
    Handles safe conversions between common glucose units.
    Critical for the Moroccan market where patients may use mg/dL, mmol/L or g/L.

    Standard: mg/dL = mmol/L * 18.018
    """

    @staticmethod
    def mg_dl_to_mmol_l(mg_dl: float) -> float:
        """Convert mg/dL to mmol/L (Standard UK/France)."""
        return round(mg_dl / 18.018, 2)

    @staticmethod
    def mmol_l_to_mg_dl(mmol_l: float) -> float:
        """Convert mmol/L to mg/dL (Standard Morocco/US)."""
        return round(mmol_l * 18.018, 1)

    @staticmethod
    def mg_dl_to_g_l(mg_dl: float) -> float:
        """Convert mg/dL to g/L (Common in older French labs)."""
        return round(mg_dl / 100.0, 3)

    @staticmethod
    def g_l_to_mg_dl(g_l: float) -> float:
        """Convert g/L to mg/dL."""
        return round(g_l * 100.0, 1)

    @classmethod
    def normalize_to_mg_dl(cls, value: float, unit: str) -> float:
        """Centralized normalization method to ensure internal consistency."""
        u = unit.lower().strip()
        if u == 'mmol/l':
            return cls.mmol_l_to_mg_dl(value)
        if u == 'g/l':
            return cls.g_l_to_mg_dl(value)
        # Default is mg/dL
        return float(value)
