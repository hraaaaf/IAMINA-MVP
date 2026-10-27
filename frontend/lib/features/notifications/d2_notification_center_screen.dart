/// D2 Web — honest notification center (consent only, no fake inbox).
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../services/api_client.dart';
import '../../services/auth_epoch.dart';
import '../../services/d2_consent_gateway.dart';

String _copy(BuildContext context, String fr, String en, String ar) {
  final locale = Localizations.localeOf(context).languageCode;
  if (locale == 'ar') return ar;
  if (locale == 'en') return en;
  return fr;
}

class D2NotificationCenterScreen extends StatefulWidget {
  final D2ConsentGateway? gateway;
  const D2NotificationCenterScreen({super.key, this.gateway});

  @override
  State<D2NotificationCenterScreen> createState() =>
      _D2NotificationCenterScreenState();
}

class _D2NotificationCenterScreenState
    extends State<D2NotificationCenterScreen> {
  D2ConsentGateway? _gateway;
  D2ConsentStatus? _consent;
  D2ObservationPreview? _preview;
  bool _previewUnavailable = false;
  bool _loading = true;
  bool _saving = false;
  bool _acknowledged = false;
  bool _unavailable = false;
  int _openedEpoch = AuthEpoch.value;
  String _locale = 'fr';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_gateway != null) return;
    _gateway = widget.gateway ?? D2ApiConsentGateway(context.read<ApiClient>());
    _openedEpoch = AuthEpoch.value;
    _locale = Localizations.localeOf(context).toLanguageTag();
    _refresh();
  }

  bool get _sameUser => AuthEpoch.value == _openedEpoch;

  Future<void> _refresh() async {
    if (!_sameUser) return;
    setState(() {
      _loading = true;
      _unavailable = false;
      _acknowledged = false;
      _consent = null;
      _preview = null;
      _previewUnavailable = false;
    });
    try {
      final result = await _gateway!.read(_locale);
      if (!mounted || !_sameUser) return;
      D2ObservationPreview? preview;
      var previewUnavailable = false;
      if (result.optedIn) {
        try {
          preview = await _gateway!.readPreview();
        } catch (_) {
          previewUnavailable = true;
        }
      }
      if (!mounted || !_sameUser) return;
      setState(() {
        _consent = result;
        _preview = preview;
        _previewUnavailable = previewUnavailable;
      });
    } catch (_) {
      if (!mounted || !_sameUser) return;
      setState(() => _unavailable = true);
    } finally {
      if (mounted && _sameUser) setState(() => _loading = false);
    }
  }

  Future<void> _submit({required bool enable}) async {
    if (_saving || !_sameUser || _consent == null) return;
    if (enable && !_acknowledged) return;
    setState(() => _saving = true);
    try {
      final result = enable
          ? await _gateway!.grant(_consent!)
          : await _gateway!.withdraw(_locale);
      if (!mounted || !_sameUser) return;
      D2ObservationPreview? preview;
      var previewUnavailable = false;
      if (result.optedIn) {
        try {
          preview = await _gateway!.readPreview();
        } catch (_) {
          previewUnavailable = true;
        }
      }
      if (!mounted || !_sameUser) return;
      setState(() {
        _consent = result;
        _preview = preview;
        _previewUnavailable = previewUnavailable;
        _acknowledged = false;
        _unavailable = false;
      });
    } catch (_) {
      if (!mounted || !_sameUser) return;
      setState(() {
        _consent = null; // Fail closed: never show a stale approval.
        _preview = null;
        _previewUnavailable = false;
        _unavailable = true;
        _acknowledged = false;
      });
    } finally {
      if (mounted && _sameUser) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final stale = !_sameUser;
    final consent = stale ? null : _consent;
    return Scaffold(
      backgroundColor: const Color(0xFFF4FBF9),
      appBar: AppBar(
        title: Text(_copy(context, 'Notifications IAmina',
            'IAmina notifications', 'إشعارات IAmina')),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 780),
            child: ListView(
              padding: const EdgeInsetsDirectional.fromSTEB(20, 20, 20, 48),
              children: [
                _card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Icon(Icons.notifications_none_outlined,
                          size: 32, color: AminaVisualLanguage.actionGreen),
                      const SizedBox(height: 12),
                      Text(
                        _copy(context, 'Aucune notification reçue',
                            'No notifications received',
                            'لا توجد إشعارات مستلمة'),
                        key: const Key('d2-empty-inbox'),
                        style: const TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(_copy(context,
                          'Les envois de notifications ne sont pas activés. Les rappels que vous créez restent séparés.',
                          'Notification delivery is not enabled. Your saved reminders remain separate.',
                          'إرسال الإشعارات غير مفعّل. تذكيراتك المحفوظة منفصلة عن ذلك.')),
                    ],
                  ),
                ),
                if (consent != null && consent.optedIn) ...[
                  const SizedBox(height: 16),
                  _card(child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(_copy(context, 'Aperçu non urgent',
                          'Non-urgent preview', 'معاينة غير عاجلة'),
                          style: const TextStyle(
                            fontSize: 19, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      if (_previewUnavailable)
                        Text(_copy(context,
                          'Aperçu indisponible pour le moment.',
                          'Preview unavailable for now.',
                          'المعاينة غير متاحة حالياً.'))
                      else if (_preview == null)
                        Text(_copy(context,
                          'Aucune nouvelle observation admissible.',
                          'No new eligible observation.',
                          'لا توجد ملاحظة جديدة مؤهلة.'))
                      else ...[
                        Text(
                          _copy(context,
                            _preview!.kind == 'meal'
                                ? 'Une observation liée aux repas est disponible.'
                                : 'Une observation de contexte est disponible.',
                            _preview!.kind == 'meal'
                                ? 'A meal-related observation is available.'
                                : 'A contextual observation is available.',
                            _preview!.kind == 'meal'
                                ? 'تتوفر ملاحظة متعلقة بالوجبات.'
                                : 'تتوفر ملاحظة سياقية.'),
                          key: const Key('d2-governed-preview'),
                        ),
                        const SizedBox(height: 8),
                        Text(_copy(context,
                          'Information descriptive uniquement : ne diagnostique pas, ne prédit pas et ne recommande aucun changement de traitement.',
                          'Descriptive information only: no diagnosis, prediction or treatment changes.',
                          'معلومات وصفية فقط: دون تشخيص أو تنبؤ أو تغيير للعلاج.')),
                      ],
                    ],
                  )),
                ],
                const SizedBox(height: 16),
                _card(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(_copy(context, 'Préférences pour les futurs aperçus',
                          'Preferences for future previews',
                          'تفضيلات المعاينات المستقبلية'),
                          style: const TextStyle(
                            fontSize: 19, fontWeight: FontWeight.w700,
                          )),
                      const SizedBox(height: 8),
                      Text(_copy(context,
                          'Facultatif, désactivé par défaut. N’active ni les alertes, ni les emails, ni les SMS.',
                          'Optional and off by default. Does not enable alerts, emails or SMS.',
                          'اختياري ومعطّل افتراضياً. لا يفعّل التنبيهات أو البريد أو الرسائل النصية.')),
                      const SizedBox(height: 16),
                      if (stale)
                        Text(_copy(context, 'Session modifiée : reconnectez-vous.',
                            'Session changed: please sign in again.',
                            'تغيّرت الجلسة: يرجى تسجيل الدخول مجدداً.'))
                      else if (_loading)
                        const Center(child: CircularProgressIndicator())
                      else if (_unavailable || consent == null) ...[
                        Text(
                          _copy(context,
                              'Préférence indisponible. Aucun accord ne peut être enregistré actuellement.',
                              'Preference unavailable. No consent can be recorded now.',
                              'التفضيل غير متاح. لا يمكن تسجيل الموافقة الآن.'),
                          key: const Key('d2-error'),
                        ),
                        const SizedBox(height: 10),
                        OutlinedButton(
                          onPressed: _refresh,
                          child: Text(_copy(context, 'Réessayer', 'Retry', 'إعادة المحاولة')),
                        ),
                      ] else ...[
                        Text(
                          consent.noticeText,
                          key: const Key('d2-server-notice'),
                          textDirection: consent.locale == 'ar'
                              ? TextDirection.rtl : TextDirection.ltr,
                        ),
                        const SizedBox(height: 14),
                        if (consent.optedIn) ...[
                          Row(children: [
                            const Icon(Icons.check_circle_outline,
                                color: AminaVisualLanguage.actionGreen),
                            const SizedBox(width: 8),
                            Expanded(child: Text(_copy(context,
                                'Accord pour aperçu uniquement enregistré',
                                'Preview-only consent saved',
                                'تم حفظ الموافقة على المعاينة فقط'))),
                          ]),
                          const SizedBox(height: 14),
                          OutlinedButton(
                            key: const Key('d2-withdraw-consent'),
                            onPressed: _saving ? null
                                : () => _submit(enable: false),
                            child: Text(_copy(context, 'Retirer mon accord',
                                'Withdraw consent', 'سحب الموافقة')),
                          ),
                        ] else ...[
                          CheckboxListTile(
                            key: const Key('d2-acknowledge-notice'),
                            value: _acknowledged,
                            onChanged: _saving
                                ? null : (value) => setState(
                                    () => _acknowledged = value ?? false),
                            contentPadding: EdgeInsets.zero,
                            controlAffinity: ListTileControlAffinity.leading,
                            title: Text(_copy(context,
                                'J’ai lu et compris cet accord facultatif.',
                                'I have read and understood this optional consent.',
                                'قرأت وفهمت هذه الموافقة الاختيارية.')),
                          ),
                          FilledButton(
                            key: const Key('d2-enable-preview-only'),
                            onPressed: _saving || !_acknowledged
                                ? null : () => _submit(enable: true),
                            child: Text(_copy(context, 'Autoriser les aperçus uniquement',
                                'Allow previews only', 'السماح بالمعاينات فقط')),
                          ),
                        ],
                        if (_saving)
                          const Padding(
                            padding: EdgeInsets.only(top: 12),
                            child: Center(child: CircularProgressIndicator()),
                          ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _card({required Widget child}) => Container(
    padding: const EdgeInsets.all(20),
    decoration: AminaVisualLanguage.cardDecoration(context),
    child: child,
  );
}
