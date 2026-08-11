from pathlib import Path

root = Path(__file__).resolve().parents[1]

# 1) Proper local persistence for medication events and in-app reminders.
db_path = root / 'frontend/lib/data/drift/database.dart'
db = db_path.read_text()
marker = "@DataClassName('PatientProfileData')\nclass PatientProfiles extends Table {"
assert marker in db
tables = r'''@DataClassName('MedicationEventData')
class MedicationEvents extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get label => text()();
  RealColumn get dose => real().nullable()();
  TextColumn get unit => text().nullable()();
  DateTimeColumn get takenAt => dateTime()();
  DateTimeColumn get createdAt => dateTime()();
}

@DataClassName('ReminderData')
class Reminders extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text()();
  DateTimeColumn get dueAt => dateTime()();
  BoolColumn get enabled => boolean().withDefault(const Constant(true))();
  DateTimeColumn get createdAt => dateTime()();
}

'''
db = db.replace(marker, tables + marker, 1)
db = db.replace(
    '@DriftDatabase(tables: [LogEntries, PatientProfiles, ChatMessages])',
    '@DriftDatabase(\n  tables: [LogEntries, PatientProfiles, ChatMessages, MedicationEvents, Reminders],\n)',
    1,
)
db = db.replace('int get schemaVersion => 9;', 'int get schemaVersion => 10;', 1)
migration_marker = "      if (from < 9) {\n        await m.addColumn(patientProfiles, patientProfiles.ramadanStartDate);\n        await m.addColumn(patientProfiles, patientProfiles.ramadanEndDate);\n      }"
assert migration_marker in db
db = db.replace(
    migration_marker,
    migration_marker + "\n      if (from < 10) {\n        await m.createTable(medicationEvents);\n        await m.createTable(reminders);\n      }",
    1,
)
method_marker = "  // Generates 21 days of realistic Type-2 diabetic patient demo data."
assert method_marker in db
methods = r'''  Stream<List<MedicationEventData>> watchMedicationEvents({int limit = 50}) {
    return (select(medicationEvents)
          ..orderBy([(t) => OrderingTerm(expression: t.takenAt, mode: OrderingMode.desc)])
          ..limit(limit))
        .watch();
  }

  Future<int> addMedicationEvent({
    required String label,
    double? dose,
    String? unit,
    required DateTime takenAt,
  }) {
    final cleanedUnit = unit?.trim();
    return into(medicationEvents).insert(
      MedicationEventsCompanion.insert(
        label: label.trim(),
        dose: Value(dose),
        unit: Value(cleanedUnit == null || cleanedUnit.isEmpty ? null : cleanedUnit),
        takenAt: takenAt,
        createdAt: DateTime.now(),
      ),
    );
  }

  Future<void> deleteMedicationEvent(int id) {
    return (delete(medicationEvents)..where((t) => t.id.equals(id))).go();
  }

  Stream<List<ReminderData>> watchReminders() {
    return (select(reminders)
          ..orderBy([(t) => OrderingTerm(expression: t.dueAt, mode: OrderingMode.asc)]))
        .watch();
  }

  Future<int> addReminder({required String title, required DateTime dueAt}) {
    return into(reminders).insert(
      RemindersCompanion.insert(
        title: title.trim(),
        dueAt: dueAt,
        createdAt: DateTime.now(),
      ),
    );
  }

  Future<void> setReminderEnabled(int id, bool enabled) {
    return (update(reminders)..where((t) => t.id.equals(id))).write(
      RemindersCompanion(enabled: Value(enabled)),
    );
  }

  Future<void> deleteReminder(int id) {
    return (delete(reminders)..where((t) => t.id.equals(id))).go();
  }

'''
db = db.replace(method_marker, methods + method_marker, 1)
db_path.write_text(db)

