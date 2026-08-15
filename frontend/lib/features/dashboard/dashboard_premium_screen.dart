import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';

String _t(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class DashboardPremiumScreen extends StatelessWidget {
  const DashboardPremiumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final db = context.read<AppDatabase>();

    return StreamBuilder<PatientProfileData?>(
      stream: db.watchProfile(),
      builder: (context, profileSnap) {
        final profile = profileSnap.data;
        final unit = profile?.unitPreference ?? 'mg/dL';
        final low = profile?.targetRangeLow ?? 70.0;
        final high = profile?.targetRangeHigh ?? 180.0;

        return StreamBuilder<List<LogEntryData>>(
          stream: db.watchRecentLogs(limit: 1),
          builder: (context, logsSnap) {
            if (profileSnap.hasError || logsSnap.hasError) {
              return _PremiumState(
                icon: Icons.cloud_off_rounded,
                title: _t(context, 'Données indisponibles', 'Data unavailable', 'البيانات غير متاحة'),
                body: _t(
                  context,
                  'IAmina ne peut pas lire vos données locales pour le moment.',
                  'IAmina cannot read your local data right now.',
                  'يتعذر على IAmina قراءة بياناتك المحلية حالياً.',
                ),
              );
            }

            if (profileSnap.connectionState == ConnectionState.waiting ||
                logsSnap.connectionState == ConnectionState.waiting) {
              return _PremiumState(
                loading: true,
                title: _t(context, 'Préparation', 'Preparing', 'جارٍ التحضير'),
                body: _t(
                  context,
                  'IAmina prépare votre espace santé.',
                  'IAmina is preparing your health space.',
                  'تقوم IAmina بإعداد مساحتك الصحية.',
                ),
              );
            }

            final logs = [...?logsSnap.data]
              ..sort((a, b) => (b.loggedAt ?? b.createdAt).compareTo(a.loggedAt ?? a.createdAt));

            return _DashboardBody(
              logs: logs,
              unit: unit,
              low: low,
              high: high,
            );
          },
        );
      },
    );
  }
}

class _DashboardBody extends StatelessWidget {
  final List<LogEntryData> logs;
  final String unit;
  final double low;
  final double high;

  const _DashboardBody({
    required this.logs,
    required this.unit,
    required this.low,
    required this.high,
  });

  String _display(double mg) =>
      unit == 'mmol/L' ? (mg / 18.0).toStringAsFixed(1) : mg.toStringAsFixed(0);

