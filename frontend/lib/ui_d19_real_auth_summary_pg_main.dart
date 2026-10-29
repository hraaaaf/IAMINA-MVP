// D19 CI only: Actual Flutter AuthService/native Django login + ApiClient,
// PostgreSQL-backed medical data and the real AISummaryScreen on Web.
// Disposable synthetic accounts, no real patient, no external model requests.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/features/journal/ai_summary_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

const ciA = String.fromEnvironment('D19_CI_A');
const ciB = String.fromEnvironment('D19_CI_B');
const ciPassword = String.fromEnvironment('D19_CI_PASS');
const ciApiBase = String.fromEnvironment('API_BASE_URL');

void requireTrue(bool condition, String reason) {
  if (!condition) throw StateError(reason);
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  var flutterRenderError = false;
  FlutterError.onError = (details) {
    flutterRenderError = true;
    FlutterError.presentError(details);
    html.document.title = 'IAMINA_D19_REAL_HTTP_FAIL:flutter_render';
  };
  final screenKey = GlobalKey();
  html.document.title = 'IAMINA_D19_REAL_HTTP_PENDING';
  final principal = Uri.base.queryParameters['principal'] ?? '';
  final language = Uri.base.queryParameters['locale'] ?? 'fr';
  if (!kIsWeb || !ciApiBase.startsWith('http://127.0.0.1:') ||
      !{'a', 'b'}.contains(principal) || !{'fr', 'ar'}.contains(language) ||
      ciPassword.length < 30 || ciA.isEmpty || ciB.isEmpty || ciA == ciB) {
    html.document.title = 'IAMINA_D19_REAL_HTTP_FAIL:bad_fixture';
    return;
  }
  var stage = 'auth_initialize';
  try {
    final auth = AuthService();
    await auth.initialize();
    stage = 'native_login';
    await auth.signInWithEmail(principal == 'a' ? ciA : ciB, ciPassword);
    requireTrue(auth.isRemoteCredentialVerified && auth.hasRemoteApiCredential,
        'not_native_authenticated');
    stage = 'vault_reconcile';
    final vault = PatientVaultSessionController.forAuth(auth);
    await vault.reconcile();
    requireTrue(vault.activeDatabase != null && vault.activeScope != null,
        'no_verified_patient_vault');
    requireTrue(vault.activeScope!.nativeDjangoUserId == auth.boundNativeAccountId,
        'cross_patient_vault');

    // D11: explicit real logout / other-account login / logout / return
    // within each synthetic B browser scene. Reusing 3 B scenes per locale
    // adds only six logins: 15 total per isolated job (IP cap 20, A cap 10).
    // The real anti-abuse thresholds are not disabled or changed.
    if (principal == 'b') {
      stage = 'logout_switch';
      final ownerB = auth.boundNativeAccountId;
      await auth.signOut();
      requireTrue(!auth.isAuthenticated && !auth.hasRemoteApiCredential &&
          auth.boundNativeAccountId == null &&
          await auth.resolvePatientVaultScope() == null,
          'logout_kept_patient_vault');
      await auth.signInWithEmail(ciA, ciPassword);
      requireTrue(auth.isRemoteCredentialVerified &&
          auth.boundNativeAccountId != null &&
          auth.boundNativeAccountId != ownerB &&
          (await auth.resolvePatientVaultScope())!.nativeDjangoUserId ==
              auth.boundNativeAccountId,
          'stale_owner_after_switch_to_a');
      await auth.signOut();
      requireTrue(!auth.isAuthenticated && !auth.hasRemoteApiCredential &&
          auth.boundNativeAccountId == null,
          'logout_a_kept_credential');
      await auth.signInWithEmail(ciB, ciPassword);
      requireTrue(auth.isRemoteCredentialVerified &&
          auth.boundNativeAccountId == ownerB,
          'stale_owner_after_return_to_b');
      await vault.reconcile();
      requireTrue(vault.activeDatabase != null &&
          vault.activeScope!.nativeDjangoUserId == ownerB,
          'vault_not_restored_to_b');
    }

    final api = ApiClient(
      baseUrl: ciApiBase,
      authService: auth,
      // CI-only explicit permission: production defaults remain local-only.
      allowClinicalTransportForSyntheticTests: () => true,
      canUsePatientSyncTransport: () => true,
    );
    stage = 'clinical_http';
    final summary = await api.getAiSummary(days: 21);
    final kpis = await api.getKpis(days: 21);
    if (summary == null || kpis == null) {
      throw StateError('http_summary_unavailable');
    }
    final expected = principal == 'a' ? 95.0 : 210.0;
    final got = (summary.kpis['avg_glucose'] as num?)?.toDouble();
    requireTrue(got == expected && kpis.avgGlucose == expected,
        'owner_kpi_mismatch');
    requireTrue(kpis.logCount >= 6 && summary.kpis['log_count'] == kpis.logCount,
        'owner_log_count_mismatch');
    requireTrue(kpis.tirPct == null && kpis.cvPct == null && kpis.gmi == null &&
        summary.kpis['tir_pct'] == null && summary.kpis['gmi'] == null,
        'non_sensor_cgm_promoted');
    requireTrue(summary.agpProfile.isEmpty, 'unverified_agp');
    stage = 'widget_render';
    runApp(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: vault.activeDatabase!),
        Provider<ApiClient>.value(value: api),
        Provider<PatientVaultSessionController>.value(value: vault),
        ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AminaTheme.light,
        darkTheme: AminaTheme.dark,
        themeMode: ThemeMode.light,
        locale: Locale(language),
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: AISummaryScreen(key: screenKey),
      ),
    ));
    // A successful HTTP assertion is not a rendered clinical screen.
    // Fail closed unless the actual Flutter widget has painted a sized frame.
    stage = 'frame_paint';
    await WidgetsBinding.instance.endOfFrame;
    await Future<void>.delayed(const Duration(milliseconds: 900));
    await WidgetsBinding.instance.endOfFrame;
    final rendered = screenKey.currentContext?.findRenderObject();
    requireTrue(!flutterRenderError && rendered is RenderBox &&
        rendered.attached && rendered.hasSize &&
        rendered.size.width >= 300 && rendered.size.height >= 600,
        'clinical_screen_not_rendered');
    html.document.title = 'IAMINA_D19_REAL_HTTP_' +
        principal.toUpperCase() + '_PASS';
  } catch (error) {
    // Do not expose account identities or credentials to browser/title/logs.
    html.document.title =
        'IAMINA_D19_REAL_HTTP_FAIL:' + stage + ':' + error.runtimeType.toString();
  }
}
