import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/clinical_card.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../services/cgm_service.dart';
import 'cgm_connections_section.dart';

class CgmScreen extends StatefulWidget {
  final CgmService? service;

  const CgmScreen({super.key, this.service});

  @override
  State<CgmScreen> createState() => _CgmScreenState();
}

class _CgmScreenState extends State<CgmScreen> {
  String? _sourceId;
  bool? _hasNightscout;

  int get _step => _sourceId == null ? 1 : _hasNightscout == null ? 2 : 3;

  void _reset() => setState(() {
        _sourceId = null;
        _hasNightscout = null;
      });

  @override
  Widget build(BuildContext context) {
    final copy = _CgmGuideCopy.of(context);

    return Scaffold(
      backgroundColor: AminaTheme.paper,
      body: SafeArea(
        child: Column(
          children: [
            _CgmHeader(copy: copy),
            Expanded(
              child: ResponsiveContentSurface(
                maxWidth: 760,
                child: SingleChildScrollView(
                  padding: const EdgeInsetsDirectional.fromSTEB(16, 16, 16, 28),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _WizardProgress(copy: copy, step: _step),
                      const SizedBox(height: 16),
                      if (_sourceId == null)
                        _SensorStep(
                          copy: copy,
                          onSelect: (value) => setState(() => _sourceId = value),
                        )
                      else if (_hasNightscout == null)
                        _NightscoutStep(
                          copy: copy,
                          sourceId: _sourceId!,
                          onBack: () => setState(() => _sourceId = null),
                          onAnswer: (value) =>
                              setState(() => _hasNightscout = value),
                        )
                      else
                        _ConnectStep(
                          copy: copy,
                          sourceId: _sourceId!,
                          hasNightscout: _hasNightscout!,
                          service: widget.service,
                          onBack: () => setState(() => _hasNightscout = null),
                          onNightscoutReady: () =>
                              setState(() => _hasNightscout = true),
                          onReset: _reset,
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WizardProgress extends StatelessWidget {
  final _CgmGuideCopy copy;
  final int step;

  const _WizardProgress({required this.copy, required this.step});

  @override
  Widget build(BuildContext context) {
    final labels = [copy.stepSensor, copy.stepNightscout, copy.stepIamina];
    return Row(
      children: [
        for (var i = 0; i < labels.length; i++) ...[
          if (i > 0)
            Expanded(
              child: Container(
                height: 2,
                color: i < step ? AminaTheme.teal500 : AminaTheme.ink200,
              ),
            ),
          Semantics(
            label: copy.stepProgress(i + 1, labels[i]),
            child: Container(
              constraints: const BoxConstraints(minHeight: 36),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: i + 1 <= step ? AminaTheme.teal50 : AminaTheme.ink50,
                borderRadius: BorderRadius.circular(99),
                border: Border.all(
                  color: i + 1 <= step ? AminaTheme.teal100 : AminaTheme.ink200,
                ),
              ),
              child: Text(
                labels[i],
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  color: i + 1 <= step ? AminaTheme.teal700 : AminaTheme.ink500,
                ),
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _SensorStep extends StatelessWidget {
  final _CgmGuideCopy copy;
  final ValueChanged<String> onSelect;

  const _SensorStep({required this.copy, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    final options = [
      ('dexcom', 'Dexcom G6/G7', Icons.bluetooth_rounded),
      ('libre', 'FreeStyle Libre', Icons.sensors_rounded),
      ('linx', 'LinX / AiDEX X', Icons.monitor_heart_outlined),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          copy.sensorQuestion,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: AminaTheme.ink900,
          ),
        ),
        const SizedBox(height: 5),
        Text(
          copy.sensorQuestionBody,
          style: const TextStyle(fontSize: 12, height: 1.45, color: AminaTheme.ink600),
        ),
        const SizedBox(height: 16),
        for (final option in options) ...[
          Semantics(
            button: true,
            label: option.$2,
            child: ClinicalCard(
              padding: EdgeInsets.zero,
              child: InkWell(
                key: ValueKey('cgm-wizard-source-${option.$1}'),
                onTap: () => onSelect(option.$1),
                borderRadius: BorderRadius.circular(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: AminaTheme.teal50,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(option.$3, color: AminaTheme.teal700, size: 21),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          option.$2,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: AminaTheme.ink900,
                          ),
                        ),
                      ),
                      const Icon(Icons.arrow_forward_rounded, color: AminaTheme.teal700),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
        ],
        const SizedBox(height: 6),
        _JourneyCard(copy: copy),
      ],
    );
  }
}

class _NightscoutStep extends StatelessWidget {
  final _CgmGuideCopy copy;
  final String sourceId;
  final VoidCallback onBack;
  final ValueChanged<bool> onAnswer;

  const _NightscoutStep({
    required this.copy,
    required this.sourceId,
    required this.onBack,
    required this.onAnswer,
  });

  @override
  Widget build(BuildContext context) {
    final title = switch (sourceId) {
      'dexcom' => 'Dexcom G6/G7',
      'libre' => 'FreeStyle Libre',
      _ => 'LinX / AiDEX X',
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _BackStepButton(copy: copy, onPressed: onBack),
        const SizedBox(height: 8),
        Text(
          copy.nightscoutQuestion(title),
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: AminaTheme.ink900,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          copy.nightscoutQuestionBody,
          style: const TextStyle(fontSize: 12, height: 1.45, color: AminaTheme.ink600),
        ),
        const SizedBox(height: 16),
        _ChoiceButton(
          key: const ValueKey('cgm-wizard-nightscout-yes'),
          icon: Icons.check_circle_outline_rounded,
          label: copy.yesNightscout,
          onPressed: () => onAnswer(true),
        ),
        const SizedBox(height: 10),
        _ChoiceButton(
          key: const ValueKey('cgm-wizard-nightscout-no'),
          icon: Icons.help_outline_rounded,
          label: copy.noNightscoutYet,
          onPressed: () => onAnswer(false),
        ),
      ],
    );
  }
}

class _ConnectStep extends StatelessWidget {
  final _CgmGuideCopy copy;
  final String sourceId;
  final bool hasNightscout;
  final CgmService? service;
  final VoidCallback onBack;
  final VoidCallback onNightscoutReady;
  final VoidCallback onReset;

  const _ConnectStep({
    required this.copy,
    required this.sourceId,
    required this.hasNightscout,
    required this.service,
    required this.onBack,
    required this.onNightscoutReady,
    required this.onReset,
  });

  @override
  Widget build(BuildContext context) {
    final guide = _guideFor(copy, sourceId);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _BackStepButton(copy: copy, onPressed: onBack),
        const SizedBox(height: 8),
        if (!hasNightscout) ...[
          Text(
            copy.prepareNightscoutTitle,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AminaTheme.ink900,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            copy.prepareNightscoutBody,
            style: const TextStyle(fontSize: 12, height: 1.45, color: AminaTheme.ink600),
          ),
          const SizedBox(height: 14),
          _SourceGuideCard(
            key: ValueKey('cgm-wizard-guide-$sourceId'),
            icon: guide.$1,
            title: guide.$2,
            path: guide.$3,
            steps: guide.$4,
            initiallyExpanded: true,
          ),
          const SizedBox(height: 14),
          _NightscoutHelpCard(copy: copy),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              key: const ValueKey('cgm-wizard-nightscout-ready'),
              onPressed: onNightscoutReady,
              icon: const Icon(Icons.check_rounded),
              label: Text(copy.nightscoutReady),
            ),
          ),
        ] else ...[
          Text(
            copy.connectTitle,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AminaTheme.ink900,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            copy.connectIntro,
            style: const TextStyle(fontSize: 12, height: 1.45, color: AminaTheme.ink600),
          ),
          const SizedBox(height: 12),
          CgmConnectionsSection(service: service, sourceFilter: sourceId),
          const SizedBox(height: 14),
          _TroubleshootingCard(copy: copy),
          const SizedBox(height: 14),
          TextButton.icon(
            onPressed: onReset,
            icon: const Icon(Icons.restart_alt_rounded),
            label: Text(copy.changeSensor),
          ),
        ],
      ],
    );
  }

  (IconData, String, String, List<String>) _guideFor(
    _CgmGuideCopy copy,
    String sourceId,
  ) {
    return switch (sourceId) {
      'dexcom' => (
          Icons.bluetooth_rounded,
          'Dexcom G6/G7',
          copy.dexcomPath,
          copy.dexcomSteps,
        ),
      'libre' => (
          Icons.sensors_rounded,
          'FreeStyle Libre',
          copy.librePath,
          copy.libreSteps,
        ),
      _ => (
          Icons.monitor_heart_outlined,
          'LinX / AiDEX X',
          copy.linxPath,
          copy.linxSteps,
        ),
    };
  }
}

class _ChoiceButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const _ChoiceButton({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon),
        label: Padding(
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Text(label),
        ),
      ),
    );
  }
}

class _BackStepButton extends StatelessWidget {
  final _CgmGuideCopy copy;
  final VoidCallback onPressed;

  const _BackStepButton({required this.copy, required this.onPressed});

  @override
  Widget build(BuildContext context) => TextButton.icon(
        onPressed: onPressed,
        icon: const Icon(Icons.arrow_back_rounded, size: 17),
        label: Text(copy.previousStep),
      );
}

class _CgmHeader extends StatelessWidget {
  final _CgmGuideCopy copy;

  const _CgmHeader({required this.copy});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsetsDirectional.fromSTEB(8, 10, 16, 12),
      decoration: const BoxDecoration(
        color: AminaTheme.cardBg,
        border: Border(bottom: BorderSide(color: AminaTheme.ink100)),
      ),
      child: Row(
        children: [
          const AminaPageExitButton(),
          const SizedBox(width: 2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  copy.title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.ink900,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  copy.subtitle,
                  style: const TextStyle(fontSize: 11.5, color: AminaTheme.ink500),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _JourneyCard extends StatelessWidget {
  final _CgmGuideCopy copy;

  const _JourneyCard({required this.copy});

  @override
  Widget build(BuildContext context) {
    return ClinicalCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AminaTheme.teal50,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: const Icon(Icons.route_rounded, color: AminaTheme.teal700, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  copy.journeyTitle,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.ink900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            decoration: BoxDecoration(
              color: AminaTheme.teal50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              copy.journeyPath,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: AminaTheme.teal800,
              ),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            copy.credentialSafety,
            style: const TextStyle(fontSize: 11.5, height: 1.4, color: AminaTheme.ink600),
          ),
        ],
      ),
    );
  }
}

class _SourceGuideCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String path;
  final List<String> steps;

  final bool initiallyExpanded;

  const _SourceGuideCard({
    super.key,
    required this.icon,
    required this.title,
    required this.path,
    required this.steps,
    this.initiallyExpanded = false,
  });

  @override
  Widget build(BuildContext context) {
    return ClinicalCard(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        initiallyExpanded: initiallyExpanded,
        tilePadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        childrenPadding: const EdgeInsetsDirectional.fromSTEB(14, 0, 14, 14),
        leading: Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: AminaTheme.teal50,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, size: 18, color: AminaTheme.teal700),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: AminaTheme.ink900,
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 3),
          child: Text(
            path,
            style: const TextStyle(fontSize: 10.5, height: 1.35, color: AminaTheme.ink500),
          ),
        ),
        children: [
          for (var index = 0; index < steps.length; index++) ...[
            if (index > 0) const SizedBox(height: 8),
            _GuideStep(index: index + 1, body: steps[index]),
          ],
        ],
      ),
    );
  }
}

class _GuideStep extends StatelessWidget {
  final int index;
  final String body;

  const _GuideStep({required this.index, required this.body});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 24,
          height: 24,
          alignment: Alignment.center,
          decoration: const BoxDecoration(color: AminaTheme.teal600, shape: BoxShape.circle),
          child: Text(
            '$index',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        const SizedBox(width: 9),
        Expanded(
          child: Text(
            body,
            style: const TextStyle(fontSize: 11.5, height: 1.45, color: AminaTheme.ink700),
          ),
        ),
      ],
    );
  }
}

class _NightscoutHelpCard extends StatelessWidget {
  final _CgmGuideCopy copy;

