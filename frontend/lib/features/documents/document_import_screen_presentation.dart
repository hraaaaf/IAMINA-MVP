part of 'document_import_screen.dart';

class _PrivacyGateNotice extends StatelessWidget {
  const _PrivacyGateNotice();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      key: const ValueKey('document-privacy-gate'),
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.isDark(context)
            ? AminaTheme.dark700
            : AminaTheme.ink50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.shield_outlined,
            size: 20,
            color: AminaTheme.teal600,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.documentPrivacyTitle,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  l10n.privacyProcessingBody,
                  style: TextStyle(
                    fontSize: 12,
                    height: 1.45,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FormatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _FormatChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
    decoration: BoxDecoration(
      color: AminaTheme.isDark(context) ? AminaTheme.dark700 : AminaTheme.ink50,
      borderRadius: BorderRadius.circular(99),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AminaTheme.teal600),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: AminaTheme.textSecondary(context),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    ),
  );
}

class _ConfidenceBanner extends StatelessWidget {
  final double confidence;
  final bool needsReview;
  const _ConfidenceBanner({
    required this.confidence,
    required this.needsReview,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final pct = (confidence * 100).round();
    final color = confidence >= 0.7
        ? AminaTheme.teal500
        : confidence >= 0.4
        ? Colors.amber
        : Colors.red;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Icon(
            confidence >= 0.7 ? Icons.check_circle : Icons.info_outline,
            color: color,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.confidencePercent(pct),
                  style: TextStyle(fontWeight: FontWeight.w700, color: color),
                ),
                if (needsReview)
                  Text(
                    l10n.verifyBeforeConfirming,
                    style: const TextStyle(fontSize: 12),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  final String? subtitle;
  const _SectionTitle({required this.title, this.subtitle});

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w800,
          color: AminaTheme.textPrimary(context),
        ),
      ),
      if (subtitle != null)
        Text(
          subtitle!,
          style: TextStyle(
            fontSize: 13,
            color: AminaTheme.textSecondary(context),
          ),
        ),
    ],
  );
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final int? count;
  const _SectionHeader({required this.title, this.count});

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Text(
        title,
        style: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
          color: AminaTheme.textPrimary(context),
        ),
      ),
      if (count != null) ...[
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: AminaTheme.teal500.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(99),
          ),
          child: Text(
            '$count',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: AminaTheme.teal600,
            ),
          ),
        ),
      ],
    ],
  );
}

class _DocumentImportIcon extends StatelessWidget {
  const _DocumentImportIcon();

  @override
  Widget build(BuildContext context) {
    final compactHeight = MediaQuery.sizeOf(context).height <= 600;
    return Container(
      width: compactHeight ? 84 : 100,
      height: compactHeight ? 84 : 100,
      decoration: BoxDecoration(
        gradient: AminaTheme.heroGradient,
        shape: BoxShape.circle,
      ),
      child: Icon(
        Icons.upload_file,
        color: Colors.white,
        size: compactHeight ? 40 : 48,
      ),
    );
  }
}

class _GlucoseReadingsList extends StatelessWidget {
  final List<GlucoseReadingPreview> readings;
  const _GlucoseReadingsList({required this.readings});

  @override
  Widget build(BuildContext context) {
    final shown = readings.take(5).toList();
    final l10n = AppLocalizations.of(context)!;
    return Column(
      children: [
        ...shown.map((r) => _GlucoseRow(reading: r)),
        if (readings.length > 5)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              l10n.additionalReadings(readings.length - 5),
              style: TextStyle(
                fontSize: 12,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
      ],
    );
  }
}

class _GlucoseRow extends StatelessWidget {
  final GlucoseReadingPreview reading;
  const _GlucoseRow({required this.reading});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: AminaTheme.cardBg,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Row(
      children: [
        Text(
          '${reading.valueMgdl.toStringAsFixed(0)} mg/dL',
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: AminaTheme.textPrimary(context),
          ),
        ),
        const Spacer(),
        if (reading.context != null) _Chip(label: reading.context!),
        if (reading.timestamp != null)
          Text(
            _shortDate(reading.timestamp!),
            style: TextStyle(
              fontSize: 11,
              color: AminaTheme.textSecondary(context),
            ),
          ),
      ],
    ),
  );

  String _shortDate(String ts) {
    try {
      return ts.substring(0, 10);
    } catch (_) {
      return ts;
    }
  }
}

