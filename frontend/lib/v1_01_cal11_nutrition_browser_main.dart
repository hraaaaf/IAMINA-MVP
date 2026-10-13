import 'package:flutter/material.dart';

import 'features/journal/widgets/nutrition_portion_editor.dart';
import 'core/data/nutrition_catalog.dart';
import 'l10n/app_localizations.dart';

/// Chrome-only CAL-11 proof fixture. Not part of the patient runtime.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final requested = Uri.base.queryParameters['locale'];
  final language = const <String>{'fr', 'en', 'ar'}.contains(requested)
      ? requested!
      : 'fr';
  runApp(_Cal11AppleAuditApp(language: language));
}

class _Cal11AppleAuditApp extends StatelessWidget {
  final String language;
  const _Cal11AppleAuditApp({required this.language});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      locale: Locale(language),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 600),
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: NutritionPortionEditor(
                  selectedFoodIds: const <String>['apple'],
                  selections: const <String, MealPortionSelection>{
                    'apple': MealPortionSelection(foodId: 'apple', grams: 100),
                  },
                  onChanged: (_) {},
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
