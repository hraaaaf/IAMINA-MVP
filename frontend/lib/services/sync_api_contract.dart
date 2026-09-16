class SyncApiException implements Exception {
  final String operation;
  final String errorType;

  const SyncApiException({
    required this.operation,
    required this.errorType,
  });

  @override
  String toString() =>
      'SyncApiException(operation: $operation, errorType: $errorType)';
}

Future<T> guardSyncApiCall<T>(
  String operation,
  Future<T> Function() request,
) async {
  try {
    return await request();
  } catch (error, stackTrace) {
    Error.throwWithStackTrace(
      SyncApiException(
        operation: operation,
        errorType: error.runtimeType.toString(),
      ),
      stackTrace,
    );
  }
}

List<String> parseBatchSyncIds(Object? body) {
  if (body == null) return const <String>[];
  if (body is! Map) {
    throw const FormatException('Unexpected batch sync response body.');
  }

  final rawIds = body['synced_ids'];
  if (rawIds == null) return const <String>[];
  if (rawIds is! List || rawIds.any((value) => value is! String)) {
    throw const FormatException('Unexpected batch sync synced_ids payload.');
  }

  return rawIds.cast<String>().toList(growable: false);
}
