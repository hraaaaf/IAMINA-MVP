from pathlib import Path
import json

def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'marker missing in {path}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1))

replace_once(
    'frontend/lib/data/drift/database.dart',
    '  /// RGPD Art. 7 — explicit AI processing consent timestamp.\n',
    '  DateTimeColumn get ramadanStartDate => dateTime().nullable()();\n'
    '  DateTimeColumn get ramadanEndDate => dateTime().nullable()();\n\n'
    '  /// RGPD Art. 7 — explicit AI processing consent timestamp.\n',
)
replace_once(
    'frontend/lib/data/drift/database.dart',
    '  int get schemaVersion => 8;',
    '  int get schemaVersion => 9;',
)
replace_once(
    'frontend/lib/data/drift/database.dart',
    '      if (from < 8) {\n        await m.addColumn(logEntries, logEntries.mealPortionsJson);\n      }\n',
    '      if (from < 8) {\n        await m.addColumn(logEntries, logEntries.mealPortionsJson);\n      }\n'
    '      if (from < 9) {\n'
    '        await m.addColumn(patientProfiles, patientProfiles.ramadanStartDate);\n'
    '        await m.addColumn(patientProfiles, patientProfiles.ramadanEndDate);\n'
    '      }\n',
)
replace_once(
    'frontend/lib/data/drift/database.dart',
    '  // Watchers\n',
    '''  Future<void> setRamadanPeriod({DateTime? start, DateTime? end}) async {
    if ((start == null) != (end == null)) {
      throw ArgumentError('Ramadan period requires both dates or neither');
    }
    if (start != null && end != null && start.isAfter(end)) {
      throw ArgumentError('Ramadan period start must not be after end');
    }
    final existing = await (select(patientProfiles)..limit(1)).getSingleOrNull();
    final userId = existing?.userId ?? 1;
    await into(patientProfiles).insertOnConflictUpdate(
      PatientProfilesCompanion.insert(
        userId: Value(userId),
        updatedAt: DateTime.now(),
        ramadanStartDate: Value(start),
        ramadanEndDate: Value(end),
      ),
    );
  }

  // Watchers
''',
)

Path('frontend/lib/core/data/ramadan_context.dart').write_text('''const List<String> regularMealTypes = <String>[
  'breakfast',
  'lunch',
  'dinner',
  'snack',
];

const List<String> ramadanMealTypes = <String>[
  'suhoor',
  'iftar',
  'snack',
  'other',
];

DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);

bool isRamadanProfileDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd,
) {
  if (configuredStart == null || configuredEnd == null) return false;
  final day = _dateOnly(eventDate);
  final start = _dateOnly(configuredStart);
  final end = _dateOnly(configuredEnd);
  return !day.isBefore(start) && !day.isAfter(end);
}

List<String> mealTypesForProfileDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd,
) =>
    isRamadanProfileDate(eventDate, configuredStart, configuredEnd)
    ? ramadanMealTypes
    : regularMealTypes;
''')

replace_once(
    'frontend/lib/services/api_client.dart',
    '  /// Envoie un log unique au backend.\n',
    '''  Future<bool> patchProfile(Map<String, dynamic> patch) async {
    try {
      final response = await _client.patch(
        Uri.parse('/api/v1/profile'),
        body: patch,
      );
      return response.isSuccessful;
    } catch (_) {
      return false;
    }
  }

  /// Envoie un log unique au backend.
''',
)

