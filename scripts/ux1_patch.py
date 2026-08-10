from pathlib import Path
import json
import re

ROOT = Path('frontend')


def replace(path, old, new, count=1):
    p = ROOT / path
    text = p.read_text()
    found = text.count(old)
    if found != count:
        raise SystemExit(
            f'{path}: expected {count} occurrence(s), found {found}: {old[:100]!r}'
        )
    p.write_text(text.replace(old, new, count))


def add_arb(path, additions):
    p = ROOT / 'lib/l10n' / path
    text = p.read_text().rstrip()
    existing = json.loads(text)
    overlap = set(additions).intersection(existing)
    if overlap:
        raise SystemExit(f'{path}: keys already exist: {sorted(overlap)}')
    body = text[:-1].rstrip()
    lines = [
        f'  {json.dumps(key, ensure_ascii=False)}: {json.dumps(value, ensure_ascii=False)}'
        for key, value in additions.items()
    ]
    p.write_text(body + ',\n' + ',\n'.join(lines) + '\n}\n')


common_meta = {
    '@dashboardTrendPer30Minutes': {
        'placeholders': {'value': {'type': 'String'}}
    },
    '@dashboardRapidInsulin': {'placeholders': {'dose': {'type': 'String'}}},
    '@dashboardInsightStrong': {
        'placeholders': {
            'percentage': {'type': 'int'},
            'range': {'type': 'int'},
        }
    },
    '@dashboardInsightProgress': {
        'placeholders': {
            'percentage': {'type': 'int'},
            'mean': {'type': 'int'},
        }
    },
    '@dashboardInsightNeedsFocus': {
        'placeholders': {'range': {'type': 'int'}}
    },
    '@dashboardInsightSummary': {
        'placeholders': {
            'discoveries': {'type': 'int'},
            'stability': {'type': 'String'},
            'measurements': {'type': 'int'},
        }
    },
    '@dashboardGmiCoverage': {
        'placeholders': {
            'mean': {'type': 'String'},
            'measurements': {'type': 'int'},
            'days': {'type': 'int'},
        }
    },
    '@dashboardMeasurementCoverage': {
        'placeholders': {
            'measurements': {'type': 'int'},
            'days': {'type': 'int'},
        }
    },
    '@dashboardHoursShort': {'placeholders': {'hours': {'type': 'int'}}},
    '@dashboardMealEvents': {'placeholders': {'count': {'type': 'int'}}},
    '@dashboardInsulinEvents': {'placeholders': {'count': {'type': 'int'}}},
    '@dashboardAgpSufficiency': {'placeholders': {'days': {'type': 'int'}}},
    '@dashboardDiscoveryCount': {'placeholders': {'count': {'type': 'int'}}},
}

fr = {
    'dashboardTrendPer30Minutes': '{value} / 30 min',
    'dashboardRapidInsulin': '{dose} u rapide',
    'dashboardIntelligenceBadge': 'INTELLIGENCE IAMINA',
    'dashboardInsightStart': 'Commencez à enregistrer pour découvrir vos tendances.',
    'dashboardInsightStrong': 'Excellent contrôle — {percentage}% en cible sur {range} jours.',
    'dashboardInsightProgress': 'Votre équilibre progresse — {percentage}% en cible, moyenne {mean} mg/dL.',
    'dashboardInsightNeedsFocus': "IAmina a repéré des axes d'amélioration sur vos {range} derniers jours.",
    'dashboardInsightFirstMeasurement': "Ajoutez votre première mesure pour activer l'intelligence IAmina.",
    'dashboardVariabilityStable': 'variabilité maîtrisée',
    'dashboardVariabilityWatch': 'variabilité à surveiller',
    'dashboardInsightSummary': 'Découvertes : {discoveries} · {stability} · {measurements} mesures.',
    'dashboardViewDiscoveries': 'Voir mes découvertes',
    'dashboardGmiEstimated': 'GMI estimée',
    'dashboardGmiCoverage': 'Moyenne {mean} mg/dL · {measurements} mesures · {days} jours de données',
    'dashboardGmiLimitedCoverage': 'Couverture limitée : moins de 14 jours ou 50 mesures. Résultat indicatif.',
    'dashboardGmiCalculated': 'Calculée à partir de la moyenne glycémique disponible.',
    'dashboardGmiDisclaimer': "Cette estimation ne remplace pas une HbA1c de laboratoire.",
    'dashboardInsufficientData': 'Données insuffisantes',
    'dashboardCvTitle': 'Variabilité (CV)',
    'dashboardCvReferenceShort': 'Repère général <36 %',
    'dashboardMeasurementCoverage': '{measurements} mesures sur {days} jours',
    'dashboardCvBelowReference': 'Sous le repère général',
    'dashboardCvAboveReference': 'Au-dessus du repère général',
    'dashboardCvReferenceExplanation': 'Repère général CV <36 %. Votre objectif personnel peut être différent.',
    'dashboardAgpTitle': 'Profil glycémique ambulatoire (AGP)',
    'dashboardLive': 'en direct',
    'dashboardAll': 'Tout',
    'dashboardHoursShort': '{hours} h',
    'dashboardBeforeBed': 'Avant le coucher',
    'dashboardAgpInsufficient': 'Données insuffisantes pour le profil AGP',
    'dashboardMedian': 'Médiane',
    'dashboardTargetLegend': 'Cible 70–180',
    'dashboardMealEvents': 'Repas : {count}',
    'dashboardInsulinEvents': 'Insuline : {count}',
    'dashboardAgpSufficiency': "AGP basé sur {days} jours · L'ADA recommande ≥ 14 jours pour une analyse fiable.",
    'dashboardKeyEvents': 'Événements clés',
    'dashboardInTarget': 'En cible',
    'dashboardHyperglycemia': 'Hyperglycémies',
    'dashboardHypoglycemia': 'Hypoglycémies',
    'dashboardTotalMeasurements': 'Total mesures',
    'dashboardDiscoveriesTitle': 'DÉCOUVERTES IAMINA',
    'dashboardWaitingForData': 'En attente de données…',
    'dashboardDiscoveryCount': 'Découvertes : {count}',
    'dashboardViewAll': 'Voir tout →',
    'dashboardAiDegraded': 'Analyse IA temporairement limitée · Les données sont bien enregistrées.',
    'dashboardAnalyzingPatterns': 'IAmina analyse vos données pour identifier des schémas…',
    'dashboardMeasurement': 'Mesure',
}

