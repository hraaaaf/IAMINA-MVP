from pathlib import Path

p = Path('frontend/lib/features/dashboard/dashboard_screen.dart')
s = p.read_text()
old = """            SizedBox(height: compactHeight ? 12 : 18),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AminaTheme.teal50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AminaTheme.teal100),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.verified_user_outlined, size: 17, color: AminaTheme.teal700),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      l10n.firstUseTruthNote,
                      style: const TextStyle(fontSize: 12, height: 1.4, color: AminaTheme.teal700),
                    ),
                  ),
                ],
              ),
            ),
"""
new = """            if (!compactHeight) ...[
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AminaTheme.teal50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AminaTheme.teal100),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.verified_user_outlined, size: 17, color: AminaTheme.teal700),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        l10n.firstUseTruthNote,
                        style: const TextStyle(fontSize: 12, height: 1.4, color: AminaTheme.teal700),
                      ),
                    ),
                  ],
                ),
              ),
            ],
"""
assert old in s
p.write_text(s.replace(old, new, 1))

t = Path('frontend/test/p0_ux_11_first_use_dashboard_contract_test.dart')
ts = t.read_text()
needle = "    expect(source, contains('compactHeight'));\n"
assert needle in ts
ts = ts.replace(needle, needle + "    expect(source, contains('if (!compactHeight)'));\n", 1)
t.write_text(ts)
