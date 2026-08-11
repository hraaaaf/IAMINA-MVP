import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../core/motion/amina_motion.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../modules/module_config.dart';
import '../../modules/module_registry.dart';
import '../../services/modules_provider.dart';

/// A single nav entry — one source of truth for sidebar + bottom nav + index
/// mapping, derived from the module registry (+ chassis settings).
class _NavEntry {
  final String route;
  final IconData icon;
  final IconData selectedIcon;
  final L10nLabel label;
  final bool isAccount;

  const _NavEntry({
    required this.route,
    required this.icon,
    required this.selectedIcon,
    required this.label,
    this.isAccount = false,
  });
}

List<_NavEntry> _navEntries(Set<String> activeIds) {
  final entries = <_NavEntry>[];
  for (final module in ModuleRegistry.activeFrom(activeIds)) {
    for (final destination in module.navDestinations) {
      entries.add(
        _NavEntry(
          route: destination.route,
          icon: destination.icon,
          selectedIcon: destination.selectedIcon,
          label: destination.label,
        ),
      );
    }
  }
  entries.add(
    _NavEntry(
      route: '/profile',
      icon: Icons.person_outline_rounded,
      selectedIcon: Icons.person_rounded,
      label: (l10n) => l10n.profile,
      isAccount: true,
    ),
  );
  return entries;
}

int _selectedIndexFor(String path, List<_NavEntry> entries) {
  for (var index = 0; index < entries.length; index++) {
    if (path.startsWith(entries[index].route)) return index;
  }
  return 0;
}

String _sensorStatusLabel(PatientProfileData? profile, AppLocalizations l10n) {
  if (profile == null) return l10n.sensorStatus;
  return switch (profile.treatment) {
    'insulin' => '💉 ${l10n.treatmentInsulin} · IAmina',
    'tablets' => '💊 ${l10n.treatmentTablets} · IAmina',
    'lifestyle' => '🌿 ${l10n.treatmentLifestyle} · IAmina',
    _ => l10n.sensorStatus,
  };
}

class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final isMedium = MediaQuery.sizeOf(context).width >= 700;
    final activeIds = context.watch<ModulesProvider>().activeIds;
    final entries = _navEntries(activeIds);
    final selected = _selectedIndexFor(
      GoRouterState.of(context).uri.path,
      entries,
    );

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Row(
        children: [
          if (isMedium) _Sidebar(entries: entries, selectedIndex: selected),
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final media = MediaQuery.of(context);
                return MediaQuery(
                  data: media.copyWith(
                    size: Size(constraints.maxWidth, constraints.maxHeight),
                  ),
                  child: child,
                );
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: isMedium
          ? null
          : _BottomNav(entries: entries, selectedIndex: selected),
    );
  }
}

class _EcgMarkPainter extends CustomPainter {
  final Color color;

  _EcgMarkPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;
    final path = Path();
    final width = size.width;
    final halfHeight = size.height / 2;

    path.moveTo(width * 0.5, 0);
    path.lineTo(width * 0.5, halfHeight * 0.55);
    path.lineTo(width * 0.35, halfHeight * 0.55);
    path.lineTo(width * 0.42, halfHeight * 0.15);
    path.lineTo(width * 0.55, halfHeight * 1.85);
    path.lineTo(width * 0.65, halfHeight * 0.55);
    path.lineTo(width * 0.65, halfHeight);
    path.moveTo(width * 0.5, halfHeight);
    path.lineTo(width * 0.5, size.height);
    canvas.drawPath(path, paint);
    canvas.drawCircle(
      Offset(width * 0.5, 0),
      1.4,
      Paint()
        ..color = color
        ..style = PaintingStyle.fill,
    );
  }

  @override
  bool shouldRepaint(_EcgMarkPainter oldDelegate) => oldDelegate.color != color;
}