en = {
    'dashboardTrendPer30Minutes': '{value} / 30 min',
    'dashboardRapidInsulin': '{dose} u rapid-acting',
    'dashboardIntelligenceBadge': 'IAMINA INTELLIGENCE',
    'dashboardInsightStart': 'Start logging to discover your trends.',
    'dashboardInsightStrong': 'Excellent control — {percentage}% in range over {range} days.',
    'dashboardInsightProgress': 'Your balance is improving — {percentage}% in range, average {mean} mg/dL.',
    'dashboardInsightNeedsFocus': 'IAmina identified areas to improve over your last {range} days.',
    'dashboardInsightFirstMeasurement': 'Add your first reading to activate IAmina insights.',
    'dashboardVariabilityStable': 'variability under control',
    'dashboardVariabilityWatch': 'variability to watch',
    'dashboardInsightSummary': 'Discoveries: {discoveries} · {stability} · {measurements} readings.',
    'dashboardViewDiscoveries': 'View my discoveries',
    'dashboardGmiEstimated': 'Estimated GMI',
    'dashboardGmiCoverage': 'Average {mean} mg/dL · {measurements} readings · {days} days of data',
    'dashboardGmiLimitedCoverage': 'Limited coverage: fewer than 14 days or 50 readings. Result is indicative.',
    'dashboardGmiCalculated': 'Calculated from the available average glucose.',
    'dashboardGmiDisclaimer': 'This estimate does not replace a laboratory HbA1c.',
    'dashboardInsufficientData': 'Insufficient data',
    'dashboardCvTitle': 'Variability (CV)',
    'dashboardCvReferenceShort': 'General reference <36%',
    'dashboardMeasurementCoverage': '{measurements} readings over {days} days',
    'dashboardCvBelowReference': 'Below the general reference',
    'dashboardCvAboveReference': 'Above the general reference',
    'dashboardCvReferenceExplanation': 'General reference CV <36%. Your personal target may differ.',
    'dashboardAgpTitle': 'Ambulatory glucose profile (AGP)',
    'dashboardLive': 'live',
    'dashboardAll': 'All',
    'dashboardHoursShort': '{hours}h',
    'dashboardBeforeBed': 'Before bed',
    'dashboardAgpInsufficient': 'Insufficient data for the AGP profile',
    'dashboardMedian': 'Median',
    'dashboardTargetLegend': 'Target 70–180',
    'dashboardMealEvents': 'Meals: {count}',
    'dashboardInsulinEvents': 'Insulin: {count}',
    'dashboardAgpSufficiency': 'AGP based on {days} days · ADA recommends ≥ 14 days for a reliable analysis.',
    'dashboardKeyEvents': 'Key events',
    'dashboardInTarget': 'In target',
    'dashboardHyperglycemia': 'High-glucose events',
    'dashboardHypoglycemia': 'Low-glucose events',
    'dashboardTotalMeasurements': 'Total readings',
    'dashboardDiscoveriesTitle': 'IAMINA DISCOVERIES',
    'dashboardWaitingForData': 'Waiting for data…',
    'dashboardDiscoveryCount': 'Discoveries: {count}',
    'dashboardViewAll': 'View all →',
    'dashboardAiDegraded': 'AI analysis is temporarily limited · Your data is still recorded.',
    'dashboardAnalyzingPatterns': 'IAmina is analyzing your data to identify patterns…',
    'dashboardMeasurement': 'Reading',
}

