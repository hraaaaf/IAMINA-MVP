from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing {label}: {old!r}')
    return text.replace(old, new, 1)


dash_path = FRONTEND / 'lib/features/dashboard/dashboard_convergent_screen.dart'
s = dash_path.read_text()

# Make the mockup's calendar control truthful: it selects the dashboard anchor date.
s = replace_once(
    s,
    "class _DashboardConvergentScreenState extends State<DashboardConvergentScreen> {\n  int _range = 21;",
    "class _DashboardConvergentScreenState extends State<DashboardConvergentScreen> {\n  final int _range = 21;\n  DateTime _anchorDate = DateTime.now();",
    'dashboard anchor date state',
)
s = replace_once(
    s,
    "    final now = DateTime.now();\n    final start = now.subtract(Duration(days: _range));",
    "    final now = DateTime(\n      _anchorDate.year,\n      _anchorDate.month,\n      _anchorDate.day,\n      23,\n      59,\n      59,\n    );\n    final start = now.subtract(Duration(days: _range));",
    'dashboard anchored query window',
)
s = replace_once(
    s,
    "              range: _range,\n              onRangeChanged: (value) => setState(() => _range = value),",
    "              range: _range,\n              anchorDate: _anchorDate,\n              onDateChanged: (value) => setState(() => _anchorDate = value),",
    'dashboard populated date wiring',
)
s = replace_once(
    s,
    "  final int range;\n  final ValueChanged<int> onRangeChanged;",
    "  final int range;\n  final DateTime anchorDate;\n  final ValueChanged<DateTime> onDateChanged;",
    'dashboard date fields',
)
s = replace_once(
    s,
    "    required this.range,\n    required this.onRangeChanged,",
    "    required this.range,\n    required this.anchorDate,\n    required this.onDateChanged,",
    'dashboard date constructor',
)
s = replace_once(
    s,
    "                      _RangePill(range: range, onChanged: onRangeChanged),",
    "                      _DatePill(date: anchorDate, onChanged: onDateChanged),",
    'dashboard date pill call',
)

old_range = '''class _RangePill extends StatelessWidget {
  final int range;
  final ValueChanged<int> onChanged;
  const _RangePill({required this.range, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<int>(
      onSelected: onChanged,
      itemBuilder: (_) => [
        7,
        21,
        90,
      ].map((v) => PopupMenuItem<int>(value: v, child: Text('$v j'))).toList(),
      child: Container(
        height: 40,
        padding: const EdgeInsetsDirectional.fromSTEB(12, 0, 10, 0),
        decoration: BoxDecoration(
          color: AminaTheme.surface(context),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.calendar_today_outlined,
              size: 14,
              color: AminaTheme.textSecondary(context),
            ),
            const SizedBox(width: 7),
            Text(
              '$range j',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(width: 3),
            Icon(
              Icons.keyboard_arrow_down_rounded,
              size: 16,
              color: AminaTheme.textSecondary(context),
            ),
          ],
        ),
      ),
    );
  }
}
'''
new_date = '''class _DatePill extends StatelessWidget {
  final DateTime date;
  final ValueChanged<DateTime> onChanged;

  const _DatePill({required this.date, required this.onChanged});

  Future<void> _pick(BuildContext context) async {
    final today = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: date.isAfter(today) ? today : date,
      firstDate: DateTime(2020),
      lastDate: today,
    );
    if (picked != null) onChanged(picked);
  }

  @override
  Widget build(BuildContext context) {
    final locale = Localizations.localeOf(context).toLanguageTag();
    final label = DateFormat('d MMM yyyy', locale).format(date);
    return InkWell(
      onTap: () => _pick(context),
      borderRadius: BorderRadius.circular(22),
      child: Container(
        height: 40,
        padding: const EdgeInsetsDirectional.fromSTEB(13, 0, 10, 0),
        decoration: BoxDecoration(
          color: AminaTheme.surface(context),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AminaTheme.divider(context)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.calendar_today_outlined,
              size: 15,
              color: AminaTheme.textSecondary(context),
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(width: 5),
            Icon(
              Icons.keyboard_arrow_down_rounded,
              size: 17,
              color: AminaTheme.textSecondary(context),
            ),
          ],
        ),
      ),
    );
  }
}
'''
s = replace_once(s, old_range, new_date, 'truthful date picker')

