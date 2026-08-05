#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, got {count}")
    return text.replace(old, new, 1)


# Dashboard library import only; all widget parts share this import.
path = "frontend/lib/features/dashboard/dashboard_screen.dart"
s = read(path)
s = replace_once(
    s,
    "import '../../core/widgets/clinical_card.dart';\n",
    "import '../../core/widgets/clinical_card.dart';\nimport '../../l10n/audited_page_copy.dart';\n",
    "dashboard audited copy import",
)
write(path, s)

# Top bar.
path = "frontend/lib/features/dashboard/widgets/top_bar.dart"
s = read(path)
s = replace_once(
    s,
    "      detailed ? 'Accueil · Vue d\\'ensemble' : 'Vue d\\'ensemble',",
    "      detailed\n          ? AuditedPageCopy.of(context).breadcrumb\n          : AuditedPageCopy.of(context).overview,",
    "dashboard breadcrumb",
)
s = replace_once(
    s,
    "      compact ? 'IAmina' : 'Parler à IAmina',",
    "      compact ? 'IAmina' : AuditedPageCopy.of(context).talk,",
    "dashboard chat label",
)
s = s.replace("      label: 'Parler à IAmina',", "      label: AuditedPageCopy.of(context).talk,")
for old, key in [
    ("'Vérification de la synchronisation'", "checking"),
    ("'Données à jour'", "upToDate"),
    ("'Données en attente de synchronisation'", "pending"),
    ("'Synchronisation en cours'", "syncing"),
    ("'Hors ligne · données conservées sur cet appareil'", "offline"),
    ("'Échec de synchronisation · appuyer pour réessayer'", "error"),
]:
    s = replace_once(s, old, f"AuditedPageCopy.of(context).sync('{key}')", f"sync {key}")
s = replace_once(s, "                '$r j',", "                '$r ${AuditedPageCopy.of(context).dayShort}',", "range day suffix")
write(path, s)

# Dashboard page heading.
path = "frontend/lib/features/dashboard/widgets/hero_section.dart"
s = read(path)
old = """    final now = DateTime.now();
    final greeting = now.hour < 12 ? 'Bonjour' : now.hour < 18 ? 'Bon après-midi' : 'Bonsoir';"""
new = """    final now = DateTime.now();
    final copy = AuditedPageCopy.of(context);"""
s = replace_once(s, old, new, "dashboard greeting setup")
old = """            final firstName = _HeroInsight._firstName();
            final salut = firstName.isNotEmpty ? '$greeting, $firstName.' : '$greeting !';"""
new = """            final firstName = _HeroInsight._firstName();
            final salut = copy.greeting(now.hour, firstName);"""
s = replace_once(s, old, new, "dashboard greeting")
old = """            logCount > 0
                ? 'Voici ce qu\\'IAmina a observé sur vos $range derniers jours.'
                : 'Chargez des données pour voir votre analyse IAmina.',"""
new = """            logCount > 0 ? copy.observation(range) : copy.emptyAnalysis,"""
s = replace_once(s, old, new, "dashboard observation")
write(path, s)

# Live hero.
path = "frontend/lib/features/dashboard/widgets/hero_live.dart"
s = read(path)
s = replace_once(
    s,
    "    final latest = logs.isNotEmpty ? logs.first : null;",
    "    final copy = AuditedPageCopy.of(context);\n    final latest = logs.isNotEmpty ? logs.first : null;",
    "live hero copy",
)
s = replace_once(
    s,
    "    final mealLabel = latest?.mealType?.isNotEmpty == true\n        ? latest!.mealType!\n        : null;",
    "    final rawMealLabel = latest?.mealType?.isNotEmpty == true\n        ? latest!.mealType!\n        : null;\n    final mealLabel = rawMealLabel == null ? null : copy.meal(rawMealLabel);",
    "meal localization",
)
s = replace_once(s, "                    const _HeroBadge(label: 'DERNIÈRE MESURE'),", "                    _HeroBadge(label: copy.latestReading),", "latest badge")
s = replace_once(
    s,
    "                      minutesAgo == 0\n                          ? 'à l\\'instant'\n                          : 'il y a $minutesAgo min',",
    "                      minutesAgo == 0 ? copy.justNow : copy.minutesAgo(minutesAgo),",
    "latest time",
)
write(path, s)

