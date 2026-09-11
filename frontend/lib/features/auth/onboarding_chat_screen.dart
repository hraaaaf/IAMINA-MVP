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
        _treatment == null) {
      return;
    }
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
        child: LayoutBuilder(
          builder: (context, constraints) {
            final desktop = constraints.maxWidth >= 900;
            final questions = _OnboardingQuestions(
              welcome: l10n.onboardingWelcome,
              steps: steps,
              ready: ready,
              readyLabel: l10n.onboardingReady,
              saving: _saving,
              savingLabel: l10n.onboardingSaving,
              startLabel: l10n.onboardingStart,
              onFinish: _finish,
            );

            if (!desktop) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: [questions],
              );
            }

            return SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(28, 28, 28, 40),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 980),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        flex: 4,
                        child: _DesktopWelcomePanel(
                          title: 'IAmina',
                          subtitle: l10n.onboardingAssistantLabel,
                          body: l10n.onboardingWelcome,
                        ),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        flex: 6,
                        child: Container(
                          padding: const EdgeInsetsDirectional.fromSTEB(
                            28,
                            26,
                            28,
                            28,
                          ),
                          decoration: BoxDecoration(
                            color: Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: AminaTheme.ink100),
                            boxShadow: AminaTheme.shadowClinicalLg,
                          ),
                          child: questions,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _OnboardingQuestions extends StatelessWidget {
  final String welcome;
  final List<Widget> steps;
  final bool ready;
  final String readyLabel;
  final bool saving;
  final String savingLabel;
  final String startLabel;
  final VoidCallback onFinish;

  const _OnboardingQuestions({
    required this.welcome,
    required this.steps,
    required this.ready,
    required this.readyLabel,
    required this.saving,
    required this.savingLabel,
    required this.startLabel,
    required this.onFinish,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          welcome,
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 20),
        ...steps,
        if (ready) ...[
          const SizedBox(height: 4),
          Text(readyLabel),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, constraints) {
              final desktop = MediaQuery.sizeOf(context).width >= 900;
              return SizedBox(
                width: desktop ? 240 : constraints.maxWidth,
                child: FilledButton(
                  onPressed: saving ? null : onFinish,
                  child: Text(saving ? savingLabel : startLabel),
                ),
              );
            },
          ),
        ],
      ],
    );
  }
}

class _DesktopWelcomePanel extends StatelessWidget {
  final String title;
  final String subtitle;
  final String body;

  const _DesktopWelcomePanel({
    required this.title,
    required this.subtitle,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(28, 30, 28, 30),
      decoration: BoxDecoration(
        gradient: AminaTheme.heroGradient,
        borderRadius: BorderRadius.circular(24),
        boxShadow: AminaTheme.shadowClinicalLg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: .16),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.favorite_outline_rounded,
              color: Colors.white,
              size: 26,
            ),
          ),
          const SizedBox(height: 28),
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: TextStyle(
              color: Colors.white.withValues(alpha: .78),
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            body,
            style: TextStyle(
              color: Colors.white.withValues(alpha: .94),
              fontSize: 16,
              height: 1.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
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
