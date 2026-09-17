import 'dart:convert';

enum AppLockCapability { supported, unavailable, insecureContext }

class AppLockCredential {
  static const int currentVersion = 1;

  final int version;
  final String credentialId;
  final String publicKeySpki;
  final String rpId;
  final String origin;
  final int signCount;

  const AppLockCredential({
    this.version = currentVersion,
    required this.credentialId,
    required this.publicKeySpki,
    required this.rpId,
    required this.origin,
    required this.signCount,
  });

  AppLockCredential copyWith({int? signCount}) => AppLockCredential(
        version: version,
        credentialId: credentialId,
        publicKeySpki: publicKeySpki,
        rpId: rpId,
        origin: origin,
        signCount: signCount ?? this.signCount,
      );

  Map<String, Object> toJson() => {
        'version': version,
        'credentialId': credentialId,
        'publicKeySpki': publicKeySpki,
        'rpId': rpId,
        'origin': origin,
        'signCount': signCount,
      };

  String encode() => jsonEncode(toJson());

  factory AppLockCredential.decode(String raw) {
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Invalid app-lock credential payload');
    }
    final version = decoded['version'];
    final credentialId = decoded['credentialId'];
    final publicKeySpki = decoded['publicKeySpki'];
    final rpId = decoded['rpId'];
    final origin = decoded['origin'];
    final signCount = decoded['signCount'];

    if (version != currentVersion ||
        credentialId is! String ||
        credentialId.isEmpty ||
        publicKeySpki is! String ||
        publicKeySpki.isEmpty ||
        rpId is! String ||
        rpId.isEmpty ||
        origin is! String ||
        origin.isEmpty ||
        signCount is! int ||
        signCount < 0) {
      throw const FormatException('Invalid app-lock credential fields');
    }

    final originUri = Uri.tryParse(origin);
    if (originUri == null ||
        !originUri.hasScheme ||
        originUri.host.isEmpty ||
        (originUri.scheme != 'https' &&
            originUri.host != 'localhost' &&
            originUri.host != '127.0.0.1' &&
            originUri.host != '::1')) {
      throw const FormatException('Invalid app-lock credential origin');
    }

    return AppLockCredential(
      version: version,
      credentialId: credentialId,
      publicKeySpki: publicKeySpki,
      rpId: rpId,
      origin: origin,
      signCount: signCount,
    );
  }
}

class AppLockAssertion {
  final int signCount;

  const AppLockAssertion({required this.signCount});
}

class AppLockException implements Exception {
  final String code;

  const AppLockException(this.code);

  @override
  String toString() => 'AppLockException($code)';
}

abstract interface class AppLockAuthenticator {
  Future<AppLockCapability> capability();
  Future<AppLockCredential> enroll();
  Future<AppLockAssertion> unlock(AppLockCredential credential);
}
