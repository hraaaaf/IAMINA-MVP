import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'data/drift/database.dart';
import 'features/dashboard/dashboard_convergent_screen.dart';
import 'l10n/app_localizations.dart';

/// CI-only entrypoint used to render the real Dashboard with the deterministic
/// local Drift demo dataset. No backend, no Firebase auth and no clinical mocks.
void main() {
  final db = AppDatabase.defaults();
  runApp(_DashboardScreenshotBootstrap(db: db));
}

class _DashboardScreenshotBootstrap extends StatefulWidget {
  final AppDatabase db;

  const _DashboardScreenshotBootstrap({required this.db});

  @override
  State<_DashboardScreenshotBootstrap> createState() =>
      _DashboardScreenshotBootstrapState();
}

class _DashboardScreenshotBootstrapState
    extends State<_DashboardScreenshotBootstrap> {
  late final Future<void> _seed = widget.db.seedDemoData();

  @override
  void dispose() {
    widget.db.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _seed,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return MaterialApp(
            debugShowCheckedModeBanner: false,
            home: Scaffold(
              body: Center(child: Text('Dashboard seed failed: ${snapshot.error}')),
            ),
          );
        }
        if (snapshot.connectionState != ConnectionState.done) {
          return const MaterialApp(
            debugShowCheckedModeBanner: false,
            home: Scaffold(body: Center(child: CircularProgressIndicator())),
          );
        }
        return Provider<AppDatabase>.value(
          value: widget.db,
          child: MaterialApp(
            debugShowCheckedModeBanner: false,
            theme: AminaTheme.light,
            locale: const Locale('fr'),
            localizationsDelegates: const [
              AppLocalizations.delegate,
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            supportedLocales: AppLocalizations.supportedLocales,
            home: const DashboardConvergentScreen(),
          ),
        );
      },
    );
  }
}
