import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart' show DateFormat;
import 'package:provider/provider.dart';

import '../../../core/theme/amina_visual_language.dart';
import '../../../data/drift/database.dart';

String _t3(BuildContext context, String fr, String en, String ar) =>
    switch (Localizations.localeOf(context).languageCode) {
      'ar' => ar,
      'en' => en,
      _ => fr,
    };

/// D3: actual next reminders from the selected patient's LOCAL Drift database.
/// No simulated events, OS notifications, recurring instances or remote calls.
class DashboardMyRemindersCard extends StatefulWidget {
  const DashboardMyRemindersCard({super.key});

  @override
  State<DashboardMyRemindersCard> createState() =>
      _DashboardMyRemindersCardState();
}

class _DashboardMyRemindersCardState extends State<DashboardMyRemindersCard> {
  AppDatabase? _database;
  Stream<List<ReminderData>>? _stream;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final next = Provider.of<AppDatabase>(context);
    if (!identical(_database, next)) {
      _database = next;
      _stream = next.watchReminders();
    }
  }

  @override
  Widget build(BuildContext context) => Container(
    key: const ValueKey('d3-my-reminders-card'),
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: AminaVisualLanguage.mintIconDecoration(context),
              child: const Icon(
                Icons.event_note_outlined,
                color: AminaVisualLanguage.actionGreen,
                size: 20,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                _t3(context, 'Mes rappels', 'My reminders', 'تذكيراتي'),
                key: const ValueKey('d3-my-reminders-heading'),
                style: TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 21,
                  fontWeight: FontWeight.w700,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
            ),
            TextButton(
              key: const ValueKey('d3-reminders-see-all'),
              onPressed: () => context.go('/reminders'),
              child: Text(_t3(context, 'Voir tout', 'See all', 'عرض الكل')),
            ),
          ],
        ),
        const SizedBox(height: 12),
        StreamBuilder<List<ReminderData>>(
          // On vault swap, discard the previous owner's snapshot immediately.
          key: ObjectKey(_database),
          stream: _stream,
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return _D3State(text: _t3(
                context,
                'Rappels indisponibles pour le moment.',
                'Reminders are temporarily unavailable.',
                'التذكيرات غير متاحة حالياً.',
              ));
            }
            if (!snapshot.hasData) {
              return _D3State(
                loading: true,
                text: _t3(
                  context,
                  'Chargement des rappels…',
                  'Loading reminders…',
                  'جارٍ تحميل التذكيرات…',
                ),
              );
            }
            // Schema currently stores only dueAt and enabled: neither a
            // completion status nor recurrence rule is available to infer.
            final now = DateTime.now();
            final upcoming = snapshot.data!
                .where((r) => r.enabled && r.dueAt.isAfter(now))
                .toList()
              ..sort((a, b) {
                final time = a.dueAt.compareTo(b.dueAt);
                return time != 0 ? time : a.id.compareTo(b.id);
              });
            if (upcoming.isEmpty) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _D3State(
                    text: snapshot.data!.isEmpty
                        ? _t3(context, 'Aucun rappel configuré.',
                            'No reminders configured.',
                            'لم يتم إعداد أي تذكير.')
                        : _t3(context, 'Aucun rappel à venir.',
                            'No upcoming reminders.',
                            'لا توجد تذكيرات قادمة.'),
                  ),
                  const SizedBox(height: 10),
                  FilledButton.icon(
                    key: const ValueKey('d3-reminders-create'),
                    onPressed: () => context.go('/reminders'),
                    icon: const Icon(Icons.add_rounded, size: 18),
                    label: Text(_t3(context, 'Créer un rappel',
                        'Create a reminder', 'إنشاء تذكير')),
                    style: FilledButton.styleFrom(
                      backgroundColor: AminaVisualLanguage.forestDeep,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(0, 46),
                    ),
                  ),
                ],
              );
            }
            return Column(
              children: [
                for (final reminder in upcoming.take(3))
                  _D3ReminderRow(reminder: reminder),
              ],
            );
          },
        ),
      ],
    ),
  );
}

class _D3State extends StatelessWidget {
  final String text;
  final bool loading;
  const _D3State({required this.text, this.loading = false});

  @override
  Widget build(BuildContext context) => Row(
    children: [
      if (loading) ...[
        const SizedBox.square(
          dimension: 16,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
        const SizedBox(width: 10),
      ] else ...[
        const Icon(
          Icons.event_available_outlined,
          size: 19,
          color: AminaVisualLanguage.actionGreen,
        ),
        const SizedBox(width: 10),
      ],
      Expanded(
        child: Text(
          text,
          key: const ValueKey('d3-reminders-state'),
          style: TextStyle(
            fontSize: 13,
            height: 1.4,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
      ),
    ],
  );
}

class _D3ReminderRow extends StatelessWidget {
  final ReminderData reminder;
  const _D3ReminderRow({required this.reminder});

  @override
  Widget build(BuildContext context) {
    // The reminder is a local wall-clock event. Show it in device local time.
    final due = DateFormat('dd/MM · HH:mm').format(reminder.dueAt.toLocal());
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .45),
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          key: ValueKey('d3-reminder-' + reminder.id.toString()),
          borderRadius: BorderRadius.circular(14),
          onTap: () => context.go('/reminders'),
          child: Semantics(
            button: true,
            label: reminder.title + ', ' + due,
            child: Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
              child: Row(
                children: [
                  const Icon(
                    Icons.schedule_outlined,
                    color: AminaVisualLanguage.actionGreen,
                    size: 18,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          reminder.title,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: AminaVisualLanguage.primaryText(context),
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          due,
                          style: TextStyle(
                            fontSize: 11.5,
                            color: AminaVisualLanguage.secondary(context),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    Directionality.of(context) == TextDirection.rtl
                        ? Icons.chevron_left_rounded
                        : Icons.chevron_right_rounded,
                    size: 20,
                    color: AminaVisualLanguage.actionGreen,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
