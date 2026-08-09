import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../l10n/app_localizations.dart';
import '../dashboard/widgets/add_log_sheet.dart';
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
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadLog();
  }

  @override
  void dispose() {
    _glucoseController.dispose();
    _insulinController.dispose();
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

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => Navigator.of(context).maybePop(),
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
        ),
        title: Text(l10n.journalEditTitle),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 680),
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
                        _glucoseCard(l10n, unit),
                        const SizedBox(height: 18),
                        _insulinCard(l10n),
                        const SizedBox(height: 14),
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AminaTheme.subtleBg(context),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: AminaTheme.divider(context),
                            ),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              const Icon(Icons.lock_outline_rounded, size: 17),
                              const SizedBox(width: 9),
                              Expanded(
                                child: Text(
                                  l10n.journalEditContextPreserved,
                                  style: TextStyle(
                                    color: AminaTheme.textSecondary(context),
                                    fontSize: 12,
                                    height: 1.4,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 24),
                        FilledButton.icon(
                          key: const Key('save-edit-log-button'),
                          onPressed: _saving
                              ? null
                              : () => _saveChanges(unit, l10n),
                          icon: _saving
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.check_rounded),
                          label: Text(_saving ? l10n.journalSaving : l10n.save),
                          style: FilledButton.styleFrom(
                            minimumSize: const Size.fromHeight(54),
                            backgroundColor: AminaTheme.teal600,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
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
          syncStatus: const drift.Value('pending'),
          syncAttempts: const drift.Value(0),
          errorSync: const drift.Value(false),
        ),
      );
      if (!mounted) return;
      _message(l10n.journalUpdated);
      await Navigator.of(context).maybePop();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _message(String text) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }
}
