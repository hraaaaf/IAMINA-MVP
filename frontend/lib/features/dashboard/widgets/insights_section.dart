part of '../dashboard_screen.dart';

// ── Insights Section ──────────────────────────────────────────────────────────

class _InsightsSection extends StatelessWidget {
  final List<LogEntryData> logs;
  final SummaryResponse? summary;
  final bool isLoading;

  const _InsightsSection({
    required this.logs,
    this.summary,
    this.isLoading = false,
  });

  bool get _isDegraded => summary?.isAiDegraded ?? false;

  @override
  Widget build(BuildContext context) {
    if (logs.length < 3) return const SizedBox.shrink();

    // If loading and no summary yet, show skeleton cards (no indefinite spinner)
    if (isLoading && summary == null) {
      return ClinicalCard(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(width: 28, height: 28, decoration: BoxDecoration(color: AminaTheme.ink100, borderRadius: BorderRadius.circular(9))),
            const SizedBox(width: 10),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(width: 140, height: 10, decoration: BoxDecoration(color: AminaTheme.ink100, borderRadius: BorderRadius.circular(4))),
              const SizedBox(height: 5),
              Container(width: 100, height: 9, decoration: BoxDecoration(color: AminaTheme.ink50, borderRadius: BorderRadius.circular(4))),
            ]),
          ]),
          const SizedBox(height: 14),
          ...List.generate(2, (_) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Container(
              height: 68,
              decoration: BoxDecoration(color: AminaTheme.ink50, borderRadius: BorderRadius.circular(AminaTheme.radiusXL)),
            ),
          )),
        ]),
      );
    }

    final insights   = summary?.insights ?? [];
    final discoveries = summary?.insights.length ?? 0;

    return ClinicalCard(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(padding: const EdgeInsets.all(7), decoration: BoxDecoration(color: AminaTheme.teal50, borderRadius: BorderRadius.circular(9)),
            child: const Icon(Icons.auto_awesome, size: 14, color: AminaTheme.teal600)),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('DÉCOUVERTES IAMINA', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AminaTheme.ink500, letterSpacing: 0.6)),
            Text(
      discoveries == 0
          ? 'En attente de données…'
          : discoveries == 1
              ? '1 découverte'
              : '$discoveries découvertes',
      style: TextStyle(fontSize: 12, color: AminaTheme.textSecondary(context)),
    ),
          ])),
          if (isLoading)
            const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
          else
            GestureDetector(
              onTap: () => GoRouter.of(context).go('/summary'),
              child: const Text('Voir tout →', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal600)),
            ),
        ]),
        const SizedBox(height: 14),

        // ── Degraded AI mode banner ────────────────────────────────
        if (_isDegraded) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF3E0),   // orange 50
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFFFCC80)), // orange 200
            ),
            child: const Row(children: [
              Icon(Icons.cloud_off_outlined, size: 14, color: Color(0xFFE65100)),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Analyse IA temporairement limitée · Les données sont bien enregistrées.',
                  style: TextStyle(fontSize: 11, color: Color(0xFF5D2E00), height: 1.4),
                ),
              ),
            ]),
          ),
          const SizedBox(height: 10),
        ],

        if (insights.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            width: double.infinity,
            decoration: BoxDecoration(
              color: AminaTheme.subtleBg(context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AminaTheme.divider(context)),
            ),
            child: Row(children: [
              const Icon(Icons.hourglass_top_rounded, size: 16, color: AminaTheme.teal400),
              const SizedBox(width: 10),
              Expanded(child: Text(
                'IAmina analyse tes données pour identifier des schémas…',
                style: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context), fontStyle: FontStyle.italic),
              )),
            ]),
          )
        else
          Builder(builder: (ctx) {
            final isWide = MediaQuery.of(ctx).size.width >= 900;
            final items = insights.take(isWide ? 4 : 2).toList();
            Widget insightCard(dynamic insight) => Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AminaTheme.teal50,
                borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                border: Border.all(color: AminaTheme.teal100),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Text(insight.icon, style: const TextStyle(fontSize: 18)),
                    const SizedBox(width: 8),
                    Expanded(child: Text(insight.title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AminaTheme.teal800))),
                  ]),
                  const SizedBox(height: 8),
                  Text(insight.body, style: const TextStyle(fontSize: 13, color: AminaTheme.teal700, height: 1.5)),
                  if (insight.action.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text('💡 ${insight.action}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal600)),
                  ],
                ],
              ),
            );
            if (isWide && items.length > 1) {
              return Column(children: [
                for (int i = 0; i < items.length; i += 2)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Expanded(child: insightCard(items[i])),
                      if (i + 1 < items.length) ...[
                        const SizedBox(width: 10),
                        Expanded(child: insightCard(items[i + 1])),
                      ] else
                        const Spacer(),
                    ]),
                  ),
              ]);
            }
            return Column(children: items.map((insight) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: insightCard(insight),
            )).toList());
          }),
      ]),
    );
  }
}
