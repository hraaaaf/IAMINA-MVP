import 'dart:async';

// D18 CANARY: a cooperative source lock lives exactly as long as its DB.
final class D18SourceLockLease {
  final Future<void> Function() _release;
  Future<void>? _closing;

  D18SourceLockLease(this._release);

  Future<void> close() => _closing ??= _release();
}
