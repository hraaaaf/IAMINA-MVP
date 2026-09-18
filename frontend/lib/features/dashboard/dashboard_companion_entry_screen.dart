import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';

bool useMobileCompanionBar(double width) => width < 720;

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
        LayoutBuilder(
          builder: (context, constraints) {
            final onTap = () => context.push('/companion/chat');
            if (useMobileCompanionBar(constraints.maxWidth)) {
              return PositionedDirectional(
                start: 20,
                end: 20,
                bottom: 92,
                child: _MobileCompanionBar(onTap: onTap),
              );
            }
            return PositionedDirectional(
              end: 20,
              bottom: 104,
              child: Semantics(
                button: true,
                label: 'Parler avec IAmina',
                child: FloatingActionButton.small(
                  key: const ValueKey('dashboard-companion-chat-action'),
                  heroTag: 'dashboard-companion-chat-action',
                  tooltip: 'Parler avec IAmina',
                  onPressed: onTap,
                  backgroundColor: AminaVisualLanguage.forestDeep,
                  foregroundColor: Colors.white,
                  child: const Icon(Icons.forum_outlined),
                ),
              ),
            );
          },
        ),
      ],
    ),
  );
}

class _MobileCompanionBar extends StatelessWidget {
  final VoidCallback onTap;

  const _MobileCompanionBar({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark
        ? AminaVisualLanguage.forestDeep.withValues(alpha: .96)
        : Colors.white.withValues(alpha: .96);
    final foreground = isDark
        ? Colors.white
        : AminaVisualLanguage.forestDeep;

    return Semantics(
      button: true,
      label: 'Poser une question à IAmina',
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          key: const ValueKey('dashboard-companion-chat-action'),
          onTap: onTap,
          borderRadius: BorderRadius.circular(999),
          child: Ink(
            height: 58,
            decoration: BoxDecoration(
              color: surface,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(
                color: isDark
                    ? Colors.white.withValues(alpha: .14)
                    : AminaVisualLanguage.forestDeep.withValues(alpha: .12),
              ),
              boxShadow: [
                BoxShadow(
                  color: AminaVisualLanguage.forestDeep.withValues(alpha: .16),
                  blurRadius: 28,
                  offset: const Offset(0, 12),
                  spreadRadius: -8,
                ),
              ],
            ),
            child: Row(
              children: [
                const SizedBox(width: 8),
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    gradient: AminaVisualLanguage.primaryGradient,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AminaVisualLanguage.actionGreen.withValues(
                          alpha: .28,
                        ),
                        blurRadius: 14,
                        spreadRadius: -3,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.auto_awesome_rounded,
                    size: 20,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Posez une question à IAmina…',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: -.15,
                      color: foreground.withValues(alpha: .82),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Icon(
                  Icons.mic_none_rounded,
                  size: 22,
                  color: foreground.withValues(alpha: .72),
                ),
                const SizedBox(width: 18),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
