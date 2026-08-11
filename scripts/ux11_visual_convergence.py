from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'frontend/lib/features/dashboard/dashboard_convergent_screen.dart'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing {label}: {old!r}')
    return text.replace(old, new, 1)


s = DASH.read_text()

# Match the reference hierarchy: greeting/date share the first line while the
# health-summary subtitle gets the full content width underneath.
old_greeting = '''                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              greeting,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 26,
                                height: 1.05,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.8,
                                color: AminaTheme.textPrimary(context),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              _t(
                                context,
                                "Voici votre résumé santé d'aujourd'hui.",
                                "Here is today's health summary.",
                                'إليك ملخص صحتك اليوم.',
                              ),
                              style: TextStyle(
                                fontSize: 13,
                                color: AminaTheme.textSecondary(context),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      _DatePill(date: anchorDate, onChanged: onDateChanged),
                    ],
                  ),'''
new_greeting = '''                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Expanded(
                            child: Text(
                              greeting,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 26,
                                height: 1.05,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.8,
                                color: AminaTheme.textPrimary(context),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _DatePill(date: anchorDate, onChanged: onDateChanged),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _t(
                          context,
                          "Voici votre résumé santé d'aujourd'hui.",
                          "Here is today's health summary.",
                          'إليك ملخص صحتك اليوم.',
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 13,
                          color: AminaTheme.textSecondary(context),
                        ),
                      ),
                    ],
                  ),'''
s = replace_once(s, old_greeting, new_greeting, 'greeting/date hierarchy')

# Keep the bell visually compact like the mockup but restore a 48 px hit target.
old_bell = '''        Material(
          color: AminaTheme.surface(context),
          shape: const CircleBorder(),
          child: InkWell(
            key: const ValueKey('dashboard-reminders-action'),
            onTap: () => GoRouter.of(context).go('/reminders'),
            customBorder: const CircleBorder(),
            child: const SizedBox(
              width: 40,
              height: 40,
              child: Center(
                child: Icon(
                  Icons.notifications_none_rounded,
                  size: 22,
                  color: Color(0xFF064E52),
                ),
              ),
            ),
          ),
        ),'''
new_bell = '''        SizedBox(
          width: 48,
          height: 48,
          child: Center(
            child: Material(
              color: AminaTheme.surface(context),
              shape: const CircleBorder(),
              child: InkWell(
                key: const ValueKey('dashboard-reminders-action'),
                onTap: () => GoRouter.of(context).go('/reminders'),
                customBorder: const CircleBorder(),
                child: const SizedBox(
                  width: 40,
                  height: 40,
                  child: Center(
                    child: Icon(
                      Icons.notifications_none_rounded,
                      size: 22,
                      color: Color(0xFF064E52),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),'''
s = replace_once(s, old_bell, new_bell, 'accessible reminder hit target')

# The reference separates the three metric columns. Add subtle dividers without
# adding any fabricated metric or clinical claim.
old_metrics = '''              Expanded(
                child: _MetricTile(
                  icon: Icons.trending_up_rounded,
                  label: _t(context, 'Moyenne', 'Average', 'المتوسط'),
                  value: meanDisplay,
                  suffix: unit,
                ),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.timelapse_rounded,
                  label: _t(context, 'Dans la cible', 'In range', 'ضمن النطاق'),
                  value: tir.toStringAsFixed(0),
                  suffix: '%',
                ),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.local_fire_department_outlined,
                  label: 'GMI',
                  value: gmi == null ? '--' : gmi!.toStringAsFixed(1),
                  suffix: gmi == null ? '' : '%',
                ),
              ),'''
new_metrics = '''              Expanded(
                child: _MetricTile(
                  icon: Icons.trending_up_rounded,
                  label: _t(context, 'Moyenne', 'Average', 'المتوسط'),
                  value: meanDisplay,
                  suffix: unit,
                ),
              ),
              Container(
                width: 1,
                height: 58,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                color: AminaTheme.divider(context),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.timelapse_rounded,
                  label: _t(context, 'Dans la cible', 'In range', 'ضمن النطاق'),
                  value: tir.toStringAsFixed(0),
                  suffix: '%',
                ),
              ),
              Container(
                width: 1,
                height: 58,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                color: AminaTheme.divider(context),
              ),
              Expanded(
                child: _MetricTile(
                  icon: Icons.local_fire_department_outlined,
                  label: 'GMI',
                  value: gmi == null ? '--' : gmi!.toStringAsFixed(1),
                  suffix: gmi == null ? '' : '%',
                ),
              ),'''
s = replace_once(s, old_metrics, new_metrics, 'metric separators')

DASH.write_text(s)