ar = {
    'dashboardTrendPer30Minutes': '{value} / 30 دقيقة',
    'dashboardRapidInsulin': '{dose} وحدة سريع المفعول',
    'dashboardIntelligenceBadge': 'ذكاء IAmina',
    'dashboardInsightStart': 'ابدأ بتسجيل القياسات لاكتشاف اتجاهاتك.',
    'dashboardInsightStrong': 'تحكم ممتاز — {percentage}٪ ضمن النطاق خلال {range} يومًا.',
    'dashboardInsightProgress': 'يتحسن توازن سكر الدم لديك — {percentage}٪ ضمن النطاق، بمتوسط {mean} mg/dL.',
    'dashboardInsightNeedsFocus': 'رصدت IAmina نقاطًا للتحسين خلال آخر {range} يومًا.',
    'dashboardInsightFirstMeasurement': 'أضف أول قياس لتفعيل تحليلات IAmina.',
    'dashboardVariabilityStable': 'تباين مستقر',
    'dashboardVariabilityWatch': 'تباين يحتاج إلى متابعة',
    'dashboardInsightSummary': 'الاكتشافات: {discoveries} · {stability} · {measurements} قياسًا.',
    'dashboardViewDiscoveries': 'عرض اكتشافاتي',
    'dashboardGmiEstimated': 'مؤشر GMI التقديري',
    'dashboardGmiCoverage': 'المتوسط {mean} mg/dL · {measurements} قياسًا · بيانات {days} أيام',
    'dashboardGmiLimitedCoverage': 'تغطية محدودة: أقل من 14 يومًا أو 50 قياسًا. النتيجة إرشادية.',
    'dashboardGmiCalculated': 'يُحسب من متوسط سكر الدم المتاح.',
    'dashboardGmiDisclaimer': 'لا يغني هذا التقدير عن فحص HbA1c المخبري.',
    'dashboardInsufficientData': 'بيانات غير كافية',
    'dashboardCvTitle': 'التباين (CV)',
    'dashboardCvReferenceShort': 'مرجع عام <36٪',
    'dashboardMeasurementCoverage': '{measurements} قياسًا خلال {days} أيام',
    'dashboardCvBelowReference': 'أقل من المرجع العام',
    'dashboardCvAboveReference': 'أعلى من المرجع العام',
    'dashboardCvReferenceExplanation': 'المرجع العام لـ CV أقل من 36٪. قد يختلف هدفك الشخصي.',
    'dashboardAgpTitle': 'ملف الغلوكوز المتنقل (AGP)',
    'dashboardLive': 'مباشر',
    'dashboardAll': 'الكل',
    'dashboardHoursShort': '{hours} س',
    'dashboardBeforeBed': 'قبل النوم',
    'dashboardAgpInsufficient': 'لا توجد بيانات كافية لملف AGP',
    'dashboardMedian': 'الوسيط',
    'dashboardTargetLegend': 'النطاق المستهدف 70–180',
    'dashboardMealEvents': 'الوجبات: {count}',
    'dashboardInsulinEvents': 'الإنسولين: {count}',
    'dashboardAgpSufficiency': 'يستند AGP إلى {days} أيام · توصي ADA ببيانات 14 يومًا على الأقل لتحليل موثوق.',
    'dashboardKeyEvents': 'الأحداث الرئيسية',
    'dashboardInTarget': 'ضمن الهدف',
    'dashboardHyperglycemia': 'حالات ارتفاع السكر',
    'dashboardHypoglycemia': 'حالات انخفاض السكر',
    'dashboardTotalMeasurements': 'إجمالي القياسات',
    'dashboardDiscoveriesTitle': 'اكتشافات IAmina',
    'dashboardWaitingForData': 'في انتظار البيانات…',
    'dashboardDiscoveryCount': 'الاكتشافات: {count}',
    'dashboardViewAll': 'عرض الكل ←',
    'dashboardAiDegraded': 'تحليل الذكاء الاصطناعي محدود مؤقتًا · بياناتك محفوظة.',
    'dashboardAnalyzingPatterns': 'تحلل IAmina بياناتك لتحديد الأنماط…',
    'dashboardMeasurement': 'قياس',
}