  const _NightscoutHelpCard({required this.copy});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AminaTheme.ink50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AminaTheme.ink200),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.help_outline_rounded, size: 21, color: AminaTheme.ink600),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  copy.noNightscoutTitle,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.ink900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  copy.noNightscoutBody,
                  style: const TextStyle(fontSize: 11.5, height: 1.45, color: AminaTheme.ink600),
                ),
                const SizedBox(height: 7),
                SelectableText(
                  'nightscout.github.io',
                  style: const TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.teal700,
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

class _TroubleshootingCard extends StatelessWidget {
  final _CgmGuideCopy copy;

  const _TroubleshootingCard({required this.copy});

  @override
  Widget build(BuildContext context) {
    return ClinicalCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            copy.troubleTitle,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: AminaTheme.ink900,
            ),
          ),
          const SizedBox(height: 8),
          for (final item in copy.troubleSteps) ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.only(top: 2),
                  child: Icon(Icons.check_circle_outline_rounded, size: 16, color: AminaTheme.teal600),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    item,
                    style: const TextStyle(fontSize: 11.5, height: 1.4, color: AminaTheme.ink600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
          ],
        ],
      ),
    );
  }
}

class _CgmGuideCopy {
  final String code;

  const _CgmGuideCopy(this.code);

  factory _CgmGuideCopy.of(BuildContext context) =>
      _CgmGuideCopy(Localizations.localeOf(context).languageCode);

