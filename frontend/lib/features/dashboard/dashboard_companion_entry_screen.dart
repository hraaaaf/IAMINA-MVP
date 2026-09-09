import 'package:drift/drift.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../services/companion_service.dart';
import 'dashboard_premium_screen.dart';

class DashboardCompanionEntryScreen extends StatefulWidget {
  final CompanionService? companionService;

  const DashboardCompanionEntryScreen({super.key, this.companionService});

  @override
  State<DashboardCompanionEntryScreen> createState() =>
      _DashboardCompanionEntryScreenState();
}

class _DashboardCompanionEntryScreenState
    extends State<DashboardCompanionEntryScreen> {
  Future<void>? _offlinePreparation;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _offlinePreparation ??= _prepareOfflineDemoTimeline();
  }

  Future<void> _prepareOfflineDemoTimeline() async {
    if (!kOfflineDemo) return;
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    await (db.delete(db.logEntries)
          ..where((row) => row.loggedAt.isBiggerThanValue(now)))
        .go();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _offlinePreparation,
      builder: (context, snapshot) {
        if (kOfflineDemo && snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        return KeyedSubtree(
          key: const ValueKey('dashboard-companion-primary-entry'),
          child: Stack(
            children: [
              DashboardPremiumScreen(
                companionService: widget.companionService,
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
      },
    );
  }
}
