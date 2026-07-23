enum InsightSeverity { good, warn, danger }

class InsightCard {
  final String code;
  final int priority;
  final String icon;
  final String title;
  final String body;
  final String action;
  final InsightSeverity severity;
  final String tag;
  final int? episodeCount;
  final int? totalDays;
  final int? confidencePct;

  InsightCard({
    required this.code,
    required this.priority,
    required this.icon,
    required this.title,
    required this.body,
    required this.action,
    required this.severity,
    required this.tag,
    this.episodeCount,
    this.totalDays,
    this.confidencePct,
  });

  factory InsightCard.fromMap(Map<String, dynamic> map) {
    final priority = map['priority'] ?? 2;
    InsightSeverity sev;
    String tag;

    if (priority >= 3) {
      sev = InsightSeverity.danger;
      tag = 'À surveiller';
    } else if (priority == 2) {
      sev = InsightSeverity.warn;
      tag = 'Priorité haute';
    } else {
      sev = InsightSeverity.good;
      tag = 'Positif';
    }

    return InsightCard(
      code: map['code'] ?? '',
      priority: priority,
      icon: map['icon'] ?? 'auto_awesome',
      title: map['title'] ?? '',
      body: map['content'] ?? '',
      action: map['action'] ?? '',
      severity: sev,
      tag: tag,
      episodeCount: map['episode_count'],
      totalDays: map['total_days'],
      confidencePct: map['confidence_pct'],
    );
  }
}

class SummaryResponse {
  final List<InsightCard> insights;
  final Map<String, dynamic> kpis;
  final List<dynamic> dailyAverages;
  final List<dynamic> agpProfile;
  final String generatedAt;
  final bool hasSufficientData;
  // "gemini" | "kimi" | "claude" | "quota-exhausted" | "fallback"
  // Used to show a degraded-mode banner in the insights section.
  final String aiProvider;

  SummaryResponse({
    required this.insights,
    required this.kpis,
    required this.dailyAverages,
    required this.agpProfile,
    required this.generatedAt,
    required this.hasSufficientData,
    this.aiProvider = 'gemini',
  });

  factory SummaryResponse.fromJson(Map<String, dynamic> json) {
    return SummaryResponse(
      insights: (json['insights'] as List? ?? [])
          .map((i) => InsightCard.fromMap(i as Map<String, dynamic>))
          .toList(),
      kpis: json['kpis'] ?? {},
      dailyAverages: json['daily_averages'] ?? [],
      agpProfile: json['agp_profile'] ?? [],
      generatedAt: json['generated_at'] ?? '',
      hasSufficientData: json['has_sufficient_data'] ?? false,
      aiProvider: json['ai_provider'] as String? ?? 'gemini',
    );
  }

  bool get isAiDegraded =>
      aiProvider == 'quota-exhausted' || aiProvider == 'fallback';

  List<InsightCard> get insightCards => insights;
}

class KpisResponse {
  final double? avgGlucose;
  final double? stdDev;
  final double? cvPct;
  final double? tirPct;
  final double? tarPct;
  final double? tbrPct;
  final double? gmi;
  final int logCount;
  final int daysWithData;
  final bool hasSufficientData;
  /// GMI reliability grade: "high" | "medium" | "low" | null
  final String? gmiConfidence;
  /// Human-readable GMI basis, e.g. "47 mesures · 15j"
  final String gmiBasis;

  KpisResponse({
    this.avgGlucose,
    this.stdDev,
    this.cvPct,
    this.tirPct,
    this.tarPct,
    this.tbrPct,
    this.gmi,
    required this.logCount,
    required this.daysWithData,
    required this.hasSufficientData,
    this.gmiConfidence,
    this.gmiBasis = '',
  });

