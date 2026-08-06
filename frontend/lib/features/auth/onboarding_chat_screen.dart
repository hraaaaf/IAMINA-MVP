import 'package:drift/drift.dart' as drift;
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
    if (_language == null ||
        _country == null ||
        _tone == null ||
        _diabetesType == null ||
        _treatment == null)
      return;
    setState(() => _saving = true);
    final localeService = context.read<LocalePreferenceService>();
    await localeService.setExperience(
      language: _language!,
      country: _country!,
      tone: _tone!,
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
      _Question(
        title: l10n.onboardingChooseLanguage,
        children: [
          _Choice(
            label: 'Français',
            selected: _language == 'fr',
            onTap: () => _selectLanguage('fr'),
          ),
          _Choice(
            label: 'English',
            selected: _language == 'en',
            onTap: () => _selectLanguage('en'),
          ),
          _Choice(
            label: 'العربية',
            selected: _language == 'ar',
            onTap: () => _selectLanguage('ar'),
          ),
        ],
      ),
      if (_language != null)
        _Question(
          title: l10n.onboardingChooseCountry,
          children: [
            _Choice(
              label: l10n.onboardingCountryMorocco,
              selected: _country == 'MA',
              onTap: () => setState(() => _country = 'MA'),
            ),
            _Choice(
              label: l10n.onboardingCountryFrance,
              selected: _country == 'FR',
              onTap: () => setState(() => _country = 'FR'),
            ),
            _Choice(
              label: l10n.onboardingCountryOther,
              selected: _country == 'OTHER',
              onTap: () => setState(() => _country = 'OTHER'),
            ),
          ],
        ),
      if (_country != null)
        _Question(
          title: l10n.onboardingChooseTone,
          children: [
            _Choice(
              label: l10n.onboardingToneNeutral,
              selected: _tone == 'neutral',
              onTap: () => setState(() => _tone = 'neutral'),
            ),
            _Choice(
              label: l10n.onboardingToneFriendly,
              selected: _tone == 'friendly',
              onTap: () => setState(() => _tone = 'friendly'),
            ),
          ],
        ),
      if (_tone != null)
        _Question(
          title: l10n.onboardingTypeQuestion,
          children: [
            _Choice(
              label: l10n.diabetesType1,
              selected: _diabetesType == 'type1',
              onTap: () => setState(() => _diabetesType = 'type1'),
            ),
            _Choice(
              label: l10n.diabetesType2,
              selected: _diabetesType == 'type2',
              onTap: () => setState(() => _diabetesType = 'type2'),
            ),
            _Choice(
              label: l10n.diabetesGestational,
              selected: _diabetesType == 'gestational',
              onTap: () => setState(() => _diabetesType = 'gestational'),
            ),
            _Choice(
              label: l10n.diabetesPreDiabetes,
              selected: _diabetesType == 'pre',
              onTap: () => setState(() => _diabetesType = 'pre'),
            ),
          ],
        ),
      if (_diabetesType != null)
        _Question(
          title: l10n.onboardingTreatmentQuestion,
          children: [
            _Choice(
              label: l10n.onboardingTreatmentInsulin,
              selected: _treatment == 'insulin',
              onTap: () => setState(() => _treatment = 'insulin'),
            ),
            _Choice(
              label: l10n.treatmentTablets,
              selected: _treatment == 'tablets',
              onTap: () => setState(() => _treatment = 'tablets'),
            ),
            _Choice(
              label: l10n.onboardingTreatmentLifestyle,
              selected: _treatment == 'lifestyle',
              onTap: () => setState(() => _treatment = 'lifestyle'),
            ),
          ],
        ),
      if (_treatment != null)
        _Question(
          title: l10n.onboardingUnitQuestion,
          children: [
            _Choice(
              label: l10n.onboardingUnitMg,
              selected: _unit == 'mg/dL',
              onTap: () => setState(() => _unit = 'mg/dL'),
            ),
            _Choice(
              label: l10n.onboardingUnitMmol,
              selected: _unit == 'mmol/L',
              onTap: () => setState(() => _unit = 'mmol/L'),
            ),
          ],
        ),
    ];

    final ready =
        _language != null &&
        _country != null &&
        _tone != null &&
        _diabetesType != null &&
        _treatment != null;
    return Scaffold(
      backgroundColor: AminaTheme.surfaceMuted,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('IAmina'),
            Text(
              l10n.onboardingAssistantLabel,
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(
              l10n.onboardingWelcome,
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 20),
            ...steps,
            if (ready) ...[
              const SizedBox(height: 12),
              Text(l10n.onboardingReady),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _saving ? null : _finish,
                child: Text(
                  _saving ? l10n.onboardingSaving : l10n.onboardingStart,
                ),
              ),
            ],
          ],
        ),
      ),
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
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
        ),
        const SizedBox(height: 10),
        Wrap(spacing: 8, runSpacing: 8, children: children),
      ],
    ),
  );
}

class _Choice extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _Choice({
    required this.label,
    required this.selected,
    required this.onTap,
  });
  @override
  Widget build(BuildContext context) => ChoiceChip(
    label: Text(label),
    selected: selected,
    onSelected: (_) => onTap(),
  );
}
