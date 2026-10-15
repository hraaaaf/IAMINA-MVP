import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../../data/drift/database.dart';
import '../../data/drift/patient_progressive_demographics_store.dart';
import '../../data/drift/patient_weight_history_store.dart';

/// D18-C: optional local patient declarations. No automatic clinical sync.
class D18ProfilePanel extends StatefulWidget {
  final AppDatabase db;
  const D18ProfilePanel({super.key, required this.db});
  @override
  State<D18ProfilePanel> createState() => _D18ProfilePanelState();
}

class _D18ProfilePanelState extends State<D18ProfilePanel> {
  final _year = TextEditingController();
  final _weight = TextEditingController();
  String? _identity;
  String _unit = 'kg';
  // A timestamp is a patient-declared fact: never manufacture it on open.
  DateTime? _measuredAt;
  List<LocalWeightObservation> _history = const [];
  bool _loading = true;
  bool _busy = false;
  bool _yearDirty = false;
  bool _identityDirty = false;
  String? _notice;
  String? _pendingWeightUuid;
  int _loadEpoch = 0;

  String _t(String fr, String en, String ar) =>
      switch (Localizations.localeOf(context).languageCode) {
        'fr' => fr, 'ar' => ar, _ => en,
      };

  @override
  void initState() { super.initState(); _reload(); }

