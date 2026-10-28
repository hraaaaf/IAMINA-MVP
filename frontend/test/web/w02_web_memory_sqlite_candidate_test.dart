import 'dart:typed_data';

import 'package:amina/data/drift/w02_web_memory_sqlite_candidate.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/services.dart' show rootBundle;

/// Run with Flutter Web/Chrome. Never enables a real patient vault.
Future<Uint8List> loadTestWasm() async {
  print('W02_STAGE asset_load:start');
  final asset = await rootBundle
      .load('web/sqlite3.wasm')
      .timeout(const Duration(seconds: 12));
  final bytes =
      asset.buffer.asUint8List(asset.offsetInBytes, asset.lengthInBytes);
  print('W02_STAGE asset_load:done bytes=${bytes.length}');
  expect(bytes.length, greaterThan(100000));
  return bytes;
}

void traceW02(String stage) => print('W02_STAGE $stage');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('W02 Drift WASM writes and reopens only a volatile SQLite snapshot', () async {
    final wasm = await loadTestWasm();
    final first = await W02WebMemorySqliteCandidate.open(
      authenticatedSnapshot: null,
      sqlite3WasmBytes: wasm,
      trace: traceW02,
    );
    print('W02_STAGE first_open:done');
    try {
      print('W02_STAGE create_table:start');
      await first.executor.runCustom(
        'CREATE TABLE synthetic_logs (id INTEGER PRIMARY KEY, note TEXT NOT NULL)',
        [],
      );
      print('W02_STAGE create_table:done');
      print('W02_STAGE insert:start');
      await first.executor.runInsert(
        'INSERT INTO synthetic_logs (note) VALUES (?)',
        ['W02_SYNTHETIC_734'],
      );
      print('W02_STAGE insert:done');
      print('W02_STAGE export:start');
      final encryptedInput = first.exportSnapshot();
      print('W02_STAGE export:done');
      expect(encryptedInput.sublist(0, 16), orderedEquals([
        83, 81, 76, 105, 116, 101, 32, 102,
        111, 114, 109, 97, 116, 32, 51, 0,
      ]));
      final reopened = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: encryptedInput,
        sqlite3WasmBytes: wasm,
        trace: traceW02,
      );
      print('W02_STAGE reopen:done');
      try {
        print('W02_STAGE select:start');
        final rows = await reopened.executor.runSelect(
          'SELECT note FROM synthetic_logs ORDER BY id', [],
        );
        expect(rows.single['note'], 'W02_SYNTHETIC_734');
        print('W02_STAGE select:done');
      } finally {
        await reopened.close();
        encryptedInput.fillRange(0, encryptedInput.length, 0);
      }
    } finally {
      await first.close();
    }
  });

  test('W02 refuses invalid snapshot before initializing SQLite', () async {
    await expectLater(
      W02WebMemorySqliteCandidate.open(authenticatedSnapshot: Uint8List(150)),
      throwsFormatException,
    );
  });

  test('W02 new volatile connection cannot see prior synthetic records', () async {
    final wasm = await loadTestWasm();
    final empty = await W02WebMemorySqliteCandidate.open(
      authenticatedSnapshot: null,
      sqlite3WasmBytes: wasm,
      trace: traceW02,
    );
    try {
      final rows = await empty.executor.runSelect(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'synthetic_logs'",
        [],
      );
      expect(rows, isEmpty);
    } finally {
      await empty.close();
    }
  });
}
