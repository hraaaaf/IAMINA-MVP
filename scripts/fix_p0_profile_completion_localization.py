#!/usr/bin/env python3
"""Close the remaining audited Profile completion copy in FR/EN/AR."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, got {count}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


copy_path = root / "frontend/lib/l10n/audited_page_copy.dart"
copy_source = copy_path.read_text(encoding="utf-8")
old_tail = """  String get profileComplete =>
      pick(fr: 'Profil complet', en: 'Profile complete', ar: 'الملف مكتمل');
  String get minimum => pick(fr: 'Min', en: 'Min', ar: 'الحد الأدنى');
  String get maximum => pick(fr: 'Max', en: 'Max', ar: 'الحد الأقصى');
}
"""
new_tail = """  String get profileComplete =>
      pick(fr: 'Profil complet', en: 'Profile complete', ar: 'الملف مكتمل');

  String profileCompletionLabel(int percentage) => percentage >= 100
      ? pick(
          fr: 'Profil complet ✓',
          en: 'Profile complete ✓',
          ar: 'الملف مكتمل ✓',
        )
      : pick(
          fr: 'Profil complété à $percentage%',
          en: 'Profile $percentage% complete',
          ar: 'اكتمل الملف بنسبة $percentage٪',
        );

  String get profileCompletionPrompt => pick(
    fr: 'Complétez votre profil pour des analyses plus précises.',
    en: 'Complete your profile for more precise analyses.',
    ar: 'أكمل ملفك للحصول على تحليلات أدق.',
  );

  String get minimum => pick(fr: 'Min', en: 'Min', ar: 'الحد الأدنى');
  String get maximum => pick(fr: 'Max', en: 'Max', ar: 'الحد الأقصى');
}
"""
if copy_source.count(old_tail) != 1:
    raise SystemExit("audited copy tail changed")
copy_path.write_text(copy_source.replace(old_tail, new_tail, 1), encoding="utf-8")

profile_path = root / "frontend/lib/features/profile/profile_screen.dart"
replace_once(
    profile_path,
    """    final label = pct >= 100 ? 'Profil complet ✓' : 'Profil complété à $pct%';
""",
    """    final copy = AuditedPageCopy.of(context);
    final label = copy.profileCompletionLabel(pct);
""",
    "profile completion label",
)
replace_once(
    profile_path,
    """            const Text(
              'Complétez votre profil pour des analyses plus précises.',
              style: TextStyle(
""",
    """            Text(
              copy.profileCompletionPrompt,
              style: const TextStyle(
""",
    "profile completion prompt",
)

test_path = root / "frontend/test/p0_audited_page_localization_contract_test.dart"
test_source = test_path.read_text(encoding="utf-8")
old_required = """      'الملف مكتمل',
    ]) {
"""
new_required = """      'الملف مكتمل',
      'اكتمل الملف بنسبة',
      'أكمل ملفك للحصول على تحليلات أدق.',
    ]) {
"""
if test_source.count(old_required) != 1:
    raise SystemExit("localization required-list shape changed")
test_source = test_source.replace(old_required, new_required, 1)
old_forbidden = """      "'Profil complet'",
    ]) {
"""
new_forbidden = """      "'Profil complet'",
      "'Profil complet ✓'",
      "'Profil complété à",
      'Complétez votre profil pour des analyses plus précises.',
    ]) {
"""
if test_source.count(old_forbidden) != 1:
    raise SystemExit("localization forbidden-list shape changed")
test_path.write_text(test_source.replace(old_forbidden, new_forbidden, 1), encoding="utf-8")

print("Profile completion localization closed.")
