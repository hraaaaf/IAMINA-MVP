import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/legacy_visitor_gate_policy.dart';

void main() {
  test('legacy IndexedDB present always requires recovery', () {
    for (final certified in [false, true]) {
      expect(
        decideLegacyVisitorGate(
          indexedDbPresence: LegacyPresence.present,
          fullLegacyInventoryCertified: certified,
        ),
        LegacyVisitorGate.recoveryRequired,
      );
    }
  });

  test('unavailable/ambiguous inventory fails closed', () {
    for (final certified in [false, true]) {
      expect(
        decideLegacyVisitorGate(
          indexedDbPresence: LegacyPresence.unknown,
          fullLegacyInventoryCertified: certified,
        ),
        LegacyVisitorGate.recoveryRequired,
      );
    }
  });

  test('empty IndexedDB alone does not prove fresh installation', () {
    expect(
      decideLegacyVisitorGate(
        indexedDbPresence: LegacyPresence.absent,
        fullLegacyInventoryCertified: false,
      ),
      LegacyVisitorGate.recoveryRequired,
    );
  });

  test('even certified empty legacy inventory never authorizes clinical use', () {
    expect(
      decideLegacyVisitorGate(
        indexedDbPresence: LegacyPresence.absent,
        fullLegacyInventoryCertified: true,
      ),
      LegacyVisitorGate.notCertified,
    );
  });
}