class _LabValuesCard extends StatelessWidget {
  final LabValuesPreview values;
  const _LabValuesCard({required this.values});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        children: [
          if (values.hba1cPct != null)
            _LabRow(
              label: 'HbA1c',
              value: '${values.hba1cPct!.toStringAsFixed(1)} %',
            ),
          if (values.fastingGlucoseMgdl != null)
            _LabRow(
              label: l10n.fastingGlucose,
              value: '${values.fastingGlucoseMgdl!.toStringAsFixed(0)} mg/dL',
            ),
          if (values.totalCholesterolMgdl != null)
            _LabRow(
              label: l10n.totalCholesterol,
              value: '${values.totalCholesterolMgdl!.toStringAsFixed(0)} mg/dL',
            ),
          if (values.hdlMgdl != null)
            _LabRow(
              label: 'HDL',
              value: '${values.hdlMgdl!.toStringAsFixed(0)} mg/dL',
            ),
          if (values.ldlMgdl != null)
            _LabRow(
              label: 'LDL',
              value: '${values.ldlMgdl!.toStringAsFixed(0)} mg/dL',
            ),
          if (values.triglyceridesMgdl != null)
            _LabRow(
              label: l10n.triglycerides,
              value: '${values.triglyceridesMgdl!.toStringAsFixed(0)} mg/dL',
            ),
          if (values.creatinineUmol != null)
            _LabRow(
              label: l10n.creatinine,
              value: '${values.creatinineUmol!.toStringAsFixed(0)} µmol/L',
            ),
          if (values.reportDate != null)
            _LabRow(label: l10n.reportDate, value: values.reportDate!),
        ],
      ),
    );
  }
}

class _LabRow extends StatelessWidget {
  final String label, value;
  const _LabRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            color: AminaTheme.textSecondary(context),
          ),
        ),
        const Spacer(),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: AminaTheme.textPrimary(context),
          ),
        ),
      ],
    ),
  );
}

class _MedicationTile extends StatelessWidget {
  final MedicationPreview med;
  const _MedicationTile({required this.med});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: AminaTheme.cardBg,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Row(
      children: [
        const Icon(Icons.medication, size: 16),
        const SizedBox(width: 8),
        Text(
          med.name,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: AminaTheme.textPrimary(context),
          ),
        ),
        if (med.dose != null) ...[
          const SizedBox(width: 8),
          _Chip(label: med.dose!),
        ],
        const Spacer(),
        if (med.frequency != null)
          Text(
            med.frequency!,
            style: TextStyle(
              fontSize: 11,
              color: AminaTheme.textSecondary(context),
            ),
          ),
      ],
    ),
  );
}

class _NotesCard extends StatelessWidget {
  final String notes;
  const _NotesCard({required this.notes});

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AminaTheme.cardBg,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: AminaTheme.divider(context)),
    ),
    child: Text(
      notes,
      style: TextStyle(
        fontSize: 13,
        color: AminaTheme.textPrimary(context),
        height: 1.5,
      ),
    ),
  );
}

class _WarningTile extends StatelessWidget {
  final String warning;
  const _WarningTile({required this.warning});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 6),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
    decoration: BoxDecoration(
      color: Colors.amber.withValues(alpha: 0.1),
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
    ),
    child: Row(
      children: [
        const Icon(Icons.warning_amber, size: 16, color: Colors.amber),
        const SizedBox(width: 8),
        Expanded(child: Text(warning, style: const TextStyle(fontSize: 12))),
      ],
    ),
  );
}

class _ErrorCard extends StatelessWidget {
  final String message;
  const _ErrorCard({required this.message});

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: Colors.red.withValues(alpha: 0.08),
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.error_outline, size: 18, color: Colors.red),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            message,
            style: const TextStyle(fontSize: 13, color: Colors.red),
          ),
        ),
      ],
    ),
  );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AminaTheme.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Column(
        children: [
          Icon(
            Icons.search_off,
            size: 40,
            color: AminaTheme.textSecondary(context),
          ),
          const SizedBox(height: 12),
          Text(
            l10n.noMedicalDataDetected,
            textAlign: TextAlign.center,
            style: TextStyle(color: AminaTheme.textSecondary(context)),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  const _Chip({required this.label});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsetsDirectional.only(end: 6),
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: AminaTheme.teal500.withValues(alpha: 0.12),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(
      label,
      style: const TextStyle(
        fontSize: 11,
        color: AminaTheme.teal600,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}

class _StatRow extends StatelessWidget {
  final String label, value;
  const _StatRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          '$label : ',
          style: TextStyle(color: AminaTheme.textSecondary(context)),
        ),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: AminaTheme.textPrimary(context),
          ),
        ),
      ],
    ),
  );
}

