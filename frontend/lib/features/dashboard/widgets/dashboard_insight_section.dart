import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/dashboard_insight_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/models/proactive_preview_models.dart';
import '../../../services/companion_service.dart';

class DashboardInsightSection extends StatefulWidget {
  final CompanionService? service;

  const DashboardInsightSection({super.key, this.service});

  @override
  State<DashboardInsightSection> createState() => _DashboardInsightSectionState();
}

class _DashboardInsightSectionState extends State<DashboardInsightSection> {
  late final CompanionService _service = widget.service ?? CompanionService();
  late Future<ProactivePreview?> _future = _service.fetchProactivePreview();

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  void _reload() => setState(() => _future = _service.fetchProactivePreview());

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: AminaVisualLanguage.cardDecoration(context, radius: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.dashboardInsightHeading,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontSize: 21,
              height: 1.05,
              fontWeight: FontWeight.w700,
              letterSpacing: -.35,
              color: AminaVisualLanguage.primaryText(context),
            ),
          ),
          const SizedBox(height: 5),
          Text(
            l10n.dashboardInsightSubheading,
            style: TextStyle(
              fontSize: 11.5,
              height: 1.35,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          const SizedBox(height: 14),
          FutureBuilder<ProactivePreview?>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return _InsightState(
                  loading: true,
                  text: l10n.dashboardInsightLoading,
                );
              }

              final preview = snapshot.data;
              if (preview == null) {
                return _InsightState(
                  icon: Icons.cloud_off_outlined,
                  text: l10n.dashboardInsightUnavailable,
                  actionLabel: l10n.dashboardInsightRetry,
                  onAction: _reload,
                );
              }

              if (preview.status == 'insufficient_data') {
                return _InsightState(
                  icon: Icons.hourglass_empty_rounded,
                  text: l10n.dashboardInsightInsufficient,
                );
              }
              if (preview.status == 'cooldown') {
                return _InsightState(
                  icon: Icons.self_improvement_rounded,
                  text: l10n.dashboardInsightCooldown,
                );
              }
              if (preview.status == 'no_change') {
                return _InsightState(
                  icon: Icons.check_circle_outline_rounded,
                  text: l10n.dashboardInsightNoChange,
                );
              }

              final item = preview.item;
              if (preview.status != 'available' || item == null) {
                return _InsightState(
                  icon: Icons.info_outline_rounded,
                  text: l10n.dashboardInsightInsufficient,
                );
              }
              return _InsightBody(item: item);
            },
          ),
        ],
      ),
    );
  }
}

class _InsightBody extends StatelessWidget {
  final ProactivePreviewItem item;

  const _InsightBody({required this.item});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: AminaVisualLanguage.mintIconDecoration(context),
              child: const Icon(
                Icons.auto_awesome_rounded,
                size: 20,
                color: AminaVisualLanguage.actionGreen,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.dashboardInsightEyebrow,
                    style: const TextStyle(
                      color: AminaVisualLanguage.actionGreen,
                      fontSize: 9.8,
                      fontWeight: FontWeight.w800,
                      letterSpacing: .9,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    l10n.dashboardInsightObservationLabel(item.observationKey),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AminaVisualLanguage.primaryText(context),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _EvidencePill(value: item.evidenceDensity),
          ],
        ),
        const SizedBox(height: 13),
        Text(
          l10n.dashboardInsightChangeLabel(item.whatChanged),
          style: TextStyle(
            fontSize: 13,
            height: 1.45,
            fontWeight: FontWeight.w600,
            color: AminaVisualLanguage.primaryText(context),
          ),
        ),
        const SizedBox(height: 14),
        Text(
          l10n.dashboardInsightEvidenceTitle,
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
        const SizedBox(height: 7),
        Wrap(
          spacing: 7,
          runSpacing: 7,
          children: [
            _ProofChip(
              icon: Icons.format_list_numbered_rounded,
              label: l10n.dashboardInsightObservationCount(item.observations),
            ),
            _ProofChip(
              icon: Icons.calendar_today_outlined,
              label: l10n.dashboardInsightDayCount(item.distinctDays),
            ),
            _ProofChip(
              icon: Icons.date_range_outlined,
              label: l10n.dashboardInsightWindow(item.evidenceWindowDays),
            ),
          ],
        ),
        const SizedBox(height: 14),
        Container(
          width: double.infinity,
          padding: const EdgeInsetsDirectional.fromSTEB(12, 11, 12, 11),
          decoration: BoxDecoration(
            color: AminaVisualLanguage.mintSurface.withValues(alpha: .62),
            borderRadius: BorderRadius.circular(15),
            border: Border.all(
              color: AminaVisualLanguage.mintBorder.withValues(alpha: .82),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                l10n.dashboardInsightAllowedAction,
                style: const TextStyle(
                  color: AminaVisualLanguage.actionGreen,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                l10n.dashboardInsightAction(item.allowedNextStep),
                style: TextStyle(
                  fontSize: 12.2,
                  height: 1.35,
                  fontWeight: FontWeight.w800,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.info_outline_rounded,
              size: 15,
              color: AminaVisualLanguage.secondary(context),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                l10n.dashboardInsightLimitation,
                style: TextStyle(
                  fontSize: 10.7,
                  height: 1.38,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 13),
        SizedBox(
          width: double.infinity,
          height: 44,
          child: OutlinedButton.icon(
            onPressed: () => context.go('/companion'),
            icon: const Icon(Icons.arrow_forward_rounded, size: 17),
            label: Text(l10n.dashboardInsightSeeEvidence),
            style: OutlinedButton.styleFrom(
              foregroundColor: AminaVisualLanguage.actionGreen,
              side: BorderSide(color: AminaVisualLanguage.mintBorder),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(
                  AminaVisualLanguage.controlRadius,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _EvidencePill extends StatelessWidget {
  final String value;

  const _EvidencePill({required this.value});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.mintSurface,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        l10n.dashboardInsightEvidenceStrength(value),
        style: const TextStyle(
          color: AminaVisualLanguage.actionGreen,
          fontSize: 10.2,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _ProofChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _ProofChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(9, 7, 9, 7),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AminaVisualLanguage.actionGreen),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              fontSize: 10.4,
              fontWeight: FontWeight.w700,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ],
      ),
    );
  }
}

class _InsightState extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String text;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _InsightState({
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
      constraints: const BoxConstraints(minHeight: 116),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaVisualLanguage.controlSurface(context),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AminaVisualLanguage.controlBorder(context)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (loading)
            const SizedBox(
              width: 23,
              height: 23,
              child: CircularProgressIndicator(strokeWidth: 2.1),
            )
          else
            Icon(
              icon ?? Icons.info_outline_rounded,
              size: 23,
              color: AminaVisualLanguage.actionGreen,
            ),
          const SizedBox(height: 9),
          Text(
            text,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 11.5,
              height: 1.38,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 10),
            TextButton.icon(
              onPressed: onAction,
              icon: const Icon(Icons.refresh_rounded, size: 16),
              label: Text(actionLabel!),
            ),
          ],
        ],
      ),
    );
  }
}
