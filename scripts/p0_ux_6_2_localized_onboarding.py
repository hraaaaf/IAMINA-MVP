#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L10N = ROOT / 'frontend' / 'lib' / 'l10n'

STRINGS = {
'fr': {
'onboardingWelcome': "Bonjour ! Je suis IAmina, votre compagnon de suivi du diabète.",
'onboardingChooseLanguage': 'Choisissez la langue de l’application.',
'onboardingChooseCountry': 'Dans quel pays utilisez-vous IAmina ?',
'onboardingChooseTone': 'Quel ton préférez-vous ?',
'onboardingToneNeutral': 'Neutre et professionnel',
'onboardingToneFriendly': 'Simple et chaleureux',
'onboardingCountryMorocco': 'Maroc',
'onboardingCountryFrance': 'France',
'onboardingCountryOther': 'Autre pays',
'onboardingTypeQuestion': 'Quel type de diabète gérez-vous au quotidien ?',
'onboardingTreatmentQuestion': 'Quel est votre mode de traitement principal ?',
'onboardingTreatmentInsulin': 'Insuline (injection ou pompe)',
'onboardingTreatmentLifestyle': 'Hygiène de vie seule',
'onboardingTargetQuestion': 'Quels sont vos objectifs glycémiques ? Le repère général affiché est 70–180 mg/dL, sauf cible personnelle différente.',
'onboardingTargetStandard': 'Repère général (70–180)',
'onboardingTargetCustom': 'Cible personnelle',
'onboardingUnitQuestion': 'Quelle unité préférez-vous pour les mesures ?',
'onboardingUnitMg': 'mg/dL',
'onboardingUnitMmol': 'mmol/L',
'onboardingReady': 'Votre espace est configuré. Vous pourrez modifier ces choix dans votre profil.',
'onboardingStart': 'Commencer',
'onboardingSaving': 'Enregistrement…',
'onboardingAssistantLabel': 'Assistant de configuration',
},
'en': {
'onboardingWelcome': 'Hello! I am IAmina, your diabetes tracking companion.',
'onboardingChooseLanguage': 'Choose the app language.',
'onboardingChooseCountry': 'Which country do you use IAmina in?',
'onboardingChooseTone': 'Which tone do you prefer?',
'onboardingToneNeutral': 'Neutral and professional',
'onboardingToneFriendly': 'Simple and warm',
'onboardingCountryMorocco': 'Morocco',
'onboardingCountryFrance': 'France',
'onboardingCountryOther': 'Another country',
'onboardingTypeQuestion': 'What type of diabetes do you manage?',
'onboardingTreatmentQuestion': 'What is your main treatment?',
'onboardingTreatmentInsulin': 'Insulin (injection or pump)',
'onboardingTreatmentLifestyle': 'Lifestyle only',
'onboardingTargetQuestion': 'What are your glucose targets? The general reference shown is 70–180 mg/dL unless your personal target differs.',
'onboardingTargetStandard': 'General reference (70–180)',
'onboardingTargetCustom': 'Personal target',
'onboardingUnitQuestion': 'Which measurement unit do you prefer?',
'onboardingUnitMg': 'mg/dL',
'onboardingUnitMmol': 'mmol/L',
'onboardingReady': 'Your space is configured. You can change these choices in your profile.',
'onboardingStart': 'Start',
'onboardingSaving': 'Saving…',
'onboardingAssistantLabel': 'Setup assistant',
},
'ar': {
'onboardingWelcome': 'مرحبًا! أنا IAmina، رفيقك لمتابعة داء السكري.',
'onboardingChooseLanguage': 'اختر لغة التطبيق.',
'onboardingChooseCountry': 'في أي بلد تستخدم IAmina؟',
'onboardingChooseTone': 'ما الأسلوب الذي تفضله؟',
'onboardingToneNeutral': 'محايد ومهني',
'onboardingToneFriendly': 'بسيط وودود',
'onboardingCountryMorocco': 'المغرب',
'onboardingCountryFrance': 'فرنسا',
'onboardingCountryOther': 'بلد آخر',
'onboardingTypeQuestion': 'ما نوع داء السكري الذي تتابعه؟',
'onboardingTreatmentQuestion': 'ما هو علاجك الرئيسي؟',
'onboardingTreatmentInsulin': 'الأنسولين (حقن أو مضخة)',
'onboardingTreatmentLifestyle': 'نمط الحياة فقط',
'onboardingTargetQuestion': 'ما أهداف سكر الدم لديك؟ المرجع العام المعروض هو 70–180 mg/dL ما لم يختلف هدفك الشخصي.',
'onboardingTargetStandard': 'المرجع العام (70–180)',
'onboardingTargetCustom': 'هدف شخصي',
'onboardingUnitQuestion': 'ما وحدة القياس التي تفضلها؟',
'onboardingUnitMg': 'mg/dL',
'onboardingUnitMmol': 'mmol/L',
'onboardingReady': 'تم إعداد مساحتك. يمكنك تعديل هذه الاختيارات من ملفك الشخصي.',
'onboardingStart': 'ابدأ',
'onboardingSaving': 'جارٍ الحفظ…',
'onboardingAssistantLabel': 'مساعد الإعداد',
}}