# 2) Focused entry modes so Alimentation / Activité / Insuline land on real capture UI.
sheet_path = root / 'frontend/lib/features/dashboard/widgets/add_log_sheet.dart'
sheet = sheet_path.read_text()
sheet = sheet.replace(
    'class AddLogSheet extends StatefulWidget {\n  final bool isPage;\n\n  const AddLogSheet({super.key, this.isPage = false});',
    "enum AddLogFocus { none, meal, activity, insulin }\n\nclass AddLogSheet extends StatefulWidget {\n  final bool isPage;\n  final AddLogFocus focus;\n\n  const AddLogSheet({\n    super.key,\n    this.isPage = false,\n    this.focus = AddLogFocus.none,\n  });",
    1,
)
state_marker = "  static const List<String> _glycemicContexts = <String>[\n    'fasting',\n    'pre_meal',\n    'post_meal',\n    'other',\n  ];\n\n  @override\n  void dispose()"
assert state_marker in sheet
init = "  static const List<String> _glycemicContexts = <String>[\n    'fasting',\n    'pre_meal',\n    'post_meal',\n    'other',\n  ];\n\n  @override\n  void initState() {\n    super.initState();\n    _mealExpanded = widget.focus == AddLogFocus.meal;\n    _detailsExpanded = widget.focus == AddLogFocus.activity ||\n        widget.focus == AddLogFocus.insulin;\n    _contextExpanded = widget.focus == AddLogFocus.activity;\n  }\n\n  @override\n  void dispose()"
sheet = sheet.replace(state_marker, init, 1)
sheet_path.write_text(sheet)

add_screen = root / 'frontend/lib/features/journal/add_log_screen.dart'
add_screen.write_text(r'''import 'package:flutter/material.dart';
import '../dashboard/widgets/add_log_sheet.dart';

class AddLogScreen extends StatelessWidget {
  final AddLogFocus focus;

  const AddLogScreen({super.key, this.focus = AddLogFocus.none});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AddLogSheet(isPage: true, focus: focus),
    );
  }
}
''')

# 3) Medication logging surface. This records only what the user says they took.
med_path = root / 'frontend/lib/features/medications/medication_screen.dart'
med_path.parent.mkdir(parents=True, exist_ok=True)
med_path.write_text(r'''import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';

String _mt(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class MedicationScreen extends StatefulWidget {
  const MedicationScreen({super.key});

  @override
  State<MedicationScreen> createState() => _MedicationScreenState();
}

class _MedicationScreenState extends State<MedicationScreen> {
  final _name = TextEditingController();
  final _dose = TextEditingController();
  final _unit = TextEditingController();
  DateTime _takenAt = DateTime.now();
  bool _saving = false;

  @override
  void dispose() {
    _name.dispose();
    _dose.dispose();
    _unit.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final label = _name.text.trim();
    if (label.isEmpty || _saving) return;
    final db = context.read<AppDatabase>();
    setState(() => _saving = true);
    try {
      await db.addMedicationEvent(
        label: label,
        dose: double.tryParse(_dose.text.trim().replaceAll(',', '.')),
        unit: _unit.text,
        takenAt: _takenAt,
      );
      if (!mounted) return;
      _name.clear();
      _dose.clear();
      _unit.clear();
      setState(() {
        _takenAt = DateTime.now();
        _saving = false;
      });
    } finally {
      if (mounted && _saving) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      appBar: AppBar(
        title: Text(_mt(context, 'Médicaments', 'Medications', 'الأدوية')),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
        children: [
          Text(
            _mt(
              context,
              'Enregistrez uniquement un traitement réellement pris. IAmina ne recommande ni médicament ni dose.',
              'Record only treatment you actually took. IAmina does not recommend a medication or dose.',
              'سجّل فقط علاجاً تناولته فعلاً. IAmina لا توصي بدواء أو جرعة.',
            ),
            style: TextStyle(color: AminaTheme.textSecondary(context), height: 1.4),
          ),
          const SizedBox(height: 18),
          TextField(
            key: const Key('medication-name-input'),
            controller: _name,
            decoration: InputDecoration(
              labelText: _mt(context, 'Nom du traitement', 'Treatment name', 'اسم العلاج'),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _dose,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: _mt(context, 'Dose (facultatif)', 'Dose (optional)', 'الجرعة (اختياري)'),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _unit,
                  decoration: InputDecoration(
                    labelText: _mt(context, 'Unité', 'Unit', 'الوحدة'),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.schedule_rounded),
            title: Text(_mt(context, 'Heure de prise', 'Time taken', 'وقت التناول')),
            subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(_takenAt)),
            onTap: () async {
              final date = await showDatePicker(
                context: context,
                initialDate: _takenAt,
                firstDate: DateTime.now().subtract(const Duration(days: 365)),
                lastDate: DateTime.now(),
              );
              if (date == null || !mounted) return;
              final time = await showTimePicker(
                context: context,
                initialTime: TimeOfDay.fromDateTime(_takenAt),
              );
              if (time == null || !mounted) return;
              setState(() {
                _takenAt = DateTime(date.year, date.month, date.day, time.hour, time.minute);
              });
            },
          ),
          const SizedBox(height: 8),
          FilledButton.icon(
            key: const Key('save-medication-event'),
            onPressed: _saving ? null : _save,
            icon: const Icon(Icons.check_rounded),
            label: Text(_mt(context, 'Enregistrer la prise', 'Save intake', 'حفظ التناول')),
          ),
          const SizedBox(height: 26),
          Text(
            _mt(context, 'Prises récentes', 'Recent intakes', 'آخر مرات التناول'),
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 10),
          StreamBuilder<List<MedicationEventData>>(
            stream: db.watchMedicationEvents(),
            builder: (context, snapshot) {
              final items = snapshot.data ?? const <MedicationEventData>[];
              if (items.isEmpty) {
                return Text(
                  _mt(context, 'Aucune prise enregistrée.', 'No intake recorded.', 'لا توجد جرعات مسجلة.'),
                  style: TextStyle(color: AminaTheme.textSecondary(context)),
                );
              }
              return Column(
                children: items.map((item) {
                  final dose = item.dose == null
                      ? ''
                      : ' · ${item.dose!.toStringAsFixed(item.dose! % 1 == 0 ? 0 : 1)} ${item.unit ?? ''}'.trimRight();
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.medication_outlined),
                    title: Text('${item.label}$dose'),
                    subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(item.takenAt)),
                    trailing: IconButton(
                      tooltip: _mt(context, 'Supprimer', 'Delete', 'حذف'),
                      icon: const Icon(Icons.delete_outline_rounded),
                      onPressed: () => db.deleteMedicationEvent(item.id),
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
''')

