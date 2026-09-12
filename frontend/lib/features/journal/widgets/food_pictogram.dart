import 'package:flutter/material.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';

/// Runtime surface for IAMINA food artwork.
///
/// Premium WebP assets are optional until a generation batch is certified.
/// The text/emoji fallback remains deterministic and keeps the picker usable
/// offline while visual production progresses independently.
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

  String get assetPath =>
      'assets/food/pictograms/v1/${item.pictogramKey}.webp';

  @override
  Widget build(BuildContext context) {
    final accent = AminaTheme.accent(context);
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
        child: Image.asset(
          assetPath,
          width: size,
          height: size,
          fit: BoxFit.contain,
          excludeFromSemantics: true,
          errorBuilder: (context, error, stackTrace) => ExcludeSemantics(
            child: Text(
              item.visual,
              style: TextStyle(fontSize: size * .48, height: 1),
            ),
          ),
        ),
      ),
    );
  }
}