for translations in (fr, en, ar):
    translations.update(common_meta)

add_arb('app_fr.arb', fr)
add_arb('app_en.arb', en)
add_arb('app_ar.arb', ar)

# Canonical/legacy meal IDs -> localized patient-facing labels.
p = ROOT / 'lib/l10n/audited_page_copy.dart'
text = p.read_text()
pattern = re.compile(
    r"  String meal\(String\? value\) \{.*?\n  \}\n\n  String targetTitle",
    re.S,
)
replacement = '''  String meal(String? value) {
    if (value == null || value.trim().isEmpty) return '';
    final normalized = value.trim().toLowerCase();
    if ({'breakfast', 'petit-déjeuner', 'petit dejeuner'}.contains(normalized)) {
      return l10n.journalMealBreakfast;
    }
    if ({'lunch', 'déjeuner', 'dejeuner'}.contains(normalized)) {
      return l10n.journalMealLunch;
    }
    if ({'dinner', 'dîner', 'diner'}.contains(normalized)) {
      return l10n.journalMealDinner;
    }
    if ({'snack', 'en-cas', 'encas', 'collation'}.contains(normalized)) {
      return l10n.journalMealSnack;
    }
    if (normalized == 'suhoor') return l10n.journalMealSuhoor;
    if (normalized == 'iftar') return l10n.journalMealIftar;
    if ({'other', 'autre'}.contains(normalized)) return l10n.journalMealOther;
    if ({'fasting', 'à jeun', 'a jeun'}.contains(normalized)) {
      return l10n.journalContextFasting;
    }
    if ({'pre_meal', 'pre-meal', 'avant repas'}.contains(normalized)) {
      return l10n.journalContextPreMeal;
    }
    if ({
      'post_meal',
      'post-meal',
      'post-prandial',
      'après repas',
      'apres repas',
    }.contains(normalized)) {
      return l10n.afterMeal;
    }
    return value;
  }

  String targetTitle'''
text2, n = pattern.subn(replacement, text)
if n != 1:
    raise SystemExit(f'audited_page_copy meal block replacements: {n}')
p.write_text(text2)

# Hero live.
replace(
    'lib/features/dashboard/widgets/hero_live.dart',
    '  String? _trend() {',
    '  String? _trend(BuildContext context) {',
)
replace(
    'lib/features/dashboard/widgets/hero_live.dart',
    "    return '${per30 >= 0 ? '+' : ''}$per30 / 30 min';",
    "    final signed = '${per30 >= 0 ? '+' : ''}$per30';\n"
    "    return AuditedPageCopy.of(context).l10n.dashboardTrendPer30Minutes(signed);",
)
replace(
    'lib/features/dashboard/widgets/hero_live.dart',
    "        ? '${latest.insulinUnits!.toStringAsFixed(latest.insulinUnits! == latest.insulinUnits!.truncateToDouble() ? 0 : 1)}u rapide'\n"
    "        : null;\n"
    "    final trend = _trend();",
    "        ? AuditedPageCopy.of(context).l10n.dashboardRapidInsulin(\n"
    "            '\\u2066${latest.insulinUnits!.toStringAsFixed(latest.insulinUnits! == latest.insulinUnits!.truncateToDouble() ? 0 : 1)}\\u2069',\n"
    "          )\n"
    "        : null;\n"
    "    final trend = _trend(context);",
)

