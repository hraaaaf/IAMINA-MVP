from __future__ import annotations

import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
add_log = root / 'frontend/lib/features/dashboard/widgets/add_log_sheet.dart'
tests = root / 'frontend/test/features/add_log_sheet_test.dart'

text = add_log.read_text()

old = "import '../../journal/widgets/insulin_logging.dart';\n"
new = old + "import '../../journal/widgets/post_save_receipt.dart';\n"
if text.count(old) != 1:
    raise SystemExit('import anchor mismatch')
text = text.replace(old, new, 1)

old = "  bool _badSleep = false;\n\n  static const List<String> _glycemicContexts"
new = "  bool _badSleep = false;\n  PostSaveReceiptData? _savedReceipt;\n\n  static const List<String> _glycemicContexts"
if text.count(old) != 1:
    raise SystemExit('receipt state anchor mismatch')
text = text.replace(old, new, 1)

old = "    final isDesktop = MediaQuery.sizeOf(context).width >= 1000;\n\n    return PopScope("
new = """    final isDesktop = MediaQuery.sizeOf(context).width >= 1000;\n\n    final savedReceipt = _savedReceipt;\n    if (savedReceipt != null) {\n      return PostSaveReceipt(\n        key: const Key('post-save-receipt'),\n        data: savedReceipt,\n        onViewJournal: _openJournal,\n        onAddAnother: () => setState(() => _savedReceipt = null),\n        onDone: _close,\n      );\n    }\n\n    return PopScope("""
if text.count(old) != 1:
    raise SystemExit('build anchor mismatch')
text = text.replace(old, new, 1)

old = """      if (!mounted) return;\n      HapticFeedback.mediumImpact();\n      _message(l10n.journalSaved);\n      _close();\n    } finally {\n      if (mounted) setState(() => _saving = false);\n    }\n  }\n\n  void _message(String text) {"""
new = """      final receipt = PostSaveReceiptData(\n        glucose: glucose,\n        unit: unit,\n        timeLabel: _timeLabel(l10n),\n        measurementContextLabel: _glycemicContext == null\n            ? null\n            : _contextLabel(l10n, _glycemicContext!),\n        mealTypeLabel: _mealType == null ? null : _mealLabel(l10n, _mealType!),\n        insulinUnits: insulin,\n        additionalContextLabels: <String>[\n          if (_isSick) l10n.journalSick,\n          if (_isStressed) l10n.journalUnusualStress,\n          if (_isActive) l10n.journalPhysicalActivity,\n          if (_badSleep) l10n.journalPoorSleep,\n        ],\n      );\n\n      if (!mounted) return;\n      HapticFeedback.mediumImpact();\n      _clearDraftForNextEntry();\n      setState(() => _savedReceipt = receipt);\n    } finally {\n      if (mounted) setState(() => _saving = false);\n    }\n  }\n\n  void _clearDraftForNextEntry() {\n    _glucoseController.clear();\n    _insulinController.clear();\n    _mealNoteController.clear();\n    _selectedMealItemIds.clear();\n    _mealPortionSelections.clear();\n    _glycemicContext = null;\n    _mealType = null;\n    _selectedTime = DateTime.now();\n    _mealExpanded = false;\n    _detailsExpanded = false;\n    _contextExpanded = false;\n    _isSick = false;\n    _isStressed = false;\n    _isActive = false;\n    _badSleep = false;\n  }\n\n  Future<void> _openJournal() async {\n    final router = GoRouter.of(context);\n    if (!widget.isPage) {\n      await Navigator.maybePop(context);\n    }\n    router.go('/journal');\n  }\n\n  void _message(String text) {"""
if text.count(old) != 1:
    raise SystemExit('save completion anchor mismatch')
text = text.replace(old, new, 1)

add_log.write_text(text)

translations = {
    'app_fr.arb': {
        'journalPostSaveDeviceStatus': 'Enregistrée sur cet appareil.',
        'journalPostSaveSummaryTitle': 'Résumé de la saisie',
        'journalPostSaveMeal': 'Repas',
        'journalPostSaveNotice': 'Cette confirmation décrit uniquement ce qui a été enregistré. Elle n’interprète pas la mesure. Les tendances personnelles apparaissent séparément dans le Journal lorsque les données sont suffisantes.',
        'journalPostSaveViewJournal': 'Voir dans le journal',
        'journalPostSaveAddAnother': 'Ajouter une autre mesure',
        'journalPostSaveDone': 'Terminer',
    },
    'app_en.arb': {
        'journalPostSaveDeviceStatus': 'Saved on this device.',
        'journalPostSaveSummaryTitle': 'Entry summary',
        'journalPostSaveMeal': 'Meal',
        'journalPostSaveNotice': 'This confirmation only describes what was saved. It does not interpret the reading. Personal patterns appear separately in Journal when there is enough data.',
        'journalPostSaveViewJournal': 'View in Journal',
        'journalPostSaveAddAnother': 'Add another reading',
        'journalPostSaveDone': 'Done',
    },
    'app_ar.arb': {
        'journalPostSaveDeviceStatus': 'تم الحفظ على هذا الجهاز.',
        'journalPostSaveSummaryTitle': 'ملخص التسجيل',
        'journalPostSaveMeal': 'الوجبة',
        'journalPostSaveNotice': 'هذا التأكيد يصف فقط ما تم تسجيله ولا يفسّر القياس. تظهر الأنماط الشخصية بشكل منفصل في السجل عندما تتوفر بيانات كافية.',
        'journalPostSaveViewJournal': 'عرض في السجل',
        'journalPostSaveAddAnother': 'إضافة قياس آخر',
        'journalPostSaveDone': 'تم',
    },
}

