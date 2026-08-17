import 'package:drift/drift.dart';

import 'database.dart';

extension DashboardTrendQueries on AppDatabase {
  Stream<List<LogEntryData>> watchDashboardTrendLogs(
    DateTime start,
    DateTime end,
  ) {
    final query = select(logEntries)
      ..where(
        (row) =>
            row.loggedAt.isBetweenValues(start, end) |
            (row.loggedAt.isNull() & row.createdAt.isBetweenValues(start, end)),
      );
    return query.watch();
  }

  Stream<List<MedicationEventData>> watchDashboardMedicationEvents(
    DateTime start,
    DateTime end,
  ) {
    return (select(medicationEvents)
          ..where((row) => row.takenAt.isBetweenValues(start, end))
          ..orderBy([
            (row) => OrderingTerm(
              expression: row.takenAt,
              mode: OrderingMode.asc,
            ),
          ]))
        .watch();
  }
}