class _Sidebar extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;

  const _Sidebar({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.sizeOf(context).width >= 1100;
    final user = FirebaseAuth.instance.currentUser;
    final fallbackName = AppLocalizations.of(context)!.profile;
    final displayName = user?.displayName ?? user?.email ?? fallbackName;

    return Container(
      width: isWide ? 260 : 72,
      height: double.infinity,
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: BorderDirectional(
          end: BorderSide(color: AminaTheme.divider(context)),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _BrandHeader(isWide: isWide),
          const SizedBox(height: 8),
          _AddButton(isWide: isWide),
          const SizedBox(height: 8),
          if (isWide)
            _NavLabel(AppLocalizations.of(context)!.navSectionMain)
          else
            const SizedBox(height: 8),
          for (var index = 0; index < entries.length; index++)
            if (!entries[index].isAccount)
              _NavItem(
                entry: entries[index],
                isWide: isWide,
                selected: selectedIndex == index,
              ),
          const SizedBox(height: 8),
          if (isWide)
            _NavLabel(AppLocalizations.of(context)!.navSectionAccount),
          for (var index = 0; index < entries.length; index++)
            if (entries[index].isAccount)
              _NavItem(
                entry: entries[index],
                isWide: isWide,
                selected: selectedIndex == index,
              ),
          _LogoutItem(isWide: isWide),
          const Spacer(),
          _UserChip(
            isWide: isWide,
            initials: _initials(displayName),
            name: displayName,
          ),
        ],
      ),
    );
  }

  String _initials(String name) {
    if (name.isEmpty) return '??';
    final parts = name
        .split(RegExp(r'[\s@.]'))
        .where((part) => part.isNotEmpty)
        .toList();
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    if (name.length >= 2) return name.substring(0, 2).toUpperCase();
    return name.toUpperCase();
  }
}

class _AddButton extends StatelessWidget {
  final bool isWide;

  const _AddButton({required this.isWide});

