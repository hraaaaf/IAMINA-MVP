from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


# Dashboard — compact first-use layout for 360x560.
p = Path('frontend/lib/features/dashboard/dashboard_screen.dart')
s = p.read_text()
s = replace_once(
    s,
    "  Widget build(BuildContext context) {\n    return Padding(\n      padding: const EdgeInsets.only(top: 40, bottom: 32),\n      child: Column(children: [\n        // Illustration\n        Container(\n          width: 96, height: 96,",
    "  Widget build(BuildContext context) {\n    final compactHeight = MediaQuery.sizeOf(context).height <= 600;\n    return Padding(\n      padding: EdgeInsets.only(\n        top: compactHeight ? 12 : 40,\n        bottom: compactHeight ? 16 : 32,\n      ),\n      child: Column(children: [\n        // Illustration\n        Container(\n          width: compactHeight ? 68 : 96,\n          height: compactHeight ? 68 : 96,",
    'dashboard compact shell',
)
s = replace_once(
    s,
    "          child: const Center(child: Text('🩺', style: TextStyle(fontSize: 44))),\n        ),\n        const SizedBox(height: 28),",
    "          child: Center(\n            child: Text('🩺', style: TextStyle(fontSize: compactHeight ? 32 : 44)),\n          ),\n        ),\n        SizedBox(height: compactHeight ? 16 : 28),",
    'dashboard compact illustration',
)
s = replace_once(
    s,
    "          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AminaTheme.ink900, letterSpacing: -0.4),",
    "          style: TextStyle(fontSize: compactHeight ? 20 : 22, fontWeight: FontWeight.w800, color: AminaTheme.ink900, letterSpacing: -0.4),",
    'dashboard compact title',
)
s = replace_once(
    s,
    "        const SizedBox(height: 10),\n        Padding(\n          padding: const EdgeInsets.symmetric(horizontal: 32),",
    "        SizedBox(height: compactHeight ? 6 : 10),\n        Padding(\n          padding: EdgeInsets.symmetric(horizontal: compactHeight ? 16 : 32),",
    'dashboard compact body',
)
s = replace_once(s, "        const SizedBox(height: 36),\n\n        // CTAs", "        SizedBox(height: compactHeight ? 18 : 36),\n\n        // CTAs", 'dashboard CTA gap')
s = replace_once(s, "                  padding: const EdgeInsets.symmetric(vertical: 16),", "                  padding: EdgeInsets.symmetric(vertical: compactHeight ? 13 : 16),", 'dashboard primary CTA')
s = replace_once(s, "                  padding: const EdgeInsets.symmetric(vertical: 15),", "                  padding: EdgeInsets.symmetric(vertical: compactHeight ? 12 : 15),", 'dashboard secondary CTA')
s = replace_once(s, "        const SizedBox(height: 32),\n        Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: [", "        SizedBox(height: compactHeight ? 18 : 32),\n        Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: [", 'dashboard feature gap')
p.write_text(s)


# IAmina Summary — remove duplicate FAB, localize mobile header and loaded-state greeting,
# and turn the technical error state into a deliberate product card.
p = Path('frontend/lib/features/journal/ai_summary_screen.dart')
s = p.read_text()
s = replace_once(s, "import '../../l10n/app_localizations.dart';\n", "import '../../l10n/app_localizations.dart';\nimport '../../l10n/audited_page_copy.dart';\n", 'summary audited copy import')
s = replace_once(s, "      // Floating chat button (bottom right)\n      floatingActionButton: _ChatFab(onTap: _openChat),\n", "", 'summary duplicate FAB')