for locale, values in STRINGS.items():
    path = L10N / f'app_{locale}.arb'
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

service = r'''import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_client.dart';

class LocalExperiencePreference {
  final String language;
  final String country;
  final String tone;

  const LocalExperiencePreference({
    required this.language,
    required this.country,
    required this.tone,
  });
}

class LocalePreferenceService extends ChangeNotifier {
  static const _languageKey = 'iamina.ui_language';
  static const _countryKey = 'iamina.country';
  static const _toneKey = 'iamina.local_tone';

  final ApiClient _apiClient;
  final Locale? _auditLocale;
  final FlutterSecureStorage _storage;

  Locale _locale = const Locale('fr');
  String _country = 'MA';
  String _tone = 'neutral';
  bool _loaded = false;

  LocalePreferenceService(
    this._apiClient, {
    Locale? auditLocale,
    FlutterSecureStorage storage = const FlutterSecureStorage(),
  })  : _auditLocale = auditLocale,
        _storage = storage;

  Locale get locale => _locale;
  String get country => _country;
  String get tone => _tone;
  bool get loaded => _loaded;
  bool get isAuditLocale => _auditLocale != null;

  static Locale localeFromResolvedLanguage(Object? value) => switch (value) {
        'ar' => const Locale('ar'),
        'en' => const Locale('en'),
        _ => const Locale('fr'),
      };

  Future<void> refresh() async {
    final auditLocale = _auditLocale;
    if (auditLocale != null) {
      _locale = auditLocale;
      _loaded = true;
      notifyListeners();
      return;
    }

    final localLanguage = await _storage.read(key: _languageKey);
    final localCountry = await _storage.read(key: _countryKey);
    final localTone = await _storage.read(key: _toneKey);
    if (localLanguage != null) _locale = localeFromResolvedLanguage(localLanguage);
    if (localCountry != null && localCountry.isNotEmpty) _country = localCountry;
    if (localTone != null && localTone.isNotEmpty) _tone = localTone;

    try {
      final response = await _apiClient.client.get(Uri.parse('/api/v1/profile/locale'));
      if (response.isSuccessful && response.body is Map<String, dynamic>) {
        final resolved = (response.body as Map<String, dynamic>)['resolved'];
        if (resolved is Map<String, dynamic> && localLanguage == null) {
          _locale = localeFromResolvedLanguage(resolved['ui_language']);
        }
      }
    } catch (_) {
      // The local choice remains authoritative while offline or signed out.
    } finally {
      _loaded = true;
      notifyListeners();
    }
  }

  Future<void> setExperience({
    required String language,
    required String country,
    required String tone,
  }) async {
    _locale = localeFromResolvedLanguage(language);
    _country = country;
    _tone = tone;
    await Future.wait([
      _storage.write(key: _languageKey, value: language),
      _storage.write(key: _countryKey, value: country),
      _storage.write(key: _toneKey, value: tone),
    ]);
    _loaded = true;
    notifyListeners();
  }
}
'''
(ROOT / 'frontend/lib/services/locale_preference_service.dart').write_text(service, encoding='utf-8')

