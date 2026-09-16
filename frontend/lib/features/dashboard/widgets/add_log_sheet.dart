import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../../core/data/meal_food_catalog.dart';
import '../../../core/data/nutrition_catalog.dart';
import '../../../core/data/ramadan_context.dart';
import '../../../data/drift/database.dart';
import '../../../l10n/app_localizations.dart';
import '../../journal/widgets/post_save_receipt.dart';
import 'add_log_view.dart';

/// Deterministic entry-safety classification for a single normalized reading.
///
/// Threshold source: American Diabetes Association, Standards of Care in
/// Diabetes—2026, Section 6: level 1 hypoglycemia is <70 and >=54 mg/dL;
/// level 2 hypoglycemia is <54 mg/dL. This function does not diagnose,
/// prescribe, or calculate treatment.
enum GlucoseEntrySafety { level2Low, level1Low, nonLow }

GlucoseEntrySafety classifyGlucoseEntrySafety(double mgdl) {
  if (mgdl < 54) return GlucoseEntrySafety.level2Low;
  if (mgdl < 70) return GlucoseEntrySafety.level1Low;
  return GlucoseEntrySafety.nonLow;
}

/// Focuses the glucose-entry flow on an optional related context.
///
/// Medication intake, including insulin, is intentionally not represented here:
/// Medications is the canonical intake journal. Add Log records a glucose
/// reading and only contextual facts that belong to that reading.
enum AddLogFocus { none, meal, activity }

class AddLogSheet extends StatefulWidget {
  final bool isPage;
  final AddLogFocus focus;

  const AddLogSheet({
    super.key,
    this.isPage = false,
    this.focus = AddLogFocus.none,
  });

  @override
  State<AddLogSheet> createState() => _AddLogSheetState();
}

class _AddLogSheetState extends State<AddLogSheet> {
  final TextEditingController _glucoseController = TextEditingController();
  final TextEditingController _mealNoteController = TextEditingController();
  final List<String> _selectedMealItemIds = <String>[];
  final Map<String, MealPortionSelection> _mealPortionSelections =
      <String, MealPortionSelection>{};

  String? _glycemicContext;
  String? _mealType;
  DateTime _selectedTime = DateTime.now();
  bool _mealExpanded = false;
  bool _detailsExpanded = false;
  bool _contextExpanded = false;
  bool _saving = false;
  bool _isSick = false;
  bool _isStressed = false;
  bool _isActive = false;
  bool _badSleep = false;
  PostSaveReceiptData? _savedReceipt;

  @override
  void initState() {
    super.initState();
    _mealExpanded = widget.focus == AddLogFocus.meal;
    _detailsExpanded = widget.focus == AddLogFocus.activity;
    _contextExpanded = widget.focus == AddLogFocus.activity;
  }

