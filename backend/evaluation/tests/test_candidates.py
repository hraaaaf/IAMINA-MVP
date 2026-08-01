from evaluation.candidates import CANDIDATES, candidates_for
from evaluation.contracts import Modality


def test_candidate_registry_has_unique_names_and_no_implied_approval():
    assert len({candidate.provider for candidate in CANDIDATES}) == len(CANDIDATES)
    assert all(candidate.status == "pending_evidence" for candidate in CANDIDATES)


def test_every_required_modality_has_multiple_candidates():
    for modality in Modality:
        assert len(candidates_for(modality)) >= 2
