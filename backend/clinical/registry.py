"""
DetectorRegistry — generic pattern-detector registry for the engine.

The capsule registers its domain-specific detector functions here.
The engine calls run_all() instead of maintaining a hardcoded list.
"""
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)


class DetectorRegistry:
    """Ordered collection of callable detectors."""

    def __init__(self):
        self._detectors: List[Callable] = []

    def register(self, fn: Callable) -> Callable:
        """Register a decorator or plain call."""
        self._detectors.append(fn)
        return fn

    def run_all(self, entries) -> list:
        """Run every registered detector; silently skip failures."""
        results = []
        for fn in self._detectors:
            try:
                result = fn(entries)
                if result:
                    results.append(result)
            except Exception:
                logger.warning("DetectorRegistry: %s failed", fn.__name__, exc_info=True)
        return results
