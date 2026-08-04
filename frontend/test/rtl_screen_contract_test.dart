import 'dart:io';

import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

class _RtlScreenEntry {
  const _RtlScreenEntry({
    required this.route,
    required this.widget,
    required this.source,
  });

  final String route;
  final String widget;
  final String source;
}

const _screenRegistry = <_RtlScreenEntry>[
  _RtlScreenEntry(
    route: '/login',
    widget: 'LoginScreen',
    source: 'lib/features/auth/login_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/reset-password',
    widget: 'ResetPasswordScreen',
    source: 'lib/features/auth/reset_password_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/consent',
    widget: 'ConsentScreen',
    source: 'lib/features/auth/consent_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/onboarding',
    widget: 'OnboardingChatScreen',
    source: 'lib/features/auth/onboarding_chat_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/profile',
    widget: 'ProfileScreen',
    source: 'lib/features/profile/profile_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/dashboard',
    widget: 'DashboardScreen',
    source: 'lib/features/dashboard/dashboard_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/summary',
    widget: 'AISummaryScreen',
    source: 'lib/features/journal/ai_summary_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/journal',
    widget: 'JournalScreen',
    source: 'lib/features/journal/journal_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/importer',
    widget: 'ImportScreen',
    source: 'lib/features/import/import_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/ajouter',
    widget: 'AddLogScreen',
    source: 'lib/features/journal/add_log_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/pulper',
    widget: 'DocumentImportScreen',
    source: 'lib/features/documents/document_import_screen.dart',
  ),
  _RtlScreenEntry(
    route: '/journal/:id/edit',
    widget: 'EditLogScreen',
    source: 'lib/features/journal/edit_log_screen.dart',
  ),
  _RtlScreenEntry(
    route: '@shell',
    widget: 'MainShell',
    source: 'lib/features/navigation/main_shell.dart',
  ),
];

final _physicalDirectionPatterns = <MapEntry<String, RegExp>>[
  MapEntry(
    'EdgeInsets.only(left/right)',
    RegExp(r'EdgeInsets\.only\s*\([^)]*\b(?:left|right)\s*:', dotAll: true),
  ),
  MapEntry('EdgeInsets.fromLTRB', RegExp(r'EdgeInsets\.fromLTRB\s*\(')),
  MapEntry(
    'physical Alignment',
    RegExp(
      r'Alignment\.(?:centerLeft|centerRight|topLeft|topRight|bottomLeft|bottomRight)\b',
    ),
  ),
  MapEntry('TextAlign.left/right', RegExp(r'TextAlign\.(?:left|right)\b')),
  MapEntry(
    'Positioned(left/right)',
    RegExp(r'Positioned\s*\([^)]*\b(?:left|right)\s*:', dotAll: true),
  ),
  MapEntry(
    'physical BorderRadius.only corner',
    RegExp(
      r'BorderRadius\.only\s*\([^)]*\b(?:topLeft|topRight|bottomLeft|bottomRight)\s*:',
      dotAll: true,
    ),
  ),
  MapEntry(
    'forced LTR Directionality',
    RegExp(r'Directionality\s*\([^)]*TextDirection\.ltr', dotAll: true),
  ),
];

Set<String> _declaredRoutes() {
  final routeSources = [
    File('lib/routes/app_router.dart').readAsStringSync(),
    File('lib/modules/diabetes_module.dart').readAsStringSync(),
  ].join('\n');
  final routes = RegExp(
    r"(?:path|route):\s*'([^']+)'",
  ).allMatches(routeSources).map((match) => match.group(1)!).toSet();
  routes.remove('/');
  return routes;
}

String _lineFor(String source, int offset) {
  final line = '\n'.allMatches(source.substring(0, offset)).length + 1;
  return line.toString();
}

void main() {
  test(
    'every routed screen is explicitly registered for RTL certification',
    () {
      final registeredRoutes = _screenRegistry
          .where((entry) => entry.route != '@shell')
          .map((entry) => entry.route)
          .toSet();

      expect(registeredRoutes, _declaredRoutes());
      expect(
        _screenRegistry.map((entry) => entry.route).toSet().length,
        _screenRegistry.length,
        reason: 'RTL screen registry contains a duplicate route.',
      );
    },
  );

  test('every registry entry resolves to its declared widget source', () {
    final failures = <String>[];
    for (final entry in _screenRegistry) {
      final file = File(entry.source);
      if (!file.existsSync()) {
        failures.add('${entry.route}: missing ${entry.source}');
        continue;
      }
      final source = file.readAsStringSync();
      if (!RegExp('class\\s+${entry.widget}\\b').hasMatch(source)) {
        failures.add(
          '${entry.route}: ${entry.widget} is not declared in ${entry.source}',
        );
      }
    }
    expect(failures, isEmpty, reason: failures.join('\n'));
  });

  test(
    'registered screens contain no physical left/right layout primitives',
    () {
      final failures = <String>[];
      for (final entry in _screenRegistry) {
        final source = File(entry.source).readAsStringSync();
        for (final rule in _physicalDirectionPatterns) {
          for (final match in rule.value.allMatches(source)) {
            failures.add(
              '${entry.route} ${entry.source}:${_lineFor(source, match.start)} '
              'uses ${rule.key}',
            );
          }
        }
      }
      expect(failures, isEmpty, reason: failures.join('\n'));
    },
  );

  testWidgets('Arabic localization resolves application direction to RTL', (
    tester,
  ) async {
    late TextDirection observedDirection;

    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Builder(
          builder: (context) {
            observedDirection = Directionality.of(context);
            return const Scaffold(body: Text('اختبار اتجاه الواجهة'));
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(observedDirection, TextDirection.rtl);
    expect(find.text('اختبار اتجاه الواجهة'), findsOneWidget);
  });
}
