import 'dart:async';
import 'dart:developer' as developer;

import 'package:drift/drift.dart' as drift;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../data/drift/database.dart';
import '../../l10n/app_localizations.dart';
import '../../services/auth_service.dart';
import '../../services/country_choices.dart';
import '../../services/locale_preference_service.dart';

String _preferencesCopy(
  BuildContext context, {
  required String fr,
  required String en,
  required String ar,
}) {
  return switch (Localizations.localeOf(context).languageCode) {
    'fr' => fr,
    'ar' => ar,
    _ => en,
  };
}

class OnboardingChatScreen extends StatefulWidget {
  final bool preferencesOnly;

  const OnboardingChatScreen({
    super.key,
    this.preferencesOnly = false,
  });

  @override
  State<OnboardingChatScreen> createState() => _OnboardingChatScreenState();
}

class _OnboardingChatScreenState extends State<OnboardingChatScreen> {
  static const _persistenceTimeout = Duration(seconds: 10);

  String? _language;
  String? _country;
  String? _diabetesType;
  String? _treatment;
  String _unit = 'mg/dL';
  bool _saving = false;
  bool _preferencesInitialized = false;
  bool _countrySuggestionRequested = false;
  bool _countryTouched = false;
  bool _countrySuggestedByIp = false;

  AppLocalizations get l10n => AppLocalizations.of(context)!;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (widget.preferencesOnly && !_preferencesInitialized) {
      final localeService = context.read<LocalePreferenceService>();
      final profile = context.read<PatientProfileData?>();
      _language = localeService.locale.languageCode;
      _country = countryByCode(localeService.country)?.code;
      _diabetesType = profile?.diabetesType;
      _treatment = profile?.treatment;
      _unit = profile?.unitPreference ?? _unit;
      _preferencesInitialized = true;
    }
    if (!_countrySuggestionRequested) {
      _countrySuggestionRequested = true;
      if (_country == null) unawaited(_suggestCountryFromIp());
    }
  }

  Future<void> _suggestCountryFromIp() async {
    final code = await context.read<LocalePreferenceService>().suggestCountryFromIp();
    if (!mounted || _countryTouched || _country != null) return;
    final choice = countryByCode(code);
    if (choice == null) return;
    setState(() {
      _country = choice.code;
      _countrySuggestedByIp = true;
    });
  }

  void _selectCountry(String country) {
    setState(() {
      _country = country;
      _countryTouched = true;
      _countrySuggestedByIp = false;
    });
  }

  void _clearCountry() {
    if (_country == null && _countryTouched) return;
    setState(() {
      _country = null;
      _countryTouched = true;
      _countrySuggestedByIp = false;
    });
  }

  Future<void> _selectLanguage(String value) async {
    _language = value;
    await context.read<LocalePreferenceService>().setLanguageOnly(value);
    if (mounted) setState(() {});
  }

  Future<void> _finish() async {
    if (_language == null || _country == null) return;
    if (!widget.preferencesOnly &&
        (_diabetesType == null || _treatment == null)) {
      return;
    }

    setState(() => _saving = true);

    try {
      final localeService = context.read<LocalePreferenceService>();
      await localeService
          .setExperience(
            language: _language!,
            country: _country!,
            tone: 'neutral',
          )
          .timeout(_persistenceTimeout);

      if (!mounted) return;
      if (widget.preferencesOnly) {
        final router = GoRouter.of(context);
        if (router.canPop()) {
          router.pop();
        } else {
          router.go('/profile');
        }
        return;
      }

      final db = context.read<AppDatabase>();
      final firebaseUser = context.read<AuthService>().firebaseUser;
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

      await db
          .into(db.patientProfiles)
          .insertOnConflictUpdate(profile)
          .timeout(_persistenceTimeout);

      if (mounted) context.go('/dashboard');
    } on TimeoutException catch (error, stackTrace) {
      developer.log(
        'Onboarding local persistence timed out.',
        name: 'iamina.onboarding.finish',
        error: error,
        stackTrace: stackTrace,
      );
      if (mounted) setState(() => _saving = false);
    } catch (error, stackTrace) {
      developer.log(
        'Onboarding local persistence failed.',
        name: 'iamina.onboarding.finish',
        error: error,
        stackTrace: stackTrace,
      );
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final preferenceSteps = <Widget>[
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
      _Question(
        title: l10n.onboardingChooseCountry,
        children: [
          _CountrySearchField(
            code: _country,
            proposedFromIp: _countrySuggestedByIp,
            onSelected: _selectCountry,
            onCleared: _clearCountry,
          ),
        ],
      ),
    ];

    final onboardingSteps = <Widget>[
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
            _CountrySearchField(
              code: _country,
              proposedFromIp: _countrySuggestedByIp,
              onSelected: _selectCountry,
              onCleared: _clearCountry,
            ),
          ],
        ),
      if (_country != null)
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

    final steps = widget.preferencesOnly ? preferenceSteps : onboardingSteps;
    final onboardingProgress = widget.preferencesOnly
        ? null
        : _onboardingProgress(
            language: _language,
            country: _country,
            diabetesType: _diabetesType,
            treatment: _treatment,
          );

    final ready =
        _language != null &&
        _country != null &&
        (widget.preferencesOnly ||
            (_diabetesType != null && _treatment != null));

    final assistantLabel = widget.preferencesOnly
        ? _preferencesCopy(
            context,
            fr: 'Préférences IAmina',
            en: 'IAmina preferences',
            ar: 'تفضيلات IAmina',
          )
        : l10n.onboardingAssistantLabel;
    final welcome = widget.preferencesOnly
        ? _preferencesCopy(
            context,
            fr: 'Choisissez vos préférences. Vos données médicales restent dans votre profil.',
            en: 'Choose your preferences. Your medical data stays in your profile.',
            ar: 'اختر تفضيلاتك. تبقى بياناتك الطبية في ملفك الشخصي.',
          )
        : l10n.onboardingWelcome;
    final readyLabel = widget.preferencesOnly
        ? _preferencesCopy(
            context,
            fr: 'Préférences prêtes',
            en: 'Preferences ready',
            ar: 'التفضيلات جاهزة',
          )
        : l10n.onboardingReady;
    final finishLabel = widget.preferencesOnly
        ? _preferencesCopy(
            context,
            fr: 'Enregistrer',
            en: 'Save',
            ar: 'حفظ',
          )
        : l10n.onboardingStart;

    final compact = MediaQuery.sizeOf(context).width < 900;

    return Scaffold(
      backgroundColor: AminaTheme.surfaceMuted,
      bottomNavigationBar: compact && ready
          ? SafeArea(
              top: false,
              child: Container(
                decoration: BoxDecoration(
                  color: AminaTheme.surfaceMuted,
                  border: Border(
                    top: BorderSide(color: Theme.of(context).dividerColor),
                  ),
                ),
                padding: const EdgeInsetsDirectional.fromSTEB(20, 10, 20, 12),
                child: SizedBox(
                  height: 52,
                  child: FilledButton(
                    key: const Key('onboarding-sticky-start'),
                    onPressed: _saving ? null : _finish,
                    child: Text(_saving ? l10n.onboardingSaving : finishLabel),
                  ),
                ),
              ),
            )
          : null,
      appBar: AppBar(
        leading: widget.preferencesOnly
            ? const AminaPageExitButton(fallbackRoute: '/profile')
            : null,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('IAmina'),
            Text(
              assistantLabel,
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
              welcome: welcome,
              steps: steps,
              ready: ready,
              readyLabel: readyLabel,
              saving: _saving,
              savingLabel: l10n.onboardingSaving,
              startLabel: finishLabel,
              onFinish: _finish,
              progress: onboardingProgress,
              showInlineFinish: !compact,
            );

            if (!desktop) {
              return ListView(
                padding: const EdgeInsets.all(20),
                children: [questions],
              );
            }

            return SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(28, 28, 28, 40),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight > 68
                      ? constraints.maxHeight - 68
                      : 0,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1040),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          flex: 4,
                          child: _DesktopWelcomePanel(
                            title: 'IAmina',
                            subtitle: assistantLabel,
                            body: welcome,
                          ),
                        ),
                        const SizedBox(width: 28),
                        Expanded(
                          flex: 6,
                          child: Container(
                            padding: const EdgeInsetsDirectional.fromSTEB(
                              30,
                              28,
                              30,
                              30,
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
              ),
            );
          },
        ),
      ),
    );
  }
}

