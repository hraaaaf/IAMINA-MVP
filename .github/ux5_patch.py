from pathlib import Path
import re

path = Path('frontend/lib/features/navigation/main_shell.dart')
source = path.read_text()

if "import 'dart:ui';" not in source:
    source = source.replace("import 'package:flutter/material.dart';", "import 'dart:ui';\n\nimport 'package:flutter/material.dart';", 1)

replacement = r'''class _BottomNav extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;

  const _BottomNav({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final rtl = Directionality.of(context) == TextDirection.rtl;
    final safeIndex = selectedIndex.clamp(0, entries.length - 1);
    final visualIndex = rtl ? entries.length - 1 - safeIndex : safeIndex;
    final glassColor = dark
        ? AminaTheme.darkCard.withValues(alpha: 0.78)
        : Colors.white.withValues(alpha: 0.74);
    final glassBorder = dark
        ? Colors.white.withValues(alpha: 0.12)
        : Colors.white.withValues(alpha: 0.88);
    final indicatorColor = dark
        ? AminaTheme.teal700.withValues(alpha: 0.34)
        : AminaTheme.teal50.withValues(alpha: 0.94);

    return SafeArea(
      top: false,
      minimum: const EdgeInsets.fromLTRB(12, 0, 12, 10),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(28),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            height: 72,
            decoration: BoxDecoration(
              color: glassColor,
              borderRadius: BorderRadius.circular(28),
              border: Border.all(color: glassBorder, width: 1),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: dark ? 0.24 : 0.10),
                  blurRadius: 28,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: LayoutBuilder(
              builder: (context, constraints) {
                final itemWidth = constraints.maxWidth / entries.length;
                return Material(
                  color: Colors.transparent,
                  child: Stack(
                    children: [
                      AnimatedPositioned(
                        duration: const Duration(milliseconds: 240),
                        curve: Curves.easeOutCubic,
                        left: visualIndex * itemWidth + 4,
                        top: 8,
                        width: itemWidth - 8,
                        height: 56,
                        child: IgnorePointer(
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: indicatorColor,
                              borderRadius: BorderRadius.circular(22),
                              border: Border.all(
                                color: dark
                                    ? AminaTheme.teal400.withValues(alpha: 0.16)
                                    : AminaTheme.teal500.withValues(alpha: 0.12),
                              ),
                            ),
                          ),
                        ),
                      ),
                      Row(
                        children: [
                          for (var index = 0; index < entries.length; index++)
                            Expanded(
                              child: _GlassNavDestination(
                                entry: entries[index],
                                selected: index == safeIndex,
                                onTap: () {
                                  HapticFeedback.selectionClick();
                                  GoRouter.of(context).go(entries[index].route);
                                },
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

class _GlassNavDestination extends StatelessWidget {
  final _NavEntry entry;
  final bool selected;
  final VoidCallback onTap;

  const _GlassNavDestination({
    required this.entry,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final label = entry.label(AppLocalizations.of(context)!);
    final activeColor = dark ? AminaTheme.teal400 : AminaTheme.teal700;
    final inactiveColor = dark ? AminaTheme.dark400 : AminaTheme.ink400;

    return Semantics(
      button: true,
      selected: selected,
      label: label,
      child: InkWell(
        key: ValueKey('mobile-nav-${entry.route}'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: SizedBox(
          height: 72,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedScale(
                scale: selected ? 1.06 : 1.0,
                duration: const Duration(milliseconds: 240),
                curve: Curves.easeOutCubic,
                child: Icon(
                  selected ? entry.selectedIcon : entry.icon,
                  color: selected ? activeColor : inactiveColor,
                  size: 21,
                ),
              ),
              const SizedBox(height: 4),
              AnimatedDefaultTextStyle(
                duration: const Duration(milliseconds: 240),
                curve: Curves.easeOutCubic,
                style: TextStyle(
                  fontSize: 9.5,
                  height: 1.05,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                  color: selected ? activeColor : inactiveColor,
                  fontFamily: 'Inter',
                ),
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
'''
pattern = re.compile(r'class _BottomNav extends StatelessWidget \{.*\Z', re.S)
updated, count = pattern.subn(replacement, source, count=1)
if count != 1:
    raise SystemExit(f'Expected one _BottomNav block, replaced {count}')
path.write_text(updated)

test = Path('frontend/test/ux_5_glass_mobile_nav_contract_test.dart')
test.write_text(r'''import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('UX-5 mobile shell uses a glass navigation rail with a gliding pill', () {
    final source = File(
      'lib/features/navigation/main_shell.dart',
    ).readAsStringSync();

    expect(source, contains("import 'dart:ui';"));
    expect(source, contains('BackdropFilter('));
    expect(source, contains('ImageFilter.blur(sigmaX: 20, sigmaY: 20)'));
    expect(source, contains('AnimatedPositioned('));
    expect(source, contains('Duration(milliseconds: 240)'));
    expect(source, contains('HapticFeedback.selectionClick()'));
    expect(source, contains("ValueKey('mobile-nav-\${entry.route}')"));
    expect(source, contains('selected: selected'));
    expect(source, contains('label: label'));
    expect(source, contains('GoRouter.of(context).go(entries[index].route)'));
    expect(source, isNot(contains('child: NavigationBar(')));
  });
}
''')
