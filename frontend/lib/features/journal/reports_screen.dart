import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import 'ai_summary_screen.dart';

part 'reports_screen_presentation.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    if (kOfflineDemo) return const _OfflineReportsScreen();
    return const AISummaryScreen();
  }
}

class _OfflineReportsScreen extends StatefulWidget {
  const _OfflineReportsScreen();

  @override
  State<_OfflineReportsScreen> createState() => _OfflineReportsScreenState();
}

class _OfflineReportsScreenState extends State<_OfflineReportsScreen> {
  int _days = 21;

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();
    final end = DateTime.now().add(const Duration(minutes: 1));
    final start = end.subtract(Duration(days: _days));

    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: StreamBuilder<PatientProfileData?>(
        stream: db.watchProfile(),
        builder: (context, profileSnapshot) {
          return StreamBuilder<List<LogEntryData>>(
            stream: db.watchLogsInRange(start, end),
            builder: (context, logsSnapshot) {
              if (profileSnapshot.hasError || logsSnapshot.hasError) {
                return _StatePanel(
                  icon: Icons.cloud_off_outlined,
                  title: _t(
                    context,
                    'Rapport local indisponible',
                    'Local report unavailable',
                    'التقرير المحلي غير متاح',
                  ),
                  body: _t(
                    context,
                    'IAmina ne peut pas lire les mesures locales pour le moment.',
                    'IAmina cannot read local measurements right now.',
                    'يتعذر على IAmina قراءة القياسات المحلية حالياً.',
                  ),
                );
              }

              if (logsSnapshot.connectionState == ConnectionState.waiting &&
                  !logsSnapshot.hasData) {
                return _StatePanel(
                  loading: true,
                  title: _t(
                    context,
                    'Préparation du rapport',
                    'Preparing report',
                    'جارٍ إعداد التقرير',
                  ),
                  body: _t(
                    context,
                    'Lecture des mesures enregistrées sur cet appareil.',
                    'Reading measurements stored on this device.',
                    'تتم قراءة القياسات المحفوظة على هذا الجهاز.',
                  ),
                );
              }

              final logs = List<LogEntryData>.from(
                logsSnapshot.data ?? const <LogEntryData>[],
              )..sort((a, b) => _recordedAt(a).compareTo(_recordedAt(b)));

              final stats = _Stats.from(logs, profileSnapshot.data);
              return _ReportView(
                stats: stats,
                days: _days,
                onDaysChanged: (value) => setState(() => _days = value),
              );
            },
          );
        },
      ),
    );
  }

  static DateTime _recordedAt(LogEntryData log) =>
      log.loggedAt ?? log.createdAt;
}
