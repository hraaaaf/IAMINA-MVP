import 'package:amina/features/profile/profile_screen.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('D7 green profile feedback requires a confirmed treatment outbox', () {
    for (final status in ['pending', 'conflict']) {
      expect(d7ProfileSaveCanShowConfirmed(
        mirrorConfirmed: true,
        treatmentSyncStatus: status,
      ), isFalse);
    }
    expect(d7ProfileSaveCanShowConfirmed(
      mirrorConfirmed: false,
      treatmentSyncStatus: 'confirmed',
    ), isFalse);
    expect(d7ProfileSaveCanShowConfirmed(
      mirrorConfirmed: true,
      treatmentSyncStatus: 'confirmed',
    ), isTrue);
    expect(d7ProfileSaveCanShowConfirmed(
      mirrorConfirmed: true,
      treatmentSyncStatus: null,
    ), isTrue);
  });
}