pattern = re.compile(r"  Widget _buildError\(\) \{.*?\n  \}\n\n  Widget _buildContent\(\) \{", re.S)
replacement = '''  Widget _buildError() {
    final l10n = AppLocalizations.of(context)!;
    return Align(
      alignment: Alignment.topCenter,
      child: Padding(
        padding: const EdgeInsetsDirectional.fromSTEB(20, 32, 20, 24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AminaTheme.surface(context),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AminaTheme.divider(context)),
              boxShadow: AminaTheme.shadowClinical,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: AminaTheme.dangerBg,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(
                    Icons.cloud_off_outlined,
                    color: AminaTheme.dangerFg,
                    size: 24,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  l10n.analysisLoadError,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                    height: 1.35,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _fetchData,
                    icon: const Icon(Icons.refresh, size: 17),
                    label: Text(l10n.retry),
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit(f'summary error card: expected 1 block, found {n}')

marker = 'class _SummaryTopBar extends StatelessWidget {'
idx = s.index(marker)
before, topbar = s[:idx], s[idx:]
topbar = replace_once(
    topbar,
    "  Widget build(BuildContext context) {\n    return Container(",
    "  Widget build(BuildContext context) {\n    final l10n = AppLocalizations.of(context)!;\n    final isCompact = MediaQuery.sizeOf(context).width < 600;\n    return Container(",
    'summary topbar locals',
)
rich = re.compile(r"              Expanded\(\n                child: RichText\(.*?\n              \),\n              Row\(", re.S)
rich_replacement = '''              Expanded(
                child: Text(
                  isCompact ? l10n.navIamina : l10n.breadcrumb,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: isCompact ? 15 : 13,
                    fontWeight: isCompact ? FontWeight.w800 : FontWeight.w600,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
              ),
              Row('''
topbar, n = rich.subn(rich_replacement, topbar, count=1)
if n != 1:
    raise SystemExit(f'summary breadcrumb: expected 1 block, found {n}')
topbar = replace_once(topbar, "label: '7j',", "label: '7 ${l10n.dayShort}',", 'summary 7-day chip')
topbar = replace_once(topbar, "label: '21j',", "label: '21 ${l10n.dayShort}',", 'summary 21-day chip')
topbar = replace_once(topbar, "label: '90j',", "label: '90 ${l10n.dayShort}',", 'summary 90-day chip')
s = before + topbar

marker = 'class _GreetingHeader extends StatelessWidget {'
idx = s.index(marker)
before, greeting = s[:idx], s[idx:]
greeting = replace_once(greeting, "    final name = _firstName();\n    return Column(", "    final copy = AuditedPageCopy.of(context);\n    final name = _firstName();\n    final hour = DateTime.now().hour;\n    return Column(", 'summary greeting locals')
greeting = replace_once(greeting, "          name.isNotEmpty ? 'Bonjour, $name.' : 'Bonjour !',", "          copy.greeting(hour, name),", 'summary localized greeting')
greeting = replace_once(greeting, "          'Voici ce qu\\'IAmina a observé sur vos $periodDays derniers jours.',", "          copy.observation(periodDays),", 'summary localized observation')
s = before + greeting
p.write_text(s)


# Arabic compact day label: avoid cramped 7ي/21ي/90ي chips while preserving ARB authority.
p = Path('frontend/lib/l10n/app_ar.arb')
s = p.read_text()
s = replace_once(s, '  "dayShort": "ي",', '  "dayShort": "يوم",', 'Arabic day short label')
p.write_text(s)
p = Path('frontend/lib/l10n/app_localizations_ar.dart')
s = p.read_text()
s = replace_once(s, "  String get dayShort => 'ي';", "  String get dayShort => 'يوم';", 'generated Arabic day short label')
p.write_text(s)


# Profile — quieter IAmina card and non-duplicated completion percentage.
p = Path('frontend/lib/features/profile/profile_screen.dart')
s = p.read_text()
s = replace_once(s, '          boxShadow: AminaTheme.shadowCardLG,', '          boxShadow: AminaTheme.shadowCard,', 'profile IAmina card shadow')
s = replace_once(s, '    final label = copy.profileCompletionLabel(pct);', "    final label = pct >= 100 ? copy.profileComplete : AppLocalizations.of(context)!.profile;", 'profile completion label')
p.write_text(s)


# Permanent contract extension.
p = Path('frontend/test/p0_ux_9_small_screen_contract_test.dart')
s = p.read_text()
s = replace_once(
    s,
    "    expect(source, contains('emptyDashboardBody'));\n",
    "    expect(source, contains('emptyDashboardBody'));\n    expect(source, contains('compactHeight = MediaQuery.sizeOf(context).height <= 600'));\n",
    'P0-UX-9 dashboard compact contract',
)
s = replace_once(
    s,
    "    expect(source, contains('.retry'));\n",
    "    expect(source, contains('.retry'));\n    expect(source, contains('isCompact ? l10n.navIamina : l10n.breadcrumb'));\n    expect(source, isNot(contains('floatingActionButton: _ChatFab')));\n    expect(source, contains('copy.greeting(hour, name)'));\n    expect(source, contains('copy.observation(periodDays)'));\n",
    'P0-UX-9 Summary visual contract',
)
s = replace_once(
    s,
    "    final ar = _read('lib/l10n/app_ar.arb');\n",
    "    final ar = _read('lib/l10n/app_ar.arb');\n    expect(ar, contains('\\\"dayShort\\\": \\\"يوم\\\"'));\n",
    'P0-UX-9 Arabic chip contract',
)
p.write_text(s)