# Contextual target-range hero.
path = "frontend/lib/features/dashboard/widgets/hero_tir.dart"
s = read(path)
s = replace_once(
    s,
    "    final percentage = ClinicalEngine.calcTIR(logs, low, high);",
    "    final copy = AuditedPageCopy.of(context);\n    final percentage = ClinicalEngine.calcTIR(logs, low, high);",
    "target hero copy",
)
s = replace_once(s, "                _HeroBadge(label: 'MESURES DANS LA CIBLE · $range JOURS'),", "                _HeroBadge(label: copy.targetTitle(range)),", "target hero title")
s = replace_once(
    s,
    "                  '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',",
    "                  copy.targetCoverage(logs.length, daysWithData),",
    "target hero coverage",
)
s = replace_once(s, "                  'Repère général ≥ 70 % · votre cible personnelle peut être différente.',", "                  copy.targetReference,", "target hero reference")
s = replace_once(s, "                  label: 'Voir le journal',", "                  label: copy.viewJournal,", "target hero journal")
write(path, s)

# Main target-range KPI.
path = "frontend/lib/features/dashboard/widgets/kpi_tir_card.dart"
s = read(path)
s = replace_once(
    s,
    "    final tir = ClinicalEngine.calcTIR(logs, low, high);",
    "    final copy = AuditedPageCopy.of(context);\n    final tir = ClinicalEngine.calcTIR(logs, low, high);",
    "target card copy",
)
s = replace_once(s, "          const CardHead(title: 'Mesures dans la cible', meta: 'Repère 70–180'),", "          CardHead(title: copy.readingsInRange, meta: copy.rangeReference),", "target card head")
s = replace_once(
    s,
    "              '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',",
    "              copy.targetCoverage(logs.length, daysWithData),",
    "target card coverage",
)
s = s.replace("label: 'Dans la cible'", "label: copy.inRange")
s = s.replace("label: 'Élevé'", "label: copy.high")
s = s.replace("label: 'Bas'", "label: copy.low")
s = s.replace("label: 'Très élevé'", "label: copy.veryHigh")
s = replace_once(
    s,
    "            'Repère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.',",
    "            copy.targetExplanation,",
    "target card explanation",
)
write(path, s)

# Import landing page.
path = "frontend/lib/features/import/import_screen.dart"
s = read(path)
s = replace_once(
    s,
    "import '../../core/widgets/clinical_card.dart';\n",
    "import '../../core/widgets/clinical_card.dart';\nimport '../../l10n/audited_page_copy.dart';\n",
    "import screen copy import",
)
s = replace_once(s, "                  const Padding(\n                    padding: EdgeInsets.only(bottom: 16),\n                    child: Text(\n                      'Connexions directes',", "                  Padding(\n                    padding: const EdgeInsets.only(bottom: 16),\n                    child: Text(\n                      AuditedPageCopy.of(context).directConnections,", "direct connections")
s = replace_once(s, "                    subtitle:\n                        'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.',", "                    subtitle: AuditedPageCopy.of(context).dexcomDescription,", "dexcom copy")
s = replace_once(s, "                    badge: 'BIENTÔT',", "                    badge: AuditedPageCopy.of(context).soon,", "dexcom soon")
s = replace_once(s, "                    subtitle:\n                        'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.',", "                    subtitle: AuditedPageCopy.of(context).libreDescription,", "libre copy")
s = replace_once(s, "                    badge: 'BIENTÔT',", "                    badge: AuditedPageCopy.of(context).soon,", "libre soon")
old = """      child: const Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Importer',"""
new = """      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AuditedPageCopy.of(context).importTitle,"""
s = replace_once(s, old, new, "import top title")
s = replace_once(s, "                Text(\n                  'Connectez vos sources de données',", "                Text(\n                  AuditedPageCopy.of(context).importSubtitle,", "import subtitle")
s = replace_once(s, "      label: 'Ouvrir l’import de document',", "      label: AuditedPageCopy.of(context).openDocumentImport,", "pulper semantics")
s = replace_once(s, "                    const Text(\n                      'Pulper IAmina',", "                    const Text(\n                      'Pulper IAmina',", "pulper brand")
s = replace_once(s, "                      'PDF · Photo · Excel · Word — IAmina extrait tout automatiquement.',", "                      AuditedPageCopy.of(context).pulperDescription,", "pulper description")
s = s.replace("_PulperChip(label: 'Bilan labo')", "_PulperChip(label: AuditedPageCopy.of(context).labReport)")
s = s.replace("_PulperChip(label: 'Export CGM')", "_PulperChip(label: AuditedPageCopy.of(context).cgmExport)")
s = s.replace("_PulperChip(label: 'Ordonnance')", "_PulperChip(label: AuditedPageCopy.of(context).prescription)")
s = s.replace("_PulperChip(label: 'Photo')", "_PulperChip(label: AuditedPageCopy.of(context).photo)")
s = replace_once(s, "    child: const Text(\n      'Non disponible',", "    child: Text(\n      AuditedPageCopy.of(context).unavailable,", "unavailable")
write(path, s)