  String _pick({required String fr, required String en, required String ar}) =>
      code == 'ar' ? ar : code == 'en' ? en : fr;

  String get title => _pick(
        fr: 'Connecter mon CGM',
        en: 'Connect my CGM',
        ar: 'ربط جهاز CGM',
      );

  String get subtitle => _pick(
        fr: 'Un parcours guidé, sans jargon inutile.',
        en: 'A guided path without unnecessary jargon.',
        ar: 'مسار إرشادي واضح بدون مصطلحات معقدة.',
      );

  String get journeyTitle => _pick(
        fr: 'Comment circulent vos mesures',
        en: 'How your readings reach IAMINA',
        ar: 'كيف تصل قراءاتك إلى IAMINA',
      );

  String get journeyPath => _pick(
        fr: 'Capteur → app/service source → Nightscout → IAMINA',
        en: 'Sensor → source app/service → Nightscout → IAMINA',
        ar: 'المستشعر ← تطبيق/خدمة المصدر ← Nightscout ← IAMINA',
      );

  String get credentialSafety => _pick(
        fr: 'IAMINA ne demande jamais votre mot de passe Dexcom, Abbott ou MicroTech. Elle lit uniquement votre relais Nightscout sécurisé.',
        en: 'IAMINA never asks for your Dexcom, Abbott or MicroTech password. It only reads your secured Nightscout relay.',
        ar: 'لا تطلب IAMINA أبدًا كلمة مرور Dexcom أو Abbott أو MicroTech. فهي تقرأ فقط جسر Nightscout الآمن الخاص بك.',
      );

