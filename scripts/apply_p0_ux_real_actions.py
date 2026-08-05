#!/usr/bin/env python3
"""Apply the scoped P0 product-truthfulness real-actions patch.

Temporary migration helper. It fails when the expected source no longer matches,
so it cannot silently produce a partial UX fix.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "frontend/lib/features/journal/ai_summary_screen.dart"
IMPORT = ROOT / "frontend/lib/features/import/import_screen.dart"


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one exact match, found {count}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def regex_once(path: Path, pattern: str, replacement: str) -> None:
    source = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{path}: expected one regex match, found {count}")
    path.write_text(updated, encoding="utf-8")


def patch_summary() -> None:
    replace_once(
        SUMMARY,
        """                  child: SingleChildScrollView(\n                    child: Column(children: [\n                      _HeroInsightCard(summary: summary, kpis: kpis, onDiscoverTap: () {}, onChatTap: _openChat),""",
        """                  child: SingleChildScrollView(\n                    controller: _scrollController,\n                    child: Column(children: [\n                      _HeroInsightCard(summary: summary, kpis: kpis, onDiscoverTap: _scrollToInsights, onChatTap: _openChat),""",
    )
    replace_once(
        SUMMARY,
        """              const SizedBox(width: 12),\n              const Icon(Icons.notifications_none, size: 20),""",
        """              const SizedBox(width: 4),""",
    )
    replace_once(
        SUMMARY,
        """            '${summary.insightCards.length} découvertes prioritaires, ${summary.insightCards.where((c) => c.action.isNotEmpty).length} recommandations à valider. Basé sur ${kpis?.logCount ?? 0} mesures continues.',""",
        """            '${summary.insightCards.length} observations prioritaires, ${summary.insightCards.where((c) => c.action.isNotEmpty).length} pistes à discuter. Basé sur ${kpis?.logCount ?? 0} mesures disponibles.',""",
    )
    replace_once(
        SUMMARY,
        """            const _PlanItem(day: 'J+1', title: 'Diviser la dose repas glucidique', sub: 'Fractionner bolus avant et après le repas', bg: AminaTheme.warnBg, dot: Color(0xFFF59E0B)),\n            const _PlanItem(day: 'J+3', title: 'Basale nocturne −15 %',            sub: 'Les soirs avec activité sportive',         bg: AminaTheme.dangerBg, dot: Color(0xFFDC2626)),\n            const _PlanItem(day: 'J+7', title: 'Bilan TIR de la semaine',          sub: 'Comparer avec la semaine N−1',             bg: AminaTheme.goodBg, dot: AminaTheme.teal500),""",
        """            const _PlanItem(day: 'J+1', title: 'Documenter les repas glucidiques', sub: 'Ajouter le contexte et les horaires du repas', bg: AminaTheme.warnBg, dot: Color(0xFFF59E0B)),\n            const _PlanItem(day: 'J+3', title: 'Documenter les valeurs nocturnes', sub: 'Noter activité, sommeil et symptômes associés', bg: AminaTheme.dangerBg, dot: Color(0xFFDC2626)),\n            const _PlanItem(day: 'J+7', title: 'Préparer le bilan TIR', sub: 'Comparer les périodes avec votre professionnel', bg: AminaTheme.goodBg, dot: AminaTheme.teal500),""",
    )
    replace_once(SUMMARY, "Text('PLAN D\\'ACTION'", "Text('POINTS À DISCUTER'")
    replace_once(
        SUMMARY,
        """Text('$count ajustement${count > 1 ? 's' : ''} · 7 prochains jours'""",
        """Text('$count point${count > 1 ? 's' : ''} à examiner sur 7 jours'""",
    )
    replace_once(
        SUMMARY,
        """Text('Partager au médecin', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AminaTheme.textSecondary(context)))""",
        """Text('À discuter avec le médecin', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AminaTheme.textSecondary(context)))""",
    )
    replace_once(
        SUMMARY,
        """              Icon(Icons.chevron_right, size: 18, color: AminaTheme.textSecondary(context)),""",
        """              Icon(Icons.info_outline, size: 17, color: AminaTheme.textSecondary(context)),""",
    )
    replace_once(
        SUMMARY,
        """                    Expanded(child: Text('Recommandation : ${card.action}',\n                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal700, height: 1.4))),""",
        """                    Expanded(child: Text('Piste à discuter : ${card.action}',\n                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.teal700, height: 1.4))),""",
    )
    replace_once(
        SUMMARY,
        """  bool _expanded = true;\n  bool _accepted = false;\n  bool _ignored  = false;""",
        """  bool _expanded = true;""",
    )
    regex_once(
        SUMMARY,
        r"""              Row\(children: \[\n                _ActionBtn\(.*?\n                GestureDetector\(\n                  onTap: \(\) => widget\.onAskWhy\(\),\n                  child: const Text\('Pourquoi \?',.*?\n                \),\n              \]\),""",
        """              Align(\n                alignment: AlignmentDirectional.centerEnd,\n                child: TextButton.icon(\n                  onPressed: widget.onAskWhy,\n                  icon: const Icon(Icons.help_outline, size: 14),\n                  label: const Text('Demander pourquoi'),\n                  style: TextButton.styleFrom(\n                    foregroundColor: AminaTheme.teal600,\n                  ),\n                ),\n              ),""",
    )
    regex_once(
        SUMMARY,
        r"""\nclass _ActionBtn extends StatelessWidget \{.*?\n\}\n\n// ─────────────────────────────────────────────────────────────────────────────\n// Chat CTA card \+ Chat FAB animé""",
        """\n// ─────────────────────────────────────────────────────────────────────────────\n// Chat CTA card + Chat FAB animé""",
    )


def patch_import() -> None:
    regex_once(
        IMPORT,
        r"""\n  void _showComingSoon\(String name\) \{.*?\n  \}\n""",
        "\n",
    )
    replace_once(
        IMPORT,
        """                    subtitle: 'Connexion directe via Dexcom CLARITY. Synchronisation automatique toutes les 5 minutes.',""",
        """                    subtitle: 'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.',""",
    )
    replace_once(
        IMPORT,
        """                    action: OutlinedButton(\n                      onPressed: () => _showComingSoon('Dexcom G6/G7'),\n                      style: OutlinedButton.styleFrom(\n                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),\n                        minimumSize: Size.zero,\n                        side: const BorderSide(color: AminaTheme.ink200),\n                      ),\n                      child: const Text('Notifiez-moi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),\n                    ),""",
        """                    action: const _UnavailableAction(),""",
    )
    replace_once(
        IMPORT,
        """                    subtitle: 'Import des données LibreView via CSV ou connexion API.',""",
        """                    subtitle: 'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.',""",
    )
    replace_once(
        IMPORT,
        """                    action: OutlinedButton(\n                      onPressed: () => _showComingSoon('Abbott LibreLink'),\n                      style: OutlinedButton.styleFrom(\n                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),\n                        minimumSize: Size.zero,\n                        side: const BorderSide(color: AminaTheme.ink200),\n                      ),\n                      child: const Text('Notifiez-moi', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.ink400)),\n                    ),""",
        """                    action: const _UnavailableAction(),""",
    )
    replace_once(
        IMPORT,
        """class _ImportOption extends StatelessWidget {""",
        """class _UnavailableAction extends StatelessWidget {\n  const _UnavailableAction();\n\n  @override\n  Widget build(BuildContext context) => Container(\n    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),\n    decoration: BoxDecoration(\n      color: AminaTheme.ink50,\n      borderRadius: BorderRadius.circular(10),\n      border: Border.all(color: AminaTheme.ink200),\n    ),\n    child: const Text(\n      'Non disponible',\n      style: TextStyle(\n        fontSize: 12,\n        fontWeight: FontWeight.w600,\n        color: AminaTheme.ink500,\n      ),\n    ),\n  );\n}\n\nclass _ImportOption extends StatelessWidget {""",
    )


def main() -> None:
    patch_summary()
    patch_import()
    print("P0 UX real-actions patch applied.")


if __name__ == "__main__":
    main()