replace_once(
    'frontend/lib/features/profile/profile_screen.dart',
    '  bool _hasPersistedProfile = false;\n',
    '  bool _hasPersistedProfile = false;\n'
    '  DateTime? _ramadanStartDate;\n'
    '  DateTime? _ramadanEndDate;\n'
    '  bool _savingRamadan = false;\n',
)
replace_once(
    'frontend/lib/features/profile/profile_screen.dart',
    '        _targetHighController.text = profile.targetRangeHigh.toStringAsFixed(0);\n',
    '        _targetHighController.text = profile.targetRangeHigh.toStringAsFixed(0);\n'
    '        _ramadanStartDate = profile.ramadanStartDate;\n'
    '        _ramadanEndDate = profile.ramadanEndDate;\n',
)
replace_once(
    'frontend/lib/features/profile/profile_screen.dart',
    '''                  _buildMedicalSection(l10n),
        const SizedBox(height: 14),
        _buildProfileSection(
''',
    '''                  _buildMedicalSection(l10n),
        const SizedBox(height: 14),
        _buildRamadanSection(l10n),
        const SizedBox(height: 14),
        _buildProfileSection(
''',
)
replace_once(
    'frontend/lib/features/profile/profile_screen.dart',
    '  Widget _buildAccountSection(AppLocalizations l10n) {\n',
    '''  Widget _buildRamadanSection(AppLocalizations l10n) {
    final configured = _ramadanStartDate != null && _ramadanEndDate != null;
    return _buildProfileSection(
      key: const ValueKey('profile-ramadan-section'),
      icon: Icons.nightlight_round,
      title: l10n.ramadanProfileSection,
      subtitle: configured
? '${_dateLabel(_ramadanStartDate!)} → ${_dateLabel(_ramadanEndDate!)}'
: l10n.ramadanNotConfigured,
      initiallyExpanded: false,
      children: [
        Text(
l10n.ramadanProfileHint,
style: const TextStyle(
  color: AminaTheme.ink500,
  fontSize: 13,
  height: 1.45,
),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
builder: (context, constraints) {
  final compact = constraints.maxWidth < 460;
  final start = _ramadanDateButton(
    key: const Key('ramadan-start-date'),
    label: l10n.ramadanStartDate,
    value: _ramadanStartDate,
    onTap: () => _pickRamadanDate(start: true),
  );
  final end = _ramadanDateButton(
    key: const Key('ramadan-end-date'),
    label: l10n.ramadanEndDate,
    value: _ramadanEndDate,
    onTap: () => _pickRamadanDate(start: false),
  );
  if (compact) {
    return Column(children: [start, const SizedBox(height: 10), end]);
  }
  return Row(
    children: [
      Expanded(child: start),
      const SizedBox(width: 12),
      Expanded(child: end),
    ],
  );
},
        ),
        const SizedBox(height: 12),
        Row(
children: [
  if (configured)
    TextButton(
      key: const Key('ramadan-clear-period'),
      onPressed: _savingRamadan
          ? null
          : () => setState(() {
              _ramadanStartDate = null;
              _ramadanEndDate = null;
            }),
      child: Text(l10n.ramadanClear),
    ),
  const Spacer(),
  FilledButton(
    key: const Key('ramadan-save-period'),
    onPressed: _savingRamadan ? null : () => _saveRamadanPeriod(l10n),
    child: Text(_savingRamadan ? l10n.journalSaving : l10n.ramadanSave),
  ),
],
        ),
      ],
    );
  }

  Widget _ramadanDateButton({
    required Key key,
    required String label,
    required DateTime? value,
    required VoidCallback onTap,
  }) {
    return OutlinedButton(
      key: key,
      onPressed: _savingRamadan ? null : onTap,
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        alignment: AlignmentDirectional.centerStart,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
Text(label, style: const TextStyle(fontSize: 11, color: AminaTheme.ink500)),
const SizedBox(height: 3),
Text(
  value == null ? AppLocalizations.of(context)!.ramadanChooseDate : _dateLabel(value),
  style: const TextStyle(fontWeight: FontWeight.w700, color: AminaTheme.ink900),
),
        ],
      ),
    );
  }

  Future<void> _pickRamadanDate({required bool start}) async {
    final initial = start
        ? (_ramadanStartDate ?? DateTime.now())
        : (_ramadanEndDate ?? _ramadanStartDate ?? DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035, 12, 31),
    );
    if (picked == null || !mounted) return;
    setState(() {
      if (start) {
        _ramadanStartDate = DateTime(picked.year, picked.month, picked.day);
      } else {
        _ramadanEndDate = DateTime(picked.year, picked.month, picked.day);
      }
    });
  }

  Future<void> _saveRamadanPeriod(AppLocalizations l10n) async {
    final start = _ramadanStartDate;
    final end = _ramadanEndDate;
    if ((start == null) != (end == null)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.ramadanNeedsBothDates)),
      );
      return;
    }
    if (start != null && end != null && start.isAfter(end)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.ramadanDateOrderError)),
      );
      return;
    }

    setState(() => _savingRamadan = true);
    try {
      final db = context.read<AppDatabase>();
      final api = context.read<ApiClient>();
      await db.setRamadanPeriod(start: start, end: end);
      final serverSaved = await api.patchProfile({
        'ramadan_start_date': start == null ? null : _apiDate(start),
        'ramadan_end_date': end == null ? null : _apiDate(end),
      });
      if (!mounted) return;
      setState(() => _hasPersistedProfile = true);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
content: Text(
  serverSaved ? l10n.ramadanSaved : l10n.ramadanSavedLocalOnly,
),
backgroundColor: serverSaved
    ? AminaTheme.successEmerald
    : AminaTheme.warningOrange,
behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _savingRamadan = false);
    }
  }

  String _dateLabel(DateTime value) {
    final dd = value.day.toString().padLeft(2, '0');
    final mm = value.month.toString().padLeft(2, '0');
    return '$dd/$mm/${value.year}';
  }

  String _apiDate(DateTime value) {
    final mm = value.month.toString().padLeft(2, '0');
    final dd = value.day.toString().padLeft(2, '0');
    return '${value.year}-$mm-$dd';
  }

  Widget _buildAccountSection(AppLocalizations l10n) {
''',
)

replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    "import '../../../core/data/nutrition_catalog.dart';\n",
    "import '../../../core/data/nutrition_catalog.dart';\nimport '../../../core/data/ramadan_context.dart';\n",
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    "  static const List<String> _mealTypes = <String>[\n    'breakfast',\n    'lunch',\n    'dinner',\n    'snack',\n  ];\n\n",
    '',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '''                                  profile?.aiConsentGivenAt != null,
                      ),''',
    '''                                  profile?.aiConsentGivenAt != null,
                        profile,
                      ),''',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '''                            profile?.aiConsentGivenAt != null,
                ),''',
    '''                            profile?.aiConsentGivenAt != null,
                  profile,
                ),''',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '''    bool canUsePhotoRecognition,
  ) => Column(''',
    '''    bool canUsePhotoRecognition,
    PatientProfileData? profile,
  ) => Column(''',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '      _mealCapture(l10n, canUsePhotoRecognition),\n',
    '      _mealCapture(l10n, canUsePhotoRecognition, profile),\n',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '  Widget _mealCapture(AppLocalizations l10n, bool canUsePhotoRecognition) {\n    if (!_mealExpanded) {',
    '''  Widget _mealCapture(
    AppLocalizations l10n,
    bool canUsePhotoRecognition,
    PatientProfileData? profile,
  ) {
    final ramadanActive = isRamadanProfileDate(
      _selectedTime,
      profile?.ramadanStartDate,
      profile?.ramadanEndDate,
    );
    final mealTypes = mealTypesForProfileDate(
      _selectedTime,
      profile?.ramadanStartDate,
      profile?.ramadanEndDate,
    );
    if (!_mealExpanded) {''',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '''          const SizedBox(height: 8),
Wrap(
  spacing: 8,
  runSpacing: 8,
  children: _mealTypes.map((value) {''',
    '''          const SizedBox(height: 8),
if (ramadanActive) ...<Widget>[
  Text(
    l10n.journalRamadanMealVocabularyHint,
    key: const Key('ramadan-meal-vocabulary-hint'),
    style: _helperStyle(),
  ),
  const SizedBox(height: 10),
],
Wrap(
  spacing: 8,
  runSpacing: 8,
  children: mealTypes.map((value) {''',
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    "    'dinner' => l10n.journalMealDinner,\n    _ => l10n.journalMealSnack,\n  };",
    "    'dinner' => l10n.journalMealDinner,\n"
    "    'suhoor' => l10n.journalMealSuhoor,\n"
    "    'iftar' => l10n.journalMealIftar,\n"
    "    'other' => l10n.journalMealOther,\n"
    "    _ => l10n.journalMealSnack,\n  };",
)
replace_once(
    'frontend/lib/features/dashboard/widgets/add_log_sheet.dart',
    '''    setState(() {
      _selectedTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });''',
    '''    final profile = context.read<PatientProfileData?>();
    setState(() {
      _selectedTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
      final allowed = mealTypesForProfileDate(
        _selectedTime,
        profile?.ramadanStartDate,
        profile?.ramadanEndDate,
      );
      if (_mealType != null && !allowed.contains(_mealType)) {
        _mealType = null;
      }
    });''',
)

