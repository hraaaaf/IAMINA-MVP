from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one target in {path}, found {count}")
    target.write_text(text.replace(old, new, 1))


replace_once(
    "frontend/lib/data/drift/database.dart",
    """  Future<void> setRamadanPeriod({DateTime? start, DateTime? end}) async {
    if ((start == null) != (end == null)) {
      throw ArgumentError('Ramadan period requires both dates or neither');
    }
    if (start != null && end != null && start.isAfter(end)) {
      throw ArgumentError('Ramadan period start must not be after end');
    }
    final existing = await (select(
      patientProfiles,
    )..limit(1)).getSingleOrNull();
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
""",
    """  Future<bool> setRamadanPeriod({DateTime? start, DateTime? end}) async {
    if ((start == null) != (end == null)) {
      throw ArgumentError('Ramadan period requires both dates or neither');
    }
    if (start != null && end != null && start.isAfter(end)) {
      throw ArgumentError('Ramadan period start must not be after end');
    }
    final existing = await (select(
      patientProfiles,
    )..limit(1)).getSingleOrNull();
    if (existing == null) return false;

    final updated = await (update(
      patientProfiles,
    )..where((row) => row.userId.equals(existing.userId))).write(
      PatientProfilesCompanion(
        updatedAt: Value(DateTime.now()),
        ramadanStartDate: Value(start),
        ramadanEndDate: Value(end),
      ),
    );
    return updated == 1;
  }
""",
)

replace_once(
    "frontend/lib/features/profile/profile_screen.dart",
    """      await db.setRamadanPeriod(start: start, end: end);
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
""",
    """      final localSaved = await db.setRamadanPeriod(start: start, end: end);
      final serverSaved = await api.patchProfile({
        'ramadan_start_date': start == null ? null : _apiDate(start),
        'ramadan_end_date': end == null ? null : _apiDate(end),
      });
      if (!mounted) return;
      if (localSaved) setState(() => _hasPersistedProfile = true);

      late final String message;
      late final Color backgroundColor;
      if (localSaved && serverSaved) {
        message = l10n.ramadanSaved;
        backgroundColor = AminaTheme.successEmerald;
      } else if (localSaved) {
        message = l10n.ramadanSavedLocalOnly;
        backgroundColor = AminaTheme.warningOrange;
      } else if (serverSaved) {
        message = l10n.ramadanSavedServerOnly;
        backgroundColor = AminaTheme.warningOrange;
      } else {
        message = l10n.ramadanSaveFailed;
        backgroundColor = AminaTheme.dangerFg;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: backgroundColor,
          behavior: SnackBarBehavior.floating,
        ),
      );
""",
)

for path, old, new in [
    (
        "frontend/lib/l10n/app_en.arb",
        '  "ramadanSavedLocalOnly": "Saved on this device. The server was not updated.",\n',
        '  "ramadanSavedLocalOnly": "Saved on this device. The server was not updated.",\n'
        '  "ramadanSavedServerOnly": "Saved to your account. No local profile was available on this device.",\n'
        '  "ramadanSaveFailed": "The Ramadan period was not saved. Retry after your profile is available or your connection is restored.",\n',
    ),
    (
        "frontend/lib/l10n/app_fr.arb",
        '  "ramadanSavedLocalOnly": "Enregistrée sur cet appareil. Le serveur n’a pas été mis à jour.",\n',
        '  "ramadanSavedLocalOnly": "Enregistrée sur cet appareil. Le serveur n’a pas été mis à jour.",\n'
        '  "ramadanSavedServerOnly": "Enregistrée sur ton compte. Aucun profil local n’était disponible sur cet appareil.",\n'
        '  "ramadanSaveFailed": "Impossible d’enregistrer la période. Réessaie lorsque ton profil est disponible ou que la connexion est rétablie.",\n',
    ),
    (
        "frontend/lib/l10n/app_ar.arb",
        '  "ramadanSavedLocalOnly": "تم الحفظ على هذا الجهاز. لم يتم تحديث الخادم.",\n',
        '  "ramadanSavedLocalOnly": "تم الحفظ على هذا الجهاز. لم يتم تحديث الخادم.",\n'
        '  "ramadanSavedServerOnly": "تم الحفظ في حسابك. لم يكن هناك ملف محلي متاح على هذا الجهاز.",\n'
        '  "ramadanSaveFailed": "تعذر حفظ فترة رمضان. أعد المحاولة عندما يصبح ملفك متاحًا أو يعود الاتصال.",\n',
    ),
]:
    replace_once(path, old, new)

migration_test = Path("frontend/test/data/drift/ramadan_period_migration_test.dart")
text = migration_test.read_text()
old_import = "import 'package:amina/data/drift/database.dart';\nimport 'package:drift/native.dart';"
new_import = "import 'package:amina/data/drift/database.dart';\nimport 'package:drift/drift.dart' as drift;\nimport 'package:drift/native.dart';"
if old_import not in text:
    raise SystemExit("migration test import target not found")
text = text.replace(old_import, new_import, 1)

insertion = r'''

  test('Ramadan save never manufactures a fresh medical profile', () async {
    final db = AppDatabase(NativeDatabase.memory());
    try {
      final saved = await db.setRamadanPeriod(
        start: DateTime(2026, 2, 18),
        end: DateTime(2026, 3, 20),
      );
      expect(saved, isFalse);
      expect(await db.select(db.patientProfiles).getSingleOrNull(), isNull);
    } finally {
      await db.close();
    }
  });

  test('Ramadan save preserves existing clinical profile values', () async {
    final db = AppDatabase(NativeDatabase.memory());
    try {
      await db.into(db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const drift.Value(7),
          updatedAt: DateTime(2026, 8, 10),
          diabetesType: const drift.Value('type2'),
          targetRangeLow: const drift.Value(82),
          targetRangeHigh: const drift.Value(155),
          unitPreference: const drift.Value('mmol/L'),
          treatment: const drift.Value('lifestyle'),
        ),
      );

      final saved = await db.setRamadanPeriod(
        start: DateTime(2026, 2, 18),
        end: DateTime(2026, 3, 20),
      );
      final profile = await db.select(db.patientProfiles).getSingle();

      expect(saved, isTrue);
      expect(profile.userId, 7);
      expect(profile.diabetesType, 'type2');
      expect(profile.targetRangeLow, 82);
      expect(profile.targetRangeHigh, 155);
      expect(profile.unitPreference, 'mmol/L');
      expect(profile.treatment, 'lifestyle');
      expect(profile.ramadanStartDate, DateTime(2026, 2, 18));
      expect(profile.ramadanEndDate, DateTime(2026, 3, 20));
    } finally {
      await db.close();
    }
  });
'''
pos = text.rfind("\n}\n")
if pos < 0:
    raise SystemExit("migration test closing brace not found")
migration_test.write_text(text[:pos] + insertion + text[pos:])
