import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../services/auth_epoch.dart';
import '../../services/d2_notification_gateway.dart';

String _txt(BuildContext context, String fr, String en, String ar) =>
    switch (Localizations.localeOf(context).languageCode) {
      'ar' => ar,
      'en' => en,
      _ => fr,
    };

String _noticeText(BuildContext context, D2NoticeItem item) {
  return switch (item.code) {
    'ai_consent_given' => _txt(
        context, 'Consentement IA confirmé',
        'AI consent confirmed', 'تم تأكيد الموافقة على الذكاء الاصطناعي',
      ),
    'ai_consent_withdrawn' => _txt(
        context, 'Consentement IA retiré',
        'AI consent withdrawn', 'تم سحب الموافقة على الذكاء الاصطناعي',
      ),
    'language_pref_available' => _txt(
        context, 'Vous pouvez personnaliser la langue de l’application',
        'You can customize your app language',
        'يمكنك تخصيص لغة التطبيق',
      ),
    _ => _txt(context, 'Information non disponible', 'Update unavailable',
        'المعلومة غير متوفرة'),
  };
}

/// In-app UI only. All data comes from a validated authenticated D2 gateway.
/// No clinical recommendations, reminders, push, or client-generated notices.
class D2LiveNotificationsScreen extends StatefulWidget {
  final D2NotificationGateway gateway;
  const D2LiveNotificationsScreen({super.key, required this.gateway});

  @override
  State<D2LiveNotificationsScreen> createState() =>
      _D2LiveNotificationsScreenState();
}

class _D2LiveNotificationsScreenState extends State<D2LiveNotificationsScreen> {
  int _epoch = AuthEpoch.value;
  D2InboxState? _state;
  String? _locale;
  bool _busy = false;
  bool _unavailable = false;

