import 'package:flutter/material.dart';

import '../core/data/nutrition_catalog.dart';
import '../core/theme/app_theme.dart';
import '../features/journal/widgets/nutrition_portion_editor.dart';
import '../l10n/app_localizations.dart';

void main() {
  final language = Uri.base.queryParameters['lang'] == 'ar' ? 'ar' : 'fr';
  runApp(_AuditApp(locale: Locale(language)));
}

class _AuditApp extends StatelessWidget {
  final Locale locale;
  const _AuditApp({required this.locale});

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    theme: AminaTheme.light,
    home: const Scaffold(body: _AuditSurface()),
  );
}

class _AuditSurface extends StatefulWidget {
  const _AuditSurface();

  @override
  State<_AuditSurface> createState() => _AuditSurfaceState();
}

class _AuditSurfaceState extends State<_AuditSurface> {
  Map<String, MealPortionSelection> selections = const {
    'banana': MealPortionSelection(foodId: 'banana', portionId: 'one_peeled'),
    'msemen': MealPortionSelection(foodId: 'msemen', portionId: 'one_piece'),
  };

  @override
  Widget build(BuildContext context) => SafeArea(
    child: SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: NutritionPortionEditor(
            selectedFoodIds: const ['banana', 'msemen'],
            selections: selections,
            onChanged: (next) => setState(() => selections = next),
          ),
        ),
      ),
    ),
  );
}