  @override
  void dispose() {
    _glucoseController.dispose();
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

  bool get _hasValidGlucose {
    final value = _displayGlucose();
    return value != null && value > 0;
  }

  bool get _hasUnsavedData =>
      _glucoseController.text.trim().isNotEmpty ||
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

    final savedReceipt = _savedReceipt;
    if (savedReceipt != null) {
      return PostSaveReceipt(
        key: const Key('post-save-receipt'),
        data: savedReceipt,
        onViewJournal: _openJournal,
        onAddAnother: () => setState(() => _savedReceipt = null),
        onDone: _close,
      );
    }

    final ramadanActive = isRamadanProfileDate(
      _selectedTime,
      profile?.ramadanStartDate,
      profile?.ramadanEndDate,
    );
    final mealTypes = mealTypesForProfileDate(
      _selectedTime,
      profile?.ramadanStartDate,
      profile?.ramadanEndDate,
    );

    final primaryEvent = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        AddLogGlucoseCard(
          controller: _glucoseController,
          unit: unit,
          mgdl: _mgdlGlucose(unit),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 18),
        AddLogMeasurementContext(
          selected: _glycemicContext,
          onChanged: (value) => setState(() => _glycemicContext = value),
        ),
        const SizedBox(height: 18),
        AddLogMealCapture(
          expanded: _mealExpanded,
          ramadanActive: ramadanActive,
          mealTypes: mealTypes,
          selectedMealType: _mealType,
          selectedMealItemIds: _selectedMealItemIds,
          mealPortionSelections: _mealPortionSelections,
          mealNoteController: _mealNoteController,
          canUsePhotoRecognition: profile?.aiConsentGivenAt != null,
          onExpand: () => setState(() => _mealExpanded = true),
          onRemove: () => setState(() {
            _mealExpanded = false;
            _mealType = null;
            _selectedMealItemIds.clear();
            _mealPortionSelections.clear();
            _mealNoteController.clear();
          }),
          onMealTypeChanged: (value) => setState(() => _mealType = value),
          onSelectedMealItemIdsChanged: (ids) => setState(() {
            _selectedMealItemIds
              ..clear()
              ..addAll(ids);
            _mealPortionSelections.removeWhere(
              (foodId, _) => !ids.contains(foodId),
            );
          }),
          onPortionsChanged: (next) => setState(() {
            _mealPortionSelections
              ..clear()
              ..addAll(next);
          }),
        ),
      ],
    );

    final detailsCard = AddLogDetailsCard(
      timeLabel: addLogTimeLabel(l10n, _selectedTime),
      onPickDateTime: _pickDateTime,
      contextExpanded: _contextExpanded,
      isSick: _isSick,
      isStressed: _isStressed,
      isActive: _isActive,
      badSleep: _badSleep,
      onExpandContext: () => setState(() => _contextExpanded = true),
      onCollapseContext: () => setState(() => _contextExpanded = false),
      onSickChanged: (value) => setState(() => _isSick = value),
      onStressedChanged: (value) => setState(() => _isStressed = value),
      onActiveChanged: (value) => setState(() => _isActive = value),
      onBadSleepChanged: (value) => setState(() => _badSleep = value),
    );

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        if (await _confirmLeave(l10n) && mounted) _close();
      },
      child: AddLogSurface(
        isPage: widget.isPage,
        onBack: () async {
          if (await _confirmLeave(l10n) && mounted) _close();
        },
        primaryEvent: primaryEvent,
        detailsCard: detailsCard,
        detailsExpanded: _detailsExpanded,
        onShowDetails: () => setState(() => _detailsExpanded = true),
        saveBar: AddLogSaveBar(
          saving: _saving,
          enabled: _hasValidGlucose,
          onSave: () => _saveLog(db, unit, l10n),
        ),
      ),
    );
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
    final profile = context.read<PatientProfileData?>();
    setState(() {
      _selectedTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
      final allowed = mealTypesForProfileDate(
        _selectedTime,
        profile?.ramadanStartDate,
        profile?.ramadanEndDate,
      );
      if (_mealType != null && !allowed.contains(_mealType)) {
        _mealType = null;
      }
    });
  }

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

    setState(() => _saving = true);
    try {
      final note = _mealNoteController.text.trim();
      await db
          .into(db.logEntries)
          .insert(
            LogEntriesCompanion.insert(
              createdAt: DateTime.now(),
              bloodSugar: mgdl,
              insulinUnits: const drift.Value(null),
              glycemicContext: drift.Value(_glycemicContext),
              mealType: drift.Value(_mealType),
              mealDescription: drift.Value(note.isEmpty ? null : note),
              mealItemsJson: drift.Value(
                encodeMealItemIds(_selectedMealItemIds),
              ),
              mealPortionsJson: drift.Value(
                encodeMealPortionSelections(_mealPortionSelections.values),
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

      final receipt = PostSaveReceiptData(
        glucose: glucose,
        unit: unit,
        timeLabel: addLogTimeLabel(l10n, _selectedTime),
        measurementContextLabel: _glycemicContext == null
            ? null
            : addLogContextLabel(l10n, _glycemicContext!),
        mealTypeLabel: _mealType == null
            ? null
            : addLogMealLabel(l10n, _mealType!),
        additionalContextLabels: <String>[
          if (_isSick) l10n.journalSick,
          if (_isStressed) l10n.journalUnusualStress,
          if (_isActive) l10n.journalPhysicalActivity,
          if (_badSleep) l10n.journalPoorSleep,
        ],
      );

      if (!mounted) return;
      HapticFeedback.mediumImpact();
      _clearDraftForNextEntry();
      setState(() => _savedReceipt = receipt);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _clearDraftForNextEntry() {
    _glucoseController.clear();
    _mealNoteController.clear();
    _selectedMealItemIds.clear();
    _mealPortionSelections.clear();
    _glycemicContext = null;
    _mealType = null;
    _selectedTime = DateTime.now();
    _mealExpanded = false;
    _detailsExpanded = false;
    _contextExpanded = false;
    _isSick = false;
    _isStressed = false;
    _isActive = false;
    _badSleep = false;
  }

  Future<void> _openJournal() async {
    final router = GoRouter.of(context);
    if (!widget.isPage) {
      await Navigator.maybePop(context);
    }
    router.go('/journal');
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
