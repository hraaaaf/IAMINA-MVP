"""
DEPRECATED: import from core.contracts.companion_identity instead.

This module is a backward-compatibility shim retained until P4 wires
DiabetesEngine.analyze() to the chassis contract. All new code must import
CompanionIdentity directly:

    from core.contracts.companion_identity import CompanionIdentity

The DomainContext name is preserved here so existing callsites continue to
work without change during the P0 → P4 transition. It will be removed in P4.

See ADR-0008 for the renaming rationale.
"""
# DEPRECATED: import from core.contracts.companion_identity
from core.contracts.companion_identity import CompanionIdentity as DomainContext

__all__ = ["DomainContext"]
