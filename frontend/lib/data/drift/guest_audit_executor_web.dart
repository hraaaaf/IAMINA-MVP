import 'package:drift/drift.dart' show LazyDatabase, QueryExecutor;
import 'package:drift/wasm.dart' show WasmDatabase;
import 'package:sqlite3/wasm.dart' show InMemoryFileSystem, WasmSqlite3;

// Loaded ONLY on Flutter Web via dart.library.js_interop.
// Guest synthetic UI is RAM-only; never use an OPFS/IndexedDB fallback.
QueryExecutor openVolatileGuestWeb({Uri? sqlite3Wasm}) {
  return LazyDatabase(() async {
    final sqlite = await WasmSqlite3.loadFromUrl(
      sqlite3Wasm ?? Uri.parse('sqlite3.wasm'),
    ).timeout(
      const Duration(seconds: 12),
      onTimeout: () => throw StateError('w02_guest_wasm_load_timeout'),
    );
    sqlite.registerVirtualFileSystem(InMemoryFileSystem(), makeDefault: true);
    return WasmDatabase.opened(
      sqlite.openInMemory(),
      closeUnderlyingOnClose: true,
    );
  });
}
