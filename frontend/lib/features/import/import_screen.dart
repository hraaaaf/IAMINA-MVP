import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/localization/import_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../l10n/audited_page_copy.dart';
import '../../data/drift/database.dart';

class ImportScreen extends StatefulWidget {
  const ImportScreen({super.key});

  @override
  State<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends State<ImportScreen> {
  bool _seeding = false;
  bool _done = false;

  int? _totalLogs;
  DateTime? _lastLogAt;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    final db = context.read<AppDatabase>();
    final rows = await db.select(db.logEntries).get();
    DateTime? lastLogAt;
    for (final row in rows) {
      final occurredAt = row.loggedAt ?? row.createdAt;
      if (lastLogAt == null || occurredAt.isAfter(lastLogAt)) {
        lastLogAt = occurredAt;
      }
    }
    if (mounted) {
      setState(() {
        _totalLogs = rows.length;
        _lastLogAt = lastLogAt;
      });
    }
  }

  Future<void> _seedDemo() async {
    setState(() {
      _seeding = true;
      _done = false;
    });
    final db = context.read<AppDatabase>();
    await db.seedDemoData();
    if (mounted) {
      setState(() {
        _seeding = false;
        _done = true;
      });
      await _loadStats();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final documentSurface = _totalLogs == 0
        ? AminaFirstUsePanel(
            key: const ValueKey('import-first-use'),
            icon: Icons.upload_file_rounded,
            title: AuditedPageCopy.of(context).documentTitle,
            body: AuditedPageCopy.of(context).documentIntro,
            primaryActionLabel: AuditedPageCopy.of(context).chooseDocument,
            onPrimaryAction: () => context.push('/pulper'),
            compact: true,
          )
        : _DocumentImportCard(
            key: const ValueKey('import-document-cta'),
            onTap: () => context.push('/pulper'),
          );

    final connectionsSurface = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            AuditedPageCopy.of(context).directConnections,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: AminaTheme.ink900,
            ),
          ),
        ),
        if (kDebugMode) ...[
          _ImportOption(
            icon: Icons.science_outlined,
            title: l10n.demoDataTitle,
            subtitle: l10n.demoDataSubtitle,
            badge: 'DEV',
            badgeBg: AminaTheme.ink100,
            badgeFg: AminaTheme.ink500,
            action: _seeding
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: AminaTheme.teal500,
                    ),
                  )
                : _done
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.check,
                        size: 16,
                        color: AminaTheme.goodFg,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        l10n.loaded,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AminaTheme.goodFg,
                        ),
                      ),
                    ],
                  )
                : FilledButton(
                    onPressed: _seedDemo,
                    style: FilledButton.styleFrom(
                      backgroundColor: AminaTheme.teal500,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 8,
                      ),
                      minimumSize: Size.zero,
                    ),
                    child: Text(
                      l10n.load,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 12),
        ],
        _CgmGuideEntryCard(onTap: () => context.push('/cgm')),
      ],
    );

    return Scaffold(
      backgroundColor: AminaTheme.paper,
      body: Column(
        children: [
          _TopBar(),
          Expanded(
            child: ResponsiveContentSurface(
              maxWidth: 1040,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_totalLogs != null && _totalLogs! > 0) ...[
                      _LastImportBanner(
                        totalLogs: _totalLogs!,
                        lastLogAt: _lastLogAt,
                      ),
                      const SizedBox(height: 16),
                    ],
                    LayoutBuilder(
                      builder: (context, constraints) {
                        if (constraints.maxWidth < 900) {
                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              documentSurface,
                              const SizedBox(height: 20),
                              connectionsSurface,
                            ],
                          );
                        }
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(flex: 6, child: documentSurface),
                            const SizedBox(width: 24),
                            Expanded(flex: 4, child: connectionsSurface),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    return AminaMobilePageHeader(
      title: copy.importTitle,
      subtitle: copy.importSubtitle,
    );
  }
}

class _LastImportBanner extends StatelessWidget {
  final int totalLogs;
  final DateTime? lastLogAt;
  const _LastImportBanner({
    required this.totalLogs,
    required this.lastLogAt,
  });

  String _relativeTime(DateTime dt, AppLocalizations l10n) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return l10n.justNowRelative;
    if (diff.inMinutes < 60) return l10n.minutesAgoRelative(diff.inMinutes);
    if (diff.inHours < 24) return l10n.hoursAgoRelative(diff.inHours);
    if (diff.inDays < 7) return l10n.daysAgoRelative(diff.inDays);
    final weeks = (diff.inDays / 7).floor();
    if (weeks < 5) return l10n.weeksAgoRelative(weeks);
    return l10n.monthsAgoRelative((diff.inDays / 30).floor());
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final label = lastLogAt != null ? _relativeTime(lastLogAt!, l10n) : '—';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AminaTheme.teal50,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.teal100),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AminaTheme.teal500,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.check_circle_outline,
              size: 18,
              color: Colors.white,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.readingsRecorded(totalLogs),
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AminaTheme.teal800,
                  ),
                ),
                if (lastLogAt != null)
                  Text(
                    l10n.latestReadingStoredLocally(label),
                    style: const TextStyle(
                      fontSize: 11,
                      color: AminaTheme.teal600,
                    ),
                  ),
              ],
            ),
          ),
          Tooltip(
            message: l10n.storedOnDevice,
            child: const Icon(
              Icons.storage_outlined,
              size: 16,
              color: AminaTheme.teal500,
            ),
          ),
        ],
      ),
    );
  }
}

