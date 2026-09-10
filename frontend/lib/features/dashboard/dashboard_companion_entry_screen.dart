import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';

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
    child: Stack(
      children: [
        DashboardPremiumScreen(
          companionService: companionService,
          scrollController: scrollController,
        ),
        PositionedDirectional(
          end: 20,
          bottom: 104,
          child: Semantics(
            button: true,
            label: 'Parler avec IAmina',
            child: FloatingActionButton.small(
              key: const ValueKey('dashboard-companion-chat-action'),
              heroTag: 'dashboard-companion-chat-action',
              tooltip: 'Parler avec IAmina',
              onPressed: () => context.push('/companion/chat'),
              backgroundColor: AminaVisualLanguage.forestDeep,
              foregroundColor: Colors.white,
              child: const Icon(Icons.forum_outlined),
            ),
          ),
        ),
      ],
    ),
  );
}