replace_once(
    'frontend/lib/features/journal/journal_screen.dart',
    "      case 'snack':\n        return l10n.journalMealSnack;\n",
    "      case 'snack':\n        return l10n.journalMealSnack;\n"
    "      case 'iftar':\n        return l10n.journalMealIftar;\n"
    "      case 'suhoor':\n        return l10n.journalMealSuhoor;\n"
    "      case 'other':\n        return l10n.journalMealOther;\n",
)

copies = {
    'fr': {
        'ramadanProfileSection': 'Période de Ramadan',
        'ramadanProfileHint': 'Optionnel. Cette période adapte les noms de repas dans le journal. IAmina n’en déduit pas que tu jeûnes.',
        'ramadanNotConfigured': 'Non configurée',
        'ramadanStartDate': 'Début',
        'ramadanEndDate': 'Fin',
        'ramadanChooseDate': 'Choisir une date',
        'ramadanClear': 'Effacer la période',
        'ramadanSave': 'Enregistrer',
        'ramadanSaved': 'Période de Ramadan enregistrée.',
        'ramadanSavedLocalOnly': 'Enregistrée sur cet appareil. Le serveur n’a pas été mis à jour.',
        'ramadanNeedsBothDates': 'Choisis une date de début et une date de fin, ou efface les deux.',
        'ramadanDateOrderError': 'La date de début doit précéder ou être égale à la date de fin.',
        'journalRamadanMealVocabularyHint': 'Repas adaptés à la période enregistrée dans ton profil. Aucun jeûne n’est supposé.',
        'journalMealSuhoor': 'Suhoor',
        'journalMealIftar': 'Iftar',
        'journalMealOther': 'Autre',
    },
    'en': {
        'ramadanProfileSection': 'Ramadan period',
        'ramadanProfileHint': 'Optional. This period adapts meal names in the journal. IAmina does not infer that you are fasting.',
        'ramadanNotConfigured': 'Not configured',
        'ramadanStartDate': 'Start',
        'ramadanEndDate': 'End',
        'ramadanChooseDate': 'Choose a date',
        'ramadanClear': 'Clear period',
        'ramadanSave': 'Save',
        'ramadanSaved': 'Ramadan period saved.',
        'ramadanSavedLocalOnly': 'Saved on this device. The server was not updated.',
        'ramadanNeedsBothDates': 'Choose both a start and end date, or clear both.',
        'ramadanDateOrderError': 'The start date must be on or before the end date.',
        'journalRamadanMealVocabularyHint': 'Meal names follow the period saved in your profile. Fasting is not assumed.',
        'journalMealSuhoor': 'Suhoor',
        'journalMealIftar': 'Iftar',
        'journalMealOther': 'Other',
    },
    'ar': {
        'ramadanProfileSection': 'فترة رمضان',
        'ramadanProfileHint': 'اختياري. تُكيّف هذه الفترة أسماء الوجبات في السجل. لا تفترض IAmina أنك صائم.',
        'ramadanNotConfigured': 'غير محددة',
        'ramadanStartDate': 'البداية',
        'ramadanEndDate': 'النهاية',
        'ramadanChooseDate': 'اختر تاريخًا',
        'ramadanClear': 'مسح الفترة',
        'ramadanSave': 'حفظ',
        'ramadanSaved': 'تم حفظ فترة رمضان.',
        'ramadanSavedLocalOnly': 'تم الحفظ على هذا الجهاز. لم يتم تحديث الخادم.',
        'ramadanNeedsBothDates': 'اختر تاريخ البداية وتاريخ النهاية معًا، أو امسحهما معًا.',
        'ramadanDateOrderError': 'يجب أن يكون تاريخ البداية قبل تاريخ النهاية أو مساويًا له.',
        'journalRamadanMealVocabularyHint': 'تتكيف أسماء الوجبات مع الفترة المحفوظة في ملفك. لا يُفترض أنك صائم.',
        'journalMealSuhoor': 'السحور',
        'journalMealIftar': 'الإفطار',
        'journalMealOther': 'أخرى',
    },
}
for locale, values in copies.items():
    path = Path(f'frontend/lib/l10n/app_{locale}.arb')
    data = json.loads(path.read_text())
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