# Hero insight is small enough to rewrite deliberately.
p = ROOT / 'lib/features/dashboard/widgets/hero_insight.dart'
p.write_text(r'''part of '../dashboard_screen.dart';

// ── Hero Insight (matin / défaut) ─────────────────────────────────────────────

class _HeroInsight extends StatelessWidget {
  final List<LogEntryData> logs;
  final int range;
  const _HeroInsight({required this.logs, required this.range});

  /// Prénom de l'utilisateur connecté, ou chaîne vide pour les comptes anonymes.
  static String _firstName() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || user.isAnonymous) return '';
    final name = user.displayName ?? user.email ?? '';
    if (name.isEmpty) return '';
    return name
        .split(RegExp(r'[\s@.]'))
        .firstWhere((p) => p.isNotEmpty, orElse: () => '');
  }

  String _headline(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightStart;
    final tir = ClinicalEngine.calcTIR(logs, 70, 180);
    final mean = ClinicalEngine.calcMean(logs);
    if (tir >= 80) return l10n.dashboardInsightStrong(tir.round(), range);
    if (tir >= 60) {
      return l10n.dashboardInsightProgress(tir.round(), mean.round());
    }
    return l10n.dashboardInsightNeedsFocus(range);
  }

  String _subtitle(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightFirstMeasurement;
    final cv = ClinicalEngine.calcCV(logs);
    final discoveries = math.min(logs.length ~/ 20 + 1, 5);
    final stability = cv < 36
        ? l10n.dashboardVariabilityStable
        : l10n.dashboardVariabilityWatch;
    return l10n.dashboardInsightSummary(discoveries, stability, logs.length);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(decoration: AminaTheme.heroCardDecoration()),
          ),
          PositionedDirectional(
            top: -50,
            end: -50,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    Colors.white.withValues(alpha: 0.14),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          PositionedDirectional(
            end: -10,
            bottom: 4,
            child: ShaderMask(
              shaderCallback: (rect) => const LinearGradient(
                colors: [Colors.transparent, Colors.white, Colors.transparent],
                stops: [0.0, 0.5, 1.0],
              ).createShader(rect),
              child: _AnimatedEcg(
                color: Colors.white.withValues(alpha: 0.22),
                width: 260,
                height: 60,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroBadge(label: l10n.dashboardIntelligenceBadge),
                const SizedBox(height: 20),
                Text(
                  _headline(context),
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                    letterSpacing: -0.4,
                    shadows: [
                      Shadow(
                        color: Colors.black.withValues(alpha: 0.2),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  _subtitle(context),
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.78),
                    fontSize: 13,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 20),
                _HeroFilledBtn(
                  label: l10n.dashboardViewDiscoveries,
                  onTap: () => GoRouter.of(context).go('/summary'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
''')

# GMI card.
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    '  Widget build(BuildContext context) {\n    final gmi =',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final gmi =',
)
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    "          CardHead(title: 'GMI estimée', meta: '$range j'),",
    "          CardHead(\n"
    "            title: l10n.dashboardGmiEstimated,\n"
    "            meta: '$range ${l10n.dayShort}',\n"
    "          ),",
)
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    "              'Moyenne ${mean.toStringAsFixed(0)} mg/dL · ${logs.length} mesures · $daysCount jour${daysCount > 1 ? 's' : ''} de données',",
    '              l10n.dashboardGmiCoverage(\n'
    '                mean.toStringAsFixed(0),\n'
    '                logs.length,\n'
    '                daysCount,\n'
    '              ),',
)
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    "                          ? 'Couverture limitée : moins de 14 jours ou 50 mesures. Résultat indicatif.'\n"
    "                          : 'Calculée à partir de la moyenne glycémique disponible.',",
    '                          ? l10n.dashboardGmiLimitedCoverage\n'
    '                          : l10n.dashboardGmiCalculated,',
)
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    "              'Cette estimation ne remplace pas une HbA1c de laboratoire.',",
    '              l10n.dashboardGmiDisclaimer,',
)
replace(
    'lib/features/dashboard/widgets/kpi_gmi_card.dart',
    "                  'Données insuffisantes',",
    '                  l10n.dashboardInsufficientData,',
)

# CV card.
replace(
    'lib/features/dashboard/widgets/kpi_cv_card.dart',
    '  Widget build(BuildContext context) {\n    final cv =',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final cv =',
)
replace(
    'lib/features/dashboard/widgets/kpi_cv_card.dart',
    "          const CardHead(\n"
    "            title: 'Variabilité (CV)',\n"
    "            meta: 'Repère général <36 %',\n"
    "          ),",
    '          CardHead(\n'
    '            title: l10n.dashboardCvTitle,\n'
    '            meta: l10n.dashboardCvReferenceShort,\n'
    '          ),',
)
replace(
    'lib/features/dashboard/widgets/kpi_cv_card.dart',
    "              '${logs.length} mesures sur $daysWithData jour${daysWithData > 1 ? 's' : ''}',",
    '              l10n.dashboardMeasurementCoverage(\n'
    '                logs.length,\n'
    '                daysWithData,\n'
    '              ),',
)
replace(
    'lib/features/dashboard/widgets/kpi_cv_card.dart',
    "                      cv == 0\n"
    "                          ? 'Données insuffisantes'\n"
    "                          : isBelowGeneralReference\n"
    "                          ? 'Sous le repère général'\n"
    "                          : 'Au-dessus du repère général',",
    '                      cv == 0\n'
    '                          ? l10n.dashboardInsufficientData\n'
    '                          : isBelowGeneralReference\n'
    '                          ? l10n.dashboardCvBelowReference\n'
    '                          : l10n.dashboardCvAboveReference,',
)
replace(
    'lib/features/dashboard/widgets/kpi_cv_card.dart',
    "                      'Repère général CV <36 %. Votre objectif personnel peut être différent.',",
    '                      l10n.dashboardCvReferenceExplanation,',
)

