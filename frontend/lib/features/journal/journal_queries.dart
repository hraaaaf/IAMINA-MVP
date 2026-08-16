import 'package:drift/drift.dart';

import '../../data/drift/database.dart';

extension JournalQueries on AppDatabase {
  Stream<List<LogEntryData>> watchAllJournalLogs() {
    return (select(logEntries)
          ..orderBy([
            (t) => OrderingTerm(
              expression: t.loggedAt,
              mode: OrderingMode.desc,
            ),
            (t) => OrderingTerm(
              expression: t.createdAt,
              mode: OrderingMode.desc,
            ),
          ]))
        .watch();
  }

  Stream<List<LogEntryData>> watchJournalLogsInRange(
    DateTime start,
    DateTime end,
  ) {
    return (select(logEntries)
          ..where(
            (t) =>
                t.loggedAt.isBetweenValues(start, end) |
                (t.loggedAt.isNull() & t.createdAt.isBetweenValues(start, end)),
          )
          ..orderBy([
            (t) => OrderingTerm(
              expression: t.loggedAt,
              mode: OrderingMode.desc,
            ),
            (t) => OrderingTerm(
              expression: t.createdAt,
              mode: OrderingMode.desc,
            ),
          ]))
        .watch();
  }
}
