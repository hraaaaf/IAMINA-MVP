#!/usr/bin/env python3
"""Fail CI when tracked files contain likely credentials or forbidden local-secret files.

This scanner is intentionally dependency-free so it can run immediately after
checkout, before installing application dependencies. It reports only file/line
and pattern type — never the matched secret value.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 5 * 1024 * 1024

FORBIDDEN_TRACKED_PATHS = (
    re.compile(r"(^|/)\.claude/settings\.local(?:\..*)?\.json$"),
    re.compile(r"(^|/)firebase-credentials\.json$"),
    re.compile(r"(^|/).*service[-_]account.*\.json$", re.IGNORECASE),
    re.compile(r"(^|/)\.env(?:\..+)?$"),
)

# High-signal credential formats only. Generic passwords are deliberately not
# guessed here because that creates noisy false positives; provider-specific
# patterns plus forbidden credential files cover the P0 incident class.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("generic sk token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "private key material",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)

# Only explicit, non-secret examples may be allow-listed. Never add a real token
# or a prefix copied from a real token here.
SAFE_EXAMPLE_FRAGMENTS = (
    "sk-example-",
    "sk-placeholder-",
    "sk-not-a-real-",
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def is_forbidden_path(path: str) -> bool:
    if path == ".env.example" or path.endswith("/.env.example"):
        return False
    return any(pattern.search(path) for pattern in FORBIDDEN_TRACKED_PATHS)


def scan_file(path: str) -> list[tuple[int, str]]:
    absolute = ROOT / path
    try:
        data = absolute.read_bytes()
    except OSError:
        return []
    if len(data) > MAX_TEXT_BYTES or b"\x00" in data:
        return []

    text = data.decode("utf-8", errors="replace")
    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(fragment in line for fragment in SAFE_EXAMPLE_FRAGMENTS):
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((line_number, label))
    return findings


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        if is_forbidden_path(path):
            failures.append(f"{path}: forbidden credential/local-secret file is tracked")
            continue
        for line_number, label in scan_file(path):
            failures.append(f"{path}:{line_number}: likely {label}")

    if failures:
        print("Secret hygiene gate FAILED. Potential credentials were not printed.", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(
            "Remove/rotate the credential. Do not solve this by allow-listing a real secret.",
            file=sys.stderr,
        )
        return 1

    print("Secret hygiene gate passed: no forbidden tracked files or known token patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
