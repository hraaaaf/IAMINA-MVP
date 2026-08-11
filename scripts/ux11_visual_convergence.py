from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing {label}: {old!r}')
    return text.replace(old, new, 1)


dash_path = FRONTEND / 'lib/features/dashboard/dashboard_convergent_screen.dart'
s = dash_path.read_text()

for old, new, label in [
    ("padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 118),", "padding: const EdgeInsetsDirectional.fromSTEB(18, 8, 18, 96),", 'dashboard outer padding'),
    ("const SizedBox(height: 22),\n                  Row(", "const SizedBox(height: 18),\n                  Row(", 'brand greeting gap'),
    ("const SizedBox(height: 15),\n                  _GlucoseHero(", "const SizedBox(height: 11),\n                  _GlucoseHero(", 'greeting hero gap'),
    ("const SizedBox(height: 14),\n                  _TrendsPanel(", "const SizedBox(height: 10),\n                  _TrendsPanel(", 'hero trends gap'),
    ("const SizedBox(height: 18),\n                  Text(", "const SizedBox(height: 14),\n                  Text(", 'trends actions gap'),
    ("const SizedBox(height: 9),\n                  const _QuickActionsRow(),", "const SizedBox(height: 7),\n                  const _QuickActionsRow(),", 'actions title gap'),
    ("const SizedBox(height: 26),\n                  _DetailedTrendCard(", "const SizedBox(height: 20),\n                  _DetailedTrendCard(", 'actions detail gap'),
    ("width: 46,\n          height: 46,\n          child: CustomPaint(painter: _SealPainter()),", "width: 40,\n          height: 40,\n          child: CustomPaint(painter: _SealPainter()),", 'brand mark size'),
    ("l10n.appTagline,", "_t(context, 'Votre santé, notre mission', 'Your health, our mission', 'صحتك، مهمتنا'),", 'brand tagline'),
    ("padding: const EdgeInsets.fromLTRB(18, 17, 18, 15),", "padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),", 'hero padding'),
    ("width: 38,\n                height: 38,", "width: 34,\n                height: 34,", 'hero icon size'),
    ("const SizedBox(height: 16),", "const SizedBox(height: 8),", 'hero body gap'),
    ("fontSize: 49,", "fontSize: 44,", 'hero number size'),
    ("height: 112,", "height: 80,", 'hero chart height'),
    ("padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),", "padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),", 'hero observation padding'),
    ("padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),", "padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),", 'trends padding'),
    ("const SizedBox(height: 13),", "const SizedBox(height: 8),", 'trends observation gap'),
    ("width: 34,\n            height: 34,", "width: 30,\n            height: 30,", 'metric icon size'),
    ("fontSize: 23,", "fontSize: 20,", 'metric value size'),
    ("width: 48,\n                    height: 48,", "width: 46,\n                    height: 46,", 'quick action icon size'),
    ("fontSize: 8.8,", "fontSize: 8.5,", 'quick action label size'),
]:
    s = replace_once(s, old, new, label)

old_action = """        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            key: const ValueKey('dashboard-import-action'),
            onTap: () => GoRouter.of(context).go('/importer'),
            customBorder: const CircleBorder(),
            child: SizedBox(
              width: 46,
              height: 46,
              child: Icon(
                Icons.upload_file_outlined,
                size: 21,
                color: AminaTheme.textPrimary(context),
              ),
            ),
          ),
        ),"""
new_action = """        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            key: const ValueKey('dashboard-reminders-action'),
            onTap: () => GoRouter.of(context).go('/reminders'),
            customBorder: const CircleBorder(),
            child: SizedBox(
              width: 42,
              height: 42,
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  const Center(
                    child: Icon(
                      Icons.notifications_none_rounded,
                      size: 21,
                      color: Color(0xFF064E52),
                    ),
                  ),
                  PositionedDirectional(
                    top: 7,
                    end: 7,
                    child: Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: Color(0xFF35C78A),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),"""
s = replace_once(s, old_action, new_action, 'header reminders action')

