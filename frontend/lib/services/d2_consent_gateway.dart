/// D2 — server-owned, revocable consent for *future nonurgent previews* only.
/// This is not a browser push, message producer, local patient cache or inbox.
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_epoch.dart';

abstract class D2ConsentGateway {
  Future<D2ConsentStatus> read(String locale);
  Future<D2ConsentStatus> grant(D2ConsentStatus acceptedNotice);
  Future<D2ConsentStatus> withdraw(String locale);
}

class D2ConsentStatus {
  final bool optedIn;
  final String noticeText;
  final String noticeVersion;
  final String noticeHash;
  final String locale;
  final String? grantedAt;

  const D2ConsentStatus({
    required this.optedIn,
    required this.noticeText,
    required this.noticeVersion,
    required this.noticeHash,
    required this.locale,
    this.grantedAt,
  });

  factory D2ConsentStatus.fromResponse(dynamic raw) {
    if (raw is! Map<String, dynamic> ||
        raw['purpose'] != 'proactive_in_app_preview' ||
        raw['delivery_enabled'] != false ||
        raw['browser_push_enabled'] != false ||
        raw['opted_in'] is! bool ||
        raw['notice_text'] is! String ||
        raw['notice_version'] is! String ||
        raw['notice_hash'] is! String ||
        raw['locale'] is! String ||
        (raw['notice_text'] as String).trim().isEmpty ||
        (raw['notice_hash'] as String).length != 64) {
      throw StateError('Unverified D2 consent contract');
    }
    return D2ConsentStatus(
      optedIn: raw['opted_in'] as bool,
      noticeText: raw['notice_text'] as String,
      noticeVersion: raw['notice_version'] as String,
      noticeHash: raw['notice_hash'] as String,
      locale: raw['locale'] as String,
      grantedAt: raw['granted_at'] as String?,
    );
  }
}

class D2ApiConsentGateway implements D2ConsentGateway {
  final ApiClient api;
  const D2ApiConsentGateway(this.api);

  Future<D2ConsentStatus> _perform(
    Future<dynamic> Function() request,
  ) async {
    final originEpoch = AuthEpoch.value;
    final response = await request();
    requireCurrentAuthEpoch(originEpoch);
    if (!response.isSuccessful) {
      throw StateError('D2 consent unavailable');
    }
    return D2ConsentStatus.fromResponse(response.body);
  }

  @override
  Future<D2ConsentStatus> read(String locale) => _perform(() =>
      api.client.get(Uri(
        path: '/api/v1/account/notification-preview-consent',
        queryParameters: {'locale': locale},
      )));

  @override
  Future<D2ConsentStatus> grant(D2ConsentStatus notice) => _perform(() =>
      api.client.put(
        Uri.parse('/api/v1/account/notification-preview-consent'),
        body: <String, dynamic>{
          'locale': notice.locale,
          'notice_version': notice.noticeVersion,
          'notice_hash': notice.noticeHash,
          'acknowledgment': 'ENABLE_PREVIEW_ONLY',
        },
      ));

  @override
  Future<D2ConsentStatus> withdraw(String locale) => _perform(() =>
      api.client.delete(
        Uri.parse('/api/v1/account/notification-preview-consent'),
      ));
}
