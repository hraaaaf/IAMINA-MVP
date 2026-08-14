import 'package:flutter/material.dart';

import 'dashboard_premium_screen.dart';

class DashboardCompanionEntryScreen extends StatelessWidget {
  const DashboardCompanionEntryScreen({super.key});

  @override
  Widget build(BuildContext context) => const KeyedSubtree(
    key: ValueKey('dashboard-companion-primary-entry'),
    child: DashboardPremiumScreen(),
  );
}
