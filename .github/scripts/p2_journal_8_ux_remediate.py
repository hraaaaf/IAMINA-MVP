from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
EXPECTED = "3fa616e48bface9ae376986ee8b224c1d9c70bb1"
head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED:
    raise SystemExit(f"stale product head: {head}")

widget = ROOT / "frontend/lib/features/journal/widgets/personal_response_section.dart"
text = widget.read_text()
old = "  late Future<PersonalResponseResult?> _future;\n"
new = old + "  bool _showAllPatterns = false;\n"
if new not in text:
    if text.count(old) != 1:
        raise SystemExit("state anchor mismatch")
    text = text.replace(old, new, 1)

old_take = ".take(3)"
new_take = ".take(_showAllPatterns ? 3 : 1)"
if new_take not in text:
    if text.count(old_take) != 1:
        raise SystemExit("pattern count anchor mismatch")
    text = text.replace(old_take, new_take, 1)

anchor = "                Container(\n                  width: double.infinity,\n                  padding: const EdgeInsets.all(12),"
control = '''                if (snapshot.data!.patterns.length > 1)
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: TextButton.icon(
                      onPressed: () {
                        setState(() => _showAllPatterns = !_showAllPatterns);
                      },
                      icon: Icon(
                        _showAllPatterns ? Icons.expand_less : Icons.expand_more,
                        size: 18,
                      ),
                      label: Text(
                        _showAllPatterns
                            ? l10n.personalResponseShowLess
                            : l10n.personalResponseShowMore(
                                snapshot.data!.patterns.length - 1,
                              ),
                      ),
                      style: TextButton.styleFrom(
                        foregroundColor: AminaTheme.primaryTeal,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 6,
                        ),
                        textStyle: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),'''
if control not in text:
    if text.count(anchor) != 1:
        raise SystemExit("disclaimer anchor mismatch")
    text = text.replace(anchor, control, 1)
widget.write_text(text)

translations = {
    "fr": {
        "personalResponseShowMore": "Afficher {count} autres motifs",
        "@personalResponseShowMore": {"placeholders": {"count": {"type": "int"}}},
        "personalResponseShowLess": "Réduire les motifs",
    },
    "en": {
        "personalResponseShowMore": "Show {count} more patterns",
        "@personalResponseShowMore": {"placeholders": {"count": {"type": "int"}}},
        "personalResponseShowLess": "Show fewer patterns",
    },
    "ar": {
        "personalResponseShowMore": "عرض {count} أنماط إضافية",
        "@personalResponseShowMore": {"placeholders": {"count": {"type": "int"}}},
        "personalResponseShowLess": "عرض أنماط أقل",
    },
}
for locale, values in translations.items():
    path = ROOT / f"frontend/lib/l10n/app_{locale}.arb"
    data = json.loads(path.read_text())
    for key, value in values.items():
        if key in data:
            raise SystemExit(f"duplicate localization key: {key}")
        data[key] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

test = ROOT / "frontend/test/features/personal_response_section_test.dart"
text = test.read_text()
anchor = "  testWidgets('AR ready state keeps RTL hierarchy without overflow', (tester) async {"
extra = '''  testWidgets('ready state keeps secondary patterns behind explicit disclosure', (
    tester,
  ) async {
    await tester.pumpWidget(
      _host(locale: const Locale('fr'), result: _readyResult()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Stress signalé'), findsOneWidget);
    expect(find.text('Après déjeuner'), findsNothing);
    expect(find.textContaining('Afficher'), findsOneWidget);

    await tester.tap(find.textContaining('Afficher'));
    await tester.pumpAndSettle();

    expect(find.text('Après déjeuner'), findsNothing);
    expect(find.text('Réduire les motifs'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

'''
# The current fixture has only one pattern, so this test only verifies the no-disclosure path.
# A max-density disclosure test is injected below with a dedicated result.
if extra not in text:
    # Do not inject the unsuitable one-pattern test; use a dedicated fixture instead.
    pass

fixture_anchor = "PersonalResponseResult _insufficientResult() {"
fixture = '''PersonalResponseResult _multiPatternResult() {
  return const PersonalResponseResult(
    status: 'ready',
    dataScope: 'server_synced_logs',
    windowDays: 90,
    totalReadings: 18,
    distinctDays: 10,
    windowMedianGlucoseMgDl: 142,
    minimumObservations: 3,
    minimumDistinctDays: 2,
    confidenceDefinition: 'descriptive only',
    causalityNotice: 'no causality',
    patterns: [
      PersonalResponsePattern(
        key: 'context:stress',
        kind: 'context',
        observations: 8,
        distinctDays: 6,
        medianGlucoseMgDl: 158,
        windowMedianGlucoseMgDl: 142,
        confidence: 'strong',
      ),
      PersonalResponsePattern(
        key: 'meal:lunch',
        kind: 'meal',
        observations: 6,
        distinctDays: 4,
        medianGlucoseMgDl: 151,
        windowMedianGlucoseMgDl: 142,
        confidence: 'moderate',
      ),
      PersonalResponsePattern(
        key: 'context:poor_sleep',
        kind: 'context',
        observations: 3,
        distinctDays: 2,
        medianGlucoseMgDl: 149,
        windowMedianGlucoseMgDl: 142,
        confidence: 'limited',
      ),
    ],
  );
}

'''
if fixture not in text:
    if text.count(fixture_anchor) != 1:
        raise SystemExit("test fixture anchor mismatch")
    text = text.replace(fixture_anchor, fixture + fixture_anchor, 1)

new_test = '''  testWidgets('secondary patterns are collapsed by default and explicitly expandable', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 560);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      _host(locale: const Locale('fr'), result: _multiPatternResult()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Stress signalé'), findsOneWidget);
    expect(find.text('Après déjeuner'), findsNothing);
    expect(find.text('Mauvais sommeil signalé'), findsNothing);
    expect(find.text('Afficher 2 autres motifs'), findsOneWidget);

    await tester.tap(find.text('Afficher 2 autres motifs'));
    await tester.pumpAndSettle();

    expect(find.text('Après déjeuner'), findsOneWidget);
    expect(find.text('Mauvais sommeil signalé'), findsOneWidget);
    expect(find.text('Réduire les motifs'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

'''
if new_test not in text:
    if text.count(anchor) != 1:
        raise SystemExit("test insertion anchor mismatch")
    text = text.replace(anchor, new_test + anchor, 1)
test.write_text(text)
