#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel: str, value: str) -> None:
    (ROOT / rel).write_text(value, encoding='utf-8')


def once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one occurrence, got {count}')
    return value.replace(old, new, 1)


# Shared dashboard import only. Do not format this large library file.
p = 'frontend/lib/features/dashboard/dashboard_screen.dart'
s = read(p)
s = once(s, "import '../../core/widgets/clinical_card.dart';\n", "import '../../core/widgets/clinical_card.dart';\nimport '../../l10n/audited_page_copy.dart';\n", 'dashboard import')
write(p, s)

p = 'frontend/lib/features/dashboard/widgets/top_bar.dart'
s = read(p)
s = once(s, "      detailed ? 'Accueil · Vue d\\'ensemble' : 'Vue d\\'ensemble',", "      detailed ? AuditedPageCopy.of(context).breadcrumb : AuditedPageCopy.of(context).overview,", 'breadcrumb')
s = once(s, "      compact ? 'IAmina' : 'Parler à IAmina',", "      compact ? 'IAmina' : AuditedPageCopy.of(context).talk,", 'talk label')
s = once(s, "      label: 'Parler à IAmina',", "      label: AuditedPageCopy.of(context).talk,", 'talk semantics')
for old, key in [
    ("'Vérification de la synchronisation'", 'checking'),
    ("'Données à jour'", 'upToDate'),
    ("'Données en attente de synchronisation'", 'pending'),
    ("'Synchronisation en cours'", 'syncing'),
    ("'Hors ligne · données conservées sur cet appareil'", 'offline'),
    ("'Échec de synchronisation · appuyer pour réessayer'", 'error'),
]:
    s = once(s, old, f"AuditedPageCopy.of(context).sync('{key}')", f'sync {key}')
s = once(s, "                '$r j',", "                '$r ${AuditedPageCopy.of(context).dayShort}',", 'range suffix')
write(p, s)

p = 'frontend/lib/features/dashboard/widgets/hero_section.dart'
s = read(p)
s = once(s, "    final now = DateTime.now();\n    final greeting = now.hour < 12 ? 'Bonjour' : now.hour < 18 ? 'Bon après-midi' : 'Bonsoir';", "    final now = DateTime.now();\n    final copy = AuditedPageCopy.of(context);", 'greeting setup')
s = once(s, "            final firstName = _HeroInsight._firstName();\n            final salut = firstName.isNotEmpty ? '$greeting, $firstName.' : '$greeting !';", "            final firstName = _HeroInsight._firstName();\n            final salut = copy.greeting(now.hour, firstName);", 'greeting')
s = once(s, "            logCount > 0\n                ? 'Voici ce qu\\'IAmina a observé sur vos $range derniers jours.'\n                : 'Chargez des données pour voir votre analyse IAmina.',", "            logCount > 0 ? copy.observation(range) : copy.emptyAnalysis,", 'observation')
write(p, s)

p = 'frontend/lib/features/dashboard/widgets/hero_live.dart'
s = read(p)
s = once(s, '    final latest = logs.isNotEmpty ? logs.first : null;', '    final copy = AuditedPageCopy.of(context);\n    final latest = logs.isNotEmpty ? logs.first : null;', 'live copy')
s = once(s, "    final mealLabel = latest?.mealType?.isNotEmpty == true\n        ? latest!.mealType!\n        : null;", "    final rawMealLabel = latest?.mealType?.isNotEmpty == true\n        ? latest!.mealType!\n        : null;\n    final mealLabel = rawMealLabel == null ? null : copy.meal(rawMealLabel);", 'meal')
s = once(s, "                    const _HeroBadge(label: 'DERNIÈRE MESURE'),", '                    _HeroBadge(label: copy.latestReading),', 'latest badge')
s = once(s, "                      minutesAgo == 0\n                          ? 'à l\\'instant'\n                          : 'il y a $minutesAgo min',", '                      minutesAgo == 0 ? copy.justNow : copy.minutesAgo(minutesAgo),', 'latest time')
write(p, s)

p = 'frontend/lib/features/dashboard/widgets/hero_tir.dart'
s = read(p)
s = once(s, '    final percentage = ClinicalEngine.calcTIR(logs, low, high);', '    final copy = AuditedPageCopy.of(context);\n    final percentage = ClinicalEngine.calcTIR(logs, low, high);', 'target hero copy')
s = once(s, "                _HeroBadge(label: 'MESURES DANS LA CIBLE · $range JOURS'),", '                _HeroBadge(label: copy.targetTitle(range)),', 'target title')
s = once(s, "                  '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',", '                  copy.targetCoverage(logs.length, daysWithData),', 'target coverage')
s = once(s, "                  'Repère général ≥ 70 % · votre cible personnelle peut être différente.',", '                  copy.targetReference,', 'target reference')
s = once(s, "                  label: 'Voir le journal',", '                  label: copy.viewJournal,', 'view journal')
write(p, s)

p = 'frontend/lib/features/dashboard/widgets/kpi_tir_card.dart'
s = read(p)
s = once(s, '    final tir = ClinicalEngine.calcTIR(logs, low, high);', '    final copy = AuditedPageCopy.of(context);\n    final tir = ClinicalEngine.calcTIR(logs, low, high);', 'target card copy')
s = once(s, "          const CardHead(title: 'Mesures dans la cible', meta: 'Repère 70–180'),", '          CardHead(title: copy.readingsInRange, meta: copy.rangeReference),', 'target card title')
s = once(s, "              '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''} · proportion de mesures, pas durée CGM',", '              copy.targetCoverage(logs.length, daysWithData),', 'target card coverage')
for old, new in [("label: 'Dans la cible'", 'label: copy.inRange'), ("label: 'Élevé'", 'label: copy.high'), ("label: 'Bas'", 'label: copy.low'), ("label: 'Très élevé'", 'label: copy.veryHigh')]:
    s = once(s, old, new, old)