# Chart section.
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    '  Widget build(BuildContext context) {\n    return Container(',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    return Container(',
    count=1,
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "            'AGP basé sur $daySpan jour${daySpan > 1 ? 's' : ''} · '\n"
    "            'L\\'ADA recommande ≥ 14 jours pour une analyse fiable.',",
    '            l10n.dashboardAgpSufficiency(daySpan),',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    '  Widget build(BuildContext context) {\n    final hypo',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final hypo',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "        const CardHead(title: 'Événements clés'),",
    '        CardHead(title: l10n.dashboardKeyEvents),',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "label: 'En cible'",
    'label: l10n.dashboardInTarget',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "label: 'Hyperglycémies'",
    'label: l10n.dashboardHyperglycemia',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "label: 'Hypoglycémies'",
    'label: l10n.dashboardHypoglycemia',
)
replace(
    'lib/features/dashboard/widgets/chart_section.dart',
    "Text('Total mesures', style:",
    'Text(l10n.dashboardTotalMeasurements, style:',
)

# Standalone AGP/glucose chart.
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "import '../../../data/drift/database.dart';\nimport 'agp_chart.dart';",
    "import '../../../data/drift/database.dart';\n"
    "import '../../../l10n/audited_page_copy.dart';\n"
    "import 'agp_chart.dart';",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    '  Widget build(BuildContext context) {\n    final logs = _filteredLogs;',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final logs = _filteredLogs;',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "CardHead(title: 'Profil glycémique ambulatoire', meta: widget.unit)",
    'CardHead(title: l10n.dashboardAgpTitle, meta: widget.unit)',
    count=2,
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "const Text('Aucune donnée', style: TextStyle(color: AminaTheme.ink400, fontSize: 13))",
    'Text(\n'
    '              l10n.noData,\n'
    '              style: const TextStyle(color: AminaTheme.ink400, fontSize: 13),\n'
    '            )',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "const Text('en direct', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AminaTheme.goodFg))",
    'Text(\n'
    '                        l10n.dashboardLive,\n'
    '                        style: const TextStyle(\n'
    '                          fontSize: 10,\n'
    '                          fontWeight: FontWeight.w600,\n'
    '                          color: AminaTheme.goodFg,\n'
    '                        ),\n'
    '                      )',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_TimeChip(label: 'Tout', value: 0",
    '_TimeChip(label: l10n.dashboardAll, value: 0',
)
for hours in (24, 12, 6, 3):
    replace(
        'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
        f"_TimeChip(label: '{hours}h',  value: {hours}",
        f'_TimeChip(label: l10n.dashboardHoursShort({hours}),  value: {hours}',
    )
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_MealChip(label: 'Tous',             value: null",
    '_MealChip(label: l10n.dashboardAll,             value: null',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_MealChip(label: 'À jeun',           value: 'À jeun'",
    "_MealChip(label: l10n.journalContextFasting,           value: 'À jeun'",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_MealChip(label: 'Post-prandial',    value: 'Post-prandial'",
    "_MealChip(label: l10n.journalContextPostMeal,    value: 'Post-prandial'",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_MealChip(label: 'Avant le coucher', value: 'Avant le coucher'",
    "_MealChip(label: l10n.dashboardBeforeBed, value: 'Avant le coucher'",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "_MealChip(label: 'En-cas',           value: 'En-cas'",
    "_MealChip(label: l10n.journalMealSnack,           value: 'En-cas'",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "child: Center(child: Text('Données insuffisantes pour le profil AGP', style: TextStyle(fontSize: 12, color: AminaTheme.ink400))),",
    'child: Center(\n'
    '                child: Text(\n'
    '                  l10n.dashboardAgpInsufficient,\n'
    '                  style: const TextStyle(\n'
    '                    fontSize: 12,\n'
    '                    color: AminaTheme.ink400,\n'
    '                  ),\n'
    '                ),\n'
    '              ),',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "          const Padding(\n"
    "            padding: EdgeInsets.fromLTRB(16, 8, 16, 16),\n"
    "            child: Wrap(\n"
    "              spacing: 16, runSpacing: 6,\n"
    "              children: [\n"
    "                _LegendItem(color: Color(0xFF1A3A2E), label: 'Médiane'),\n"
    "                _LegendItem(color: Color(0xFF3CC3A0), label: '25–75%', opacity: 0.5),\n"
    "                _LegendItem(color: Color(0xFF3CC3A0), label: '5–95%',  opacity: 0.2),\n"
    "                _LegendItem(color: Color(0xFFE4A85B), label: 'Cible 70–180', dashed: true),\n"
    "              ],\n"
    "            ),\n"
    "          ),",
    "          Padding(\n"
    "            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),\n"
    "            child: Wrap(\n"
    "              spacing: 16,\n"
    "              runSpacing: 6,\n"
    "              children: [\n"
    "                _LegendItem(\n"
    "                  color: const Color(0xFF1A3A2E),\n"
    "                  label: l10n.dashboardMedian,\n"
    "                ),\n"
    "                const _LegendItem(\n"
    "                  color: Color(0xFF3CC3A0),\n"
    "                  label: '25–75%',\n"
    "                  opacity: 0.5,\n"
    "                ),\n"
    "                const _LegendItem(\n"
    "                  color: Color(0xFF3CC3A0),\n"
    "                  label: '5–95%',\n"
    "                  opacity: 0.2,\n"
    "                ),\n"
    "                _LegendItem(\n"
    "                  color: const Color(0xFFE4A85B),\n"
    "                  label: l10n.dashboardTargetLegend,\n"
    "                  dashed: true,\n"
    "                ),\n"
    "              ],\n"
    "            ),\n"
    "          ),",
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    '  Widget build(BuildContext context) {\n    final mealCount',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final mealCount',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "Text('$mealCount repas', style: const TextStyle(fontSize: 11, color: AminaTheme.ink500))",
    'Text(\n'
    '            l10n.dashboardMealEvents(mealCount),\n'
    '            style: const TextStyle(fontSize: 11, color: AminaTheme.ink500),\n'
    '          )',
)
replace(
    'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
    "Text('$insulinCount insuline', style: const TextStyle(fontSize: 11, color: AminaTheme.ink500))",
    'Text(\n'
    '            l10n.dashboardInsulinEvents(insulinCount),\n'
    '            style: const TextStyle(fontSize: 11, color: AminaTheme.ink500),\n'
    '          )',
)

# Insights section.
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    '  Widget build(BuildContext context) {\n    if (logs.length < 3)',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    if (logs.length < 3)',
)
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    "const Text('DÉCOUVERTES IAMINA', style:",
    'Text(l10n.dashboardDiscoveriesTitle, style: const',
)
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    "      discoveries == 0\n"
    "          ? 'En attente de données…'\n"
    "          : discoveries == 1\n"
    "              ? '1 découverte'\n"
    "              : '$discoveries découvertes',",
    '      discoveries == 0\n'
    '          ? l10n.dashboardWaitingForData\n'
    '          : l10n.dashboardDiscoveryCount(discoveries),',
)
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    "child: const Text('Voir tout →', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal600))",
    'child: Text(\n'
    '              l10n.dashboardViewAll,\n'
    '              style: const TextStyle(\n'
    '                fontSize: 12,\n'
    '                fontWeight: FontWeight.w600,\n'
    '                color: AminaTheme.teal600,\n'
    '              ),\n'
    '            )',
)
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    "            child: const Row(children: [\n"
    "              Icon(Icons.cloud_off_outlined, size: 14, color: Color(0xFFE65100)),\n"
    "              SizedBox(width: 8),\n"
    "              Expanded(\n"
    "                child: Text(\n"
    "                  'Analyse IA temporairement limitée · Les données sont bien enregistrées.',\n"
    "                  style: TextStyle(fontSize: 11, color: Color(0xFF5D2E00), height: 1.4),\n"
    "                ),\n"
    "              ),\n"
    "            ]),",
    "            child: Row(children: [\n"
    "              const Icon(\n"
    "                Icons.cloud_off_outlined,\n"
    "                size: 14,\n"
    "                color: Color(0xFFE65100),\n"
    "              ),\n"
    "              const SizedBox(width: 8),\n"
    "              Expanded(\n"
    "                child: Text(\n"
    "                  l10n.dashboardAiDegraded,\n"
    "                  style: const TextStyle(\n"
    "                    fontSize: 11,\n"
    "                    color: Color(0xFF5D2E00),\n"
    "                    height: 1.4,\n"
    "                  ),\n"
    "                ),\n"
    "              ),\n"
    "            ]),",
)
replace(
    'lib/features/dashboard/widgets/insights_section.dart',
    "                'IAmina analyse tes données pour identifier des schémas…',",
    '                l10n.dashboardAnalyzingPatterns,',
)

