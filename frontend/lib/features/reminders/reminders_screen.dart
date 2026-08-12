import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

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

  Future<void> _pickDueAt() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _dueAt,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 730)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_dueAt),
    );
    if (time == null || !mounted) return;
    setState(() {
      _dueAt = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final mobile = MediaQuery.sizeOf(context).width < 700;
    final title = _rt(context, 'Rappels', 'Reminders', 'التذكيرات');
    final subtitle = _rt(
      context,
      'Des repères enregistrés dans IAmina',
      'Saved prompts inside IAmina',
      'تذكيرات محفوظة داخل IAmina',
    );

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: mobile ? null : AppBar(title: Text(title)),
      body: Column(
        children: [
          if (mobile) AminaMobilePageHeader(title: title, subtitle: subtitle),
          Expanded(
            child: ListView(
              physics: const BouncingScrollPhysics(),
              padding: EdgeInsetsDirectional.fromSTEB(
                mobile ? 18 : 24,
                mobile ? 6 : 18,
                mobile ? 18 : 24,
                112,
              ),
              children: [
                _ReminderPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Container(
                        padding: const EdgeInsetsDirectional.fromSTEB(
                          12,
                          11,
                          12,
                          11,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0F7F4),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(
                              Icons.info_outline_rounded,
                              size: 19,
                              color: Color(0xFF064E52),
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
                                style: const TextStyle(
                                  color: Color(0xFF355E59),
                                  fontSize: 12,
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
                          prefixIcon: const Icon(
                            Icons.notifications_none_rounded,
                          ),
                        ),
                      ),
                      const SizedBox(height: 10),
                      _DateAction(
                        title: _rt(
                          context,
                          'Date et heure',
                          'Date and time',
                          'التاريخ والوقت',
                        ),
                        value: DateFormat('dd/MM/yyyy · HH:mm').format(_dueAt),
                        onTap: _pickDueAt,
                      ),
                      const SizedBox(height: 12),
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
                        style: FilledButton.styleFrom(
                          minimumSize: const Size.fromHeight(50),
                          backgroundColor: const Color(0xFF064E52),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  _rt(context, 'Mes rappels', 'My reminders', 'تذكيراتي'),
                  style: TextStyle(
                    color: AminaTheme.textPrimary(context),
                    fontSize: 15.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.25,
                  ),
                ),
                const SizedBox(height: 8),
                StreamBuilder<List<ReminderData>>(
                  stream: db.watchReminders(),
                  builder: (context, snapshot) {
                    final reminders = snapshot.data ?? const <ReminderData>[];
                    if (reminders.isEmpty) {
                      return _ReminderPanel(
                        child: Row(
                          children: [
                            const _IconBadge(
                              icon: Icons.notifications_none_rounded,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                _rt(
                                  context,
                                  'Aucun rappel enregistré.',
                                  'No reminder saved.',
                                  'لا توجد تذكيرات محفوظة.',
                                ),
                                style: TextStyle(
                                  color: AminaTheme.textSecondary(context),
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    }
                    return Column(
                      children: reminders
                          .map(
                            (item) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: _ReminderPanel(
                                padding: const EdgeInsetsDirectional.fromSTEB(
                                  14,
                                  11,
                                  8,
                                  11,
                                ),
                                child: Row(
                                  children: [
                                    _IconBadge(
                                      icon: item.enabled
                                          ? Icons.notifications_active_outlined
                                          : Icons.notifications_off_outlined,
                                      size: 38,
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            item.title,
                                            style: TextStyle(
                                              color: AminaTheme.textPrimary(
                                                context,
                                              ),
                                              fontSize: 14,
                                              fontWeight: FontWeight.w800,
                                            ),
                                          ),
                                          const SizedBox(height: 3),
                                          Text(
                                            DateFormat(
                                              'dd/MM/yyyy · HH:mm',
                                            ).format(item.dueAt),
                                            style: TextStyle(
                                              color: AminaTheme.textSecondary(
                                                context,
                                              ),
                                              fontSize: 11.5,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
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
                                      icon: const Icon(
                                        Icons.delete_outline_rounded,
                                      ),
                                      color: AminaTheme.textSecondary(context),
                                      onPressed: () =>
                                          db.deleteReminder(item.id),
                                    ),
                                  ],
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
    );
  }
}

class _ReminderPanel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const _ReminderPanel({
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF064E52).withValues(alpha: 0.045),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _IconBadge extends StatelessWidget {
  final IconData icon;
  final double size;

  const _IconBadge({required this.icon, this.size = 42});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: const Color(0xFFE5F5EF),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Icon(icon, size: size * 0.48, color: const Color(0xFF064E52)),
    );
  }
}

class _DateAction extends StatelessWidget {
  final String title;
  final String value;
  final VoidCallback onTap;

  const _DateAction({
    required this.title,
    required this.value,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        constraints: const BoxConstraints(minHeight: 54),
        padding: const EdgeInsetsDirectional.fromSTEB(12, 8, 10, 8),
        decoration: BoxDecoration(
          color: AminaTheme.subtleBg(context),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.event_outlined,
              size: 20,
              color: Color(0xFF064E52),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: AminaTheme.textPrimary(context),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    value,
                    style: TextStyle(
                      color: AminaTheme.textSecondary(context),
                      fontSize: 11.5,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              color: AminaTheme.textSecondary(context),
            ),
          ],
        ),
      ),
    );
  }
}