class _DocumentImportCard extends StatelessWidget {
  final VoidCallback onTap;
  const _DocumentImportCard({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: AuditedPageCopy.of(context).openDocumentImport,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: AminaTheme.heroGradient,
            borderRadius: BorderRadius.circular(20),
            boxShadow: AminaTheme.shadowFab,
          ),
          child: Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.upload_file,
                  color: Colors.white,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      AuditedPageCopy.of(context).documentTitle,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      AuditedPageCopy.of(context).pulperDescription,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.82),
                        fontSize: 12,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 6,
                      children: [
                        _DocumentFormatChip(
                          label: AuditedPageCopy.of(context).labReport,
                        ),
                        _DocumentFormatChip(
                          label: AuditedPageCopy.of(context).cgmExport,
                        ),
                        _DocumentFormatChip(
                          label: AuditedPageCopy.of(context).prescription,
                        ),
                        _DocumentFormatChip(
                          label: AuditedPageCopy.of(context).photo,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(
                Icons.arrow_forward_ios,
                color: Colors.white,
                size: 16,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DocumentFormatChip extends StatelessWidget {
  final String label;
  const _DocumentFormatChip({required this.label});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha: 0.18),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(
      label,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 10,
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}

class _CgmGuideEntryCard extends StatelessWidget {
  final VoidCallback onTap;

  const _CgmGuideEntryCard({required this.onTap});

  String _pick(BuildContext context, {required String fr, required String en, required String ar}) {
    final code = Localizations.localeOf(context).languageCode;
    return code == 'ar' ? ar : code == 'en' ? en : fr;
  }

  @override
  Widget build(BuildContext context) {
    final title = _pick(
      context,
      fr: 'Capteur CGM',
      en: 'CGM sensor',
      ar: 'مستشعر CGM',
    );
    final subtitle = _pick(
      context,
      fr: 'Connectez Dexcom, FreeStyle Libre ou LinX avec un guide étape par étape.',
      en: 'Connect Dexcom, FreeStyle Libre or LinX with a step-by-step guide.',
      ar: 'اربط Dexcom أو FreeStyle Libre أو LinX عبر دليل خطوة بخطوة.',
    );
    final action = _pick(
      context,
      fr: 'Ouvrir le guide CGM',
      en: 'Open CGM guide',
      ar: 'فتح دليل CGM',
    );

    return ClinicalCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AminaTheme.teal50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.sensors_rounded, size: 21, color: AminaTheme.teal700),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: AminaTheme.ink900,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                      decoration: BoxDecoration(
                        color: AminaTheme.teal50,
                        borderRadius: BorderRadius.circular(99),
                      ),
                      child: const Text(
                        'GUIDÉ',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w800,
                          color: AminaTheme.teal700,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 12, height: 1.4, color: AminaTheme.ink500),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: onTap,
                  icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                  label: Text(action),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ImportOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String badge;
  final Color badgeBg, badgeFg;
  final Widget action;

  const _ImportOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.badgeBg,
    required this.badgeFg,
    required this.action,
  });

  @override
  Widget build(BuildContext context) {
    return ClinicalCard(
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AminaTheme.teal50,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: AminaTheme.teal600),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: AminaTheme.ink900,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 7,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: badgeBg,
                        borderRadius: BorderRadius.circular(100),
                      ),
                      child: Text(
                        badge,
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: badgeFg,
                          letterSpacing: 0.04,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AminaTheme.ink500,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 12),
                action,
              ],
            ),
          ),
        ],
      ),
    );
  }
}
