from pathlib import Path


def repl(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing {label} in {path}")
    p.write_text(text.replace(old, new, 1))

summary = "frontend/lib/features/journal/ai_summary_screen.dart"
repl(
    summary,
    """    if (isCompact) {\n      return AminaMobilePageHeader(\n        title: l10n.navIamina,\n        bottom: Align(""",
    """    if (isCompact) {\n      final language = Localizations.localeOf(context).languageCode;\n      final reportsTitle = language == 'ar'\n          ? 'التقارير'\n          : language == 'en'\n          ? 'Reports'\n          : 'Rapports';\n      final reportsSubtitle = language == 'ar'\n          ? 'تحليلات واتجاهات بياناتك'\n          : language == 'en'\n          ? 'Analysis and trends from your data'\n          : 'Analyses et tendances de vos données';\n      return AminaMobilePageHeader(\n        title: reportsTitle,\n        subtitle: reportsSubtitle,\n        bottom: Align(""",
    "summary mobile title",
)

imp = "frontend/lib/features/import/import_screen.dart"
repl(
    imp,
    """import 'package:drift/drift.dart' as drift;\n\nclass ImportScreen""",
    """import 'package:drift/drift.dart' as drift;\n\nString _importT(BuildContext context, String fr, String en, String ar) {\n  final code = Localizations.localeOf(context).languageCode;\n  if (code == 'ar') return ar;\n  if (code == 'en') return en;\n  return fr;\n}\n\nclass ImportScreen""",
    "import locale helper",
)
repl(
    imp,
    """                        title: 'Données démo — 21 jours',\n                        subtitle:\n                            'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',""",
    """                        title: _importT(\n                          context,\n                          'Données démo — 21 jours',\n                          'Demo data — 21 days',\n                          'بيانات تجريبية — 21 يوماً',\n                        ),\n                        subtitle: _importT(\n                          context,\n                          'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',\n                          'Load realistic clinical demo data to explore all features.',\n                          'حمّل بيانات سريرية تجريبية واقعية لاستكشاف جميع الميزات.',\n                        ),""",
    "demo card copy",
)
repl(
    imp,
    """                            ? const Row(\n                                mainAxisSize: MainAxisSize.min,\n                                children: [\n                                  Icon(\n                                    Icons.check,\n                                    size: 16,\n                                    color: AminaTheme.goodFg,\n                                  ),\n                                  SizedBox(width: 4),\n                                  Text(\n                                    'Chargé',\n                                    style: TextStyle(\n                                      fontSize: 12,\n                                      fontWeight: FontWeight.w700,\n                                      color: AminaTheme.goodFg,\n                                    ),\n                                  ),\n                                ],\n                              )""",
    """                            ? Row(\n                                mainAxisSize: MainAxisSize.min,\n                                children: [\n                                  const Icon(\n                                    Icons.check,\n                                    size: 16,\n                                    color: AminaTheme.goodFg,\n                                  ),\n                                  const SizedBox(width: 4),\n                                  Text(\n                                    _importT(context, 'Chargé', 'Loaded', 'تم التحميل'),\n                                    style: const TextStyle(\n                                      fontSize: 12,\n                                      fontWeight: FontWeight.w700,\n                                      color: AminaTheme.goodFg,\n                                    ),\n                                  ),\n                                ],\n                              )""",
    "demo loaded label",
)
repl(
    imp,
    """                                child: const Text(\n                                  'Charger',\n                                  style: TextStyle(""",
    """                                child: Text(\n                                  _importT(context, 'Charger', 'Load', 'تحميل'),\n                                  style: const TextStyle(""",
    "demo load label",
)
repl(
    imp,
    """  String _relativeTime(DateTime dt) {\n    final diff = DateTime.now().difference(dt);\n    if (diff.inMinutes < 1) return 'à l\\'instant';\n    if (diff.inMinutes < 60) return 'il y a ${diff.inMinutes} min';\n    if (diff.inHours < 24) return 'il y a ${diff.inHours} h';\n    if (diff.inDays < 7) return 'il y a ${diff.inDays} j';\n    final weeks = (diff.inDays / 7).floor();\n    if (weeks < 5) return 'il y a $weeks sem.';\n    return 'il y a ${(diff.inDays / 30).floor()} mois';\n  }""",
    """  String _relativeTime(BuildContext context, DateTime dt) {\n    final diff = DateTime.now().difference(dt);\n    if (diff.inMinutes < 1) {\n      return _importT(context, 'à l\\'instant', 'just now', 'الآن');\n    }\n    if (diff.inMinutes < 60) {\n      return _importT(\n        context,\n        'il y a ${diff.inMinutes} min',\n        '${diff.inMinutes} min ago',\n        'منذ ${diff.inMinutes} د',\n      );\n    }\n    if (diff.inHours < 24) {\n      return _importT(\n        context,\n        'il y a ${diff.inHours} h',\n        '${diff.inHours} h ago',\n        'منذ ${diff.inHours} س',\n      );\n    }\n    if (diff.inDays < 7) {\n      return _importT(\n        context,\n        'il y a ${diff.inDays} j',\n        '${diff.inDays} d ago',\n        'منذ ${diff.inDays} ي',\n      );\n    }\n    final weeks = (diff.inDays / 7).floor();\n    if (weeks < 5) {\n      return _importT(context, 'il y a $weeks sem.', '$weeks wk ago', 'منذ $weeks أسب.');\n    }\n    final months = (diff.inDays / 30).floor();\n    return _importT(context, 'il y a $months mois', '$months mo ago', 'منذ $months شهر');\n  }""",
    "relative time localization",
)
repl(
    imp,
    """    final label = lastLogAt != null ? _relativeTime(lastLogAt!) : '—';""",
    """    final label = lastLogAt != null ? _relativeTime(context, lastLogAt!) : '—';""",
    "relative time call",
)
repl(
    imp,
    """                  const Text(\n                    'Données expirées',\n                    style: TextStyle(""",
    """                  Text(\n                    _importT(context, 'Données expirées', 'Data expired', 'انتهت صلاحية البيانات'),\n                    style: const TextStyle(""",
    "stale title",
)
repl(
    imp,
    """                    Text(\n                      'Dernière mesure $label · Rechargez la démo pour des analyses correctes.',\n                      style: const TextStyle(""",
    """                    Text(\n                      _importT(\n                        context,\n                        'Dernière mesure $label · Rechargez la démo pour des analyses correctes.',\n                        'Last measurement $label · Reload demo data for accurate analyses.',\n                        'آخر قياس $label · أعد تحميل البيانات التجريبية لتحليلات صحيحة.',\n                      ),\n                      style: const TextStyle(""",
    "stale subtitle",
)
repl(
    imp,
    """                Text(\n                  '$totalLogs mesure${totalLogs > 1 ? 's' : ''} enregistrée${totalLogs > 1 ? 's' : ''}',""",
    """                Text(\n                  _importT(\n                    context,\n                    '$totalLogs mesure${totalLogs > 1 ? 's' : ''} enregistrée${totalLogs > 1 ? 's' : ''}',\n                    '$totalLogs saved measurement${totalLogs > 1 ? 's' : ''}',\n                    '$totalLogs قياس محفوظ',\n                  ),""",
    "normal banner title",
)
repl(
    imp,
    """                  Text(\n                    'Dernière mesure $label · Stockage local',""",
    """                  Text(\n                    _importT(\n                      context,\n                      'Dernière mesure $label · Stockage local',\n                      'Last measurement $label · Local storage',\n                      'آخر قياس $label · تخزين محلي',\n                    ),""",
    "normal banner subtitle",
)
repl(
    imp,
    """          const Tooltip(\n            message: 'Données stockées sur cet appareil',""",
    """          Tooltip(\n            message: _importT(\n              context,\n              'Données stockées sur cet appareil',\n              'Data stored on this device',\n              'البيانات محفوظة على هذا الجهاز',\n            ),""",
    "storage tooltip",
)