  @override
  Widget build(BuildContext context) {
    final latest = logs.isEmpty ? null : logs.first;
    final latestAt = latest == null ? null : (latest.loggedAt ?? latest.createdAt);
    final inRange = latest != null && latest.bloodSugar >= low && latest.bloodSugar <= high;
    final highValue = latest != null && latest.bloodSugar > high;
    final locale = Localizations.localeOf(context).toLanguageTag();

    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(
            bottom: false,
            child: CustomScrollView(
              physics: const BouncingScrollPhysics(),
              slivers: [
                SliverPadding(
                  padding: const EdgeInsetsDirectional.fromSTEB(20, 16, 20, 128),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([
                      const _PremiumBrandHeader(),
                      const SizedBox(height: 26),
                      Text(
                        _t(context, 'Bonjour', 'Welcome back', 'مرحباً'),
                        style: TextStyle(
                          fontFamily: 'Georgia',
                          fontSize: 31,
                          height: 1.02,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -.8,
                          color: AminaVisualLanguage.primaryText(context),
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        _t(
                          context,
                          'Votre résumé santé, clair et sans bruit.',
                          'Your health summary, clear and focused.',
                          'ملخص صحتك، بوضوح وبدون تشويش.',
                        ),
                        style: TextStyle(
                          fontSize: 14,
                          height: 1.35,
                          color: AminaVisualLanguage.secondary(context),
                        ),
                      ),
                      const SizedBox(height: 22),
                      _LatestReadingCard(
                        latest: latest,
                        latestAt: latestAt,
                        display: latest == null ? '—' : _display(latest.bloodSugar),
                        unit: unit,
                        status: latest == null
                            ? _t(context, 'Aucune mesure', 'No reading yet', 'لا توجد قراءة بعد')
                            : inRange
                            ? _t(context, 'Dans votre cible', 'In your range', 'ضمن نطاقك')
                            : highValue
                            ? _t(context, 'Au-dessus de la cible', 'Above range', 'فوق النطاق')
                            : _t(context, 'Sous la cible', 'Below range', 'تحت النطاق'),
                        inRange: inRange,
                        locale: locale,
                      ),
                      const SizedBox(height: 16),
                      const _QuickActions(),
                      const SizedBox(height: 16),
                      _TrustCard(hasData: logs.isNotEmpty),
                    ]),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PremiumBrandHeader extends StatelessWidget {
  const _PremiumBrandHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 72,
          height: 72,
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: .86),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: .95)),
            boxShadow: AminaVisualLanguage.cardShadowLight,
          ),
          child: Image.asset(
            'assets/images/logo_amina.png',
            fit: BoxFit.contain,
            filterQuality: FilterQuality.high,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'IAmina',
                style: TextStyle(
                  fontSize: 22,
                  height: 1,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -.6,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              const SizedBox(height: 5),
              Text(
                _t(
                  context,
                  'Votre compagnon du diabète',
                  'Your diabetes companion',
                  'رفيقك لمرض السكري',
                ),
                style: TextStyle(
                  fontSize: 12.5,
                  color: AminaVisualLanguage.secondary(context),
                ),
              ),
            ],
          ),
        ),
        IconButton(
          key: const ValueKey('dashboard-reminders-action'),
          onPressed: () => context.go('/reminders'),
          icon: const Icon(Icons.notifications_none_rounded),
          style: IconButton.styleFrom(
            minimumSize: const Size(48, 48),
            backgroundColor: AminaVisualLanguage.controlSurface(context),
            foregroundColor: AminaVisualLanguage.forestDeep,
            side: BorderSide(color: AminaVisualLanguage.controlBorder(context)),
          ),
        ),
      ],
    );
  }
}

class _LatestReadingCard extends StatelessWidget {
  final LogEntryData? latest;
  final DateTime? latestAt;
  final String display;
  final String unit;
  final String status;
  final bool inRange;
  final String locale;

