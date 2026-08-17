class CompanionNextActionSuggestion {
  final String suggestionClass;
  final String observationKey;
  final String reason;
  final String proactiveState;
  final String? changeSinceReview;
  final List<String> missingData;
  final List<String> limitations;
  final String proactiveSourceVersion;
  final String patternSourceVersion;
  final String sourceVersion;

  const CompanionNextActionSuggestion({
    required this.suggestionClass,
    required this.observationKey,
    required this.reason,
    required this.proactiveState,
    required this.changeSinceReview,
    required this.missingData,
    required this.limitations,
    required this.proactiveSourceVersion,
    required this.patternSourceVersion,
    required this.sourceVersion,
  });

  factory CompanionNextActionSuggestion.fromJson(Map<String, dynamic> json) =>
      CompanionNextActionSuggestion(
        suggestionClass: json['suggestion_class'] as String? ?? '',
        observationKey: json['observation_key'] as String? ?? '',
        reason: json['reason'] as String? ?? '',
        proactiveState: json['proactive_state'] as String? ?? '',
        changeSinceReview: json['change_since_review'] as String?,
        missingData: (json['missing_data'] as List? ?? const [])
            .whereType<String>()
            .toList(growable: false),
        limitations: (json['limitations'] as List? ?? const [])
            .whereType<String>()
            .toList(growable: false),
        proactiveSourceVersion:
            json['proactive_source_version'] as String? ?? '',
        patternSourceVersion: json['pattern_source_version'] as String? ?? '',
        sourceVersion: json['source_version'] as String? ?? '',
      );
}

class CompanionNextAction {
  final String status;
  final String attentionBudget;
  final int pendingCount;
  final String safetyNotice;
  final CompanionNextActionSuggestion? suggestion;

  const CompanionNextAction({
    required this.status,
    required this.attentionBudget,
    required this.pendingCount,
    required this.safetyNotice,
    required this.suggestion,
  });

  factory CompanionNextAction.fromJson(Map<String, dynamic> json) {
    final rawSuggestion = json['suggestion'];
    return CompanionNextAction(
      status: json['status'] as String? ?? 'insufficient_data',
      attentionBudget:
          json['attention_budget'] as String? ?? 'one_non_urgent_item_per_24h',
      pendingCount: json['pending_count'] as int? ?? 0,
      safetyNotice: json['safety_notice'] as String? ?? '',
      suggestion: rawSuggestion is Map
          ? CompanionNextActionSuggestion.fromJson(
              Map<String, dynamic>.from(rawSuggestion),
            )
          : null,
    );
  }
}
