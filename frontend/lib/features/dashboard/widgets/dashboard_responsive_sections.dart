import 'package:flutter/material.dart';

import '../../../services/companion_service.dart';
import 'dashboard_adaptive_kpi_section.dart';
import 'dashboard_insight_section.dart';
import 'dashboard_next_action_section.dart';
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

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 760) {
          return Column(
            children: [
              DashboardTrendSection(unit: unit, low: low, high: high),
              const SizedBox(height: 18),
              DashboardAdaptiveKpiSection(unit: unit, low: low, high: high),
              const SizedBox(height: 18),
              DashboardInsightSection(service: companionService),
              const SizedBox(height: 18),
              DashboardNextActionSection(service: companionService),
            ],
          );
        }

        // Desktop hierarchy: trend first, metrics second, interpretation/actions last.
        // This keeps the primary clinical signal large enough to read instead of
        // compressing it into a half-width technical card.
        return Column(
          children: [
            DashboardTrendSection(unit: unit, low: low, high: high),
            const SizedBox(height: 18),
            DashboardAdaptiveKpiSection(unit: unit, low: low, high: high),
            const SizedBox(height: 18),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: DashboardInsightSection(service: companionService),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: DashboardNextActionSection(
                    service: companionService,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}
