import 'package:flutter/material.dart';

import '../../services/synthetic_doctor_export_gate.dart';
import '../../services/synthetic_doctor_report.dart';

/// CAL-12 Web test harness only; never routed from the production application.
/// No patient database, network client, storage, email or OS share operation.
class SyntheticDoctorExportWebFlow extends StatefulWidget {
  const SyntheticDoctorExportWebFlow({super.key, required this.languageCode});
  final String languageCode;

  @override
  State<SyntheticDoctorExportWebFlow> createState() => _SyntheticFlowState();
}

enum _Step { preview, consent, recipient, simulated }

class _SyntheticFlowState extends State<SyntheticDoctorExportWebFlow> {
  SyntheticVaultFixture _owner = SyntheticVaultFixture.alpha;
  _Step _step = _Step.preview;
  bool _consented = false;
  bool _destinationConfirmed = false;
  SyntheticRecipientFixture? _destination;
  String? _inMemoryPreview;

  String _t(String fr, String en, String ar) =>
      widget.languageCode == 'ar' ? ar : widget.languageCode == 'en' ? en : fr;

  int get _reading => _owner == SyntheticVaultFixture.alpha ? 142 : 119;

  void _reset([SyntheticVaultFixture? owner]) {
    setState(() {
      _owner = owner ?? _owner;
      _step = _Step.preview;
      _consented = false;
      _destinationConfirmed = false;
      _destination = null;
      _inMemoryPreview = null;
    });
  }

