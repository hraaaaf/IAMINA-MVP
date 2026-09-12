import 'package:amina/core/data/meal_food_catalog.dart';
import 'package:amina/features/journal/widgets/food_category_rail.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('category rail exposes Morocco and Gulf shortcuts without losing All', (
    tester,
  ) async {
    MealFoodCategory? selected;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('fr'),
        localizationsDelegates: const <LocalizationsDelegate<dynamic>>[
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const <Locale>[
          Locale('fr'),
          Locale('en'),
          Locale('ar'),
        ],
        home: Scaffold(
          body: FoodCategoryRail(
            selected: selected,
            onChanged: (value) => selected = value,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('meal-category-all')), findsOneWidget);
    expect(
      find.byKey(const Key('meal-category-moroccanDish')),
      findsOneWidget,
    );

    await tester.drag(
      find.byKey(const Key('meal-category-rail')),
      const Offset(-500, 0),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('meal-category-gulfDish')), findsOneWidget);

    await tester.tap(find.byKey(const Key('meal-category-gulfDish')));
    expect(selected, MealFoodCategory.gulfDish);
  });

  testWidgets('category rail localizes Arabic and stays RTL-compatible', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        localizationsDelegates: const <LocalizationsDelegate<dynamic>>[
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const <Locale>[
          Locale('fr'),
          Locale('en'),
          Locale('ar'),
        ],
        home: Scaffold(
          body: FoodCategoryRail(selected: null, onChanged: (_) {}),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final all = find.byKey(const Key('meal-category-all'));
    expect(Directionality.of(tester.element(all)), TextDirection.rtl);
    expect(find.text('الكل'), findsOneWidget);
    expect(find.text('أطباق مغربية'), findsOneWidget);
  });
}
