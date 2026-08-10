from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'frontend/test/features/add_log_sheet_test.dart'
text = path.read_text()
old = """      await tester.tap(find.byKey(const Key('meal-type-lunch')));\n      await tester.tap(find.byKey(const Key('journal-details-button')));\n      await tester.pumpAndSettle();\n      await tester.enterText(find.byKey(const Key('insulin-taken-input')), '2.5');\n      await tester.tap(find.byKey(const Key('journal-context-button')));\n      await tester.pumpAndSettle();\n      await tester.tap(find.byKey(const Key('context-stress')));\n\n      await tester.tap(find.text('Enregistrer la mesure'));\n"""
new = """      await tester.tap(find.byKey(const Key('meal-type-lunch')));\n\n      final detailsButton = find.byKey(const Key('journal-details-button'));\n      await tester.ensureVisible(detailsButton);\n      await tester.pumpAndSettle();\n      await tester.tap(detailsButton);\n      await tester.pumpAndSettle();\n\n      final insulinInput = find.byKey(const Key('insulin-taken-input'));\n      await tester.ensureVisible(insulinInput);\n      await tester.pumpAndSettle();\n      await tester.enterText(insulinInput, '2.5');\n\n      final contextButton = find.byKey(const Key('journal-context-button'));\n      await tester.ensureVisible(contextButton);\n      await tester.pumpAndSettle();\n      await tester.tap(contextButton);\n      await tester.pumpAndSettle();\n      final stressChip = find.byKey(const Key('context-stress'));\n      await tester.ensureVisible(stressChip);\n      await tester.pumpAndSettle();\n      await tester.tap(stressChip);\n\n      await tester.tap(find.text('Enregistrer la mesure'));\n"""
if text.count(old) != 1:
    raise SystemExit('J9 scrolling sequence anchor mismatch')
text = text.replace(old, new, 1)
old = """      await tester.tap(find.byKey(const Key('post-save-add-another')));\n      await tester.pumpAndSettle();\n"""
new = """      final addAnother = find.byKey(const Key('post-save-add-another'));\n      await tester.ensureVisible(addAnother);\n      await tester.pumpAndSettle();\n      await tester.tap(addAnother);\n      await tester.pumpAndSettle();\n"""
if text.count(old) != 1:
    raise SystemExit('J9 add-another anchor mismatch')
path.write_text(text.replace(old, new, 1))
