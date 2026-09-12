import 'package:flutter_test/flutter_test.dart';
import 'package:amina/services/consent_notice_contract.dart';

void main() {
  test('known locales resolve to current exact claims', () {
    final fr = ConsentNoticeContract.forLocale('fr-FR');
    final en = ConsentNoticeContract.forLocale('en-US');
    final ar = ConsentNoticeContract.forLocale('ar');
    final darija = ConsentNoticeContract.forLocale('ar-MA');

    expect(fr.version, '2026-09-12.1');
    expect(fr.locale, 'fr');
    expect(en.locale, 'en');
    expect(ar.locale, 'ar');
    expect(darija.locale, 'ar-MA');
    expect(darija.noticeHash, ar.noticeHash);
  });

  test('modified evidence is not current', () {
    final claim = ConsentNoticeContract.forLocale('fr');
    expect(
      ConsentNoticeContract.isCurrent(
        versionValue: claim.version,
        noticeHash: claim.noticeHash,
        locale: claim.locale,
      ),
      isTrue,
    );
    expect(
      ConsentNoticeContract.isCurrent(
        versionValue: claim.version,
        noticeHash: '0' * 64,
        locale: claim.locale,
      ),
      isFalse,
    );
    expect(
      ConsentNoticeContract.isCurrent(
        versionValue: 'legacy',
        noticeHash: claim.noticeHash,
        locale: claim.locale,
      ),
      isFalse,
    );
  });

  test('unsupported locale fails closed', () {
    expect(
      () => ConsentNoticeContract.forLocale('xx'),
      throwsArgumentError,
    );
    expect(
      ConsentNoticeContract.isCurrent(
        versionValue: ConsentNoticeContract.version,
        noticeHash: '0' * 64,
        locale: 'xx',
      ),
      isFalse,
    );
  });
}
