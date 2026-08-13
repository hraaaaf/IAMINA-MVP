from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CorpusEntry:
    case_id: str
    dimension_code: str
    suite_index: int


CORPUS = (
    CorpusEntry("L1", "L", 0),
    CorpusEntry("N1", "N", 2),
    CorpusEntry("F1", "F", 10),
    CorpusEntry("B1", "B", 3),
)


def validate_corpus(entries: tuple[CorpusEntry, ...] = CORPUS) -> None:
    if {entry.dimension_code for entry in entries} != {"L", "N", "F", "B"}:
        raise ValueError("missing dimension")
    ids = tuple(entry.case_id for entry in entries)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate id")
    if any(entry.suite_index < 0 for entry in entries):
        raise ValueError("invalid suite index")