({int current, int total}) _onboardingProgress({
  required String? language,
  required String? country,
  required String? diabetesType,
  required String? treatment,
}) {
  var current = 1;
  if (language != null) current = 2;
  if (country != null) current = 3;
  if (diabetesType != null) current = 4;
  if (treatment != null) current = 5;
  return (current: current, total: 5);
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
  final ({int current, int total})? progress;
  final bool showInlineFinish;

  const _OnboardingQuestions({
    required this.welcome,
    required this.steps,
    required this.ready,
    required this.readyLabel,
    required this.saving,
    required this.savingLabel,
    required this.startLabel,
    required this.onFinish,
    this.progress,
    this.showInlineFinish = true,
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
        if (progress != null) ...[
          const SizedBox(height: 14),
          Semantics(
            label: _preferencesCopy(
              context,
              fr: 'Étape ${progress!.current} sur ${progress!.total}',
              en: 'Step ${progress!.current} of ${progress!.total}',
              ar: 'الخطوة ${progress!.current} من ${progress!.total}',
            ),
            child: ExcludeSemantics(
              child: Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: LinearProgressIndicator(
                        minHeight: 7,
                        value: progress!.current / progress!.total,
                        backgroundColor: AminaTheme.ink100,
                        color: AminaTheme.teal500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    _preferencesCopy(
                      context,
                      fr: 'Étape ${progress!.current}/${progress!.total} · ~1 min',
                      en: 'Step ${progress!.current}/${progress!.total} · ~1 min',
                      ar: 'الخطوة ${progress!.current}/${progress!.total} · نحو دقيقة',
                    ),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: AminaTheme.textSecondary(context),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 20),
        ...steps,
        if (ready && showInlineFinish) ...[
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

/// Editable, offline country suggestions. Free text alone is never saved.
class _CountrySearchField extends StatefulWidget {
  final String? code;
  final bool proposedFromIp;
  final ValueChanged<String> onSelected;
  final VoidCallback onCleared;
  const _CountrySearchField({
    required this.code,
    required this.proposedFromIp,
    required this.onSelected,
    required this.onCleared,
  });

  @override
  State<_CountrySearchField> createState() => _CountrySearchFieldState();
}

class _CountrySearchFieldState extends State<_CountrySearchField> {
  final TextEditingController _controller = TextEditingController();
  bool _updating = false;

  String get _lang => Localizations.localeOf(context).languageCode;

  void _setText(String text) {
    _updating = true;
    _controller.value = TextEditingValue(
      text: text, selection: TextSelection.collapsed(offset: text.length),
    );
    _updating = false;
  }

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_controller.text.isEmpty && widget.code != null) {
      final choice = countryByCode(widget.code);
      if (choice != null) _setText(choice.label(_lang));
    }
  }

  @override
  void didUpdateWidget(covariant _CountrySearchField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.code != null && widget.code != oldWidget.code) {
      final choice = countryByCode(widget.code);
      if (choice != null) _setText(choice.label(_lang));
    }
  }

  void _onTextChanged() {
    if (_updating || widget.code == null) return;
    final selected = countryByCode(widget.code);
    if (selected != null && _controller.text != selected.label(_lang)) {
      widget.onCleared(); // Unsuggested typing cannot silently keep old choice.
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lang = _lang;
    final entries = countryChoices
        .map((option) => DropdownMenuEntry<CountryChoice>(
              value: option,
              label: option.label(lang),
            ))
        .toList()
      ..sort((a, b) => a.label.compareTo(b.label));
    final width = (MediaQuery.sizeOf(context).width - 80).clamp(240.0, 520.0);
    return SizedBox(
      width: width,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DropdownMenu<CountryChoice>(
            key: const Key('onboarding-country-search'),
            controller: _controller,
            enableFilter: true,
            enableSearch: true,
            menuHeight: 260,
            requestFocusOnTap: true,
            expandedInsets: EdgeInsets.zero,
            leadingIcon: const Icon(Icons.search),
            label: Text(_preferencesCopy(context,
              fr: 'Rechercher un pays',
              en: 'Search for a country',
              ar: 'ابحث عن بلد',
            )),
            hintText: _preferencesCopy(context,
              fr: 'Saisissez le nom du pays',
              en: 'Type a country name',
              ar: 'اكتب اسم البلد',
            ),
            dropdownMenuEntries: entries,
            onSelected: (value) {
              if (value != null) widget.onSelected(value.code);
            },
          ),
          const SizedBox(height: 6),
          Text(
            widget.proposedFromIp
                ? _preferencesCopy(context,
                    fr: 'Proposé selon votre connexion Internet. Vérifiez ou modifiez le pays.',
                    en: 'Suggested from your Internet connection. Check or change the country.',
                    ar: 'مقترح حسب اتصال الإنترنت. تحقق من البلد أو غيّره.',
                  )
                : _preferencesCopy(context,
                    fr: 'Choisissez votre pays d’utilisation. La localisation IP est indicative.',
                    en: 'Choose your country of use. IP location is only an estimate.',
                    ar: 'اختر بلد الاستخدام. تحديد البلد حسب IP تقريبي فقط.',
                  ),
            style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context)),
          ),
        ],
      ),
    );
  }
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