  bool get _sameEpoch => AuthEpoch.value == _epoch;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final locale = switch (Localizations.localeOf(context).languageCode) {
      'ar' => 'ar',
      'en' => 'en',
      _ => 'fr',
    };
    if (_locale == locale) return;
    _locale = locale;
    _epoch = AuthEpoch.value;
    _load();
  }

  Future<void> _load() async {
    if (!_sameEpoch || _locale == null) return;
    setState(() {
      _busy = true;
      _state = null;
      _unavailable = false;
    });
    try {
      final state = await widget.gateway.inbox(_locale!);
      if (!mounted || !_sameEpoch) return;
      setState(() => _state = state);
    } catch (_) {
      if (!mounted || !_sameEpoch) return;
      setState(() {
        _unavailable = true;
        _state = null;
      });
    } finally {
      if (mounted && _sameEpoch) setState(() => _busy = false);
    }
  }

  Future<void> _run(Future<D2InboxState> Function() action) async {
    if (_busy || !_sameEpoch) return;
    setState(() => _busy = true);
    try {
      final state = await action();
      if (!mounted || !_sameEpoch) return;
      setState(() {
        _state = state;
        _unavailable = false;
      });
    } catch (_) {
      if (!mounted || !_sameEpoch) return;
      setState(() {
        _state = null; // fail closed on stale/failed consent or ownership
        _unavailable = true;
      });
    } finally {
      if (mounted && _sameEpoch) setState(() => _busy = false);
    }
  }

  Future<void> _confirmOptIn(D2InboxState data) async {
    if (_busy || !_sameEpoch || data.proactivityEnabled) return;
    final approved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(_txt(ctx, 'Notifications proactives',
            'Proactive notifications', 'الإشعارات الاستباقية')),
        content: Text(data.noticeText),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(_txt(ctx, 'Annuler', 'Cancel', 'إلغاء')),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(_txt(ctx, 'Activer', 'Enable', 'تفعيل')),
          ),
        ],
      ),
    );
    if (approved == true && mounted && _sameEpoch) {
      await _run(() => widget.gateway.enable(data));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = _sameEpoch ? _state : null;
    final unavailable = !_sameEpoch || _unavailable;
    return Scaffold(
      key: const ValueKey('d2-live-notifications-screen'),
      backgroundColor: AminaTheme.bg(context),
      body: Column(
        children: [
          AminaMobilePageHeader(
            leading: const AminaPageExitButton(fallbackRoute: '/dashboard'),
            title: _txt(context, 'Notifications', 'Notifications', 'الإشعارات'),
            subtitle: _txt(context, 'Informations de votre application',
                'Updates from your app', 'مستجدات التطبيق'),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsetsDirectional.fromSTEB(16, 20, 16, 50),
              children: [
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 760),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (_busy && state == null)
                          const Center(child: CircularProgressIndicator())
                        else if (unavailable || state == null)
                          Card(
                            key: const ValueKey('d2-live-unavailable'),
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                children: [
                                  Text(_txt(context,
                                      'Notifications non disponibles pour le moment.',
                                      'Notifications are not available right now.',
                                      'الإشعارات غير متاحة حالياً.')),
                                  const SizedBox(height: 12),
                                  OutlinedButton(
                                    onPressed: _sameEpoch ? _load : null,
                                    child: Text(_txt(context, 'Réessayer',
                                        'Retry', 'إعادة المحاولة')),
                                  ),
                                ],
                              ),
                            ),
                          )
                        else ...[
                          Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  SwitchListTile.adaptive(
                                    key: const ValueKey('d2-proactivity-toggle'),
                                    contentPadding: EdgeInsets.zero,
                                    title: Text(_txt(context,
                                        'Informations proactives',
                                        'Proactive updates',
                                        'المعلومات الاستباقية')),
                                    subtitle: Text(_txt(context,
                                        'Facultatives, non médicales et limitées.',
                                        'Optional, non-medical, and limited.',
                                        'اختيارية وغير طبية ومحدودة.')),
                                    value: state.proactivityEnabled,
                                    onChanged: _busy ? null : (value) {
                                      if (value) {
                                        _confirmOptIn(state);
                                      } else {
                                        _run(() => widget.gateway.disable(_locale!));
                                      }
                                    },
                                  ),
                                  Text(_txt(context,
                                      'Les rappels restent séparés sur l’accueil.',
                                      'Reminders remain separate on Home.',
                                      'تبقى التذكيرات منفصلة في الرئيسية.'),
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: AminaVisualLanguage.secondary(context),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  _txt(context, 'Mes notifications',
                                      'My notifications', 'إشعاراتي'),
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                              ),
                              if (state.unreadCount > 0)
                                TextButton(
                                  key: const ValueKey('d2-read-all'),
                                  onPressed: _busy ? null : () =>
                                      _run(() => widget.gateway.readAll(_locale!)),
                                  child: Text(_txt(context, 'Tout marquer comme lu',
                                      'Mark all read', 'تحديد الكل كمقروء')),
                                ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          if (state.items.isEmpty)
                            Card(
                              key: const ValueKey('d2-live-empty'),
                              child: Padding(
                                padding: const EdgeInsets.all(28),
                                child: Text(_txt(context,
                                    'Aucune notification pour le moment.',
                                    'No notifications right now.',
                                    'لا توجد إشعارات حالياً.'),
                                  textAlign: TextAlign.center),
                              ),
                            ),
                          for (final item in state.items)
                            Card(
                              key: ValueKey('d2-notice-${item.id}'),
                              child: ListTile(
                                leading: Icon(
                                  item.kind == 'proactive'
                                      ? Icons.tips_and_updates_outlined
                                      : Icons.verified_user_outlined,
                                  color: AminaVisualLanguage.actionGreen,
                                ),
                                title: Text(_noticeText(context, item),
                                    style: TextStyle(
                                      fontWeight: item.readAt == null
                                          ? FontWeight.w700 : FontWeight.w400,
                                    )),
                                subtitle: Text(item.kind == 'proactive'
                                    ? _txt(context, 'Proactive', 'Proactive',
                                        'استباقي')
                                    : _txt(context, 'Compte', 'Account', 'الحساب')),
                                trailing: Wrap(
                                  spacing: 0,
                                  children: [
                                    if (item.readAt == null)
                                      IconButton(
                                        tooltip: _txt(context, 'Marquer comme lu',
                                            'Mark read', 'تحديد كمقروء'),
                                        onPressed: _busy ? null : () =>
                                            _run(() => widget.gateway.readOne(
                                                item.id, _locale!)),
                                        icon: const Icon(Icons.done_rounded),
                                      ),
                                    IconButton(
                                      tooltip: _txt(context, 'Supprimer', 'Delete',
                                          'حذف'),
                                      onPressed: _busy ? null : () =>
                                          _run(() => widget.gateway.deleteOne(
                                              item.id, _locale!)),
                                      icon: const Icon(Icons.close_rounded),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
