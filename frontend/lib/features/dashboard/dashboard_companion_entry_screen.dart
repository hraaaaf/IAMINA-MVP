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
          child: const DashboardCompanionAvatarAction(),
        ),
      ],
    ),
  );
}

/// D27: the branded, floating IAmina entrypoint is only instantiated by
/// DashboardCompanionEntryScreen (the /dashboard shell route). Chat uses its
/// normal in-page header; there is no floating overlay in /companion/chat.
class DashboardCompanionAvatarAction extends StatelessWidget {
  const DashboardCompanionAvatarAction({super.key});

  @override
  Widget build(BuildContext context) {
    final label = switch (Localizations.localeOf(context).languageCode) {
      'ar' => 'تحدث مع IAmina',
      'en' => 'Talk with IAmina',
      _ => 'Parler avec IAmina',
    };
    return Semantics(
      button: true,
      label: label,
      child: FloatingActionButton.small(
        key: const ValueKey('dashboard-companion-chat-action'),
        heroTag: 'dashboard-companion-chat-action',
        tooltip: label,
        onPressed: () => context.push('/companion/chat'),
        backgroundColor: AminaVisualLanguage.forestDeep,
        foregroundColor: Colors.white,
        child: ClipOval(
          child: SizedBox.square(
            dimension: 34,
            child: ColoredBox(
              color: Colors.white,
              child: Image.asset(
                'assets/images/logo_amina.png',
                fit: BoxFit.cover,
                alignment: Alignment.topCenter,
                excludeFromSemantics: true,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
