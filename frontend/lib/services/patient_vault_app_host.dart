import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;

import '../core/theme/app_theme.dart';
import '../data/drift/database.dart';
import '../data/drift/patient_vault_scope.dart';
import '../main.dart' show AminaApp;
import '../routes/app_router.dart';
import 'api_client.dart';
import 'app_lock_service.dart';
import 'auth_service.dart';
import 'consent_evidence_store.dart';
import 'consent_service.dart';
import 'd9_first_use_transport.dart';
import 'locale_preference_service.dart';
import 'modules_provider.dart';
import 'offline_demo_audit_seed.dart';
import 'patient_vault_session_controller.dart';
import 'sync_service.dart';

enum _D9FirstUseGate { notRequired, unresolved, checking, complete, newPatient, unavailable }

/// Each subtree holds ONLY ONE physical patient vault and its own consent,
/// profile stream, sync queue and router. No legacy 'amina' database is
/// injected into patient-facing providers.
class _VaultBindings {
  final AppDatabase db;
  final PatientVaultScope scope;
  final ConsentEvidenceStore evidence;
  final ConsentService consent;
  final SyncService sync;
  final AppRouterHolder router;
  final int authEpoch;
  bool syncStarted = false;
  final D9FirstUseTransport? d9FirstUse;
  final http.Client? d9Client;
  _D9FirstUseGate d9Gate;

  _VaultBindings(this.db, this.scope, this.evidence, this.consent,
      this.sync, this.router, this.authEpoch, {
        required this.d9FirstUse,
        required this.d9Client,
        required this.d9Gate,
      });

  void dispose() {
    d9Client?.close();
    router.dispose();
    consent.dispose();
    sync.dispose();
    // The vault controller exclusively owns and closes the physical DB.
  }
}

class PatientVaultAppHost extends StatefulWidget {
  final AuthService auth;
  final ApiClient api;
  final AppLockService appLock;
  final LocalePreferenceService locale;
  final PatientVaultSessionController controller;
  final bool auditAllowed;

  const PatientVaultAppHost({
    super.key,
    required this.auth,
    required this.api,
    required this.appLock,
    required this.locale,
    required this.controller,
    required this.auditAllowed,
  });

  @override
  State<PatientVaultAppHost> createState() => _PatientVaultAppHostState();
}

