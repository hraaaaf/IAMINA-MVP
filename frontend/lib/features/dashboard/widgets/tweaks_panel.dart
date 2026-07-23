import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';

/// Tweaks panel — slide-in panel (right side) with:
///   Direction : Clinique / Éditorial / Dense
///   Thème     : Clair / Sombre
///   Densité   : Confort / Compact
///   Accent    : Teal / Océan / Ambre
///
/// Usage: wrap your Scaffold body in a Stack and overlay this widget,
/// controlled by a bool _showTweaks in parent state.
///
/// Example:
///   Stack(children: [
///     _mainContent,
///     if (_showTweaks)
///       Positioned(top: 0, right: 0, bottom: 0, child: TweaksPanel(onClose: () => setState(() => _showTweaks = false))),
///   ])

class TweaksPanel extends StatelessWidget {
  final VoidCallback onClose;

  const TweaksPanel({super.key, required this.onClose});

  @override
  Widget build(BuildContext context) {
    final tweaks = context.watch<TweaksNotifier>();
    final isDark  = tweaks.isDark;

    final bg     = isDark ? AminaTheme.darkCard       : AminaTheme.cardBg;
    final border = isDark ? AminaTheme.dark600         : AminaTheme.ink100;
    final muted  = isDark ? AminaTheme.dark400         : AminaTheme.ink500;

    return GestureDetector(
      onTap: onClose, // tap outside panel closes it
      behavior: HitTestBehavior.opaque,
      child: Align(
        alignment: Alignment.centerRight,
        child: GestureDetector(
          onTap: () {}, // absorb taps inside panel
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOutCubic,
            width: 260,
            decoration: BoxDecoration(
              color: bg,
              border: Border(left: BorderSide(color: border)),
              boxShadow: isDark ? AminaTheme.shadowDark : AminaTheme.shadowClinicalLg,
            ),
            child: SafeArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 20, 12, 16),
                    child: Row(
                      children: [
                        Text('TWEAKS', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: muted, letterSpacing: 0.1)),
                        const Spacer(),
                        IconButton(
                          onPressed: onClose,
                          icon: Icon(Icons.close, size: 18, color: muted),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                        ),
                      ],
                    ),
                  ),
                  Divider(color: border, height: 1),
                  Expanded(
                    child: ListView(
                      padding: const EdgeInsets.all(20),
                      children: [
                        // Direction
                        _SectionLabel(label: 'Direction', isDark: isDark),
                        const SizedBox(height: 10),
                        _SegmentGroup<TweaksDirection>(
                          options: const [
                            (TweaksDirection.clinique,  'Clinique'),
                            (TweaksDirection.editorial, 'Éditorial'),
                            (TweaksDirection.dense,     'Dense'),
                          ],
                          selected: tweaks.direction,
                          onSelect: tweaks.setDirection,
                          isDark: isDark,
                          accent: tweaks.primaryColor,
                        ),
                        const SizedBox(height: 24),

                        // Thème
                        _SectionLabel(label: 'Thème', isDark: isDark),
                        const SizedBox(height: 10),
                        _SegmentGroup<bool>(
                          options: const [
                            (false, 'Clair'),
                            (true,  'Sombre'),
                          ],
                          selected: tweaks.isDark,
                          onSelect: tweaks.setDark,
                          isDark: isDark,
                          accent: tweaks.primaryColor,
                        ),
                        const SizedBox(height: 24),

                        // Densité
                        _SectionLabel(label: 'Densité', isDark: isDark),
                        const SizedBox(height: 10),
                        _SegmentGroup<TweaksDensity>(
                          options: const [
                            (TweaksDensity.confort,  'Confort'),
                            (TweaksDensity.compact,  'Compact'),
                          ],
                          selected: tweaks.density,
                          onSelect: tweaks.setDensity,
                          isDark: isDark,
                          accent: tweaks.primaryColor,
                        ),
                        const SizedBox(height: 24),

                        // Accent
                        _SectionLabel(label: 'Accent', isDark: isDark),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            _AccentDot(
                              color: AminaTheme.teal500,
                              label: 'Teal',
                              selected: tweaks.accent == TweaksAccent.teal,
                              onTap: () => tweaks.setAccent(TweaksAccent.teal),
                              isDark: isDark,
                            ),
                            const SizedBox(width: 10),
                            _AccentDot(
                              color: AminaTheme.ocean500,
                              label: 'Océan',
                              selected: tweaks.accent == TweaksAccent.ocean,
                              onTap: () => tweaks.setAccent(TweaksAccent.ocean),
                              isDark: isDark,
                            ),
                            const SizedBox(width: 10),
                            _AccentDot(
                              color: AminaTheme.ambre500,
                              label: 'Ambre',
                              selected: tweaks.accent == TweaksAccent.ambre,
                              onTap: () => tweaks.setAccent(TweaksAccent.ambre),
                              isDark: isDark,
                            ),
                          ],
                        ),
                        const SizedBox(height: 32),

                        // Info
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: tweaks.primaryColor.withValues(alpha: isDark ? 0.15 : 0.07),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: tweaks.primaryColor.withValues(alpha: 0.2)),
                          ),
                          child: Text(
                            'Les changements s\'appliquent en temps réel.',
                            style: TextStyle(fontSize: 11, color: tweaks.primaryColor, height: 1.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Section Label ─────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  final bool isDark;
  const _SectionLabel({required this.label, required this.isDark});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: isDark ? AminaTheme.dark300 : AminaTheme.ink700,
      ),
    );
  }
}

