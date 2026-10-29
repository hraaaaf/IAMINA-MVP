// D19 isolated *actual AISummaryScreen* Flutter Web presentation fixture.
// No real patient, no backend request, no credentials, no external AI.
// Not a substitute for backend auth/consent and human clinical approval.
import 'package:amina/data/drift/database.dart';
import 'package:amina/data/models/ai_models.dart';
import 'package:amina/core/theme/app_theme.dart';
import 'package:amina/features/journal/ai_summary_screen.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:amina/services/api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

// The negative/recovery scenario needs locally recorded data so the actual
// analysis screen shows its retry control rather than the first-use panel.
class _D19LocalLogsPresentDatabase extends AppDatabase {
  _D19LocalLogsPresentDatabase() : super.defaults();

  @override
  Future<int> countLogs() async => 1;
}

class _D19SyntheticApi extends ApiClient {
  int _summaryCalls = 0;
  final String scenario;

  _D19SyntheticApi(this.scenario)
      : super(
          baseUrl: 'http://127.0.0.1:1',
          allowClinicalTransportForSyntheticTests: () => false,
        );

  Map<String, dynamic> get _kpis {
    // A 14-day manual glucose diary is descriptive; density is not CGM coverage.
    final verified = scenario == 'verified';
    return {
      'avg_glucose': 130,
      'std_dev': 32,
      'cv_pct': verified ? 17.3 : null,
      'tir_pct': verified ? 84.4 : null,
      'tar_pct': verified ? 12.2 : null,
      'tbr_pct': verified ? 3.4 : null,
      'gmi': null,
      'log_count': 60,
      'days_with_data': 14,
      'has_sufficient_data': true,
      'gmi_confidence': null,
      'gmi_basis': verified
          ? 'Sensor-backed synthetic coverage — GMI not certified'
          : 'No verified CGM sensor session',
    };
  }

  @override
  Future<SummaryResponse?> getAiSummary({int days = 21}) async {
    // Observable in Chrome when the real period control is activated by Tab+Enter.
    print('D19_SYNTHETIC_AI_DAYS=$days');
    _summaryCalls += 1;
    if (scenario == 'unavailable') return null;
    if (scenario == 'recover' && _summaryCalls == 1) return null;
    if (scenario == 'recover') {
      print('D19_SYNTHETIC_AI_RECOVERED_DAYS=$days');
    }
    return SummaryResponse.fromJson({
      'insights': <dynamic>[],
      'kpis': _kpis,
      'daily_averages': [
        {'date': '2026-10-14', 'avg': 130.0, 'count': 4},
        {'date': '2026-10-15', 'avg': 129.0, 'count': 4},
      ],
      // RISK-02 keeps this suppressed until a verified AGP producer exists.
      'agp_profile': <dynamic>[],
      'generated_at': '2026-10-29T10:00:00Z',
      'has_sufficient_data': true,
      'ai_provider': 'fallback',
    });
  }

  @override
  Future<KpisResponse?> getKpis({
    int days = 21,
    double targetLow = 70.0,
    double targetHigh = 180.0,
  }) async {
    return KpisResponse.fromJson(_kpis);
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Fail visibly if the *real* AI Summary throws during a browser render.
  // Release-mode Flutter defaults to a neutral grey ErrorWidget, which could
  // otherwise be mistaken for a loading state in a screenshot-only test.
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    debugPrint('D19_AI_SUMMARY_RENDER_ERROR: ${details.exceptionAsString()}');
    debugPrint('D19_AI_SUMMARY_STACK: ${details.stack}');
  };
  ErrorWidget.builder = (details) => Material(
    color: const Color(0xFFFFE0E0),
    child: Center(
      child: Text('D19 browser fixture failure: ${details.exceptionAsString()}'),
    ),
  );
  final scenario = Uri.base.queryParameters['scenario'] ?? 'manual';
  if (!{'manual', 'verified', 'unavailable', 'recover'}.contains(scenario)) {
    throw ArgumentError.value(scenario, 'scenario', 'Unapproved synthetic scenario');
  }
  final locale = Uri.base.queryParameters['locale'] == 'ar'
      ? const Locale('ar')
      : const Locale('fr');
  final AppDatabase db = scenario == 'recover'
      ? _D19LocalLogsPresentDatabase()
      : AppDatabase.defaults();
  final api = _D19SyntheticApi(scenario);
  runApp(
    MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<ApiClient>.value(value: api),
        ChangeNotifierProvider<TweaksNotifier>(
          create: (_) => TweaksNotifier(),
        ),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AminaTheme.light,
        darkTheme: AminaTheme.dark,
        themeMode: ThemeMode.light,
        locale: locale,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        home: const AISummaryScreen(),
      ),
    ),
  );
}