Path('frontend/test/core/data').mkdir(parents=True, exist_ok=True)
Path('frontend/test/core/data/ramadan_context_test.dart').write_text('''import 'package:amina/core/data/ramadan_context.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Ramadan context is never inferred without an explicit complete period', () {
    final day = DateTime(2026, 2, 20, 12);
    expect(isRamadanProfileDate(day, null, null), isFalse);
    expect(isRamadanProfileDate(day, DateTime(2026, 2, 18), null), isFalse);
    expect(mealTypesForProfileDate(day, null, null), regularMealTypes);
  });

  test('configured period is inclusive and switches vocabulary only', () {
    final start = DateTime(2026, 2, 18);
    final end = DateTime(2026, 3, 20);
    expect(isRamadanProfileDate(DateTime(2026, 2, 18, 23, 59), start, end), isTrue);
    expect(isRamadanProfileDate(DateTime(2026, 3, 20, 0, 1), start, end), isTrue);
    expect(isRamadanProfileDate(DateTime(2026, 3, 21), start, end), isFalse);
    expect(
      mealTypesForProfileDate(DateTime(2026, 3, 1), start, end),
      <String>['suhoor', 'iftar', 'snack', 'other'],
    );
  });
}
''')

Path('frontend/test/features/ramadan_mode_v2_test.dart').write_text('''import 'package:amina/data/drift/database.dart';
import 'package:amina/features/dashboard/widgets/add_log_sheet.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:drift/drift.dart' as drift;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

AppDatabase openDb() => AppDatabase(NativeDatabase.memory());

Widget sheet(AppDatabase db, PatientProfileData profile, {Locale locale = const Locale('fr')}) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Scaffold(
      body: MultiProvider(
        providers: [
Provider<AppDatabase>.value(value: db),
Provider<PatientProfileData?>.value(value: profile),
        ],
        child: const AddLogSheet(),
      ),
    ),
  );
}

Future<PatientProfileData> activeProfile(AppDatabase db) async {
  final now = DateTime.now();
  await db.into(db.patientProfiles).insert(
    PatientProfilesCompanion.insert(
      userId: const drift.Value(1),
      updatedAt: now,
      ramadanStartDate: drift.Value(now.subtract(const Duration(days: 1))),
      ramadanEndDate: drift.Value(now.add(const Duration(days: 1))),
    ),
  );
  return db.select(db.patientProfiles).getSingle();
}

void main() {
  late AppDatabase db;
  setUp(() => db = openDb());
  tearDown(() async => db.close());

  testWidgets('configured period adapts meal vocabulary without selecting a meal', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    final profile = await activeProfile(db);
    await tester.pumpWidget(sheet(db, profile));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('add-meal-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('ramadan-meal-vocabulary-hint')), findsOneWidget);
    expect(find.byKey(const Key('meal-type-suhoor')), findsOneWidget);
    expect(find.byKey(const Key('meal-type-iftar')), findsOneWidget);
    expect(find.byKey(const Key('meal-type-snack')), findsOneWidget);
    expect(find.byKey(const Key('meal-type-other')), findsOneWidget);
    expect(find.byKey(const Key('meal-type-breakfast')), findsNothing);
    for (final key in <String>['suhoor', 'iftar', 'snack', 'other']) {
      expect(tester.widget<ChoiceChip>(find.byKey(Key('meal-type-$key'))).selected, isFalse);
    }
    expect(find.textContaining('Aucun jeûne n’est supposé'), findsOneWidget);
  });

  testWidgets('Arabic Ramadan vocabulary is localized RTL and still neutral', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    final profile = await activeProfile(db);
    await tester.pumpWidget(sheet(db, profile, locale: const Locale('ar')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('add-meal-button')));
    await tester.pumpAndSettle();

    expect(find.text('السحور'), findsOneWidget);
    expect(find.text('الإفطار'), findsOneWidget);
    final hint = find.byKey(const Key('ramadan-meal-vocabulary-hint'));
    expect(hint, findsOneWidget);
    expect(Directionality.of(tester.element(hint)), TextDirection.rtl);
    expect(find.textContaining('لا يُفترض أنك صائم'), findsOneWidget);
  });
}
''')

