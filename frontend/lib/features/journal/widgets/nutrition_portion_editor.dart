import 'package:flutter/material.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/data/nutrition_catalog.dart';
import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';

String debugNutritionCarbRangeForTest(
  AppLocalizations l10n,
  Locale locale,
  String low,
  String high,
) => _localizedCarbRange(l10n, locale, low, high);

String _localizedCarbRange(
  AppLocalizations l10n,
  Locale locale,
  String low,
  String high,
) {
  if (locale.languageCode != 'ar') {
    return l10n.journalNutritionCarbsRange(low, high);
  }
  final lri = String.fromCharCode(0x2066);
  final pdi = String.fromCharCode(0x2069);
  return l10n.journalNutritionCarbsRange('$lri$low', '$high$pdi');
}

class NutritionPortionEditor extends StatelessWidget {
  final List<String> selectedFoodIds;
  final Map<String, MealPortionSelection> selections;
  final ValueChanged<Map<String, MealPortionSelection>> onChanged;

  const NutritionPortionEditor({
    super.key,
    required this.selectedFoodIds,
    required this.selections,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    if (selectedFoodIds.isEmpty) return const SizedBox.shrink();
    final l10n = AppLocalizations.of(context)!;
    final locale = Localizations.localeOf(context);

    return Column(
      key: const Key('nutrition-portion-editor'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          l10n.journalNutritionPortionTitle,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: .55,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          l10n.journalNutritionPortionHint,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            height: 1.35,
          ),
        ),
        const SizedBox(height: 10),
        ...selectedFoodIds.map((foodId) {
          final food = mealFoodById(foodId);
          if (food == null) return const SizedBox.shrink();
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _FoodPortionCard(
              foodId: foodId,
              foodLabel: food.labelFor(locale),
              locale: locale,
              selection: selections[foodId],
              onChanged: (selection) {
                final next = Map<String, MealPortionSelection>.from(selections);
                if (selection == null) {
                  next.remove(foodId);
                } else {
                  next[foodId] = selection;
                }
                onChanged(next);
              },
            ),
          );
        }),
      ],
    );
  }
}

class _FoodPortionCard extends StatefulWidget {
  final String foodId;
  final String foodLabel;
  final Locale locale;
  final MealPortionSelection? selection;
  final ValueChanged<MealPortionSelection?> onChanged;

  const _FoodPortionCard({
    required this.foodId,
    required this.foodLabel,
    required this.locale,
    required this.selection,
    required this.onChanged,
  });

  @override
  State<_FoodPortionCard> createState() => _FoodPortionCardState();
}

class _FoodPortionCardState extends State<_FoodPortionCard> {
  late final TextEditingController _gramsController;

  @override
  void initState() {
    super.initState();
    _gramsController = TextEditingController(
      text: widget.selection?.grams?.toStringAsFixed(0) ?? '',
    );
  }

  @override
  void didUpdateWidget(covariant _FoodPortionCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    final grams = widget.selection?.grams;
    final next = grams?.toStringAsFixed(0) ?? '';
    if (_gramsController.text != next && !_gramsController.selection.isValid) {
      _gramsController.text = next;
    }
  }

  @override
  void dispose() {
    _gramsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final profile = nutritionProfileFor(widget.foodId);
    final portions = profile?.portions ?? const <NutritionPortion>[];
    final selectedPortion = widget.selection?.portionId;
    final estimate = _estimate(profile);

    return Container(
      key: Key('nutrition-food-${widget.foodId}'),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AminaTheme.bg(context),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            widget.foodLabel,
            style: TextStyle(
              color: AminaTheme.textPrimary(context),
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (portions.isNotEmpty) ...<Widget>[
            const SizedBox(height: 8),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: portions.map((portion) {
                return ChoiceChip(
                  key: Key('nutrition-${widget.foodId}-${portion.id}'),
                  label: Text(portion.label.forLocale(widget.locale)),
                  selected: selectedPortion == portion.id,
                  onSelected: (selected) {
                    _gramsController.clear();
                    widget.onChanged(
                      selected
                          ? MealPortionSelection(
                              foodId: widget.foodId,
                              portionId: portion.id,
                            )
                          : null,
                    );
                  },
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 9),
          SizedBox(
            width: 150,
            child: TextField(
              key: Key('nutrition-grams-${widget.foodId}'),
              controller: _gramsController,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: InputDecoration(
                labelText: l10n.journalNutritionGrams,
                suffixText: 'g',
                isDense: true,
                border: const OutlineInputBorder(),
              ),
              onChanged: (raw) {
                final grams = double.tryParse(raw.trim().replaceAll(',', '.'));
                if (grams == null || grams <= 0 || grams > 3000) {
                  if (raw.trim().isEmpty) widget.onChanged(null);
                  return;
                }
                widget.onChanged(
                  MealPortionSelection(foodId: widget.foodId, grams: grams),
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          if (estimate == null)
            Text(
              l10n.journalNutritionUnavailable,
              key: Key('nutrition-unavailable-${widget.foodId}'),
              style: TextStyle(
                color: AminaTheme.textSecondary(context),
                fontSize: 11,
                height: 1.35,
              ),
            )
          else ...<Widget>[
            Text(
              estimate.isExact
                  ? l10n.journalNutritionCarbsExact(
                      estimate.low.toStringAsFixed(1),
                    )
                  : _localizedCarbRange(
                      l10n,
                      widget.locale,
                      estimate.low.toStringAsFixed(1),
                      estimate.high.toStringAsFixed(1),
                    ),
              key: Key('nutrition-carbs-${widget.foodId}'),
              style: TextStyle(
                color: AminaTheme.textPrimary(context),
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 3),
            Text(
              l10n.journalNutritionSource(
                nutritionSourceFor(estimate.sourceId)?.publisher ??
                    estimate.sourceId,
              ),
              style: TextStyle(
                color: AminaTheme.textSecondary(context),
                fontSize: 10,
              ),
            ),
          ],
        ],
      ),
    );
  }

  CarbEstimate? _estimate(MealNutritionProfile? profile) {
    if (profile == null || widget.selection == null) return null;
    final selection = widget.selection!;
    if (selection.grams != null) {
      return estimateCarbsForGrams(widget.foodId, selection.grams!);
    }
    final portionId = selection.portionId;
    if (portionId == null) return null;
    for (final portion in profile.portions) {
      if (portion.id == portionId) {
        return estimateCarbsForPortion(widget.foodId, portion);
      }
    }
    return null;
  }
}
