// CI-only L01/D18 legacy DB bootstrap experiment. Never import this entrypoint
// from the patient app. Uses an isolated Chrome profile and synthetic origin.
import 'package:flutter/material.dart';

import 'data/drift/database.dart';
import 'services/medical_vault_protected_state.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Control phase: no database constructor or query of any kind.
  // Experimental phase: reproduce main.dart's legacy default-name query.
  final phase = Uri.base.queryParameters['phase'];
  if (phase == 'legacy_probe') {
    final legacy = AppDatabase.defaults();
    try {
      await hasProtectedMedicalVaultRows(legacy);
    } finally {
      await legacy.close();
    }
  } else if (phase != 'control') {
    throw StateError('Unknown CI-only L01 phase; no patient data allowed');
  }

  runApp(const MaterialApp(
    home: Scaffold(
      body: Center(child: Text('IAMINA L01 SYNTHETIC LEGACY DB PROBE')),
    ),
  ));
}
