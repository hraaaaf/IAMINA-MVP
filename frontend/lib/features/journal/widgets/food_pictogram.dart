import 'package:flutter/material.dart';

import '../../../core/data/food_pictogram_registry.dart';
import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';

/// Runtime surface for IAMINA food artwork.
///
/// Only assets listed in [certifiedFoodPictogramIds] are read from the bundle.
/// This avoids hundreds of failed asset lookups while visual batches are still
/// being produced. The local fallback keeps food selection fully offline.
class FoodPictogram extends StatelessWidget {
  final MealFoodItem item;
  final double size;
  final bool selected;

  const FoodPictogram({
    super.key,
    required this.item,
    this.size = 42,
    this.selected = false,
  });

  String get assetPath => certifiedFoodPictogramPath(item.pictogramKey);

  Widget _fallback() => ExcludeSemantics(
    child: Text(
      item.visual,
      style: TextStyle(fontSize: size * .48, height: 1),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final accent = AminaTheme.accent(context);
    final certified = hasCertifiedFoodPictogram(item.pictogramKey);

    return Semantics(
      image: true,
      label: item.plainLabelFor(Localizations.localeOf(context)),
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: selected
              ? accent.withValues(alpha: AminaTheme.isDark(context) ? .18 : .09)
              : AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(size * .31),
          border: Border.all(
            color: selected
                ? accent.withValues(alpha: .45)
                : AminaTheme.divider(context),
          ),
        ),
        clipBehavior: Clip.antiAlias,
        alignment: Alignment.center,
        child: certified
            ? Image.asset(
                assetPath,
                width: size,
                height: size,
                fit: BoxFit.contain,
                excludeFromSemantics: true,
                errorBuilder: (context, error, stackTrace) => _fallback(),
              )
            : _fallback(),
      ),
    );
  }
}
