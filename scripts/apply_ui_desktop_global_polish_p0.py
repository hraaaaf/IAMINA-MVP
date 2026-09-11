from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    return text.replace(old, new, 1)


def matching_paren(text: str, open_idx: int) -> int:
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = open_idx
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if ch == '\n':
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == '*' and nxt == '/':
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == '/' and nxt == '/':
            line_comment = True
            i += 2
            continue
        if ch == '/' and nxt == '*':
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit('unbalanced call while patching Dart source')


def wrap_first_call_after(
    text: str,
    marker: str,
    call: str,
    prefix: str,
    suffix: str,
    label: str,
) -> str:
    marker_idx = text.find(marker)
    if marker_idx < 0:
        raise SystemExit(f'{label}: marker not found')
    call_idx = text.find(call, marker_idx)
    if call_idx < 0:
        raise SystemExit(f'{label}: call not found')
    open_idx = call_idx + call.index('(')
    close_idx = matching_paren(text, open_idx)
    return text[:call_idx] + prefix + text[call_idx : close_idx + 1] + suffix + text[close_idx + 1 :]


# 1) Canonical page header: full-width background, body-aligned content rail.
path = 'frontend/lib/core/widgets/mobile_page_header.dart'
text = read(path)
text = replace_once(
    text,
    '    final dark = AminaTheme.isDark(context);\n',
    "    final dark = AminaTheme.isDark(context);\n"
    "    final surfaceWidth = MediaQuery.sizeOf(context).width;\n"
    "    final desktopInset = surfaceWidth >= 1160\n"
    "        ? (surfaceWidth - 1120) / 2\n"
    "        : 20.0;\n",
    'mobile header desktop inset',
)
text = replace_once(
    text,
    '      padding: EdgeInsetsDirectional.fromSTEB(20, top + 14, 20, 18),',
    '      padding: EdgeInsetsDirectional.fromSTEB(\n        desktopInset,\n        top + 14,\n        desktopInset,\n        18,\n      ),',
    'mobile header chrome padding',
)
text = replace_once(
    text,
    '            padding: const EdgeInsetsDirectional.fromSTEB(20, 0, 20, 14),',
    '            padding: EdgeInsetsDirectional.fromSTEB(\n              desktopInset,\n              0,\n              desktopInset,\n              14,\n            ),',
    'mobile header bottom padding',
)
write(path, text)

# 2) New reading: keep the save bar, stop turning one action into a 1080px runway.
path = 'frontend/lib/features/dashboard/widgets/add_log_sheet.dart'
text = read(path)
text = wrap_first_call_after(
    text,
    'Widget _saveBar(',
    'FilledButton.icon(',
    "SizedBox(\n              width: MediaQuery.sizeOf(context).width >= 1000\n                  ? 300\n                  : double.infinity,\n              child: ",
    ')',
    'add-log save action',
)
write(path, text)

# 3) Document import: make the desktop flow focal and bound its actions.
path = 'frontend/lib/features/documents/document_import_screen.dart'
text = read(path)
text = replace_once(text, '        maxWidth: 980,', '        maxWidth: 760,', 'document import rail')
for call in ('ElevatedButton.icon(', 'OutlinedButton(', 'ElevatedButton('):
    start = 0
    while True:
        idx = text.find(call, start)
        if idx < 0:
            break
        window_start = max(0, idx - 180)
        before = text[window_start:idx]
        token = 'width: double.infinity,'
        width_idx_rel = before.rfind(token)
        if width_idx_rel >= 0:
            width_idx = window_start + width_idx_rel
            between = text[width_idx + len(token):idx]
            if 'child:' in between and 'SizedBox(' in before[width_idx_rel - 60:]:
                text = (
                    text[:width_idx]
                    + 'width: MediaQuery.sizeOf(context).width >= 900 ? 280 : double.infinity,'
                    + text[width_idx + len(token):]
                )
                idx += 40
        start = idx + len(call)
write(path, text)

# 4) Importer: one governed desktop rail, including header alignment.
path = 'frontend/lib/features/import/import_screen.dart'
text = read(path)
text = replace_once(text, '              maxWidth: 1160,', '              maxWidth: 1040,', 'importer rail')
text = wrap_first_call_after(
    text,
    'class _TopBar extends StatelessWidget',
    'Row(',
    'Center(\n        child: ConstrainedBox(\n          constraints: const BoxConstraints(maxWidth: 1040),\n          child: ',
    ')),',
    'importer desktop header rail',
)
write(path, text)

