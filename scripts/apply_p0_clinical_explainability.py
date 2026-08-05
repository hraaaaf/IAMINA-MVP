#!/usr/bin/env python3
"""Apply the scoped P0 clinical-explainability patch.

The patch is deliberately assertion-heavy: every replacement must match exactly
once so a future source drift cannot silently leave fabricated confidence or
threshold-derived trends in the patient UI.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "frontend/lib/features/journal/ai_summary_screen.dart"


def replace_once(old: str, new: str) -> None:
    source = SUMMARY.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"expected one exact match, found {count}: {old[:80]!r}")
    SUMMARY.write_text(source.replace(old, new), encoding="utf-8")


def regex_once(pattern: str, replacement: str) -> None:
    source = SUMMARY.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"expected one regex match, found {count}: {pattern[:80]!r}")
    SUMMARY.write_text(updated, encoding="utf-8")


def main() -> None:
    regex_once(
        r"""          Text\(\n            tir >= 70.*?\n            style: const TextStyle\(""",
        """          Text(\n            tir >= 70\n                ? 'Une majorité des mesures disponibles\\nse situe dans le repère 70–180 mg/dL.'\n                : 'Certaines mesures disponibles\\nméritent d’être examinées.',\n            style: const TextStyle(""",
    )

    new_kpi_section = r'''class _KpiRow extends StatelessWidget {
  final KpisResponse kpis;
  const _KpiRow({required this.kpis});

  @override
  Widget build(BuildContext context) {
    final tir = kpis.tirPct ?? 0.0;
    final gmi = kpis.gmi ?? 0.0;
    final cv = kpis.cvPct ?? 0.0;
    final coverage =
        '${kpis.logCount} mesures sur ${kpis.daysWithData} jour${kpis.daysWithData > 1 ? 's' : ''}';

    final cards = <Widget>[
      _KpiCard(
        label: 'MESURES DANS LA CIBLE',
        value: '${tir.toStringAsFixed(0)}%',
        color: AminaTheme.teal500,
        reference: 'Repère général 70–180 mg/dL',
      ),
      _KpiCard(
        label: 'GMI ESTIMÉE',
        value: '${gmi.toStringAsFixed(1)}%',
        color: AminaTheme.ocean500,
        reference: kpis.gmiBasis.isNotEmpty
            ? '${kpis.gmiBasis} · estimation, pas HbA1c laboratoire'
            : 'Moyenne disponible · estimation, pas HbA1c laboratoire',
      ),
      _KpiCard(
        label: 'VARIABILITÉ (CV)',
        value: '${cv.toStringAsFixed(0)}%',
        color: AminaTheme.ambre500,
        reference: 'Repère général <36 %',
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            if (constraints.maxWidth < 720) {
              return Column(
                children: [
                  for (var index = 0; index < cards.length; index++) ...[
                    cards[index],
                    if (index < cards.length - 1) const SizedBox(height: 12),
                  ],
                ],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var index = 0; index < cards.length; index++) ...[
                  Expanded(child: cards[index]),
                  if (index < cards.length - 1) const SizedBox(width: 12),
                ],
              ],
            );
          },
        ),
        const SizedBox(height: 10),
        Text(
          'Repères généraux non personnalisés · $coverage. Les données manquantes peuvent modifier l’interprétation.',
          style: TextStyle(
            fontSize: 10.5,
            color: AminaTheme.textSecondary(context),
            height: 1.4,
          ),
        ),
      ],
    );
  }
}

class _KpiCard extends StatelessWidget {
  final String label, value, reference;
  final Color color;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.color,
    required this.reference,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsetsDirectional.fromSTEB(20, 22, 20, 20),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: AminaTheme.textSecondary(context),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: TextStyle(
              fontSize: 42,
              fontWeight: FontWeight.w800,
              color: AminaTheme.textPrimary(context),
              letterSpacing: -1.5,
              height: 1.0,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            width: 28,
            height: 3,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(99),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            reference,
            style: TextStyle(
              fontSize: 10.5,
              color: AminaTheme.textSecondary(context),
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }
}
'''

    regex_once(
        r"""class _KpiRow extends StatelessWidget \{.*?\nclass _KpiCard extends StatelessWidget \{.*?\n\}\n\n// ─────────────────────────────────────────────────────────────────────────────\n// AGP Card""",
        new_kpi_section
        + "\n// ─────────────────────────────────────────────────────────────────────────────\n// AGP Card",
    )

    replace_once(
        """                            const SizedBox(width: 8),\n                            _SignalBars(color: barColor),\n                            const SizedBox(width: 6),\n                            Text(\n                              'conf. ${_confidenceForSeverity(card.severity)}%',\n                              style: TextStyle(\n                                fontSize: 10,\n                                color: AminaTheme.textSecondary(context),\n                              ),\n                            ),""",
        """                            const SizedBox(width: 8),\n                            Text(\n                              'Observation automatique',\n                              style: TextStyle(\n                                fontSize: 10,\n                                color: AminaTheme.textSecondary(context),\n                              ),\n                            ),""",
    )

    regex_once(
        r"""\n  int _confidenceForSeverity\(InsightSeverity s\) => switch \(s\) \{.*?\n  \};""",
        "",
    )

    regex_once(
        r"""\nclass _SignalBars extends StatelessWidget \{.*?\n\}\n\nclass _PulseAnimation""",
        "\nclass _PulseAnimation",
    )

    replace_once("'Cible 70–180'", "'Repère général 70–180'")
    replace_once(
        "'Posez vos questions ou demandez des conseils personnalisés.'",
        "'Posez vos questions ou demandez une explication des données disponibles.'",
    )

    source = SUMMARY.read_text(encoding="utf-8")
    forbidden = (
        "_confidenceForSeverity",
        "conf. ",
        "class _SignalBars",
        "Icons.arrow_upward",
        "Icons.arrow_downward",
        "confidenceBadge",
        "required this.trend",
    )
    leftovers = [token for token in forbidden if token in source]
    if leftovers:
        raise RuntimeError("forbidden explainability leftovers: " + ", ".join(leftovers))

    print("P0 clinical-explainability patch applied.")


if __name__ == "__main__":
    main()
