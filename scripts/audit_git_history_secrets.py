#!/usr/bin/env python3
"""Fail when any reachable Git blob contains a likely credential.

The scanner reports only blob identifiers, paths, line numbers and credential
categories. It never prints matched values. It requires a full Git checkout.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

MAX_TEXT_BYTES = 5 * 1024 * 1024

FORBIDDEN_PATHS = (
    re.compile(r"(^|/)\.claude/settings\.local(?:\..*)?\.json$"),
    re.compile(r"(^|/)firebase-credentials\.json$"),
    re.compile(r"(^|/).*service[-_]account.*\.json$", re.IGNORECASE),
    re.compile(r"(^|/)\.env(?:\..+)?$"),
)

GOOGLE_API_KEY_PATTERN = re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("generic sk token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("Google API key", GOOGLE_API_KEY_PATTERN),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "private key material",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)

PATTERN_PATH_EXCEPTIONS: dict[str, frozenset[str]] = {
    "Google API key": frozenset({"frontend/lib/firebase_options.dart"}),
}

PUBLIC_FIREBASE_COMPILED_PATHS = frozenset({"main.dart.js"})

SAFE_GENERIC_SK_PREFIXES = (
    "sk-example-",
    "sk-placeholder-",
    "sk-not-a-real-",
)
SAFE_GENERIC_SK_EXACT = frozenset(
    {
        "sk-" + "this-must-never-be-in-the-manifest",
    }
)


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            input=input_bytes,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}") from exc


def _is_shallow(repo: Path) -> bool:
    return _git(repo, "rev-parse", "--is-shallow-repository").strip() == b"true"


def _reachable_blob_paths(repo: Path) -> dict[str, set[str]]:
    objects: dict[str, set[str]] = defaultdict(set)
    output = _git(repo, "rev-list", "--objects", "--all")
    for raw_line in output.splitlines():
        decoded = raw_line.decode("utf-8", errors="replace")
        object_id, separator, path = decoded.partition(" ")
        if separator and path:
            objects[object_id].add(path)

    if not objects:
        return {}

    object_ids = sorted(objects)
    check_input = ("\n".join(object_ids) + "\n").encode("ascii")
    metadata = _git(
        repo,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=check_input,
    )
    blobs: dict[str, set[str]] = {}
    for line in metadata.decode("ascii", errors="replace").splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        object_id, object_type, raw_size = parts
        if object_type != "blob":
            continue
        try:
            size = int(raw_size)
        except ValueError:
            continue
        if size <= MAX_TEXT_BYTES:
            blobs[object_id] = objects[object_id]
    return blobs


def _read_blobs(repo: Path, object_ids: list[str]):
    if not object_ids:
        return
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    for object_id in object_ids:
        process.stdin.write(f"{object_id}\n".encode("ascii"))
    process.stdin.close()

    try:
        for expected_id in object_ids:
            header = process.stdout.readline().decode("ascii", errors="replace").strip()
            parts = header.split()
            if len(parts) != 3 or parts[1] != "blob":
                raise RuntimeError(f"unexpected cat-file response for {expected_id}")
            object_id, _, raw_size = parts
            size = int(raw_size)
            content = process.stdout.read(size)
            separator = process.stdout.read(1)
            if separator != b"\n":
                raise RuntimeError(f"invalid cat-file blob terminator for {object_id}")
            yield object_id, content
    finally:
        stderr = process.stderr.read() if process.stderr is not None else b""
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(
                "git cat-file --batch failed: "
                + stderr.decode("utf-8", errors="replace").strip()
            )


def _is_forbidden_path(path: str) -> bool:
    if path == ".env.example" or path.endswith("/.env.example"):
        return False
    return any(pattern.search(path) for pattern in FORBIDDEN_PATHS)


def _pattern_allowed_for_all_paths(label: str, paths: set[str]) -> bool:
    exceptions = PATTERN_PATH_EXCEPTIONS.get(label, frozenset())
    return bool(paths) and all(path in exceptions for path in paths)


def _current_public_google_identifiers(repo: Path) -> frozenset[str]:
    """Return deliberate Firebase client identifiers from the canonical HEAD config.

    FlutterFire client API identifiers are public application metadata. Exact copies
    emitted into the approved compiled web artifact may therefore be ignored, but
    only when the value is anchored in the canonical generated Firebase options at
    HEAD. Missing configuration produces an empty allow-set so the scanner fails
    closed.
    """

    try:
        content = _git(repo, "show", "HEAD:frontend/lib/firebase_options.dart")
    except RuntimeError:
        return frozenset()
    text = content.decode("utf-8", errors="replace")
    return frozenset(match.group(0) for match in GOOGLE_API_KEY_PATTERN.finditer(text))


def _match_is_known_safe_example(label: str, value: str) -> bool:
    if label != "generic sk token":
        return False
    if value in SAFE_GENERIC_SK_EXACT:
        return True
    return any(value.startswith(prefix) for prefix in SAFE_GENERIC_SK_PREFIXES)


def _public_google_copy_allowed(
    value: str,
    paths: set[str],
    public_google_identifiers: frozenset[str],
) -> bool:
    return (
        value in public_google_identifiers
        and bool(paths)
        and all(path in PUBLIC_FIREBASE_COMPILED_PATHS for path in paths)
    )


def scan_text(
    content: bytes,
    paths: set[str],
    *,
    public_google_identifiers: frozenset[str] = frozenset(),
) -> list[tuple[int, str]]:
    if b"\x00" in content:
        return []
    text = content.decode("utf-8", errors="replace")
    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in SECRET_PATTERNS:
            if _pattern_allowed_for_all_paths(label, paths):
                continue
            for match in pattern.finditer(line):
                value = match.group(0)
                if _match_is_known_safe_example(label, value):
                    continue
                if label == "Google API key" and _public_google_copy_allowed(
                    value,
                    paths,
                    public_google_identifiers,
                ):
                    continue
                findings.append((line_number, label))
                break
    return findings


def audit_repository(repo: Path) -> list[str]:
    repo = repo.resolve()
    _git(repo, "rev-parse", "--git-dir")
    if _is_shallow(repo):
        raise RuntimeError("history secret audit requires a full, non-shallow checkout")

    blob_paths = _reachable_blob_paths(repo)
    public_google_identifiers = _current_public_google_identifiers(repo)
    failures: list[str] = []
    forbidden_reported: set[tuple[str, str]] = set()
    for object_id, paths in sorted(blob_paths.items()):
        for path in sorted(paths):
            if _is_forbidden_path(path):
                key = (object_id, path)
                if key not in forbidden_reported:
                    failures.append(
                        f"blob {object_id[:12]} path {path}: forbidden credential/local-secret path"
                    )
                    forbidden_reported.add(key)

    for object_id, content in _read_blobs(repo, sorted(blob_paths)):
        paths = blob_paths[object_id]
        display_path = sorted(paths)[0] if paths else "<unknown>"
        for line_number, label in scan_text(
            content,
            paths,
            public_google_identifiers=public_google_identifiers,
        ):
            failures.append(
                f"blob {object_id[:12]} path {display_path}:{line_number}: likely {label}"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    try:
        failures = audit_repository(args.repo)
    except RuntimeError as exc:
        print(f"Git history secret audit ERROR: {exc}", file=sys.stderr)
        return 2

    if failures:
        print(
            "Git history secret audit FAILED. Potential credential values were not printed.",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(
            "Rotate affected credentials before any history rewrite. Locate commits with "
            "git log --all --find-object=<full-blob-id>.",
            file=sys.stderr,
        )
        return 1

    print("Git history secret audit passed: no known credential patterns in reachable blobs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
