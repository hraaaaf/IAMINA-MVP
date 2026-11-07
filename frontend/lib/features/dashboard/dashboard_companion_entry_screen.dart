import 'package:flutter/material.dart';

import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';

/// W03: one in-flow companion entry per Dashboard state.
/// No floating launcher: clinical cards and reminder actions stay unobstructed.
class DashboardCompanionEntryScreen extends StatelessWidget {
  final CompanionService? companionService;
  final ScrollController? scrollController;

  const DashboardCompanionEntryScreen({
    super.key,
    this.companionService,
    this.scrollController,
  });

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('dashboard-companion-primary-entry'),
        child: DashboardPremiumScreen(
          companionService: companionService,
          scrollController: scrollController,
        ),
      );
}
