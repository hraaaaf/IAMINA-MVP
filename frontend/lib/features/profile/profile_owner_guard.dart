/// Identity guard for editing an existing patient-owned local profile.
///
/// Preserve the existing primary key, reject multiple rows or a mismatched
/// authenticated account, and keep the legacy offline=1 baseline only when
/// no record and no authenticated account exist. This is not certification
/// of complete multi-account database isolation.
int resolveProfileRecordOwner({
  required Iterable<int> localUserIds,
  required int? authenticatedUserId,
}) {
  final ids = localUserIds.toList(growable: false);
  if (ids.length > 1) {
    throw StateError('Ambiguous local patient ownership.');
  }
  if (authenticatedUserId != null && authenticatedUserId <= 0) {
    throw StateError('Invalid account identity.');
  }
  if (ids.isEmpty) return authenticatedUserId ?? 1;
  final existing = ids.single;
  if (existing <= 0 ||
      (authenticatedUserId != null && existing != authenticatedUserId)) {
    throw StateError('Patient profile ownership mismatch.');
  }
  return existing;
}
