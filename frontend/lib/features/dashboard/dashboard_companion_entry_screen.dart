import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';
import 'widgets/dashboard_companion_fab.dart';

/// W03: one companion entry on Home, with a dedicated non-scrolling FAB lane.
/// The launcher cannot intersect a reading, trend, or reminder card even when
/// their content moves behind the viewport during scrolling.
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
        child: DashboardCompanionFloatingShell(
          child: DashboardPremiumScreen(
            companionService: companionService,
            scrollController: scrollController,
          ),
        ),
      );
}

/// The scroll viewport ends above the 78dp FAB lane. This is intentionally NOT
/// a Positioned overlay, which previously obscured patient and reminder actions.
/// The MainShell navigation bar is outside these bounds.
class DashboardCompanionFloatingShell extends StatelessWidget {
  final Widget child;
  const DashboardCompanionFloatingShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      child: Column(
        children: [
          Expanded(child: child),
          SizedBox(
            key: const ValueKey('dashboard-companion-safe-lane'),
            height: 78,
            child: Align(
              alignment: AlignmentDirectional.bottomEnd,
              child: const Padding(
                padding: EdgeInsetsDirectional.only(end: 20, bottom: 10),
                child: DashboardCompanionFab(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
