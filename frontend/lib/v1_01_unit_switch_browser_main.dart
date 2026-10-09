import 'dart:async';
import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/dashboard/widgets/add_log_sheet.dart';
import 'features/journal/edit_log_screen.dart';
import 'features/profile/profile_screen.dart';
import 'services/auth_service.dart';
import 'services/consent_service.dart';
import 'l10n/app_localizations.dart';

/// Isolated synthetic visual-certification entrypoint, never used by the app.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const _ProofApp());
}

class _ProofApp extends StatefulWidget {
  const _ProofApp();
  @override
  State<_ProofApp> createState() => _ProofAppState();
}

class _ProofAppState extends State<_ProofApp> {
  final _db = AppDatabase.defaults();
  late final String _mode = Uri.base.queryParameters['mode'] ?? 'add';
  bool get _edit => _mode == 'edit';
  bool get _profileMode => _mode == 'profile';
  PatientProfileData? _profile;
  GoRouter? _router;
  bool _switched = false;
  int _attempt = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => unawaited(_seed()));
  }

  Future<void> _seed() async {
    try {
      final recordedAt = DateTime.utc(2026, 9, 20, 10, 30);
      await _db.into(_db.patientProfiles).insert(
        PatientProfilesCompanion.insert(
          userId: const Value(1),
          updatedAt: recordedAt,
          unitPreference: const Value('mmol/L'),
          targetRangeLow: const Value(69.9),
          targetRangeHigh: const Value(180.0),
          diabetesType: const Value('type2'),
          treatment: const Value('lifestyle'),
        ),
      );
      final profile = await _db.select(_db.patientProfiles).getSingle();
      final id = await _db.into(_db.logEntries).insert(
        LogEntriesCompanion.insert(
          createdAt: recordedAt,
          bloodSugar: 69.9,
          loggedAt: Value(recordedAt),
          clientUuid: 'v1-01-chrome-synthetic',
        ),
      );
      if (!mounted) return;
      _router = GoRouter(
        initialLocation: '/',
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => _profileMode
                ? const ProfileScreen()
                : _edit
                    ? EditLogScreen(logId: id)
                    : const AddLogSheet(isPage: true),
          ),
          GoRoute(
            path: '/journal',
            builder: (context, state) =>
                const Scaffold(body: Text('Synthetic journal')),
          ),
        ],
      );
      setState(() => _profile = profile);
      WidgetsBinding.instance.addPostFrameCallback((_) => _profileMode
          ? _signalProfileReady()
          : _changeUnit());
    } catch (error, stackTrace) {
      debugPrint('V101_UNIT_SWITCH_ERROR $error');
      debugPrintStack(stackTrace: stackTrace);
    }
  }

  void _signalProfileReady() {
    if (!mounted) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) debugPrint('V101_UNIT_SWITCH_READY');
    });
  }

  void _changeUnit() {
    if (!mounted || _switched) return;
    if (++_attempt > 90) {
      debugPrint('V101_UNIT_SWITCH_ERROR missing input');
      return;
    }
    final key = Key(_edit ? 'edit-glucose-input' : 'glucose-input');
    TextField? input;
    void walk(Element element) {
      if (input != null) return;
      final widget = element.widget;
      if (widget is TextField && widget.key == key) {
        input = widget;
        return;
      }
      element.visitChildren(walk);
    }
    context.visitChildElements(walk);
    if (input == null || (_edit && input!.controller?.text != '3.9')) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _changeUnit());
      return;
    }
    if (!_edit) {
      input!.controller!.text = '4.0';
      input!.onChanged?.call('4.0');
    }
    _switched = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || _profile == null) return;
      setState(() =>
          _profile = _profile!.copyWith(unitPreference: 'mg/dL'));
      WidgetsBinding.instance.addPostFrameCallback((_) {
        debugPrint('V101_UNIT_SWITCH_READY');
      });
    });
  }

  @override
  void dispose() {
    _router?.dispose();
    unawaited(_db.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profile = _profile;
    final router = _router;
    if (profile == null || router == null) {
      return const MaterialApp(
        home: Scaffold(body: Center(child: CircularProgressIndicator())),
      );
    }
    return MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: _db),
        Provider<PatientProfileData?>.value(value: profile),
        ChangeNotifierProvider<TweaksNotifier>(create: (_) => TweaksNotifier()),
        ChangeNotifierProvider<AuthService>(create: (_) => AuthService()),
        ChangeNotifierProvider<ConsentService>(
          create: (_) => ConsentService()..seedInitialProfile(profile),
        ),
      ],
      child: MaterialApp.router(
        theme: ThemeData.light(),
        locale: const Locale('fr'),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        routerConfig: router,
      ),
    );
  }
}
