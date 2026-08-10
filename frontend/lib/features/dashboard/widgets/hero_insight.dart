part of '../dashboard_screen.dart';

// ── Hero Insight (matin / défaut) ─────────────────────────────────────────────

class _HeroInsight extends StatelessWidget {
  final List<LogEntryData> logs;
  final int range;
  const _HeroInsight({required this.logs, required this.range});

  /// Prénom de l'utilisateur connecté, ou chaîne vide pour les comptes anonymes.
  static String _firstName() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null || user.isAnonymous) return '';
    final name = user.displayName ?? user.email ?? '';
    if (name.isEmpty) return '';
    return name
        .split(RegExp(r'[\s@.]'))
        .firstWhere((p) => p.isNotEmpty, orElse: () => '');
  }

  String _headline(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightStart;
    final tir = ClinicalEngine.calcTIR(logs, 70, 180);
    final mean = ClinicalEngine.calcMean(logs);
    if (tir >= 80) return l10n.dashboardInsightStrong(tir.round(), range);
    if (tir >= 60) {
      return l10n.dashboardInsightProgress(tir.round(), mean.round());
    }
    return l10n.dashboardInsightNeedsFocus(range);
  }

  String _subtitle(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    if (logs.isEmpty) return l10n.dashboardInsightFirstMeasurement;
    final cv = ClinicalEngine.calcCV(logs);
    final discoveries = math.min(logs.length ~/ 20 + 1, 5);
    final stability = cv < 36
        ? l10n.dashboardVariabilityStable
        : l10n.dashboardVariabilityWatch;
    return l10n.dashboardInsightSummary(discoveries, stability, logs.length);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AuditedPageCopy.of(context).l10n;
    return ClipRRect(
      borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
      child: Stack(
        children: [
          Positioned.fill(
            child: Container(decoration: AminaTheme.heroCardDecoration()),
          ),
          PositionedDirectional(
            top: -50,
            end: -50,
            child: Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    Colors.white.withValues(alpha: 0.14),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _DotsPainter())),
          PositionedDirectional(
            end: -10,
            bottom: 4,
            child: ShaderMask(
              shaderCallback: (rect) => const LinearGradient(
                colors: [Colors.transparent, Colors.white, Colors.transparent],
                stops: [0.0, 0.5, 1.0],
              ).createShader(rect),
              child: _AnimatedEcg(
                color: Colors.white.withValues(alpha: 0.22),
                width: 260,
                height: 60,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _HeroBadge(label: l10n.dashboardIntelligenceBadge),
                const SizedBox(height: 20),
                Text(
                  _headline(context),
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                    letterSpacing: -0.4,
                    shadows: [
                      Shadow(
                        color: Colors.black.withValues(alpha: 0.2),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  _subtitle(context),
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.78),
                    fontSize: 13,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 20),
                _HeroFilledBtn(
                  label: l10n.dashboardViewDiscoveries,
                  onTap: () => GoRouter.of(context).go('/summary'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