# Recent entries.
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    '  Widget build(BuildContext context) {\n    final recent =',
    '  Widget build(BuildContext context) {\n'
    '    final l10n = AuditedPageCopy.of(context).l10n;\n'
    '    final recent =',
    count=1,
)
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    "const Expanded(child: CardHead(title: 'Journal · Aujourd\\'hui'))",
    "Expanded(\n"
    "            child: CardHead(title: '${l10n.navJournal} · ${l10n.journalToday}'),\n"
    "          )",
)
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    "child: const Text('Voir tout →', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal600))",
    'child: Text(\n'
    '              l10n.dashboardViewAll,\n'
    '              style: const TextStyle(\n'
    '                fontSize: 12,\n'
    '                fontWeight: FontWeight.w600,\n'
    '                color: AminaTheme.teal600,\n'
    '              ),\n'
    '            )',
)
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    "    final meal = log.mealType ?? '';",
    "    final rawMeal = log.mealType ?? '';\n"
    "    final copy = AuditedPageCopy.of(context);\n"
    "    final meal = copy.meal(rawMeal);",
)
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    "Text(meal.isNotEmpty ? meal : 'Mesure',",
    'Text(meal.isNotEmpty ? meal : copy.l10n.dashboardMeasurement,',
)
replace(
    'lib/features/dashboard/widgets/recent_entries.dart',
    'Center(child: Text(_mealEmoji(meal),',
    'Center(child: Text(_mealEmoji(rawMeal),',
)
p = ROOT / 'lib/features/dashboard/widgets/recent_entries.dart'
text = p.read_text()
pattern = re.compile(r"  String _mealEmoji\(String type\) \{.*?\n  \}\n\}", re.S)
replacement = '''  String _mealEmoji(String type) {
    return switch (type.trim().toLowerCase()) {
      'breakfast' || 'petit-déjeuner' || 'petit dejeuner' => '🥐',
      'lunch' || 'déjeuner' || 'dejeuner' => '🥗',
      'dinner' || 'dîner' || 'diner' => '🍽️',
      'snack' || 'en-cas' || 'encas' || 'collation' => '🍎',
      'fasting' || 'à jeun' || 'a jeun' => '☕',
      _ => '💧',
    };
  }
}'''
text2, n = pattern.subn(replacement, text)
if n != 1:
    raise SystemExit(f'recent_entries meal emoji replacements: {n}')
