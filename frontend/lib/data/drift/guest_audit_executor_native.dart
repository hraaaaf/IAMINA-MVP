import 'package:drift/drift.dart' show QueryExecutor;

// The native Flutter VM must never import drift/wasm.dart or sqlite3/wasm.dart.
// Regular native guest SQLite is selected by database.dart before this stub.
QueryExecutor openVolatileGuestWeb({Uri? sqlite3Wasm}) =>
    throw StateError('w02_guest_web_executor_not_available_on_native');
