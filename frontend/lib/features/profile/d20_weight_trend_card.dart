import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../data/drift/patient_weight_history_store.dart';
import 'weight_trend_snapshot.dart';

/// D20 UI: descriptive, local-only, not a health assessment or alert.
/// All values are sourced from existing patient-declared, owner-scoped history.
class D20WeightTrendCard extends StatelessWidget {
  final List<LocalWeightObservation> observations;
  final DateTime asOfUtc;

  const D20WeightTrendCard({
    super.key,
    required this.observations,
    required this.asOfUtc,
  });

  static String _copy(
    String language,
    String fr,
    String en,
    String ar,
  ) => switch (language) {
    'fr' => fr,
    'ar' => ar,
    _ => en,
  };

  @override
  Widget build(BuildContext context) {
    final language = Localizations.localeOf(context).languageCode;
    final trend = LocalWeightTrendSnapshot.fromObservations(
      observations, asOfUtc: asOfUtc,
    );
    final dates = MaterialLocalizations.of(context);
    final theme = Theme.of(context);
    final secondary = AminaVisualLanguage.secondary(context);
    final textColor = AminaVisualLanguage.primaryText(context);

    String localDate(DateTime instant) =>
        dates.formatMediumDate(instant.toLocal());
    String signedChange(int hundredths) {
      final sign = hundredths > 0 ? '+' : hundredths < 0 ? '−' : '';
      final amount = (hundredths.abs() / 100).toStringAsFixed(2);
      return '$sign${language == 'fr' ? amount.replaceAll('.', ',') : amount} kg';
    }

    return Semantics(
      container: true,
      child: Container(
        key: const Key('d20-weight-trend-card'),
        width: double.infinity,
        padding: const EdgeInsetsDirectional.fromSTEB(14, 14, 14, 14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AminaVisualLanguage.controlBorder(context),
          ),
          color: AminaVisualLanguage.cardSurface(context),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(Icons.timeline_outlined, size: 20, color: secondary),
              const SizedBox(width: 8),
              Expanded(child: Text(
                _copy(language, 'Évolution du poids · facultatif',
                    'Weight change · optional', 'تغيّر الوزن · اختياري'),
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700, color: textColor,
                ),
              )),
            ]),
            const SizedBox(height: 8),
            if (trend == null)
              Text(
                _copy(language,
                    'Pas assez de pesées datées et fiables pour comparer.',
                    'Not enough reliable dated readings to compare.',
                    'لا توجد قياسات مؤرخة وموثوقة كافية للمقارنة.'),
                key: const Key('d20-weight-trend-unavailable'),
                style: theme.textTheme.bodyMedium,
              )
            else ...[
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: Text(
                  signedChange(trend.deltaKgHundredths),
                  key: const Key('d20-weight-trend-delta'),
                  textDirection: TextDirection.ltr,
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: textColor, fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _copy(language, 'Du', 'From', 'من') +
                    ' ' + localDate(trend.baselineAtUtc) +
                    '  —  ' +
                    _copy(language, 'au', 'to', 'إلى') +
                    ' ' + localDate(trend.latestAtUtc),
                key: const Key('d20-weight-trend-period'),
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 4),
              Text(
                _copy(language,
                    'Mesures déclarées par le patient · parmi les 20 plus récentes.',
                    'Patient-entered readings · among the 20 most recent.',
                    'قياسات صرّح بها المريض · ضمن آخر 20 قياسًا.'),
                key: const Key('d20-weight-trend-source'),
                style: theme.textTheme.bodySmall?.copyWith(color: secondary),
              ),
            ],
            const SizedBox(height: 4),
            Text(
              _copy(language,
                  'Information descriptive uniquement. Ne modifie ni traitement ni objectifs.',
                  'Descriptive information only. Does not change treatment or targets.',
                  'معلومة وصفية فقط، لا تغيّر العلاج أو الأهداف.'),
              key: const Key('d20-weight-trend-safety-copy'),
              style: theme.textTheme.bodySmall?.copyWith(color: secondary),
            ),
          ],
        ),
      ),
    );
  }
}