# Width-normalized comparison to the approved mockup: trim hero/trends by ~60 px.
for old, new, label in [
    ("padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 100),", "padding: const EdgeInsetsDirectional.fromSTEB(18, 10, 18, 112),", 'dashboard outer bottom room'),
    ("fontSize: 27,\n                                height: 1.05,", "fontSize: 26,\n                                height: 1.05,", 'greeting size'),
    ("width: 46,\n          height: 46,\n          child: CustomPaint(painter: _SealPainter()),", "width: 40,\n          height: 40,\n          child: CustomPaint(painter: _SealPainter()),", 'brand mark size'),
    ("fontSize: 28,\n                  height: 1,", "fontSize: 25,\n                  height: 1,", 'brand name size'),
    ("fontSize: 12,\n                  fontWeight: FontWeight.w600,", "fontSize: 10.8,\n                  fontWeight: FontWeight.w600,", 'brand tagline size'),
    ("width: 46,\n              height: 46,", "width: 40,\n              height: 40,", 'header bell size'),
    ("size: 24,\n                  color: Color(0xFF064E52),", "size: 22,\n                  color: Color(0xFF064E52),", 'header bell icon size'),
    ("padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),", "padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),", 'hero padding'),
    ("width: 36,\n                height: 36,", "width: 34,\n                height: 34,", 'hero icon size'),
    ("const SizedBox(height: 10),\n          Row(", "const SizedBox(height: 6),\n          Row(", 'hero body gap'),
    ("height: 92,", "height: 76,", 'hero chart height'),
    ("const SizedBox(height: 14),\n          InkWell(", "const SizedBox(height: 10),\n          InkWell(", 'hero observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),", "padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),", 'hero observation padding'),
    ("const SizedBox(height: 11),\n                  _TrendsPanel(", "const SizedBox(height: 9),\n                  _TrendsPanel(", 'hero trends gap'),
    ("padding: const EdgeInsets.fromLTRB(15, 11, 15, 11),", "padding: const EdgeInsets.fromLTRB(15, 8, 15, 8),", 'trends padding'),
    ("width: 32,\n            height: 32,", "width: 28,\n            height: 28,", 'metric icon size'),
    ("const SizedBox(height: 7),", "const SizedBox(height: 5),", 'metric icon label gap'),
    ("fontSize: 22,\n                      fontWeight: FontWeight.w800,", "fontSize: 21,\n                      fontWeight: FontWeight.w800,", 'metric value size'),
    ("const SizedBox(height: 9),\n          InkWell(", "const SizedBox(height: 6),\n          InkWell(", 'trends observation gap'),
    ("padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),", "padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),", 'trends observation padding'),
    ("width: 36,\n                    height: 36,", "width: 32,\n                    height: 32,", 'trends observation icon size'),
    ("const SizedBox(height: 14),\n                  Text(", "const SizedBox(height: 10),\n                  Text(", 'trends actions gap'),
    ("width: 54,\n                    height: 54,", "width: 50,\n                    height: 50,", 'quick action tile size'),
    ("size: 20,\n                      color: const Color(0xFF064E52),", "size: 21,\n                      color: const Color(0xFF064E52),", 'quick action icon size'),
    ("fontSize: 8.5,\n                      fontWeight: FontWeight.w600,", "fontSize: 9.3,\n                      fontWeight: FontWeight.w600,", 'quick action label size'),
    ("const SizedBox(height: 20),\n                  _DetailedTrendCard(", "const SizedBox(height: 48),\n                  _DetailedTrendCard(", 'hide detailed trend below first viewport'),
]:
    s = replace_once(s, old, new, label)

dash_path.write_text(s)

nav_path = FRONTEND / 'lib/features/navigation/main_shell.dart'
s = nav_path.read_text()
for old, new, label in [
    ("        : Colors.white.withValues(alpha: 0.92);", "        : Colors.white.withValues(alpha: 0.98);", 'nav glass opacity'),
    ("        : Colors.white.withValues(alpha: 0.92);\n    final indicatorColor", "        : const Color(0xFFE8E5DF);\n    final indicatorColor", 'nav light border'),
    ("    final indicatorColor = dark\n        ? AminaTheme.teal700.withValues(alpha: 0.34)\n        : AminaTheme.teal50.withValues(alpha: 0.96);", "    final indicatorColor = Colors.transparent;", 'nav indicator fill'),
    ("borderRadius: BorderRadius.circular(28),", "borderRadius: BorderRadius.circular(22),", 'nav outer radius 1'),
    ("borderRadius: BorderRadius.circular(28),", "borderRadius: BorderRadius.circular(22),", 'nav outer radius 2'),
    ("                                        color: dark\n                                            ? AminaTheme.teal400.withValues(\n                                                alpha: 0.16,\n                                              )\n                                            : AminaTheme.teal500.withValues(\n                                                alpha: 0.12,\n                                              ),", "                                        color: Colors.transparent,", 'nav selected border'),
    ("width: 52,\n                    height: 52,", "width: 46,\n                    height: 46,", 'center add size'),
    ("width: 5,", "width: 4,", 'center add border'),
    ("size: 29,", "size: 27,", 'center add icon'),
]:
    s = replace_once(s, old, new, label)
nav_path.write_text(s)
