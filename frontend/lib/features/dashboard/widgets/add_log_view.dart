import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/data/nutrition_catalog.dart';
import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../journal/widgets/meal_capture_panel.dart';
import '../../journal/widgets/nutrition_portion_editor.dart';

String addLogContextLabel(AppLocalizations l10n, String value) => switch (value) {
  'fasting' => l10n.journalContextFasting,
  'pre_meal' => l10n.journalContextPreMeal,
  'post_meal' => l10n.journalContextPostMeal,
  _ => l10n.journalContextOther,
};

String addLogMealLabel(AppLocalizations l10n, String value) => switch (value) {
  'breakfast' => l10n.journalMealBreakfast,
  'lunch' => l10n.journalMealLunch,
  'dinner' => l10n.journalMealDinner,
  'suhoor' => l10n.journalMealSuhoor,
  'iftar' => l10n.journalMealIftar,
  'other' => l10n.journalMealOther,
  _ => l10n.journalMealSnack,
};

String addLogDetailsLabel(BuildContext context) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return 'تفاصيل: الوقت والسياق…';
  if (code == 'en') return 'Details: time and context…';
  return 'Détails : heure et contexte…';
}

String addLogTimeLabel(AppLocalizations l10n, DateTime selectedTime) {
  final now = DateTime.now();
  final sameDay =
      selectedTime.year == now.year &&
      selectedTime.month == now.month &&
      selectedTime.day == now.day;
  final hh = selectedTime.hour.toString().padLeft(2, '0');
  final mm = selectedTime.minute.toString().padLeft(2, '0');
  if (sameDay) return '${l10n.journalToday} · $hh:$mm';
  final dd = selectedTime.day.toString().padLeft(2, '0');
  final mo = selectedTime.month.toString().padLeft(2, '0');
  return '$dd/$mo · $hh:$mm';
}

Widget _sectionLabel(BuildContext context, String text) => Text(
  text,
  style: TextStyle(
    color: AminaTheme.textSecondary(context),
    fontSize: 11,
    fontWeight: FontWeight.w800,
    letterSpacing: .55,
  ),
);

TextStyle _helperStyle(BuildContext context) => TextStyle(
  color: AminaTheme.textSecondary(context),
  fontSize: 12,
  height: 1.4,
);

TextStyle _glucoseHelperStyle(BuildContext context) => TextStyle(
  color: AminaTheme.textSecondary(context),
  fontSize: 11.5,
  height: 1.35,
);

class AddLogSurface extends StatelessWidget {
  final bool isPage;
  final Future<void> Function() onBack;
  final Widget primaryEvent;
  final Widget detailsCard;
  final bool detailsExpanded;
  final VoidCallback onShowDetails;
  final Widget saveBar;

  const AddLogSurface({
    super.key,
    required this.isPage,
    required this.onBack,
    required this.primaryEvent,
    required this.detailsCard,
    required this.detailsExpanded,
    required this.onShowDetails,
    required this.saveBar,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isDesktop = MediaQuery.sizeOf(context).width >= 1000;
    final isDark = AminaTheme.isDark(context);

    return DecoratedBox(
      key: const Key('add-log-ambient-backdrop'),
      decoration: BoxDecoration(
        color: AminaTheme.bg(context),
        gradient: isDark
            ? null
            : const LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: <Color>[
                  Color(0xFFF8FBFA),
                  Color(0xFFF0F7F5),
                  Color(0xFFF7FAF9),
                ],
                stops: <double>[0, 0.62, 1],
              ),
      ),
      child: SafeArea(
        child: Stack(
          children: <Widget>[
            SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 112),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1080),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      if (!isPage) ...<Widget>[
                        _AddLogHeader(onBack: onBack),
                        const SizedBox(height: 22),
                      ],
                      if (isDesktop)
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Expanded(flex: 6, child: primaryEvent),
                            const SizedBox(width: 28),
                            Expanded(flex: 4, child: detailsCard),
                          ],
                        )
                      else ...<Widget>[
                        primaryEvent,
                        const SizedBox(height: 18),
                        if (!detailsExpanded)
                          OutlinedButton.icon(
                            key: const Key('journal-details-button'),
                            onPressed: onShowDetails,
                            icon: const Icon(Icons.tune_rounded, size: 18),
                            label: Text(addLogDetailsLabel(context)),
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size.fromHeight(48),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                          )
                        else
                          detailsCard,
                      ],
                    ],
                  ),
                ),
              ),
            ),
            PositionedDirectional(
              start: 0,
              end: 0,
              bottom: 0,
              child: saveBar,
            ),
          ],
        ),
      ),
    );
  }
}