  factory KpisResponse.fromJson(Map<String, dynamic> json) {
    return KpisResponse(
      avgGlucose:       (json['avg_glucose'] as num?)?.toDouble(),
      stdDev:           (json['std_dev'] as num?)?.toDouble(),
      cvPct:            (json['cv_pct'] as num?)?.toDouble(),
      tirPct:           (json['tir_pct'] as num?)?.toDouble(),
      tarPct:           (json['tar_pct'] as num?)?.toDouble(),
      tbrPct:           (json['tbr_pct'] as num?)?.toDouble(),
      gmi:              (json['gmi'] as num?)?.toDouble(),
      logCount:         (json['log_count'] as num?)?.toInt() ?? 0,
      daysWithData:     (json['days_with_data'] as num?)?.toInt() ?? 0,
      hasSufficientData: json['has_sufficient_data'] ?? false,
      gmiConfidence:    json['gmi_confidence'] as String?,
      gmiBasis:         json['gmi_basis'] as String? ?? '',
    );
  }
}

class ChatResponse {
  final String reply;
  final String conversationId;
  final DateTime timestamp;
  final bool isEmergency;
  final String replyLanguage;

  ChatResponse({
    required this.reply,
    required this.conversationId,
    required this.timestamp,
    this.isEmergency = false,
    this.replyLanguage = 'fr',
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    return ChatResponse(
      reply: json['reply'] ?? '',
      conversationId: json['conversation_id'] ?? '',
      timestamp: DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      isEmergency: json['is_emergency'] ?? false,
      replyLanguage: json['reply_language'] as String? ?? 'fr',
    );
  }
}

/// Phase 11-C: result from POST /api/v1/ai/analyze-meal-image
class MealAnalysisResult {
  /// French food names identified by Gemini Vision (max 8).
  final List<String> foods;

  /// Overall detection confidence: "high" | "medium" | "low"
  final String confidence;

  /// True when the LLM failed or returned nothing useful.
  /// UI must show a manual fallback message when true.
  final bool fallback;

  const MealAnalysisResult({
    required this.foods,
    required this.confidence,
    required this.fallback,
  });

  factory MealAnalysisResult.fromJson(Map<String, dynamic> json) {
    return MealAnalysisResult(
      foods:      List<String>.from(json['foods'] as List? ?? []),
      confidence: json['confidence'] as String? ?? 'low',
      fallback:   json['fallback']   as bool?   ?? true,
    );
  }
}

class GlucometerOcrResponse {
  final double? value;        // glucose value (null if not detected)
  final String unit;          // "mg/dL" | "mmol/L"
  final String confidence;    // "high" | "medium" | "low"
  final bool fallback;

  GlucometerOcrResponse({
    required this.value,
    required this.unit,
    required this.confidence,
    required this.fallback,
  });

  factory GlucometerOcrResponse.fromJson(Map<String, dynamic> json) {
    final raw = json['value'];
    return GlucometerOcrResponse(
      value:      raw != null ? (raw as num).toDouble() : null,
      unit:       json['unit']       as String? ?? 'mg/dL',
      confidence: json['confidence'] as String? ?? 'low',
      fallback:   json['fallback']   as bool?   ?? true,
    );
  }
}

class VoiceResponse {
  final String transcript;   // what IAmina heard — shown as user bubble subtitle
  final String reply;        // IAmina's text reply — read via flutter_tts
  final String conversationId;
  final DateTime timestamp;
  final bool isEmergency;
  final String replyLanguage;

  VoiceResponse({
    required this.transcript,
    required this.reply,
    required this.conversationId,
    required this.timestamp,
    this.isEmergency = false,
    this.replyLanguage = 'fr',
  });

  factory VoiceResponse.fromJson(Map<String, dynamic> json) {
    return VoiceResponse(
      transcript:     json['transcript']      ?? '',
      reply:          json['reply']           ?? '',
      conversationId: json['conversation_id'] ?? '',
      timestamp:      DateTime.tryParse(json['timestamp'] ?? '') ?? DateTime.now(),
      isEmergency:    json['is_emergency']    ?? false,
      replyLanguage:  json['reply_language']  as String? ?? 'fr',
    );
  }
}