for name, values in translations.items():
    path = root / 'frontend/lib/l10n' / name
    arb = path.read_text()
    parsed = json.loads(arb)
    overlap = set(values) & set(parsed)
    if overlap:
        raise SystemExit(f'{name}: keys already exist: {sorted(overlap)}')
    stripped = arb.rstrip()
    if not stripped.endswith('}'):
        raise SystemExit(f'{name}: malformed ARB')
    body = stripped[:-1].rstrip()
    if not body.endswith(','):
        body += ','
    additions = []
    for key, value in values.items():
        additions.append(f'  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}')
    path.write_text(body + '\n' + ',\n'.join(additions) + '\n}\n')

# Extend the existing integration-style widget suite using its in-memory Drift helper.
t = tests.read_text()
insert = r'''

  group('P2-JOURNAL-9 post-save experience', () {
    testWidgets('successful save shows a factual local receipt and resets the next draft',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.tap(find.byKey(const Key('glycemic-context-post_meal')));
      await tester.tap(find.byKey(const Key('add-meal-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('meal-type-lunch')));
      await tester.tap(find.byKey(const Key('journal-details-button')));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const Key('insulin-taken-input')), '2.5');
      await tester.tap(find.byKey(const Key('journal-context-button')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('context-stress')));

      await tester.tap(find.text('Enregistrer la mesure'));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('Enregistrée sur cet appareil.'), findsOneWidget);
      expect(find.textContaining('126 mg/dL'), findsOneWidget);
      expect(find.textContaining('Après le repas'), findsOneWidget);
      expect(find.textContaining('Déjeuner'), findsOneWidget);
      expect(find.textContaining('2.5 U'), findsOneWidget);
      expect(find.text('Stress inhabituel'), findsOneWidget);
      expect(find.textContaining('n’interprète pas la mesure'), findsOneWidget);
      expect(find.textContaining('dose recommandée'), findsNothing);
      expect(find.textContaining('cause'), findsNothing);

      final logs = await db.select(db.logEntries).get();
      expect(logs, hasLength(1));
      expect(logs.single.bloodSugar, 126);
      expect(logs.single.glycemicContext, 'post_meal');
      expect(logs.single.mealType, 'lunch');
      expect(logs.single.insulinUnits, 2.5);
      expect(logs.single.isStressed, isTrue);

      await tester.tap(find.byKey(const Key('post-save-add-another')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsNothing);
      final glucose = tester.widget<TextField>(
        find.byKey(const Key('glucose-input')),
      );
      expect(glucose.controller?.text, isEmpty);
      expect(
        tester.widget<ChoiceChip>(
          find.byKey(const Key('glycemic-context-post_meal')),
        ).selected,
        isFalse,
      );
      expect(find.byKey(const Key('meal-section')), findsNothing);
      expect(find.byKey(const Key('journal-details-card')), findsNothing);
    });

    testWidgets('Arabic receipt is localized RTL and remains factual',
        (tester) async {
      _narrow(tester);
      await tester.pumpWidget(_sheet(db, locale: const Locale('ar')));
      await tester.pumpAndSettle();

      await tester.enterText(find.byKey(const Key('glucose-input')), '126');
      await tester.tap(find.text('حفظ القياس'));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);
      expect(find.text('تم الحفظ على هذا الجهاز.'), findsOneWidget);
      expect(find.text('عرض في السجل'), findsOneWidget);
      expect(find.text('إضافة قياس آخر'), findsOneWidget);
      expect(
        Directionality.of(
          tester.element(find.text('تم الحفظ على هذا الجهاز.')),
        ),
        TextDirection.rtl,
      );
      expect(tester.takeException(), isNull);
    });
  });
'''
if not t.rstrip().endswith('}'):
    raise SystemExit('test file closing anchor missing')
# main() owns the last closing brace.
t = t.rstrip()[:-1].rstrip() + insert + '\n}\n'
tests.write_text(t)
