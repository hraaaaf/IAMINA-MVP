import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/data/meal_food_catalog.dart';
import '../../core/data/nutrition_catalog.dart';
import '../../core/data/ramadan_context.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../data/drift/database.dart';
import '../../l10n/app_localizations.dart';
import '../dashboard/widgets/add_log_sheet.dart';
import '../dashboard/widgets/add_log_view.dart';
import 'widgets/insulin_logging.dart';

class EditLogScreen extends StatefulWidget {
  final int logId;

  const EditLogScreen({super.key, required this.logId});

  @override
  State<EditLogScreen> createState() => _EditLogScreenState();
}

class _EditLogScreenState extends State<EditLogScreen> {
  final TextEditingController _glucoseController = TextEditingController();
  final TextEditingController _insulinController = TextEditingController();
  final TextEditingController _mealNoteController = TextEditingController();
  final List<String> _selectedMealItemIds = <String>[];
  final Map<String, MealPortionSelection> _mealPortionSelections =
      <String, MealPortionSelection>{};
  String? _glycemicContext;
  String? _mealType;
  DateTime _selectedTime = DateTime.now();
  bool _mealExpanded = false;
  bool _loading = true;
  bool _saving = false;
  bool _deleting = false;
  bool _isSick = false;
  bool _isStressed = false;
  bool _isActive = false;
  bool _badSleep = false;

  @override
  void initState() {
    super.initState();
    _loadLog();
  }

  @override
  void dispose() {
    _glucoseController.dispose();
    _insulinController.dispose();
    _mealNoteController.dispose();
    super.dispose();
  }

  Future<void> _loadLog() async {
    final db = context.read<AppDatabase>();
    final profile = context.read<PatientProfileData?>();
    final log = await db.getLogById(widget.logId);
    if (!mounted) return;
    if (log == null) {
      setState(() => _loading = false);
      return;
    }
    final unit = profile?.unitPreference ?? 'mg/dL';
    final display = unit == 'mmol/L' ? log.bloodSugar / 18.0 : log.bloodSugar;
    _glucoseController.text = display.toStringAsFixed(unit == 'mmol/L' ? 1 : 0);
    _insulinController.text = log.insulinUnits == null
        ? ''
        : formatTakenInsulinUnits(log.insulinUnits!);
    _glycemicContext = log.glycemicContext;
    _mealType = log.mealType;
    _mealNoteController.text = log.mealDescription ?? '';
    _selectedMealItemIds
      ..clear()
      ..addAll(decodeMealItemIds(log.mealItemsJson));
    _mealPortionSelections
      ..clear()
      ..addEntries(
        decodeMealPortionSelections(log.mealPortionsJson).map(
          (selection) => MapEntry(selection.foodId, selection),
        ),
      );
    _selectedTime = log.loggedAt ?? log.createdAt;
    _mealExpanded =
        _mealType != null ||
        _mealNoteController.text.trim().isNotEmpty ||
        _selectedMealItemIds.isNotEmpty;
    _isSick = log.isSick;
    _isStressed = log.isStressed;
    _isActive = log.isActive;
    _badSleep = log.sleepQuality == 'bad';
    setState(() => _loading = false);
  }

  double? _displayGlucose() =>
      double.tryParse(_glucoseController.text.trim().replaceAll(',', '.'));

