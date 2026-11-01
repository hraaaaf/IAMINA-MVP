// D13 synthetic Chromium fixture ONLY. Never included in production entrypoint.
// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:async';
import 'dart:html' as html;
import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';
import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'data/drift/database.dart';
import 'features/journal/add_log_screen.dart';
import 'l10n/app_localizations.dart';

void stage(String v) => html.document.documentElement?.dataset['d13Stage'] = v;

class HoldInsert extends QueryInterceptor {
  final gate = Completer<void>();
  @override
  Future<int> runInsert(QueryExecutor executor, String sql, List<Object?> args) async {
    if (!sql.toLowerCase().contains('log_entries')) {
      return executor.runInsert(sql, args);
    }
    stage('held');
    await gate.future;
    final id = await executor.runInsert(sql, args);
    stage('written');
    return id;
  }
}

class Probe extends StatelessWidget {
  const Probe({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
    body: Center(child: FilledButton(
      onPressed: () => GoRouter.of(c).go('/add'),
      child: const Text('D13_OPEN'),
    )),
  );
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SemanticsBinding.instance.ensureSemantics();
  final lang = Uri.base.queryParameters['lang'] == 'ar' ? 'ar' : 'fr';
  final id = (Uri.base.queryParameters['case'] ?? 'fresh').replaceAll(RegExp('[^a-zA-Z0-9_]'), '_');
  final pause = HoldInsert();
  html.window.addEventListener('d13-release', (_) {
    if (!pause.gate.isCompleted) pause.gate.complete();
  });
  stage('boot');
  try {
    final db = AppDatabase(
      driftDatabase(
        name: 'd13_web_ci_' + id,
        web: DriftWebOptions(
          sqlite3Wasm: Uri.parse('sqlite3.wasm'),
          driftWorker: Uri.parse('drift_worker.js'),
        ),
      ).interceptWith(pause),
    );
    html.document.documentElement?.dataset['d13Count'] = (await db.countLogs()).toString();
    stage('ready');
    final router = GoRouter(routes: [
      GoRoute(path: '/', builder: (_, __) => const Probe()),
      GoRoute(path: '/add', builder: (_, __) => const AddLogScreen()),
      GoRoute(path: '/dashboard', builder: (_, __) => const Scaffold(body: Text('D13_EXIT_OK'))),
    ]);
    runApp(MultiProvider(
      providers: [
        Provider<AppDatabase>.value(value: db),
        Provider<PatientProfileData?>.value(value: null),
      ],
      child: MaterialApp.router(
        locale: Locale(lang),
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        routerConfig: router,
      ),
    ));
  } catch (e, stack) {
    html.document.documentElement?.dataset['d13Error'] = e.toString();
    stage('error');
    debugPrintStack(stackTrace: stack);
  }
}
