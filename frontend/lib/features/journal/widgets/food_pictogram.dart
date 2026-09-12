import 'package:flutter/material.dart';

import '../../../core/data/food_pictogram_registry.dart';
import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import 'food_pictogram_painter.dart';

/// Runtime surface for IAMINA food artwork.
///
/// Rendering priority:
/// 1. certified bundled artwork when a reviewed asset exists;
/// 2. native IAMINA vector pictogram for the coded launch set;
/// 3. deterministic emoji fallback for the remaining long tail.
///
/// This keeps food selection fully offline and gives the first launch batch a
/// premium, platform-independent visual identity without waiting for binary
/// artwork production.
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

  Widget _emojiFallback() => ExcludeSemantics(
    child: Text(
      item.visual,
      style: TextStyle(fontSize: size * .48, height: 1),
    ),
  );

  Widget _nativePictogram() => ExcludeSemantics(
    child: CustomPaint(
      size: Size.square(size),
      painter: FoodPictogramPainter(item.pictogramKey),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final accent = AminaTheme.accent(context);
    final certified = hasCertifiedFoodPictogram(item.pictogramKey);
    final native = hasCodeFoodPictogram(item.pictogramKey);

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
                errorBuilder: (context, error, stackTrace) =>
                    native ? _nativePictogram() : _emojiFallback(),
              )
            : native
            ? _nativePictogram()
            : _emojiFallback(),
      ),
    );
  }
}
