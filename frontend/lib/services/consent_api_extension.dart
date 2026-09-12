import 'api_client.dart';
import 'consent_notice_contract.dart';

extension VersionedConsentApi on ApiClient {
  Future<bool> giveVersionedConsent(ConsentNoticeClaim claim) async {
    try {
      final response = await client.post(
        Uri.parse('/api/v1/account/consent'),
        body: {
          'notice_version': claim.version,
          'notice_hash': claim.noticeHash,
          'locale': claim.locale,
        },
      );
      if (!response.isSuccessful || response.body is! Map) return false;
      final body = Map<String, dynamic>.from(response.body as Map);
      return body['ai_consent_given'] == true &&
          body['notice_version'] == claim.version &&
          body['notice_hash'] == claim.noticeHash &&
          body['locale'] == claim.locale;
    } catch (_) {
      return false;
    }
  }
}