Path('frontend/test/data/drift/ramadan_period_migration_test.dart').write_text("""import 'dart:io';

import 'package:amina/data/drift/database.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
// ignore: depend_on_referenced_packages
import 'package:sqlite3/sqlite3.dart' as sqlite;

void main() {
  test('Drift v8 to v9 adds nullable Ramadan profile period without rewriting logs', () async {
    final dir = await Directory.systemTemp.createTemp('iamina-journal-v8-');
    final file = File('${dir.path}/amina.sqlite');
    final legacy = sqlite.sqlite3.open(file.path);
    legacy.execute('''
      CREATE TABLE patient_profiles (
        user_id INTEGER NOT NULL PRIMARY KEY,
        preferred_language TEXT NOT NULL DEFAULT 'fr',
        updated_at INTEGER NOT NULL,
        diabetes_type TEXT,
        target_range_low REAL NOT NULL DEFAULT 70.0,
        target_range_high REAL NOT NULL DEFAULT 180.0,
        unit_preference TEXT NOT NULL DEFAULT 'mg/dL',
        treatment TEXT,
        ai_consent_given_at INTEGER
      );
    ''');
    legacy.execute('''
      INSERT INTO patient_profiles (user_id, updated_at, diabetes_type)
      VALUES (1, 1723200000, NULL);
    ''');
    legacy.execute('''
      CREATE TABLE log_entries (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        created_at INTEGER NOT NULL,
        blood_sugar REAL NOT NULL,
        insulin_units REAL,
        glycemic_context TEXT,
        meal_type TEXT,
        meal_description TEXT,
        meal_items_json TEXT,
        meal_portions_json TEXT,
        source TEXT NOT NULL DEFAULT 'manual',
        sync_status TEXT NOT NULL DEFAULT 'pending',
        client_uuid TEXT NOT NULL UNIQUE,
        logged_at INTEGER,
        fatigue_level INTEGER,
        is_sick INTEGER NOT NULL DEFAULT 0 CHECK (is_sick IN (0, 1)),
        is_stressed INTEGER NOT NULL DEFAULT 0 CHECK (is_stressed IN (0, 1)),
        is_tired INTEGER NOT NULL DEFAULT 0 CHECK (is_tired IN (0, 1)),
        is_active INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1)),
        ramadan_mode INTEGER NOT NULL DEFAULT 0 CHECK (ramadan_mode IN (0, 1)),
        sleep_quality TEXT,
        sync_attempts INTEGER NOT NULL DEFAULT 0,
        error_sync INTEGER NOT NULL DEFAULT 0 CHECK (error_sync IN (0, 1))
      );
    ''');
    legacy.execute('''
      INSERT INTO log_entries (
        created_at, blood_sugar, meal_type, source, sync_status, client_uuid, ramadan_mode
      ) VALUES (
        1723200000, 126.0, 'iftar', 'manual', 'pending',
        '99999999-9999-9999-9999-999999999999', 1
      );
    ''');
    legacy.execute('PRAGMA user_version = 8;');
    legacy.dispose();

    final db = AppDatabase(NativeDatabase(file));
    try {
      final profile = await db.select(db.patientProfiles).getSingle();
      expect(profile.ramadanStartDate, isNull);
      expect(profile.ramadanEndDate, isNull);
      final log = await db.select(db.logEntries).getSingle();
      expect(log.mealType, 'iftar');
      expect(log.ramadanMode, isTrue);
      expect(log.clientUuid, '99999999-9999-9999-9999-999999999999');
      final version = await db.customSelect('PRAGMA user_version').getSingle();
      expect(version.data['user_version'], 9);
    } finally {
      await db.close();
      await dir.delete(recursive: true);
    }
  });
}
""")
