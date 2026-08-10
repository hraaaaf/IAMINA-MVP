#!/usr/bin/env python3
"""Fail closed on direct LLM/provider callsites outside sanctioned boundaries.

The gate intentionally scans only tracked backend files so generated caches and
local artifacts cannot change CI behavior. Egress checks use Python AST nodes and
lexical scopes so comments, imports, or an authorized sibling function cannot
impersonate authorization for a direct provider call. Findings report file paths
and rule names only; source contents are never printed.
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

# `GatewayLLM.__init__` only acquires the provider object. It performs no provider
# request; complete/stream/think are separately guarded at the gateway boundary.
# Keep this exemption symbol- and scope-specific so another get_llm callsite cannot
# inherit it by sharing the file or class.
GET_LLM_FACTORY_ONLY_SCOPES = frozenset(
    {("core/llm_gateway.py", ("GatewayLLM", "__init__"))}
)

CENTRAL_RUNTIME_RELATIVE = "llm/runtime.py"
CENTRAL_RUNTIME_FUNCTION = "execute_external_provider_call"
CENTRAL_RUNTIME_REQUIRED_CONTROLS = frozenset(
    {"assert_ai_egress_allowed", "authorize_processor_policy"}
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


class _LexicalEgressVisitor(ast.NodeVisitor):
    """Track egress and authorization calls independently per lexical scope."""

    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self._scope_stack: list[dict[str, bool]] = [
            {"egress": False, "authorization": False}
        ]
        self._scope_names: list[str] = []
        self.unsafe_scope_found = False
        self.central_wrapper_used = False

    @property
    def _scope(self) -> dict[str, bool]:
        return self._scope_stack[-1]

    def _enter_scope(self, body: list[ast.stmt] | ast.expr, name: str) -> None:
        self._scope_stack.append({"egress": False, "authorization": False})
        self._scope_names.append(name)
        if isinstance(body, list):
            for statement in body:
                self.visit(statement)
        else:
            self.visit(body)
        self._scope_names.pop()
        scope = self._scope_stack.pop()
        if scope["egress"] and not scope["authorization"]:
            self.unsafe_scope_found = True

    def _factory_only_get_llm_allowed(self, symbol: str | None) -> bool:
        if symbol != "get_llm":
            return False
        return (
            self.relative_path,
            tuple(self._scope_names),
        ) in GET_LLM_FACTORY_ONLY_SCOPES

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - ast API name
        symbol = _dotted_name(node.func)
        if _is_direct_egress_symbol(symbol) and not self._factory_only_get_llm_allowed(
            symbol
        ):
            self._scope["egress"] = True
        if _authorization_symbol(symbol):
            self._scope["authorization"] = True
        if symbol == CENTRAL_RUNTIME_FUNCTION:
            self.central_wrapper_used = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        # Decorators/defaults execute in the enclosing scope; the function body is a
        # separate lexical scope.
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        self._enter_scope(node.body, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.visit_FunctionDef(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        self._enter_scope(node.body, "<lambda>")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        # Bases, keywords and decorators execute in the enclosing scope. The class
        # body gets its own scope; methods create nested scopes from there.
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        self._enter_scope(node.body, node.name)

    def finalize(self) -> tuple[bool, bool]:
        module_scope = self._scope_stack[0]
        if module_scope["egress"] and not module_scope["authorization"]:
            self.unsafe_scope_found = True
        return self.unsafe_scope_found, self.central_wrapper_used


def _analyze_egress_scopes(path: Path, relative: str, text: str) -> tuple[bool, bool]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(
            f"cannot parse tracked Python file {path.as_posix()}: line {exc.lineno}"
        ) from exc

    visitor = _LexicalEgressVisitor(relative)
    visitor.visit(tree)
    return visitor.finalize()


def _top_level_expression(statement: ast.stmt) -> ast.expr | None:
    if isinstance(statement, ast.Expr):
        return statement.value
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    if isinstance(statement, ast.Return):
        return statement.value
    return None


def _calls_in_expression(expression: ast.expr) -> list[ast.Call]:
    calls: list[ast.Call] = []

    class ExpressionVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            calls.append(node)
            self.generic_visit(node)

        def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
            # A deferred lambda body is not executed before provider submission.
            return

    ExpressionVisitor().visit(expression)
    return calls


def _central_runtime_wrapper_valid(path: Path, text: str) -> bool:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(
            f"cannot parse central runtime {path.as_posix()}: line {exc.lineno}"
        ) from exc

    wrapper = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == CENTRAL_RUNTIME_FUNCTION
        ),
        None,
    )
    if wrapper is None:
        return False

    control_indices: dict[str, int] = {}
    submit_indices: list[int] = []
    for index, statement in enumerate(wrapper.body):
        expression = _top_level_expression(statement)
        if expression is None:
            continue

        # Required controls must be unconditional top-level call statements or
        # assignments, not calls hidden in a branch/try/nested function.
        if isinstance(expression, ast.Call):
            direct_symbol = _dotted_name(expression.func)
            if direct_symbol in CENTRAL_RUNTIME_REQUIRED_CONTROLS:
                control_indices.setdefault(direct_symbol, index)

        for call in _calls_in_expression(expression):
            symbol = _dotted_name(call.func)
            if symbol is not None and symbol.endswith(".submit"):
                submit_indices.append(index)

    if set(control_indices) != CENTRAL_RUNTIME_REQUIRED_CONTROLS:
        return False
    if not submit_indices:
        return False
    return max(control_indices.values()) < min(submit_indices)


def egress_authorization_findings(repo: Path) -> list[str]:
    tracked_files = _tracked_backend_files(repo)
    findings: list[str] = []
    central_wrapper_used = False

    for path in tracked_files:
        relative = _backend_relative(repo, path)
        if _egress_path_excluded(relative) or path.suffix != ".py":
            continue
        text = _read_text(path)
        if text is None:
            continue
        unsafe_scope, wrapper_used = _analyze_egress_scopes(path, relative, text)
        central_wrapper_used |= wrapper_used
        if unsafe_scope:
            findings.append(relative)

    if central_wrapper_used:
        runtime_path = repo / "backend" / CENTRAL_RUNTIME_RELATIVE
        tracked_runtime = any(path == runtime_path for path in tracked_files)
        runtime_text = _read_text(runtime_path) if tracked_runtime else None
        if (
            not tracked_runtime
            or runtime_text is None
            or not _central_runtime_wrapper_valid(runtime_path, runtime_text)
        ):
            findings.append(CENTRAL_RUNTIME_RELATIVE)

    return sorted(set(findings))


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
