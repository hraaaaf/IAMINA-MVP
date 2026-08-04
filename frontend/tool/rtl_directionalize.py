#!/usr/bin/env python3
"""Convert physical Flutter layout primitives to directional equivalents.

The codemod is deliberately scoped to the screen registry certified by
`test/rtl_screen_contract_test.dart`. It is idempotent and exits non-zero if a
known physical primitive remains after rewriting.
"""

from __future__ import annotations

import re
from pathlib import Path

TARGETS = (
    "lib/features/auth/login_screen.dart",
    "lib/features/auth/reset_password_screen.dart",
    "lib/features/auth/consent_screen.dart",
    "lib/features/auth/onboarding_chat_screen.dart",
    "lib/features/profile/profile_screen.dart",
    "lib/features/dashboard/dashboard_screen.dart",
    "lib/features/journal/ai_summary_screen.dart",
    "lib/features/journal/journal_screen.dart",
    "lib/features/import/import_screen.dart",
    "lib/features/journal/add_log_screen.dart",
    "lib/features/documents/document_import_screen.dart",
    "lib/features/journal/edit_log_screen.dart",
    "lib/features/navigation/main_shell.dart",
)

LITERAL_REPLACEMENTS = {
    "EdgeInsets.fromLTRB(": "EdgeInsetsDirectional.fromSTEB(",
    "Alignment.centerLeft": "AlignmentDirectional.centerStart",
    "Alignment.centerRight": "AlignmentDirectional.centerEnd",
    "Alignment.topLeft": "AlignmentDirectional.topStart",
    "Alignment.topRight": "AlignmentDirectional.topEnd",
    "Alignment.bottomLeft": "AlignmentDirectional.bottomStart",
    "Alignment.bottomRight": "AlignmentDirectional.bottomEnd",
    "TextAlign.left": "TextAlign.start",
    "TextAlign.right": "TextAlign.end",
}

REMAINING_PATTERNS = (
    re.compile(r"EdgeInsets\.only\s*\([^)]*\b(?:left|right)\s*:", re.DOTALL),
    re.compile(r"EdgeInsets\.fromLTRB\s*\("),
    re.compile(
        r"Alignment\.(?:centerLeft|centerRight|topLeft|topRight|bottomLeft|bottomRight)\b"
    ),
    re.compile(r"TextAlign\.(?:left|right)\b"),
    re.compile(r"Positioned\s*\([^)]*\b(?:left|right)\s*:", re.DOTALL),
    re.compile(
        r"BorderRadius\.only\s*\([^)]*\b(?:topLeft|topRight|bottomLeft|bottomRight)\s*:",
        re.DOTALL,
    ),
)


def _matching_paren(source: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    index = open_index
    while index < len(source):
        char = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError(f"unbalanced call beginning at offset {open_index}")


def _rewrite_calls(
    source: str,
    *,
    call_name: str,
    replacement_name: str,
    argument_map: dict[str, str],
) -> str:
    needle = f"{call_name}("
    cursor = 0
    output: list[str] = []
    while True:
        start = source.find(needle, cursor)
        if start < 0:
            output.append(source[cursor:])
            break
        open_index = start + len(call_name)
        close_index = _matching_paren(source, open_index)
        body = source[open_index + 1 : close_index]
        contains_physical_argument = any(
            re.search(rf"\b{re.escape(argument)}\s*:", body)
            for argument in argument_map
        )
        output.append(source[cursor:start])
        if contains_physical_argument:
            for physical, directional in argument_map.items():
                body = re.sub(
                    rf"\b{re.escape(physical)}(\s*:)",
                    rf"{directional}\1",
                    body,
                )
            output.append(f"{replacement_name}({body})")
        else:
            output.append(source[start : close_index + 1])
        cursor = close_index + 1
    return "".join(output)


def rewrite(source: str) -> str:
    for physical, directional in LITERAL_REPLACEMENTS.items():
        source = source.replace(physical, directional)
    source = _rewrite_calls(
        source,
        call_name="EdgeInsets.only",
        replacement_name="EdgeInsetsDirectional.only",
        argument_map={"left": "start", "right": "end"},
    )
    source = _rewrite_calls(
        source,
        call_name="BorderRadius.only",
        replacement_name="BorderRadiusDirectional.only",
        argument_map={
            "topLeft": "topStart",
            "topRight": "topEnd",
            "bottomLeft": "bottomStart",
            "bottomRight": "bottomEnd",
        },
    )
    source = _rewrite_calls(
        source,
        call_name="Positioned",
        replacement_name="PositionedDirectional",
        argument_map={"left": "start", "right": "end"},
    )
    return source


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    changed: list[str] = []
    failures: list[str] = []
    for relative in TARGETS:
        path = root / relative
        original = path.read_text(encoding="utf-8")
        updated = rewrite(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(relative)
        for pattern in REMAINING_PATTERNS:
            if pattern.search(updated):
                failures.append(f"{relative}: {pattern.pattern}")
    if failures:
        raise SystemExit("RTL codemod left physical primitives:\n" + "\n".join(failures))
    print(f"Directionalized {len(changed)} screen files")


if __name__ == "__main__":
    main()