# 4) Real persisted in-app reminders, explicitly not device notifications.
rem_path = root / 'frontend/lib/features/reminders/reminders_screen.dart'
rem_path.parent.mkdir(parents=True, exist_ok=True)
rem_path.write_text(r'''import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

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
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 40),
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
                    style: TextStyle(color: AminaTheme.textSecondary(context), height: 1.35),
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
              labelText: _rt(context, 'Titre du rappel', 'Reminder title', 'عنوان التذكير'),
            ),
          ),
          const SizedBox(height: 10),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.event_outlined),
            title: Text(_rt(context, 'Date et heure', 'Date and time', 'التاريخ والوقت')),
            subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(_dueAt)),
            onTap: () async {
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
                _dueAt = DateTime(date.year, date.month, date.day, time.hour, time.minute);
              });
            },
          ),
          FilledButton.icon(
            key: const Key('save-reminder'),
            onPressed: _addReminder,
            icon: const Icon(Icons.add_alert_outlined),
            label: Text(_rt(context, 'Ajouter le rappel', 'Add reminder', 'إضافة التذكير')),
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
                  _rt(context, 'Aucun rappel enregistré.', 'No reminder saved.', 'لا توجد تذكيرات محفوظة.'),
                  style: TextStyle(color: AminaTheme.textSecondary(context)),
                );
              }
              return Column(
                children: reminders.map((item) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(item.enabled ? Icons.notifications_active_outlined : Icons.notifications_off_outlined),
                  title: Text(item.title),
                  subtitle: Text(DateFormat('dd/MM/yyyy HH:mm').format(item.dueAt)),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Switch(
                        value: item.enabled,
                        onChanged: (value) => db.setReminderEnabled(item.id, value),
                      ),
                      IconButton(
                        tooltip: _rt(context, 'Supprimer', 'Delete', 'حذف'),
                        icon: const Icon(Icons.delete_outline_rounded),
                        onPressed: () => db.deleteReminder(item.id),
                      ),
                    ],
                  ),
                )).toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
''')

