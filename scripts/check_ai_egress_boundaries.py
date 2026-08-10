#!/usr/bin/env python3
"""Fail closed on direct LLM/provider callsites outside sanctioned boundaries.

The gate intentionally scans only tracked backend files so generated caches and
local artifacts cannot change CI behavior. Egress checks use Python AST nodes so
comments/imports cannot impersonate an authorization call. Findings report file
paths and rule names only; source contents are never printed.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path, PurePosixPath

LLM_GATEWAY_ALLOWED_EXACT = frozenset(
    {
        "core/llm_gateway.py",
        "llm/factory.py",
        "llm/pipeline.py",
        "diabetes/tests/test_llm_factory.py",
        "ai/api/v1/ai.py",
        "diabetes/services/summary.py",
        "diabetes/services/clinical/engine.py",
        "media/documents/pulper.py",
    }
)
LLM_GATEWAY_ALLOWED_PREFIXES = ("llm/tests/", "core/tests/")

DIRECT_EGRESS_CALLS = frozenset({"get_llm", "genai.Client", "GenerativeModel"})
CENTRAL_AUTHORIZATION_CALLS = frozenset(
    {"assert_ai_egress_allowed", "execute_external_provider_call"}
)


def _git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        if isinstance(exc, FileNotFoundError):
            detail = "git executable is unavailable"
        else:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"cannot enumerate tracked files: {detail}") from exc


def _tracked_backend_files(repo: Path) -> list[Path]:
    output = _git(repo, "ls-files", "-z", "--", "backend")
    files: list[Path] = []
    for raw_path in output.split(b"\x00"):
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8", errors="strict")
        path = repo / relative
        if path.is_file():
            files.append(path)
    return files


def _backend_relative(repo: Path, path: Path) -> str:
    return path.relative_to(repo / "backend").as_posix()


def _read_text(path: Path) -> str | None:
    content = path.read_bytes()
    if b"\x00" in content:
        return None
    return content.decode("utf-8", errors="replace")


def _gateway_path_allowed(relative: str) -> bool:
    if relative in LLM_GATEWAY_ALLOWED_EXACT:
        return True
    return any(relative.startswith(prefix) for prefix in LLM_GATEWAY_ALLOWED_PREFIXES)


def gateway_bypass_findings(repo: Path) -> list[str]:
    findings: list[str] = []
    for path in _tracked_backend_files(repo):
        relative = _backend_relative(repo, path)
        text = _read_text(path)
        if text is None or "get_llm" not in text:
            continue
        if not _gateway_path_allowed(relative):
            findings.append(relative)
    return sorted(findings)


def _egress_path_excluded(relative: str) -> bool:
    posix = PurePosixPath(relative)
    if relative == "llm" or relative.startswith("llm/"):
        return True
    return "tests" in posix.parts or "migrations" in posix.parts


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _is_direct_egress_symbol(symbol: str | None) -> bool:
    if symbol is None:
        return False
    if symbol in DIRECT_EGRESS_CALLS:
        return True
    return symbol.endswith(".GenerativeModel")


def _authorization_symbol(symbol: str | None) -> bool:
    if symbol is None:
        return False
    return symbol in CENTRAL_AUTHORIZATION_CALLS


def _ast_call_symbols(path: Path, text: str) -> tuple[set[str], set[str]]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(
            f"cannot parse tracked Python file {path.as_posix()}: line {exc.lineno}"
        ) from exc

    egress_calls: set[str] = set()
    authorization_calls: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        symbol = _dotted_name(node.func)
        if _is_direct_egress_symbol(symbol):
            assert symbol is not None
            egress_calls.add(symbol)
        if _authorization_symbol(symbol):
            assert symbol is not None
            authorization_calls.add(symbol)
    return egress_calls, authorization_calls


def egress_authorization_findings(repo: Path) -> list[str]:
    findings: list[str] = []
    for path in _tracked_backend_files(repo):
        relative = _backend_relative(repo, path)
        if _egress_path_excluded(relative) or path.suffix != ".py":
            continue
        text = _read_text(path)
        if text is None:
            continue
        egress_calls, authorization_calls = _ast_call_symbols(path, text)
        if not egress_calls:
            continue
        if not authorization_calls:
            findings.append(relative)
    return sorted(findings)


def _report(rule: str, findings: list[str]) -> int:
    if not findings:
        print(f"{rule}: passed")
        return 0
    print(f"{rule}: FAILED", file=sys.stderr)
    for path in findings:
        print(f"- {path}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the script's parent repository)",
    )
    parser.add_argument(
        "--check",
        choices=("gateway", "egress", "all"),
        default="all",
    )
    args = parser.parse_args(argv)
    repo = args.repo.resolve()

    try:
        if args.check == "gateway":
            return _report("LLM gateway anti-bypass", gateway_bypass_findings(repo))
        if args.check == "egress":
            return _report(
                "AI egress authorization anti-bypass",
                egress_authorization_findings(repo),
            )

        gateway = gateway_bypass_findings(repo)
        egress = egress_authorization_findings(repo)
    except (OSError, RuntimeError, UnicodeDecodeError, ValueError) as exc:
        print(f"AI boundary gate ERROR: {exc}", file=sys.stderr)
        return 2

    result = 0
    result |= _report("LLM gateway anti-bypass", gateway)
    result |= _report("AI egress authorization anti-bypass", egress)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