# Document picker initial state.
path = "frontend/lib/features/documents/document_import_screen.dart"
s = read(path)
s = replace_once(
    s,
    "import '../../core/theme/app_theme.dart';\n",
    "import '../../core/theme/app_theme.dart';\nimport '../../l10n/audited_page_copy.dart';\n",
    "document copy import",
)
s = replace_once(s, "          'Importer un document',", "          AuditedPageCopy.of(context).documentTitle,", "document title")
s = replace_once(
    s,
    "                'Importez n\\'importe quel document médical.\\nIAmina l\\'analyse et extrait les données automatiquement.',",
    "                AuditedPageCopy.of(context).documentIntro,",
    "document intro",
)
s = replace_once(s, "                  label: const Text('Choisir un document'),", "                  label: Text(AuditedPageCopy.of(context).chooseDocument),", "document chooser")
write(path, s)

# Profile residual labels only; existing primary fields already use AppLocalizations.
path = "frontend/lib/features/profile/profile_screen.dart"
s = read(path)
s = replace_once(
    s,
    "import '../../core/widgets/amina_text_field.dart';\n",
    "import '../../core/widgets/amina_text_field.dart';\nimport '../../l10n/audited_page_copy.dart';\n",
    "profile audited import",
)
s = replace_once(s, "Expanded(child: _buildTextField('Min', _targetLowController, l10n)),", "Expanded(child: _buildTextField(AuditedPageCopy.of(context).minimum, _targetLowController, l10n)),", "profile minimum")
s = replace_once(s, "Expanded(child: _buildTextField('Max', _targetHighController, l10n)),", "Expanded(child: _buildTextField(AuditedPageCopy.of(context).maximum, _targetHighController, l10n)),", "profile maximum")
s = s.replace("'Profil complet'", "AuditedPageCopy.of(context).profileComplete")
write(path, s)

# Permanent source contract.
test = ROOT / "frontend/test/p0_audited_page_localization_contract_test.dart"
test.write_text(
    """import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String read(String path) => File(path).readAsStringSync();

void main() {
  test('audited pages expose explicit FR EN AR product copy', () {
    final copy = read('lib/l10n/audited_page_copy.dart');
    for (final required in <String>[
      "'ar' => ar",
      'نظرة عامة',
      'البيانات محدّثة',
      'آخر قياس',
      'القياسات ضمن النطاق',
      'اربط مصادر بياناتك',
      'اتصالات مباشرة',
      'غير متاح',
      'استيراد مستند',
      'الملف مكتمل',
    ]) {
      expect(copy, contains(required), reason: 'Missing audited Arabic copy: $required');
    }
  });

  test('dashboard audited surfaces consume localized copy', () {
    final sources = [
      read('lib/features/dashboard/widgets/top_bar.dart'),
      read('lib/features/dashboard/widgets/hero_section.dart'),
      read('lib/features/dashboard/widgets/hero_live.dart'),
      read('lib/features/dashboard/widgets/hero_tir.dart'),
      read('lib/features/dashboard/widgets/kpi_tir_card.dart'),
    ].join('\n');
    expect(sources, contains('AuditedPageCopy.of(context)'));
    for (final forbidden in <String>[
      "detailed ? 'Accueil · Vue d\\'ensemble'",
      "? 'Bonjour'",
      "const _HeroBadge(label: 'DERNIÈRE MESURE')",
      "CardHead(title: 'Mesures dans la cible'",
    ]) {
      expect(sources, isNot(contains(forbidden)), reason: 'Hardcoded audited dashboard copy remains: $forbidden');
    }
  });

  test('import and profile audited surfaces consume localized copy', () {
    final importer = read('lib/features/import/import_screen.dart');
    final document = read('lib/features/documents/document_import_screen.dart');
    final profile = read('lib/features/profile/profile_screen.dart');
    for (final source in [importer, document, profile]) {
      expect(source, contains('audited_page_copy.dart'));
      expect(source, contains('AuditedPageCopy.of(context)'));
    }
    for (final forbidden in <String>[
      "child: const Text(\n      'Non disponible'",
      "label: const Text('Choisir un document')",
      "_buildTextField('Min'",
      "_buildTextField('Max'",
    ]) {
      expect('$importer\n$document\n$profile', isNot(contains(forbidden)), reason: 'Hardcoded audited page copy remains: $forbidden');
    }
  });
}
""",
    encoding="utf-8",
)

print("Audited-page Arabic coverage applied.")
