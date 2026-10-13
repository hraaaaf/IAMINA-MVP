import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

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
import 'locale_preference_service.dart';
import 'modules_provider.dart';
import 'offline_demo_audit_seed.dart';
import 'patient_vault_session_controller.dart';
import 'sync_service.dart';

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
  bool syncStarted = false;

  _VaultBindings(this.db, this.scope, this.evidence, this.consent,
      this.sync, this.router);

  void dispose() {
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

  void _onLockChanged() => _maybeStartSync();

  void _maybeStartSync() {
    final current = _bindings;
    if (current == null ||
        current.syncStarted ||
        !widget.appLock.isUnlocked ||
        !widget.auth.hasRemoteApiCredential ||
        current.scope.nativeDjangoUserId == null) {
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
      final sync = SyncService(db, widget.api);
      final router = createAppRouterHolder(
        authService: widget.auth,
        consentService: consent,
        appLockService: widget.appLock,
      );
      final bundle = _VaultBindings(db, scope, evidence, consent, sync, router);
      if (!mounted || generation != _generation ||
          widget.controller.activeDatabase != db ||
          epoch != AuthService.authEpoch) {
        bundle.dispose();
        return;
      }
      setState(() => _bindings = bundle);
      _maybeStartSync();
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

  @override
  Widget build(BuildContext context) {
    final bundle = _bindings;
    if (bundle != null &&
        widget.controller.activeDatabase == bundle.db &&
        AuthService.authEpoch >= 0) {
      return MultiProvider(
        key: ValueKey('d7-patient-vault-${bundle.scope.databaseName}'),
        providers: [
          Provider<AppDatabase>.value(value: bundle.db),
          ChangeNotifierProvider<AuthService>.value(value: widget.auth),
          ChangeNotifierProvider<AppLockService>.value(value: widget.appLock),
          Provider<ApiClient>.value(value: widget.api),
          Provider<SyncService>.value(value: bundle.sync),
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
                    const Text('Session patient indisponible. Reconnexion requise.'),
                    TextButton(
                      onPressed: () => unawaited(widget.auth.signOut()),
                      child: const Text('Se déconnecter'),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
