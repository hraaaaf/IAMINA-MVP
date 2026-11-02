// D18 synthetic test worker. This is NOT the product worker.
import 'package:drift/wasm.dart';
import 'd18_cipher_worker_setup.dart';

void main() => WasmDatabase.workerMainForOpen(
  setupAllDatabases: (db) => d18Configure(db, d18Right),
);
