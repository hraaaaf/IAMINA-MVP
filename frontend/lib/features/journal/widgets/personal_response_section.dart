import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/clinical_card.dart';
import '../../../data/models/personal_response_models.dart';
import '../../../l10n/app_localizations.dart';
import '../../../services/api_client.dart';

class PersonalResponseSection extends StatefulWidget {
  final String unit;
  final Future<PersonalResponseResult?> Function()? loader;

  const PersonalResponseSection({super.key, required this.unit, this.loader});

  @override
  State<PersonalResponseSection> createState() =>
      _PersonalResponseSectionState();
}

class _PersonalResponseSectionState extends State<PersonalResponseSection> {
  late Future<PersonalResponseResult?> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<PersonalResponseResult?> _load() {
    return widget.loader?.call() ?? ApiClient().getPersonalResponse();
  }

  @override
  void didUpdateWidget(covariant PersonalResponseSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.loader != widget.loader) {
      _future = _load();
    }
  }

  String _formatGlucose(double mgDl) {
    if (widget.unit == 'mmol/L') {
      return (mgDl / 18.0).toStringAsFixed(1);
    }
    return mgDl.round().toString();
  }

  String _labelForPattern(
    PersonalResponsePattern pattern,
    AppLocalizations l10n,
  ) {
    switch (pattern.key) {
      case 'context:stress':
        return l10n.personalResponseStress;
      case 'context:activity':
        return l10n.personalResponseActivity;
      case 'context:illness':
        return l10n.personalResponseIllness;
      case 'context:poor_sleep':
        return l10n.personalResponsePoorSleep;
      case 'context:fatigue':
        return l10n.personalResponseFatigue;
      case 'meal:breakfast':
        return l10n.personalResponseBreakfast;
      case 'meal:lunch':
        return l10n.personalResponseLunch;
      case 'meal:dinner':
        return l10n.personalResponseDinner;
      case 'meal:snack':
        return l10n.personalResponseSnack;
      case 'meal:suhoor':
        return l10n.personalResponseSuhoor;
      case 'meal:iftar':
        return l10n.personalResponseIftar;
      default:
        return l10n.personalResponseObservedPattern;
    }
  }

  String _confidenceLabel(String confidence, AppLocalizations l10n) {
    switch (confidence) {
      case 'strong':
        return l10n.personalResponseEvidenceStrong;
      case 'moderate':
        return l10n.personalResponseEvidenceModerate;
      default:
        return l10n.personalResponseEvidenceLimited;
    }
  }

  Color _confidenceColor(String confidence) {
    switch (confidence) {
      case 'strong':
        return AminaTheme.successEmerald;
      case 'moderate':
        return AminaTheme.primaryTeal;
      default:
        return AminaTheme.accentAmber;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return FutureBuilder<PersonalResponseResult?>(
      future: _future,
      builder: (context, snapshot) {
        return ClinicalCard(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AminaTheme.primaryTeal.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.insights_outlined,
                      color: AminaTheme.primaryTeal,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l10n.personalResponseTitle,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: AminaTheme.textDark,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          l10n.personalResponseSubtitle,
                          style: const TextStyle(
                            fontSize: 12,
                            height: 1.35,
                            color: AminaTheme.ink500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (snapshot.connectionState == ConnectionState.waiting)
                const _ResponseSkeleton()
              else if (snapshot.hasError || snapshot.data == null)
                _InfoState(
                  icon: Icons.cloud_off_outlined,
                  title: l10n.personalResponseUnavailable,
                  body: l10n.personalResponseUnavailableBody,
                )
              else if (!snapshot.data!.hasPatterns)
                _InfoState(
                  icon: Icons.timeline_outlined,
                  title: l10n.personalResponseInsufficient,
                  body: l10n.personalResponseMinimumBasis(
                    snapshot.data!.minimumObservations,
                    snapshot.data!.minimumDistinctDays,
                  ),
                )
              else ...[
                ...snapshot.data!.patterns
                    .take(3)
                    .map(
                      (pattern) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _PatternCard(
                          title: _labelForPattern(pattern, l10n),
                          evidenceBasis: l10n.personalResponseEvidenceBasis(
                            pattern.observations,
                            pattern.distinctDays,
                          ),
                          confidenceLabel: _confidenceLabel(
                            pattern.confidence,
                            l10n,
                          ),
                          confidenceColor: _confidenceColor(pattern.confidence),
                          patternMedianLabel:
                              l10n.personalResponsePatternMedian,
                          patternMedian: _formatGlucose(
                            pattern.medianGlucoseMgDl,
                          ),
                          windowMedianLabel: l10n.personalResponseWindowMedian(
                            snapshot.data!.windowDays,
                          ),
                          windowMedian: _formatGlucose(
                            pattern.windowMedianGlucoseMgDl,
                          ),
                          unit: widget.unit,
                        ),
                      ),
                    ),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AminaTheme.primaryTeal.withValues(alpha: 0.06),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        l10n.personalResponseCausalityNotice,
                        style: const TextStyle(
                          fontSize: 11.5,
                          height: 1.45,
                          color: AminaTheme.ink700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        l10n.personalResponseConfidenceNotice,
                        style: const TextStyle(
                          fontSize: 11,
                          height: 1.4,
                          color: AminaTheme.ink500,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.sync_outlined,
                    size: 14,
                    color: AminaTheme.ink500,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      l10n.personalResponseSyncedScope,
                      style: const TextStyle(
                        fontSize: 10.5,
                        height: 1.35,
                        color: AminaTheme.ink500,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _PatternCard extends StatelessWidget {
  final String title;
  final String evidenceBasis;
  final String confidenceLabel;
  final Color confidenceColor;
  final String patternMedianLabel;
  final String patternMedian;
  final String windowMedianLabel;
  final String windowMedian;
  final String unit;

  const _PatternCard({
    required this.title,
    required this.evidenceBasis,
    required this.confidenceLabel,
    required this.confidenceColor,
    required this.patternMedianLabel,
    required this.patternMedian,
    required this.windowMedianLabel,
    required this.windowMedian,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.ink50,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.ink100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13.5,
                  fontWeight: FontWeight.w800,
                  color: AminaTheme.ink900,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: confidenceColor.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  confidenceLabel,
                  style: TextStyle(
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    color: confidenceColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          Text(
            evidenceBasis,
            style: const TextStyle(
              fontSize: 11,
              color: AminaTheme.ink500,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          _MetricLine(
            label: patternMedianLabel,
            value: patternMedian,
            unit: unit,
          ),
          const SizedBox(height: 8),
          _MetricLine(
            label: windowMedianLabel,
            value: windowMedian,
            unit: unit,
          ),
        ],
      ),
    );
  }
}

class _MetricLine extends StatelessWidget {
  final String label;
  final String value;
  final String unit;

  const _MetricLine({
    required this.label,
    required this.value,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 11.5,
              height: 1.3,
              color: AminaTheme.ink700,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Directionality(
          textDirection: TextDirection.ltr,
          child: Text(
            '$value $unit',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: AminaTheme.ink900,
            ),
          ),
        ),
      ],
    );
  }
}

class _InfoState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;

  const _InfoState({
    required this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.ink50,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: AminaTheme.ink500),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w700,
                    color: AminaTheme.ink900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: const TextStyle(
                    fontSize: 11.5,
                    height: 1.4,
                    color: AminaTheme.ink500,
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

class _ResponseSkeleton extends StatelessWidget {
  const _ResponseSkeleton();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 82,
      decoration: BoxDecoration(
        color: AminaTheme.ink50,
        borderRadius: BorderRadius.circular(14),
      ),
      alignment: Alignment.center,
      child: const SizedBox(
        width: 22,
        height: 22,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
    );
  }
}
