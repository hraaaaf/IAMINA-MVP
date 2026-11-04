// D18 experiment only: synthetic keys, never shipped in the patient runtime.
// ignore_for_file: depend_on_referenced_packages
import 'package:sqlite3/common.dart';

const d18Right = 'D18-CI-ONLY-MC-KEY-20261102';
const d18Wrong = 'D18-CI-ONLY-MC-WRONG-20261102';

/// Called before Drift schema access, in BOTH worker and local fallback.
void d18Configure(CommonDatabase db, String key) {
  if (key != d18Right && key != d18Wrong) {
    throw StateError('D18_POC_INVALID_KEY_SOURCE');
  }
  final cipher = db.select('PRAGMA cipher');
  if (cipher.length != 1 || cipher.first.values.first is! String) {
    throw StateError('D18_POC_CIPHER_UNAVAILABLE');
  }
  // Fixed keys are synthetic browser fixtures ONLY.
  db.execute("PRAGMA key = '$key'");
  // PRAGMA key itself does not validate the key: actual read must succeed.
  db.select('SELECT count(*) FROM sqlite_master');
}