// ── Segment Group ─────────────────────────────────────────────────────────────

class _SegmentGroup<T> extends StatelessWidget {
  final List<(T, String)> options;
  final T selected;
  final void Function(T) onSelect;
  final bool isDark;
  final Color accent;

  const _SegmentGroup({
    required this.options,
    required this.selected,
    required this.onSelect,
    required this.isDark,
    required this.accent,
  });

  @override
  Widget build(BuildContext context) {
    final bg     = isDark ? AminaTheme.darkCardElevated : AminaTheme.ink50;
    final selBg  = isDark ? AminaTheme.darkCard         : AminaTheme.cardBg;
    final selText = accent;
    final defText = isDark ? AminaTheme.dark400          : AminaTheme.ink500;

    return Container(
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(3),
      child: Row(
        children: options.map((opt) {
          final (value, label) = opt;
          final isSelected = selected == value;
          return Expanded(
            child: GestureDetector(
              onTap: () => onSelect(value),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                padding: const EdgeInsets.symmetric(vertical: 7),
                decoration: BoxDecoration(
                  color: isSelected ? selBg : Colors.transparent,
                  borderRadius: BorderRadius.circular(6),
                  boxShadow: isSelected
                      ? (isDark ? AminaTheme.shadowDark : AminaTheme.shadowClinical)
                      : null,
                ),
                child: Text(
                  label,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                    color: isSelected ? selText : defText,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── Accent Dot ────────────────────────────────────────────────────────────────

class _AccentDot extends StatelessWidget {
  final Color color;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final bool isDark;

  const _AccentDot({
    required this.color,
    required this.label,
    required this.selected,
    required this.onTap,
    required this.isDark,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: 32, height: 32,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              border: selected
                  ? Border.all(color: isDark ? Colors.white : AminaTheme.ink900, width: 2.5)
                  : null,
              boxShadow: selected
                  ? [BoxShadow(color: color.withValues(alpha: 0.4), blurRadius: 8, offset: const Offset(0, 2))]
                  : null,
            ),
            child: selected
                ? const Icon(Icons.check, color: Colors.white, size: 16)
                : null,
          ),
          const SizedBox(height: 5),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              color: selected ? color : (isDark ? AminaTheme.dark400 : AminaTheme.ink500),
            ),
          ),
        ],
      ),
    );
  }
}