  String get chooseSensor => _pick(
        fr: 'Choisissez votre capteur et suivez le chemin conseillé',
        en: 'Choose your sensor and follow the recommended path',
        ar: 'اختر المستشعر واتبع المسار المقترح',
      );

  String get dexcomPath => _pick(
        fr: 'Dexcom app + Share → Nightscout Connect → IAMINA',
        en: 'Dexcom app + Share → Nightscout Connect → IAMINA',
        ar: 'تطبيق Dexcom + Share ← Nightscout Connect ← IAMINA',
      );

  List<String> get dexcomSteps => [
        _pick(
          fr: 'Dans l’app Dexcom, activez Partage/Share et ajoutez au moins un follower afin que les données soient disponibles via Dexcom Share.',
          en: 'In the Dexcom app, enable Share and add at least one follower so readings are available through Dexcom Share.',
          ar: 'في تطبيق Dexcom فعّل Share وأضف متابعًا واحدًا على الأقل حتى تصبح القراءات متاحة عبر Dexcom Share.',
        ),
        _pick(
          fr: 'Dans votre site Nightscout, configurez Dexcom Share/Connect avec le compte qui reçoit réellement les mesures. Hors USA, utilisez la région hors-US/EU prévue par votre hébergement.',
          en: 'In your Nightscout site, configure Dexcom Share/Connect with the account that actually receives readings. Outside the US, use the non-US/EU region required by your host.',
          ar: 'في موقع Nightscout اضبط Dexcom Share/Connect باستخدام الحساب الذي يستقبل القراءات فعليًا. خارج الولايات المتحدة استخدم منطقة خارج-US/EU المناسبة لخدمة الاستضافة.',
        ),
        _pick(
          fr: 'Quand une mesure récente apparaît dans Nightscout, revenez dans IAMINA avec l’URL HTTPS Nightscout et un token/API secret dédié.',
          en: 'When a recent reading appears in Nightscout, return to IAMINA with the Nightscout HTTPS URL and a dedicated token/API secret.',
          ar: 'عندما تظهر قراءة حديثة في Nightscout، ارجع إلى IAMINA باستخدام رابط HTTPS الخاص بـNightscout ورمز token/API secret مخصص.',
        ),
      ];

