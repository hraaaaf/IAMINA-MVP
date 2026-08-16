import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';
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

  Future<void> _confirmDeleteReminder(AppDatabase db, ReminderData item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(_rt(context, 'Supprimer le rappel ?', 'Delete reminder?', 'حذف التذكير؟')),
        content: Text(
          _rt(
            context,
            'Ce rappel enregistré sera supprimé.',
            'This saved reminder will be deleted.',
            'سيتم حذف هذا التذكير المحفوظ.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: Text(_rt(context, 'Annuler', 'Cancel', 'إلغاء')),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(
              _rt(context, 'Supprimer', 'Delete', 'حذف'),
              style: const TextStyle(color: AminaTheme.dangerFg),
            ),
          ),
        ],
      ),
    );
    if (confirmed == true) await db.deleteReminder(item.id);
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          if (!AminaTheme.isDark(context))
            PositionedDirectional(
              top: -120,
              end: -100,
              child: Container(
                width: 280,
                height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .68),
                ),
              ),
            ),
          SafeArea(
            top: false,
            child: Column(
              children: [
                AminaMobilePageHeader(
                  title: _rt(context, 'Rappels', 'Reminders', 'التذكيرات'),
                  subtitle: _rt(
                    context,
                    'Planifiez vos rappels sans inventer de suivi.',
                    'Plan reminders without inventing follow-up.',
                    'خطط لتذكيراتك دون اختلاق متابعة.',
                  ),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsetsDirectional.fromSTEB(20, 18, 20, 40),
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: AminaVisualLanguage.cardDecoration(context),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 42,
                                  height: 42,
                                  decoration: AminaVisualLanguage.mintIconDecoration(context),
                                  child: const Icon(
                                    Icons.notifications_none_rounded,
                                    color: AminaVisualLanguage.actionGreen,
                                    size: 21,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    _rt(context, 'Nouveau rappel', 'New reminder', 'تذكير جديد'),
                                    style: TextStyle(
                                      fontFamily: 'Georgia',
                                      fontSize: 20,
                                      fontWeight: FontWeight.w700,
                                      color: AminaVisualLanguage.primaryText(context),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            Container(
                              padding: const EdgeInsets.all(14),
                              decoration: AminaVisualLanguage.cardDecoration(
                                context,
                                color: AminaVisualLanguage.mintSurface.withValues(alpha: .72),
                                radius: 18,
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Icon(
                                    Icons.info_outline_rounded,
                                    size: 19,
                                    color: AminaVisualLanguage.actionGreen,
                                  ),
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
                                        color: AminaVisualLanguage.secondary(context),
                                        height: 1.4,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 16),
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
                              leading: Container(
                                width: 38,
                                height: 38,
                                decoration: AminaVisualLanguage.mintIconDecoration(context),
                                child: const Icon(
                                  Icons.event_outlined,
                                  color: AminaVisualLanguage.actionGreen,
                                  size: 19,
                                ),
                              ),
                              title: Text(_rt(context, 'Date et heure', 'Date and time', 'التاريخ والوقت')),
                              subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(_dueAt)),
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
                            const SizedBox(height: 8),
                            SizedBox(
                              height: 48,
                              child: FilledButton.icon(
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
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 22),
                      Text(
                        _rt(context, 'Mes rappels', 'My reminders', 'تذكيراتي'),
                        style: TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: AminaVisualLanguage.primaryText(context),
                        ),
                      ),
                      const SizedBox(height: 10),
                      StreamBuilder<List<ReminderData>>(
                        stream: db.watchReminders(),
                        builder: (context, snapshot) {
                          final reminders = snapshot.data ?? const <ReminderData>[];
                          if (reminders.isEmpty) {
                            return Container(
                              padding: const EdgeInsets.all(18),
                              decoration: AminaVisualLanguage.cardDecoration(context),
                              child: Text(
                                _rt(
                                  context,
                                  'Aucun rappel enregistré.',
                                  'No reminder saved.',
                                  'لا توجد تذكيرات محفوظة.',
                                ),
                                style: TextStyle(color: AminaVisualLanguage.secondary(context)),
                              ),
                            );
                          }
                          return Column(
                            children: reminders
                                .map(
                                  (item) => Container(
                                    margin: const EdgeInsets.only(bottom: 10),
                                    decoration: AminaVisualLanguage.cardDecoration(context),
                                    child: ListTile(
                                      leading: Container(
                                        width: 40,
                                        height: 40,
                                        decoration: AminaVisualLanguage.mintIconDecoration(context),
                                        child: const Icon(
                                          Icons.event_note_outlined,
                                          color: AminaVisualLanguage.actionGreen,
                                          size: 20,
                                        ),
                                      ),
                                      title: Text(item.title),
                                      subtitle: Text(
                                        DateFormat('dd/MM/yyyy HH:mm').format(item.dueAt),
                                      ),
                                      trailing: IconButton(
                                        key: Key('delete-reminder-${item.id}'),
                                        tooltip: _rt(context, 'Supprimer', 'Delete', 'حذف'),
                                        icon: const Icon(Icons.delete_outline_rounded),
                                        onPressed: () => _confirmDeleteReminder(db, item),
                                      ),
                                    ),
                                  ),
                                )
                                .toList(),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
