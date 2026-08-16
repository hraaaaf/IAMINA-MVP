import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/localization/dashboard_next_action_localized_copy.dart';
import '../../../core/theme/amina_visual_language.dart';
import '../../../data/models/companion_next_action_models.dart';
import '../../../services/companion_service.dart';

class DashboardNextActionSection extends StatefulWidget {
  final CompanionService? service;

  const DashboardNextActionSection({super.key, this.service});

  @override
  State<DashboardNextActionSection> createState() =>
      _DashboardNextActionSectionState();
}

class _DashboardNextActionSectionState
    extends State<DashboardNextActionSection> {
  late final CompanionService _service = widget.service ?? CompanionService();
  CompanionNextAction? _result;
  bool _loading = false;
  bool _failed = false;

  @override
  void dispose() {
    if (widget.service == null) _service.dispose();
    super.dispose();
  }

  Future<void> _evaluate() async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _failed = false;
    });
    final result = await _service.evaluateNextAction();
    if (!mounted) return;
    setState(() {
      _loading = false;
      _failed = result == null;
      _result = result;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AminaVisualLanguage.mintSurface.withValues(alpha: .78),
            AminaVisualLanguage.controlSurface(context),
          ],
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AminaVisualLanguage.mintBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: AminaVisualLanguage.mintIconDecoration(context),
                child: const Icon(
                  Icons.near_me_outlined,
                  size: 19,
                  color: AminaVisualLanguage.actionGreen,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  l10n.dashboardNextActionHeading,
                  style: TextStyle(
                    fontFamily: 'Georgia',
                    fontSize: 21,
                    height: 1.05,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -.35,
                    color: AminaVisualLanguage.primaryText(context),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          if (_loading)
            _StateBody(
              loading: true,
              text: l10n.dashboardNextActionLoading,
            )
          else if (_failed)
            _StateBody(
              icon: Icons.cloud_off_outlined,
              text: l10n.dashboardNextActionUnavailable,
              actionLabel: l10n.dashboardNextActionRetry,
              onAction: _evaluate,
            )
          else if (_result == null)
            _IdleBody(onPrepare: _evaluate)
          else
            _ResultBody(result: _result!, onRetry: _evaluate),
        ],
      ),
    );
  }
}

class _IdleBody extends StatelessWidget {
  final VoidCallback onPrepare;

  const _IdleBody({required this.onPrepare});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.dashboardNextActionIntro,
          style: TextStyle(
            fontSize: 11.8,
            height: 1.42,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
        const SizedBox(height: 13),
        SizedBox(
          width: double.infinity,
          height: 46,
          child: FilledButton.icon(
            onPressed: onPrepare,
            icon: const Icon(Icons.auto_awesome_rounded, size: 18),
            label: Text(l10n.dashboardNextActionPrepare),
            style: FilledButton.styleFrom(
              backgroundColor: AminaVisualLanguage.forestDeep,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(
                  AminaVisualLanguage.controlRadius,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 9),
        _SafetyCopy(text: l10n.dashboardNextActionSafety),
      ],
    );
  }
}

class _ResultBody extends StatelessWidget {
  final CompanionNextAction result;
  final VoidCallback onRetry;

  const _ResultBody({required this.result, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final suggestion = result.suggestion;

    if (result.status == 'cooldown') {
      return _StateBody(
        icon: Icons.self_improvement_rounded,
        text: l10n.dashboardNextActionCooldown,
      );
    }
    if (result.status == 'no_change') {
      return _StateBody(
        icon: Icons.check_circle_outline_rounded,
        text: l10n.dashboardNextActionNoChange,
      );
    }
    if (result.status == 'insufficient_data') {
      return _StateBody(
        icon: Icons.hourglass_empty_rounded,
        text: l10n.dashboardNextActionInsufficient,
      );
    }
    if (result.status != 'suggested' || suggestion == null) {
      return _StateBody(
        icon: Icons.info_outline_rounded,
        text: l10n.dashboardNextActionUnavailable,
        actionLabel: l10n.dashboardNextActionRetry,
        onAction: onRetry,
      );
    }

    final allowed = const {
      'UNDERSTAND_DATA',
      'MONITOR',
      'PREPARE_CLINICIAN_DISCUSSION',
    }.contains(suggestion.suggestionClass);
    if (!allowed) {
      return _StateBody(
        icon: Icons.lock_outline_rounded,
        text: l10n.dashboardNextActionUnavailable,
      );
    }

    final route = suggestion.suggestionClass == 'MONITOR' ? '/journal' : '/companion';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.dashboardNextActionTitle(suggestion.suggestionClass),
          style: TextStyle(
            fontSize: 16,
            height: 1.2,
            fontWeight: FontWeight.w800,
            color: AminaVisualLanguage.primaryText(context),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          l10n.dashboardNextActionBody(suggestion.suggestionClass),
          style: TextStyle(
            fontSize: 11.8,
            height: 1.42,
            color: AminaVisualLanguage.secondary(context),
          ),
        ),
        const SizedBox(height: 13),
        SizedBox(
          width: double.infinity,
          height: 46,
          child: FilledButton.icon(
            onPressed: () => context.go(route),
            icon: Icon(
              suggestion.suggestionClass == 'MONITOR'
                  ? Icons.timeline_rounded
                  : Icons.arrow_forward_rounded,
              size: 18,
            ),
            label: Text(
              l10n.dashboardNextActionOpenLabel(suggestion.suggestionClass),
            ),
            style: FilledButton.styleFrom(
              backgroundColor: AminaVisualLanguage.forestDeep,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(
                  AminaVisualLanguage.controlRadius,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 9),
        _SafetyCopy(text: l10n.dashboardNextActionSafety),
      ],
    );
  }
}

class _SafetyCopy extends StatelessWidget {
  final String text;

  const _SafetyCopy({required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          Icons.shield_outlined,
          size: 14,
          color: AminaVisualLanguage.secondary(context),
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 9.8,
              height: 1.35,
              color: AminaVisualLanguage.secondary(context),
            ),
          ),
        ),
      ],
    );
  }
}

class _StateBody extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String text;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _StateBody({
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
      constraints: const BoxConstraints(minHeight: 104),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (loading)
            const SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(strokeWidth: 2.1),
            )
          else
            Icon(
              icon ?? Icons.info_outline_rounded,
              size: 22,
              color: AminaVisualLanguage.actionGreen,
            ),
          const SizedBox(height: 8),
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
            const SizedBox(height: 8),
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
