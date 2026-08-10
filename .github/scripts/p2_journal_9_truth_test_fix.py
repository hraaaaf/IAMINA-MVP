from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'frontend/test/features/add_log_sheet_test.dart'
text = path.read_text()

text = text.replace("expect(find.textContaining('Après le repas'), findsOneWidget);", "expect(find.textContaining('Après repas'), findsOneWidget);")

old = """      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);\n      expect(find.text('Enregistrée sur cet appareil.'), findsOneWidget);\n      expect(find.textContaining('126 mg/dL'), findsOneWidget);\n      expect(find.textContaining('Après repas'), findsOneWidget);\n      expect(find.textContaining('Déjeuner'), findsOneWidget);\n      expect(find.textContaining('2.5 U'), findsOneWidget);\n      expect(find.text('Stress inhabituel'), findsOneWidget);\n      expect(find.textContaining('n’interprète pas la mesure'), findsOneWidget);\n      expect(find.textContaining('dose recommandée'), findsNothing);\n      expect(find.textContaining('cause'), findsNothing);\n\n      final logs = await db.select(db.logEntries).get();\n      expect(logs, hasLength(1));\n      expect(logs.single.bloodSugar, 126);\n      expect(logs.single.glycemicContext, 'post_meal');\n      expect(logs.single.mealType, 'lunch');\n      expect(logs.single.insulinUnits, 2.5);\n      expect(logs.single.isStressed, isTrue);\n"""
new = """      final logs = await db.select(db.logEntries).get();\n      expect(logs, hasLength(1));\n      expect(logs.single.bloodSugar, 126);\n      expect(logs.single.glycemicContext, 'post_meal');\n      expect(logs.single.mealType, 'lunch');\n      expect(logs.single.insulinUnits, 2.5);\n      expect(logs.single.isStressed, isTrue);\n\n      expect(find.byKey(const Key('post-save-receipt')), findsOneWidget);\n      expect(find.text('Enregistrée sur cet appareil.'), findsOneWidget);\n      expect(find.textContaining('126 mg/dL'), findsOneWidget);\n      expect(find.textContaining('Après repas'), findsOneWidget);\n      expect(find.textContaining('Déjeuner'), findsOneWidget);\n      expect(find.textContaining('2.5 U'), findsOneWidget);\n      expect(find.text('Stress inhabituel'), findsOneWidget);\n      expect(find.textContaining('n’interprète pas la mesure'), findsOneWidget);\n      expect(find.textContaining('dose recommandée'), findsNothing);\n      expect(find.textContaining('cause'), findsNothing);\n"""
if text.count(old) != 1:
    raise SystemExit('J9 truth assertion anchor mismatch')
path.write_text(text.replace(old, new, 1))
