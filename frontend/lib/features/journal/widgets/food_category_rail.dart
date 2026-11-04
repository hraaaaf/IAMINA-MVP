import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';

class FoodCategoryRail extends StatelessWidget {
  final MealFoodCategory? selected;
  final bool allSelected;
  final ValueChanged<MealFoodCategory?> onChanged;

  const FoodCategoryRail({
    super.key,
    required this.selected,
    this.allSelected = false,
    required this.onChanged,
  });

  static const List<MealFoodCategory> primaryCategories = <MealFoodCategory>[
    MealFoodCategory.moroccanDish,
    MealFoodCategory.gulfDish,
    MealFoodCategory.breadGrain,
    MealFoodCategory.meatPoultry,
    MealFoodCategory.fishSeafood,
    MealFoodCategory.egg,
    MealFoodCategory.dairy,
    MealFoodCategory.legume,
    MealFoodCategory.vegetable,
    MealFoodCategory.fruit,
    MealFoodCategory.nutSeed,
    MealFoodCategory.drink,
    MealFoodCategory.sweetDessert,
    MealFoodCategory.snackFastFood,
    MealFoodCategory.soup,
  ];

  String _allLabel(Locale locale) => switch (locale.languageCode) {
    'ar' => 'الكل',
    'en' => 'All',
    _ => 'Tous',
  };

  String _visual(MealFoodCategory category) => switch (category) {
    MealFoodCategory.moroccanDish => '🇲🇦',
    MealFoodCategory.gulfDish => '🌙',
    MealFoodCategory.breadGrain => '🌾',
    MealFoodCategory.meatPoultry => '🍗',
    MealFoodCategory.fishSeafood => '🐟',
    MealFoodCategory.egg => '🥚',
    MealFoodCategory.dairy => '🥛',
    MealFoodCategory.legume => '🫘',
    MealFoodCategory.vegetable => '🥦',
    MealFoodCategory.fruit => '🍎',
    MealFoodCategory.nutSeed => '🌰',
    MealFoodCategory.fatSauce => '🫒',
    MealFoodCategory.drink => '🥤',
    MealFoodCategory.sweetDessert => '🍰',
    MealFoodCategory.snackFastFood => '🥪',
    MealFoodCategory.saladMeal => '🥗',
    MealFoodCategory.soup => '🥣',
    MealFoodCategory.other => '🍽️',
  };

  // Web must never resolve emoji glyphs using a remote engine font fallback.
  // Keep the same category semantics and chip size using bundled MaterialIcons.
  IconData _webIcon(MealFoodCategory? category) => switch (category) {
    null => Icons.auto_awesome_rounded,
    MealFoodCategory.moroccanDish => Icons.ramen_dining_rounded,
    MealFoodCategory.gulfDish => Icons.nightlight_round,
    MealFoodCategory.breadGrain => Icons.bakery_dining_rounded,
    MealFoodCategory.meatPoultry => Icons.kebab_dining_rounded,
    MealFoodCategory.fishSeafood => Icons.set_meal_rounded,
    MealFoodCategory.egg => Icons.egg_alt_rounded,
    MealFoodCategory.dairy => Icons.local_drink_rounded,
    MealFoodCategory.legume => Icons.grain_rounded,
    MealFoodCategory.vegetable => Icons.eco_rounded,
    MealFoodCategory.fruit => Icons.apple_rounded,
    MealFoodCategory.nutSeed => Icons.spa_rounded,
    MealFoodCategory.fatSauce => Icons.water_drop_rounded,
    MealFoodCategory.drink => Icons.local_cafe_rounded,
    MealFoodCategory.sweetDessert => Icons.cake_rounded,
    MealFoodCategory.snackFastFood => Icons.lunch_dining_rounded,
    MealFoodCategory.saladMeal => Icons.rice_bowl_rounded,
    MealFoodCategory.soup => Icons.soup_kitchen_rounded,
    MealFoodCategory.other => Icons.restaurant_rounded,
  };

  @override
  Widget build(BuildContext context) {
    final locale = Localizations.localeOf(context);
    final accent = AminaTheme.accent(context);

    return SizedBox(
      height: 46,
      child: ListView.separated(
        key: const Key('meal-category-rail'),
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.zero,
        itemCount: primaryCategories.length + 1,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final category = index == 0 ? null : primaryCategories[index - 1];
          final active = category == null
              ? (allSelected || selected == null)
              : selected == category;
          final label = category == null
              ? _allLabel(locale)
              : mealFoodCategoryLabel(category, locale);
          final visual = category == null ? '✦' : _visual(category);

          return Semantics(
            button: true,
            selected: active,
            label: label,
            child: Material(
              color: active ? accent : AminaTheme.surface(context),
              shape: StadiumBorder(
                side: BorderSide(
                  color: active ? accent : AminaTheme.divider(context),
                ),
              ),
              clipBehavior: Clip.antiAlias,
              child: InkWell(
                key: Key(
                  category == null
                      ? 'meal-category-all'
                      : 'meal-category-${category.name}',
                ),
                onTap: () => onChanged(category),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 13),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      ExcludeSemantics(
                        child: kIsWeb
                            ? Icon(
                                _webIcon(category),
                                size: 17,
                                color: active
                                    ? Colors.white
                                    : AminaTheme.textSecondary(context),
                              )
                            : Text(
                                visual,
                                style: const TextStyle(fontSize: 15),
                              ),
                      ),
                      const SizedBox(width: 7),
                      Text(
                        label,
                        style: TextStyle(
                          color: active
                              ? Colors.white
                              : AminaTheme.textPrimary(context),
                          fontSize: 12,
                          fontWeight: active
                              ? FontWeight.w700
                              : FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
