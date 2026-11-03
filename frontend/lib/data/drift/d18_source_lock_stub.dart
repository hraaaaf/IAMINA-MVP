import 'dart:async';

import 'd18_source_lock_lease.dart';

Future<D18SourceLockLease> acquireLegacy() =>
    Future.error(UnsupportedError('D18_SOURCE_LOCK_WEB_ONLY'));

Future<D18SourceLockLease> acquirePatient(String scope) =>
    Future.error(UnsupportedError('D18_SOURCE_LOCK_WEB_ONLY'));
