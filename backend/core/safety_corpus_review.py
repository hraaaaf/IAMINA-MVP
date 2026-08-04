"""Fingerprint, export and audit the restricted native safety review manifest.

The corpus contains synthetic safety phrases only. Reviewer identities, signed
approvals and private evidence remain outside Git and are referenced by opaque
identifiers. Missing, stale, partial or fingerprint-mismatched review evidence
fails closed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from core.safety_corpora import SafetyCorpusCase, all_safety_corpus_cases

SCHEMA_VERSION = "2026-08-04.1"
APPROVED = "approved"
REJECTED = "rejected"
REQUIRED_LOCALES = frozenset({"fr", "ar", "en", "ar-MA"})

_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "corpus_fingerprint",
        "source_commit_sha",
        "review_batch_reference",
        "clinical_approval_reference",
        "safety_owner_approval_reference",
        "reviewed_on",
        "review_due_on",
        "locale_reviews",
        "case_reviews",
        "parity_reviews",
    }
)
_LOCALE_REVIEW_KEYS = frozenset(
    {
        "locale",
        "native_reviewer_reference",
        "qualification_reference",
        "decision",
    }
)
_CASE_REVIEW_KEYS = frozenset(
    {
        "case_id",
        "native_decision",
        "clinical_decision",
        "issue_reference",
    }
)
_PARITY_REVIEW_KEYS = frozenset(
    {
        "locale",
        "channel",
        "input_form",
        "reviewer_reference",
        "decision",
    }
)
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}$")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d .()-]{7,}\d(?!\w)")


@dataclass(frozen=True, slots=True)
class LocaleReview:
    locale: str
    native_reviewer_reference: str
    qualification_reference: str
    decision: str


@dataclass(frozen=True, slots=True)
class CaseReview:
    case_id: str
    native_decision: str
    clinical_decision: str
    issue_reference: str


@dataclass(frozen=True, slots=True)
class ParityReview:
    locale: str
    channel: str
    input_form: str
    reviewer_reference: str
    decision: str


@dataclass(frozen=True, slots=True)
class SafetyReviewManifest:
    schema_version: str
    corpus_fingerprint: str
    source_commit_sha: str
    review_batch_reference: str
    clinical_approval_reference: str
    safety_owner_approval_reference: str
    reviewed_on: date
    review_due_on: date
    locale_reviews: tuple[LocaleReview, ...]
    case_reviews: tuple[CaseReview, ...]
    parity_reviews: tuple[ParityReview, ...]

    def validate(self, *, today: date) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported native-review manifest schema version")
        expected_fingerprint = safety_corpus_fingerprint()
        if self.corpus_fingerprint != expected_fingerprint:
            raise ValueError("native-review manifest corpus fingerprint mismatch")
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_commit_sha):
            raise ValueError("native-review source_commit_sha must be a full Git SHA")
        for label, reference in (
            ("review_batch_reference", self.review_batch_reference),
            ("clinical_approval_reference", self.clinical_approval_reference),
            ("safety_owner_approval_reference", self.safety_owner_approval_reference),
        ):
            _validate_reference(reference, label=label)
        if self.reviewed_on > today:
            raise ValueError("native-review date is in the future")
        if self.review_due_on < today:
            raise ValueError("native-review manifest is stale")
        if self.review_due_on < self.reviewed_on:
            raise ValueError("native-review due date precedes review date")

        locale_map: dict[str, LocaleReview] = {}
        for review in self.locale_reviews:
            if review.locale in locale_map:
                raise ValueError(f"duplicate locale review: {review.locale}")
            if review.locale not in REQUIRED_LOCALES:
                raise ValueError(f"unexpected locale review: {review.locale}")
            _validate_reference(
                review.native_reviewer_reference,
                label=f"{review.locale}.native_reviewer_reference",
            )
            _validate_reference(
                review.qualification_reference,
                label=f"{review.locale}.qualification_reference",
            )
            _validate_decision(review.decision, label=f"{review.locale}.decision")
            locale_map[review.locale] = review
        if set(locale_map) != set(REQUIRED_LOCALES):
            missing = sorted(REQUIRED_LOCALES - set(locale_map))
            raise ValueError(f"native-review locale coverage incomplete: {missing}")

        expected_cases = {case.case_id for case in all_safety_corpus_cases()}
        case_map: dict[str, CaseReview] = {}
        for review in self.case_reviews:
            if review.case_id in case_map:
                raise ValueError(f"duplicate case review: {review.case_id}")
            if review.case_id not in expected_cases:
                raise ValueError(f"unexpected case review: {review.case_id}")
            _validate_decision(
                review.native_decision,
                label=f"{review.case_id}.native_decision",
            )
            _validate_decision(
                review.clinical_decision,
                label=f"{review.case_id}.clinical_decision",
            )
            if review.issue_reference:
                _validate_reference(
                    review.issue_reference,
                    label=f"{review.case_id}.issue_reference",
                )
            case_map[review.case_id] = review
        if set(case_map) != expected_cases:
            missing = sorted(expected_cases - set(case_map))
            extra = sorted(set(case_map) - expected_cases)
            raise ValueError(
                f"native-review case coverage incomplete; missing={missing}, extra={extra}"
            )

        expected_parity = required_parity_dimensions()
        parity_map: dict[tuple[str, str, str], ParityReview] = {}
        for review in self.parity_reviews:
            key = (review.locale, review.channel, review.input_form)
            if key in parity_map:
                raise ValueError(f"duplicate parity review: {key}")
            if key not in expected_parity:
                raise ValueError(f"unexpected parity review: {key}")
            _validate_reference(
                review.reviewer_reference,
                label=f"parity.{review.locale}.{review.channel}.{review.input_form}",
            )
            _validate_decision(review.decision, label=f"parity.{key}")
            parity_map[key] = review
        if set(parity_map) != expected_parity:
            missing = sorted(expected_parity - set(parity_map))
            raise ValueError(f"native-review parity coverage incomplete: {missing}")

    def blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        blockers.extend(
            f"locale:{review.locale}:{review.decision}"
            for review in self.locale_reviews
            if review.decision != APPROVED
        )
        blockers.extend(
            f"case:{review.case_id}:native:{review.native_decision}"
            for review in self.case_reviews
            if review.native_decision != APPROVED
        )
        blockers.extend(
            f"case:{review.case_id}:clinical:{review.clinical_decision}"
            for review in self.case_reviews
            if review.clinical_decision != APPROVED
        )
        blockers.extend(
            f"parity:{review.locale}:{review.channel}:{review.input_form}:{review.decision}"
            for review in self.parity_reviews
            if review.decision != APPROVED
        )
        return tuple(sorted(blockers))


def _validate_reference(reference: str, *, label: str) -> None:
    if not _REFERENCE_RE.fullmatch(reference):
        raise ValueError(f"{label} must be an opaque evidence reference")
    if _EMAIL_RE.search(reference) or _PHONE_RE.search(reference):
        raise ValueError(f"{label} must not contain direct reviewer contact data")


def _validate_decision(decision: str, *, label: str) -> None:
    if decision not in {APPROVED, REJECTED}:
        raise ValueError(f"{label} must be approved or rejected")


def _case_payload(case: SafetyCorpusCase) -> dict[str, str]:
    return {
        "case_id": case.case_id,
        "locale": case.locale,
        "channel": case.channel,
        "input_form": case.input_form,
        "text": case.text,
        "expected": case.expected.value,
        "review_scope": case.review_scope,
    }


def safety_corpus_packet_payload() -> dict[str, object]:
    cases = [_case_payload(case) for case in all_safety_corpus_cases()]
    return {
        "schema_version": SCHEMA_VERSION,
        "corpus_fingerprint": safety_corpus_fingerprint(cases=cases),
        "required_locales": sorted(REQUIRED_LOCALES),
        "required_parity_dimensions": [
            {
                "locale": locale,
                "channel": channel,
                "input_form": input_form,
            }
            for locale, channel, input_form in sorted(required_parity_dimensions())
        ],
        "case_count": len(cases),
        "cases": cases,
        "instructions": {
            "native_review": "Assess meaning, naturalness, severity and dangerous ambiguity.",
            "clinical_review": "Confirm the expected high-severity classification is appropriate.",
            "parity_review": "Compare behavior across channel, script and transliteration dimensions.",
            "privacy": "Use opaque reviewer and evidence references; do not add names or contact data.",
        },
    }


def safety_corpus_fingerprint(*, cases: list[dict[str, str]] | None = None) -> str:
    canonical_cases = cases or [_case_payload(case) for case in all_safety_corpus_cases()]
    canonical = json.dumps(
        canonical_cases,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def required_parity_dimensions() -> set[tuple[str, str, str]]:
    return {
        (case.locale, case.channel, case.input_form)
        for case in all_safety_corpus_cases()
    }


def write_safety_corpus_packet(path: str | os.PathLike[str]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        safety_corpus_packet_payload(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
        os.replace(temporary, destination)
        os.chmod(destination, 0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _exact_keys(payload: dict, expected: frozenset[str], *, label: str) -> None:
    actual = set(payload)
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        extra = sorted(actual - set(expected))
        raise ValueError(f"{label} keys invalid; missing={missing}, extra={extra}")


def _parse_date(value: object, *, label: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date") from exc


def _parse_manifest(payload: object) -> SafetyReviewManifest:
    if not isinstance(payload, dict):
        raise ValueError("native-review manifest root must be an object")
    _exact_keys(payload, _MANIFEST_KEYS, label="manifest")

    locale_reviews_raw = payload["locale_reviews"]
    case_reviews_raw = payload["case_reviews"]
    parity_reviews_raw = payload["parity_reviews"]
    if not isinstance(locale_reviews_raw, list):
        raise ValueError("manifest.locale_reviews must be a list")
    if not isinstance(case_reviews_raw, list):
        raise ValueError("manifest.case_reviews must be a list")
    if not isinstance(parity_reviews_raw, list):
        raise ValueError("manifest.parity_reviews must be a list")

    locale_reviews: list[LocaleReview] = []
    for index, item in enumerate(locale_reviews_raw):
        if not isinstance(item, dict):
            raise ValueError(f"locale_reviews[{index}] must be an object")
        _exact_keys(item, _LOCALE_REVIEW_KEYS, label=f"locale_reviews[{index}]")
        locale_reviews.append(
            LocaleReview(
                locale=str(item["locale"]),
                native_reviewer_reference=str(item["native_reviewer_reference"]),
                qualification_reference=str(item["qualification_reference"]),
                decision=str(item["decision"]),
            )
        )

    case_reviews: list[CaseReview] = []
    for index, item in enumerate(case_reviews_raw):
        if not isinstance(item, dict):
            raise ValueError(f"case_reviews[{index}] must be an object")
        _exact_keys(item, _CASE_REVIEW_KEYS, label=f"case_reviews[{index}]")
        case_reviews.append(
            CaseReview(
                case_id=str(item["case_id"]),
                native_decision=str(item["native_decision"]),
                clinical_decision=str(item["clinical_decision"]),
                issue_reference=str(item["issue_reference"]),
            )
        )

    parity_reviews: list[ParityReview] = []
    for index, item in enumerate(parity_reviews_raw):
        if not isinstance(item, dict):
            raise ValueError(f"parity_reviews[{index}] must be an object")
        _exact_keys(item, _PARITY_REVIEW_KEYS, label=f"parity_reviews[{index}]")
        parity_reviews.append(
            ParityReview(
                locale=str(item["locale"]),
                channel=str(item["channel"]),
                input_form=str(item["input_form"]),
                reviewer_reference=str(item["reviewer_reference"]),
                decision=str(item["decision"]),
            )
        )

    return SafetyReviewManifest(
        schema_version=str(payload["schema_version"]),
        corpus_fingerprint=str(payload["corpus_fingerprint"]),
        source_commit_sha=str(payload["source_commit_sha"]),
        review_batch_reference=str(payload["review_batch_reference"]),
        clinical_approval_reference=str(payload["clinical_approval_reference"]),
        safety_owner_approval_reference=str(payload["safety_owner_approval_reference"]),
        reviewed_on=_parse_date(payload["reviewed_on"], label="reviewed_on"),
        review_due_on=_parse_date(payload["review_due_on"], label="review_due_on"),
        locale_reviews=tuple(locale_reviews),
        case_reviews=tuple(case_reviews),
        parity_reviews=tuple(parity_reviews),
    )


def load_safety_review_manifest(path: str | os.PathLike[str]) -> SafetyReviewManifest:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ValueError("native-review manifest file does not exist")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("native-review manifest is unreadable or invalid JSON") from exc
    return _parse_manifest(payload)


def native_review_readiness_payload(
    *,
    manifest_path: str | os.PathLike[str] | None = None,
    today: date | None = None,
    require_approved: bool = False,
) -> dict[str, object]:
    current = today or date.today()
    selected_path = manifest_path or os.environ.get("SAFETY_CORPUS_REVIEW_MANIFEST_PATH", "")
    packet = safety_corpus_packet_payload()
    if not selected_path:
        blocker = "restricted_native_review_manifest_missing"
        if require_approved:
            raise ValueError(f"native safety review is not approved: {blocker}")
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "pending_native_review",
            "corpus_fingerprint": packet["corpus_fingerprint"],
            "case_count": packet["case_count"],
            "required_locales": packet["required_locales"],
            "required_parity_dimensions": packet["required_parity_dimensions"],
            "blockers": [blocker],
            "non_claim": "Automated classifier parity is not native or clinical approval.",
        }

    manifest = load_safety_review_manifest(selected_path)
    manifest.validate(today=current)
    blockers = list(manifest.blockers())
    if require_approved and blockers:
        raise ValueError("native safety review is not approved: " + ", ".join(blockers))
    return {
        "schema_version": manifest.schema_version,
        "status": "approved" if not blockers else "review_rejected",
        "corpus_fingerprint": manifest.corpus_fingerprint,
        "source_commit_sha": manifest.source_commit_sha,
        "review_batch_reference": manifest.review_batch_reference,
        "reviewed_on": manifest.reviewed_on.isoformat(),
        "review_due_on": manifest.review_due_on.isoformat(),
        "locale_reviews": [asdict(review) for review in manifest.locale_reviews],
        "case_count": len(manifest.case_reviews),
        "parity_review_count": len(manifest.parity_reviews),
        "blockers": blockers,
        "non_claim": (
            "Manifest validation proves recorded approvals for the exact corpus fingerprint; "
            "it does not disclose reviewer identity or private evidence."
        ),
    }
