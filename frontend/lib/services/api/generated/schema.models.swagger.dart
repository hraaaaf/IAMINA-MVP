// coverage:ignore-file
// ignore_for_file: type=lint

import 'package:json_annotation/json_annotation.dart';
import 'package:collection/collection.dart';
import 'dart:convert';

part 'schema.models.swagger.g.dart';

@JsonSerializable(explicitToJson: true)
class LogEntrySchema {
  const LogEntrySchema({
    required this.id,
    required this.loggedAt,
    required this.mealType,
    required this.bloodSugar,
    this.mealDescription,
    this.insulinUnits,
    this.exercised,
    this.sleepQuality,
    this.stressed,
    this.fatigueLevel,
    this.isSick,
    required this.createdAt,
  });

  factory LogEntrySchema.fromJson(Map<String, dynamic> json) =>
      _$LogEntrySchemaFromJson(json);

  static const toJsonFactory = _$LogEntrySchemaToJson;
  Map<String, dynamic> toJson() => _$LogEntrySchemaToJson(this);

  @JsonKey(name: 'id')
  final int id;
  @JsonKey(name: 'logged_at')
  final DateTime? loggedAt;
  @JsonKey(name: 'meal_type')
  final String mealType;
  @JsonKey(name: 'blood_sugar')
  final double bloodSugar;
  @JsonKey(name: 'meal_description')
  final String? mealDescription;
  @JsonKey(name: 'insulin_units')
  final double? insulinUnits;
  @JsonKey(name: 'exercised')
  final String? exercised;
  @JsonKey(name: 'sleep_quality')
  final String? sleepQuality;
  @JsonKey(name: 'stressed')
  final String? stressed;
  @JsonKey(name: 'fatigue_level')
  final String? fatigueLevel;
  @JsonKey(name: 'is_sick')
  final String? isSick;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  static const fromJsonFactory = _$LogEntrySchemaFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is LogEntrySchema &&
            (identical(other.id, id) ||
                const DeepCollectionEquality().equals(other.id, id)) &&
            (identical(other.loggedAt, loggedAt) ||
                const DeepCollectionEquality().equals(
                  other.loggedAt,
                  loggedAt,
                )) &&
            (identical(other.mealType, mealType) ||
                const DeepCollectionEquality().equals(
                  other.mealType,
                  mealType,
                )) &&
            (identical(other.bloodSugar, bloodSugar) ||
                const DeepCollectionEquality().equals(
                  other.bloodSugar,
                  bloodSugar,
                )) &&
            (identical(other.mealDescription, mealDescription) ||
                const DeepCollectionEquality().equals(
                  other.mealDescription,
                  mealDescription,
                )) &&
            (identical(other.insulinUnits, insulinUnits) ||
                const DeepCollectionEquality().equals(
                  other.insulinUnits,
                  insulinUnits,
                )) &&
            (identical(other.exercised, exercised) ||
                const DeepCollectionEquality().equals(
                  other.exercised,
                  exercised,
                )) &&
            (identical(other.sleepQuality, sleepQuality) ||
                const DeepCollectionEquality().equals(
                  other.sleepQuality,
                  sleepQuality,
                )) &&
            (identical(other.stressed, stressed) ||
                const DeepCollectionEquality().equals(
                  other.stressed,
                  stressed,
                )) &&
            (identical(other.fatigueLevel, fatigueLevel) ||
                const DeepCollectionEquality().equals(
                  other.fatigueLevel,
                  fatigueLevel,
                )) &&
            (identical(other.isSick, isSick) ||
                const DeepCollectionEquality().equals(other.isSick, isSick)) &&
            (identical(other.createdAt, createdAt) ||
                const DeepCollectionEquality().equals(
                  other.createdAt,
                  createdAt,
                )));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(id) ^
      const DeepCollectionEquality().hash(loggedAt) ^
      const DeepCollectionEquality().hash(mealType) ^
      const DeepCollectionEquality().hash(bloodSugar) ^
      const DeepCollectionEquality().hash(mealDescription) ^
      const DeepCollectionEquality().hash(insulinUnits) ^
      const DeepCollectionEquality().hash(exercised) ^
      const DeepCollectionEquality().hash(sleepQuality) ^
      const DeepCollectionEquality().hash(stressed) ^
      const DeepCollectionEquality().hash(fatigueLevel) ^
      const DeepCollectionEquality().hash(isSick) ^
      const DeepCollectionEquality().hash(createdAt) ^
      runtimeType.hashCode;
}

