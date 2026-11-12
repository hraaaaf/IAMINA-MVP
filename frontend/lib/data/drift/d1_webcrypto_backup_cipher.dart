// D1 research WebCrypto bridge to the real authenticated backup interface.
// This code has not undergone independent cryptographic/security review.
// ignore: avoid_web_libraries_in_flutter
import 'dart:js_interop';
import 'dart:typed_data';

import 'd1_authenticated_backup_boundary.dart';

@JS('iaminaD1CryptoBackup.seal')
external JSPromise<JSString> _sealJs(
  JSString owner, JSString plaintext, JSUint8Array recovery);

@JS('iaminaD1CryptoBackup.open')
external JSPromise<JSString> _openJs(
  JSString owner, JSString envelope, JSUint8Array recovery);

final class D1WebCryptoBackupCipher implements D1AuthenticatedBackupCipher {
  final Uint8List _recovery;
  bool _disposed = false;

  /// A random 32-byte recovery key from an approved custody flow is required.
  /// A password/PIN, email, bearer, ID, or fixture key is NOT sufficient.
  D1WebCryptoBackupCipher(Uint8List recovery)
      : _recovery=Uint8List.fromList(recovery) {
    if(recovery.length!=32||recovery.every((v)=>v==0)) {
      _recovery.fillRange(0,_recovery.length,0);
      throw StateError('D1_BACKUP_KEY_UNVERIFIED');
    }
  }

  void dispose(){
    _disposed=true;
    _recovery.fillRange(0,_recovery.length,0);
  }

  JSUint8Array _key() {
    if(_disposed)throw StateError('D1_BACKUP_CIPHER_RETIRED');
    return _recovery.toJS;
  }

  @override
  Future<String> seal({required String owner,required String plaintextJson}) async {
    if(_disposed)throw StateError('D1_BACKUP_CIPHER_RETIRED');
    try {
      final result=await _sealJs(owner.toJS,plaintextJson.toJS,_key()).toDart;
      if(_disposed)throw StateError('D1_BACKUP_CIPHER_RETIRED');
      return result.toDart;
    } catch (_) {
      throw StateError('D1_BACKUP_ENCRYPTION_FAILED');
    }
  }

  @override
  Future<String> authenticateAndOpen({
    required String expectedOwner,required String sealedEnvelope,
  }) async {
    if(_disposed)throw StateError('D1_BACKUP_CIPHER_RETIRED');
    try {
      final result=await _openJs(
        expectedOwner.toJS,sealedEnvelope.toJS,_key(),
      ).toDart;
      if(_disposed)throw StateError('D1_BACKUP_CIPHER_RETIRED');
      return result.toDart;
    } catch (_) {
      throw StateError('D1_BACKUP_AUTH_FAILED');
    }
  }
}
