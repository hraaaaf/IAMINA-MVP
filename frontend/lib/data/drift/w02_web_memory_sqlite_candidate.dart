import 'dart:typed_data';

import 'package:drift/wasm.dart';
import 'package:sqlite3/wasm.dart';
import 'package:typed_data/typed_buffers.dart';

/// W02 isolated proof-of-concept. This is NOT opened by AppDatabase or a
/// patient route. Persistent SQLite/OPFS/IndexedDB is intentionally forbidden.
///
/// Caller must first authenticate account, encrypted envelope and rollback
/// floor before providing [authenticatedSnapshot]. This class does not do so.
final class W02WebMemorySqliteCandidate {
  static const _path = '/iamina_w02_volatile.db';
  static const maxSnapshotBytes = 64 * 1024 * 1024;
  static const _header = <int>[
    0x53, 0x51, 0x4c, 0x69, 0x74, 0x65, 0x20, 0x66,
    0x6f, 0x72, 0x6d, 0x61, 0x74, 0x20, 0x33, 0x00,
  ];

  final InMemoryFileSystem _memory;
  final CommonDatabase _sqlite;
  final WasmDatabase executor;
  bool _closed = false;

  W02WebMemorySqliteCandidate._(this._memory, this._sqlite, this.executor);

  static void _assertSnapshot(Uint8List bytes) {
    if (bytes.length < 100 || bytes.length > maxSnapshotBytes) {
      throw const FormatException('w02_invalid_sqlite_snapshot_size');
    }
    for (var i = 0; i < _header.length; i++) {
      if (bytes[i] != _header[i]) {
        throw const FormatException('w02_invalid_sqlite_header');
      }
    }
  }

  /// Only the memory VFS is registered; no persistent fallback is available.
  /// An absent snapshot means a new *synthetic* database for tests ONLY.
  static Future<W02WebMemorySqliteCandidate> open({
    required Uint8List? authenticatedSnapshot,
    Uri? sqlite3Wasm,
  }) async {
    final initial = authenticatedSnapshot;
    if (initial != null) _assertSnapshot(initial);

    final sqlite3 = await WasmSqlite3.loadFromUrl(
      sqlite3Wasm ?? Uri.parse('sqlite3.wasm'),
    );
    final memory = InMemoryFileSystem();
    sqlite3.registerVirtualFileSystem(memory, makeDefault: true);
    if (initial != null) {
      memory.fileData[_path] = Uint8Buffer()..addAll(initial);
    }

    CommonDatabase? raw;
    try {
      raw = sqlite3.open(_path);
      raw.execute('PRAGMA journal_mode=DELETE');
      raw.execute('PRAGMA temp_store=MEMORY');
      if (raw.select('PRAGMA journal_mode').first.values.first != 'delete') {
        throw StateError('w02_persistent_journal_not_excluded');
      }
      if (raw.select('PRAGMA temp_store').first.values.first != 2) {
        throw StateError('w02_disk_temp_not_excluded');
      }
      if (initial != null &&
          raw.select('PRAGMA quick_check').first.values.first != 'ok') {
        throw StateError('w02_sqlite_integrity_failed');
      }
      final executor = WasmDatabase.opened(
        raw,
        closeUnderlyingOnClose: false,
      );
      return W02WebMemorySqliteCandidate._(memory, raw, executor);
    } catch (_) {
      raw?.dispose();
      memory.fileData.clear();
      rethrow;
    }
  }

  /// Quiescent-snapshot primitive. Call only after all Drift transactions are
  /// finished; no clinical write-through or crash atomicity is provided here.
  Uint8List exportSnapshot() {
    if (_closed) throw StateError('w02_memory_connection_closed');
    if (!_sqlite.autocommit) throw StateError('w02_unfinished_transaction');
    if (_sqlite.select('PRAGMA quick_check').first.values.first != 'ok') {
      throw StateError('w02_sqlite_integrity_failed');
    }
    for (final item in _memory.fileData.entries) {
      if (item.key != _path && item.value?.isNotEmpty == true) {
        throw StateError('w02_unexpected_sqlite_sidecar');
      }
    }
    final file = _memory.fileData[_path];
    if (file == null) throw StateError('w02_empty_sqlite_database');
    final bytes = Uint8List.fromList(file);
    _assertSnapshot(bytes);
    return bytes;
  }

  Future<void> close() async {
    if (_closed) return;
    _closed = true;
    try {
      await executor.close();
    } finally {
      _sqlite.dispose();
      _memory.fileData.clear();
    }
  }
}
