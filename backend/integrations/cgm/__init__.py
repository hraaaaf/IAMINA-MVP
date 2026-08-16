"""CGM integration boundary.

Vendor/cloud bridges remain outside IAmina. IAmina consumes a normalized,
read-only CGM feed through provider adapters defined in this package.
"""

from .contracts import CGMProvider, CGMReading, CGMSource, ProviderHealth
from .nightscout import NightscoutCGMProvider, NightscoutConfig

__all__ = [
    "CGMProvider",
    "CGMReading",
    "CGMSource",
    "ProviderHealth",
    "NightscoutCGMProvider",
    "NightscoutConfig",
]