screen = r'''import 'package:drift/drift.dart' as drift;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../l10n/app_localizations.dart';
import '../../services/locale_preference_service.dart';

class OnboardingChatScreen extends StatefulWidget {
  const OnboardingChatScreen({super.key});

  @override
  State<OnboardingChatScreen> createState() => _OnboardingChatScreenState();
}

class _OnboardingChatScreenState extends State<OnboardingChatScreen> {
  String? _language;
  String? _country;
  String? _tone;
  String? _diabetesType;
  String? _treatment;
  String _unit = 'mg/dL';
  bool _saving = false;

  AppLocalizations get l10n => AppLocalizations.of(context)!;

  Future<void> _selectLanguage(String value) async {
    _language = value;
    await context.read<LocalePreferenceService>().setExperience(
      language: value,
      country: _country ?? 'MA',
      tone: _tone ?? 'neutral',
    );
    if (mounted) setState(() {});
  }

  Future<void> _finish() async {
    if (_language == null || _country == null || _tone == null ||
        _diabetesType == null || _treatment == null) return;
    setState(() => _saving = true);
    final localeService = context.read<LocalePreferenceService>();
    await localeService.setExperience(
      language: _language!, country: _country!, tone: _tone!,
    );
    if (!mounted) return;
    final db = context.read<AppDatabase>();
    final firebaseUser = FirebaseAuth.instance.currentUser;
    final userId = firebaseUser?.uid.hashCode.abs() ?? 1;
    final profile = PatientProfilesCompanion.insert(
      userId: drift.Value(userId),
      preferredLanguage: drift.Value(_language!),
      updatedAt: DateTime.now(),
      diabetesType: drift.Value(_diabetesType!),
      treatment: drift.Value(_treatment!),
      unitPreference: drift.Value(_unit),
      targetRangeLow: const drift.Value(70),
      targetRangeHigh: const drift.Value(180),
    );
    await db.into(db.patientProfiles).insertOnConflictUpdate(profile);
    if (mounted) context.go('/dashboard');
  }

  @override
  Widget build(BuildContext context) {
    final steps = <Widget>[
      _Question(title: l10n.onboardingChooseLanguage, children: [
        _Choice(label: 'Français', selected: _language == 'fr', onTap: () => _selectLanguage('fr')),
        _Choice(label: 'English', selected: _language == 'en', onTap: () => _selectLanguage('en')),
        _Choice(label: 'العربية', selected: _language == 'ar', onTap: () => _selectLanguage('ar')),
      ]),
      if (_language != null) _Question(title: l10n.onboardingChooseCountry, children: [
        _Choice(label: l10n.onboardingCountryMorocco, selected: _country == 'MA', onTap: () => setState(() => _country = 'MA')),
        _Choice(label: l10n.onboardingCountryFrance, selected: _country == 'FR', onTap: () => setState(() => _country = 'FR')),
        _Choice(label: l10n.onboardingCountryOther, selected: _country == 'OTHER', onTap: () => setState(() => _country = 'OTHER')),
      ]),
      if (_country != null) _Question(title: l10n.onboardingChooseTone, children: [
        _Choice(label: l10n.onboardingToneNeutral, selected: _tone == 'neutral', onTap: () => setState(() => _tone = 'neutral')),
        _Choice(label: l10n.onboardingToneFriendly, selected: _tone == 'friendly', onTap: () => setState(() => _tone = 'friendly')),
      ]),
      if (_tone != null) _Question(title: l10n.onboardingTypeQuestion, children: [
        _Choice(label: l10n.diabetesType1, selected: _diabetesType == 'type1', onTap: () => setState(() => _diabetesType = 'type1')),
        _Choice(label: l10n.diabetesType2, selected: _diabetesType == 'type2', onTap: () => setState(() => _diabetesType = 'type2')),
        _Choice(label: l10n.diabetesGestational, selected: _diabetesType == 'gestational', onTap: () => setState(() => _diabetesType = 'gestational')),
        _Choice(label: l10n.diabetesPreDiabetes, selected: _diabetesType == 'pre', onTap: () => setState(() => _diabetesType = 'pre')),
      ]),
      if (_diabetesType != null) _Question(title: l10n.onboardingTreatmentQuestion, children: [
        _Choice(label: l10n.onboardingTreatmentInsulin, selected: _treatment == 'insulin', onTap: () => setState(() => _treatment = 'insulin')),
        _Choice(label: l10n.treatmentTablets, selected: _treatment == 'tablets', onTap: () => setState(() => _treatment = 'tablets')),
        _Choice(label: l10n.onboardingTreatmentLifestyle, selected: _treatment == 'lifestyle', onTap: () => setState(() => _treatment = 'lifestyle')),
      ]),
      if (_treatment != null) _Question(title: l10n.onboardingUnitQuestion, children: [
        _Choice(label: l10n.onboardingUnitMg, selected: _unit == 'mg/dL', onTap: () => setState(() => _unit = 'mg/dL')),
        _Choice(label: l10n.onboardingUnitMmol, selected: _unit == 'mmol/L', onTap: () => setState(() => _unit = 'mmol/L')),
      ]),
    ];

    final ready = _language != null && _country != null && _tone != null &&
        _diabetesType != null && _treatment != null;
    return Scaffold(
      backgroundColor: AminaTheme.surfaceMuted,
      appBar: AppBar(title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('IAmina'),
        Text(l10n.onboardingAssistantLabel, style: const TextStyle(fontSize: 12)),
      ])),
      body: SafeArea(child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(l10n.onboardingWelcome, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 20),
          ...steps,
          if (ready) ...[
            const SizedBox(height: 12),
            Text(l10n.onboardingReady),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _saving ? null : _finish,
              child: Text(_saving ? l10n.onboardingSaving : l10n.onboardingStart),
            ),
          ],
        ],
      )),
    );
  }
}

class _Question extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Question({required this.title, required this.children});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
      const SizedBox(height: 10),
      Wrap(spacing: 8, runSpacing: 8, children: children),
    ]),
  );
}

class _Choice extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _Choice({required this.label, required this.selected, required this.onTap});
  @override
  Widget build(BuildContext context) => ChoiceChip(
    label: Text(label), selected: selected, onSelected: (_) => onTap(),
  );
}
'''
(ROOT / 'frontend/lib/features/auth/onboarding_chat_screen.dart').write_text(screen, encoding='utf-8')

test = r'''import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('onboarding separates language country and tone and never forces French', () {
    final source = File('lib/features/auth/onboarding_chat_screen.dart').readAsStringSync();
    expect(source, contains('onboardingChooseLanguage'));
    expect(source, contains('onboardingChooseCountry'));
    expect(source, contains('onboardingChooseTone'));
    expect(source, contains('preferredLanguage: drift.Value(_language!)'));
    expect(source, isNot(contains("preferredLanguage: const drift.Value('fr')")));
  });

  test('locale preference persists pre-auth experience locally', () {
    final source = File('lib/services/locale_preference_service.dart').readAsStringSync();
    expect(source, contains('FlutterSecureStorage'));
    expect(source, contains('iamina.ui_language'));
    expect(source, contains('iamina.country'));
    expect(source, contains('iamina.local_tone'));
    expect(source, contains('setExperience'));
  });
}
'''
path = ROOT / 'frontend/test/p0_localized_onboarding_contract_test.dart'
path.write_text(test, encoding='utf-8')
