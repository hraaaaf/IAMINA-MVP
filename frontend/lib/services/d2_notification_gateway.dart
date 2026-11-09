/// D2: fail-closed account-scoped in-app inbox contract (NOT clinical advice).
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_epoch.dart';

const _kKinds = {'event', 'proactive'};
const _kCodes = {
  'ai_consent_given',
  'ai_consent_withdrawn',
  'language_pref_available',
};

class D2NoticeItem {
  final int id;
  final String kind;
  final String code;
  final DateTime createdAt;
  final DateTime expiresAt;
  final DateTime? readAt;

  const D2NoticeItem({
    required this.id,
    required this.kind,
    required this.code,
    required this.createdAt,
    required this.expiresAt,
    required this.readAt,
  });

  static D2NoticeItem parse(dynamic value) {
    if (value is! Map<String, dynamic> ||
        value['id'] is! int ||
        value['id'] <= 0 ||
        !_kKinds.contains(value['kind']) ||
        !_kCodes.contains(value['code']) ||
        value['created_at'] is! String ||
        value['expires_at'] is! String ||
        (value['read_at'] != null && value['read_at'] is! String)) {
      throw StateError('Invalid D2 notice item');
    }
    if ((value['kind'] == 'proactive') !=
        (value['code'] == 'language_pref_available')) {
      throw StateError('Inconsistent D2 notification kind');
    }
    final created = DateTime.tryParse(value['created_at'] as String);
    final expiry = DateTime.tryParse(value['expires_at'] as String);
    final read = value['read_at'] == null
        ? null
        : DateTime.tryParse(value['read_at'] as String);
    if (created == null ||
        expiry == null ||
        !expiry.isAfter(created) ||
        (value['read_at'] != null && read == null) ||
        !RegExp(r'(Z|[+-][0-9]{2}:[0-9]{2})$')
            .hasMatch(value['created_at'] as String) ||
        !RegExp(r'(Z|[+-][0-9]{2}:[0-9]{2})$')
            .hasMatch(value['expires_at'] as String)) {
      throw StateError('Unverified D2 timestamp');
    }
    return D2NoticeItem(
      id: value['id'] as int,
      kind: value['kind'] as String,
      code: value['code'] as String,
      createdAt: created.toUtc(),
      expiresAt: expiry.toUtc(),
      readAt: read?.toUtc(),
    );
  }
}

class D2InboxState {
  final bool proactivityEnabled;
  final String locale;
  final String noticeVersion;
  final String noticeDigest;
  final String noticeText;
  final String? csrfToken;
  final List<D2NoticeItem> items;

  const D2InboxState({
    required this.proactivityEnabled,
    required this.locale,
    required this.noticeVersion,
    required this.noticeDigest,
    required this.noticeText,
    this.csrfToken,
    required this.items,
  });

  int get unreadCount => items.where((n) => n.readAt == null).length;

  static D2InboxState parse(dynamic raw) {
    if (raw is! Map<String, dynamic> ||
        raw['purpose'] != 'd2_in_app_notifications' ||
        raw['in_app_enabled'] != true ||
        raw['browser_push_enabled'] != false ||
        raw['proactive_opt_in'] is! bool ||
        raw['unread_count'] is! int ||
        (raw['csrf_token'] != null &&
            (raw['csrf_token'] is! String ||
                (raw['csrf_token'] as String).isEmpty)) ||
        raw['items'] is! List ||
        (raw['items'] as List).length > 40 ||
        raw['consent'] is! Map<String, dynamic>) {
      throw StateError('Unverified D2 inbox envelope');
    }
    final notice = raw['consent'] as Map<String, dynamic>;
    if (!const {'fr', 'en', 'ar'}.contains(notice['locale']) ||
        notice['notice_version'] != 'd2.inapp.proactivity.2026-11-08.v1' ||
        notice['notice_digest'] is! String ||
        (notice['notice_digest'] as String).length != 64 ||
        notice['notice_text'] is! String ||
        (notice['notice_text'] as String).trim().isEmpty) {
      throw StateError('Unverified D2 consent notice');
    }
    final ids = <int>{};
    final items = <D2NoticeItem>[];
    for (final row in (raw['items'] as List)) {
      final item = D2NoticeItem.parse(row);
      if (!ids.add(item.id)) throw StateError('Duplicate D2 notice identity');
      items.add(item);
    }
    final state = D2InboxState(
      proactivityEnabled: raw['proactive_opt_in'] as bool,
      locale: notice['locale'] as String,
      noticeVersion: notice['notice_version'] as String,
      noticeDigest: notice['notice_digest'] as String,
      noticeText: notice['notice_text'] as String,
      csrfToken: raw['csrf_token'] as String?,
      items: List.unmodifiable(items),
    );
    if (state.unreadCount != raw['unread_count']) {
      throw StateError('D2 unread count mismatch');
    }
    return state;
  }
}

