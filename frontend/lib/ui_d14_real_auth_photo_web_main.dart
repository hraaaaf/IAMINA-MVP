// D14 CI-only real native Django authentication, owner-scoped Web vault and
// real MealCapturePanel. Photo recognition is an in-memory synthetic Future.
// This entrypoint is NEVER imported by lib/main.dart.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:async';
import 'dart:convert';

import 'package:amina/core/theme/amina_visual_language.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/features/journal/widgets/meal_capture_panel.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:amina/services/auth_service.dart';
import 'package:amina/services/meal_food_favorites_repository.dart';
import 'package:amina/services/patient_vault_session_controller.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

const _accountA = String.fromEnvironment('D14_CI_A');
const _accountB = String.fromEnvironment('D14_CI_B');
const _password = String.fromEnvironment('D14_CI_PASS');

void ensure(bool condition, String label) {
  if (!condition) throw StateError('D14 real-auth: $label');
}

class _EmptyFavorites implements MealFoodFavoritesRepository {
  @override
  Future<Set<String>> load() async => <String>{};
  @override
  Future<void> save(Set<String> ids) async {}
}

class _OwnerPhotoSurface extends StatefulWidget {
  final AppDatabase db;
  final ApiClient api;
  final bool fixtureEnabled;
  final Future<MealAnalysisResult?> Function() recognition;

  const _OwnerPhotoSurface({
    super.key,
    required this.db,
    required this.api,
    required this.fixtureEnabled,
    required this.recognition,
  });

  @override
  State<_OwnerPhotoSurface> createState() => _OwnerPhotoSurfaceState();
}

class _OwnerPhotoSurfaceState extends State<_OwnerPhotoSurface> {
  List<String> selected = <String>[];
  final _favorites = _EmptyFavorites();

  bool get hasProposal {
    var found = false;
    void visit(Element element) {
      if (element.widget.key == const Key('meal-photo-proposal')) {
        found = true;
      }
      element.visitChildren(visit);
    }
    context.visitChildElements(visit);
    return found;
  }

  void pressPhoto() {
    OutlinedButton? button;
    void visit(Element element) {
      final widget = element.widget;
      if (widget is OutlinedButton &&
          widget.key == const Key('meal-photo-button')) {
        button = widget;
      }
      element.visitChildren(visit);
    }
    context.visitChildElements(visit);
    ensure(button?.onPressed != null, 'photo button absent');
    button!.onPressed!.call();
  }

  @override
  Widget build(BuildContext context) => MultiProvider(
    providers: [
      Provider<AppDatabase>.value(value: widget.db),
      Provider<ApiClient>.value(value: widget.api),
    ],
    child: Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 820),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  const Text('D14 real Django auth / image: synthetic only'),
                  MealCapturePanel(
                    selectedIds: selected,
                    onChanged: (items) => setState(() => selected = items),
                    canUsePhotoRecognition: widget.fixtureEnabled,
                    photoRecognition: widget.recognition,
                    favoritesRepository: _favorites,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

class _D14RealAuthApp extends StatefulWidget {
  const _D14RealAuthApp();
  @override
  State<_D14RealAuthApp> createState() => _D14RealAuthAppState();
}

class _D14RealAuthAppState extends State<_D14RealAuthApp> {
  final _auth = AuthService();
  final _panelKey = GlobalKey<_OwnerPhotoSurfaceState>();
  PatientVaultSessionController? _controller;
  ApiClient? _api;
  AppDatabase? _db;
  bool _photoFixtureEnabled = false;
  int? _activeOwner;
  final _steps = <String>[];
  Completer<MealAnalysisResult?>? _oldA;
  int _photoCalls = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => unawaited(_run()));
  }

  Future<void> _frame() async {
    await WidgetsBinding.instance.endOfFrame;
    await Future<void>.delayed(const Duration(milliseconds: 120));
  }

  Future<MealAnalysisResult?> _syntheticPhoto() {
    _photoCalls++;
    return (_oldA ??= Completer<MealAnalysisResult?>()).future;
  }

  Future<int> _signIn(String email, {required bool enabled}) async {
    await _auth.signInWithEmail(email, _password);
    ensure(_auth.hasRemoteApiCredential, 'no native bearer');
    ensure(_auth.isRemoteCredentialVerified, 'native bearer not verified');
    await _controller!.reconcile();
    final user = _auth.boundNativeAccountId;
    final db = _controller!.activeDatabase;
    ensure(user != null && user > 0, 'native owner ID missing');
    ensure(db != null && db.activeProfileRowId == user, 'owner-vault mismatch');
    ensure(_controller!.activeScope?.nativeDjangoUserId == user,
        'wrong physical owner scope');
    setState(() {
      _activeOwner = user;
      _db = db;
      _photoFixtureEnabled = enabled;
    });
    await _frame();
    return user!;
  }

  Future<void> _unmountPanel() async {
    setState(() {
      _db = null;
      _activeOwner = null;
      _photoFixtureEnabled = false;
    });
    await _frame();
  }

