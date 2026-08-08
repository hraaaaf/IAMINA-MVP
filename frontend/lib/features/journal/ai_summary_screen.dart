import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../services/api_client.dart';
import '../../data/models/ai_models.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/audited_page_copy.dart';
import './widgets/amina_chat_view.dart';
import '../dashboard/widgets/tweaks_panel.dart';
import '../dashboard/widgets/agp_chart.dart';

// ─────────────────────────────────────────────────────────────────────────────
// IAmina Summary Screen — Redesign
// ─────────────────────────────────────────────────────────────────────────────

class AISummaryScreen extends StatefulWidget {
  const AISummaryScreen({super.key});
  @override
  State<AISummaryScreen> createState() => _AISummaryScreenState();
}

class _AISummaryScreenState extends State<AISummaryScreen> {
  bool _isLoading = true;
  SummaryResponse? _summary;
  KpisResponse? _kpis;
  String? _errorMessage;
  bool _showTweaks = false;
  int _periodDays = 21;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToInsights() {
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent * 0.45,
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeInOut,
    );
  }

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    final api = context.read<ApiClient>();
    final results = await Future.wait([
      api.getAiSummary(days: _periodDays),
      api.getKpis(days: _periodDays),
    ]);
    if (!mounted) return;
    final summary = results[0] as SummaryResponse?;
    final kpis = results[1] as KpisResponse?;
    setState(() {
      _summary = summary;
      _kpis = kpis;
      _isLoading = false;
      if (summary == null)
        _errorMessage = AppLocalizations.of(context)!.analysisLoadError;
    });
  }

  void _setPeriod(int days) {
    if (_periodDays == days) return;
    setState(() => _periodDays = days);
    _fetchData();
  }

  void _openChat() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        builder: (ctx, _) => AminaChatView(onClose: () => Navigator.pop(ctx)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        children: [
          Positioned.fill(
            child: Column(
              children: [
                _SummaryTopBar(
                  periodDays: _periodDays,
                  onPeriodChange: _setPeriod,
                  onTweaksTap: () => setState(() => _showTweaks = !_showTweaks),
                ),
                Expanded(
                  child: _isLoading
                      ? _buildLoader()
                      : _errorMessage != null
                      ? _buildError()
                      : _buildContent(),
                ),
              ],
            ),
          ),
          if (_showTweaks)
            Positioned.fill(
              child: TweaksPanel(
                onClose: () => setState(() => _showTweaks = false),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLoader() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _PulseAnimation(
            child: Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                gradient: AminaTheme.heroGradient,
                borderRadius: BorderRadius.circular(18),
                boxShadow: AminaTheme.shadowFab,
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: Colors.white,
                size: 28,
              ),
            ),
          ),
          const SizedBox(height: 22),
          Text(
            AppLocalizations.of(context)!.analysisLoading,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: AminaTheme.textPrimary(context),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            AppLocalizations.of(context)!.analysisLoadingWait,
            style: TextStyle(
              color: AminaTheme.textSecondary(context),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    final l10n = AppLocalizations.of(context)!;
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 720;
        final icon = Container(
          width: isWide ? 56 : 48,
          height: isWide ? 56 : 48,
          decoration: BoxDecoration(
            color: AminaTheme.dangerBg,
            borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
          ),
          child: Icon(
            Icons.cloud_off_outlined,
            color: AminaTheme.dangerFg,
            size: isWide ? 28 : 24,
          ),
        );
        final message = Text(
          l10n.analysisLoadError,
          textAlign: isWide ? TextAlign.start : TextAlign.center,
          style: TextStyle(
            fontSize: isWide ? 16 : 15,
            height: 1.35,
            fontWeight: FontWeight.w800,
            color: AminaTheme.textPrimary(context),
          ),
        );
        final retry = FilledButton.icon(
          onPressed: _fetchData,
          icon: const Icon(Icons.refresh, size: 17),
          label: Text(l10n.retry),
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
            ),
          ),
        );
        return Align(
          alignment: Alignment.topCenter,
          child: Padding(
            padding: EdgeInsetsDirectional.fromSTEB(20, isWide ? 48 : 32, 20, 24),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: isWide ? 680 : 420),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.all(isWide ? 28 : 24),
                decoration: BoxDecoration(
                  color: AminaTheme.surface(context),
                  borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
                  border: Border.all(color: AminaTheme.divider(context)),
                  boxShadow: AminaTheme.shadowClinical,
                ),
                child: isWide
                    ? Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          icon,
                          const SizedBox(width: 20),
                          Expanded(child: message),
                          const SizedBox(width: 24),
                          SizedBox(width: 190, child: retry),
                        ],
                      )
                    : Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          icon,
                          const SizedBox(height: 16),
                          message,
                          const SizedBox(height: 18),
                          SizedBox(width: double.infinity, child: retry),
                        ],
                      ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildContent() {
    final summary = _summary!;
    final cards = summary.insightCards;
    final kpis = _kpis;
    final isWide = MediaQuery.of(context).size.width >= 600;

    if (isWide) {
      return _buildWideLayout(summary, cards, kpis);
    }
    return _buildNarrowLayout(summary, cards, kpis);
  }

  // ── Mobile layout ──────────────────────────────────────────────────────────
  Widget _buildNarrowLayout(
    SummaryResponse summary,
    List<InsightCard> cards,
    KpisResponse? kpis,
  ) {
    return CustomScrollView(
      controller: _scrollController,
      slivers: [
        SliverPadding(
          padding: const EdgeInsetsDirectional.fromSTEB(16, 16, 16, 120),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _GreetingHeader(periodDays: _periodDays),
              const SizedBox(height: 16),
              _HeroInsightCard(
                summary: summary,
                kpis: kpis,
                onDiscoverTap: _scrollToInsights,
                onChatTap: _openChat,
              ),
              const SizedBox(height: 24),
              ..._buildAnalyticsSection(summary, kpis),
              ..._buildInsightsSection(cards),
              const SizedBox(height: 24),
              _ActionPlan(cards: cards),
            ]),
          ),
        ),
      ],
    );
  }

  // ── Desktop layout ─────────────────────────────────────────────────────────
  Widget _buildWideLayout(
    SummaryResponse summary,
    List<InsightCard> cards,
    KpisResponse? kpis,
  ) {
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(20, 16, 20, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _GreetingHeader(periodDays: _periodDays),
          const SizedBox(height: 16),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  flex: 6,
                  child: SingleChildScrollView(
                    controller: _scrollController,
                    child: Column(
                      children: [
                        _HeroInsightCard(
                          summary: summary,
                          kpis: kpis,
                          onDiscoverTap: _scrollToInsights,
                          onChatTap: _openChat,
                        ),
                        const SizedBox(height: 24),
                        ..._buildAnalyticsSection(summary, kpis),
                        _ActionPlan(cards: cards),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 24),
                Expanded(
                  flex: 4,
                  child: SingleChildScrollView(
                    child: Column(
                      children: [
                        ..._buildInsightsSection(cards),
                        const SizedBox(height: 24),
                        _ChatCta(onTap: _openChat),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildAnalyticsSection(
    SummaryResponse summary,
    KpisResponse? kpis,
  ) {
    final agpData = summary.agpProfile.isNotEmpty
        ? summary.agpProfile
        : summary.dailyAverages;
    final useHourly = summary.agpProfile.isNotEmpty;
    return [
      if (kpis != null && kpis.hasSufficientData) ...[
        _KpiRow(kpis: kpis),
        const SizedBox(height: 16),
      ],
      if (agpData.isNotEmpty) ...[
        _AgpCard(
          agpData: agpData,
          isHourly: useHourly,
          periodDays: _periodDays,
          kpis: kpis,
        ),
        const SizedBox(height: 16),
      ],
    ];
  }

  List<Widget> _buildInsightsSection(List<InsightCard> cards) {
    return [
      _SectionHeader(
        title: 'ÉVÉNEMENTS CLÉS',
        subtitle: '${cards.length} priorité${cards.length > 1 ? 's' : ''}',
        icon: Icons.flag_outlined,
      ),
      const SizedBox(height: 12),
      if (cards.isEmpty)
        ClinicalCard(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: Text(
                'Aucune découverte pour le moment.',
                style: TextStyle(color: AminaTheme.textSecondary(context)),
              ),
            ),
          ),
        )
      else
        ...cards.map(
          (card) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _InsightCardWidget(card: card, onAskWhy: _openChat),
          ),
        ),
    ];
  }
}

// ─────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────
// Top Bar
// ─────────────────────────────────────────────────────────────────────────────

class _SummaryTopBar extends StatelessWidget {
  final int periodDays;
  final ValueChanged<int> onPeriodChange;
  final VoidCallback onTweaksTap;

  const _SummaryTopBar({
    required this.periodDays,
    required this.onPeriodChange,
    required this.onTweaksTap,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isCompact = MediaQuery.sizeOf(context).width < 600;
    return Container(
      padding: EdgeInsetsDirectional.fromSTEB(
        16,
        MediaQuery.of(context).padding.top + 10,
        16,
        0,
      ),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: Border(bottom: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  isCompact ? l10n.navIamina : l10n.breadcrumb,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: isCompact ? 15 : 13,
                    fontWeight: isCompact ? FontWeight.w800 : FontWeight.w600,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              Row(
                children: [
                  _PeriodTab(
                    label: '7 ${l10n.dayShort}',
                    days: 7,
                    selected: periodDays == 7,
                    onTap: onPeriodChange,
                  ),
                  const SizedBox(width: 4),
                  _PeriodTab(
                    label: '21 ${l10n.dayShort}',
                    days: 21,
                    selected: periodDays == 21,
                    onTap: onPeriodChange,
                  ),
                  const SizedBox(width: 4),
                  _PeriodTab(
                    label: '90 ${l10n.dayShort}',
                    days: 90,
                    selected: periodDays == 90,
                    onTap: onPeriodChange,
                  ),
                ],
              ),
              const SizedBox(width: 4),
            ],
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

class _PeriodTab extends StatelessWidget {
  final String label;
  final int days;
  final bool selected;
  final ValueChanged<int> onTap;
  const _PeriodTab({
    required this.label,
    required this.days,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(days),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? Colors.black : Colors.transparent,
          borderRadius: BorderRadius.circular(99),
          border: Border.all(
            color: selected ? Colors.black : AminaTheme.divider(context),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: selected ? Colors.white : AminaTheme.textSecondary(context),
          ),
        ),
      ),
    );
  }
}

class _GreetingHeader extends StatelessWidget {
  final int periodDays;
  const _GreetingHeader({required this.periodDays});

  /// Returns the user's first name from Firebase, or empty string if unknown.
  String _firstName() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || user.isAnonymous) return '';
    final display = user.displayName ?? '';
    if (display.isEmpty) return '';
    return display
        .split(RegExp(r'[\s@.]'))
        .firstWhere((p) => p.isNotEmpty, orElse: () => '');
  }

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final name = _firstName();
    final hour = DateTime.now().hour;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          copy.greeting(hour, name),
          style: TextStyle(
            fontSize: 32,
            fontWeight: FontWeight.w800,
            color: AminaTheme.textPrimary(context),
            letterSpacing: -1.0,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          copy.observation(periodDays),
          style: TextStyle(
            fontSize: 14,
            color: AminaTheme.textSecondary(context),
          ),
        ),
      ],
    );
  }
}

class _HeroInsightCard extends StatelessWidget {
  final SummaryResponse summary;
  final KpisResponse? kpis;
  final VoidCallback onDiscoverTap;
  final VoidCallback onChatTap;

  const _HeroInsightCard({
    required this.summary,
    required this.kpis,
    required this.onDiscoverTap,
    required this.onChatTap,
  });

  @override
  Widget build(BuildContext context) {
    final tir = kpis?.tirPct ?? 0.0;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        gradient: AminaTheme.heroGradient,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: AminaTheme.teal500.withValues(alpha: 0.3),
            blurRadius: 30,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(99),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.auto_awesome, color: Colors.white, size: 10),
                SizedBox(width: 6),
                Text(
                  'IAMINA INTELLIGENCE',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 9,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.8,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            tir >= 70
                ? 'Une majorité des mesures disponibles\nse situe dans le repère 70–180 mg/dL.'
                : 'Certaines mesures disponibles\nméritent d’être examinées.',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.w800,
              height: 1.1,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            '${summary.insightCards.length} observations prioritaires, ${summary.insightCards.where((c) => c.action.isNotEmpty).length} pistes à discuter. Basé sur ${kpis?.logCount ?? 0} mesures disponibles.',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.8),
              fontSize: 13,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 32),
          Row(
            children: [
              _HeroButton(
                label: 'Voir mes découvertes',
                onTap: onDiscoverTap,
                isPrimary: true,
              ),
              const SizedBox(width: 12),
              _HeroButton(
                label: 'Discuter avec IAmina',
                onTap: onChatTap,
                isPrimary: false,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final bool isPrimary;

  const _HeroButton({
    required this.label,
    required this.onTap,
    required this.isPrimary,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        decoration: BoxDecoration(
          color: isPrimary
              ? Colors.white
              : Colors.white.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isPrimary ? AminaTheme.teal700 : Colors.white,
            fontSize: 13,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// KPI Row
// ─────────────────────────────────────────────────────────────────────────────

class _KpiRow extends StatelessWidget {
  final KpisResponse kpis;
  const _KpiRow({required this.kpis});

  @override
  Widget build(BuildContext context) {
    final tir = kpis.tirPct ?? 0.0;
    final gmi = kpis.gmi ?? 0.0;
    final cv = kpis.cvPct ?? 0.0;
    final coverage =
        '${kpis.logCount} mesures sur ${kpis.daysWithData} jour${kpis.daysWithData > 1 ? 's' : ''}';

    final cards = <Widget>[
      _KpiCard(
        label: 'MESURES DANS LA CIBLE',
        value: '${tir.toStringAsFixed(0)}%',
        color: AminaTheme.teal500,
        reference: 'Repère général 70–180 mg/dL',
      ),
      _KpiCard(
        label: 'GMI ESTIMÉE',
        value: '${gmi.toStringAsFixed(1)}%',
        color: AminaTheme.ocean500,
        reference: kpis.gmiBasis.isNotEmpty
            ? '${kpis.gmiBasis} · estimation, pas HbA1c laboratoire'
            : 'Moyenne disponible · estimation, pas HbA1c laboratoire',
      ),
      _KpiCard(
        label: 'VARIABILITÉ (CV)',
        value: '${cv.toStringAsFixed(0)}%',
        color: AminaTheme.ambre500,
        reference: 'Repère général <36 %',
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < 720) {
              return Column(
                children: [
                  for (var index = 0; index < cards.length; index++) ...[
                    cards[index],
                    if (index < cards.length - 1) const SizedBox(height: 12),
                  ],
                ],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var index = 0; index < cards.length; index++) ...[
                  Expanded(child: cards[index]),
                  if (index < cards.length - 1) const SizedBox(width: 12),
                ],
              ],
            );
          },
        ),
        const SizedBox(height: 10),
        Text(
          'Repères généraux non personnalisés · $coverage. Les données manquantes peuvent modifier l’interprétation.',
          style: TextStyle(
            fontSize: 10.5,
            color: AminaTheme.textSecondary(context),
            height: 1.4,
          ),
        ),
      ],
    );
  }
}

class _KpiCard extends StatelessWidget {
  final String label, value, reference;
  final Color color;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.color,
    required this.reference,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsetsDirectional.fromSTEB(20, 22, 20, 20),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: AminaTheme.textSecondary(context),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: TextStyle(
              fontSize: 42,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
              letterSpacing: -1.5,
              height: 1.0,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            width: 28,
            height: 3,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(99),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            reference,
            style: TextStyle(
              fontSize: 10.5,
              color: AminaTheme.textSecondary(context),
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AGP Card — inchangée, dark-mode adapté
// ─────────────────────────────────────────────────────────────────────────────

class _AgpCard extends StatelessWidget {
  final List<dynamic> agpData;
  final bool isHourly;
  final int periodDays;
  final KpisResponse? kpis;

  const _AgpCard({
    required this.agpData,
    required this.isHourly,
    required this.periodDays,
    this.kpis,
  });

  @override
  Widget build(BuildContext context) {
    final hasData = agpData.any((e) {
      final m = e as Map<String, dynamic>;
      final v = (m['p50'] ?? m['avg'] ?? m['avg_glucose'] ?? 0);
      return (v as num) > 0;
    });
    final tir = kpis?.tirPct ?? 0.0;
    final tar = kpis?.tarPct ?? 0.0;
    final tbr = kpis?.tbrPct ?? 0.0;
    final vtar = (100 - tir - tar - tbr).clamp(0.0, 100.0);

    return ClinicalCard(
      padding: EdgeInsets.zero,
      backgroundColor: AminaTheme.surface(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(16, 14, 16, 0),
            child: Row(
              children: [
                const Icon(
                  Icons.show_chart,
                  size: 16,
                  color: AminaTheme.teal500,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'PROFIL GLYCÉMIQUE AMBULATOIRE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textSecondary(context),
                      letterSpacing: 0.6,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: AminaTheme.teal50,
                    borderRadius: BorderRadius.circular(99),
                  ),
                  child: Text(
                    '${periodDays}j',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AminaTheme.teal600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          if (kpis != null && kpis!.hasSufficientData)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: SizedBox(
                      height: 8,
                      child: Row(
                        children: [
                          if (tbr > 0)
                            Flexible(
                              flex: tbr.round(),
                              child: Container(color: AminaTheme.dangerFg),
                            ),
                          if (tir > 0)
                            Flexible(
                              flex: tir.round(),
                              child: Container(color: AminaTheme.teal500),
                            ),
                          if (tar > 0)
                            Flexible(
                              flex: tar.round(),
                              child: Container(color: AminaTheme.ambre500),
                            ),
                          if (vtar > 0)
                            Flexible(
                              flex: vtar.round(),
                              child: Container(
                                color: AminaTheme.dangerFg.withValues(
                                  alpha: 0.6,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      _TirLegend(
                        color: AminaTheme.teal500,
                        label: 'En cible',
                        value: '${tir.toStringAsFixed(0)}%',
                      ),
                      const SizedBox(width: 10),
                      _TirLegend(
                        color: AminaTheme.ambre500,
                        label: 'Élevé',
                        value: '${tar.toStringAsFixed(0)}%',
                      ),
                      const SizedBox(width: 10),
                      _TirLegend(
                        color: AminaTheme.dangerFg,
                        label: 'Bas',
                        value: '${tbr.toStringAsFixed(0)}%',
                      ),
                      const Spacer(),
                      Text(
                        'Objectif ADA > 70%',
                        style: TextStyle(
                          fontSize: 9,
                          color: tir >= 70
                              ? AminaTheme.teal500
                              : AminaTheme.textSecondary(context),
                        ),
                      ),
                      if (tir >= 70) ...[
                        const SizedBox(width: 4),
                        const Icon(
                          Icons.check_circle,
                          size: 11,
                          color: AminaTheme.teal500,
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 10),
                ],
              ),
            ),
          if (!hasData)
            Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(16, 0, 16, 16),
              child: Center(
                child: Text(
                  'Données insuffisantes.',
                  style: TextStyle(
                    color: AminaTheme.textSecondary(context),
                    fontSize: 12,
                  ),
                ),
              ),
            )
          else
            Builder(
              builder: (ctx) {
                final isDark = ctx.watch<TweaksNotifier>().isDark;
                // Parse server AGP points — filter out hours with no p50 data
                // Convert server Map data → canonical AgpPoint list
                const minY = 40.0;
                const maxY = 280.0;
                final pts = agpData
                    .map((e) => e as Map<String, dynamic>)
                    .where((m) => (m['p50'] ?? m['avg'] ?? 0) > 0)
                    .map((m) {
                      num v(String k) => m[k] as num? ?? 0;
                      final p50 = (v('p50') > 0 ? v('p50') : v('avg'))
                          .toDouble();
                      return AgpPoint(
                        hour: v('hour').toDouble(),
                        p5: v('p5').toDouble(),
                        p25: v('p25').toDouble(),
                        p50: p50,
                        p75: v('p75').toDouble(),
                        p95: v('p95').toDouble(),
                      );
                    })
                    .toList();
                return SizedBox(
                  height: 180,
                  child: Padding(
                    padding: const EdgeInsetsDirectional.fromSTEB(4, 0, 12, 0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Y-axis labels
                        SizedBox(
                          width: 30,
                          child: AgpYAxis(
                            minY: minY,
                            maxY: maxY,
                            isDark: isDark,
                          ),
                        ),
                        // Chart + X-axis
                        Expanded(
                          child: Column(
                            children: [
                              Expanded(
                                child: ClipRect(
                                  child: CustomPaint(
                                    painter: AgpPainter(
                                      points: pts,
                                      minY: minY,
                                      maxY: maxY,
                                      low: 70,
                                      high: 180,
                                      isDark: isDark,
                                    ),
                                  ),
                                ),
                              ),
                              if (isHourly)
                                SizedBox(
                                  height: 16,
                                  child: AgpXAxis(isDark: isDark),
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(16, 0, 16, 12),
            child: Row(
              children: [
                const _LegendDot(color: AminaTheme.teal700, label: 'Médiane'),
                const SizedBox(width: 10),
                _LegendDot(
                  color: AminaTheme.teal400.withValues(alpha: 0.55),
                  label: '25–75%',
                ),
                const SizedBox(width: 10),
                _LegendDot(
                  color: AminaTheme.teal400.withValues(alpha: 0.25),
                  label: '5–95%',
                ),
                const Spacer(),
                Text(
                  'Repère général 70–180',
                  style: TextStyle(
                    fontSize: 9,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        width: 10,
        height: 3,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
      const SizedBox(width: 4),
      Text(
        label,
        style: TextStyle(fontSize: 9, color: AminaTheme.textSecondary(context)),
      ),
    ],
  );
}

// _AgpSummaryPainter, _AgpSummaryYAxis, _AgpSummaryXAxis extracted to
// agp_chart.dart — use AgpPainter, AgpYAxis, AgpXAxis from that shared module.

class _TirLegend extends StatelessWidget {
  final Color color;
  final String label, value;
  const _TirLegend({
    required this.color,
    required this.label,
    required this.value,
  });
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 8,
        height: 8,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
      const SizedBox(width: 4),
      Text(
        '$label ',
        style: TextStyle(fontSize: 9, color: AminaTheme.textSecondary(context)),
      ),
      Text(
        value,
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    ],
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Action Plan (nouveau)
// ─────────────────────────────────────────────────────────────────────────────

class _ActionPlan extends StatelessWidget {
  final List<InsightCard> cards;
  const _ActionPlan({required this.cards});

  static Color _bgForSeverity(InsightSeverity s) => switch (s) {
    InsightSeverity.danger => AminaTheme.dangerBg,
    InsightSeverity.warn => AminaTheme.warnBg,
    InsightSeverity.good => AminaTheme.goodBg,
  };

  static Color _dotForSeverity(InsightSeverity s) => switch (s) {
    InsightSeverity.danger => const Color(0xFFDC2626),
    InsightSeverity.warn => const Color(0xFFF59E0B),
    InsightSeverity.good => AminaTheme.teal500,
  };

  @override
  Widget build(BuildContext context) {
    // Generate plan items from cards that have an action, up to 7
    final actionCards = cards
        .where((c) => c.action.isNotEmpty)
        .take(7)
        .toList();

    // Fallback static plans when no AI cards
    final List<_PlanItem> plans = actionCards.isEmpty
        ? [
            const _PlanItem(
              day: 'J+1',
              title: 'Documenter les repas glucidiques',
              sub: 'Ajouter le contexte et les horaires du repas',
              bg: AminaTheme.warnBg,
              dot: Color(0xFFF59E0B),
            ),
            const _PlanItem(
              day: 'J+3',
              title: 'Documenter les valeurs nocturnes',
              sub: 'Noter activité, sommeil et symptômes associés',
              bg: AminaTheme.dangerBg,
              dot: Color(0xFFDC2626),
            ),
            const _PlanItem(
              day: 'J+7',
              title: 'Préparer le bilan TIR',
              sub: 'Comparer les périodes avec votre professionnel',
              bg: AminaTheme.goodBg,
              dot: AminaTheme.teal500,
            ),
          ]
        : actionCards.asMap().entries.map((e) {
            final i = e.key;
            final card = e.value;
            final dayOffset = [1, 2, 3, 5, 6, 7, 7][i.clamp(0, 6)];
            return _PlanItem(
              day: 'J+$dayOffset',
              title: card.action,
              sub: card.body.length > 60
                  ? '${card.body.substring(0, 60)}…'
                  : card.body,
              bg: _bgForSeverity(card.severity),
              dot: _dotForSeverity(card.severity),
            );
          }).toList();

    final count = plans.length;
    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: AminaTheme.surface(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'POINTS À DISCUTER',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AminaTheme.textSecondary(context),
                        letterSpacing: 0.12,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$count point${count > 1 ? 's' : ''} à examiner sur 7 jours',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AminaTheme.textPrimary(context),
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  border: Border.all(color: AminaTheme.divider(context)),
                  borderRadius: BorderRadius.circular(99),
                ),
                child: Text(
                  'À discuter avec le médecin',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...plans.map(
            (p) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Container(
                padding: const EdgeInsetsDirectional.fromSTEB(14, 12, 14, 12),
                decoration: BoxDecoration(
                  color: p.bg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AminaTheme.divider(context)),
                ),
                child: Row(
                  children: [
                    // Day badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      margin: const EdgeInsetsDirectional.only(end: 12),
                      decoration: BoxDecoration(
                        color: p.dot.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        p.day,
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: p.dot,
                          letterSpacing: 0.06,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            p.title,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: AminaTheme.textPrimary(context),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            p.sub,
                            style: TextStyle(
                              fontSize: 11,
                              color: AminaTheme.textSecondary(context),
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(
                      Icons.info_outline,
                      size: 17,
                      color: AminaTheme.textSecondary(context),
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

class _PlanItem {
  final String day, title, sub;
  final Color bg;
  final Color dot;
  const _PlanItem({
    required this.day,
    required this.title,
    required this.sub,
    required this.bg,
    required this.dot,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Section header
// ─────────────────────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title, subtitle;
  final IconData icon;
  const _SectionHeader({
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(7),
          decoration: BoxDecoration(
            color: AminaTheme.teal50,
            borderRadius: BorderRadius.circular(9),
          ),
          child: Icon(icon, size: 14, color: AminaTheme.teal600),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: AminaTheme.textSecondary(context),
                  letterSpacing: 0.8,
                ),
              ),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 12,
                  color: AminaTheme.textSecondary(context),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Insight Card widget
// ─────────────────────────────────────────────────────────────────────────────

class _InsightCardWidget extends StatefulWidget {
  final InsightCard card;
  final VoidCallback onAskWhy;
  const _InsightCardWidget({required this.card, required this.onAskWhy});
  @override
  State<_InsightCardWidget> createState() => _InsightCardWidgetState();
}

class _InsightCardWidgetState extends State<_InsightCardWidget> {
  bool _expanded = true;

  @override
  Widget build(BuildContext context) {
    final InsightCard card = widget.card;
    final (
      barColor,
      bgColor,
      severityLabel,
      severityIcon,
    ) = switch (card.severity) {
      InsightSeverity.good => (
        AminaTheme.goodFg,
        AminaTheme.goodBg,
        'Positif',
        Icons.check_circle_outline,
      ),
      InsightSeverity.warn => (
        AminaTheme.warnFg,
        AminaTheme.warnBg,
        'À surveiller',
        Icons.radio_button_unchecked,
      ),
      InsightSeverity.danger => (
        AminaTheme.dangerFg,
        AminaTheme.dangerBg,
        'Priorité haute',
        Icons.warning_amber_rounded,
      ),
    };

    return ClinicalCard(
      padding: EdgeInsets.zero,
      backgroundColor: AminaTheme.surface(context),
      child: Column(
        children: [
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(AminaTheme.radius2XL),
            ),
            child: Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(16, 14, 12, 14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    margin: const EdgeInsetsDirectional.only(end: 12, top: 1),
                    decoration: BoxDecoration(
                      color: bgColor,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(severityIcon, size: 17, color: barColor),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          card.title,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: AminaTheme.textPrimary(context),
                            height: 1.3,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 7,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: bgColor,
                                borderRadius: BorderRadius.circular(99),
                              ),
                              child: Text(
                                severityLabel,
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: barColor,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Observation automatique',
                              style: TextStyle(
                                fontSize: 10,
                                color: AminaTheme.textSecondary(context),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                    size: 20,
                    color: AminaTheme.textSecondary(context),
                  ),
                ],
              ),
            ),
          ),
          AnimatedCrossFade(
            duration: const Duration(milliseconds: 200),
            crossFadeState: _expanded
                ? CrossFadeState.showFirst
                : CrossFadeState.showSecond,
            firstChild: Container(
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(color: AminaTheme.divider(context)),
                ),
              ),
              padding: const EdgeInsetsDirectional.fromSTEB(16, 14, 16, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    card.body,
                    style: TextStyle(
                      fontSize: 13,
                      color: AminaTheme.textSecondary(context),
                      height: 1.55,
                    ),
                  ),
                  if (card.action.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AminaTheme.teal50,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(
                            Icons.check_circle_outline,
                            size: 14,
                            color: AminaTheme.teal600,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Piste à discuter : ${card.action}',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: AminaTheme.teal700,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 14),
                  Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: TextButton.icon(
                      onPressed: widget.onAskWhy,
                      icon: const Icon(Icons.help_outline, size: 14),
                      label: const Text('Demander pourquoi'),
                      style: TextButton.styleFrom(
                        foregroundColor: AminaTheme.teal600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            secondChild: const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat CTA card + Chat FAB animé
// ─────────────────────────────────────────────────────────────────────────────

class _ChatCta extends StatelessWidget {
  final VoidCallback onTap;
  const _ChatCta({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AminaTheme.heroGradient,
        borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
        boxShadow: AminaTheme.shadowHero,
      ),
      child: Row(
        children: [
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Discuter avec IAmina',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Posez vos questions ou demandez une explication des données disponibles.',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white70,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          FilledButton(
            onPressed: onTap,
            style: FilledButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: AminaTheme.teal700,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              minimumSize: Size.zero,
            ),
            child: const Text(
              'Démarrer',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

/// FAB pulsant "Parler à IAmina" (floating)
class _ChatFab extends StatefulWidget {
  final VoidCallback onTap;
  const _ChatFab({required this.onTap});
  @override
  State<_ChatFab> createState() => _ChatFabState();
}

class _ChatFabState extends State<_ChatFab>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2600),
    )..repeat();
    _pulse = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulse,
      builder: (_, child) {
        final ripple = _pulse.value;
        return GestureDetector(
          onTap: widget.onTap,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 56 + ripple * 22,
                height: 56 + ripple * 22,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AminaTheme.teal500.withValues(
                    alpha: (1.0 - ripple) * 0.28,
                  ),
                ),
              ),
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  gradient: AminaTheme.heroGradient,
                  shape: BoxShape.circle,
                  boxShadow: AminaTheme.shadowFab,
                ),
                child: const Icon(
                  Icons.auto_awesome,
                  color: Colors.white,
                  size: 22,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Signal Bars + Pulse Animation (inchangés)
// ─────────────────────────────────────────────────────────────────────────────

class _PulseAnimation extends StatefulWidget {
  final Widget child;
  const _PulseAnimation({required this.child});
  @override
  State<_PulseAnimation> createState() => _PulseAnimationState();
}

class _PulseAnimationState extends State<_PulseAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;
  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    _scale = Tween<double>(
      begin: 0.92,
      end: 1.08,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      ScaleTransition(scale: _scale, child: widget.child);
}
