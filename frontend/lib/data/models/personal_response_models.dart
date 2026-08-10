class PersonalResponsePattern {
  final String key;
  final String kind;
  final int observations;
  final int distinctDays;
  final double medianGlucoseMgDl;
  final double windowMedianGlucoseMgDl;
  final String confidence;

  const PersonalResponsePattern({
    required this.key,
    required this.kind,
    required this.observations,
    required this.distinctDays,
    required this.medianGlucoseMgDl,
    required this.windowMedianGlucoseMgDl,
    required this.confidence,
  });

  factory PersonalResponsePattern.fromJson(Map<String, dynamic> json) {
    return PersonalResponsePattern(
      key: json['key'] as String,
      kind: json['kind'] as String,
      observations: json['observations'] as int,
      distinctDays: json['distinct_days'] as int,
      medianGlucoseMgDl: (json['median_glucose_mg_dl'] as num).toDouble(),
      windowMedianGlucoseMgDl: (json['window_median_glucose_mg_dl'] as num)
          .toDouble(),
      confidence: json['confidence'] as String,
    );
  }
}

class PersonalResponseResult {
  final String status;
  final String dataScope;
  final int windowDays;
  final int totalReadings;
  final int distinctDays;
  final double? windowMedianGlucoseMgDl;
  final int minimumObservations;
  final int minimumDistinctDays;
  final String confidenceDefinition;
  final String causalityNotice;
  final List<PersonalResponsePattern> patterns;

  const PersonalResponseResult({
    required this.status,
    required this.dataScope,
    required this.windowDays,
    required this.totalReadings,
    required this.distinctDays,
    required this.windowMedianGlucoseMgDl,
    required this.minimumObservations,
    required this.minimumDistinctDays,
    required this.confidenceDefinition,
    required this.causalityNotice,
    required this.patterns,
  });

  bool get hasPatterns => status == 'ready' && patterns.isNotEmpty;

  factory PersonalResponseResult.fromJson(Map<String, dynamic> json) {
    final rawPatterns = json['patterns'] as List<dynamic>? ?? const [];
    return PersonalResponseResult(
      status: json['status'] as String,
      dataScope: json['data_scope'] as String,
      windowDays: json['window_days'] as int,
      totalReadings: json['total_readings'] as int,
      distinctDays: json['distinct_days'] as int,
      windowMedianGlucoseMgDl: (json['window_median_glucose_mg_dl'] as num?)
          ?.toDouble(),
      minimumObservations: json['minimum_observations'] as int,
      minimumDistinctDays: json['minimum_distinct_days'] as int,
      confidenceDefinition: json['confidence_definition'] as String,
      causalityNotice: json['causality_notice'] as String,
      patterns: rawPatterns
          .map(
            (item) =>
                PersonalResponsePattern.fromJson(item as Map<String, dynamic>),
          )
          .toList(growable: false),
    );
  }
}
