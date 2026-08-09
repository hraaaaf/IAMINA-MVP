import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/drift/database.dart';
import '../../../l10n/app_localizations.dart';
import '../../journal/widgets/meal_capture_panel.dart';

/// Deterministic entry-safety classification for a single normalized reading.
///
/// Threshold source: American Diabetes Association, Standards of Care in
/// Diabetes—2026, Section 6: level 1 hypoglycemia is <70 and >=54 mg/dL;
/// level 2 hypoglycemia is <54 mg/dL. This function does not diagnose, prescribe,
/// or calculate treatment.
enum GlucoseEntrySafety { level2Low, level1Low, nonLow }

GlucoseEntrySafety classifyGlucoseEntrySafety(double mgdl) {
  if (mgdl < 54) return GlucoseEntrySafety.level2Low;
  if (mgdl < 70) return GlucoseEntrySafety.level1Low;
  return GlucoseEntrySafety.nonLow;
}

/// Express metabolic-event capture.
///
/// The primary path records a glucose value, optional measurement context and
/// optional meal. Treatment context and daily-state details remain secondary.
/// Measurement context and meal category are persisted independently; neither
/// is inferred when the patient does not select it.
class AddLogSheet extends StatefulWidget {
  final bool isPage;

  const AddLogSheet({super.key, this.isPage = false});

  @override
  State<AddLogSheet> createState() => _AddLogSheetState();
}

class _AddLogSheetState extends State<AddLogSheet> {
  final TextEditingController _glucoseController = TextEditingController();
  final TextEditingController _insulinController = TextEditingController();
  final TextEditingController _mealNoteController = TextEditingController();
  final List<String> _selectedMealItemIds = <String>[];

  String? _glycemicContext;
  String? _mealType;
  DateTime _selectedTime = DateTime.now();
  bool _mealExpanded = false;
  bool _detailsExpanded = false;
  bool _saving = false;
  bool _isSick = false;
  bool _isStressed = false;
  bool _isActive = false;
  bool _badSleep = false;

  static const List<String> _glycemicContexts = <String>[
    'fasting',
    'pre_meal',
    'post_meal',
    'other',
  ];

  static const List<String> _mealTypes = <String>[
    'breakfast',
    'lunch',
    'dinner',
    'snack',
  ];

  @override
  void dispose() {
    _glucoseController.dispose();
    _insulinController.dispose();
    _mealNoteController.dispose();
    super.dispose();
  }

  double? _displayGlucose() =>
      double.tryParse(_glucoseController.text.trim().replaceAll(',', '.'));

  double? _mgdlGlucose(String unit) {
    final value = _displayGlucose();
    if (value == null) return null;
    return unit == 'mmol/L' ? value * 18.0 : value;
  }