class _AddLogHeader extends StatelessWidget {
  final Future<void> Function() onBack;

  const _AddLogHeader({required this.onBack});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: <Widget>[
        IconButton(
          tooltip: l10n.journalBack,
          onPressed: onBack,
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                l10n.journalAddTitle,
                style: TextStyle(
                  color: AminaTheme.textPrimary(context),
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                l10n.journalAddSubtitle,
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class AddLogGlucoseCard extends StatelessWidget {
  final TextEditingController controller;
  final String unit;
  final double? mgdl;
  final ValueChanged<String> onChanged;

  const AddLogGlucoseCard({
    super.key,
    required this.controller,
    required this.unit,
    required this.mgdl,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isLow = mgdl != null && mgdl! < 70;
    final isDark = AminaTheme.isDark(context);
    final radius = BorderRadius.circular(22);
    final glassSurface = isDark
        ? AminaTheme.darkCardElevated.withValues(alpha: 0.78)
        : Colors.white.withValues(alpha: 0.68);
    final glassBorder = isDark
        ? AminaTheme.dark400.withValues(alpha: 0.22)
        : Colors.white.withValues(alpha: 0.92);
    final fieldSurface = isDark
        ? AminaTheme.dark700.withValues(alpha: 0.54)
        : Colors.white.withValues(alpha: 0.78);

    return Semantics(
      container: true,
      label: l10n.journalGlucose,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: radius,
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: isLow
                  ? const Color(0xFFF97316).withValues(alpha: 0.12)
                  : AminaTheme.teal900.withValues(
                      alpha: isDark ? 0.16 : 0.10,
                    ),
              blurRadius: 30,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: radius,
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
            child: Container(
              key: const Key('glucose-glass-card'),
              padding: const EdgeInsets.fromLTRB(18, 16, 18, 15),
              decoration: BoxDecoration(
                color: isLow
                    ? const Color(0xFFFFF7ED).withValues(alpha: 0.94)
                    : glassSurface,
                borderRadius: radius,
                border: Border.all(
                  color: isLow ? const Color(0xFFF97316) : glassBorder,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  _sectionLabel(context, l10n.journalGlucose),
                  const SizedBox(height: 10),
                  TextField(
                    key: const Key('glucose-input'),
                    controller: controller,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
                    ],
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 44,
                      fontWeight: FontWeight.w800,
                      height: 1.0,
                    ),
                    decoration: InputDecoration(
                      hintText: '—',
                      suffixIcon: Padding(
                        padding: const EdgeInsetsDirectional.only(end: 16),
                        child: Center(
                          widthFactor: 1,
                          child: Text(
                            unit,
                            key: const Key('glucose-unit'),
                            style: TextStyle(
                              color: AminaTheme.textSecondary(context),
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ),
                      suffixIconConstraints: const BoxConstraints(
                        minWidth: 0,
                        minHeight: 0,
                      ),
                      filled: true,
                      fillColor: isLow
                          ? Colors.white.withValues(alpha: 0.82)
                          : fieldSurface,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 13,
                      ),
                      isDense: true,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(
                          color: AminaTheme.divider(context),
                        ),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(
                          color: isLow
                              ? const Color(0xFFF97316).withValues(alpha: 0.48)
                              : AminaTheme.divider(context),
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(
                          color: isLow
                              ? const Color(0xFFF97316)
                              : AminaTheme.accent(context),
                          width: 1.5,
                        ),
                      ),
                    ),
                    onChanged: onChanged,
                  ),
                  const SizedBox(height: 9),
                  if (mgdl == null)
                    Text(
                      l10n.journalNoGlucoseAssumption,
                      style: _glucoseHelperStyle(context),
                    )
                  else if (isLow)
                    Text(
                      l10n.journalLowGlucoseDetected,
                      style: const TextStyle(
                        color: Color(0xFFC2410C),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                      ),
                    )
                  else
                    Text(
                      l10n.journalTargetNotInferred,
                      style: _glucoseHelperStyle(context),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class AddLogMeasurementContext extends StatelessWidget {
  final String? selected;
  final ValueChanged<String?> onChanged;

  const AddLogMeasurementContext({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  static const List<String> _contexts = <String>[
    'fasting',
    'pre_meal',
    'post_meal',
    'other',
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _sectionLabel(context, l10n.journalMeasurementContext),
        const SizedBox(height: 5),
        Text(l10n.journalContextHint, style: _helperStyle(context)),
        const SizedBox(height: 11),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _contexts.map((value) {
            return ChoiceChip(
              key: Key('glycemic-context-$value'),
              label: Text(addLogContextLabel(l10n, value)),
              selected: selected == value,
              onSelected: (isSelected) =>
                  onChanged(isSelected ? value : null),
            );
          }).toList(),
        ),
      ],
    );
  }
}

class AddLogMealCapture extends StatelessWidget {
  final bool expanded;
  final bool ramadanActive;
  final List<String> mealTypes;
  final String? selectedMealType;
  final List<String> selectedMealItemIds;
  final Map<String, MealPortionSelection> mealPortionSelections;
  final TextEditingController mealNoteController;
  final bool canUsePhotoRecognition;
  final VoidCallback onExpand;
  final VoidCallback onRemove;
  final ValueChanged<String?> onMealTypeChanged;
  final ValueChanged<List<String>> onSelectedMealItemIdsChanged;
  final ValueChanged<Map<String, MealPortionSelection>> onPortionsChanged;

  const AddLogMealCapture({
    super.key,
    required this.expanded,
    required this.ramadanActive,
    required this.mealTypes,
    required this.selectedMealType,
    required this.selectedMealItemIds,
    required this.mealPortionSelections,
    required this.mealNoteController,
    required this.canUsePhotoRecognition,
    required this.onExpand,
    required this.onRemove,
    required this.onMealTypeChanged,
    required this.onSelectedMealItemIdsChanged,
    required this.onPortionsChanged,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    if (!expanded) {
      return OutlinedButton.icon(
        key: const Key('add-meal-button'),
        onPressed: onExpand,
        icon: const Icon(Icons.restaurant_outlined, size: 18),
        label: Text('${l10n.journalAddMeal} · ${l10n.journalOptional}'),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(48),
          alignment: AlignmentDirectional.center,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      );
    }

    return Container(
      key: const Key('meal-section'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AminaTheme.subtleBg(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: _sectionLabel(context, l10n.journalMealOptional),
              ),
              TextButton(
                onPressed: onRemove,
                child: Text(l10n.journalRemoveMeal),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (ramadanActive) ...<Widget>[
            Text(
              l10n.journalRamadanMealVocabularyHint,
              key: const Key('ramadan-meal-vocabulary-hint'),
              style: _helperStyle(context),
            ),
            const SizedBox(height: 10),
          ],
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: mealTypes.map((value) {
              return ChoiceChip(
                key: Key('meal-type-$value'),
                label: Text(addLogMealLabel(l10n, value)),
                selected: selectedMealType == value,
                onSelected: (isSelected) =>
                    onMealTypeChanged(isSelected ? value : null),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          MealCapturePanel(
            selectedIds: selectedMealItemIds,
            canUsePhotoRecognition: canUsePhotoRecognition,
            onChanged: onSelectedMealItemIdsChanged,
          ),
          if (selectedMealItemIds.isNotEmpty) ...<Widget>[
            const SizedBox(height: 16),
            NutritionPortionEditor(
              selectedFoodIds: selectedMealItemIds,
              selections: mealPortionSelections,
              onChanged: onPortionsChanged,
            ),
          ],
          const SizedBox(height: 16),
          TextField(
            key: const Key('meal-note-input'),
            controller: mealNoteController,
            minLines: 2,
            maxLines: 4,
            decoration: InputDecoration(
              labelText: l10n.journalMealNoteLabel,
              hintText: l10n.journalMealNoteHint,
              border: const OutlineInputBorder(),
            ),
          ),
        ],
      ),
    );
  }
}

class AddLogDetailsCard extends StatelessWidget {
  final String timeLabel;
  final Future<void> Function() onPickDateTime;
  final bool contextExpanded;
  final bool isSick;
  final bool isStressed;
  final bool isActive;
  final bool badSleep;
  final VoidCallback onExpandContext;
  final VoidCallback onCollapseContext;
  final ValueChanged<bool> onSickChanged;
  final ValueChanged<bool> onStressedChanged;
  final ValueChanged<bool> onActiveChanged;
  final ValueChanged<bool> onBadSleepChanged;

  const AddLogDetailsCard({
    super.key,
    required this.timeLabel,
    required this.onPickDateTime,
    required this.contextExpanded,
    required this.isSick,
    required this.isStressed,
    required this.isActive,
    required this.badSleep,
    required this.onExpandContext,
    required this.onCollapseContext,
    required this.onSickChanged,
    required this.onStressedChanged,
    required this.onActiveChanged,
    required this.onBadSleepChanged,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      key: const Key('journal-details-card'),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AminaTheme.subtleBg(context),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            l10n.journalDetailsTitle,
            style: TextStyle(
              color: AminaTheme.textPrimary(context),
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 16),
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: onPickDateTime,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
              decoration: BoxDecoration(
                color: AminaTheme.bg(context),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AminaTheme.divider(context)),
              ),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.schedule_outlined, size: 18),
                  const SizedBox(width: 10),
                  Expanded(child: Text(timeLabel)),
                  const Icon(Icons.edit_outlined, size: 16),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          _healthContext(context, l10n),
        ],
      ),
    );
  }

  Widget _healthContext(BuildContext context, AppLocalizations l10n) {
    final hasContext = isSick || isStressed || isActive || badSleep;
    if (!contextExpanded && !hasContext) {
      return OutlinedButton.icon(
        key: const Key('journal-context-button'),
        onPressed: onExpandContext,
        icon: const Icon(Icons.add_circle_outline_rounded, size: 18),
        label: Text(
          '${l10n.journalAdditionalContext} · ${l10n.journalOptional}',
        ),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(48),
          alignment: AlignmentDirectional.centerStart,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      );
    }
    return Column(
      key: const Key('journal-context-selector'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            Expanded(
              child: _sectionLabel(context, l10n.journalAdditionalContext),
            ),
            if (!hasContext)
              TextButton(
                onPressed: onCollapseContext,
                child: Text(l10n.cancel),
              ),
          ],
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: <Widget>[
            FilterChip(
              key: const Key('context-illness'),
              label: Text(l10n.journalSick),
              selected: isSick,
              onSelected: onSickChanged,
            ),
            FilterChip(
              key: const Key('context-stress'),
              label: Text(l10n.journalUnusualStress),
              selected: isStressed,
              onSelected: onStressedChanged,
            ),
            FilterChip(
              key: const Key('context-activity'),
              label: Text(l10n.journalPhysicalActivity),
              selected: isActive,
              onSelected: onActiveChanged,
            ),
            FilterChip(
              key: const Key('context-poor-sleep'),
              label: Text(l10n.journalPoorSleep),
              selected: badSleep,
              onSelected: onBadSleepChanged,
            ),
          ],
        ),
      ],
    );
  }
}

class AddLogSaveBar extends StatelessWidget {
  final bool saving;
  final bool enabled;
  final Future<void> Function() onSave;

  const AddLogSaveBar({
    super.key,
    required this.saving,
    required this.enabled,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final desktop = MediaQuery.sizeOf(context).width >= 1000;
    final isDark = AminaTheme.isDark(context);
    final surface = (isDark ? AminaTheme.darkPaper : Colors.white).withValues(
      alpha: isDark ? 0.84 : 0.74,
    );

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          key: const Key('save-log-glass-bar'),
          padding: const EdgeInsets.fromLTRB(20, 10, 20, 14),
          decoration: BoxDecoration(
            color: surface,
            border: Border(
              top: BorderSide(
                color: isDark
                    ? AminaTheme.dark600.withValues(alpha: 0.58)
                    : Colors.white.withValues(alpha: 0.92),
              ),
            ),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: AminaTheme.teal900.withValues(
                  alpha: isDark ? 0.18 : 0.06,
                ),
                blurRadius: 24,
                offset: const Offset(0, -8),
              ),
            ],
          ),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1080),
              child: Align(
                alignment: desktop
                    ? AlignmentDirectional.centerEnd
                    : AlignmentDirectional.center,
                child: SizedBox(
                  width: desktop ? 280 : double.infinity,
                  child: FilledButton.icon(
                    key: const Key('save-log-button'),
                    onPressed: saving || !enabled ? null : onSave,
                    icon: saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.check_rounded),
                    label: Text(saving ? l10n.journalSaving : l10n.journalSave),
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(54),
                      backgroundColor: AminaTheme.teal600,
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: isDark
                          ? AminaTheme.dark600
                          : AminaTheme.ink200,
                      disabledForegroundColor: isDark
                          ? AminaTheme.dark300
                          : AminaTheme.ink500,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