# 5) Module routing + semantic nav labels. Import stays available on desktop/sidebar.
module_path = root / 'frontend/lib/modules/diabetes_module.dart'
module_path.write_text(r'''import 'package:flutter/material.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/dashboard/dashboard_convergent_screen.dart';
import '../features/dashboard/widgets/add_log_sheet.dart';
import '../features/journal/journal_screen.dart';
import '../features/journal/ai_summary_screen.dart';
import '../features/journal/add_log_screen.dart';
import '../features/journal/edit_log_screen.dart';
import '../features/import/import_screen.dart';
import '../features/documents/document_import_screen.dart';
import '../features/medications/medication_screen.dart';
import '../features/reminders/reminders_screen.dart';
import '../l10n/app_localizations.dart';
import 'module_config.dart';

String _navText(AppLocalizations l, String fr, String en, String ar) {
  final code = l.localeName.split('_').first;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

AddLogFocus _focusFromState(String? value) => switch (value) {
  'meal' => AddLogFocus.meal,
  'activity' => AddLogFocus.activity,
  'insulin' => AddLogFocus.insulin,
  _ => AddLogFocus.none,
};

/// Diabetes condition module. Mobile navigation is filtered by MainShell
/// to preserve the approved four-destination + central-add composition;
/// Import remains available in desktop navigation and by direct route.
final ModuleConfig diabetesModule = ModuleConfig(
  id: 'diabetes',
  navDestinations: [
    ModuleNavDestination(
      route: '/dashboard',
      icon: Icons.home_outlined,
      selectedIcon: Icons.home_rounded,
      label: (l) => l.navHome,
    ),
    ModuleNavDestination(
      route: '/journal',
      icon: Icons.monitor_heart_outlined,
      selectedIcon: Icons.monitor_heart_rounded,
      label: (l) => _navText(l, 'Mesures', 'Measurements', 'القياسات'),
    ),
    ModuleNavDestination(
      route: '/summary',
      icon: Icons.insert_chart_outlined_rounded,
      selectedIcon: Icons.insert_chart_rounded,
      label: (l) => _navText(l, 'Rapports', 'Reports', 'التقارير'),
    ),
    ModuleNavDestination(
      route: '/importer',
      icon: Icons.upload_file_outlined,
      selectedIcon: Icons.upload_file,
      label: (l) => l.navImport,
    ),
  ],
  shellRoutes: [
    ModuleShellRoute(
      path: '/dashboard',
      builder: () => LayoutBuilder(
        builder: (context, constraints) => constraints.maxWidth < 700
            ? const DashboardConvergentScreen()
            : const DashboardScreen(),
      ),
    ),
    ModuleShellRoute(path: '/journal', builder: () => const JournalScreen()),
    ModuleShellRoute(path: '/summary', builder: () => const AISummaryScreen()),
    ModuleShellRoute(path: '/importer', builder: () => const ImportScreen()),
  ],
  fullScreenRoutes: [
    ModuleFullScreenRoute(
      path: '/ajouter',
      builder: (s) => AddLogScreen(
        focus: _focusFromState(s.uri.queryParameters['focus']),
      ),
    ),
    ModuleFullScreenRoute(path: '/medications', builder: (s) => const MedicationScreen()),
    ModuleFullScreenRoute(path: '/reminders', builder: (s) => const RemindersScreen()),
    ModuleFullScreenRoute(path: '/pulper', builder: (s) => const DocumentImportScreen()),
    ModuleFullScreenRoute(
      path: '/journal/:id/edit',
      builder: (s) => EditLogScreen(logId: int.parse(s.pathParameters['id']!)),
    ),
  ],
);
''')

