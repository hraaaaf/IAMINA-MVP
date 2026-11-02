// D18 synthetic wrong-key worker. Not used in production.
import 'package:drift/wasm.dart';
import 'd18_cipher_worker_setup.dart';

void main() => WasmDatabase.workerMainForOpen(
  setupAllDatabases: (db) => d18Configure(db, d18Wrong),
);
