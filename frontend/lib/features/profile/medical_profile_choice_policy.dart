/// D7: presentation-only grouping of *patient-declared* treatments.
////
//// These are not prescribing options, recommendations or clinical rules.
//// No selection changes clinical thresholds, risk triage or medications.
const knownDiabetesTypes = <String>[
  'type1', 'type2', 'gestational', 'pre', 'other', 'unknown',
];

const declaredTreatmentChoices = <String>[
  'lifestyle', 'tablets', 'insulin', 'other', 'unknown',
];

class TreatmentPresentation {
  final List<String> primary;
  final List<String> onRequest;
  const TreatmentPresentation(this.primary, this.onRequest);
}

/// Initial visibility follows common *reporting* paths, never care advice.
///
/// Pre-diabetes does NOT foreground insulin. If actually prescribed, insulin
/// remains reportable under "Other treatment I already receive" to prevent
/// erasing an unusual, but possibly real, patient declaration.
///
/// All IDs remain selectable for *all* types if patient explicitly requests.
/// UI must never infer an insulin prescription, diagnosis or eligibility.
TreatmentPresentation treatmentPresentation(String? diabetesType) {
  final priority = switch (diabetesType) {
    'type1' => <String>['insulin', 'lifestyle'],
    'type2' => <String>['lifestyle', 'tablets'],
    'gestational' => <String>['lifestyle', 'insulin'],
    'pre' => <String>['lifestyle'],
    _ => <String>[],
  };
  return TreatmentPresentation(
    List.unmodifiable(priority),
    List.unmodifiable(
      declaredTreatmentChoices.where((item) => !priority.contains(item)),
    ),
  );
}

/// Changing the declared diagnosis must never overwrite or remove a
/// treatment someone said they *actually takes*.
bool isValidPatientDeclaredTreatment(String? treatment) =>
    treatment != null && declaredTreatmentChoices.contains(treatment);

bool isValidPatientDeclaredDiabetesType(String? type) =>
    type != null && knownDiabetesTypes.contains(type);