  double? _mgdlGlucose(String unit) {
    final value = _displayGlucose();
    if (value == null) return null;
    return unit == 'mmol/L' ? value * 18.0 : value;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final profile = context.watch<PatientProfileData?>();
    final unit = profile?.unitPreference ?? 'mg/dL';
    final desktop = MediaQuery.sizeOf(context).width >= 900;

    return Scaffold(
      appBar: AppBar(
        leading: const AminaPageExitButton(),
        title: Text(l10n.journalEditTitle),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: EdgeInsetsDirectional.fromSTEB(
                  20,
                  desktop ? 28 : 12,
                  20,
                  32,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      maxWidth: desktop ? 960 : 680,
                    ),
                    child: Container(
                      padding: desktop
                          ? const EdgeInsets.all(24)
                          : EdgeInsets.zero,
                      decoration: desktop
                          ? BoxDecoration(
                              color: AminaTheme.surface(context),
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(
                                color: AminaTheme.divider(context),
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.04),
                                  blurRadius: 28,
                                  offset: const Offset(0, 12),
                                ),
                              ],
                            )
                          : null,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: <Widget>[
                          Text(
                            l10n.journalEditSubtitle,
                            style: TextStyle(
                              color: AminaTheme.textSecondary(context),
                              fontSize: 13,
                              height: 1.45,
                            ),
                          ),
                          const SizedBox(height: 20),
                          if (desktop)
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(child: _glucoseCard(l10n, unit)),
                                const SizedBox(width: 18),
                                Expanded(child: _insulinCard(l10n)),
                              ],
                            )
                          else ...[
                            _glucoseCard(l10n, unit),
                            const SizedBox(height: 18),
                            _insulinCard(l10n),
                          ],
                          const SizedBox(height: 18),
                          AddLogMeasurementContext(
                            selected: _glycemicContext,
                            onChanged: (value) =>
                                setState(() => _glycemicContext = value),
                          ),
                          const SizedBox(height: 18),
                          AddLogMealCapture(
                            expanded: _mealExpanded,
                            ramadanActive: isRamadanProfileDate(
                              _selectedTime,
                              profile?.ramadanStartDate,
                              profile?.ramadanEndDate,
                            ),
                            mealTypes: mealTypesForProfileDate(
                              _selectedTime,
                              profile?.ramadanStartDate,
                              profile?.ramadanEndDate,
                            ),
                            selectedMealType: _mealType,
                            selectedMealItemIds: _selectedMealItemIds,
                            mealPortionSelections: _mealPortionSelections,
                            mealNoteController: _mealNoteController,
                            canUsePhotoRecognition: false,
                            voiceRecording: false,
                            voiceTranscribing: false,
                            showVoiceAction: false,
                            onVoiceToggle: () async {},
                            onExpand: () =>
                                setState(() => _mealExpanded = true),
                            onRemove: () => setState(() {
                              _mealExpanded = false;
                              _mealType = null;
                              _selectedMealItemIds.clear();
                              _mealPortionSelections.clear();
                              _mealNoteController.clear();
                            }),
                            onMealTypeChanged: (value) =>
                                setState(() => _mealType = value),
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
                          const SizedBox(height: 18),
                          AddLogDetailsCard(
                            timeLabel: addLogTimeLabel(l10n, _selectedTime),
                            onPickDateTime: _pickDateTime,
                            isSick: _isSick,
                            isStressed: _isStressed,
                            isActive: _isActive,
                            badSleep: _badSleep,
                            onSickChanged: (value) =>
                                setState(() => _isSick = value),
                            onStressedChanged: (value) =>
                                setState(() => _isStressed = value),
                            onActiveChanged: (value) =>
                                setState(() => _isActive = value),
                            onBadSleepChanged: (value) =>
                                setState(() => _badSleep = value),
                          ),
                          const SizedBox(height: 24),
                          _actionButtons(unit, l10n),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _actionButtons(String unit, AppLocalizations l10n) {
    final save = FilledButton.icon(
      key: const Key('save-edit-log-button'),
      onPressed: _saving || _deleting ? null : () => _saveChanges(unit, l10n),
      icon: _saving
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.check_rounded),
      label: Text(_saving ? l10n.journalSaving : l10n.save),
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(54),
        backgroundColor: AminaTheme.teal600,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );

    final delete = OutlinedButton.icon(
      key: const Key('delete-edit-log-button'),
      onPressed: _saving || _deleting ? null : () => _deleteLog(l10n),
      icon: _deleting
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Icon(Icons.delete_outline_rounded),
      label: Text(l10n.delete),
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(50),
        foregroundColor: AminaTheme.dangerRed,
        side: BorderSide(color: AminaTheme.dangerRed.withValues(alpha: 0.35)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );

    if (MediaQuery.sizeOf(context).width < 900) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [save, const SizedBox(height: 12), delete],
      );
    }

    return Row(
      children: [
        SizedBox(width: 220, child: save),
        const SizedBox(width: 12),
        SizedBox(width: 180, child: delete),
      ],
    );
  }