  bool get _hasUnsavedData =>
      _glucoseController.text.trim().isNotEmpty ||
      _insulinController.text.trim().isNotEmpty ||
      _glycemicContext != null ||
      _mealType != null ||
      _selectedMealItemIds.isNotEmpty ||
      _mealNoteController.text.trim().isNotEmpty ||
      _isSick ||
      _isStressed ||
      _isActive ||
      _badSleep;

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final profile = context.watch<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';
    final l10n = AppLocalizations.of(context)!;
    final isDesktop = MediaQuery.sizeOf(context).width >= 1000;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        if (await _confirmLeave(l10n) && mounted) _close();
      },
      child: ColoredBox(
        color: AminaTheme.bg(context),
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
                        _header(l10n),
                        const SizedBox(height: 22),
                        if (isDesktop)
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Expanded(
                                flex: 6,
                                child: _primaryEvent(
                                  l10n,
                                  unit,
                                  profile?.aiConsentGivenAt != null,
                                ),
                              ),
                              const SizedBox(width: 28),
                              Expanded(flex: 4, child: _detailsCard(l10n)),
                            ],
                          )
                        else ...<Widget>[
                          _primaryEvent(
                            l10n,
                            unit,
                            profile?.aiConsentGivenAt != null,
                          ),
                          const SizedBox(height: 18),
                          if (!_detailsExpanded)
                            _detailsButton(l10n)
                          else
                            _detailsCard(l10n),
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
                child: _saveBar(db, unit, l10n),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _header(AppLocalizations l10n) => Row(
    children: <Widget>[
      IconButton(
        tooltip: l10n.journalBack,
        onPressed: () async {
          if (await _confirmLeave(l10n) && mounted) _close();
        },
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

  Widget _primaryEvent(
    AppLocalizations l10n,
    String unit,
    bool canUsePhotoRecognition,
  ) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: <Widget>[
      _glucoseCard(l10n, unit),
      const SizedBox(height: 22),
      _measurementContext(l10n),
      const SizedBox(height: 22),
      _mealCapture(l10n, canUsePhotoRecognition),
    ],
  );

  Widget _glucoseCard(AppLocalizations l10n, String unit) {
    final mgdl = _mgdlGlucose(unit);
    final isLow = mgdl != null && mgdl < 70;

    return Semantics(
      container: true,
      label: l10n.journalGlucose,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isLow ? const Color(0xFFFFF7ED) : AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: isLow
                ? const Color(0xFFF97316)
                : AminaTheme.divider(context),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _sectionLabel(l10n.journalGlucose),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('glucose-input'),
                    controller: _glucoseController,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    inputFormatters: <TextInputFormatter>[
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
                    ],
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 48,
                      fontWeight: FontWeight.w800,
                    ),
                    decoration: const InputDecoration(
                      hintText: '—',
                      border: InputBorder.none,
                      isDense: true,
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text(
                    unit,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            if (mgdl == null)
              Text(l10n.journalNoGlucoseAssumption, style: _helperStyle())
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
              Text(l10n.journalTargetNotInferred, style: _helperStyle()),
          ],
        ),
      ),
    );
  }

  Widget _measurementContext(AppLocalizations l10n) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      _sectionLabel(l10n.journalMeasurementContext),
      const SizedBox(height: 5),
      Text(l10n.journalContextHint, style: _helperStyle()),
      const SizedBox(height: 11),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: _glycemicContexts.map((value) {
          return ChoiceChip(
            key: Key('glycemic-context-$value'),
            label: Text(_contextLabel(l10n, value)),
            selected: _glycemicContext == value,
            onSelected: (selected) => setState(() {
              _glycemicContext = selected ? value : null;
            }),
          );
        }).toList(),
      ),
    ],
  );

  Widget _mealCapture(AppLocalizations l10n, bool canUsePhotoRecognition) {
    if (!_mealExpanded) {
      return OutlinedButton.icon(
        key: const Key('add-meal-button'),
        onPressed: () => setState(() => _mealExpanded = true),
        icon: const Icon(Icons.restaurant_outlined, size: 18),
        label: Text('${l10n.journalAddMeal} · ${l10n.journalOptional}'),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          alignment: AlignmentDirectional.centerStart,
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
              Expanded(child: _sectionLabel(l10n.journalMealOptional)),
              TextButton(
                onPressed: () => setState(() {
                  _mealExpanded = false;
                  _mealType = null;
                  _selectedMealItemIds.clear();
                  _mealNoteController.clear();
                }),
                child: Text(l10n.journalRemoveMeal),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _mealTypes.map((value) {
              return ChoiceChip(
                key: Key('meal-type-$value'),
                label: Text(_mealLabel(l10n, value)),
                selected: _mealType == value,
                onSelected: (selected) => setState(() {
                  _mealType = selected ? value : null;
                }),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          MealCapturePanel(
            selectedIds: _selectedMealItemIds,
            canUsePhotoRecognition: canUsePhotoRecognition,
            onChanged: (ids) => setState(() {
              _selectedMealItemIds
                ..clear()
                ..addAll(ids);
            }),
          ),
          const SizedBox(height: 16),
          TextField(
            key: const Key('meal-note-input'),
            controller: _mealNoteController,
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

  Widget _detailsButton(AppLocalizations l10n) => OutlinedButton.icon(
    key: const Key('journal-details-button'),
    onPressed: () => setState(() => _detailsExpanded = true),
    icon: const Icon(Icons.tune_rounded, size: 18),
    label: Text(l10n.journalDetailsButton),
    style: OutlinedButton.styleFrom(
      minimumSize: const Size.fromHeight(50),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  );

  Widget _detailsCard(AppLocalizations l10n) => Container(
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
        _timeRow(l10n),
        const SizedBox(height: 20),
        _insulinSection(l10n),
        const SizedBox(height: 20),
        _healthContext(l10n),
      ],
    ),
  );

  Widget _timeRow(AppLocalizations l10n) => InkWell(
    borderRadius: BorderRadius.circular(14),
    onTap: _pickDateTime,
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
          Expanded(child: Text(_timeLabel(l10n))),
          const Icon(Icons.edit_outlined, size: 16),
        ],
      ),
    ),
  );

  Widget _insulinSection(AppLocalizations l10n) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      _sectionLabel(l10n.journalInsulinTaken),
      const SizedBox(height: 5),
      Text(l10n.journalInsulinExplanation, style: _helperStyle()),
      const SizedBox(height: 10),
      TextField(
        key: const Key('insulin-taken-input'),
        controller: _insulinController,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        inputFormatters: <TextInputFormatter>[
          FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
        ],
        decoration: InputDecoration(
          labelText: l10n.journalDoseTaken,
          suffixText: 'U',
          hintText: l10n.journalOptional,
          border: const OutlineInputBorder(),
        ),
      ),
    ],
  );

  Widget _healthContext(AppLocalizations l10n) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: <Widget>[
      _sectionLabel(l10n.journalAdditionalContext),
      const SizedBox(height: 10),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: <Widget>[
          FilterChip(
            label: Text(l10n.journalSick),
            selected: _isSick,
            onSelected: (value) => setState(() => _isSick = value),
          ),
          FilterChip(
            label: Text(l10n.journalUnusualStress),
            selected: _isStressed,
            onSelected: (value) => setState(() => _isStressed = value),
          ),
          FilterChip(
            label: Text(l10n.journalPhysicalActivity),
            selected: _isActive,
            onSelected: (value) => setState(() => _isActive = value),
          ),
          FilterChip(
            label: Text(l10n.journalPoorSleep),
            selected: _badSleep,
            onSelected: (value) => setState(() => _badSleep = value),
          ),
        ],
      ),
    ],
  );

  Widget _sectionLabel(String text) => Text(
    text,
    style: TextStyle(
      color: AminaTheme.textSecondary(context),
      fontSize: 11,
      fontWeight: FontWeight.w800,
      letterSpacing: .55,
    ),
  );

  TextStyle _helperStyle() => TextStyle(
    color: AminaTheme.textSecondary(context),
    fontSize: 12,
    height: 1.4,
  );

  String _contextLabel(AppLocalizations l10n, String value) => switch (value) {
    'fasting' => l10n.journalContextFasting,
    'pre_meal' => l10n.journalContextPreMeal,
    'post_meal' => l10n.journalContextPostMeal,
    _ => l10n.journalContextOther,
  };

  String _mealLabel(AppLocalizations l10n, String value) => switch (value) {
    'breakfast' => l10n.journalMealBreakfast,
    'lunch' => l10n.journalMealLunch,
    'dinner' => l10n.journalMealDinner,
    _ => l10n.journalMealSnack,
  };

  String _timeLabel(AppLocalizations l10n) {
    final now = DateTime.now();
    final sameDay =
        _selectedTime.year == now.year &&
        _selectedTime.month == now.month &&
        _selectedTime.day == now.day;
    final hh = _selectedTime.hour.toString().padLeft(2, '0');
    final mm = _selectedTime.minute.toString().padLeft(2, '0');
    if (sameDay) return '${l10n.journalToday} · $hh:$mm';
    final dd = _selectedTime.day.toString().padLeft(2, '0');
    final mo = _selectedTime.month.toString().padLeft(2, '0');
    return '$dd/$mo · $hh:$mm';
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedTime,
      firstDate: DateTime.now().subtract(const Duration(days: 90)),
      lastDate: DateTime.now(),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_selectedTime),
    );
    if (time == null || !mounted) return;
    setState(() {
      _selectedTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  Widget _saveBar(AppDatabase db, String unit, AppLocalizations l10n) =>
      Container(
        padding: const EdgeInsets.fromLTRB(20, 10, 20, 14),
        decoration: BoxDecoration(
          color: AminaTheme.bg(context),
          border: Border(top: BorderSide(color: AminaTheme.divider(context))),
        ),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1080),
            child: FilledButton.icon(
              onPressed: _saving ? null : () => _saveLog(db, unit, l10n),
              icon: _saving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.check_rounded),
              label: Text(_saving ? l10n.journalSaving : l10n.journalSave),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(54),
                backgroundColor: AminaTheme.teal600,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
        ),
      );

  Future<bool> _confirmLowGlucose(double mgdl, AppLocalizations l10n) async {
    final level = classifyGlucoseEntrySafety(mgdl);
    if (level == GlucoseEntrySafety.nonLow) return true;

    final level2 = level == GlucoseEntrySafety.level2Low;
    final proceed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        key: Key(level2 ? 'level2-low-dialog' : 'level1-low-dialog'),
        title: Text(level2 ? l10n.journalVeryLowTitle : l10n.journalLowTitle),
        content: Text(
          level2 ? l10n.journalVeryLowSafety : l10n.journalLowSafety,
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(l10n.journalBackToEntry),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(l10n.journalSaveAnyway),
          ),
        ],
      ),
    );
    return proceed == true;
  }

  Future<void> _saveLog(
    AppDatabase db,
    String unit,
    AppLocalizations l10n,
  ) async {
    final glucose = _displayGlucose();
    final mgdl = _mgdlGlucose(unit);
    if (glucose == null || mgdl == null || glucose <= 0) {
      _message(l10n.journalInvalidGlucose);
      return;
    }

    if (!await _confirmLowGlucose(mgdl, l10n) || !mounted) return;

    final insulinRaw = _insulinController.text.trim().replaceAll(',', '.');
    final insulin = insulinRaw.isEmpty ? null : double.tryParse(insulinRaw);
    if (insulinRaw.isNotEmpty && (insulin == null || insulin < 0)) {
      _message(l10n.journalInvalidInsulin);
      return;
    }

    setState(() => _saving = true);
    try {
      final note = _mealNoteController.text.trim();
      await db
          .into(db.logEntries)
          .insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime.now(),
              bloodSugar: mgdl,
              insulinUnits: drift.Value(insulin),
              glycemicContext: drift.Value(_glycemicContext),
              mealType: drift.Value(_mealType),
              mealDescription: drift.Value(note.isEmpty ? null : note),
              mealItemsJson: drift.Value(
                encodeMealItemIds(_selectedMealItemIds),
              ),
              clientUuid: const Uuid().v4(),
              loggedAt: drift.Value(_selectedTime),
              isSick: drift.Value(_isSick),
              isStressed: drift.Value(_isStressed),
              isTired: const drift.Value(false),
              isActive: drift.Value(_isActive),
              sleepQuality: drift.Value(_badSleep ? 'bad' : null),
              fatigueLevel: const drift.Value(null),
            ),
          );

      if (!mounted) return;
      HapticFeedback.mediumImpact();
      _message(l10n.journalSaved);
      _close();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _message(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  Future<bool> _confirmLeave(AppLocalizations l10n) async {
    if (!_hasUnsavedData) return true;
    final leave = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(l10n.journalDiscardTitle),
        content: Text(l10n.journalDiscardBody),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(l10n.journalContinueEditing),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(l10n.journalDiscard),
          ),
        ],
      ),
    );
    return leave == true;
  }

  void _close() {
    if (widget.isPage) {
      GoRouter.of(context).go('/dashboard');
    } else {
      Navigator.maybePop(context);
    }
  }
}
