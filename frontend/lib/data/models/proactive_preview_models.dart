class ProactivePreviewPriority {
  final String safetyTimeSensitivity;
  final String clinicalRelevance;
  final String persistence;
  final double changeFromPersonalBaselineMgDl;
  final String evidenceDensity;
  final String actionability;
  final String evidenceMaturity;
  final String interruptionCost;

  const ProactivePreviewPriority({
    required this.safetyTimeSensitivity,
    required this.clinicalRelevance,
    required this.persistence,
    required this.changeFromPersonalBaselineMgDl,
    required this.evidenceDensity,
    required this.actionability,
    required this.evidenceMaturity,
    required this.interruptionCost,
  });

  factory ProactivePreviewPriority.fromJson(Map<String, dynamic> json) =>
      ProactivePreviewPriority(
        safetyTimeSensitivity:
            json['safety_time_sensitivity'] as String? ?? 'non_urgent_observation',
        clinicalRelevance:
            json['clinical_relevance'] as String? ?? 'observational',
        persistence: json['persistence'] as String? ?? 'monitoring_episode',
        changeFromPersonalBaselineMgDl:
            (json['change_from_personal_baseline_mg_dl'] as num?)?.toDouble() ?? 0,
        evidenceDensity: json['evidence_density'] as String? ?? 'limited',
        actionability: json['actionability'] as String? ?? 'MONITOR',
        evidenceMaturity: json['evidence_maturity'] as String? ?? '',
        interruptionCost: json['interruption_cost'] as String? ?? 'eligible',
      );
}

class ProactivePreviewItem {
  final String observationKey;
  final String kind;
  final String state;
  final bool surfaceNow;
  final String whatChanged;
  final String whyItIsSurfacingNow;
  final int evidenceWindowDays;
  final double personalBaselineComparisonMgDl;
  final int observations;
  final int distinctDays;
  final String evidenceDensity;
  final List<String> limitationsOrMissingData;
  final String allowedNextStep;
  final String escalationClass;
  final String evidenceId;
  final String sourceVersion;
  final ProactivePreviewPriority priority;

  const ProactivePreviewItem({
    required this.observationKey,
    required this.kind,
    required this.state,
    required this.surfaceNow,
    required this.whatChanged,
    required this.whyItIsSurfacingNow,
    required this.evidenceWindowDays,
    required this.personalBaselineComparisonMgDl,
    required this.observations,
    required this.distinctDays,
    required this.evidenceDensity,
    required this.limitationsOrMissingData,
    required this.allowedNextStep,
    required this.escalationClass,
    required this.evidenceId,
    required this.sourceVersion,
    required this.priority,
  });

  factory ProactivePreviewItem.fromJson(Map<String, dynamic> json) =>
      ProactivePreviewItem(
        observationKey: json['observation_key'] as String? ?? '',
        kind: json['kind'] as String? ?? '',
        state: json['state'] as String? ?? 'monitoring',
        surfaceNow: json['surface_now'] as bool? ?? false,
        whatChanged: json['what_changed'] as String? ?? '',
        whyItIsSurfacingNow: json['why_it_is_surfacing_now'] as String? ?? '',
        evidenceWindowDays: json['evidence_window_days'] as int? ?? 0,
        personalBaselineComparisonMgDl:
            (json['personal_baseline_comparison_mg_dl'] as num?)?.toDouble() ?? 0,
        observations: json['observations'] as int? ?? 0,
        distinctDays: json['distinct_days'] as int? ?? 0,
        evidenceDensity: json['evidence_density'] as String? ?? 'limited',
        limitationsOrMissingData:
            (json['limitations_or_missing_data'] as List? ?? const [])
                .whereType<String>()
                .toList(growable: false),
        allowedNextStep: json['allowed_next_step'] as String? ?? 'MONITOR',
        escalationClass: json['escalation_class'] as String? ?? 'none',
        evidenceId: json['evidence_id'] as String? ?? '',
        sourceVersion: json['source_version'] as String? ?? '',
        priority: ProactivePreviewPriority.fromJson(
          Map<String, dynamic>.from(json['priority'] as Map? ?? const {}),
        ),
      );
}

class ProactivePreview {
  final String status;
  final String attentionBudget;
  final DateTime? cooldownUntil;
  final int pendingCount;
  final String safetyNotice;
  final ProactivePreviewItem? item;

  const ProactivePreview({
    required this.status,
    required this.attentionBudget,
    required this.cooldownUntil,
    required this.pendingCount,
    required this.safetyNotice,
    required this.item,
  });

  factory ProactivePreview.fromJson(Map<String, dynamic> json) {
    final rawItem = json['item'];
    return ProactivePreview(
      status: json['status'] as String? ?? 'insufficient_data',
      attentionBudget:
          json['attention_budget'] as String? ?? 'one_non_urgent_item_per_24h',
      cooldownUntil: json['cooldown_until'] == null
          ? null
          : DateTime.tryParse(json['cooldown_until'] as String),
      pendingCount: json['pending_count'] as int? ?? 0,
      safetyNotice: json['safety_notice'] as String? ?? '',
      item: rawItem is Map
          ? ProactivePreviewItem.fromJson(Map<String, dynamic>.from(rawItem))
          : null,
    );
  }
}
