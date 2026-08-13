class CompanionPattern {
  final String observationKey;
  final String currentState;
  final List<String> markers;
  final String evidenceDensity;
  final int recurrenceCount;
  final String baselineDirection;
  final String baselineMovement;
  final DateTime firstObservedAt;
  final DateTime lastObservedAt;
  final String evidenceId;
  final List<String> limitations;

  const CompanionPattern({
    required this.observationKey,
    required this.currentState,
    required this.markers,
    required this.evidenceDensity,
    required this.recurrenceCount,
    required this.baselineDirection,
    required this.baselineMovement,
    required this.firstObservedAt,
    required this.lastObservedAt,
    required this.evidenceId,
    required this.limitations,
  });

  factory CompanionPattern.fromJson(Map<String, dynamic> json) => CompanionPattern(
    observationKey: json['observation_key'] as String? ?? '',
    currentState: json['current_state'] as String? ?? 'unknown',
    markers: (json['markers'] as List? ?? const []).whereType<String>().toList(),
    evidenceDensity: json['evidence_density'] as String? ?? 'limited',
    recurrenceCount: json['recurrence_count'] as int? ?? 0,
    baselineDirection: json['baseline_direction'] as String? ?? 'unknown',
    baselineMovement: json['baseline_movement'] as String? ?? 'initial_or_unknown',
    firstObservedAt: DateTime.parse(json['first_observed_at'] as String),
    lastObservedAt: DateTime.parse(json['last_observed_at'] as String),
    evidenceId: json['evidence_id'] as String? ?? '',
    limitations: (json['limitations'] as List? ?? const []).whereType<String>().toList(),
  );
}

class CompanionChange {
  final String observationKey;
  final String changeKind;
  final String evidenceStrength;
  final List<String> missingData;

  const CompanionChange({
    required this.observationKey,
    required this.changeKind,
    required this.evidenceStrength,
    required this.missingData,
  });

  factory CompanionChange.fromJson(Map<String, dynamic> json) => CompanionChange(
    observationKey: json['observation_key'] as String? ?? '',
    changeKind: json['change_kind'] as String? ?? 'unknown',
    evidenceStrength: json['evidence_strength'] as String? ?? 'limited',
    missingData: (json['missing_data'] as List? ?? const []).whereType<String>().toList(),
  );
}

class CompanionAfterVisit {
  final String status;
  final int? anchorId;
  final DateTime? occurredAt;
  final String? source;
  final int factCount;
  final DateTime? latestFactAt;

  const CompanionAfterVisit({
    required this.status,
    required this.anchorId,
    required this.occurredAt,
    required this.source,
    required this.factCount,
    required this.latestFactAt,
  });

  factory CompanionAfterVisit.fromJson(Map<String, dynamic> json) => CompanionAfterVisit(
    status: json['status'] as String? ?? 'no_recorded_visit',
    anchorId: json['anchor_id'] as int?,
    occurredAt: json['occurred_at'] == null
        ? null
        : DateTime.parse(json['occurred_at'] as String),
    source: json['source'] as String?,
    factCount: json['fact_count'] as int? ?? 0,
    latestFactAt: json['latest_fact_at'] == null
        ? null
        : DateTime.parse(json['latest_fact_at'] as String),
  );
}

class CompanionOverview {
  final String patternStatus;
  final String reviewStatus;
  final DateTime? reviewAnchorCapturedAt;
  final List<CompanionPattern> patterns;
  final List<CompanionChange> changesSinceReview;
  final CompanionAfterVisit afterVisit;
  final String safetyNotice;
  final String sourceVersion;

  const CompanionOverview({
    required this.patternStatus,
    required this.reviewStatus,
    required this.reviewAnchorCapturedAt,
    required this.patterns,
    required this.changesSinceReview,
    required this.afterVisit,
    required this.safetyNotice,
    required this.sourceVersion,
  });

  factory CompanionOverview.fromJson(Map<String, dynamic> json) => CompanionOverview(
    patternStatus: json['pattern_status'] as String? ?? 'no_governed_patterns',
    reviewStatus: json['review_status'] as String? ?? 'insufficient_anchor',
    reviewAnchorCapturedAt: json['review_anchor_captured_at'] == null
        ? null
        : DateTime.parse(json['review_anchor_captured_at'] as String),
    patterns: (json['patterns'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => CompanionPattern.fromJson(Map<String, dynamic>.from(item)))
        .toList(),
    changesSinceReview: (json['changes_since_review'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => CompanionChange.fromJson(Map<String, dynamic>.from(item)))
        .toList(),
    afterVisit: CompanionAfterVisit.fromJson(
      Map<String, dynamic>.from(json['after_visit'] as Map? ?? const {}),
    ),
    safetyNotice: json['safety_notice'] as String? ?? '',
    sourceVersion: json['source_version'] as String? ?? '',
  );
}
