import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' as drift;
import '../../core/theme/app_theme.dart';
import '../../core/widgets/amina_text_field.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../l10n/audited_page_copy.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../services/api_client.dart';
import '../../services/consent_service.dart';

part 'profile_screen_presentation.dart';

String _profileValidationMessage(BuildContext context) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') {
    return 'اختر نوع السكري والعلاج وأدخل نطاق غلوكوز صالحًا قبل الحفظ.';
  }
  if (code == 'en') {
    return 'Select diabetes type and treatment, and enter a valid glucose range before saving.';
  }
  return 'Sélectionnez le type de diabète et le traitement, puis saisissez une plage glycémique valide avant d’enregistrer.';
}

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _targetLowController = TextEditingController();
  final _targetHighController = TextEditingController();
  String? _diabetesType;
  String? _treatment;
  String _unit = 'mg/dL';
  bool _hasPersistedProfile = false;
  DateTime? _ramadanStartDate;
  DateTime? _ramadanEndDate;
  bool _savingRamadan = false;

  void _setPresentationState(VoidCallback fn) => setState(fn);

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  void _loadProfile() async {
    final db = context.read<AppDatabase>();
    final profile = await db.select(db.patientProfiles).getSingleOrNull();
    if (profile != null) {
      setState(() {
        _hasPersistedProfile = true;
        _diabetesType = profile.diabetesType;
        _treatment = profile.treatment;
        _unit = profile.unitPreference;
        _targetLowController.text = profile.targetRangeLow.toStringAsFixed(0);
        _targetHighController.text = profile.targetRangeHigh.toStringAsFixed(0);
        _ramadanStartDate = profile.ramadanStartDate;
        _ramadanEndDate = profile.ramadanEndDate;
      });
    }
  }

  @override
  Widget build(BuildContext context) => _buildPresentation(context);


  Future<void> _pickRamadanDate({required bool start}) async {
    final initial = start
        ? (_ramadanStartDate ?? DateTime.now())
        : (_ramadanEndDate ?? _ramadanStartDate ?? DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035, 12, 31),
    );
    if (picked == null || !mounted) return;
    setState(() {
      if (start) {
        _ramadanStartDate = DateTime(picked.year, picked.month, picked.day);
      } else {
        _ramadanEndDate = DateTime(picked.year, picked.month, picked.day);
      }
    });
  }

  Future<void> _saveRamadanPeriod(AppLocalizations l10n) async {
    final start = _ramadanStartDate;
    final end = _ramadanEndDate;
    if ((start == null) != (end == null)) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(l10n.ramadanNeedsBothDates)));
      return;
    }
    if (start != null && end != null && start.isAfter(end)) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(l10n.ramadanDateOrderError)));
      return;
    }

    setState(() => _savingRamadan = true);
    try {
      final db = context.read<AppDatabase>();
      final api = context.read<ApiClient>();
      final localSaved = await db.setRamadanPeriod(start: start, end: end);
      final serverSaved = await api.patchProfile({
        'ramadan_start_date': start == null ? null : _apiDate(start),
        'ramadan_end_date': end == null ? null : _apiDate(end),
      });
      if (!mounted) return;
      if (localSaved) setState(() => _hasPersistedProfile = true);

      late final String message;
      late final Color backgroundColor;
      if (localSaved && serverSaved) {
        message = l10n.ramadanSaved;
        backgroundColor = AminaTheme.successEmerald;
      } else if (localSaved) {
        message = l10n.ramadanSavedLocalOnly;
        backgroundColor = AminaTheme.warningOrange;
      } else if (serverSaved) {
        message = l10n.ramadanSavedServerOnly;
        backgroundColor = AminaTheme.warningOrange;
      } else {
        message = l10n.ramadanSaveFailed;
        backgroundColor = AminaTheme.dangerFg;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: backgroundColor,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _savingRamadan = false);
    }
  }


  String _apiDate(DateTime value) {
    final mm = value.month.toString().padLeft(2, '0');
    final dd = value.day.toString().padLeft(2, '0');
    return '${value.year}-$mm-$dd';
  }


  void _confirmSignOut() {
    final l10n = AppLocalizations.of(context)!;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => SingleChildScrollView(
        child: Container(
          padding: const EdgeInsetsDirectional.fromSTEB(24, 20, 24, 40),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: AminaTheme.ink200,
                  borderRadius: BorderRadius.circular(100),
                ),
              ),
              const SizedBox(height: 20),
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: AminaTheme.dangerBg,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.logout,
                  color: AminaTheme.dangerFg,
                  size: 24,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                l10n.signOutConfirmTitle,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: AminaTheme.ink900,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                l10n.signOutConfirmBody,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 13,
                  color: AminaTheme.ink500,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: const BorderSide(color: AminaTheme.ink200),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        l10n.cancel,
                        style: const TextStyle(
                          color: AminaTheme.ink700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () async {
                        // Capture everything before the async gap
                        final auth = context.read<AuthService>();
                        final router = GoRouter.of(context);
                        Navigator.pop(context);
                        await auth.signOut();
                        router.go('/login');
                      },
                      style: FilledButton.styleFrom(
                        backgroundColor: AminaTheme.dangerFg,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        l10n.confirmSignOut,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _confirmWithdrawConsent(AppLocalizations l10n) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetCtx) => Container(
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsetsDirectional.fromSTEB(24, 16, 24, 36),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AminaTheme.ink200,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: AminaTheme.dangerBg,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.psychology_outlined,
                color: AminaTheme.dangerFg,
                size: 24,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              l10n.consentWithdrawConfirmTitle,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: AminaTheme.ink900,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.consentWithdrawConfirmBody,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                color: AminaTheme.ink500,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(sheetCtx),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: AminaTheme.ink200),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      l10n.cancel,
                      style: const TextStyle(
                        color: AminaTheme.ink700,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: () async {
                      // Capture before async gap
                      final api = context.read<ApiClient>();
                      final db = context.read<AppDatabase>();
                      final consent = context.read<ConsentService>();
                      Navigator.pop(sheetCtx);
                      await api.withdrawConsent().catchError((_) => false);
                      await db.setAiConsent(granted: false);
                      consent.declineLocally();
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              AppLocalizations.of(context)!.consentWithdrawn,
                            ),
                          ),
                        );
                      }
                    },
                    style: FilledButton.styleFrom(
                      backgroundColor: AminaTheme.dangerFg,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      l10n.consentWithdraw,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _saveProfile() async {
    final diabetesType = _diabetesType;
    final treatment = _treatment;
    final low = double.tryParse(_targetLowController.text.trim());
    final high = double.tryParse(_targetHighController.text.trim());
    final validRange =
        low != null &&
        high != null &&
        low.isFinite &&
        high.isFinite &&
        low > 0 &&
        high > 0 &&
        low < high;

    if (diabetesType == null || treatment == null || !validRange) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_profileValidationMessage(context))),
      );
      return;
    }

    final db = context.read<AppDatabase>();
    await db
        .into(db.patientProfiles)
        .insertOnConflictUpdate(
          PatientProfilesCompanion.insert(
            userId: const drift.Value(1),
            preferredLanguage: drift.Value(
              Localizations.localeOf(context).languageCode,
            ),
            updatedAt: DateTime.now(),
            diabetesType: drift.Value(diabetesType),
            treatment: drift.Value(treatment),
            unitPreference: drift.Value(_unit),
            targetRangeLow: drift.Value(low),
            targetRangeHigh: drift.Value(high),
          ),
        );

    if (mounted) {
      setState(() => _hasPersistedProfile = true);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)!.profileUpdated),
          backgroundColor: AminaTheme.successEmerald,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}