# 6) Mobile shell: four real destinations around the central add button.
shell_path = root / 'frontend/lib/features/navigation/main_shell.dart'
shell = shell_path.read_text()
shell = shell.replace(
    "      icon: Icons.settings_outlined,\n      selectedIcon: Icons.settings_rounded,\n      label: (l10n) => l10n.navSettings,",
    "      icon: Icons.person_outline_rounded,\n      selectedIcon: Icons.person_rounded,\n      label: (l10n) => l10n.profile,",
    1,
)
start = shell.index('class _BottomNav extends StatelessWidget')
bottom = r'''class _BottomNav extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;

  const _BottomNav({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final mobileEntries = entries
        .where((entry) => entry.route != '/importer')
        .toList(growable: false);
    final currentPath = GoRouterState.of(context).uri.path;
    final safeIndex = _selectedIndexFor(currentPath, mobileEntries)
        .clamp(0, mobileEntries.length - 1);
    final rtl = Directionality.of(context) == TextDirection.rtl;
    final visualIndex = rtl
        ? mobileEntries.length - 1 - safeIndex
        : safeIndex;
    final glassColor = dark
        ? AminaTheme.darkCard.withValues(alpha: 0.88)
        : Colors.white.withValues(alpha: 0.92);
    final glassBorder = dark
        ? Colors.white.withValues(alpha: 0.12)
        : Colors.white.withValues(alpha: 0.92);
    final indicatorColor = dark
        ? AminaTheme.teal700.withValues(alpha: 0.34)
        : AminaTheme.teal50.withValues(alpha: 0.96);
    final addLabel = AppLocalizations.of(context)!.addEntry;

    return SafeArea(
      top: false,
      minimum: EdgeInsets.symmetric(horizontal: 12).copyWith(bottom: 10),
      child: SizedBox(
        height: 92,
        child: Stack(
          alignment: Alignment.topCenter,
          clipBehavior: Clip.none,
          children: [
            Positioned.fill(
              top: 20,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(28),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                  child: Container(
                    height: 72,
                    decoration: BoxDecoration(
                      color: glassColor,
                      borderRadius: BorderRadius.circular(28),
                      border: Border.all(color: glassBorder, width: 1),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: dark ? 0.24 : 0.10),
                          blurRadius: 28,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        final itemWidth = constraints.maxWidth / mobileEntries.length;
                        return Material(
                          color: Colors.transparent,
                          child: Stack(
                            children: [
                              AnimatedPositioned(
                                duration: AminaMotion.resolve(context, AminaMotion.navSelection),
                                curve: AminaMotion.enter,
                                left: visualIndex * itemWidth + 4,
                                top: 8,
                                width: itemWidth - 8,
                                height: 56,
                                child: IgnorePointer(
                                  child: DecoratedBox(
                                    decoration: BoxDecoration(
                                      color: indicatorColor,
                                      borderRadius: BorderRadius.circular(22),
                                      border: Border.all(
                                        color: dark
                                            ? AminaTheme.teal400.withValues(alpha: 0.16)
                                            : AminaTheme.teal500.withValues(alpha: 0.12),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              Row(
                                children: [
                                  for (var index = 0; index < mobileEntries.length; index++)
                                    Expanded(
                                      child: Padding(
                                        padding: EdgeInsetsDirectional.only(
                                          end: index == 1 ? 22 : 0,
                                          start: index == 2 ? 22 : 0,
                                        ),
                                        child: _GlassNavDestination(
                                          entry: mobileEntries[index],
                                          selected: index == safeIndex,
                                          onTap: () {
                                            HapticFeedback.selectionClick();
                                            GoRouter.of(context).go(mobileEntries[index].route);
                                          },
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ),
            ),
            Semantics(
              button: true,
              label: addLabel,
              child: Tooltip(
                message: addLabel,
                child: InkWell(
                  key: const ValueKey('mobile-nav-add'),
                  onTap: () {
                    HapticFeedback.lightImpact();
                    GoRouter.of(context).go('/ajouter');
                  },
                  customBorder: const CircleBorder(),
                  child: Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF0A766B), Color(0xFF064D50)],
                        begin: AlignmentDirectional.topStart,
                        end: AlignmentDirectional.bottomEnd,
                      ),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: dark ? AminaTheme.darkCard : Colors.white,
                        width: 5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF064D50).withValues(alpha: 0.30),
                          blurRadius: 18,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(Icons.add_rounded, color: Colors.white, size: 27),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GlassNavDestination extends StatelessWidget {
  final _NavEntry entry;
  final bool selected;
  final VoidCallback onTap;

  const _GlassNavDestination({
    required this.entry,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final label = entry.label(AppLocalizations.of(context)!);
    final activeColor = dark ? AminaTheme.teal400 : AminaTheme.teal700;
    final inactiveColor = dark ? AminaTheme.dark400 : AminaTheme.ink400;

    return Semantics(
      button: true,
      selected: selected,
      label: label,
      child: InkWell(
        key: ValueKey('mobile-nav-${entry.route}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: SizedBox(
          height: 72,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedScale(
                scale: selected ? 1.06 : 1.0,
                duration: AminaMotion.resolve(context, AminaMotion.navSelection),
                curve: AminaMotion.enter,
                child: Icon(
                  selected ? entry.selectedIcon : entry.icon,
                  color: selected ? activeColor : inactiveColor,
                  size: 20,
                ),
              ),
              const SizedBox(height: 4),
              AnimatedDefaultTextStyle(
                duration: AminaMotion.resolve(context, AminaMotion.navSelection),
                curve: AminaMotion.enter,
                style: TextStyle(
                  fontSize: 9.2,
                  height: 1.05,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                  color: selected ? activeColor : inactiveColor,
                  fontFamily: 'Inter',
                ),
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
'''
shell = shell[:start] + bottom
shell_path.write_text(shell)

