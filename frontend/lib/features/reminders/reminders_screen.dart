import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/localization/locale_formatting.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';

String _rt(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class RemindersScreen extends StatefulWidget {
  const RemindersScreen({super.key});

  @override
  State<RemindersScreen> createState() => _RemindersScreenState();
}

class _RemindersScreenState extends State<RemindersScreen> {
  final _title = TextEditingController();
  DateTime _dueAt = DateTime.now().add(const Duration(hours: 1));

  @override
  void dispose() {
    _title.dispose();
    super.dispose();
  }

  Future<void> _addReminder() async {
    final title = _title.text.trim();
    if (title.isEmpty) return;
    await context.read<AppDatabase>().addReminder(title: title, dueAt: _dueAt);
    if (!mounted) return;
    _title.clear();
    setState(() => _dueAt = DateTime.now().add(const Duration(hours: 1)));
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: AppBar(
        title: Text(_rt(context, 'Rappels', 'Reminders', 'التذكيرات')),
      ),
      body: ListView(
        padding: const EdgeInsetsDirectional.fromSTEB(20, 16, 20, 40),
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AminaTheme.subtleBg(context),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AminaTheme.divider(context)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.info_outline_rounded, size: 19),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _rt(
                      context,
                      'Ces rappels sont enregistrés dans IAmina. Les notifications système ne sont pas activées dans cette version.',
                      'These reminders are stored in IAmina. System notifications are not enabled in this version.',
                      'تُحفظ هذه التذكيرات داخل IAmina. إشعارات النظام غير مفعّلة في هذا الإصدار.',
                    ),
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          TextField(
            key: const Key('reminder-title-input'),
            controller: _title,
            decoration: InputDecoration(
              labelText: _rt(
                context,
                'Titre du rappel',
                'Reminder title',
                'عنوان التذكير',
              ),
            ),
          ),
          const SizedBox(height: 10),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.event_outlined),
            title: Text(
              _rt(context, 'Date et heure', 'Date and time', 'التاريخ والوقت'),
            ),
            subtitle: Text(formatLocalizedDateTime(context, _dueAt)),
            onTap: () async {
              final date = await showDatePicker(
                context: context,
                initialDate: _dueAt,
                firstDate: DateTime.now(),
                lastDate: DateTime.now().add(const Duration(days: 730)),
              );
              if (date == null || !context.mounted) return;
              final time = await showTimePicker(
                context: context,
                initialTime: TimeOfDay.fromDateTime(_dueAt),
              );
              if (time == null || !context.mounted) return;
              setState(() {
                _dueAt = DateTime(
                  date.year,
                  date.month,
                  date.day,
                  time.hour,
                  time.minute,
                );
              });
            },
          ),
          FilledButton.icon(
            key: const Key('save-reminder'),
            onPressed: _addReminder,
            icon: const Icon(Icons.add_alert_outlined),
            label: Text(
              _rt(
                context,
                'Ajouter le rappel',
                'Add reminder',
                'إضافة التذكير',
              ),
            ),
          ),
          const SizedBox(height: 26),
          Text(
            _rt(context, 'Mes rappels', 'My reminders', 'تذكيراتي'),
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 8),
          StreamBuilder<List<ReminderData>>(
            stream: db.watchReminders(),
            builder: (context, snapshot) {
              final reminders = snapshot.data ?? const <ReminderData>[];
              if (reminders.isEmpty) {
                return Text(
                  _rt(
                    context,
                    'Aucun rappel enregistré.',
                    'No reminder saved.',
                    'لا توجد تذكيرات محفوظة.',
                  ),
                  style: TextStyle(color: AminaTheme.textSecondary(context)),
                );
              }
              return Column(
                children: reminders
                    .map(
                      (item) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          item.enabled
                              ? Icons.notifications_active_outlined
                              : Icons.notifications_off_outlined,
                        ),
                        title: Text(item.title),
                        subtitle: Text(
                          formatLocalizedDateTime(context, item.dueAt),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Switch(
                              value: item.enabled,
                              onChanged: (value) =>
                                  db.setReminderEnabled(item.id, value),
                            ),
                            IconButton(
                              tooltip: _rt(
                                context,
                                'Supprimer',
                                'Delete',
                                'حذف',
                              ),
                              icon: const Icon(Icons.delete_outline_rounded),
                              onPressed: () => db.deleteReminder(item.id),
                            ),
                          ],
                        ),
                      ),
                    )
                    .toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