  String get librePath => _pick(
        fr: 'Libre → Juggluco (ou xDrip compatible) → Nightscout → IAMINA',
        en: 'Libre → Juggluco (or compatible xDrip) → Nightscout → IAMINA',
        ar: 'Libre ← Juggluco (أو xDrip المتوافق) ← Nightscout ← IAMINA',
      );

  List<String> get libreSteps => [
        _pick(
          fr: 'Pour Libre 2/2+/3/3+, Juggluco est un chemin pris en charge sur Android selon le capteur/la région. xDrip ou xDrip4iOS peuvent aussi convenir selon le modèle.',
          en: 'For Libre 2/2+/3/3+, Juggluco is a supported Android path depending on sensor/region. xDrip or xDrip4iOS can also work depending on the model.',
          ar: 'بالنسبة إلى Libre 2/2+/3/3+، يمكن استخدام Juggluco على Android بحسب المستشعر/المنطقة. وقد يكون xDrip أو xDrip4iOS مناسبًا بحسب الطراز.',
        ),
        _pick(
          fr: 'Dans l’app source, activez l’envoi/synchronisation Nightscout et renseignez l’URL HTTPS Nightscout avec le secret/token prévu pour l’upload.',
          en: 'In the source app, enable Nightscout upload/sync and enter the Nightscout HTTPS URL with the secret/token intended for upload.',
          ar: 'في تطبيق المصدر فعّل الرفع/المزامنة إلى Nightscout وأدخل رابط HTTPS مع الرمز/السر المخصص للرفع.',
        ),
        _pick(
          fr: 'Vérifiez qu’une mesure récente est visible dans Nightscout, puis configurez IAMINA avec l’URL et un accès Nightscout dédié.',
          en: 'Verify that a recent reading is visible in Nightscout, then configure IAMINA with the URL and dedicated Nightscout access.',
          ar: 'تحقق من ظهور قراءة حديثة في Nightscout، ثم اضبط IAMINA باستخدام الرابط ووصول Nightscout مخصص.',
        ),
      ];

  String get linxPath => _pick(
        fr: 'LinX / AiDEX X → Juggluco → Nightscout → IAMINA',
        en: 'LinX / AiDEX X → Juggluco → Nightscout → IAMINA',
        ar: 'LinX / AiDEX X ← Juggluco ← Nightscout ← IAMINA',
      );

