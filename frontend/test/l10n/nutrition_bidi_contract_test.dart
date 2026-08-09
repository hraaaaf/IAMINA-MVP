import 'package:amina/features/journal/widgets/nutrition_portion_editor.dart';
import 'package:amina/l10n/app_localizations_ar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Arabic nutrition range keeps low-to-high order', (tester) async {
    late String rendered;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            rendered = debugNutritionCarbRangeForTest(
              AppLocalizationsAr(),
              const Locale('ar'),
              '22.1',
              '26.4',
            );
            return const SizedBox.shrink();
          },
        ),
      ),
    );
    expect(
      rendered,
      contains(
        '${String.fromCharCode(0x2066)}22.1–26.4${String.fromCharCode(0x2069)}',
      ),
    );
    expect(rendered, isNot(contains('26.4–22.1')));
  });
}