class _PatientVaultAppHostState extends State<PatientVaultAppHost> {
  late final AppDatabase _guestDatabase;
  late final AppRouterHolder _guestRouter;
  _VaultBindings? _bindings;
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    // Guest login only: this synthetic audit namespace is never a clinical
    // account, nor can it access quarantined pre-D7 'amina' rows.
    _guestDatabase = AppDatabase.forPatientVault(
      PatientVaultScope.auditOnly(),
    );
    _guestRouter = createAppRouterHolder(authService: widget.auth);
    widget.controller.addListener(_onVaultChanged);
    widget.appLock.addListener(_onLockChanged);
    unawaited(_bindCurrentVault());
  }

  void _onLockChanged() {
    _maybeStartSync();
    if (widget.appLock.isUnlocked) unawaited(_verifyD9FirstUse());
  }

  Future<void> _verifyD9FirstUse() async {
    final current = _bindings;
    if (current == null ||
        current.d9FirstUse == null ||
        !widget.appLock.isUnlocked ||
        (current.d9Gate != _D9FirstUseGate.unresolved &&
            current.d9Gate != _D9FirstUseGate.unavailable)) {
      return;
    }
    final generation = _generation;
    final epoch = AuthService.authEpoch;
    final owner = current.scope.nativeDjangoUserId;
    if (owner == null || widget.controller.activeDatabase != current.db) {
      return;
    }
    current.d9Gate = _D9FirstUseGate.checking;
    if (mounted) setState(() {});
    final proof = await current.d9FirstUse!.fetch();
    if (!mounted ||
        generation != _generation ||
        epoch != AuthService.authEpoch ||
        widget.controller.activeDatabase != current.db ||
        _bindings != current ||
        !widget.appLock.isUnlocked) {
      return; // A -> B -> A, logout, lock and disposal invalidate the result.
    }
    if (proof == null) {
      current.d9Gate = _D9FirstUseGate.unavailable;
    } else if (proof.completed &&
        current.consent.adoptVerifiedD9FirstUseProof(
          proof, activeOwner: owner,
        )) {
      current.d9Gate = _D9FirstUseGate.complete;
    } else if (!proof.completed && proof.ownerUserId == owner) {
      current.d9Gate = _D9FirstUseGate.newPatient;
    } else {
      current.d9Gate = _D9FirstUseGate.unavailable;
    }
    setState(() {});
  }

  void _maybeStartSync() {
    final current = _bindings;
    if (current == null ||
        current.authEpoch != AuthService.authEpoch ||
        !widget.appLock.isUnlocked ||
        !widget.auth.hasRemoteApiCredential ||
        current.scope.nativeDjangoUserId == null) {
      return;
    }
    if (current.syncStarted) {
      // A lock transition may have interrupted an upload or a GET.
      // Resume safely on unlock; never reuse the retired account's sync.
      unawaited(current.sync.resumeAfterUnlock());
      return;
    }
    current.syncStarted = true;
    current.sync.init();
  }

  void _retire(_VaultBindings old) {
    // First remove providers from the widget tree, then dispose stream/router
    // clients after the frame. Auth epoch already stops stale sync egress.
    WidgetsBinding.instance.addPostFrameCallback((_) => old.dispose());
  }

  void _onVaultChanged() {
    if (_bindings != null &&
        widget.controller.activeDatabase == _bindings?.db) return;
    final old = _bindings;
    _bindings = null;
    ++_generation;
    if (old != null) _retire(old);
    if (mounted) setState(() {});
    unawaited(_bindCurrentVault());
  }

  Future<void> _bindCurrentVault() async {
    final db = widget.controller.activeDatabase;
    final scope = widget.controller.activeScope;
    if (db == null || scope == null || !mounted) return;
    if (db == _bindings?.db) return;
    final epoch = AuthService.authEpoch;
    final generation = ++_generation;
    final evidence = ConsentEvidenceStore.forPatientVault(scope);
    bool hasVerifiedEvidence = false;
    try {
      hasVerifiedEvidence = await evidence.hasCurrentEvidence();
    } catch (_) {
      // Evidence failure must never grant AI processing consent.
    }
    if (!mounted || generation != _generation ||
        widget.controller.activeDatabase != db ||
        epoch != AuthService.authEpoch) return;
    try {
      await seedOfflineDemoAuditData(
        db, auditAllowed: widget.auditAllowed, offlineDemo: kOfflineDemo,
      );
      final profile = await db.getProfileForLocalUserId(db.activeProfileRowId);
      if (!mounted || generation != _generation ||
          widget.controller.activeDatabase != db ||
          epoch != AuthService.authEpoch) return;
      final consent = ConsentService(hasVerifiedEvidence: hasVerifiedEvidence)
        ..seedInitialProfile(profile)
        ..attachStream(db.watchProfileForLocalUserId(db.activeProfileRowId));
      final needsD9Proof =
          profile == null && scope.nativeDjangoUserId != null;
      final d9Client = needsD9Proof ? http.Client() : null;
      final d9FirstUse = d9Client == null ? null : D9FirstUseTransport(
        baseUri: Uri.parse(widget.api.baseUrl),
        client: d9Client,
        readBearer: widget.auth.getIdToken,
        hasNativeCredential: () =>
            widget.auth.hasRemoteApiCredential &&
            widget.auth.boundNativeAccountId == scope.nativeDjangoUserId,
        appLockUnlocked: () => widget.appLock.isUnlocked,
        activePatientOwner: () =>
            widget.controller.activeScope?.nativeDjangoUserId,
        authEpoch: () => AuthService.authEpoch,
        vaultGeneration: () => _generation,
      );
      final sync = SyncService(
        db,
        widget.api,
        canUseNetwork: () =>
            mounted &&
            widget.appLock.isUnlocked &&
            widget.auth.hasRemoteApiCredential &&
            widget.controller.activeDatabase == db &&
            AuthService.authEpoch == epoch,
      );
      final router = createAppRouterHolder(
        authService: widget.auth,
        consentService: consent,
        appLockService: widget.appLock,
      );
      final bundle = _VaultBindings(
        db, scope, evidence, consent, sync, router, epoch,
        d9FirstUse: d9FirstUse,
        d9Client: d9Client,
        d9Gate: needsD9Proof
            ? _D9FirstUseGate.unresolved
            : _D9FirstUseGate.notRequired,
      );
      if (!mounted || generation != _generation ||
          widget.controller.activeDatabase != db ||
          epoch != AuthService.authEpoch) {
        bundle.dispose();
        return;
      }
      setState(() => _bindings = bundle);
      _maybeStartSync();
      unawaited(_verifyD9FirstUse());
    } catch (_) {
      // Any inaccessible/migrating vault must stay fail-closed. No legacy
      // fallback or cross-account copy is ever attempted.
    }
  }

  @override
  void dispose() {
    ++_generation;
    widget.controller.removeListener(_onVaultChanged);
    widget.appLock.removeListener(_onLockChanged);
    final b = _bindings;
    if (b != null) b.dispose();
    _guestRouter.dispose();
    unawaited(_guestDatabase.close());
    super.dispose();
  }

  // D9: a remote first-use claim is not a clinical profile or AI consent.
  // Keep patient-facing routes hidden until the current, unlocked native owner
  // has an explicit answer. Unknown != first-use incomplete.
  Widget _buildD9VerificationGate(_VaultBindings bundle) {
    final waiting = bundle.d9Gate == _D9FirstUseGate.unresolved ||
        bundle.d9Gate == _D9FirstUseGate.checking;
    final lang = widget.locale.locale.languageCode;
    final message = waiting
        ? switch (lang) {
            'fr' => 'Vérification sécurisée du compte…',
            'ar' => 'جارٍ التحقق من الحساب بأمان…',
            _ => 'Verifying your account securely…',
          }
        : switch (lang) {
            'fr' => 'Connexion requise pour vérifier votre première utilisation.',
            'ar' => 'يلزم الاتصال للتحقق من إكمال الإعداد الأولي.',
            _ => 'Reconnect to verify your previous setup.',
          };
    return MaterialApp(
      home: Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (waiting)
                const CircularProgressIndicator()
              else
                const Icon(Icons.lock_outline, size: 40),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              if (!waiting) TextButton(
                onPressed: () => unawaited(_verifyD9FirstUse()),
                child: Text(switch (lang) {
                  'fr' => 'Réessayer',
                  'ar' => 'إعادة المحاولة',
                  _ => 'Retry',
                }),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAuditLockPreview() => MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: _guestDatabase),
      ChangeNotifierProvider<AuthService>.value(value: widget.auth),
      ChangeNotifierProvider<AppLockService>.value(value: widget.appLock),
      Provider<ApiClient>.value(value: widget.api),
      ChangeNotifierProvider<LocalePreferenceService>.value(value: widget.locale),
      ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
    ],
    child: AminaApp(router: _guestRouter.router, appLockService: widget.appLock),
  );

  @override
  Widget build(BuildContext context) {
    // Only loopback+compile-time audit visual previews may render an app-lock
    // route before resolving a patient vault. No clinical vault or consent
    // provider is ever exposed in this synthetic preview.
    final auditLockVisual = widget.auditAllowed &&
        widget.auth.isAuditSession &&
        Uri.base.queryParameters['audit'] == 'visual-cert' &&
        Uri.base.fragment.startsWith('/app-lock/');
    if (auditLockVisual) return _buildAuditLockPreview();

    final bundle = _bindings;
    if (bundle != null &&
        widget.controller.activeDatabase == bundle.db &&
        bundle.authEpoch == AuthService.authEpoch) {
      if (widget.appLock.isUnlocked &&
          (bundle.d9Gate == _D9FirstUseGate.unresolved ||
              bundle.d9Gate == _D9FirstUseGate.checking ||
              bundle.d9Gate == _D9FirstUseGate.unavailable)) {
        return _buildD9VerificationGate(bundle);
      }
      return MultiProvider(
        key: ValueKey('d7-patient-vault-${bundle.scope.databaseName}'),
        providers: [
          Provider<AppDatabase>.value(value: bundle.db),
          ChangeNotifierProvider<AuthService>.value(value: widget.auth),
          ChangeNotifierProvider<AppLockService>.value(value: widget.appLock),
          Provider<ApiClient>.value(value: widget.api),
          Provider<SyncService>.value(value: bundle.sync),
          Provider<D9FirstUseTransport?>.value(value: bundle.d9FirstUse),
          Provider<ConsentEvidenceStore>.value(value: bundle.evidence),
          ChangeNotifierProvider<ConsentService>.value(value: bundle.consent),
          ChangeNotifierProvider<LocalePreferenceService>.value(
            value: widget.locale,
          ),
          ChangeNotifierProvider<ModulesProvider>(
            create: (_) => ModulesProvider(widget.api)..refresh(),
          ),
          StreamProvider<PatientProfileData?>(
            create: (_) => bundle.db.watchProfileForLocalUserId(
              bundle.db.activeProfileRowId,
            ),
            initialData: null,
          ),
          ChangeNotifierProvider<TweaksNotifier>(
            create: (_) => TweaksNotifier(),
          ),
        ],
        child: AminaApp(router: bundle.router.router, appLockService: widget.appLock),
      );
    }

    if (!widget.controller.isResolving && !widget.auth.isAuthenticated) {
      return MultiProvider(
        providers: [
          Provider<AppDatabase>.value(value: _guestDatabase),
          ChangeNotifierProvider<AuthService>.value(value: widget.auth),
          ChangeNotifierProvider<AppLockService>.value(value: widget.appLock),
          Provider<ApiClient>.value(value: widget.api),
          ChangeNotifierProvider<LocalePreferenceService>.value(
            value: widget.locale,
          ),
          ChangeNotifierProvider<TweaksNotifier>(
            create: (_) => TweaksNotifier(),
          ),
        ],
        child: AminaApp(router: _guestRouter.router, appLockService: widget.appLock),
      );
    }

    // A verified local patient namespace is unavailable or being switched.
    // Never show the previous patient's screen, even for one new route.
    return MaterialApp(
      home: Scaffold(
        body: Center(
          child: widget.controller.isResolving
              ? const CircularProgressIndicator()
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.lock_outline, size: 40),
                    const SizedBox(height: 12),
                    Text(switch (widget.locale.locale.languageCode) {
                      'fr' => 'Session patient indisponible. Reconnexion requise.',
                      'ar' => 'جلسة المريض غير متاحة. يجب تسجيل الدخول مجددًا.',
                      _ => 'Patient session unavailable. Please sign in again.',
                    }),
                    TextButton(
                      onPressed: () => unawaited(widget.auth.signOut()),
                      child: Text(switch (widget.locale.locale.languageCode) {
                        'fr' => 'Se déconnecter',
                        'ar' => 'تسجيل الخروج',
                        _ => 'Sign out',
                      }),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