  const _LatestReadingCard({
    required this.latest,
    required this.latestAt,
    required this.display,
    required this.unit,
    required this.status,
    required this.inRange,
    required this.locale,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: AminaVisualLanguage.cardDecoration(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: AminaVisualLanguage.mintIconDecoration(context),
                child: const Icon(
                  Icons.water_drop_outlined,
                  color: AminaVisualLanguage.actionGreen,
                  size: 21,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  _t(context, 'Dernière mesure', 'Latest reading', 'آخر قياس'),
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AminaVisualLanguage.secondary(context),
                  ),
                ),
              ),
              if (latestAt != null)
                Text(
                  DateFormat('HH:mm', locale).format(latestAt!),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AminaVisualLanguage.secondary(context),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 22),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                display,
                style: TextStyle(
                  fontFamily: 'Georgia',
                  fontSize: 52,
                  height: .9,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -1.8,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
              if (latest != null) ...[
                const SizedBox(width: 8),
                Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text(
                    unit,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AminaVisualLanguage.secondary(context),
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: inRange
                  ? AminaVisualLanguage.mintSurface
                  : const Color(0xFFF4F1E8),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              status,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: AminaVisualLanguage.primaryText(context),
              ),
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: AminaVisualLanguage.primaryGradient,
                borderRadius: BorderRadius.circular(AminaVisualLanguage.controlRadius),
                boxShadow: AminaVisualLanguage.controlShadowLight,
              ),
              child: TextButton.icon(
                onPressed: () => context.go('/ajouter'),
                icon: const Icon(Icons.add_rounded, color: Colors.white, size: 20),
                label: Text(
                  _t(context, 'Ajouter une mesure', 'Add a reading', 'إضافة قياس'),
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ActionCard(
            icon: Icons.auto_awesome_rounded,
            label: _t(context, 'Compagnon', 'Companion', 'الرفيق'),
            onTap: () => context.go('/companion'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ActionCard(
            icon: Icons.upload_file_outlined,
            label: _t(context, 'Importer', 'Import', 'استيراد'),
            onTap: () => context.go('/importer'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ActionCard(
            icon: Icons.show_chart_rounded,
            label: _t(context, 'Journal', 'Journal', 'السجل'),
            onTap: () => context.go('/journal'),
          ),
        ),
      ],
    );
  }
}

class _ActionCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionCard({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Ink(
          height: 108,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 13),
          decoration: AminaVisualLanguage.cardDecoration(context, radius: 20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: AminaVisualLanguage.mintIconDecoration(context),
                child: Icon(icon, color: AminaVisualLanguage.actionGreen, size: 20),
              ),
              const SizedBox(height: 9),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w800,
                  color: AminaVisualLanguage.primaryText(context),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TrustCard extends StatelessWidget {
  final bool hasData;
  const _TrustCard({required this.hasData});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: AminaVisualLanguage.cardDecoration(
        context,
        color: AminaVisualLanguage.mintSurface.withValues(alpha: .72),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.shield_outlined, color: AminaVisualLanguage.actionGreen, size: 21),
          const SizedBox(width: 11),
          Expanded(
            child: Text(
              hasData
                  ? _t(
                      context,
                      'Vos données restent interprétées dans des limites cliniques gouvernées. IAmina n’invente pas ce qui manque.',
                      'Your data stays within governed clinical boundaries. IAmina does not invent what is missing.',
                      'تبقى بياناتك ضمن حدود سريرية محكومة. لا تخترع IAmina ما هو مفقود.',
                    )
                  : _t(
                      context,
                      'Ajoutez une première mesure pour commencer. IAmina n’affiche aucune valeur fictive.',
                      'Add your first reading to begin. IAmina never displays fabricated values.',
                      'أضف قياسك الأول للبدء. لا تعرض IAmina قيماً مختلقة.',
                    ),
              style: TextStyle(
                fontSize: 12.5,
                height: 1.45,
                color: AminaVisualLanguage.secondary(context),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AmbientBackground extends StatelessWidget {
  const _AmbientBackground();

  @override
  Widget build(BuildContext context) {
    if (AminaTheme.isDark(context)) return const SizedBox.shrink();
    return IgnorePointer(
      child: Stack(
        children: [
          PositionedDirectional(
            top: -120,
            end: -90,
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AminaVisualLanguage.mintWaveLight.withValues(alpha: .72),
              ),
            ),
          ),
          PositionedDirectional(
            bottom: -150,
            start: -80,
            child: Container(
              width: 330,
              height: 250,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(180),
                color: AminaVisualLanguage.mintWaveStrong.withValues(alpha: .45),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PremiumState extends StatelessWidget {
  final bool loading;
  final IconData? icon;
  final String title;
  final String body;

  const _PremiumState({
    this.loading = false,
    this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AminaTheme.isDark(context)
          ? AminaTheme.bg(context)
          : const Color(0xFFF4FBF9),
      body: Stack(
        children: [
          const Positioned.fill(child: _AmbientBackground()),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                children: [
                  const _PremiumBrandHeader(),
                  const Spacer(),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(26),
                    decoration: AminaVisualLanguage.cardDecoration(context),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (loading)
                          const CircularProgressIndicator()
                        else
                          Container(
                            width: 52,
                            height: 52,
                            decoration: AminaVisualLanguage.mintIconDecoration(context),
                            child: Icon(
                              icon ?? Icons.info_outline_rounded,
                              color: AminaVisualLanguage.actionGreen,
                            ),
                          ),
                        const SizedBox(height: 18),
                        Text(
                          title,
                          style: TextStyle(
                            fontFamily: 'Georgia',
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: AminaVisualLanguage.primaryText(context),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          body,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            height: 1.45,
                            color: AminaVisualLanguage.secondary(context),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(flex: 2),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