  Future<void> _run() async {
    try {
      ensure(_accountA.isNotEmpty && _accountB.isNotEmpty &&
          _accountA != _accountB && _password.isNotEmpty,
          'synthetic login fixture missing');
      await _auth.initialize();
      _controller = PatientVaultSessionController.forAuth(_auth);
      await _controller!.reconcile();
      ensure(_controller!.activeDatabase == null, 'unexpected patient vault');
      _api = ApiClient(
        authService: _auth,
        canUsePatientSyncTransport: () => false,
      );
      ensure(!_api!.canSyncClinicalData,
          'clinical upload transport must stay local-only');
      _oldA = Completer<MealAnalysisResult?>();

      final a = await _signIn(_accountA, enabled: true);
      _panelKey.currentState!.pressPhoto();
      await _frame();
      ensure(_photoCalls == 1, 'A synthetic photo not invoked');
      ensure(!_panelKey.currentState!.hasProposal, 'A proposal before reply');
      ensure(_panelKey.currentState!.selected.isEmpty, 'A auto selection');
      _steps.add('A_REAL_LOGIN_AND_PENDING_SYNTHETIC_PHOTO');

      // Dispose the old photo panel BEFORE AuthService switches owner.
      await _unmountPanel();
      final b = await _signIn(_accountB, enabled: false);
      ensure(a != b, 'accounts A and B not isolated');
      _panelKey.currentState!.pressPhoto();
      await _frame();
      ensure(_photoCalls == 1, 'B OFF invoked photo recognizer');
      ensure(!_panelKey.currentState!.hasProposal, 'B inherited A proposal');
      ensure(_panelKey.currentState!.selected.isEmpty, 'B inherited selection');
      _steps.add('B_REAL_LOGIN_PHOTO_DENIED');

      _oldA!.complete(const MealAnalysisResult(
        foods: <String>['œuf'], confidence: 'high', fallback: false));
      await _frame();
      ensure(!_panelKey.currentState!.hasProposal,
          'A late response appeared in B');
      ensure(_panelKey.currentState!.selected.isEmpty,
          'A late response selected B meal');
      _steps.add('A_LATE_RESULT_NOT_VISIBLE_IN_B');

      await _unmountPanel();
      await _auth.signOut();
      await _controller!.reconcile();
      ensure(_controller!.activeScope == null &&
          _controller!.activeDatabase == null, 'logout retained owner');
      _steps.add('LOGOUT_VAULT_CLOSED');

      final aAgain = await _signIn(_accountA, enabled: false);
      ensure(aAgain == a, 'returned A identity differs');
      _panelKey.currentState!.pressPhoto();
      await _frame();
      ensure(_photoCalls == 1, 'A return OFF invoked recognizer');
      ensure(!_panelKey.currentState!.hasProposal, 'old proposal resurrected');
      ensure(_panelKey.currentState!.selected.isEmpty,
          'old selection resurrected');
      _steps.add('A_REAL_RETURN_OFF_AND_CLEAN');

      ensure(!_api!.canSyncClinicalData, 'clinical API unexpectedly enabled');
      html.document.title = 'IAMINA_D14_REAL_AUTH_PASS';
      html.window.postMessage(jsonEncode(<String, Object?>{
        'kind': 'IAMINA_D14_REAL_AUTH_REPORT',
        'status': 'PASS',
        'steps': _steps,
        'ownerA': 'synthetic',
        'ownerB': 'synthetic',
        'photoCalls': _photoCalls,
        'providerCalls': 0,
        'realDjangoAuth': true,
        'realPatientVault': true,
        'photo': 'synthetic_future_only',
        'clinicalTransport': 'disabled',
      }), '*');
    } catch (error) {
      html.document.title = 'IAMINA_D14_REAL_AUTH_FAIL:' +
          error.runtimeType.toString();
      html.window.postMessage(jsonEncode(<String, Object?>{
        'kind': 'IAMINA_D14_REAL_AUTH_REPORT',
        'status': 'FAIL',
        'reason': error.toString().replaceAll(RegExp(r'[^a-zA-Z0-9 _:-]'), ' '),
        'steps': _steps,
      }), '*');
    }
  }

  @override
  void dispose() {
    if (_oldA != null && !_oldA!.isCompleted) {
      _oldA!.complete(null);
    }
    _controller?.dispose();
    _auth.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final db = _db;
    final owner = _activeOwner;
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      // Match the patient Web theme and its bundled Inter/Noto font fallbacks.
      theme: AminaVisualLanguage.harmonize(AminaTheme.light),
      darkTheme: AminaVisualLanguage.harmonize(AminaTheme.dark),
      themeMode: ThemeMode.light,
      locale: Uri.base.queryParameters['locale'] == 'ar'
          ? const Locale('ar') : const Locale('fr'),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: db == null || owner == null || _api == null
          ? const Scaffold(body: Center(child: Text('D14 auth fixture loading')))
          : _OwnerPhotoSurface(
              key: _panelKey,
              db: db,
              api: _api!,
              fixtureEnabled: _photoFixtureEnabled,
              recognition: _syntheticPhoto,
            ),
    );
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  html.document.title = 'IAMINA_D14_REAL_AUTH_PENDING';
  runApp(const _D14RealAuthApp());
}
