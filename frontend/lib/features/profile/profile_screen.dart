import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' as drift;
import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/amina_text_field.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../../core/widgets/first_use_panel.dart';
import '../../l10n/audited_page_copy.dart';
import '../../data/drift/database.dart';
import '../../data/drift/patient_treatment_declaration_store.dart';
import '../../services/auth_service.dart';
import '../../services/app_lock_service.dart';
import '../../services/api_client.dart';
import '../../services/consent_service.dart';
import '../../services/sync_service.dart';
import 'medical_treatment_declaration_v1.dart';
import 'medical_treatment_multi_selector.dart';

part 'profile_screen_presentation.dart';

String _profileUiText(
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

String _profileValidationMessage(BuildContext context) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') {
    return 'أدخل نطاق غلوكوز صالحًا. يمكنك إضافة نوع السكري والعلاج لاحقًا.';
  }
  if (code == 'en') {
    return 'Enter a valid glucose range. Diagnosis and treatment can be added later.';
  }
  return 'Saisissez une plage glycémique valide. Le diagnostic et le traitement peuvent être ajoutés plus tard.';
}

/// Do not claim remote confirmation while treatment data is pending or in conflict.
bool d7ProfileSaveCanShowConfirmed({
  required bool mirrorConfirmed,
  required String? treatmentSyncStatus,
}) =>
    mirrorConfirmed &&
    (treatmentSyncStatus == null || treatmentSyncStatus == 'confirmed');

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _targetLowController = TextEditingController();
  final _targetHighController = TextEditingController();
  String? _diabetesType;
  String? _treatment; // legacy clinical scalar stays unchanged
  D7TreatmentDeclaration _declaredTreatments = D7TreatmentDeclaration.later();
  bool _treatmentTouched = false;
  bool _treatmentConflict = false;
  bool _resolvingTreatmentConflict = false;
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
    final profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
    if (profile != null) {
      if (!mounted) return;
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
    if (db.patientVaultScope != null) {
      final record = await PatientTreatmentDeclarationStore(db).read();
      if (!mounted || record == null) return;
      final status = D7TreatmentStatus.values.firstWhere(
        (value) => d7StateCode(value) == record.state,
      );
      setState(() {
        _declaredTreatments = D7TreatmentDeclaration(status, record.codes);
        _treatmentConflict = record.syncStatus == 'conflict';
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
          decoration: BoxDecoration(
            color: AminaVisualLanguage.cardSurface(context),
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: AminaVisualLanguage.controlBorder(context),
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
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                l10n.signOutConfirmBody,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 13,
                  color: AminaVisualLanguage.secondary(context),
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
                        side: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        l10n.cancel,
                        style: TextStyle(
                          color: AminaVisualLanguage.primaryText(context),
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
                color: AminaVisualLanguage.controlBorder(context),
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
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: AminaVisualLanguage.primaryText(context),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.consentWithdrawConfirmBody,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: AminaVisualLanguage.secondary(context),
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
                      side: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      l10n.cancel,
                      style: TextStyle(
                        color: AminaVisualLanguage.primaryText(context),
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

  String _conflictSummary(String state, List<String> codes) {
    if (state != 'declared') {
      return switch (state) {
        'unsure' => _profileUiText(context, fr: 'Je ne sais pas',
          en: 'Not sure', ar: 'لا أعرف'),
        'none_declared' => _profileUiText(context, fr: 'Aucun traitement déclaré',
          en: 'No treatment reported', ar: 'لا يوجد علاج مصرّح به'),
        _ => _profileUiText(context, fr: 'Je répondrai plus tard',
          en: 'Answer later', ar: 'سأجيب لاحقًا'),
      };
    }
    return codes.map((code) => switch (code) {
      'insulin' => _profileUiText(context,
        fr: 'Insuline', en: 'Insulin', ar: 'الأنسولين'),
      'oral_meds' => _profileUiText(context,
        fr: 'Médicaments oraux', en: 'Oral medicines', ar: 'أدوية فموية'),
      'lifestyle' => _profileUiText(context,
        fr: 'Habitudes de vie', en: 'Lifestyle measures', ar: 'نمط الحياة'),
      _ => _profileUiText(context,
        fr: 'Autre traitement déclaré', en: 'Other reported treatment',
        ar: 'علاج آخر مصرّح به'),
    }).join(' + ');
  }

  Future<void> _resolveTreatmentConflict() async {
    if (_resolvingTreatmentConflict) return;
    final db = context.read<AppDatabase>();
    final api = context.read<ApiClient>();
    final auth = context.read<AuthService>();
    final lock = context.read<AppLockService>();
    final sync = context.read<SyncService>();
    final epoch = AuthService.authEpoch;
    if (db.patientVaultScope?.nativeDjangoUserId == null ||
        !auth.hasRemoteApiCredential || !lock.isUnlocked) return;
    setState(() => _resolvingTreatmentConflict = true);
    try {
      final store = PatientTreatmentDeclarationStore(db);
      final local = await store.read();
      if (!mounted || AuthService.authEpoch != epoch ||
          !lock.isUnlocked || local == null ||
          local.syncStatus != 'conflict') return;
      final remote = await api.getProfile();
      if (!mounted || AuthService.authEpoch != epoch ||
          !lock.isUnlocked || remote == null) return;
      final remoteState = remote['treatment_declaration_state'];
      final remoteCodes = remote['treatment_declarations'];
      final serverAt = verifiedServerTreatmentRevision(remote);
      if (remote['treatment_declaration_source'] != 'patient_declared' ||
          remote['treatment_declaration_version'] != 1 ||
          remoteState is! String || remoteCodes is! List ||
          remoteCodes.any((item) => item is! String) ||
          serverAt == null) return;
      final codes = remoteCodes.cast<String>().toList(growable: false);
      try {
        validatePatientTreatmentDeclarationV1(
          state: remoteState, codes: codes,
        );
      } on ArgumentError {
        return;
      }
      final apply = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(_profileUiText(context,
            fr: 'Conflit de synchronisation',
            en: 'Synchronization conflict',
            ar: 'تعارض في المزامنة')),
          content: SingleChildScrollView(child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(_profileUiText(context, fr: 'Sur cet appareil :',
                en: 'On this device:', ar: 'على هذا الجهاز:')),
              Text(_conflictSummary(local.state, local.codes)),
              const SizedBox(height: 12),
              Text(_profileUiText(context, fr: 'Sur votre compte :',
                en: 'On your account:', ar: 'على حسابك:')),
              Text(_conflictSummary(remoteState, codes)),
              const SizedBox(height: 12),
              Text(_profileUiText(context,
                fr: 'Conserver ma version remplacera la déclaration distante après confirmation du serveur.',
                en: 'Keeping my version will replace the remote declaration only after server confirmation.',
                ar: 'الاحتفاظ بنسختي سيستبدل التصريح البعيد فقط بعد تأكيد الخادم.')),
            ])),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: Text(_profileUiText(context, fr: 'Annuler',
                en: 'Cancel', ar: 'إلغاء')),
            ),
            FilledButton(
              key: const Key('d7-keep-local-conflict'),
              onPressed: () => Navigator.pop(dialogContext, true),
              child: Text(_profileUiText(context,
                fr: 'Conserver ma version', en: 'Keep my version',
                ar: 'الاحتفاظ بنسختي')),
            ),
          ],
        ),
      );
      if (apply != true || !mounted || AuthService.authEpoch != epoch ||
          !lock.isUnlocked) return;
      final rebased = await store.retryConflictAfterExplicitReview(
        expectedGeneration: local.localGeneration,
        currentServerRevisionUtc: serverAt,
      );
      if (!rebased || !mounted || AuthService.authEpoch != epoch ||
          !lock.isUnlocked) return;
      final confirmed = await sync.sendPendingTreatmentDeclaration();
      if (!mounted || AuthService.authEpoch != epoch) return;
      final latest = await store.read();
      if (!mounted || AuthService.authEpoch != epoch) return;
      setState(() => _treatmentConflict = latest?.syncStatus == 'conflict');
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(confirmed
          ? _profileUiText(context, fr: 'Déclaration synchronisée.',
              en: 'Declaration synchronized.', ar: 'تمت مزامنة التصريح.')
          : _profileUiText(context,
              fr: 'Déclaration conservée sur cet appareil. Synchronisation non confirmée.',
              en: 'Declaration kept on this device. Remote synchronization not confirmed.',
              ar: 'تم الاحتفاظ بالتصريح على هذا الجهاز. لم يتم تأكيد المزامنة.')),
      ));
    } catch (_) {
      if (mounted && AuthService.authEpoch == epoch) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(_profileUiText(context,
            fr: 'Impossible de vérifier la déclaration distante. Les données locales sont conservées.',
            en: 'Unable to verify remote declaration. Local data is preserved.',
            ar: 'تعذر التحقق من التصريح البعيد. تم الاحتفاظ بالبيانات المحلية.')),
        ));
      }
    } finally {
      if (mounted) setState(() => _resolvingTreatmentConflict = false);
    }
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

    if (!validRange) {
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
            userId: drift.Value(db.activeProfileRowId),
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

    bool remoteMirrorConfirmed = context.read<ApiClient>().canSyncClinicalData;
    if (_treatmentTouched && db.patientVaultScope != null) {
      // Durable local-first write. Do not use legacy unconditioned PATCH:
      // only the vault-bound synchronizer may upload and ACK this generation.
      await PatientTreatmentDeclarationStore(db).write(
        state: d7StateCode(_declaredTreatments.state),
        codes: _declaredTreatments.codes,
      );
      final auth = context.read<AuthService>();
      remoteMirrorConfirmed = false;
      if (mounted && auth.hasRemoteApiCredential &&
          db.patientVaultScope?.nativeDjangoUserId != null) {
        remoteMirrorConfirmed =
            await context.read<SyncService>().sendPendingTreatmentDeclaration();
      }
    }

    if (mounted) {
      final latest = db.patientVaultScope != null
          ? await PatientTreatmentDeclarationStore(db).read()
          : null;
      if (!mounted) return;
      final fullyConfirmed = d7ProfileSaveCanShowConfirmed(
        mirrorConfirmed: remoteMirrorConfirmed,
        treatmentSyncStatus: latest?.syncStatus,
      );
      setState(() {
        _hasPersistedProfile = true;
        _treatmentTouched = false;
        _treatmentConflict = latest?.syncStatus == 'conflict';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(fullyConfirmed
              ? AppLocalizations.of(context)!.profileUpdated
              : !context.read<ApiClient>().canSyncClinicalData
                ? AppLocalizations.of(context)!.syncLocalOnly
                : _profileUiText(context,
                  fr: 'Enregistré localement. Synchronisation non confirmée.',
                  en: 'Saved locally. Remote sync not confirmed.',
                  ar: 'تم الحفظ محليًا. لم يتم تأكيد المزامنة.',
                )),
          backgroundColor: fullyConfirmed
              ? AminaTheme.successEmerald : AminaTheme.warningOrange,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}
