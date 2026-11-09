/// Patient declarations, NOT clinical or prescribing recommendations.
enum D7TreatmentStatus { notAnswered, unsure, declared, noneDeclared }

String d7StateCode(D7TreatmentStatus s) => switch (s) {
  D7TreatmentStatus.notAnswered => 'not_answered',
  D7TreatmentStatus.unsure => 'unsure',
  D7TreatmentStatus.declared => 'declared',
  D7TreatmentStatus.noneDeclared => 'none_declared',
};

const d7TreatmentCodes = ['lifestyle', 'oral_meds', 'insulin', 'other'];

final class D7TreatmentDeclaration {
  final D7TreatmentStatus state;
  final List<String> codes;

  D7TreatmentDeclaration(this.state, Iterable<String> codes)
      : codes = List.unmodifiable(codes) {
    if (this.codes.length != this.codes.toSet().length ||
        this.codes.any((c) => !d7TreatmentCodes.contains(c))) {
      throw ArgumentError('Unsupported or duplicate treatment declaration');
    }
    if ((state == D7TreatmentStatus.declared) != this.codes.isNotEmpty) {
      throw ArgumentError('Declaration state and codes disagree');
    }
  }

  factory D7TreatmentDeclaration.later() =>
      D7TreatmentDeclaration(D7TreatmentStatus.notAnswered, const []);

  Map<String, Object> toApiPatch() => {
    'treatment_declaration': {
      'version': 1,
      'state': d7StateCode(state),
      'codes': codes,
    },
  };
}

List<String> d7PrimaryOptions(String? type) => List.unmodifiable(switch (type) {
  'type1' => <String>['insulin'],
  'type2' => <String>['lifestyle', 'oral_meds'],
  'gestational' => <String>['lifestyle', 'insulin'],
  'pre' || 'prediabetes' => <String>['lifestyle'],
  _ => <String>[],
});

List<String> d7OtherOptions(String? type) {
  final primary = d7PrimaryOptions(type);
  return List.unmodifiable(d7TreatmentCodes.where((c) => !primary.contains(c)));
}