p.write_text(text2)

# Permanent regression contract.
test = ROOT / 'test/ux_1_dashboard_rich_locale_contract_test.dart'
test.write_text(r'''import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/l10n/audited_page_copy.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _localizedProbe(Locale locale, String rawMeal) {
  return MaterialApp(
    locale: locale,
    localizationsDelegates: const [
      AppLocalizations.delegate,
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    supportedLocales: AppLocalizations.supportedLocales,
    home: Builder(
      builder: (context) => Text(AuditedPageCopy.of(context).meal(rawMeal)),
    ),
  );
}

void main() {
  testWidgets('canonical meal IDs are localized in French and Arabic', (
    tester,
  ) async {
    await tester.pumpWidget(_localizedProbe(const Locale('fr'), 'dinner'));
    await tester.pumpAndSettle();
    expect(find.text('Dîner'), findsOneWidget);

    await tester.pumpWidget(_localizedProbe(const Locale('ar'), 'dinner'));
    await tester.pumpAndSettle();
    expect(find.text('العشاء'), findsOneWidget);

    await tester.pumpWidget(_localizedProbe(const Locale('ar'), 'breakfast'));
    await tester.pumpAndSettle();
    expect(find.text('الفطور'), findsOneWidget);
  });

  test('rich Dashboard widgets do not reintroduce known hard-coded French copy', () {
    const files = [
      'lib/features/dashboard/widgets/hero_live.dart',
      'lib/features/dashboard/widgets/hero_insight.dart',
      'lib/features/dashboard/widgets/kpi_gmi_card.dart',
      'lib/features/dashboard/widgets/kpi_cv_card.dart',
      'lib/features/dashboard/widgets/chart_section.dart',
      'lib/features/dashboard/widgets/glucose_chart_with_events.dart',
      'lib/features/dashboard/widgets/insights_section.dart',
      'lib/features/dashboard/widgets/recent_entries.dart',
    ];
    const forbidden = [
      'GMI estimée',
      'Variabilité (CV)',
      'Événements clés',
      'DÉCOUVERTES IAMINA',
      "Journal · Aujourd'hui",
      'Profil glycémique ambulatoire',
      'Données insuffisantes',
      'Analyse IA temporairement limitée',
      'IAmina analyse tes données',
      'u rapide',
    ];
    for (final file in files) {
      final source = File(file).readAsStringSync();
      for (final literal in forbidden) {
        expect(
          source.contains(literal),
          isFalse,
          reason: '$file contains $literal',
        );
      }
    }
  });
}
''')
