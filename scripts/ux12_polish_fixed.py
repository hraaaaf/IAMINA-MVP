from pathlib import Path


def once(path: str, old: str, new: str, label: str) -> None:
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing {label} in {path}")
    p.write_text(text.replace(old, new, 1))

summary = "frontend/lib/features/journal/ai_summary_screen.dart"
once(
    summary,
    """    if (isCompact) {
      return AminaMobilePageHeader(
        title: l10n.navIamina,
        bottom: Align(""",
    """    if (isCompact) {
      final language = Localizations.localeOf(context).languageCode;
      final reportsTitle = language == 'ar'
          ? 'التقارير'
          : language == 'en'
          ? 'Reports'
          : 'Rapports';
      final reportsSubtitle = language == 'ar'
          ? 'تحليلات واتجاهات بياناتك'
          : language == 'en'
          ? 'Analysis and trends from your data'
          : 'Analyses et tendances de vos données';
      return AminaMobilePageHeader(
        title: reportsTitle,
        subtitle: reportsSubtitle,
        bottom: Align(""",
    "summary mobile page identity",
)

imp = "frontend/lib/features/import/import_screen.dart"
once(
    imp,
    "import 'package:drift/drift.dart' as drift;\n\nclass ImportScreen",
    """import 'package:drift/drift.dart' as drift;

String _importT(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class ImportScreen""",
    "import locale helper",
)
once(
    imp,
    """                        title: 'Données démo — 21 jours',
                        subtitle:
                            'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',""",
    """                        title: _importT(
                          context,
                          'Données démo — 21 jours',
                          'Demo data — 21 days',
                          'بيانات تجريبية — 21 يوماً',
                        ),
                        subtitle: _importT(
                          context,
                          'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',
                          'Load realistic clinical demo data to explore all features.',
                          'حمّل بيانات سريرية تجريبية واقعية لاستكشاف جميع الميزات.',
                        ),""",
    "demo copy",
)
once(
    imp,
    """                            ? const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.check,
                                    size: 16,
                                    color: AminaTheme.goodFg,
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    'Chargé',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: AminaTheme.goodFg,
                                    ),
                                  ),
                                ],
                              )""",
    """                            ? Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(
                                    Icons.check,
                                    size: 16,
                                    color: AminaTheme.goodFg,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    _importT(context, 'Chargé', 'Loaded', 'تم التحميل'),
                                    style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: AminaTheme.goodFg,
                                    ),
                                  ),
                                ],
                              )""",
    "loaded label",
)
once(
    imp,
    """                                child: const Text(
                                  'Charger',
                                  style: TextStyle(""",
    """                                child: Text(
                                  _importT(context, 'Charger', 'Load', 'تحميل'),
                                  style: const TextStyle(""",
    "load label",
)
once(
    imp,
    """  String _relativeTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'à l\\'instant';
    if (diff.inMinutes < 60) return 'il y a ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'il y a ${diff.inHours} h';
    if (diff.inDays < 7) return 'il y a ${diff.inDays} j';
    final weeks = (diff.inDays / 7).floor();
    if (weeks < 5) return 'il y a $weeks sem.';
    return 'il y a ${(diff.inDays / 30).floor()} mois';
  }""",
    """  String _relativeTime(BuildContext context, DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) {
      return _importT(context, 'à l\\'instant', 'just now', 'الآن');
    }
    if (diff.inMinutes < 60) {
      return _importT(context, 'il y a ${diff.inMinutes} min', '${diff.inMinutes} min ago', 'منذ ${diff.inMinutes} د');
    }
    if (diff.inHours < 24) {
      return _importT(context, 'il y a ${diff.inHours} h', '${diff.inHours} h ago', 'منذ ${diff.inHours} س');
    }
    if (diff.inDays < 7) {
      return _importT(context, 'il y a ${diff.inDays} j', '${diff.inDays} d ago', 'منذ ${diff.inDays} ي');
    }
    final weeks = (diff.inDays / 7).floor();
    if (weeks < 5) {
      return _importT(context, 'il y a $weeks sem.', '$weeks wk ago', 'منذ $weeks أسب.');
    }
    final months = (diff.inDays / 30).floor();
    return _importT(context, 'il y a $months mois', '$months mo ago', 'منذ $months شهر');
  }""",
    "relative time",
)
once(
    imp,
    "final label = lastLogAt != null ? _relativeTime(lastLogAt!) : '—';",
    "final label = lastLogAt != null ? _relativeTime(context, lastLogAt!) : '—';",
    "relative time invocation",
)
once(
    imp,
    """                  const Text(
                    'Données expirées',
                    style: TextStyle(""",
    """                  Text(
                    _importT(context, 'Données expirées', 'Data expired', 'انتهت صلاحية البيانات'),
                    style: const TextStyle(""",
    "stale title",
)
once(
    imp,
    "'Dernière mesure $label · Rechargez la démo pour des analyses correctes.',",
    """_importT(
                        context,
                        'Dernière mesure $label · Rechargez la démo pour des analyses correctes.',
                        'Last measurement $label · Reload demo data for accurate analyses.',
                        'آخر قياس $label · أعد تحميل البيانات التجريبية لتحليلات صحيحة.',
                      ),""",
    "stale detail",
)
once(
    imp,
    "'$totalLogs mesure${totalLogs > 1 ? 's' : ''} enregistrée${totalLogs > 1 ? 's' : ''}',",
    """_importT(
                    context,
                    '$totalLogs mesure${totalLogs > 1 ? 's' : ''} enregistrée${totalLogs > 1 ? 's' : ''}',
                    '$totalLogs saved measurement${totalLogs > 1 ? 's' : ''}',
                    '$totalLogs قياس محفوظ',
                  ),""",
    "normal title",
)
once(
    imp,
    "'Dernière mesure $label · Stockage local',",
    """_importT(
                      context,
                      'Dernière mesure $label · Stockage local',
                      'Last measurement $label · Local storage',
                      'آخر قياس $label · تخزين محلي',
                    ),""",
    "normal detail",
)
once(
    imp,
    """          const Tooltip(
            message: 'Données stockées sur cet appareil',""",
    """          Tooltip(
            message: _importT(
              context,
              'Données stockées sur cet appareil',
              'Data stored on this device',
              'البيانات محفوظة على هذا الجهاز',
            ),""",
    "storage tooltip",
)