extension $LogEntrySchemaExtension on LogEntrySchema {
  LogEntrySchema copyWith({
    int? id,
    DateTime? loggedAt,
    String? mealType,
    double? bloodSugar,
    String? mealDescription,
    double? insulinUnits,
    String? exercised,
    String? sleepQuality,
    String? stressed,
    String? fatigueLevel,
    String? isSick,
    DateTime? createdAt,
  }) {
    return LogEntrySchema(
      id: id ?? this.id,
      loggedAt: loggedAt ?? this.loggedAt,
      mealType: mealType ?? this.mealType,
      bloodSugar: bloodSugar ?? this.bloodSugar,
      mealDescription: mealDescription ?? this.mealDescription,
      insulinUnits: insulinUnits ?? this.insulinUnits,
      exercised: exercised ?? this.exercised,
      sleepQuality: sleepQuality ?? this.sleepQuality,
      stressed: stressed ?? this.stressed,
      fatigueLevel: fatigueLevel ?? this.fatigueLevel,
      isSick: isSick ?? this.isSick,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  LogEntrySchema copyWithWrapped({
    Wrapped<int>? id,
    Wrapped<DateTime?>? loggedAt,
    Wrapped<String>? mealType,
    Wrapped<double>? bloodSugar,
    Wrapped<String?>? mealDescription,
    Wrapped<double?>? insulinUnits,
    Wrapped<String?>? exercised,
    Wrapped<String?>? sleepQuality,
    Wrapped<String?>? stressed,
    Wrapped<String?>? fatigueLevel,
    Wrapped<String?>? isSick,
    Wrapped<DateTime>? createdAt,
  }) {
    return LogEntrySchema(
      id: (id != null ? id.value : this.id),
      loggedAt: (loggedAt != null ? loggedAt.value : this.loggedAt),
      mealType: (mealType != null ? mealType.value : this.mealType),
      bloodSugar: (bloodSugar != null ? bloodSugar.value : this.bloodSugar),
      mealDescription: (mealDescription != null
          ? mealDescription.value
          : this.mealDescription),
      insulinUnits: (insulinUnits != null
          ? insulinUnits.value
          : this.insulinUnits),
      exercised: (exercised != null ? exercised.value : this.exercised),
      sleepQuality: (sleepQuality != null
          ? sleepQuality.value
          : this.sleepQuality),
      stressed: (stressed != null ? stressed.value : this.stressed),
      fatigueLevel: (fatigueLevel != null
          ? fatigueLevel.value
          : this.fatigueLevel),
      isSick: (isSick != null ? isSick.value : this.isSick),
      createdAt: (createdAt != null ? createdAt.value : this.createdAt),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class LogEntryCreateSchema {
  const LogEntryCreateSchema({
    this.loggedAt,
    this.mealType,
    required this.bloodSugar,
    this.mealDescription,
    this.insulinUnits,
    this.exercised,
    this.sleepQuality,
    this.stressed,
    this.fatigueLevel,
    this.isSick,
  });

  factory LogEntryCreateSchema.fromJson(Map<String, dynamic> json) =>
      _$LogEntryCreateSchemaFromJson(json);

  static const toJsonFactory = _$LogEntryCreateSchemaToJson;
  Map<String, dynamic> toJson() => _$LogEntryCreateSchemaToJson(this);

  @JsonKey(name: 'logged_at')
  final DateTime? loggedAt;
  @JsonKey(name: 'meal_type')
  final String? mealType;
  @JsonKey(name: 'blood_sugar')
  final double bloodSugar;
  @JsonKey(name: 'meal_description')
  final String? mealDescription;
  @JsonKey(name: 'insulin_units')
  final double? insulinUnits;
  @JsonKey(name: 'exercised')
  final String? exercised;
  @JsonKey(name: 'sleep_quality')
  final String? sleepQuality;
  @JsonKey(name: 'stressed')
  final String? stressed;
  @JsonKey(name: 'fatigue_level')
  final String? fatigueLevel;
  @JsonKey(name: 'is_sick')
  final String? isSick;
  static const fromJsonFactory = _$LogEntryCreateSchemaFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is LogEntryCreateSchema &&
            (identical(other.loggedAt, loggedAt) ||
                const DeepCollectionEquality().equals(
                  other.loggedAt,
                  loggedAt,
                )) &&
            (identical(other.mealType, mealType) ||
                const DeepCollectionEquality().equals(
                  other.mealType,
                  mealType,
                )) &&
            (identical(other.bloodSugar, bloodSugar) ||
                const DeepCollectionEquality().equals(
                  other.bloodSugar,
                  bloodSugar,
                )) &&
            (identical(other.mealDescription, mealDescription) ||
                const DeepCollectionEquality().equals(
                  other.mealDescription,
                  mealDescription,
                )) &&
            (identical(other.insulinUnits, insulinUnits) ||
                const DeepCollectionEquality().equals(
                  other.insulinUnits,
                  insulinUnits,
                )) &&
            (identical(other.exercised, exercised) ||
                const DeepCollectionEquality().equals(
                  other.exercised,
                  exercised,
                )) &&
            (identical(other.sleepQuality, sleepQuality) ||
                const DeepCollectionEquality().equals(
                  other.sleepQuality,
                  sleepQuality,
                )) &&
            (identical(other.stressed, stressed) ||
                const DeepCollectionEquality().equals(
                  other.stressed,
                  stressed,
                )) &&
            (identical(other.fatigueLevel, fatigueLevel) ||
                const DeepCollectionEquality().equals(
                  other.fatigueLevel,
                  fatigueLevel,
                )) &&
            (identical(other.isSick, isSick) ||
                const DeepCollectionEquality().equals(other.isSick, isSick)));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(loggedAt) ^
      const DeepCollectionEquality().hash(mealType) ^
      const DeepCollectionEquality().hash(bloodSugar) ^
      const DeepCollectionEquality().hash(mealDescription) ^
      const DeepCollectionEquality().hash(insulinUnits) ^
      const DeepCollectionEquality().hash(exercised) ^
      const DeepCollectionEquality().hash(sleepQuality) ^
      const DeepCollectionEquality().hash(stressed) ^
      const DeepCollectionEquality().hash(fatigueLevel) ^
      const DeepCollectionEquality().hash(isSick) ^
      runtimeType.hashCode;
}

extension $LogEntryCreateSchemaExtension on LogEntryCreateSchema {
  LogEntryCreateSchema copyWith({
    DateTime? loggedAt,
    String? mealType,
    double? bloodSugar,
    String? mealDescription,
    double? insulinUnits,
    String? exercised,
    String? sleepQuality,
    String? stressed,
    String? fatigueLevel,
    String? isSick,
  }) {
    return LogEntryCreateSchema(
      loggedAt: loggedAt ?? this.loggedAt,
      mealType: mealType ?? this.mealType,
      bloodSugar: bloodSugar ?? this.bloodSugar,
      mealDescription: mealDescription ?? this.mealDescription,
      insulinUnits: insulinUnits ?? this.insulinUnits,
      exercised: exercised ?? this.exercised,
      sleepQuality: sleepQuality ?? this.sleepQuality,
      stressed: stressed ?? this.stressed,
      fatigueLevel: fatigueLevel ?? this.fatigueLevel,
      isSick: isSick ?? this.isSick,
    );
  }

  LogEntryCreateSchema copyWithWrapped({
    Wrapped<DateTime?>? loggedAt,
    Wrapped<String?>? mealType,
    Wrapped<double>? bloodSugar,
    Wrapped<String?>? mealDescription,
    Wrapped<double?>? insulinUnits,
    Wrapped<String?>? exercised,
    Wrapped<String?>? sleepQuality,
    Wrapped<String?>? stressed,
    Wrapped<String?>? fatigueLevel,
    Wrapped<String?>? isSick,
  }) {
    return LogEntryCreateSchema(
      loggedAt: (loggedAt != null ? loggedAt.value : this.loggedAt),
      mealType: (mealType != null ? mealType.value : this.mealType),
      bloodSugar: (bloodSugar != null ? bloodSugar.value : this.bloodSugar),
      mealDescription: (mealDescription != null
          ? mealDescription.value
          : this.mealDescription),
      insulinUnits: (insulinUnits != null
          ? insulinUnits.value
          : this.insulinUnits),
      exercised: (exercised != null ? exercised.value : this.exercised),
      sleepQuality: (sleepQuality != null
          ? sleepQuality.value
          : this.sleepQuality),
      stressed: (stressed != null ? stressed.value : this.stressed),
      fatigueLevel: (fatigueLevel != null
          ? fatigueLevel.value
          : this.fatigueLevel),
      isSick: (isSick != null ? isSick.value : this.isSick),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class Error {
  const Error({required this.message});

  factory Error.fromJson(Map<String, dynamic> json) => _$ErrorFromJson(json);

  static const toJsonFactory = _$ErrorToJson;
  Map<String, dynamic> toJson() => _$ErrorToJson(this);

  @JsonKey(name: 'message')
  final String message;
  static const fromJsonFactory = _$ErrorFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is Error &&
            (identical(other.message, message) ||
                const DeepCollectionEquality().equals(other.message, message)));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(message) ^ runtimeType.hashCode;
}

extension $ErrorExtension on Error {
  Error copyWith({String? message}) {
    return Error(message: message ?? this.message);
  }

  Error copyWithWrapped({Wrapped<String>? message}) {
    return Error(message: (message != null ? message.value : this.message));
  }
}

@JsonSerializable(explicitToJson: true)
class PatientProfileSchema {
  const PatientProfileSchema({
    required this.diabetesType,
    required this.treatmentType,
    required this.targetRangeLow,
    required this.targetRangeHigh,
    required this.unitPreference,
    this.gender,
    this.dateOfBirth,
    this.weight,
    this.height,
  });

  factory PatientProfileSchema.fromJson(Map<String, dynamic> json) =>
      _$PatientProfileSchemaFromJson(json);

  static const toJsonFactory = _$PatientProfileSchemaToJson;
  Map<String, dynamic> toJson() => _$PatientProfileSchemaToJson(this);

  @JsonKey(name: 'diabetes_type')
  final String diabetesType;
  @JsonKey(name: 'treatment_type')
  final String treatmentType;
  @JsonKey(name: 'target_range_low')
  final double targetRangeLow;
  @JsonKey(name: 'target_range_high')
  final double targetRangeHigh;
  @JsonKey(name: 'unit_preference')
  final String unitPreference;
  @JsonKey(name: 'gender')
  final String? gender;
  @JsonKey(name: 'date_of_birth')
  final DateTime? dateOfBirth;
  @JsonKey(name: 'weight')
  final double? weight;
  @JsonKey(name: 'height')
  final double? height;
  static const fromJsonFactory = _$PatientProfileSchemaFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is PatientProfileSchema &&
            (identical(other.diabetesType, diabetesType) ||
                const DeepCollectionEquality().equals(
                  other.diabetesType,
                  diabetesType,
                )) &&
            (identical(other.treatmentType, treatmentType) ||
                const DeepCollectionEquality().equals(
                  other.treatmentType,
                  treatmentType,
                )) &&
            (identical(other.targetRangeLow, targetRangeLow) ||
                const DeepCollectionEquality().equals(
                  other.targetRangeLow,
                  targetRangeLow,
                )) &&
            (identical(other.targetRangeHigh, targetRangeHigh) ||
                const DeepCollectionEquality().equals(
                  other.targetRangeHigh,
                  targetRangeHigh,
                )) &&
            (identical(other.unitPreference, unitPreference) ||
                const DeepCollectionEquality().equals(
                  other.unitPreference,
                  unitPreference,
                )) &&
            (identical(other.gender, gender) ||
                const DeepCollectionEquality().equals(other.gender, gender)) &&
            (identical(other.dateOfBirth, dateOfBirth) ||
                const DeepCollectionEquality().equals(
                  other.dateOfBirth,
                  dateOfBirth,
                )) &&
            (identical(other.weight, weight) ||
                const DeepCollectionEquality().equals(other.weight, weight)) &&
            (identical(other.height, height) ||
                const DeepCollectionEquality().equals(other.height, height)));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(diabetesType) ^
      const DeepCollectionEquality().hash(treatmentType) ^
      const DeepCollectionEquality().hash(targetRangeLow) ^
      const DeepCollectionEquality().hash(targetRangeHigh) ^
      const DeepCollectionEquality().hash(unitPreference) ^
      const DeepCollectionEquality().hash(gender) ^
      const DeepCollectionEquality().hash(dateOfBirth) ^
      const DeepCollectionEquality().hash(weight) ^
      const DeepCollectionEquality().hash(height) ^
      runtimeType.hashCode;
}

extension $PatientProfileSchemaExtension on PatientProfileSchema {
  PatientProfileSchema copyWith({
    String? diabetesType,
    String? treatmentType,
    double? targetRangeLow,
    double? targetRangeHigh,
    String? unitPreference,
    String? gender,
    DateTime? dateOfBirth,
    double? weight,
    double? height,
  }) {
    return PatientProfileSchema(
      diabetesType: diabetesType ?? this.diabetesType,
      treatmentType: treatmentType ?? this.treatmentType,
      targetRangeLow: targetRangeLow ?? this.targetRangeLow,
      targetRangeHigh: targetRangeHigh ?? this.targetRangeHigh,
      unitPreference: unitPreference ?? this.unitPreference,
      gender: gender ?? this.gender,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      weight: weight ?? this.weight,
      height: height ?? this.height,
    );
  }

  PatientProfileSchema copyWithWrapped({
    Wrapped<String>? diabetesType,
    Wrapped<String>? treatmentType,
    Wrapped<double>? targetRangeLow,
    Wrapped<double>? targetRangeHigh,
    Wrapped<String>? unitPreference,
    Wrapped<String?>? gender,
    Wrapped<DateTime?>? dateOfBirth,
    Wrapped<double?>? weight,
    Wrapped<double?>? height,
  }) {
    return PatientProfileSchema(
      diabetesType: (diabetesType != null
          ? diabetesType.value
          : this.diabetesType),
      treatmentType: (treatmentType != null
          ? treatmentType.value
          : this.treatmentType),
      targetRangeLow: (targetRangeLow != null
          ? targetRangeLow.value
          : this.targetRangeLow),
      targetRangeHigh: (targetRangeHigh != null
          ? targetRangeHigh.value
          : this.targetRangeHigh),
      unitPreference: (unitPreference != null
          ? unitPreference.value
          : this.unitPreference),
      gender: (gender != null ? gender.value : this.gender),
      dateOfBirth: (dateOfBirth != null ? dateOfBirth.value : this.dateOfBirth),
      weight: (weight != null ? weight.value : this.weight),
      height: (height != null ? height.value : this.height),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class SummaryResponse {
  const SummaryResponse({
    required this.insights,
    required this.alerts,
    required this.kpis,
    required this.recommendations,
    required this.nextSteps,
    required this.generatedAt,
  });

  factory SummaryResponse.fromJson(Map<String, dynamic> json) =>
      _$SummaryResponseFromJson(json);

  static const toJsonFactory = _$SummaryResponseToJson;
  Map<String, dynamic> toJson() => _$SummaryResponseToJson(this);

  @JsonKey(name: 'insights', defaultValue: <String>[])
  final List<String> insights;
  @JsonKey(name: 'alerts', defaultValue: <String>[])
  final List<String> alerts;
  @JsonKey(name: 'kpis')
  final Map<String, dynamic> kpis;
  @JsonKey(name: 'recommendations', defaultValue: <String>[])
  final List<String> recommendations;
  @JsonKey(name: 'next_steps')
  final String nextSteps;
  @JsonKey(name: 'generated_at')
  final String generatedAt;
  static const fromJsonFactory = _$SummaryResponseFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is SummaryResponse &&
            (identical(other.insights, insights) ||
                const DeepCollectionEquality().equals(
                  other.insights,
                  insights,
                )) &&
            (identical(other.alerts, alerts) ||
                const DeepCollectionEquality().equals(other.alerts, alerts)) &&
            (identical(other.kpis, kpis) ||
                const DeepCollectionEquality().equals(other.kpis, kpis)) &&
            (identical(other.recommendations, recommendations) ||
                const DeepCollectionEquality().equals(
                  other.recommendations,
                  recommendations,
                )) &&
            (identical(other.nextSteps, nextSteps) ||
                const DeepCollectionEquality().equals(
                  other.nextSteps,
                  nextSteps,
                )) &&
            (identical(other.generatedAt, generatedAt) ||
                const DeepCollectionEquality().equals(
                  other.generatedAt,
                  generatedAt,
                )));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(insights) ^
      const DeepCollectionEquality().hash(alerts) ^
      const DeepCollectionEquality().hash(kpis) ^
      const DeepCollectionEquality().hash(recommendations) ^
      const DeepCollectionEquality().hash(nextSteps) ^
      const DeepCollectionEquality().hash(generatedAt) ^
      runtimeType.hashCode;
}

extension $SummaryResponseExtension on SummaryResponse {
  SummaryResponse copyWith({
    List<String>? insights,
    List<String>? alerts,
    Map<String, dynamic>? kpis,
    List<String>? recommendations,
    String? nextSteps,
    String? generatedAt,
  }) {
    return SummaryResponse(
      insights: insights ?? this.insights,
      alerts: alerts ?? this.alerts,
      kpis: kpis ?? this.kpis,
      recommendations: recommendations ?? this.recommendations,
      nextSteps: nextSteps ?? this.nextSteps,
      generatedAt: generatedAt ?? this.generatedAt,
    );
  }

  SummaryResponse copyWithWrapped({
    Wrapped<List<String>>? insights,
    Wrapped<List<String>>? alerts,
    Wrapped<Map<String, dynamic>>? kpis,
    Wrapped<List<String>>? recommendations,
    Wrapped<String>? nextSteps,
    Wrapped<String>? generatedAt,
  }) {
    return SummaryResponse(
      insights: (insights != null ? insights.value : this.insights),
      alerts: (alerts != null ? alerts.value : this.alerts),
      kpis: (kpis != null ? kpis.value : this.kpis),
      recommendations: (recommendations != null
          ? recommendations.value
          : this.recommendations),
      nextSteps: (nextSteps != null ? nextSteps.value : this.nextSteps),
      generatedAt: (generatedAt != null ? generatedAt.value : this.generatedAt),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class SummaryRequest {
  const SummaryRequest({this.days, this.patientId});

  factory SummaryRequest.fromJson(Map<String, dynamic> json) =>
      _$SummaryRequestFromJson(json);

  static const toJsonFactory = _$SummaryRequestToJson;
  Map<String, dynamic> toJson() => _$SummaryRequestToJson(this);

  @JsonKey(name: 'days')
  final int? days;
  @JsonKey(name: 'patient_id')
  final int? patientId;
  static const fromJsonFactory = _$SummaryRequestFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is SummaryRequest &&
            (identical(other.days, days) ||
                const DeepCollectionEquality().equals(other.days, days)) &&
            (identical(other.patientId, patientId) ||
                const DeepCollectionEquality().equals(
                  other.patientId,
                  patientId,
                )));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(days) ^
      const DeepCollectionEquality().hash(patientId) ^
      runtimeType.hashCode;
}

extension $SummaryRequestExtension on SummaryRequest {
  SummaryRequest copyWith({int? days, int? patientId}) {
    return SummaryRequest(
      days: days ?? this.days,
      patientId: patientId ?? this.patientId,
    );
  }

  SummaryRequest copyWithWrapped({
    Wrapped<int?>? days,
    Wrapped<int?>? patientId,
  }) {
    return SummaryRequest(
      days: (days != null ? days.value : this.days),
      patientId: (patientId != null ? patientId.value : this.patientId),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class ChatResponse {
  const ChatResponse({
    required this.reply,
    required this.conversationId,
    required this.timestamp,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatResponseFromJson(json);

  static const toJsonFactory = _$ChatResponseToJson;
  Map<String, dynamic> toJson() => _$ChatResponseToJson(this);

  @JsonKey(name: 'reply')
  final String reply;
  @JsonKey(name: 'conversation_id')
  final String conversationId;
  @JsonKey(name: 'timestamp')
  final String timestamp;
  static const fromJsonFactory = _$ChatResponseFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is ChatResponse &&
            (identical(other.reply, reply) ||
                const DeepCollectionEquality().equals(other.reply, reply)) &&
            (identical(other.conversationId, conversationId) ||
                const DeepCollectionEquality().equals(
                  other.conversationId,
                  conversationId,
                )) &&
            (identical(other.timestamp, timestamp) ||
                const DeepCollectionEquality().equals(
                  other.timestamp,
                  timestamp,
                )));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(reply) ^
      const DeepCollectionEquality().hash(conversationId) ^
      const DeepCollectionEquality().hash(timestamp) ^
      runtimeType.hashCode;
}

extension $ChatResponseExtension on ChatResponse {
  ChatResponse copyWith({
    String? reply,
    String? conversationId,
    String? timestamp,
  }) {
    return ChatResponse(
      reply: reply ?? this.reply,
      conversationId: conversationId ?? this.conversationId,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  ChatResponse copyWithWrapped({
    Wrapped<String>? reply,
    Wrapped<String>? conversationId,
    Wrapped<String>? timestamp,
  }) {
    return ChatResponse(
      reply: (reply != null ? reply.value : this.reply),
      conversationId: (conversationId != null
          ? conversationId.value
          : this.conversationId),
      timestamp: (timestamp != null ? timestamp.value : this.timestamp),
    );
  }
}

@JsonSerializable(explicitToJson: true)
class ChatRequest {
  const ChatRequest({required this.message, this.contextType});

  factory ChatRequest.fromJson(Map<String, dynamic> json) =>
      _$ChatRequestFromJson(json);

  static const toJsonFactory = _$ChatRequestToJson;
  Map<String, dynamic> toJson() => _$ChatRequestToJson(this);

  @JsonKey(name: 'message')
  final String message;
  @JsonKey(name: 'context_type')
  final String? contextType;
  static const fromJsonFactory = _$ChatRequestFromJson;

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is ChatRequest &&
            (identical(other.message, message) ||
                const DeepCollectionEquality().equals(
                  other.message,
                  message,
                )) &&
            (identical(other.contextType, contextType) ||
                const DeepCollectionEquality().equals(
                  other.contextType,
                  contextType,
                )));
  }

  @override
  String toString() => jsonEncode(this);

  @override
  int get hashCode =>
      const DeepCollectionEquality().hash(message) ^
      const DeepCollectionEquality().hash(contextType) ^
      runtimeType.hashCode;
}

extension $ChatRequestExtension on ChatRequest {
  ChatRequest copyWith({String? message, String? contextType}) {
    return ChatRequest(
      message: message ?? this.message,
      contextType: contextType ?? this.contextType,
    );
  }

  ChatRequest copyWithWrapped({
    Wrapped<String>? message,
    Wrapped<String?>? contextType,
  }) {
    return ChatRequest(
      message: (message != null ? message.value : this.message),
      contextType: (contextType != null ? contextType.value : this.contextType),
    );
  }
}

// ignore: unused_element
String? _dateToJson(DateTime? date) {
  if (date == null) {
    return null;
  }

  final year = date.year.toString();
  final month = date.month < 10 ? '0${date.month}' : date.month.toString();
  final day = date.day < 10 ? '0${date.day}' : date.day.toString();

  return '$year-$month-$day';
}

class Wrapped<T> {
  final T value;
  const Wrapped.value(this.value);
}
