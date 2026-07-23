// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'schema.models.swagger.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LogEntrySchema _$LogEntrySchemaFromJson(Map<String, dynamic> json) =>
    LogEntrySchema(
      id: (json['id'] as num).toInt(),
      loggedAt: json['logged_at'] == null
          ? null
          : DateTime.parse(json['logged_at'] as String),
      mealType: json['meal_type'] as String,
      bloodSugar: (json['blood_sugar'] as num).toDouble(),
      mealDescription: json['meal_description'] as String?,
      insulinUnits: (json['insulin_units'] as num?)?.toDouble(),
      exercised: json['exercised'] as String?,
      sleepQuality: json['sleep_quality'] as String?,
      stressed: json['stressed'] as String?,
      fatigueLevel: json['fatigue_level'] as String?,
      isSick: json['is_sick'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$LogEntrySchemaToJson(LogEntrySchema instance) =>
    <String, dynamic>{
      'id': instance.id,
      'logged_at': instance.loggedAt?.toIso8601String(),
      'meal_type': instance.mealType,
      'blood_sugar': instance.bloodSugar,
      'meal_description': instance.mealDescription,
      'insulin_units': instance.insulinUnits,
      'exercised': instance.exercised,
      'sleep_quality': instance.sleepQuality,
      'stressed': instance.stressed,
      'fatigue_level': instance.fatigueLevel,
      'is_sick': instance.isSick,
      'created_at': instance.createdAt.toIso8601String(),
    };

LogEntryCreateSchema _$LogEntryCreateSchemaFromJson(
  Map<String, dynamic> json,
) => LogEntryCreateSchema(
  loggedAt: json['logged_at'] == null
      ? null
      : DateTime.parse(json['logged_at'] as String),
  mealType: json['meal_type'] as String?,
  bloodSugar: (json['blood_sugar'] as num).toDouble(),
  mealDescription: json['meal_description'] as String?,
  insulinUnits: (json['insulin_units'] as num?)?.toDouble(),
  exercised: json['exercised'] as String?,
  sleepQuality: json['sleep_quality'] as String?,
  stressed: json['stressed'] as String?,
  fatigueLevel: json['fatigue_level'] as String?,
  isSick: json['is_sick'] as String?,
);

Map<String, dynamic> _$LogEntryCreateSchemaToJson(
  LogEntryCreateSchema instance,
) => <String, dynamic>{
  'logged_at': instance.loggedAt?.toIso8601String(),
  'meal_type': instance.mealType,
  'blood_sugar': instance.bloodSugar,
  'meal_description': instance.mealDescription,
  'insulin_units': instance.insulinUnits,
  'exercised': instance.exercised,
  'sleep_quality': instance.sleepQuality,
  'stressed': instance.stressed,
  'fatigue_level': instance.fatigueLevel,
  'is_sick': instance.isSick,
};

Error _$ErrorFromJson(Map<String, dynamic> json) =>
    Error(message: json['message'] as String);

Map<String, dynamic> _$ErrorToJson(Error instance) => <String, dynamic>{
  'message': instance.message,
};

PatientProfileSchema _$PatientProfileSchemaFromJson(
  Map<String, dynamic> json,
) => PatientProfileSchema(
  diabetesType: json['diabetes_type'] as String,
  treatmentType: json['treatment_type'] as String,
  targetRangeLow: (json['target_range_low'] as num).toDouble(),
  targetRangeHigh: (json['target_range_high'] as num).toDouble(),
  unitPreference: json['unit_preference'] as String,
  gender: json['gender'] as String?,
  dateOfBirth: json['date_of_birth'] == null
      ? null
      : DateTime.parse(json['date_of_birth'] as String),
  weight: (json['weight'] as num?)?.toDouble(),
  height: (json['height'] as num?)?.toDouble(),
);

Map<String, dynamic> _$PatientProfileSchemaToJson(
  PatientProfileSchema instance,
) => <String, dynamic>{
  'diabetes_type': instance.diabetesType,
  'treatment_type': instance.treatmentType,
  'target_range_low': instance.targetRangeLow,
  'target_range_high': instance.targetRangeHigh,
  'unit_preference': instance.unitPreference,
  'gender': instance.gender,
  'date_of_birth': instance.dateOfBirth?.toIso8601String(),
  'weight': instance.weight,
  'height': instance.height,
};

SummaryResponse _$SummaryResponseFromJson(
  Map<String, dynamic> json,
) => SummaryResponse(
  insights:
      (json['insights'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      [],
  alerts:
      (json['alerts'] as List<dynamic>?)?.map((e) => e as String).toList() ??
      [],
  kpis: json['kpis'] as Map<String, dynamic>,
  recommendations:
      (json['recommendations'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList() ??
      [],
  nextSteps: json['next_steps'] as String,
  generatedAt: json['generated_at'] as String,
);

Map<String, dynamic> _$SummaryResponseToJson(SummaryResponse instance) =>
    <String, dynamic>{
      'insights': instance.insights,
      'alerts': instance.alerts,
      'kpis': instance.kpis,
      'recommendations': instance.recommendations,
      'next_steps': instance.nextSteps,
      'generated_at': instance.generatedAt,
    };

SummaryRequest _$SummaryRequestFromJson(Map<String, dynamic> json) =>
    SummaryRequest(
      days: (json['days'] as num?)?.toInt(),
      patientId: (json['patient_id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$SummaryRequestToJson(SummaryRequest instance) =>
    <String, dynamic>{'days': instance.days, 'patient_id': instance.patientId};

ChatResponse _$ChatResponseFromJson(Map<String, dynamic> json) => ChatResponse(
  reply: json['reply'] as String,
  conversationId: json['conversation_id'] as String,
  timestamp: json['timestamp'] as String,
);

Map<String, dynamic> _$ChatResponseToJson(ChatResponse instance) =>
    <String, dynamic>{
      'reply': instance.reply,
      'conversation_id': instance.conversationId,
      'timestamp': instance.timestamp,
    };

ChatRequest _$ChatRequestFromJson(Map<String, dynamic> json) => ChatRequest(
  message: json['message'] as String,
  contextType: json['context_type'] as String?,
);

Map<String, dynamic> _$ChatRequestToJson(ChatRequest instance) =>
    <String, dynamic>{
      'message': instance.message,
      'context_type': instance.contextType,
    };
