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
part 'widgets/hero_section.dart';   // PageHead + HeroContextual orchestrator
part 'widgets/hero_ecg.dart';        // ECG painter + AnimatedEcg
part 'widgets/hero_atoms.dart';      // Badge / Chip / Btn / DotsPainter atoms
part 'widgets/hero_live.dart';       // HeroLive — post-meal <90 min card
part 'widgets/hero_insight.dart';    // HeroInsight — morning / default card
part 'widgets/hero_tir.dart';        // HeroTIR — midday target-range card
// KPI cards split into focused part-files
part 'widgets/kpi_cards.dart';       // MetricRow layout + DeltaChip + LegendDot
part 'widgets/kpi_tir_card.dart';    // target-range card
part 'widgets/kpi_gmi_card.dart';    // GMICard + GmiConfidenceBadge
part 'widgets/kpi_cv_card.dart';     // CVCard
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

class _DashboardScreenState extends State<DashboardScreen> with TickerProviderStateMixin {
  int _range = 21;
  late AnimationController _staggerCtrl;
  final List<Animation<double>> _fadeAnims = [];
  final List<Animation<Offset>> _slideAnims = [];
  static const _itemCount = 6;

  SummaryResponse? _aiSummary;
  bool _isLoadingSummary = false;

  // C1: last known logs cached so _openChat can build a context message
  List<LogEntryData> _cachedLogs = [];
  String?            _cachedUnit;

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
      _fadeAnims.add(Tween<double>(begin: 0.0, end: 1.0).animate(
        CurvedAnimation(parent: _staggerCtrl, curve: Interval(start, end, curve: Curves.easeOut)),
      ));
      _slideAnims.add(Tween<Offset>(begin: const Offset(0, 0.08), end: Offset.zero).animate(
        CurvedAnimation(parent: _staggerCtrl, curve: Interval(start, end, curve: Curves.easeOutCubic)),
      ));
    }
    _staggerCtrl.forward();
    _loadAISummary();
  }

  @override
  void dispose() {
    _staggerCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadAISummary() async {
    if (_isLoadingSummary) return;
    setState(() => _isLoadingSummary = true);
    final api = context.read<ApiClient>();
    final result = await api.fetchSummary(days: _range);
    if (!mounted) return;
    setState(() {
      _aiSummary = result;
      _isLoadingSummary = false;
    });
  }

  void _onRangeChanged(int value) {
    if (_range == value) return;
    setState(() => _range = value);
    _loadAISummary();
  }

  Future<void> _openChat() async {
    final logs = _cachedLogs;
    final unit = _cachedUnit ?? 'mg/dL';
    String? initial;
    if (logs.isNotEmpty) {
      final recent = logs.take(3).map((l) => '${l.bloodSugar.toStringAsFixed(0)} $unit').join(', ');
      initial = 'Mes dernières mesures : $recent.';
    }
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => FractionallySizedBox(
        heightFactor: 0.94,
        child: AminaChatView(initialMessage: initial),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final syncService = context.read<SyncService>();
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: StreamBuilder<List<LogEntryData>>(
        stream: db.watchLogsForDays(_range),
        builder: (context, snapshot) {
          final logs = snapshot.data ?? const <LogEntryData>[];
          _cachedLogs = logs;
          final unit = logs.isNotEmpty ? logs.first.unit : 'mg/dL';
          _cachedUnit = unit;
          final targetLow = 70.0;
          final targetHigh = 180.0;
          return LayoutBuilder(
            builder: (context, constraints) {
              final isDesktop = constraints.maxWidth >= 920;
              final hPad = isDesktop ? 32.0 : 16.0;
              return Stack(
                children: [
                  Column(
                    children: [
                      _TopBar(
                        range: _range,
                        onRangeChanged: _onRangeChanged,
                        syncService: syncService,
                        onChatTap: _openChat,
                        hPad: hPad,
                      ),
                      Expanded(
                        child: RefreshIndicator(
                          onRefresh: () async {
                            await syncService.syncPendingLogs();
                            await _loadAISummary();
                          },
                          child: SingleChildScrollView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: EdgeInsetsDirectional.only(
                              start: hPad,
                              end: hPad,
                              bottom: 110,
                            ),
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 1280),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  _PageHead(
                                    logCount: logs.length,
                                    range: _range,
                                    isDesktop: isDesktop,
                                  ),
                                  const SizedBox(height: 22),
                                  _animated(
                                    0,
                                    _HeroContextual(
                                      logs: logs,
                                      unit: unit,
                                      low: targetLow,
                                      high: targetHigh,
                                      range: _range,
                                    ),
                                  ),
                                  const SizedBox(height: 22),
                                  _animated(
                                    1,
                                    _KpiCards(
                                      logs: logs,
                                      low: targetLow,
                                      high: targetHigh,
                                      range: _range,
                                      isDesktop: isDesktop,
                                    ),
                                  ),
                                  const SizedBox(height: 22),
                                  _animated(
                                    2,
                                    _ChartSection(
                                      logs: logs,
                                      low: targetLow,
                                      high: targetHigh,
                                      unit: unit,
                                      isDesktop: isDesktop,
                                    ),
                                  ),
                                  const SizedBox(height: 22),
                                  _animated(
                                    3,
                                    _InsightsSection(
                                      summary: _aiSummary,
                                      loading: _isLoadingSummary,
                                      onRetry: _loadAISummary,
                                    ),
                                  ),
                                  const SizedBox(height: 22),
                                  _animated(
                                    4,
                                    _RecentEntries(logs: logs, unit: unit),
                                  ),
                                  const SizedBox(height: 28),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  PositionedDirectional(
                    end: isDesktop ? 32 : 16,
                    bottom: isDesktop ? 24 : 88,
                    child: _AddFab(onTap: () => context.push('/log/new')),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Widget _animated(int index, Widget child) {
    return FadeTransition(
      opacity: _fadeAnims[index],
      child: SlideTransition(position: _slideAnims[index], child: child),
    );
  }
}