start = s.index('class _SealPainter extends CustomPainter {')
end = s.index('class _ConvergentState extends StatelessWidget {')
seal = '''class _SealPainter extends CustomPainter {
  const _SealPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final teal = Paint()..color = const Color(0xFF075A5D);
    final mint = Paint()..color = const Color(0xFF27B984);
    final c = size.width / 7;
    final blocks = <(int, int, int, int)>[
      (0, 0, 3, 1), (0, 0, 1, 3), (2, 1, 1, 2),
      (4, 0, 3, 1), (6, 0, 1, 3), (4, 2, 2, 1),
      (0, 4, 1, 3), (0, 6, 3, 1), (2, 4, 1, 2),
      (4, 4, 3, 1), (4, 6, 3, 1), (6, 4, 1, 3),
      (1, 3, 2, 1), (3, 1, 1, 2), (3, 4, 1, 2),
      (4, 3, 2, 1), (1, 5, 1, 1), (5, 5, 1, 1),
    ];
    for (final b in blocks) {
      canvas.drawRect(
        Rect.fromLTWH(b.$1 * c, b.$2 * c, b.$3 * c, b.$4 * c),
        teal,
      );
    }
    canvas.drawRect(Rect.fromLTWH(3 * c, 3 * c, c, c), mint);
    canvas.drawRect(Rect.fromLTWH(5 * c, 1 * c, c, c), mint);
    canvas.drawRect(Rect.fromLTWH(1 * c, 4 * c, c, c), mint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

'''
s = s[:start] + seal + s[end:]

brand_start = s.index('class _BrandRow extends StatelessWidget {')
brand_end = s.index('class _RangePill extends StatelessWidget {')
brand = s[brand_start:brand_end].replace(
    '    final l10n = AppLocalizations.of(context)!;\n',
    '',
    1,
)
s = s[:brand_start] + brand + s[brand_end:]
dash_path.write_text(s)

nav_path = FRONTEND / 'lib/features/navigation/main_shell.dart'
s = nav_path.read_text()
for old, new, label in [
    ("minimum: EdgeInsets.symmetric(horizontal: 12).copyWith(bottom: 10),", "minimum: EdgeInsets.symmetric(horizontal: 18).copyWith(bottom: 6),", 'nav safe area'),
    ("height: 92,", "height: 72,", 'nav overall height'),
    ("top: 20,", "top: 12,", 'nav bar top'),
    ("width: 52,", "width: 48,", 'add width'),
    ("height: 52,", "height: 48,", 'add height'),
    ("size: 27,", "size: 28,", 'add icon'),
    ("fontSize: 9.2,", "fontSize: 8.8,", 'nav label size'),
]:
    s = replace_once(s, old, new, label)
nav_path.write_text(s)

module_path = FRONTEND / 'lib/modules/diabetes_module.dart'
s = module_path.read_text()
s = replace_once(
    s,
    'icon: Icons.monitor_heart_outlined,\n      selectedIcon: Icons.monitor_heart_rounded,',
    'icon: Icons.show_chart_rounded,\n      selectedIcon: Icons.show_chart_rounded,',
    'measure nav icon',
)
s = replace_once(
    s,
    'icon: Icons.insert_chart_outlined_rounded,\n      selectedIcon: Icons.insert_chart_rounded,',
    'icon: Icons.description_outlined,\n      selectedIcon: Icons.description_rounded,',
    'report nav icon',
)
module_path.write_text(s)

real_actions = FRONTEND / 'test/p0_real_actions_contract_test.dart'
s = real_actions.read_text()
s = replace_once(
    s,
    "expect(dashboard, contains(\"ValueKey('dashboard-import-action')\"));",
    "expect(dashboard, contains(\"ValueKey('dashboard-reminders-action')\"));",
    'real-actions dashboard control key',
)
s = replace_once(
    s,
    "expect(dashboard, contains(\"GoRouter.of(context).go('/importer')\"));",
    "expect(dashboard, contains(\"GoRouter.of(context).go('/reminders')\"));",
    'real-actions dashboard control route',
)
real_actions.write_text(s)

mobile_import = FRONTEND / 'test/p0_mobile_import_navigation_test.dart'
s = mobile_import.read_text()
old = """      final importerAction = find.byKey(
        const ValueKey('dashboard-import-action'),
      );
      expect(importerAction, findsOneWidget);
      expect(find.byKey(const ValueKey('mobile-nav-/importer')), findsNothing);
      expect(tester.takeException(), isNull);

      await tester.tap(importerAction);
      await tester.pumpAndSettle();
"""
new = """      expect(find.byKey(const ValueKey('mobile-nav-/importer')), findsNothing);
      expect(
        find.byKey(const ValueKey('dashboard-reminders-action')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);

      router.go('/importer');
      await tester.pumpAndSettle();
"""
s = replace_once(s, old, new, 'mobile importer interaction')
s = s.replace(
    "'390px user can navigate to Importer and open the document review flow'",
    "'390px Importer route remains functional outside approved bottom navigation'",
    1,
)
mobile_import.write_text(s)

glass_contract = FRONTEND / 'test/ux_5_glass_mobile_nav_contract_test.dart'
s = glass_contract.read_text()
s = replace_once(
    s,
    "contains('EdgeInsets.symmetric(horizontal: 12).copyWith(bottom: 10)'),",
    "contains('EdgeInsets.symmetric(horizontal: 18).copyWith(bottom: 6)'),",
    'glass nav approved safe-area contract',
)
glass_contract.write_text(s)