# 7) Dashboard exact quick-action semantics + truthful import affordance.
dash_path = root / 'frontend/lib/features/dashboard/dashboard_convergent_screen.dart'
dash = dash_path.read_text()
old_brand = r'''        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            onTap: () => GoRouter.of(context).go('/summary'),
            customBorder: const CircleBorder(),
            child: SizedBox(
              width: 46,
              height: 46,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Icon(
                    Icons.notifications_none_rounded,
                    size: 21,
                    color: AminaTheme.textPrimary(context),
                  ),
                  const PositionedDirectional(
                    top: 8,
                    end: 8,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: Color(0xFF31C78A),
                        shape: BoxShape.circle,
                      ),
                      child: SizedBox(width: 7, height: 7),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),'''
new_brand = r'''        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            onTap: () => GoRouter.of(context).go('/importer'),
            customBorder: const CircleBorder(),
            child: SizedBox(
              width: 46,
              height: 46,
              child: Icon(
                Icons.upload_file_outlined,
                size: 21,
                color: AminaTheme.textPrimary(context),
              ),
            ),
          ),
        ),'''
assert old_brand in dash
dash = dash.replace(old_brand, new_brand, 1)
qa_start = dash.index('class _QuickActionsRow extends StatelessWidget')
qa_end = dash.index('class _DetailedTrendCard extends StatelessWidget')
qa = r'''class _QuickActionsRow extends StatelessWidget {
  const _QuickActionsRow();

  @override
  Widget build(BuildContext context) {
    final actions = <({IconData icon, String label, String route})>[
      (
        icon: Icons.menu_book_outlined,
        label: _t(context, 'Journal', 'Journal', 'السجل'),
        route: '/journal',
      ),
      (
        icon: Icons.restaurant_outlined,
        label: _t(context, 'Alimentation', 'Food', 'التغذية'),
        route: '/ajouter?focus=meal',
      ),
      (
        icon: Icons.directions_run_rounded,
        label: _t(context, 'Activité', 'Activity', 'النشاط'),
        route: '/ajouter?focus=activity',
      ),
      (
        icon: Icons.medication_outlined,
        label: _t(context, 'Médicaments', 'Medications', 'الأدوية'),
        route: '/medications',
      ),
      (
        icon: Icons.notifications_none_rounded,
        label: _t(context, 'Rappels', 'Reminders', 'التذكيرات'),
        route: '/reminders',
      ),
    ];
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final action in actions)
          Expanded(
            child: InkWell(
              key: ValueKey('dashboard-action-${action.route}'),
              onTap: () => GoRouter.of(context).go(action.route),
              borderRadius: BorderRadius.circular(15),
              child: Column(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: AminaTheme.surface(context),
                      borderRadius: BorderRadius.circular(15),
                      border: Border.all(color: AminaTheme.divider(context)),
                    ),
                    child: Icon(
                      action.icon,
                      size: 20,
                      color: const Color(0xFF064E52),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    action.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 8.8,
                      fontWeight: FontWeight.w600,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

'''
dash = dash[:qa_start] + qa + dash[qa_end:]
dash_path.write_text(dash)

# 8) Contract test.
test_path = root / 'frontend/test/ux11_action_parity_contract_test.dart'
test_path.write_text(r'''import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('UX-11 dashboard actions and mobile nav preserve approved semantics', () {
    final dash = File('lib/features/dashboard/dashboard_convergent_screen.dart').readAsStringSync();
    for (final label in ['Journal', 'Alimentation', 'Activité', 'Médicaments', 'Rappels']) {
      expect(dash, contains("'$label'"));
    }
    expect(dash, contains("'/ajouter?focus=meal'"));
    expect(dash, contains("'/ajouter?focus=activity'"));
    expect(dash, contains("'/medications'"));
    expect(dash, contains("'/reminders'"));
    expect(dash, contains("go('/importer')"));

    final module = File('lib/modules/diabetes_module.dart').readAsStringSync();
    expect(module, contains("'Mesures'"));
    expect(module, contains("'Rapports'"));
    expect(module, contains("route: '/importer'"));

    final shell = File('lib/features/navigation/main_shell.dart').readAsStringSync();
    expect(shell, contains("entry.route != '/importer'"));
    expect(shell, contains("label: (l10n) => l10n.profile"));
    expect(shell, contains('mobile-nav-add'));
  });
}
''')
