part of 'ai_summary_screen.dart';

extension _AISummaryScreenPresentation on _AISummaryScreenState {
  Widget _buildFirstUse() {
    final l10n = AppLocalizations.of(context)!;
    return SingleChildScrollView(
      padding: const EdgeInsetsDirectional.fromSTEB(20, 20, 20, 120),
      child: Align(
        alignment: AlignmentDirectional.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 820),
          child: AminaFirstUsePanel(
            icon: Icons.auto_graph_rounded,
            eyebrow: l10n.navIamina,
            title: l10n.emptyDashboardTitle,
            body: AuditedPageCopy.of(context).emptyAnalysis,
            primaryActionLabel: l10n.addFirstMeasurement,
            onPrimaryAction: () => context.go('/ajouter'),
            secondaryActionLabel: l10n.importDocument,
            onSecondaryAction: () => context.go('/importer'),
            note: l10n.firstUseTruthNote,
          ),
        ),
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
        final periodLabel = '$_periodDays ${l10n.dayShort}';
        final icon = Container(
          width: isWide ? 58 : 50,
          height: isWide ? 58 : 50,
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
        final periodChip = Container(
          padding: const EdgeInsetsDirectional.fromSTEB(10, 6, 10, 6),
          decoration: BoxDecoration(
            color: AminaTheme.bg(context),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AminaTheme.divider(context)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.calendar_today_outlined,
                size: 13,
                color: AminaTheme.textSecondary(context),
              ),
              const SizedBox(width: 6),
              Text(
                periodLabel,
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
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
        final copy = Column(
          crossAxisAlignment: isWide
              ? CrossAxisAlignment.start
              : CrossAxisAlignment.center,
          children: [
            Text(
              l10n.navIamina,
              textAlign: isWide ? TextAlign.start : TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                height: 1.2,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.18,
                color: AminaTheme.textSecondary(context),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.analysisLoadError,
              textAlign: isWide ? TextAlign.start : TextAlign.center,
              style: TextStyle(
                fontSize: isWide ? 20 : 16,
                height: 1.35,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(height: 14),
            periodChip,
          ],
        );

        return SingleChildScrollView(
          padding: EdgeInsetsDirectional.fromSTEB(
            isWide ? 28 : 20,
            isWide ? 22 : 28,
            isWide ? 28 : 20,
            28,
          ),
          child: Align(
            alignment: AlignmentDirectional.topStart,
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: isWide ? 960 : 520),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isWide) ...[
                    _GreetingHeader(periodDays: _periodDays),
                    const SizedBox(height: 18),
                  ],
                  Semantics(
                    container: true,
                    liveRegion: true,
                    label: l10n.analysisLoadError,
                    child: Container(
                      width: double.infinity,
                      padding: EdgeInsets.all(isWide ? 28 : 24),
                      decoration: BoxDecoration(
                        color: AminaTheme.surface(context),
                        borderRadius: BorderRadius.circular(
                          AminaTheme.radius2XL,
                        ),
                        border: Border.all(color: AminaTheme.divider(context)),
                        boxShadow: AminaTheme.shadowClinical,
                      ),
                      child: isWide
                          ? Row(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                icon,
                                const SizedBox(width: 20),
                                Expanded(child: copy),
                                const SizedBox(width: 28),
                                SizedBox(width: 190, child: retry),
                              ],
                            )
                          : Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                icon,
                                const SizedBox(height: 16),
                                copy,
                                const SizedBox(height: 20),
                                SizedBox(width: double.infinity, child: retry),
                              ],
                            ),
                    ),
                  ),
                ],
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
    final l10n = AppLocalizations.of(context)!;
    return [
      _SectionHeader(
        title: l10n.keyEvents,
        subtitle: l10n.priorities(cards.length),
        icon: Icons.flag_outlined,
      ),
      const SizedBox(height: 12),
      if (cards.isEmpty)
        ClinicalCard(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: Text(
                l10n.noDiscoveryYet,
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
