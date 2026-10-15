import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/database.dart';

String _copy(BuildContext context, String fr, String en, String ar) {
  return switch (Localizations.localeOf(context).languageCode) {
    'ar' => ar,
    'en' => en,
    _ => fr,
  };
}

/// Read-only local reminders preview. No OS push or network calls.
///
/// Titles may contain private medical text and are deliberately not shown on
/// Home. Actual reminder editing stays inside the local Reminders screen.
class DashboardRemindersSummaryCard extends StatefulWidget {
  const DashboardRemindersSummaryCard({super.key});

  @override
  State<DashboardRemindersSummaryCard> createState() =>
      _DashboardRemindersSummaryCardState();
}

class _DashboardRemindersSummaryCardState
    extends State<DashboardRemindersSummaryCard> {
  late final Stream<List<ReminderData>> _reminders;

  @override
  void initState() {
    super.initState();
    _reminders = context.read<AppDatabase>().watchReminders();
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<ReminderData>>(
      stream: _reminders,
      builder: (context, snapshot) {
        final activeCount = snapshot.hasData
            ? snapshot.data!.where((item) => item.enabled).length
            : null;
        final status = snapshot.hasError
            ? _copy(context, 'Rappels indisponibles', 'Reminders unavailable',
                'التذكيرات غير متاحة')
            : activeCount == null
            ? _copy(context, 'Chargement des rappels…', 'Loading reminders…',
                'جارٍ تحميل التذكيرات…')
            : activeCount == 0
            ? _copy(context, 'Aucun rappel actif', 'No active reminders',
                'لا توجد تذكيرات نشطة')
            : activeCount == 1
            ? _copy(context, '1 rappel actif', '1 active reminder',
                'تذكير نشط واحد')
            : _copy(context, '$activeCount rappels actifs',
                '$activeCount active reminders', '$activeCount تذكيرات نشطة');

        return Semantics(
          button: true,
          hint: _copy(context, 'Ouvrir les rappels', 'Open reminders',
              'فتح التذكيرات'),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              key: const ValueKey('dashboard-reminders-card'),
              onTap: () => context.go('/reminders'),
              borderRadius: BorderRadius.circular(18),
              child: Ink(
                padding: const EdgeInsetsDirectional.fromSTEB(14, 14, 14, 14),
                decoration:
                    AminaVisualLanguage.cardDecoration(context, radius: 18),
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration:
                          AminaVisualLanguage.mintIconDecoration(context),
                      child: const Icon(Icons.event_note_outlined,
                          size: 20, color: AminaVisualLanguage.actionGreen),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _copy(context, 'Rappels', 'Reminders', 'التذكيرات'),
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                              color: AminaVisualLanguage.primaryText(context),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            status,
                            key: const ValueKey('dashboard-reminders-status'),
                            style: TextStyle(
                              fontSize: 12,
                              color: AminaVisualLanguage.secondary(context),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Icon(
                      Directionality.of(context) == TextDirection.rtl
                          ? Icons.arrow_back_ios_new_rounded
                          : Icons.arrow_forward_ios_rounded,
                      size: 16,
                      color: AminaVisualLanguage.actionGreen,
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
