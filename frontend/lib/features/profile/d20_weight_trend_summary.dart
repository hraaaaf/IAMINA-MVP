import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../data/drift/patient_weight_history_store.dart';
import 'weight_trend_snapshot.dart';

/// D20-E: read-only descriptive slice of up to 20 displayed weight records.
///
/// No settings, OS permission, alarm, notification dispatch, medical
/// interpretation, BMI or external service. The user must not mistake a
/// descriptive arithmetic difference for a safety alert.
class D20WeightTrendSummary extends StatelessWidget {
  final List<LocalWeightObservation> history;
  final DateTime asOfUtc;

  const D20WeightTrendSummary({
    super.key,
    required this.history,
    required this.asOfUtc,
  });

  String _t(BuildContext context, String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr,
        'ar' => ar,
        _ => en,
      };

  @override
  Widget build(BuildContext context) {
    final snapshot = LocalWeightTrendSnapshot.fromObservations(
      history, asOfUtc: asOfUtc,
    );
    final locale = Localizations.localeOf(context).languageCode;
    final theme = Theme.of(context);
    final local = MaterialLocalizations.of(context);
    final caption = theme.textTheme.bodySmall;

    return Semantics(
      container: true,
      explicitChildNodes: true,
      child: Container(
        key: const Key('d20-weight-trend-section'),
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: theme.colorScheme.outlineVariant),
          color: theme.colorScheme.surfaceContainerLowest,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _t(context, 'Évolution du poids', 'Weight change',
                  'تغيّر الوزن'),
              key: const Key('d20-trend-heading'),
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 6),
            if (snapshot == null)
              Text(
                history.isEmpty
                    ? _t(context,
                        'Pas de tendance : aucune pesée enregistrée.',
                        'No trend: no weight readings recorded.',
                        'لا يوجد اتجاه: لم تُسجّل أي قياسات للوزن.')
                    : _t(context,
                        'Tendance indisponible : deux pesées fiables avec des dates distinctes sont nécessaires.',
                        'Trend unavailable: two reliable readings on distinct dates are required.',
                        'الاتجاه غير متاح: يلزم قياسان موثوقان بتاريخين مختلفين.'),
                key: const Key('d20-trend-insufficient'),
              )
            else ...[
              Text(
                _t(context, 'Différence : ', 'Difference: ', 'الفرق: ') +
                    (snapshot.deltaKgHundredths > 0 ? '+' : '') +
                    NumberFormat('0.00', locale).format(
                      snapshot.deltaKgHundredths / 100,
                    ) + ' kg',
                key: const Key('d20-trend-delta'),
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 4),
              Text(
                local.formatMediumDate(
                      snapshot.baselineAtUtc.toLocal(),
                    ) +
                    ' → ' +
                    local.formatMediumDate(
                      snapshot.latestAtUtc.toLocal(),
                    ),
                key: const Key('d20-trend-period'),
                style: caption,
              ),
              Tooltip(
                message: snapshot.baselineEvidenceId +
                    ' → ' + snapshot.latestEvidenceId,
                child: Text(
                  _t(context,
                      'Source : pesées déclarées par le patient.',
                      'Source: patient-entered weight readings.',
                      'المصدر: قياسات الوزن التي أدخلها المريض.'),
                  key: const Key('d20-trend-provenance'),
                  style: caption,
                ),
              ),
            ],
            const SizedBox(height: 6),
            Text(
              _t(context,
                  'Comparaison descriptive parmi les 20 pesées les plus récentes affichées ; ce n’est pas une alerte médicale.',
                  'Descriptive comparison among up to 20 displayed recent readings; not a medical alert.',
                  'مقارنة وصفية بين آخر 20 قياسًا معروضًا كحد أقصى؛ ليست إنذارًا طبيًا.'),
              key: const Key('d20-trend-disclaimer'),
              style: caption,
            ),
          ],
        ),
      ),
    );
  }
}