  SyntheticDoctorReport _report() => SyntheticDoctorReport(
    generatedAtUtc: DateTime.utc(2026, 11, 9, 18),
    periodStartUtc: DateTime.utc(2026, 11, 1),
    periodEndUtc: DateTime.utc(2026, 11, 8),
    observations: [
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 2, 8), mgDl: _reading,
      ),
      SyntheticGlucoseObservation(
        recordedAtUtc: DateTime.utc(2026, 11, 3, 10), mgDl: null,
      ),
    ],
  );

  void _simulate() {
    final doctor = _destination;
    if (!_consented || !_destinationConfirmed || doctor == null) return;
    final preview = SyntheticDoctorExportGate.previewHtml(
      languageCode: widget.languageCode,
      intent: SyntheticDoctorPreviewIntent(
        report: _report(),
        reportOwner: _owner,
        activeOwner: _owner,
        recipient: doctor,
        confirmedRecipient: doctor,
        recipientConfirmedAtUtc: DateTime.utc(2026, 11, 10, 9),
        requestedAtUtc: DateTime.utc(2026, 11, 10, 10),
        consent: SyntheticExportConsentFixture(
          owner: _owner,
          recipient: doctor,
          purpose: SyntheticExportPurpose.doctorFollowUp,
          grantedAtUtc: DateTime.utc(2026, 11, 9, 21),
          expiresAtUtc: DateTime.utc(2026, 11, 10, 11),
          explicitlyConfirmed: _consented,
        ),
      ),
    );
    if (!preview.contains('$_reading mg/dL')) {
      throw StateError('CAL-12 synthetic owner mismatch');
    }
    // Preview stays in memory, is never opened or transferred to a real user.
    setState(() {
      _inMemoryPreview = preview;
      _step = _Step.simulated;
    });
  }

  Widget _card(List<Widget> children) => Card(
    // Prevent a single aria-label from swallowing title, reading and CTA.
    // Expose each meaningful child as an individual accessibility node.
    semanticContainer: false,
    color: Colors.white,
    elevation: 0,
    shape: RoundedRectangleBorder(
      side: const BorderSide(color: Color(0xFFDCE9E5)),
      borderRadius: BorderRadius.circular(20),
    ),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      ),
    ),
  );

  Widget _stepContent() {
    const heading = TextStyle(fontSize: 22, fontWeight: FontWeight.w700);
    switch (_step) {
      case _Step.preview:
        return _card([
          Text(_t('Aperçu fictif', 'Fictional preview', 'معاينة تجريبية'),
            key: const ValueKey('cal12-step-preview'), style: heading),
          const SizedBox(height: 18),
          Text('$_reading mg/dL', key: const ValueKey('cal12-reading'),
            textDirection: TextDirection.ltr, textAlign: TextAlign.start,
            style: const TextStyle(
              fontSize: 32, fontWeight: FontWeight.bold, color: Color(0xFF176655))),
          const SizedBox(height: 8),
          Text(_t('Mesures inventées, aucune donnée personnelle.',
                  'Invented measurements; no personal data.',
                  'قياسات افتراضية دون أي بيانات شخصية.')),
          const SizedBox(height: 18),
          FilledButton(
            key: const ValueKey('cal12-preview-next'),
            onPressed: () => setState(() => _step = _Step.consent),
            child: Text(_t('Continuer', 'Continue', 'متابعة')),
          ),
        ]);
      case _Step.consent:
        return _card([
          Text(_t('Consentement fictif', 'Fictional consent', 'موافقة تجريبية'),
            key: const ValueKey('cal12-step-consent'), style: heading),
          const SizedBox(height: 10),
          Text(_t('Aucun document ne sera enregistré ou transmis.',
                  'No document will be saved or transmitted.',
                  'لن يتم حفظ أي مستند أو إرساله.')),
          CheckboxListTile(
            key: const ValueKey('cal12-consent-checkbox'),
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _consented,
            onChanged: (v) => setState(() => _consented = v == true),
            title: Text(_t('J’accepte cette simulation uniquement',
                'I agree to this simulation only', 'أوافق على هذه المحاكاة فقط')),
          ),
          FilledButton(
            key: const ValueKey('cal12-consent-next'),
            onPressed: !_consented ? null :
                () => setState(() => _step = _Step.recipient),
            child: Text(_t('Valider le consentement',
                'Confirm consent', 'تأكيد الموافقة')),
          ),
          TextButton(
            key: const ValueKey('cal12-cancel'),
            onPressed: _reset,
            child: Text(_t('Annuler', 'Cancel', 'إلغاء')),
          ),
        ]);
      case _Step.recipient:
        return _card([
          Text(_t('Destinataire fictif', 'Fictional recipient', 'مستلم تجريبي'),
            key: const ValueKey('cal12-step-recipient'), style: heading),
          for (final doctor in SyntheticRecipientFixture.values)
            ListTile(
              key: ValueKey('cal12-recipient-' + doctor.name),
              title: Text(doctor == SyntheticRecipientFixture.doctorOne
                ? _t('Médecin fictif 1', 'Fictional doctor 1', 'طبيب تجريبي ١')
                : _t('Médecin fictif 2', 'Fictional doctor 2', 'طبيب تجريبي ٢')),
              leading: Icon(_destination == doctor
                ? Icons.radio_button_checked : Icons.radio_button_unchecked),
              selected: _destination == doctor,
              onTap: () => setState(() {
                _destination = doctor;
                _destinationConfirmed = false;
              }),
            ),
          CheckboxListTile(
            key: const ValueKey('cal12-recipient-confirm'),
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: EdgeInsets.zero,
            value: _destinationConfirmed,
            onChanged: _destination == null ? null :
                (v) => setState(() => _destinationConfirmed = v == true),
            title: Text(_t('Je confirme le destinataire sélectionné',
                'I confirm the selected recipient', 'أؤكد المستلم المحدد')),
          ),
          FilledButton(
            key: const ValueKey('cal12-simulate'),
            onPressed: _destinationConfirmed && _destination != null
                ? _simulate : null,
            child: Text(_t('Simuler le partage',
                'Simulate sharing', 'محاكاة المشاركة')),
          ),
          TextButton(
            key: const ValueKey('cal12-revoke'),
            onPressed: _reset,
            child: Text(_t('Retirer mon accord', 'Withdraw consent', 'سحب الموافقة')),
          ),
        ]);
      case _Step.simulated:
        return _card([
          Text(_t('Simulation terminée', 'Simulation complete',
                  'اكتملت المحاكاة'),
            key: const ValueKey('cal12-step-done'), style: heading),
          const SizedBox(height: 10),
          Text(_t('Aucun document ni message n’a été envoyé.',
                  'No document or message was sent.',
                  'لم يتم إرسال أي مستند أو رسالة.')),
          const SizedBox(height: 14),
          Text('$_reading mg/dL',
            key: const ValueKey('cal12-confirmed-reading'),
            textDirection: TextDirection.ltr,
            style: const TextStyle(fontSize: 23, fontWeight: FontWeight.bold)),
          if (_inMemoryPreview != null)
            Text(_t('Prévisualisation validée en mémoire.',
                'Preview verified in memory.', 'تم التحقق من المعاينة في الذاكرة.')),
          const SizedBox(height: 20),
          OutlinedButton(
            key: const ValueKey('cal12-revoke'),
            onPressed: _reset,
            child: Text(_t('Retirer mon accord', 'Withdraw consent', 'سحب الموافقة')),
          ),
        ]);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: widget.languageCode == 'ar'
          ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        key: const ValueKey('cal12-isolated-flow'),
        backgroundColor: const Color(0xFFF3F8F6),
        body: SafeArea(
          child: LayoutBuilder(
            builder: (context, size) => SingleChildScrollView(
              child: Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: size.maxWidth < 600 ? 14 : 28, vertical: 20),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 780),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(_t('CAL-12 · Démonstration fictive',
                                'CAL-12 · Fictional demo', 'CAL-12 · عرض تجريبي'),
                            style: const TextStyle(
                              fontSize: 25, color: Color(0xFF103B34),
                              fontWeight: FontWeight.bold)),
                        const SizedBox(height: 10),
                        Text(_t('Aucun patient, fichier, e-mail ou partage réel.',
                                'No patient, file, email or real sharing.',
                                'لا يوجد مريض أو ملف أو بريد أو مشاركة حقيقية.')),
                        const SizedBox(height: 18),
                        Wrap(spacing: 10, runSpacing: 8, children: [
                          for (final owner in SyntheticVaultFixture.values)
                            ChoiceChip(
                              key: ValueKey('cal12-owner-' + owner.name),
                              selected: _owner == owner,
                              label: Text(owner == SyntheticVaultFixture.alpha
                                ? _t('Profil fictif A', 'Fictional profile A',
                                    'ملف تجريبي أ')
                                : _t('Profil fictif B', 'Fictional profile B',
                                    'ملف تجريبي ب')),
                              onSelected: (_) => _reset(owner),
                            ),
                        ]),
                        const SizedBox(height: 18),
                        _stepContent(),
                        const SizedBox(height: 14),
                        Text(_t(
                          'Données SYNTHÉTIQUES uniquement · export patient désactivé',
                          'SYNTHETIC data only · patient export disabled',
                          'بيانات تجريبية فقط · تصدير المريض معطل',
                        ), style: const TextStyle(
                            color: Color(0xFF61746E), fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