  List<String> get linxSteps => [
        _pick(
          fr: 'Connectez LinX / AiDEX X à Juggluco et vérifiez que Juggluco reçoit bien des mesures du capteur.',
          en: 'Connect LinX / AiDEX X to Juggluco and verify that Juggluco is receiving sensor readings.',
          ar: 'اربط LinX / AiDEX X مع Juggluco وتحقق من أن Juggluco يستقبل قراءات المستشعر.',
        ),
        _pick(
          fr: 'Dans Juggluco, ouvrez les réglages d’échange de données puis activez l’uploader Nightscout avec l’URL HTTPS et le secret/token.',
          en: 'In Juggluco, open data-exchange settings and enable the Nightscout uploader with the HTTPS URL and secret/token.',
          ar: 'في Juggluco افتح إعدادات تبادل البيانات وفعّل رافع Nightscout باستخدام رابط HTTPS والسر/الرمز.',
        ),
        _pick(
          fr: 'Quand Nightscout affiche une mesure récente, configurez IAMINA puis lancez Synchroniser.',
          en: 'When Nightscout shows a recent reading, configure IAMINA and run Sync.',
          ar: 'عندما يعرض Nightscout قراءة حديثة، اضبط IAMINA ثم شغّل المزامنة.',
        ),
      ];

  String get noNightscoutTitle => _pick(
        fr: 'Je n’ai pas encore Nightscout',
        en: 'I do not have Nightscout yet',
        ar: 'ليس لدي Nightscout بعد',
      );

  String get noNightscoutBody => _pick(
        fr: 'Nightscout est un relais indépendant : IAMINA ne le crée ni ne l’héberge aujourd’hui. Créez ou ouvrez votre site via la documentation officielle, sécurisez-le, vérifiez qu’il affiche une mesure récente, puis revenez avec son URL HTTPS et un token/API secret dédié.',
        en: 'Nightscout is an independent relay: IAMINA does not create or host it today. Create or open your site using the official documentation, secure it, verify that it shows a recent reading, then return with its HTTPS URL and a dedicated token/API secret.',
        ar: 'Nightscout جسر مستقل، وIAMINA لا تنشئه ولا تستضيفه حاليًا. أنشئ أو افتح موقعك عبر الوثائق الرسمية، أمّنه، وتحقق من ظهور قراءة حديثة، ثم عد برابط HTTPS ورمز token/API secret مخصص.',
      );

  String get stepSensor => _pick(
        fr: '1 · Capteur',
        en: '1 · Sensor',
        ar: '1 · المستشعر',
      );

  String get stepNightscout => _pick(
        fr: '2 · Nightscout',
        en: '2 · Nightscout',
        ar: '2 · Nightscout',
      );

  String get stepIamina => _pick(
        fr: '3 · IAMINA',
        en: '3 · IAMINA',
        ar: '3 · IAMINA',
      );

  String stepProgress(int step, String label) => _pick(
        fr: 'Étape $step : $label',
        en: 'Step $step: $label',
        ar: 'الخطوة $step: $label',
      );

  String get sensorQuestion => _pick(
        fr: 'Quel capteur utilisez-vous ?',
        en: 'Which sensor do you use?',
        ar: 'ما المستشعر الذي تستخدمه؟',
      );

  String get sensorQuestionBody => _pick(
        fr: 'Choisissez votre capteur. IAMINA vous montrera uniquement le chemin qui vous concerne.',
        en: 'Choose your sensor. IAMINA will show only the setup path that applies to you.',
        ar: 'اختر المستشعر. ستعرض IAMINA فقط مسار الإعداد المناسب لك.',
      );

  String nightscoutQuestion(String sensor) => _pick(
        fr: 'Avez-vous déjà Nightscout pour $sensor ?',
        en: 'Do you already have Nightscout for $sensor?',
        ar: 'هل لديك Nightscout بالفعل لـ $sensor؟',
      );

  String get nightscoutQuestionBody => _pick(
        fr: 'Nightscout est le relais sécurisé entre votre capteur et IAMINA.',
        en: 'Nightscout is the secure relay between your sensor and IAMINA.',
        ar: 'Nightscout هو الجسر الآمن بين المستشعر وIAMINA.',
      );

  String get yesNightscout => _pick(
        fr: 'Oui, Nightscout fonctionne déjà',
        en: 'Yes, Nightscout is already working',
        ar: 'نعم، Nightscout يعمل بالفعل',
      );

  String get noNightscoutYet => _pick(
        fr: 'Non / je ne sais pas encore',
        en: 'No / I am not sure yet',
        ar: 'لا / لست متأكدًا بعد',
      );

