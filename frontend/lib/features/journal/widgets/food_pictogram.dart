import 'package:flutter/material.dart';

import '../../../core/data/food_pictogram_registry.dart';
import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import 'food_pictogram_painter.dart';
import 'food_pictogram_painter_batch2.dart';
import 'food_pictogram_painter_batch3.dart';
import 'food_pictogram_painter_batch4.dart';
import 'food_pictogram_painter_batch5.dart';
import 'food_pictogram_painter_batch6.dart';

/// Runtime surface for IAMINA food artwork.
///
/// Rendering priority:
/// 1. certified bundled artwork when a reviewed asset exists;
/// 2. native IAMINA vector pictogram for the coded launch/catalog set;
/// 3. deterministic emoji fallback for the remaining long tail.
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
    child: Text(item.visual, style: TextStyle(fontSize: size * .48, height: 1)),
  );

  Widget _nativePictogram() {
    final key = item.pictogramKey;
    final CustomPainter painter;
    if (hasCodeFoodPictogramBatch6(key)) {
      painter = FoodPictogramPainterBatch6(key);
    } else if (hasCodeFoodPictogramBatch5(key)) {
      painter = FoodPictogramPainterBatch5(key);
    } else if (hasCodeFoodPictogramBatch4(key)) {
      painter = FoodPictogramPainterBatch4(key);
    } else if (hasCodeFoodPictogramBatch3(key)) {
      painter = FoodPictogramPainterBatch3(key);
    } else if (hasCodeFoodPictogramBatch2(key)) {
      painter = FoodPictogramPainterBatch2(key);
    } else {
      painter = FoodPictogramPainter(key);
    }
    return ExcludeSemantics(
      child: CustomPaint(size: Size.square(size), painter: painter),
    );
  }

  @override
  Widget build(BuildContext context) {
    final accent = AminaTheme.accent(context);
    final certified = hasCertifiedFoodPictogram(item.pictogramKey);
    final native = hasCodeFoodPictogram(item.pictogramKey) ||
        hasCodeFoodPictogramBatch2(item.pictogramKey) ||
        hasCodeFoodPictogramBatch3(item.pictogramKey) ||
        hasCodeFoodPictogramBatch4(item.pictogramKey) ||
        hasCodeFoodPictogramBatch5(item.pictogramKey) ||
        hasCodeFoodPictogramBatch6(item.pictogramKey);

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
            color: selected ? accent.withValues(alpha: .45) : AminaTheme.divider(context),
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
