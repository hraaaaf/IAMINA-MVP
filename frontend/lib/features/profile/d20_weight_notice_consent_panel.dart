import 'package:flutter/material.dart';

import '../../data/drift/database.dart';
import '../../data/drift/patient_weight_notice_preferences_store.dart';
import 'weight_notice_policy.dart';

/// D20-F: local opt-in controls; no OS permission, scheduling or sending.
class D20WeightNoticeConsentPanel extends StatefulWidget {
  final AppDatabase db;
  const D20WeightNoticeConsentPanel({super.key, required this.db});
  @override
  State<D20WeightNoticeConsentPanel> createState() => _ConsentState();
}

class _ConsentState extends State<D20WeightNoticeConsentPanel> {
  final _kg = TextEditingController();
  final _span = TextEditingController();
  final _age = TextEditingController();
  final _spacing = TextEditingController();
  bool _busy = false, _loading = true, _enabled = false, _agree = false;
  int _epoch = 0;
  String? _message;

  String _t(String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };

  @override
  void initState() { super.initState(); _load(); }

  @override
  void didUpdateWidget(covariant D20WeightNoticeConsentPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(widget.db, oldWidget.db)) {
      ++_epoch;
      _agree = false; _enabled = false; _busy = false; _loading = true;
      _message = null;
      for (final field in [_kg, _span, _age, _spacing]) { field.clear(); }
      _load();
    }
  }

  @override
  void dispose() {
    ++_epoch;
    for (final field in [_kg, _span, _age, _spacing]) { field.dispose(); }
    super.dispose();
  }

  Future<void> _load() async {
    final db = widget.db, epoch = ++_epoch;
    try {
      final prefs = await PatientWeightNoticePreferencesStore(db).read();
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() {
        _enabled = prefs.enabled; _agree = false; _loading = false;
        _kg.text = prefs.enabled
            ? (prefs.minimumChangeKgHundredths! / 100).toStringAsFixed(2) : '';
        _span.text = prefs.enabled ? prefs.minimumSpan!.inDays.toString() : '';
        _age.text = prefs.enabled ? prefs.maximumLatestAge!.inDays.toString() : '';
        _spacing.text = prefs.enabled
            ? prefs.minimumSpacing!.inDays.toString() : '';
      });
    } catch (_) {
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() {
        _loading = false;
        _message = _t('Coffre indisponible. Accord non enregistré.',
            'Vault unavailable. Consent not recorded.',
            'الخزنة غير متاحة. لم تُسجل الموافقة.');
      });
    }
  }

  static int? _hundredths(String input) {
    final s = input.trim().replaceAll(',', '.');
    if (!RegExp(r'^\d{1,4}(?:\.\d{1,2})?$').hasMatch(s)) return null;
    final parts = s.split('.');
    final amount = int.parse(parts.first) * 100 +
        (parts.length > 1 ? int.parse(parts.last.padRight(2, '0')) : 0);
    return amount > 0 && amount <= 999999 ? amount : null;
  }

  static int? _days(String input) {
    final s = input.trim();
    if (!RegExp(r'^[1-9]\d{0,3}$').hasMatch(s)) return null;
    final value = int.parse(s);
    return value <= 3650 ? value : null;
  }

  Future<void> _save() async {
    if (_busy || _loading || !_agree) return;
    final kg = _hundredths(_kg.text), span = _days(_span.text);
    final age = _days(_age.text), spacing = _days(_spacing.text);
    if (kg == null || span == null || age == null || spacing == null) {
      setState(() => _message = _t(
        'Seuil positif en kg et trois durées positives en jours requis.',
        'Positive kg threshold and three positive day periods required.',
        'يلزم حد موجب بالكيلوغرام وثلاث مدد موجبة بالأيام.',
      ));
      return;
    }
    final db = widget.db, epoch = _epoch;
    setState(() { _busy = true; _message = null; });
    try {
      final now = DateTime.now().toUtc();
      await PatientWeightNoticePreferencesStore(db).optIn(
        confirmedByUser: true,
        policy: LocalWeightNoticePolicy(
          enabled: true,
          minimumAbsoluteChangeKgHundredths: kg,
          minimumMeasurementSpan: Duration(days: span),
          maximumLatestReadingAge: Duration(days: age),
          minimumNoticeSpacing: Duration(days: spacing),
        ),
        consentedAtUtc: now, nowUtc: now,
      );
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() {
        _enabled = true; _agree = false;
        _message = _t('Accord enregistré localement. Aucun envoi dans cette version.',
            'Consent saved locally. No messages are sent in this version.',
            'حُفظت الموافقة محليًا. لا تُرسل إشعارات في هذا الإصدار.');
      });
    } catch (_) {
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() => _message = _t('Enregistrement refusé.',
          'Save refused.', 'رُفض الحفظ.'));
    } finally {
      if (mounted && epoch == _epoch && identical(db, widget.db)) {
        setState(() => _busy = false);
      }
    }
  }

  Future<void> _revoke() async {
    if (_busy || _loading || !_enabled) return;
    final db = widget.db, epoch = _epoch;
    setState(() { _busy = true; _message = null; });
    try {
      await PatientWeightNoticePreferencesStore(db).optOut();
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() {
        _enabled = false; _agree = false;
        for (final field in [_kg, _span, _age, _spacing]) { field.clear(); }
        _message = _t('Accord retiré : critères supprimés.',
            'Consent withdrawn: criteria deleted.',
            'سُحبت الموافقة وحُذفت المعايير.');
      });
    } catch (_) {
      if (!mounted || epoch != _epoch || !identical(db, widget.db)) return;
      setState(() => _message = _t('Révocation non confirmée.',
          'Withdrawal not confirmed.', 'لم يتم تأكيد سحب الموافقة.'));
    } finally {
      if (mounted && epoch == _epoch && identical(db, widget.db)) {
        setState(() => _busy = false);
      }
    }
  }

  Widget _field(String key, TextEditingController ctl,
      String fr, String en, String ar, String hint) => TextField(
    key: Key(key), controller: ctl,
    enabled: !_busy && !_loading,
    keyboardType: const TextInputType.numberWithOptions(decimal: true),
    decoration: InputDecoration(labelText: _t(fr, en, ar),
        hintText: hint, border: const OutlineInputBorder()),
  );

  @override
  Widget build(BuildContext context) => Theme(
    // Inter is the IAMINA body font. Explicitly bind form-specific Material
    // label/button typography so audit rendering never falls back to Ahem.
    data: Theme.of(context).copyWith(
      textTheme: Theme.of(context).textTheme.apply(fontFamily: 'Inter'),
      inputDecorationTheme: Theme.of(context).inputDecorationTheme.copyWith(
        labelStyle: const TextStyle(fontFamily: 'Inter'),
        hintStyle: const TextStyle(fontFamily: 'Inter'),
      ),
    ),
    child: Container(
    key: const Key('d20-consent-panel'),
    decoration: BoxDecoration(
      border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
      borderRadius: BorderRadius.circular(14),
    ),
    child: ExpansionTile(
      key: const Key('d20-consent-expand'),
      maintainState: true,
      title: Text(_t('Notifications de poids · facultatives',
          'Weight notifications · optional', 'إشعارات الوزن · اختيارية')),
      subtitle: Text(_enabled
          ? _t('Accord enregistré (envoi indisponible)',
              'Consent saved (sending unavailable)',
              'الموافقة محفوظة (الإرسال غير متاح)')
          : _t('Désactivées par défaut', 'Off by default', 'معطّلة افتراضيًا')),
      childrenPadding: const EdgeInsetsDirectional.fromSTEB(14, 0, 14, 16),
      children: [
        Text(_t(
          'Choisissez vos critères pour une future version. Aucun envoi '
          'actuellement ; l’autorisation système sera demandée séparément.',
          'Choose criteria for a future version. No messages are sent now; '
          'system permission will be requested separately.',
          'اختر معاييرك لإصدار قادم. لا تُرسل إشعارات الآن، '
          'وسيُطلب إذن النظام بشكل منفصل.',
        ), key: const Key('d20-consent-explanation')),
        const SizedBox(height: 12),
        if (_loading)
          const CircularProgressIndicator(key: Key('d20-consent-loading'))
        else ...[
          _field('d20-consent-kg', _kg, 'Variation minimale (kg)',
              'Minimum change (kg)', 'الحد الأدنى للتغيّر (كغ)', '1,50'),
          const SizedBox(height: 10),
          _field('d20-consent-span', _span,
              'Intervalle min. entre pesées (j)',
              'Min. interval between weighings (d)',
              'المدة الدنيا بين القياسات (أيام)', '7'),
          const SizedBox(height: 10),
          _field('d20-consent-age', _age,
              'Âge max. de la pesée (j)',
              'Max. latest reading age (d)',
              'أقصى عمر لآخر قياس (أيام)', '7'),
          const SizedBox(height: 10),
          _field('d20-consent-spacing', _spacing,
              'Délai min. entre notifications (j)',
              'Min. notice spacing (d)',
              'المدة الدنيا بين الإشعارات (أيام)', '4'),
          CheckboxListTile(
            key: const Key('d20-consent-choice'), value: _agree,
            controlAffinity: ListTileControlAffinity.leading,
            onChanged: _busy ? null :
                (v) => setState(() => _agree = v == true),
            title: Text(_t(
              'J’accepte les notifications selon ces critères '
              'lorsqu’elles seront disponibles.',
              'I agree to notifications under these criteria when available.',
              'أوافق على الإشعارات وفق هذه المعايير عندما تصبح متاحة.',
            )),
          ),
          Wrap(alignment: WrapAlignment.end, spacing: 8, children: [
            if (_enabled) OutlinedButton(
              key: const Key('d20-consent-revoke'),
              onPressed: _busy ? null : _revoke,
              child: Text(_t('Retirer mon accord',
                  'Withdraw consent', 'سحب الموافقة'),
                  style: const TextStyle(fontFamily: 'Inter')),
            ),
            FilledButton(
              key: const Key('d20-consent-save'),
              onPressed: _busy || !_agree ? null : _save,
              child: Text(_t('Enregistrer mes critères',
                  'Save my criteria', 'حفظ معاييري'),
                  style: const TextStyle(fontFamily: 'Inter')),
            ),
          ]),
        ],
        if (_message != null) Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Text(_message!, key: const Key('d20-consent-message')),
        ),
      ],
    ),
    ),
  );
}
