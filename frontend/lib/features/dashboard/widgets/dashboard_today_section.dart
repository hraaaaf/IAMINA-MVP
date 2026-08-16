import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/dashboard_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/models/companion_models.dart';
import '../../../services/companion_service.dart';

class DashboardTodaySection extends StatefulWidget {
  final bool targetConfigured;
  final CompanionService? service;

  const DashboardTodaySection({
    super.key,
    required this.targetConfigured,
    this.service,
  });

  @override
  State<DashboardTodaySection> createState() => _DashboardTodaySectionState();
}

class _DashboardTodaySectionState extends State<DashboardTodaySection> {
  late final CompanionService _service = widget.service ?? CompanionService();
  late Future<CompanionOverview?> _overviewFuture;

  @override
  void initState() {
    super.initState();
    _overviewFuture = _service.fetchOverview();
  }

  void _reload() {
    setState(() => _overviewFuture = _service.fetchOverview());
  }

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return FutureBuilder<CompanionOverview?>(
      future: _overviewFuture,
      builder: (context, snapshot) {
        final signals = _signals(l10n, snapshot.data);
        final loading = snapshot.connectionState != ConnectionState.done;
        final overviewResolved = snapshot.connectionState == ConnectionState.done;
        final unavailable = overviewResolved && snapshot.data == null;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.dashboardTodayHeading,
              style: TextStyle(
                fontFamily: 'Georgia',
                fontSize: 21,
                height: 1.05,
                fontWeight: FontWeight.w700,
                letterSpacing: -.35,
                color: AminaVisualLanguage.primaryText(context),
              ),
            ),
            const SizedBox(height: 10),
            if (signals.isNotEmpty)
              ...signals.map((signal) => _TodaySignalCard(signal: signal)),
            if (loading)
              _TodayStateStrip(
                loading: true,
                text: l10n.dashboardTodayLoading,
              )
            else if (unavailable)
              _TodayStateStrip(
                icon: Icons.cloud_off_outlined,
                text: l10n.dashboardTodayUnavailable,
                actionLabel: l10n.dashboardRetry,
                onAction: _reload,
              )
            else if (signals.isEmpty && snapshot.data != null)
              _TodaySignalCard(
                signal: _TodaySignal(
                  icon: Icons.check_circle_outline_rounded,
                  title: l10n.dashboardNoGovernedHighlight,
                  actionLabel: l10n.dashboardOpenCompanion,
                  onTap: () => context.go('/companion'),
                ),
              ),
            const SizedBox(height: 2),
            const _SecondaryActions(),
            const SizedBox(height: 10),
            const _TrustStrip(),
          ],
        );
      },
    );
  }

  List<_TodaySignal> _signals(
    AppLocalizations l10n,
    CompanionOverview? overview,
  ) {
    final signals = <_TodaySignal>[];

    if (!widget.targetConfigured) {
      signals.add(
        _TodaySignal(
          icon: Icons.tune_rounded,
          title: l10n.dashboardConfigureTargetSignal,
          actionLabel: l10n.dashboardConfigureTargetAction,
          onTap: () => context.go('/profile'),
        ),
      );
    }

    if (overview != null) {
      final determinateChangeCount = overview.changesSinceReview
          .where((change) => change.changeKind != 'unknown')
          .length;
      if (overview.reviewStatus == 'ready' && determinateChangeCount > 0) {
        signals.add(
          _TodaySignal(
            icon: Icons.change_circle_outlined,
            title: l10n.dashboardGovernedChanges(determinateChangeCount),
            actionLabel: l10n.dashboardOpenCompanion,
            onTap: () => context.go('/companion'),
          ),
        );
      } else if (overview.patternStatus == 'ready' &&
          overview.patterns.isNotEmpty) {
        signals.add(
          _TodaySignal(
            icon: Icons.auto_graph_rounded,
            title: l10n.dashboardGovernedPatterns(overview.patterns.length),
            actionLabel: l10n.dashboardOpenCompanion,
            onTap: () => context.go('/companion'),
          ),
        );
      }
    }

    return signals.take(2).toList(growable: false);
  }
}

class _TodaySignal {
  final IconData icon;
  final String title;
  final String actionLabel;
  final VoidCallback onTap;

  const _TodaySignal({
    required this.icon,
    required this.title,
    required this.actionLabel,
    required this.onTap,
  });
}

class _TodaySignalCard extends StatelessWidget {
  final _TodaySignal signal;
  const _TodaySignalCard({required this.signal});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: signal.onTap,
          borderRadius: BorderRadius.circular(18),
          child: Ink(
            padding: const EdgeInsetsDirectional.fromSTEB(14, 12, 10, 12),
            decoration: AminaVisualLanguage.cardDecoration(context, radius: 18),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: AminaVisualLanguage.mintIconDecoration(context),
                  child: Icon(
                    signal.icon,
                    color: AminaVisualLanguage.actionGreen,
                    size: 19,
                  ),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: Text(
                    signal.title,
                    style: TextStyle(
                      fontSize: 12.5,
                      height: 1.35,
                      fontWeight: FontWeight.w700,
                      color: AminaVisualLanguage.primaryText(context),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Semantics(
                  label: signal.actionLabel,
                  child: const Icon(
                    Icons.arrow_forward_ios_rounded,
                    color: AminaVisualLanguage.actionGreen,
                    size: 15,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TodayStateStrip extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String text;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _TodayStateStrip({
    this.loading = false,
    this.icon,
    required this.text,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 8, 10),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Row(
        children: [
          if (loading)
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            Icon(
              icon ?? Icons.info_outline_rounded,
              size: 18,
              color: AminaVisualLanguage.actionGreen,
            ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 11.5,
                height: 1.35,
                fontWeight: FontWeight.w600,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(width: 6),
            TextButton(
              key: const ValueKey('dashboard-today-retry'),
              onPressed: onAction,
              child: Text(actionLabel!),
            ),
          ],
        ],
      ),
    );
  }
}

class _SecondaryActions extends StatelessWidget {
  const _SecondaryActions();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            key: const ValueKey('dashboard-secondary-companion'),
            onPressed: () => context.go('/companion'),
            icon: const Icon(Icons.auto_awesome_rounded, size: 17),
            label: Text(l10n.dashboardOpenCompanion),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: OutlinedButton.icon(
            key: const ValueKey('dashboard-secondary-import'),
            onPressed: () => context.go('/importer'),
            icon: const Icon(Icons.upload_file_outlined, size: 17),
            label: Text(l10n.dashboardImportData),
          ),
        ),
      ],
    );
  }
}

class _TrustStrip extends StatelessWidget {
  const _TrustStrip();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .62),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AminaVisualLanguage.mintBorder.withValues(alpha: .72),
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.shield_outlined,
            color: AminaVisualLanguage.actionGreen,
            size: 17,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              l10n.dashboardGovernedTrustShort,
              style: TextStyle(
                fontSize: 11,
                height: 1.3,
                fontWeight: FontWeight.w600,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
