// Phase 12 — Document Pulper models.
// Maps to /api/v1/documents/ingest and /api/v1/documents/ responses.

class GlucoseReadingPreview {
  final double valueMgdl;
  final String? timestamp;
  final String? context;
  final double? originalValue;
  final String? originalUnit;

  const GlucoseReadingPreview({
    required this.valueMgdl,
    this.timestamp,
    this.context,
    this.originalValue,
    this.originalUnit,
  });

  factory GlucoseReadingPreview.fromJson(Map<String, dynamic> j) =>
      GlucoseReadingPreview(
        valueMgdl: (j['value_mgdl'] as num).toDouble(),
        timestamp: j['timestamp'] as String?,
        context: j['context'] as String?,
        originalValue: (j['original_value'] as num?)?.toDouble(),
        originalUnit: j['original_unit'] as String?,
      );
}

class LabValuesPreview {
  final double? hba1cPct;
  final double? fastingGlucoseMgdl;
  final double? totalCholesterolMgdl;
  final double? hdlMgdl;
  final double? ldlMgdl;
  final double? triglyceridesMgdl;
  final double? creatinineUmol;
  final String? reportDate;

  const LabValuesPreview({
    this.hba1cPct,
    this.fastingGlucoseMgdl,
    this.totalCholesterolMgdl,
    this.hdlMgdl,
    this.ldlMgdl,
    this.triglyceridesMgdl,
    this.creatinineUmol,
    this.reportDate,
  });

  bool get isEmpty =>
      hba1cPct == null &&
      fastingGlucoseMgdl == null &&
      totalCholesterolMgdl == null &&
      hdlMgdl == null &&
      ldlMgdl == null &&
      triglyceridesMgdl == null &&
      creatinineUmol == null;

  factory LabValuesPreview.fromJson(Map<String, dynamic> j) => LabValuesPreview(
    hba1cPct: (j['hba1c_pct'] as num?)?.toDouble(),
    fastingGlucoseMgdl: (j['fasting_glucose_mgdl'] as num?)?.toDouble(),
    totalCholesterolMgdl: (j['total_cholesterol_mgdl'] as num?)?.toDouble(),
    hdlMgdl: (j['hdl_mgdl'] as num?)?.toDouble(),
    ldlMgdl: (j['ldl_mgdl'] as num?)?.toDouble(),
    triglyceridesMgdl: (j['triglycerides_mgdl'] as num?)?.toDouble(),
    creatinineUmol: (j['creatinine_umol'] as num?)?.toDouble(),
    reportDate: j['report_date'] as String?,
  );
}

class MedicationPreview {
  final String name;
  final String? dose;
  final String? frequency;

  const MedicationPreview({required this.name, this.dose, this.frequency});

  factory MedicationPreview.fromJson(Map<String, dynamic> j) =>
      MedicationPreview(
        name: j['name'] as String,
        dose: j['dose'] as String?,
        frequency: j['frequency'] as String?,
      );
}

/// Returned by POST /api/v1/documents/ingest (confirm=false).
/// Nothing is persisted yet — this is the preview for user confirmation.
class PulperPreview {
  final String batchId;
  final String documentType;
  final String sourceFormat;
  final double confidence;
  final bool needsReview;
  final List<GlucoseReadingPreview> glucoseReadings;
  final LabValuesPreview labValues;
  final List<MedicationPreview> medications;
  final String clinicalNotes;
  final List<String> warnings;
  final List<String> errors;

  const PulperPreview({
    required this.batchId,
    required this.documentType,
    required this.sourceFormat,
    required this.confidence,
    required this.needsReview,
    required this.glucoseReadings,
    required this.labValues,
    required this.medications,
    required this.clinicalNotes,
    required this.warnings,
    required this.errors,
  });

  bool get hasUsefulData =>
      glucoseReadings.isNotEmpty ||
      !labValues.isEmpty ||
      medications.isNotEmpty ||
      clinicalNotes.isNotEmpty;

  factory PulperPreview.fromJson(Map<String, dynamic> j) => PulperPreview(
    batchId: j['batch_id'] as String,
    documentType: j['document_type'] as String,
    sourceFormat: j['source_format'] as String,
    confidence: (j['confidence'] as num).toDouble(),
    needsReview: j['needs_review'] as bool,
    glucoseReadings: (j['glucose_readings'] as List? ?? [])
        .map((e) => GlucoseReadingPreview.fromJson(e as Map<String, dynamic>))
        .toList(),
    labValues: LabValuesPreview.fromJson(
      (j['lab_values'] as Map<String, dynamic>?) ?? {},
    ),
    medications: (j['medications'] as List? ?? [])
        .map((e) => MedicationPreview.fromJson(e as Map<String, dynamic>))
        .toList(),
    clinicalNotes: j['clinical_notes'] as String? ?? '',
    warnings: List<String>.from(j['warnings'] ?? []),
    errors: List<String>.from(j['errors'] ?? []),
  );
}

/// Returned by POST /api/v1/documents/confirm/{batchId}.
class PulperConfirmResult {
  final bool ok;
  final int? labReportId;
  final int glucoseReadingsSaved;
  final int glucoseDuplicates;
  final List<String> errors;

  const PulperConfirmResult({
    required this.ok,
    this.labReportId,
    required this.glucoseReadingsSaved,
    required this.glucoseDuplicates,
    required this.errors,
  });

  factory PulperConfirmResult.fromJson(Map<String, dynamic> j) =>
      PulperConfirmResult(
        ok: j['ok'] as bool,
        labReportId: j['lab_report_id'] as int?,
        glucoseReadingsSaved: (j['glucose_readings_saved'] as num).toInt(),
        glucoseDuplicates: (j['glucose_duplicates'] as num).toInt(),
        errors: List<String>.from(j['errors'] ?? []),
      );
}

/// Row from GET /api/v1/documents/
class LabReportSummary {
  final int id;
  final String documentType;
  final String sourceFormat;
  final String? reportDate;
  final double? hba1cPct;
  final double? fastingGlucoseMgdl;
  final int glucoseReadingsImported;
  final double confidence;
  final String clinicalNotes;
  final String createdAt;

  const LabReportSummary({
    required this.id,
    required this.documentType,
    required this.sourceFormat,
    this.reportDate,
    this.hba1cPct,
    this.fastingGlucoseMgdl,
    required this.glucoseReadingsImported,
    required this.confidence,
    required this.clinicalNotes,
    required this.createdAt,
  });

  factory LabReportSummary.fromJson(Map<String, dynamic> j) => LabReportSummary(
    id: (j['id'] as num).toInt(),
    documentType: j['document_type'] as String,
    sourceFormat: j['source_format'] as String,
    reportDate: j['report_date'] as String?,
    hba1cPct: (j['hba1c_pct'] as num?)?.toDouble(),
    fastingGlucoseMgdl: (j['fasting_glucose_mgdl'] as num?)?.toDouble(),
    glucoseReadingsImported: (j['glucose_readings_imported'] as num).toInt(),
    confidence: (j['confidence'] as num).toDouble(),
    clinicalNotes: j['clinical_notes'] as String? ?? '',
    createdAt: j['created_at'] as String,
  );
}