  @override
  Widget build(BuildContext context) {
    final label = AppLocalizations.of(context)!.addEntry;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Tooltip(
        message: label,
        child: Semantics(
          button: true,
          label: label,
          child: InkWell(
            onTap: () {
              HapticFeedback.lightImpact();
              GoRouter.of(context).go('/ajouter');
            },
            borderRadius: BorderRadius.circular(10),
            child: Container(
              constraints: const BoxConstraints(minHeight: 44),
              padding: EdgeInsetsDirectional.fromSTEB(
                isWide ? 14 : 0,
                8,
                isWide ? 14 : 0,
                8,
              ),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AminaTheme.teal500, AminaTheme.teal700],
                  begin: AlignmentDirectional.topStart,
                  end: AlignmentDirectional.bottomEnd,
                ),
                borderRadius: BorderRadius.circular(10),
                boxShadow: AminaTheme.shadowFab,
              ),
              child: Row(
                mainAxisAlignment: isWide
                    ? MainAxisAlignment.start
                    : MainAxisAlignment.center,
                children: [
                  const Icon(Icons.add, color: Colors.white, size: 18),
                  if (isWide) ...[
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        label,
                        maxLines: 2,
                        softWrap: true,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BrandHeader extends StatelessWidget {
  final bool isWide;

  const _BrandHeader({required this.isWide});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(16, 24, 16, 8),
      child: Row(
        children: [
          ExcludeSemantics(
            child: Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AminaTheme.teal500, AminaTheme.teal800],
                  begin: AlignmentDirectional.topStart,
                  end: AlignmentDirectional.bottomEnd,
                ),
                borderRadius: BorderRadius.circular(10),
                boxShadow: [
                  BoxShadow(
                    color: AminaTheme.teal700.withValues(alpha: 0.45),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Center(
                child: SizedBox(
                  width: 18,
                  height: 22,
                  child: CustomPaint(
                    painter: _EcgMarkPainter(
                      color: Colors.white.withValues(alpha: 0.92),
                    ),
                  ),
                ),
              ),
            ),
          ),
          if (isWide) ...[
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    AppLocalizations.of(context)!.appTitle,
                    maxLines: 2,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  Text(
                    AppLocalizations.of(context)!.appSubtitle,
                    maxLines: 2,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 10,
                      color: AminaTheme.textSecondary(context),
                      letterSpacing: 0.18,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _NavLabel extends StatelessWidget {
  final String label;

  const _NavLabel(this.label);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 6),
      child: Text(
        label.toUpperCase(),
        maxLines: 2,
        style: TextStyle(
          fontSize: 10.5,
          color: AminaTheme.textSecondary(context).withValues(alpha: 0.7),
          fontWeight: FontWeight.w600,
          letterSpacing: 0.16,
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final _NavEntry entry;
  final bool isWide;
  final bool selected;

  const _NavItem({
    required this.entry,
    required this.isWide,
    required this.selected,
  });

  @override
  Widget build(BuildContext context) {
    final label = entry.label(AppLocalizations.of(context)!);
    final dark = AminaTheme.isDark(context);
    final activeBackground = dark
        ? AminaTheme.teal700.withValues(alpha: 0.22)
        : AminaTheme.teal50;
    final activeColor = dark ? AminaTheme.teal400 : AminaTheme.teal700;
    final inactiveColor = dark ? AminaTheme.dark400 : AminaTheme.ink500;
    final textColor = dark ? AminaTheme.dark200 : AminaTheme.ink700;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Tooltip(
        message: label,
        child: Semantics(
          button: true,
          selected: selected,
          label: label,
          child: InkWell(
            onTap: () => GoRouter.of(context).go(entry.route),
            borderRadius: BorderRadius.circular(10),
            child: AnimatedContainer(
              duration: AminaMotion.resolve(context, AminaMotion.fast),
              curve: AminaMotion.standardCurve,
              constraints: const BoxConstraints(minHeight: 44),
              padding: EdgeInsetsDirectional.fromSTEB(
                isWide ? 12 : 0,
                4,
                isWide ? 12 : 0,
                4,
              ),
              decoration: BoxDecoration(
                color: selected ? activeBackground : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Stack(
                children: [
                  if (selected)
                    PositionedDirectional(
                      start: -8,
                      top: 8,
                      bottom: 8,
                      child: Container(
                        width: 2.5,
                        decoration: BoxDecoration(
                          color: activeColor,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  Row(
                    mainAxisAlignment: isWide
                        ? MainAxisAlignment.start
                        : MainAxisAlignment.center,
                    children: [
                      Icon(
                        selected ? entry.selectedIcon : entry.icon,
                        color: selected ? activeColor : inactiveColor,
                        size: 18,
                      ),
                      if (isWide) ...[
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            label,
                            maxLines: 2,
                            softWrap: true,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: selected
                                  ? FontWeight.w600
                                  : FontWeight.w500,
                              color: selected ? activeColor : textColor,
                            ),
                          ),
                        ),
                      ],
                    ],
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

class _LogoutItem extends StatelessWidget {
  final bool isWide;

  const _LogoutItem({required this.isWide});

  @override
  Widget build(BuildContext context) {
    final label = AppLocalizations.of(context)!.logout;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Tooltip(
        message: label,
        child: Semantics(
          button: true,
          label: label,
          child: InkWell(
            onTap: () async {
              await context.read<AuthService>().signOut();
              if (context.mounted) GoRouter.of(context).go('/login');
            },
            borderRadius: BorderRadius.circular(10),
            child: Container(
              constraints: const BoxConstraints(minHeight: 44),
              padding: EdgeInsetsDirectional.fromSTEB(
                isWide ? 12 : 0,
                4,
                isWide ? 12 : 0,
                4,
              ),
              child: Row(
                mainAxisAlignment: isWide
                    ? MainAxisAlignment.start
                    : MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.logout_rounded,
                    color: AminaTheme.textSecondary(context),
                    size: 18,
                  ),
                  if (isWide) ...[
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        label,
                        maxLines: 2,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AminaTheme.textPrimary(context),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _UserChip extends StatelessWidget {
  final bool isWide;
  final String initials;
  final String name;

  const _UserChip({
    required this.isWide,
    required this.initials,
    required this.name,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Row(
        children: [
          ExcludeSemantics(
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFE9D3A3), Color(0xFFC78B3A)],
                ),
                borderRadius: BorderRadius.circular(10),
              ),
              alignment: Alignment.center,
              child: Text(
                initials,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          if (isWide) ...[
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  Builder(
                    builder: (context) {
                      final status = _sensorStatusLabel(
                        context.watch<PatientProfileData?>(),
                        AppLocalizations.of(context)!,
                      );
                      return Text(
                        status,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: AminaTheme.textSecondary(context),
                          fontSize: 11,
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _BottomNav extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;

  const _BottomNav({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final mobileEntries = entries
        .where((entry) => entry.route != '/importer')
        .toList(growable: false);
    final currentPath = GoRouterState.of(context).uri.path;
    final safeIndex = _selectedIndexFor(
      currentPath,
      mobileEntries,
    ).clamp(0, mobileEntries.length - 1);
    final rtl = Directionality.of(context) == TextDirection.rtl;
    final visualIndex = rtl ? mobileEntries.length - 1 - safeIndex : safeIndex;
    final glassColor = dark
        ? AminaTheme.darkCard.withValues(alpha: 0.88)
        : Colors.white.withValues(alpha: 0.92);
    final glassBorder = dark
        ? Colors.white.withValues(alpha: 0.12)
        : Colors.white.withValues(alpha: 0.92);
    final indicatorColor = dark
        ? AminaTheme.teal700.withValues(alpha: 0.34)
        : AminaTheme.teal50.withValues(alpha: 0.96);
    final addLabel = AppLocalizations.of(context)!.addEntry;

    return SafeArea(
      top: false,
      minimum: EdgeInsets.symmetric(horizontal: 18).copyWith(bottom: 6),
      child: SizedBox(
        height: 82,
        child: Stack(
          alignment: Alignment.topCenter,
          clipBehavior: Clip.none,
          children: [
            Positioned.fill(
              top: 14,
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
                          color: Colors.black.withValues(
                            alpha: dark ? 0.24 : 0.10,
                          ),
                          blurRadius: 28,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        final itemWidth =
                            constraints.maxWidth / mobileEntries.length;
                        return Material(
                          color: Colors.transparent,
                          child: Stack(
                            children: [
                              AnimatedPositioned(
                                duration: AminaMotion.resolve(
                                  context,
                                  AminaMotion.navSelection,
                                ),
                                curve: AminaMotion.enter,
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
                                            ? AminaTheme.teal400.withValues(
                                                alpha: 0.16,
                                              )
                                            : AminaTheme.teal500.withValues(
                                                alpha: 0.12,
                                              ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              Row(
                                children: [
                                  for (
                                    var index = 0;
                                    index < mobileEntries.length;
                                    index++
                                  )
                                    Expanded(
                                      child: Padding(
                                        padding: EdgeInsetsDirectional.only(
                                          end: index == 1 ? 22 : 0,
                                          start: index == 2 ? 22 : 0,
                                        ),
                                        child: _GlassNavDestination(
                                          entry: mobileEntries[index],
                                          selected: index == safeIndex,
                                          onTap: () {
                                            HapticFeedback.selectionClick();
                                            GoRouter.of(
                                              context,
                                            ).go(mobileEntries[index].route);
                                          },
                                        ),
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
            ),
            Semantics(
              button: true,
              label: addLabel,
              child: Tooltip(
                message: addLabel,
                child: InkWell(
                  key: const ValueKey('mobile-nav-add'),
                  onTap: () {
                    HapticFeedback.lightImpact();
                    GoRouter.of(context).go('/ajouter');
                  },
                  customBorder: const CircleBorder(),
                  child: Container(
                    width: 54,
                    height: 54,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF0A766B), Color(0xFF064D50)],
                        begin: AlignmentDirectional.topStart,
                        end: AlignmentDirectional.bottomEnd,
                      ),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: dark ? AminaTheme.darkCard : Colors.white,
                        width: 5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(
                            0xFF064D50,
                          ).withValues(alpha: 0.30),
                          blurRadius: 18,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.add_rounded,
                      color: Colors.white,
                      size: 30,
                    ),
                  ),
                ),
              ),
            ),
          ],
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
                duration: AminaMotion.resolve(
                  context,
                  AminaMotion.navSelection,
                ),
                curve: AminaMotion.enter,
                child: Icon(
                  selected ? entry.selectedIcon : entry.icon,
                  color: selected ? activeColor : inactiveColor,
                  size: 20,
                ),
              ),
              const SizedBox(height: 4),
              AnimatedDefaultTextStyle(
                duration: AminaMotion.resolve(
                  context,
                  AminaMotion.navSelection,
                ),
                curve: AminaMotion.enter,
                style: TextStyle(
                  fontSize: 9.6,
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