  String get previousStep => _pick(
        fr: 'Étape précédente',
        en: 'Previous step',
        ar: 'الخطوة السابقة',
      );

  String get prepareNightscoutTitle => _pick(
        fr: 'Préparez Nightscout pour ce capteur',
        en: 'Set up Nightscout for this sensor',
        ar: 'أعد Nightscout لهذا المستشعر',
      );

  String get prepareNightscoutBody => _pick(
        fr: 'Suivez uniquement ce parcours. Quand une mesure récente apparaît dans Nightscout, continuez vers IAMINA.',
        en: 'Follow only this path. When a recent reading appears in Nightscout, continue to IAMINA.',
        ar: 'اتبع هذا المسار فقط. عندما تظهر قراءة حديثة في Nightscout، تابع إلى IAMINA.',
      );

  String get nightscoutReady => _pick(
        fr: 'J’ai une mesure récente dans Nightscout',
        en: 'I have a recent reading in Nightscout',
        ar: 'لدي قراءة حديثة في Nightscout',
      );

  String get changeSensor => _pick(
        fr: 'Changer de capteur',
        en: 'Change sensor',
        ar: 'تغيير المستشعر',
      );

  String get connectTitle => _pick(
        fr: 'Connecter IAMINA',
        en: 'Connect IAMINA',
        ar: 'ربط IAMINA',
      );

  String get connectIntro => _pick(
        fr: 'Une fois Nightscout alimenté, choisissez votre capteur ci-dessous, appuyez sur Configurer, enregistrez l’URL + l’accès Nightscout, puis lancez Synchroniser. Une connexion réussie doit afficher une mesure récente et l’heure de la dernière synchro.',
        en: 'Once Nightscout has data, choose your sensor below, tap Configure, save the Nightscout URL + access, then run Sync. A successful connection should show a recent reading and the last sync time.',
        ar: 'بعد وصول البيانات إلى Nightscout، اختر المستشعر أدناه واضغط إعداد، ثم احفظ رابط Nightscout وبيانات الوصول وشغّل المزامنة. يجب أن يعرض الاتصال الناجح قراءة حديثة ووقت آخر مزامنة.',
      );

  String get troubleTitle => _pick(
        fr: 'Aucune mesure n’arrive ? Vérifiez dans cet ordre',
        en: 'No readings arriving? Check in this order',
        ar: 'لا تصل قراءات؟ تحقق بهذا الترتيب',
      );

  List<String> get troubleSteps => [
        _pick(
          fr: 'Le capteur affiche d’abord une mesure récente dans son app/service source.',
          en: 'The sensor first shows a recent reading in its source app/service.',
          ar: 'يجب أن يعرض المستشعر أولًا قراءة حديثة في تطبيق/خدمة المصدر.',
        ),
        _pick(
          fr: 'La même mesure apparaît ensuite dans Nightscout avant d’essayer IAMINA.',
          en: 'The same reading then appears in Nightscout before you try IAMINA.',
          ar: 'ثم يجب أن تظهر القراءة نفسها في Nightscout قبل تجربة IAMINA.',
        ),
        _pick(
          fr: 'L’URL IAMINA commence par HTTPS et le token/API secret correspond bien à ce site Nightscout.',
          en: 'The IAMINA URL starts with HTTPS and the token/API secret belongs to that Nightscout site.',
          ar: 'يبدأ رابط IAMINA بـHTTPS ويخص الرمز/API secret موقع Nightscout نفسه.',
        ),
        _pick(
          fr: 'Après correction, relancez Synchroniser. Si Nightscout est frais mais IAMINA reste vide, la connexion IAMINA doit être diagnostiquée.',
          en: 'After fixing the upstream issue, run Sync again. If Nightscout is fresh but IAMINA remains empty, the IAMINA connection needs diagnosis.',
          ar: 'بعد إصلاح المصدر أعد تشغيل المزامنة. إذا كانت بيانات Nightscout حديثة وبقيت IAMINA فارغة، فيجب تشخيص اتصال IAMINA.',
        ),
      ];
}
