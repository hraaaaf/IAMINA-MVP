import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';

class PostSaveReceiptData {
  final double glucose;
  final String unit;
  final String timeLabel;
  final String? measurementContextLabel;
  final String? mealTypeLabel;
  final double? insulinUnits;
  final List<String> additionalContextLabels;

  const PostSaveReceiptData({
    required this.glucose,
    required this.unit,
    required this.timeLabel,
    this.measurementContextLabel,
    this.mealTypeLabel,
    this.insulinUnits,
    this.additionalContextLabels = const <String>[],
  });
}

class PostSaveReceipt extends StatelessWidget {
  final PostSaveReceiptData data;
  final VoidCallback onViewJournal;
  final VoidCallback onAddAnother;
  final VoidCallback onDone;

  const PostSaveReceipt({
    super.key,
    required this.data,
    required this.onViewJournal,
    required this.onAddAnother,
    required this.onDone,
  });

  String _number(double value) {
    if (value == value.roundToDouble()) return value.toInt().toString();
    return value
        .toStringAsFixed(2)
        .replaceFirst(RegExp(r'0+$'), '')
        .replaceFirst(RegExp(r'\.$'), '');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return ColoredBox(
      color: AminaTheme.bg(context),
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 600;
            if (!compact) {
              return SingleChildScrollView(
                padding: const EdgeInsetsDirectional.fromSTEB(20, 28, 20, 32),
                child: Column(
                  children: <Widget>[
                    _receiptBody(context, l10n),
                    const SizedBox(height: 20),
                    _actions(context, l10n, compact: false),
                  ],
                ),
              );
            }

            return Column(
              children: <Widget>[
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsetsDirectional.fromSTEB(
                      20,
                      20,
                      20,
                      14,
                    ),
                    child: _receiptBody(context, l10n),
                  ),
                ),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsetsDirectional.fromSTEB(20, 10, 20, 10),
                  decoration: BoxDecoration(
                    color: AminaTheme.bg(context),
                    border: Border(
                      top: BorderSide(color: AminaTheme.divider(context)),
                    ),
                  ),
                  child: _actions(context, l10n, compact: true),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _receiptBody(BuildContext context, AppLocalizations l10n) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Align(
              alignment: AlignmentDirectional.center,
              child: Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AminaTheme.teal600.withValues(alpha: 0.10),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check_rounded,
                  color: AminaTheme.teal600,
                  size: 34,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              l10n.journalSaved,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AminaTheme.textPrimary(context),
                fontSize: 24,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              l10n.journalPostSaveDeviceStatus,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AminaTheme.textSecondary(context),
                fontSize: 13,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: AminaTheme.subtleBg(context),
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: AminaTheme.divider(context)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    l10n.journalPostSaveSummaryTitle,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: .45,
                    ),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: <Widget>[
                      Expanded(
                        child: Text(
                          l10n.journalGlucose,
                          style: TextStyle(
                            color: AminaTheme.textSecondary(context),
                            fontSize: 13,
                          ),
                        ),
                      ),
                      Directionality(
                        textDirection: TextDirection.ltr,
                        child: Text(
                          '${_number(data.glucose)} ${data.unit}',
                          style: TextStyle(
                            color: AminaTheme.textPrimary(context),
                            fontSize: 22,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _FactRow(
                    icon: Icons.schedule_outlined,
                    label: data.timeLabel,
                  ),
                  if (data.measurementContextLabel != null) ...<Widget>[
                    const SizedBox(height: 10),
                    _FactRow(
                      icon: Icons.tune_rounded,
                      label:
                          '${l10n.journalMeasurementContext} · ${data.measurementContextLabel!}',
                    ),
                  ],
                  if (data.mealTypeLabel != null) ...<Widget>[
                    const SizedBox(height: 10),
                    _FactRow(
                      icon: Icons.restaurant_outlined,
                      label:
                          '${l10n.journalPostSaveMeal} · ${data.mealTypeLabel!}',
                    ),
                  ],
                  if (data.insulinUnits != null) ...<Widget>[
                    const SizedBox(height: 10),
                    _FactRow(
                      icon: Icons.medication_outlined,
                      label: l10n.journalInsulinTaken,
                      value: '${_number(data.insulinUnits!)} U',
                    ),
                  ],
                  if (data.additionalContextLabels.isNotEmpty) ...<Widget>[
                    const SizedBox(height: 14),
                    Text(
                      l10n.journalAdditionalContext,
                      style: TextStyle(
                        color: AminaTheme.textSecondary(context),
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 7,
                      runSpacing: 7,
                      children: data.additionalContextLabels
                          .map(
                            (label) => Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: AminaTheme.teal600.withValues(
                                  alpha: 0.08,
                                ),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                label,
                                style: const TextStyle(
                                  color: AminaTheme.teal600,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AminaTheme.teal600.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Icon(
                    Icons.info_outline_rounded,
                    size: 18,
                    color: AminaTheme.teal600,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      l10n.journalPostSaveNotice,
                      style: TextStyle(
                        color: AminaTheme.textSecondary(context),
                        fontSize: 11.5,
                        height: 1.45,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _actions(
    BuildContext context,
    AppLocalizations l10n, {
    required bool compact,
  }) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            FilledButton.icon(
              key: const Key('post-save-view-journal'),
              onPressed: onViewJournal,
              icon: const Icon(Icons.history_rounded, size: 18),
              label: Text(l10n.journalPostSaveViewJournal),
              style: FilledButton.styleFrom(
                minimumSize: Size.fromHeight(compact ? 48 : 52),
                backgroundColor: AminaTheme.teal600,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              key: const Key('post-save-add-another'),
              onPressed: onAddAnother,
              icon: const Icon(Icons.add_rounded, size: 18),
              label: Text(l10n.journalPostSaveAddAnother),
              style: OutlinedButton.styleFrom(
                minimumSize: Size.fromHeight(compact ? 46 : 50),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
            TextButton(
              key: const Key('post-save-done'),
              onPressed: onDone,
              style: TextButton.styleFrom(
                minimumSize: Size.fromHeight(compact ? 36 : 40),
              ),
              child: Text(l10n.journalPostSaveDone),
            ),
          ],
        ),
      ),
    );
  }
}

class _FactRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? value;

  const _FactRow({required this.icon, required this.label, this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, size: 17, color: AminaTheme.textSecondary(context)),
        const SizedBox(width: 9),
        Expanded(
          child: Text(
            label,
            style: TextStyle(
              color: AminaTheme.textPrimary(context),
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
              height: 1.35,
            ),
          ),
        ),
        if (value != null) ...<Widget>[
          const SizedBox(width: 10),
          Directionality(
            textDirection: TextDirection.ltr,
            child: Text(
              value!,
              style: TextStyle(
                color: AminaTheme.textPrimary(context),
                fontSize: 12.5,
                fontWeight: FontWeight.w700,
                height: 1.35,
              ),
            ),
          ),
        ],
      ],
    );
  }
}
