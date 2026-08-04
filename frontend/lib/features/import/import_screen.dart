import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../data/drift/database.dart';
import 'package:drift/drift.dart' as drift;

class ImportScreen extends StatefulWidget {
  const ImportScreen({super.key});

  @override
  State<ImportScreen> createState() => _ImportScreenState();
}

class _ImportScreenState extends State<ImportScreen> {
  bool _seeding = false;
  bool _done    = false;

  // Last-import stats (populated from Drift on init)
  int?      _totalLogs;
  DateTime? _lastLogAt;

  // True when the most recent log is older than 3 days (demo data goes stale).
  bool get _isDataStale {
    if (_lastLogAt == null) return false;
    return DateTime.now().difference(_lastLogAt!).inDays >= 3;
  }

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    final db = context.read<AppDatabase>();
    final count = await db.countLogs();
    // Most recent log
    final rows = await (db.select(db.logEntries)
      ..orderBy([(t) => drift.OrderingTerm.desc(t.createdAt)])
      ..limit(1))
      .get();
    if (mounted) {
      setState(() {
        _totalLogs = count;
        _lastLogAt = rows.isNotEmpty ? (rows.first.loggedAt ?? rows.first.createdAt) : null;
      });
    }
  }

  Future<void> _seedDemo() async {
    setState(() { _seeding = true; _done = false; });
    final db = context.read<AppDatabase>();
    await db.seedDemoData();
    if (mounted) {
      setState(() { _seeding = false; _done = true; });
      await _loadStats(); // refresh banner with new timestamps
    }
  }

  void _showComingSoon(String name) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$name arrive bientôt — rejoignez la liste d\'attente dans Profil.'),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.paper,
      body: Column(
        children: [
          _TopBar(),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Last import summary banner ──────────────────────────────
                  if (_totalLogs != null && _totalLogs! > 0) ...[
                    _LastImportBanner(totalLogs: _totalLogs!, lastLogAt: _lastLogAt, isStale: _isDataStale),
                    const SizedBox(height: 16),
                  ],
                  // ── Pulper IAmina ──────────────────────────────────────────
                  _PulperCard(onTap: () => context.push('/pulper')),
                  const SizedBox(height: 20),
                  const Padding(
                    padding: EdgeInsets.only(bottom: 16),
                    child: Text('Connexions directes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AminaTheme.ink900)),
                  ),
                  if (kDebugMode) ...[
                    _ImportOption(
                      icon: Icons.science_outlined,
                      title: 'Données démo — 21 jours',
                      subtitle: 'Charger un jeu de données cliniques réalistes pour explorer toutes les fonctionnalités.',
                      badge: 'DEV',
                      badgeBg: AminaTheme.ink100,
                      badgeFg: AminaTheme.ink500,
                      action: _seeding
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: AminaTheme.teal500))
                          : _done
                              ? const Row(mainAxisSize: MainAxisSize.min, children: [
                                  Icon(Icons.check, size: 16, color: AminaTheme.goodFg),
                                  SizedBox(width: 4),
                                  Text('Chargé', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AminaTheme.goodFg)),
                                ])
                              : FilledButton(
                                  onPressed: _seedDemo,
                                  style: FilledButton.styleFrom(
                                    backgroundColor: AminaTheme.teal500,
                                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                    minimumSize: Size.zero,
                                  ),
                                  child: const Text('Charger', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  _ImportOption(
                    icon: Icons.bluetooth,
                    title: 'Dexcom G6/G7',
                    subtitle: 'Connexion directe via Dexcom CLARITY. Synchronisation automatique toutes les 5 minutes.',
                    badge: 'BIENTÔT',
                    badgeBg: AminaTheme.ink50,
                    badgeFg: AminaTheme.ink500,
                    action: OutlinedButton(
                      onPressed: () => _showComingSoon('Dexcom G6/G7'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        minimumSize: Size.zero,
                        side: const BorderSide(color: AminaTheme.ink200),
                      ),
                      child: const Text('Notifiez-moi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _ImportOption(
                    icon: Icons.sensors,
                    title: 'Abbott LibreLink',
                    subtitle: 'Import des données LibreView via CSV ou connexion API.',
                    badge: 'BIENTÔT',
                    badgeBg: AminaTheme.ink50,
                    badgeFg: AminaTheme.ink500,
                    action: OutlinedButton(
                      onPressed: () => _showComingSoon('Abbott LibreLink'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        minimumSize: Size.zero,
                        side: const BorderSide(color: AminaTheme.ink200),
                      ),
                      child: const Text('Notifiez-moi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),
                    ),
                  ),
                ],
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
    return Container(
      padding: EdgeInsetsDirectional.fromSTEB(16, MediaQuery.of(context).padding.top + 12, 16, 12),
      decoration: const BoxDecoration(
        color: AminaTheme.cardBg,
        border: Border(bottom: BorderSide(color: AminaTheme.ink100)),
      ),
      child: const Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Importer', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AminaTheme.ink900)),
                Text('Connectez vos sources de données', style: TextStyle(fontSize: 12, color: AminaTheme.ink500)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Last-import summary banner ────────────────────────────────────────────────

class _LastImportBanner extends StatelessWidget {
  final int totalLogs;
  final DateTime? lastLogAt;
  final bool isStale;
  const _LastImportBanner({required this.totalLogs, required this.lastLogAt, this.isStale = false});

  String _relativeTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1)  return 'à l\'instant';
    if (diff.inMinutes < 60) return 'il y a ${diff.inMinutes} min';
    if (diff.inHours   < 24) return 'il y a ${diff.inHours} h';
    if (diff.inDays    < 7)  return 'il y a ${diff.inDays} j';
    final weeks = (diff.inDays / 7).floor();
    if (weeks < 5) return 'il y a $weeks sem.';
    return 'il y a ${(diff.inDays / 30).floor()} mois';
  }

  @override
  Widget build(BuildContext context) {
    final label = lastLogAt != null ? _relativeTime(lastLogAt!) : '—';

    // Stale state: amber palette + warning icon + "recharger" hint.
    if (isStale) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF8E1),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFFFE082)),
        ),
        child: Row(children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(color: const Color(0xFFF9A825), borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.update, size: 18, color: Colors.white),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text(
              'Données expirées',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Color(0xFF5D3A00)),
            ),
            if (lastLogAt != null)
              Text('Dernière mesure $label · Rechargez la démo pour des analyses correctes.',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF795900), height: 1.4)),
          ])),
          const Icon(Icons.warning_amber_rounded, size: 16, color: Color(0xFFF9A825)),
        ]),
      );
    }

    // Normal state: teal palette.
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AminaTheme.teal50,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.teal100),
      ),
      child: Row(children: [
        Container(
          width: 36, height: 36,
          decoration: BoxDecoration(color: AminaTheme.teal500, borderRadius: BorderRadius.circular(10)),
          child: const Icon(Icons.check_circle_outline, size: 18, color: Colors.white),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(
            '$totalLogs mesure${totalLogs > 1 ? 's' : ''} enregistrée${totalLogs > 1 ? 's' : ''}',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AminaTheme.teal800),
          ),
          if (lastLogAt != null)
            Text('Dernière mesure $label', style: const TextStyle(fontSize: 11, color: AminaTheme.teal600)),
        ])),
        const Icon(Icons.sync_outlined, size: 16, color: AminaTheme.teal500),
      ]),
    );
  }
}

