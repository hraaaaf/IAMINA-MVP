import 'package:flutter/material.dart';

import '../../../services/companion_service.dart';
import 'dashboard_insight_section.dart';
import 'dashboard_my_reminders_card.dart';
import 'dashboard_trend_section.dart';

class DashboardResponsiveSections extends StatelessWidget {
  final String unit;
  final double? low;
  final double? high;
  final CompanionService? companionService;

  const DashboardResponsiveSections({
    super.key,
    required this.unit,
    required this.low,
    required this.high,
    required this.companionService,
  });

  // D22 Gate A: without signed individual target provenance these live
  // preview/next-action sections must not mount or call remote services.
  bool get _d22PersonalizedSectionsAuthorized => false;

  @override
  Widget build(BuildContext context) {
    if (!_d22PersonalizedSectionsAuthorized) {
      return Column(
        children: [
          DashboardTrendSection(unit: unit, low: low, high: high),
          const SizedBox(height: 18),
          const _D22PersonalizationNotice(),
        ],
      );
    }
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 760) {
          return Column(
            children: [
              DashboardTrendSection(unit: unit, low: low, high: high),
              const SizedBox(height: 18),
              DashboardInsightSection(service: companionService),
              const SizedBox(height: 18),
              const DashboardMyRemindersCard(),
            ],
          );
        }

        // Dashboard hierarchy: one trend block, then interpretation/actions.
        // Repeated KPIs were removed because they duplicated the trend summary.
        return Column(
          children: [
            DashboardTrendSection(unit: unit, low: low, high: high),
            const SizedBox(height: 18),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: DashboardInsightSection(service: companionService),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: const DashboardMyRemindersCard(),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _D22PersonalizationNotice extends StatelessWidget {
  const _D22PersonalizationNotice();

  @override
  Widget build(BuildContext context) {
    final message = switch (Localizations.localeOf(context).languageCode) {
      'fr' => 'Analyses personnalisées indisponibles : objectifs glycémiques non vérifiés.',
      'ar' => 'التحليلات الشخصية غير متاحة: أهداف سكر الدم غير مؤكدة.',
      _ => 'Personalized insights unavailable: glucose targets unverified.',
    };
    return Container(
      key: const ValueKey('d22-dashboard-personalization-blocked'),
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline_rounded, size: 20),
          const SizedBox(width: 10),
          Expanded(child: Text(message)),
        ],
      ),
    );
  }
}