abstract class D2NotificationGateway {
  Future<D2InboxState> inbox(String locale);
  Future<D2InboxState> enable(D2InboxState accepted);
  Future<D2InboxState> disable(String locale);
  Future<D2InboxState> readOne(int id, String locale);
  Future<D2InboxState> readAll(String locale);
  Future<D2InboxState> deleteOne(int id, String locale);
}

class D2ApiNotificationGateway implements D2NotificationGateway {
  final ApiClient api;
  String? _csrfToken;
  D2ApiNotificationGateway(this.api);

  Future<void> _perform(Future<dynamic> Function() call) async {
    final epoch = AuthEpoch.value;
    final response = await call();
    requireCurrentAuthEpoch(epoch);
    if (!response.isSuccessful) {
      throw StateError('D2 account request unavailable');
    }
  }

  @override
  Future<D2InboxState> inbox(String locale) async {
    final epoch = AuthEpoch.value;
    final response = await api.client.get(
      Uri(path: '/api/v1/account/notifications',
          queryParameters: {'locale': locale}),
    );
    requireCurrentAuthEpoch(epoch);
    if (!response.isSuccessful) throw StateError('D2 inbox unavailable');
    final state = D2InboxState.parse(response.body);
    _csrfToken = state.csrfToken;
    return state;
  }

  @override
  Future<D2InboxState> enable(D2InboxState accepted) async {
    await _perform(() => api.client.put(
      Uri.parse('/api/v1/account/notifications/proactivity'),
      headers: _csrfToken == null ? const <String, String>{} : <String, String>{'X-CSRFToken': _csrfToken!},
      body: <String, dynamic>{
        'locale': accepted.locale,
        'notice_version': accepted.noticeVersion,
        'notice_digest': accepted.noticeDigest,
        'acknowledgment': 'ENABLE_D2_IN_APP_PROACTIVITY',
      },
    ));
    return inbox(accepted.locale);
  }

  @override
  Future<D2InboxState> disable(String locale) async {
    await _perform(() => api.client.delete(
      Uri.parse('/api/v1/account/notifications/proactivity'),
      headers: _csrfToken == null ? const <String, String>{} : <String, String>{'X-CSRFToken': _csrfToken!},
    ));
    return inbox(locale);
  }

  @override
  Future<D2InboxState> readOne(int id, String locale) async {
    await _perform(() => api.client.put(
      Uri.parse('/api/v1/account/notifications/$id/read'),
      headers: _csrfToken == null ? const <String, String>{} : <String, String>{'X-CSRFToken': _csrfToken!},
      body: <String, dynamic>{},
    ));
    return inbox(locale);
  }

  @override
  Future<D2InboxState> readAll(String locale) async {
    await _perform(() => api.client.post(
      Uri.parse('/api/v1/account/notifications/read-all'),
      headers: _csrfToken == null ? const <String, String>{} : <String, String>{'X-CSRFToken': _csrfToken!},
      body: <String, dynamic>{},
    ));
    return inbox(locale);
  }

  @override
  Future<D2InboxState> deleteOne(int id, String locale) async {
    await _perform(() => api.client.delete(
      Uri.parse('/api/v1/account/notifications/$id'),
      headers: _csrfToken == null ? const <String, String>{} : <String, String>{'X-CSRFToken': _csrfToken!},
    ));
    return inbox(locale);
  }
}