# 5) Medication: bound the desktop canvas and the save action.
path = 'frontend/lib/features/medications/medication_screen.dart'
text = read(path)
text = wrap_first_call_after(
    text,
    'class _MedicationScreenState',
    'ListView(',
    "Align(\n                    alignment: AlignmentDirectional.topCenter,\n                    child: ConstrainedBox(\n                      constraints: const BoxConstraints(maxWidth: 920),\n                      child: ",
    ')),',
    'medication desktop rail',
)
text = replace_once(
    text,
    '                            SizedBox(\n                              height: 48,\n                              child: FilledButton.icon(',
    '                            SizedBox(\n                              width: MediaQuery.sizeOf(context).width >= 900\n                                  ? 260\n                                  : double.infinity,\n                              height: 48,\n                              child: FilledButton.icon(',
    'medication save width',
)
write(path, text)

# 6) Reminders: same desktop discipline as medication.
path = 'frontend/lib/features/reminders/reminders_screen.dart'
text = read(path)
text = wrap_first_call_after(
    text,
    'class _RemindersScreenState',
    'ListView(',
    "Align(\n                    alignment: AlignmentDirectional.topCenter,\n                    child: ConstrainedBox(\n                      constraints: const BoxConstraints(maxWidth: 920),\n                      child: ",
    ')),',
    'reminders desktop rail',
)
text = replace_once(
    text,
    '                            SizedBox(\n                              height: 48,\n                              child: FilledButton.icon(',
    '                            SizedBox(\n                              width: MediaQuery.sizeOf(context).width >= 900\n                                  ? 260\n                                  : double.infinity,\n                              height: 48,\n                              child: FilledButton.icon(',
    'reminder save width',
)
write(path, text)

# 7) Companion: focus loading/error states and govern the full overview rail.
path = 'frontend/lib/features/companion/companion_premium_screen.dart'
text = read(path)
text = wrap_first_call_after(
    text,
    'class _Shell extends StatelessWidget',
    'CustomScrollView(',
    "Align(\n      alignment: AlignmentDirectional.topCenter,\n      child: ConstrainedBox(\n        constraints: const BoxConstraints(maxWidth: 680),\n        child: ",
    ')),',
    'companion state rail',
)
text = wrap_first_call_after(
    text,
    'class _Overview extends StatelessWidget',
    'CustomScrollView(',
    "Align(\n      alignment: AlignmentDirectional.topCenter,\n      child: ConstrainedBox(\n        constraints: const BoxConstraints(maxWidth: 1080),\n        child: ",
    ')),',
    'companion overview rail',
)
segment_start = text.index('class _StateCard extends StatelessWidget')
segment_end = text.index('class _AmbientBackground', segment_start)
segment = text[segment_start:segment_end]
segment = replace_once(
    segment,
    '            SizedBox(\n              width: double.infinity,\n              height: 46,\n              child: FilledButton.icon(',
    '            SizedBox(\n              width: MediaQuery.sizeOf(context).width >= 900\n                  ? 240\n                  : double.infinity,\n              height: 46,\n              child: FilledButton.icon(',
    'companion retry width',
)
text = text[:segment_start] + segment + text[segment_end:]
write(path, text)

# Static guardrail: catches accidental removal of the desktop contract before browser evidence.
test_path = ROOT / 'frontend/test/features/ui_desktop_global_polish_contract_test.dart'
test_path.write_text(
    """import 'dart:io';\n\nimport 'package:flutter_test/flutter_test.dart';\n\nvoid main() {\n  test('global desktop polish keeps bounded rails and actions', () {\n    final header = File('lib/core/widgets/mobile_page_header.dart').readAsStringSync();\n    final addLog = File('lib/features/dashboard/widgets/add_log_sheet.dart').readAsStringSync();\n    final document = File('lib/features/documents/document_import_screen.dart').readAsStringSync();\n    final importer = File('lib/features/import/import_screen.dart').readAsStringSync();\n    final medication = File('lib/features/medications/medication_screen.dart').readAsStringSync();\n    final reminders = File('lib/features/reminders/reminders_screen.dart').readAsStringSync();\n    final companion = File('lib/features/companion/companion_premium_screen.dart').readAsStringSync();\n\n    expect(header, contains('desktopInset'));\n    expect(header, contains('(surfaceWidth - 1120) / 2'));\n    expect(addLog, contains('? 300'));\n    expect(document, contains('maxWidth: 760'));\n    expect(document, contains('? 280 : double.infinity'));\n    expect(importer, contains('maxWidth: 1040'));\n    expect(medication, contains('maxWidth: 920'));\n    expect(medication, contains('? 260'));\n    expect(reminders, contains('maxWidth: 920'));\n    expect(reminders, contains('? 260'));\n    expect(companion, contains('maxWidth: 680'));\n    expect(companion, contains('maxWidth: 1080'));\n    expect(companion, contains('? 240'));\n  });\n}\n""",
    encoding='utf-8',
)

print('Applied UI desktop global P0 polish successfully')