// ── Pulper IAmina card ────────────────────────────────────────────────────────

class _PulperCard extends StatelessWidget {
  final VoidCallback onTap;
  const _PulperCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
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
              width: 52, height: 52,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.upload_file, color: Colors.white, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text(
                  'Pulper IAmina',
                  style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  'PDF · Photo · Excel · Word — IAmina extrait tout automatiquement.',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.82), fontSize: 12, height: 1.4),
                ),
                const SizedBox(height: 10),
                const Wrap(spacing: 6, children: [
                  _PulperChip(label: 'Bilan labo'),
                  _PulperChip(label: 'Export CGM'),
                  _PulperChip(label: 'Ordonnance'),
                  _PulperChip(label: 'Photo'),
                ]),
              ]),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16),
          ],
        ),
      ),
    );
  }
}

class _PulperChip extends StatelessWidget {
  final String label;
  const _PulperChip({required this.label});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha: 0.18),
      borderRadius: BorderRadius.circular(99),
    ),
    child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
  );
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
            width: 36, height: 36,
            decoration: BoxDecoration(color: AminaTheme.teal50, borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, size: 18, color: AminaTheme.teal600),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AminaTheme.ink900))),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                      decoration: BoxDecoration(color: badgeBg, borderRadius: BorderRadius.circular(100)),
                      child: Text(badge, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: badgeFg, letterSpacing: 0.04)),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(subtitle, style: const TextStyle(fontSize: 12, color: AminaTheme.ink500, height: 1.4)),
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
