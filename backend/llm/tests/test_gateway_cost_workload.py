from core.contracts.capabilities import Capability
from core.llm_gateway import _workload_for_capability


def test_gateway_maps_capabilities_to_cost_workloads():
    assert _workload_for_capability(Capability.EXPLAIN_APPROVED_DATA) == "conversation"
    assert _workload_for_capability(Capability.SUMMARIZE_APPROVED_DATA) == "summary"
    assert _workload_for_capability(Capability.PREPARE_CLINICIAN_QUESTIONS) == "writing"
    assert _workload_for_capability(Capability.SURFACE_DETERMINISTIC_PATTERN) == "conversation"