  Widget _glucoseCard(AppLocalizations l10n, String unit) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: AminaTheme.subtleBg(context),
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          l10n.journalGlucose,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: .55,
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          key: const Key('edit-glucose-input'),
          controller: _glucoseController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          inputFormatters: <TextInputFormatter>[
            FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
          ],
          decoration: InputDecoration(
            suffixText: unit,
            border: const OutlineInputBorder(),
          ),
        ),
      ],
    ),
  );

  Widget _insulinCard(AppLocalizations l10n) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: AminaTheme.subtleBg(context),
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          l10n.journalInsulinTaken,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: .55,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          l10n.journalInsulinExplanation,
          style: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 12,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 10),
        TextField(
          key: const Key('edit-insulin-taken-input'),
          controller: _insulinController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          inputFormatters: <TextInputFormatter>[
            FilteringTextInputFormatter.allow(RegExp(r'[0-9,.]')),
          ],
          decoration: InputDecoration(
            labelText: l10n.journalDoseTaken,
            suffixText: 'U',
            hintText: l10n.journalOptional,
            helperText: l10n.journalNoInsulinTakenHint,
            helperMaxLines: 2,
            border: const OutlineInputBorder(),
          ),
        ),
      ],
    ),
  );

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

  Future<void> _saveChanges(String unit, AppLocalizations l10n) async {
    final glucose = _displayGlucose();
    final mgdl = _mgdlGlucose(unit);
    if (glucose == null || mgdl == null || glucose <= 0) {
      _message(l10n.journalInvalidGlucose);
      return;
    }
    if (!isValidTakenInsulinInput(_insulinController.text)) {
      _message(l10n.journalInvalidInsulin);
      return;
    }
    if (!await _confirmLowGlucose(mgdl, l10n) || !mounted) return;

    setState(() => _saving = true);
    try {
      final db = context.read<AppDatabase>();
      await db.updateLog(
        widget.logId,
        LogEntriesCompanion(
          bloodSugar: drift.Value(mgdl),
          insulinUnits: drift.Value(
            parseTakenInsulinUnits(_insulinController.text),
          ),
          glycemicContext: drift.Value(_glycemicContext),
          mealType: drift.Value(_mealType),
          mealDescription: drift.Value(
            _mealNoteController.text.trim().isEmpty
                ? null
                : _mealNoteController.text.trim(),
          ),
          mealItemsJson: drift.Value(encodeMealItemIds(_selectedMealItemIds)),
          mealPortionsJson: drift.Value(
            encodeMealPortionSelections(_mealPortionSelections.values),
          ),
          loggedAt: drift.Value(_selectedTime),
          isSick: drift.Value(_isSick),
          isStressed: drift.Value(_isStressed),
          isActive: drift.Value(_isActive),
          sleepQuality: drift.Value(_badSleep ? 'bad' : null),
          syncStatus: const drift.Value('pending'),
          syncAttempts: const drift.Value(0),
          errorSync: const drift.Value(false),
        ),
      );
      if (!mounted) return;
      _message(l10n.journalUpdated);
      _leavePage();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _deleteLog(AppLocalizations l10n) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(l10n.deleteEntryTitle),
        content: Text(l10n.actionIrreversible),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(
              l10n.delete,
              style: const TextStyle(color: AminaTheme.dangerRed),
            ),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _deleting = true);
    try {
      final db = context.read<AppDatabase>();
      await db.deleteLog(widget.logId);
      if (!mounted) return;
      _leavePage();
    } finally {
      if (mounted) setState(() => _deleting = false);
    }
  }

  void _leavePage() {
    final router = GoRouter.of(context);
    if (router.canPop()) {
      router.pop();
    } else {
      router.go('/journal');
    }
  }

  void _message(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }
}
