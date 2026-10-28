import 'dart:typed_data';

import 'package:amina/data/drift/w02_web_memory_sqlite_candidate.dart';
import 'package:flutter_test/flutter_test.dart';

/// Run with Flutter Web/Chrome. Never enables a real patient vault.
void main() {
  test('W02 Drift WASM writes and reopens only a volatile SQLite snapshot', () async {
    final first = await W02WebMemorySqliteCandidate.open(authenticatedSnapshot: null);
    try {
      await first.executor.runCustom(
        'CREATE TABLE synthetic_logs (id INTEGER PRIMARY KEY, note TEXT NOT NULL)',
        [],
      );
      await first.executor.runInsert(
        'INSERT INTO synthetic_logs (note) VALUES (?)',
        ['W02_SYNTHETIC_734'],
      );
      final encryptedInput = first.exportSnapshot();
      expect(encryptedInput.sublist(0, 16), orderedEquals([
        83, 81, 76, 105, 116, 101, 32, 102,
        111, 114, 109, 97, 116, 32, 51, 0,
      ]));
      final reopened = await W02WebMemorySqliteCandidate.open(
        authenticatedSnapshot: encryptedInput,
      );
      try {
        final rows = await reopened.executor.runSelect(
          'SELECT note FROM synthetic_logs ORDER BY id', [],
        );
        expect(rows.single['note'], 'W02_SYNTHETIC_734');
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
    final empty = await W02WebMemorySqliteCandidate.open(authenticatedSnapshot: null);
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