  @override
  void didUpdateWidget(covariant D18ProfilePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(widget.db, oldWidget.db)) {
      _year.clear(); _weight.clear(); _identity = null; _history = const [];
      _loading = true; _busy = false;
      _yearDirty = false; _identityDirty = false; _notice = null;
      _pendingWeightUuid = null;
      _measuredAt = null;
      _reload();
    }
  }

  @override
  void dispose() { _year.dispose(); _weight.dispose(); super.dispose(); }

  Future<void> _reload() async {
    final db = widget.db;
    final epoch = ++_loadEpoch;
    try {
      final details = await PatientProgressiveDemographicsStore(db).read();
      final history = await PatientWeightHistoryStore(db).recent(limit: 20);
      if (!mounted || epoch != _loadEpoch || !identical(db, widget.db)) return;
      setState(() {
        _year.text = details?.birthYear?.toString() ?? '';
        _identity = details?.genderIdentity;
        _history = history;
        _yearDirty = false; _identityDirty = false;
        _loading = false; _notice = null;
      });
    } catch (_) {
      if (!mounted || epoch != _loadEpoch || !identical(db, widget.db)) return;
      setState(() {
        _loading = false;
        _notice = _t('Coffre patient inaccessible ; aucune donnée modifiée.',
            'Patient vault unavailable; nothing changed.',
            'خزنة المريض غير متاحة؛ لم تتغير البيانات.');
      });
    }
  }

  Future<void> _saveDetails() async {
    if (_busy || _loading || (!_yearDirty && !_identityDirty)) return;
    final raw = _year.text.trim();
    final birthYear = raw.isEmpty ? null : int.tryParse(raw);
    if (_yearDirty && raw.isNotEmpty &&
        (!RegExp(r'^\d{4}$').hasMatch(raw) ||
        birthYear == null || birthYear < 1900 ||
        birthYear > DateTime.now().year)) {
      setState(() => _notice = _t('Année non valide.', 'Invalid birth year.',
          'سنة الميلاد غير صالحة.'));
      return;
    }
    final db = widget.db;
    setState(() { _busy = true; _notice = null; });
    try {
      await PatientProgressiveDemographicsStore(db).update(
        updateBirthYear: _yearDirty,
        birthYear: _yearDirty ? birthYear : null,
        updateGenderIdentity: _identityDirty,
        genderIdentity: _identityDirty ? _identity : null,
      );
      if (!mounted || !identical(db, widget.db)) return;
      setState(() {
        _yearDirty = false; _identityDirty = false;
        _notice = _t('Informations enregistrées localement uniquement.',
            'Details saved locally only.', 'تم حفظ المعلومات محليًا فقط.');
      });
    } catch (_) {
      if (mounted && identical(db, widget.db)) setState(() => _notice = _t(
          'Enregistrement refusé. Vérifiez votre profil patient.',
          'Save refused. Check your patient profile.',
          'تم رفض الحفظ. تحقق من ملف المريض.'));
    } finally {
      if (mounted && identical(db, widget.db)) setState(() => _busy = false);
    }
  }

  Future<void> _selectTime() async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      initialDate: _measuredAt != null && _measuredAt!.isBefore(now)
          ? _measuredAt! : now,
      firstDate: DateTime(1900), lastDate: now,
    );
    if (!mounted || date == null) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_measuredAt ?? now));
    if (!mounted || time == null) return;
    setState(() {
      _measuredAt = DateTime(
          date.year, date.month, date.day, time.hour, time.minute);
      _pendingWeightUuid = null;
    });
  }

  Future<void> _addWeight() async {
    if (_busy || _loading || _weight.text.trim().isEmpty ||
        _measuredAt == null) return;
    final db = widget.db;
    _pendingWeightUuid ??= const Uuid().v4();
    final clientUuid = _pendingWeightUuid!;
    setState(() { _busy = true; _notice = null; });
    try {
      await PatientWeightHistoryStore(db).append(
        clientUuid: clientUuid,
        value: _weight.text.trim().replaceAll(',', '.'),
        unit: _unit, measuredAtUtc: _measuredAt!.toUtc(),
      );
      if (!mounted || !identical(db, widget.db)) return;
      final history = await PatientWeightHistoryStore(db).recent(limit: 20);
      if (!mounted || !identical(db, widget.db)) return;
      setState(() {
        _pendingWeightUuid = null;
        _history = history; _weight.clear(); _measuredAt = null;
        _notice = _t('Pesée ajoutée ; historique conservé.',
            'Reading added; history preserved.', 'تمت إضافة القياس مع حفظ السجل.');
      });
    } catch (_) {
      if (mounted && identical(db, widget.db)) setState(() => _notice = _t(
          'Pesée refusée. Vérifiez la valeur, la date et votre profil.',
          'Reading refused. Check amount, date and profile.',
          'تم رفض القياس. تحقق من القيمة والتاريخ وملف المريض.'));
    } finally {
      if (mounted && identical(db, widget.db)) setState(() => _busy = false);
    }
  }

  String _date(DateTime at) {
    final local = at.toLocal();
    final fmt = MaterialLocalizations.of(context);
    return fmt.formatMediumDate(local) + ' · ' +
        fmt.formatTimeOfDay(TimeOfDay.fromDateTime(local));
  }

  String _weightText(LocalWeightObservation row) =>
      (row.valueHundredths / 100).toStringAsFixed(2) + ' ' + row.unit;

  DropdownMenuItem<String?> _option(String? code, String fr, String en, String ar) =>
      DropdownMenuItem<String?>(value: code, child: Text(_t(fr, en, ar)));

  @override
  Widget build(BuildContext context) {
    return Card(
      key: const Key('d18-profile-section'),
      clipBehavior: Clip.antiAlias,
      child: ExpansionTile(
        key: const Key('d18-expand-profile'),
        leading: const Icon(Icons.monitor_weight_outlined),
        title: Text(_t('Informations personnelles facultatives',
            'Optional personal details', 'معلومات شخصية اختيارية')),
        subtitle: Text(_t('Historique du poids et déclarations personnelles',
            'Weight history and personal declarations',
            'سجل الوزن والتصريحات الشخصية')),
        childrenPadding: const EdgeInsets.fromLTRB(16, 8, 16, 20),
        children: [
          Text(_t(
            'Enregistré uniquement dans ce coffre patient. Ces champs ne modifient pas les traitements, cibles ou alertes.',
            'Saved only in this patient vault. These fields do not alter treatment, targets or safety messages.',
            'تُحفظ في خزنة هذا المريض فقط ولا تغيّر العلاج أو الأهداف أو رسائل السلامة.',
          )),
          const SizedBox(height: 16),
          if (_loading)
            const CircularProgressIndicator(key: Key('d18-loading'))
          else ...[
            TextField(
              key: const Key('d18-birth-year'), controller: _year,
              keyboardType: TextInputType.number,
              enabled: !_busy,
              decoration: InputDecoration(
                labelText: _t('Année de naissance (facultative)',
                    'Birth year (optional)', 'سنة الميلاد (اختياري)'),
                helperText: _t('Sans jour ni mois de naissance',
                    'Without day or month', 'دون يوم أو شهر الميلاد'),
              ),
              onChanged: (_) => setState(() => _yearDirty = true),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: Text(_t('Identité de genre déclarée (facultative)',
                  'Self-declared gender identity (optional)',
                  'الهوية الجندرية المصرح بها (اختياري)')),
            ),
            DropdownButton<String?>(
              key: const Key('d18-gender-identity'), isExpanded: true,
              value: _identity,
              items: [
                _option(null, 'Non renseignée', 'Not provided', 'غير محددة'),
                _option('woman', 'Femme', 'Woman', 'امرأة'),
                _option('man', 'Homme', 'Man', 'رجل'),
                _option('non_binary', 'Non binaire', 'Non-binary', 'غير ثنائي'),
                _option('another_identity', 'Autre identité',
                    'Another identity', 'هوية أخرى'),
                _option('prefer_not_to_say', 'Préfère ne pas répondre',
                    'Prefer not to say', 'أفضل عدم الإجابة'),
              ],
              onChanged: _busy ? null : (code) => setState(() {
                _identity = code; _identityDirty = true;
              }),
            ),
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: FilledButton(
                key: const Key('d18-save-demographics'),
                onPressed: (_yearDirty || _identityDirty) && !_busy
                    ? _saveDetails : null,
                child: Text(_t('Enregistrer', 'Save', 'حفظ')),
              ),
            ),
            const Divider(height: 32),
            Align(alignment: AlignmentDirectional.centerStart,
              child: Text(_t('Historique du poids', 'Weight history',
                  'سجل الوزن'), style: Theme.of(context).textTheme.titleMedium)),
            const SizedBox(height: 8),
            Text(_t(
                'Chaque pesée conserve sa date, son unité et sa provenance. Aucune ancienne valeur n’est remplacée.',
                'Each reading retains its date, unit and provenance. Previous readings are never replaced.',
                'يحتفظ كل قياس بتاريخه ووحدته ومصدره، ولا يُستبدل أي قياس سابق.')),
            const SizedBox(height: 10),
            TextField(
              key: const Key('d18-weight-value'), controller: _weight,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              enabled: !_busy,
              decoration: InputDecoration(
                labelText: _t('Poids mesuré', 'Measured weight', 'الوزن المقاس'),
                hintText: '72,50'),
              onChanged: (_) => setState(() => _pendingWeightUuid = null),
            ),
            DropdownButton<String>(
              key: const Key('d18-weight-unit'), value: _unit,
              items: const [
                DropdownMenuItem(value: 'kg', child: Text('kg')),
                DropdownMenuItem(value: 'lb', child: Text('lb')),
              ],
              onChanged: _busy ? null : (unit) {
                if (unit != null) setState(() {
                  _unit = unit;
                  _pendingWeightUuid = null;
                });
              },
            ),
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                key: const Key('d18-measured-at'),
                onPressed: _busy ? null : _selectTime,
                icon: const Icon(Icons.event_outlined),
                label: Text(_measuredAt == null
                    ? _t('Choisir la date et l’heure de la pesée',
                        'Choose the reading date and time',
                        'اختر تاريخ ووقت قياس الوزن')
                    : _date(_measuredAt!)),
              ),
            ),
            SizedBox(width: double.infinity,
              child: FilledButton(
                key: const Key('d18-save-weight'),
                onPressed: _busy || _loading || _measuredAt == null ||
                        _weight.text.trim().isEmpty
                    ? null : _addWeight,
                child: Text(_t('Ajouter cette pesée',
                    'Add this reading', 'إضافة هذا القياس')),
              )),
            const SizedBox(height: 12),
            if (_history.isEmpty)
              Text(_t('Aucune pesée enregistrée.',
                  'No recorded readings.', 'لا توجد قياسات مسجلة.'))
            else ...[
              Text(_t('20 pesées les plus récentes au maximum',
                  'Up to 20 most recent readings',
                  'آخر 20 قياسًا كحد أقصى'),
                style: Theme.of(context).textTheme.bodySmall),
              for (final row in _history)
                ListTile(
                  key: ValueKey('d18-weight-' + row.clientUuid), dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.history),
                  title: Text(_weightText(row)),
                  subtitle: Text(_date(row.measuredAtUtc)),
                ),
            ],
          ],
          if (_notice != null)
            Padding(padding: const EdgeInsets.only(top: 12),
              child: Text(_notice!, key: const Key('d18-local-status'))),
          if (!_loading)
            Align(alignment: AlignmentDirectional.centerEnd,
              child: TextButton(
                key: const Key('d18-refresh'),
                // Explicit edits must not vanish under a casual refresh.
                onPressed: _busy || _yearDirty || _identityDirty
                    ? null : _reload,
                child: Text(_t('Actualiser', 'Refresh', 'تحديث')),
              )),
        ],
      ),
    );
  }
}