s = once(s, "            'Repère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.',", '            copy.targetExplanation,', 'target explanation')
write(p, s)

p = 'frontend/lib/features/import/import_screen.dart'
s = read(p)
s = once(s, "import '../../core/widgets/clinical_card.dart';\n", "import '../../core/widgets/clinical_card.dart';\nimport '../../l10n/audited_page_copy.dart';\n", 'import copy import')
s = once(s, "                  const Padding(\n                    padding: EdgeInsets.only(bottom: 16),\n                    child: Text(\n                      'Connexions directes',", "                  Padding(\n                    padding: const EdgeInsets.only(bottom: 16),\n                    child: Text(\n                      AuditedPageCopy.of(context).directConnections,", 'direct connections')
s = once(s, "                    subtitle:\n                        'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.',", '                    subtitle: AuditedPageCopy.of(context).dexcomDescription,', 'dexcom')
s = once(s, "                    subtitle:\n                        'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.',", '                    subtitle: AuditedPageCopy.of(context).libreDescription,', 'libre')
badge = "                    badge: 'BIENTÔT',"
if s.count(badge) != 2:
    raise SystemExit(f'connector badges: expected two, got {s.count(badge)}')
s = s.replace(badge, '                    badge: AuditedPageCopy.of(context).soon,', 2)
s = once(s, "      child: const Row(\n        children: [\n          Expanded(\n            child: Column(\n              crossAxisAlignment: CrossAxisAlignment.start,\n              children: [\n                Text(\n                  'Importer',", "      child: Row(\n        children: [\n          Expanded(\n            child: Column(\n              crossAxisAlignment: CrossAxisAlignment.start,\n              children: [\n                Text(\n                  AuditedPageCopy.of(context).importTitle,", 'import title')
s = once(s, "                Text(\n                  'Connectez vos sources de données',", '                Text(\n                  AuditedPageCopy.of(context).importSubtitle,', 'import subtitle')
s = once(s, "      label: 'Ouvrir l’import de document',", '      label: AuditedPageCopy.of(context).openDocumentImport,', 'pulper semantics')
s = once(s, "                      'PDF · Photo · Excel · Word — IAmina extrait tout automatiquement.',", '                      AuditedPageCopy.of(context).pulperDescription,', 'pulper description')
for old, new in [("_PulperChip(label: 'Bilan labo')", '_PulperChip(label: AuditedPageCopy.of(context).labReport)'), ("_PulperChip(label: 'Export CGM')", '_PulperChip(label: AuditedPageCopy.of(context).cgmExport)'), ("_PulperChip(label: 'Ordonnance')", '_PulperChip(label: AuditedPageCopy.of(context).prescription)'), ("_PulperChip(label: 'Photo')", '_PulperChip(label: AuditedPageCopy.of(context).photo)')]:
    s = once(s, old, new, old)
s = once(s, '                    const Wrap(\n                      spacing: 6,', '                    Wrap(\n                      spacing: 6,', 'dynamic Pulper wrap')
s = once(s, "    child: const Text(\n      'Non disponible',", '    child: Text(\n      AuditedPageCopy.of(context).unavailable,', 'unavailable')
write(p, s)

p = 'frontend/lib/features/documents/document_import_screen.dart'
s = read(p)
s = once(s, "import '../../core/theme/app_theme.dart';\n", "import '../../core/theme/app_theme.dart';\nimport '../../l10n/audited_page_copy.dart';\n", 'document import')
s = once(s, "          'Importer un document',", '          AuditedPageCopy.of(context).documentTitle,', 'document title')
s = once(s, "                'Importez n\\'importe quel document médical.\\nIAmina l\\'analyse et extrait les données automatiquement.',", '                AuditedPageCopy.of(context).documentIntro,', 'document intro')
s = once(s, "                  label: const Text('Choisir un document'),", '                  label: Text(AuditedPageCopy.of(context).chooseDocument),', 'choose document')
write(p, s)

p = 'frontend/lib/features/profile/profile_screen.dart'
s = read(p)
s = once(s, "import '../../core/widgets/amina_text_field.dart';\n", "import '../../core/widgets/amina_text_field.dart';\nimport '../../l10n/audited_page_copy.dart';\n", 'profile import')
s = once(s, "Expanded(child: _buildTextField('Min', _targetLowController, l10n)),", 'Expanded(child: _buildTextField(AuditedPageCopy.of(context).minimum, _targetLowController, l10n)),', 'minimum')
s = once(s, "Expanded(child: _buildTextField('Max', _targetHighController, l10n)),", 'Expanded(child: _buildTextField(AuditedPageCopy.of(context).maximum, _targetHighController, l10n)),', 'maximum')
s = once(s, "    final label = pct >= 100 ? 'Profil complet ✓' : 'Profil complété à $pct%';", '    final copy = AuditedPageCopy.of(context);\n    final label = copy.profileCompletionLabel(pct);', 'profile label')
s = once(s, "            const Text(\n              'Complétez votre profil pour des analyses plus précises.',\n              style: TextStyle(", '            Text(\n              copy.profileCompletionPrompt,\n              style: const TextStyle(', 'profile prompt')
write(p, s)

print('Clean audited-page localization migration applied.')
