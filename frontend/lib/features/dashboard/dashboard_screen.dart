import 'dart:math' as math;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'package:go_router/go_router.dart';
import '../../data/drift/database.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../l10n/audited_page_copy.dart';
import '../../services/sync_service.dart';
import 'clinical_engine.dart';
import 'widgets/glucose_chart_with_events.dart';
import '../journal/widgets/amina_chat_view.dart';
import '../../data/models/ai_models.dart';
import '../../services/api_client.dart';

// Widget parts — private classes split by concern to stay ≤200 lines each.
// All share the imports above via the Dart library part mechanism.
part 'widgets/top_bar.dart';
// Hero section split into focused part-files
part 'widgets/hero_section.dart'; // PageHead + HeroContextual orchestrator
part 'widgets/hero_ecg.dart'; // ECG painter + AnimatedEcg
part 'widgets/hero_atoms.dart'; // Badge / Chip / Btn / DotsPainter atoms
part 'widgets/hero_live.dart'; // HeroLive — post-meal <90 min card
part 'widgets/hero_insight.dart'; // HeroInsight — morning / default card
part 'widgets/hero_tir.dart'; // HeroTIR — midday TIR card
// KPI cards split into focused part-files
part 'widgets/kpi_cards.dart'; // MetricRow layout + DeltaChip + LegendDot
part 'widgets/kpi_tir_card.dart'; // TIRCard
part 'widgets/kpi_gmi_card.dart'; // GMICard + GmiConfidenceBadge
part 'widgets/kpi_cv_card.dart'; // CVCard
part 'widgets/chart_section.dart';
part 'widgets/insights_section.dart';
part 'widgets/recent_entries.dart';
part 'widgets/speed_dial.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DashboardScreen
// ─────────────────────────────────────────────────────────────────────────────

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  int _range = 21;
  late AnimationController _staggerCtrl;
  final List<Animation<double>> _fadeAnims = [];
  final List<Animation<Offset>> _slideAnims = [];
  static const _itemCount = 6;

  SummaryResponse? _aiSummary;
  bool _isLoadingSummary = false;

  // C1: last known logs cached so _openChat can build a context message
  List<LogEntryData> _cachedLogs = [];
  String? _cachedUnit;

  @override
  void initState() {
    super.initState();
    _staggerCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    for (int i = 0; i < _itemCount; i++) {
      final start = (i * 0.12).clamp(0.0, 0.7);
      final end = (start + 0.4).clamp(0.0, 1.0);
      _fadeAnims.add(
        Tween<double>(begin: 0.0, end: 1.0).animate(
          CurvedAnimation(
            parent: _staggerCtrl,
            curve: Interval(start, end, curve: Curves.easeOut),
          ),
        ),
      );
      _slideAnims.add(
        Tween<Offset>(begin: const Offset(0, 0.08), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _staggerCtrl,
            curve: Interval(start, end, curve: Curves.easeOutCubic),
          ),
        ),
      );
    }
    _staggerCtrl.forward();

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      final db = context.read<AppDatabase>();
      final count = await db.select(db.logEntries).get().then((r) => r.length);
      // Seed only in debug — production users must see their own real data.
      if (count == 0 && kDebugMode) await db.seedDemoData();
      _fetchAiSummary();
    });
  }

  Future<void> _fetchAiSummary() async {
    if (!mounted) return;
    setState(() => _isLoadingSummary = true);
    try {
      final api = context.read<ApiClient>();
      final res = await api.getAiSummary(days: _range);
      if (mounted) setState(() => _aiSummary = res);
    } catch (e) {
      debugPrint('Error fetching AI summary: $e');
    } finally {
      if (mounted) setState(() => _isLoadingSummary = false);
    }
  }

  @override
  void dispose() {
    _staggerCtrl.dispose();
    super.dispose();
  }

  Widget _staggered(int index, Widget child) {
    final i = index.clamp(0, _itemCount - 1);
    return FadeTransition(
      opacity: _fadeAnims[i],
      child: SlideTransition(position: _slideAnims[i], child: child),
    );
  }

  /// Builds a context string from the most recent log entry so IAmina
  /// has immediate clinical context when the chat opens from the dashboard.
  String? _buildChatContext() {
    if (_cachedLogs.isEmpty) return null;
    final latest = _cachedLogs.reduce((a, b) {
      final aTime = a.loggedAt ?? a.createdAt;
      final bTime = b.loggedAt ?? b.createdAt;
      return aTime.isAfter(bTime) ? a : b;
    });
    final unit = _cachedUnit ?? 'mg/dL';
    final val = unit == 'mmol/L'
        ? '${(latest.bloodSugar / 18.0).toStringAsFixed(1)} mmol/L'
        : '${latest.bloodSugar.toInt()} mg/dL';
    final mealPart = latest.mealType != null && latest.mealType!.isNotEmpty
        ? ' — ${latest.mealType}'
        : '';
    return 'Ma dernière mesure est $val$mealPart. Peux-tu analyser ma situation actuelle ?';
  }

  void _openChat() {
    final ctx = _buildChatContext();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (sheetCtx, sc) => AminaChatView(
          onClose: () => Navigator.pop(sheetCtx),
          initialMessage: ctx,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final now = DateTime.now();
    final start = now.subtract(Duration(days: _range));

    return StreamBuilder<PatientProfileData?>(
      stream: db.watchProfile(),
      builder: (context, profileSnap) {
        final profile = profileSnap.data;
        final unit = profile?.unitPreference ?? 'mg/dL';
        final low = profile?.targetRangeLow ?? 70.0;
        final high = profile?.targetRangeHigh ?? 180.0;

        return StreamBuilder<List<LogEntryData>>(
          stream: db.watchLogsInRange(start, now),
          builder: (context, logsSnap) {
            final logs = logsSnap.data ?? [];
            final localDataLoading =
                profileSnap.connectionState == ConnectionState.waiting ||
                logsSnap.connectionState == ConnectionState.waiting;
            final localDataError = profileSnap.hasError || logsSnap.hasError;
            // Cache logs + unit for _buildChatContext (no setState — read-only cache)
            WidgetsBinding.instance.addPostFrameCallback((_) {
              _cachedLogs = logs;
              _cachedUnit = unit;
            });
            // Previous period for delta chips (same window, shifted back)
            final prevStart = start.subtract(Duration(days: _range));
            return StreamBuilder<List<LogEntryData>>(
              stream: db.watchLogsInRange(prevStart, start),
              builder: (context, prevSnap) {
                final prevLogs = prevSnap.data ?? [];

                final screenW = MediaQuery.of(context).size.width;
                final hPad = screenW >= 1400
                    ? (screenW - 1200) / 2
                    : screenW >= 900
                    ? 48.0
                    : 16.0;

                return Scaffold(
                  backgroundColor: AminaTheme.bg(context),
                  floatingActionButton: screenW >= 720 || logs.isEmpty
                      ? null
                      : _AddFab(
                          onTap: () => GoRouter.of(context).go('/ajouter'),
                        ),
                  body: CustomScrollView(
                    slivers: [
                      SliverToBoxAdapter(
                        child: _TopBar(
                          range: _range,
                          onRangeChanged: (r) {
                            setState(() => _range = r);
                            _fetchAiSummary();
                          },
                          syncService: context.read<SyncService>(),
                          onChatTap: _openChat,
                          hPad: hPad,
                        ),
                      ),
                      SliverPadding(
                        padding: EdgeInsetsDirectional.fromSTEB(
                          hPad,
                          0,
                          hPad,
                          120,
                        ),
                        sliver: SliverList(
                          delegate: SliverChildListDelegate([
                            if (localDataError) ...[
                              _DashboardLocalState(
                                isError: true,
                                onRetry: () => setState(() {}),
                              ),
                            ] else if (localDataLoading) ...[
                              const _DashboardLocalState(),
                            ] else if (logs.isEmpty) ...[
                              if (kDebugMode) _SeedBanner(db: db),
                              Align(
                                alignment: AlignmentDirectional.topCenter,
                                child: ConstrainedBox(
                                  constraints: const BoxConstraints(
                                    maxWidth: 900,
                                  ),
                                  child: _EmptyDashboard(
                                    onAddTap: () =>
                                        GoRouter.of(context).go('/ajouter'),
                                    onImportTap: () =>
                                        GoRouter.of(context).go('/importer'),
                                  ),
                                ),
                              ),
                            ] else ...[
                              _staggered(
                                0,
                                _PageHead(
                                  logCount: logs.length,
                                  range: _range,
                                  isDesktop: screenW >= 900,
                                ),
                              ),
                              const SizedBox(height: 14),
                              _staggered(
                                1,
                                _HeroContextual(
                                  logs: logs,
                                  unit: unit,
                                  low: low,
                                  high: high,
                                  range: _range,
                                ),
                              ),
                              const SizedBox(height: 18),
                              _staggered(
                                2,
                                _MetricRow(
                                  logs: logs,
                                  prevLogs: prevLogs,
                                  low: low,
                                  high: high,
                                  range: _range,
                                ),
                              ),
                              const SizedBox(height: 18),
                              _staggered(
                                3,
                                _ChartSection(
                                  logs: logs,
                                  low: low,
                                  high: high,
                                  unit: unit,
                                ),
                              ),
                              const SizedBox(height: 18),
                              _staggered(
                                4,
                                _InsightsSection(
                                  logs: logs,
                                  summary: _aiSummary,
                                  isLoading: _isLoadingSummary,
                                ),
                              ),
                              const SizedBox(height: 18),
                              _staggered(
                                5,
                                _RecentEntries(
                                  logs: logs,
                                  unit: unit,
                                  low: low,
                                  high: high,
                                  isDesktop: screenW >= 900,
                                ),
                              ),
                            ],
                          ]),
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        );
      },
    );
  }
}

// ── Seed Banner (debug only) ──────────────────────────────────────────────────

class _SeedBanner extends StatefulWidget {
  final AppDatabase db;
  const _SeedBanner({required this.db});
  @override
  State<_SeedBanner> createState() => _SeedBannerState();
}

class _SeedBannerState extends State<_SeedBanner> {
  bool _loading = false;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: AminaTheme.warnBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.warnFg.withValues(alpha: 0.25)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.science_outlined,
            size: 15,
            color: AminaTheme.warnFg,
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              'Mode dev — aucune donnée patient.',
              style: TextStyle(
                fontSize: 12,
                color: AminaTheme.warnFg,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          GestureDetector(
            onTap: _loading ? null : _seed,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
              decoration: BoxDecoration(
                color: AminaTheme.warnFg,
                borderRadius: BorderRadius.circular(8),
              ),
              child: _loading
                  ? const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Charger démo',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _seed() async {
    setState(() => _loading = true);
    await widget.db.seedDemoData();
    if (mounted) setState(() => _loading = false);
  }
}

// ── Dashboard local states + first use ────────────────────────────────────────

class _DashboardLocalState extends StatelessWidget {
  final bool isError;
  final VoidCallback? onRetry;

  const _DashboardLocalState({this.isError = false, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return Align(
      alignment: AlignmentDirectional.topCenter,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 720),
        margin: const EdgeInsets.only(top: 32),
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AminaTheme.surface(context),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: (isError ? AminaTheme.dangerFg : AminaTheme.teal500)
                    .withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: isError
                  ? const Icon(Icons.error_outline, color: AminaTheme.dangerFg)
                  : const Padding(
                      padding: EdgeInsets.all(14),
                      child: CircularProgressIndicator(strokeWidth: 2.2),
                    ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isError
                        ? l10n.dashboardLoadErrorTitle
                        : l10n.dashboardLoadingTitle,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isError
                        ? l10n.dashboardLoadErrorBody
                        : l10n.dashboardLoadingBody,
                    style: TextStyle(
                      fontSize: 13,
                      height: 1.45,
                      color: AminaTheme.textSecondary(context),
                    ),
                  ),
                ],
              ),
            ),
            if (isError && onRetry != null) ...[
              const SizedBox(width: 12),
              TextButton(onPressed: onRetry, child: Text(l10n.retry)),
            ],
          ],
        ),
      ),
    );
  }
}

class _EmptyDashboard extends StatelessWidget {
  final VoidCallback onAddTap;
  final VoidCallback onImportTap;

  const _EmptyDashboard({required this.onAddTap, required this.onImportTap});

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return ValueListenableBuilder<SyncUiState>(
      valueListenable: context.read<SyncService>().state,
      builder: (context, state, _) {
        final note = state == SyncUiState.offline
            ? '${AuditedPageCopy.of(context).sync('offline')} · ${l10n.firstUseTruthNote}'
            : l10n.firstUseTruthNote;
        return AminaFirstUsePanel(
          icon: Icons.monitor_heart_outlined,
          title: l10n.emptyDashboardTitle,
          body: l10n.emptyDashboardBody,
          primaryActionLabel: l10n.addFirstMeasurement,
          onPrimaryAction: onAddTap,
          secondaryActionLabel: l10n.importDocument,
          onSecondaryAction: onImportTap,
          note: note,
        );
      },
    );
  }
}
