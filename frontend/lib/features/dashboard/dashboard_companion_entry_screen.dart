import 'package:flutter/material.dart';

import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';

class DashboardCompanionEntryScreen extends StatelessWidget {
  final CompanionService? companionService;

  const DashboardCompanionEntryScreen({super.key, this.companionService});

  @override
  Widget build(BuildContext context) => KeyedSubtree(
    key: const ValueKey('dashboard-companion-primary-entry'),
    child: DashboardPremiumScreen(companionService: companionService),
  );
}
