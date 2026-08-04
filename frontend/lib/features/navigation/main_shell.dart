import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../modules/module_config.dart';
import '../../modules/module_registry.dart';
import '../../services/modules_provider.dart';

/// A single nav entry — one source of truth for sidebar + bottom nav + index
/// mapping, derived from the module registry (+ chassis settings). Replaces the
/// former hardcoded integer-index switch (MISTAKES #16: those must never drift).
class _NavEntry {
  final String route;
  final IconData icon;
  final IconData selectedIcon;
  final L10nLabel label;
  final bool isAccount; // false = MAIN section, true = ACCOUNT section
  const _NavEntry({
    required this.route,
    required this.icon,
    required this.selectedIcon,
    required this.label,
    this.isAccount = false,
  });
}

/// Build the ordered nav entries: each active module's destinations (MAIN),
/// then the chassis "settings" entry (ACCOUNT). The active set comes from
/// ModulesProvider (backend GET /account/modules), defaulting to all registered.
List<_NavEntry> _navEntries(Set<String> activeIds) {
  final entries = <_NavEntry>[];
  for (final m in ModuleRegistry.activeFrom(activeIds)) {
    for (final d in m.navDestinations) {
      entries.add(_NavEntry(
        route: d.route,
        icon: d.icon,
        selectedIcon: d.selectedIcon,
        label: d.label,
      ));
    }
  }
  entries.add(_NavEntry(
    route: '/profile',
    icon: Icons.settings_outlined,
    selectedIcon: Icons.settings_rounded,
    label: (l) => l.navSettings,
    isAccount: true,
  ));
  return entries;
}

int _selectedIndexFor(String path, List<_NavEntry> entries) {
  for (var i = 0; i < entries.length; i++) {
    if (path.startsWith(entries[i].route)) return i;
  }
  return 0;
}

/// Returns a short status string based on the user's treatment plan.
/// Falls back to the generic l10n key when profile is unavailable.
String _sensorStatusLabel(PatientProfileData? profile, AppLocalizations l10n) {
  if (profile == null) return l10n.sensorStatus;
  switch (profile.treatment) {
    case 'insulin':    return '💉 Insuline · IAmina';
    case 'tablets':    return '💊 Comprimés · IAmina';
    case 'lifestyle':  return '🌿 Mode bien-être · IAmina';
    default:           return l10n.sensorStatus;
  }
}

class MainShell extends StatelessWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final bool isMedium = MediaQuery.of(context).size.width >= 700;
    final bg = AminaTheme.bg(context);
    final activeIds = context.watch<ModulesProvider>().activeIds;
    final entries = _navEntries(activeIds);
    final selected = _selectedIndexFor(GoRouterState.of(context).uri.path, entries);

    return Scaffold(
      backgroundColor: bg,
      body: Row(
        children: [
          if (isMedium) _Sidebar(entries: entries, selectedIndex: selected),
          Expanded(child: child),
        ],
      ),
      bottomNavigationBar:
          isMedium ? null : _BottomNav(entries: entries, selectedIndex: selected),
    );
  }
}

// ── ECG Logo Mark (CustomPainter) ─────────────────────────────────────────────

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
    final w = size.width;
    final h = size.height / 2;

    // Vertical Alif stroke (top)
    path.moveTo(w * 0.5, 0);
    path.lineTo(w * 0.5, h * 0.55);

    // ECG burst
    path.lineTo(w * 0.35, h * 0.55);
    path.lineTo(w * 0.42, h * 0.15);
    path.lineTo(w * 0.55, h * 1.85);
    path.lineTo(w * 0.65, h * 0.55);

    // Vertical Alif stroke (bottom)
    path.moveTo(w * 0.65, h * 0.55);
    path.lineTo(w * 0.65, h * 1.0);
    path.moveTo(w * 0.5, h * 1.0);
    path.lineTo(w * 0.5, size.height);

    canvas.drawPath(path, paint);

    // Dot on top
    canvas.drawCircle(Offset(w * 0.5, 0), 1.4, Paint()..color = color..style = PaintingStyle.fill);
  }

  @override
  bool shouldRepaint(_EcgMarkPainter old) => old.color != color;
}

// ── Sidebar (desktop ≥ 700px) ──────────────────────────────────────────────

class _Sidebar extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;
  const _Sidebar({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final bool isWide = MediaQuery.of(context).size.width >= 1100;
    final user = FirebaseAuth.instance.currentUser;
    final initials = _initials(user?.displayName ?? user?.email ?? 'U');

    return Container(
      width: isWide ? 260 : 72,
      height: double.infinity,
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: Border(right: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _BrandHeader(isWide: isWide),
          const SizedBox(height: 8),
          _AddButton(isWide: isWide),
          const SizedBox(height: 8),
          if (isWide)
            _NavLabel(AppLocalizations.of(context)!.navSectionMain, context: context)
          else
            const SizedBox(height: 8),
          for (var i = 0; i < entries.length; i++)
            if (!entries[i].isAccount)
              _NavItem(entry: entries[i], isWide: isWide, selected: selectedIndex == i),
          const SizedBox(height: 8),
          if (isWide) _NavLabel(AppLocalizations.of(context)!.navSectionAccount, context: context),
          for (var i = 0; i < entries.length; i++)
            if (entries[i].isAccount)
              _NavItem(entry: entries[i], isWide: isWide, selected: selectedIndex == i),
          _LogoutItem(isWide: isWide),
          const Spacer(),
          _UserChip(isWide: isWide, initials: initials, name: user?.displayName ?? user?.email ?? 'Utilisateur'),
        ],
      ),
    );
  }

  String _initials(String name) {
    if (name.isEmpty) return '??';
    final parts = name.split(RegExp(r'[\s@.]')).where((p) => p.isNotEmpty).toList();
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    if (name.length >= 2) return name.substring(0, 2).toUpperCase();
    return name.toUpperCase();
  }
}

class _AddButton extends StatelessWidget {
  final bool isWide;
  const _AddButton({required this.isWide});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          GoRouter.of(context).go('/ajouter');
        },
        child: Container(
          height: 40,
          padding: EdgeInsets.symmetric(horizontal: isWide ? 14 : 0),
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
            mainAxisAlignment: isWide ? MainAxisAlignment.start : MainAxisAlignment.center,
            children: [
              const Icon(Icons.add, color: Colors.white, size: 18),
              if (isWide) ...[
                const SizedBox(width: 8),
                const Text(
                  'Ajouter',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ],
            ],
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
          // ECG mark container
          Container(
            width: 34, height: 34,
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
                width: 18, height: 22,
                child: CustomPaint(
                  painter: _EcgMarkPainter(color: Colors.white.withValues(alpha: 0.92)),
                ),
              ),
            ),
          ),
          if (isWide) ...[
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  AppLocalizations.of(context)!.brandName,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: AminaTheme.textPrimary(context),
                    letterSpacing: -0.02,
                  ),
                ),
                Text(
                  AppLocalizations.of(context)!.brandTagShort,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 10,
                    color: AminaTheme.textSecondary(context),
                    letterSpacing: 0.18,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _NavLabel extends StatelessWidget {
  final String label;
  final BuildContext context;
  const _NavLabel(this.label, {required this.context});

  @override
  Widget build(BuildContext ctx) {
    return Padding(
      padding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 6),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          fontSize: 10.5,
          color: AminaTheme.textSecondary(ctx).withValues(alpha: 0.7),
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
    final icon = entry.icon;
    final selectedIcon = entry.selectedIcon;
    final dark = AminaTheme.isDark(context);
    final activeBg = dark
        ? AminaTheme.teal700.withValues(alpha: 0.22)
        : AminaTheme.teal50;
    final activeColor = dark ? AminaTheme.teal400 : AminaTheme.teal700;
    final inactiveColor = dark ? AminaTheme.dark400 : AminaTheme.ink500;
    final textColor = dark ? AminaTheme.dark200 : AminaTheme.ink700;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: InkWell(
        onTap: () => _navigate(context),
        borderRadius: BorderRadius.circular(10),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          height: 38,
          padding: EdgeInsets.symmetric(horizontal: isWide ? 12 : 0),
          decoration: BoxDecoration(
            color: selected ? activeBg : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Stack(
            children: [
              // Active left bar
              if (selected)
                PositionedDirectional(
                  start: isWide ? -8 : -8,
                  top: 8, bottom: 8,
                  child: Container(
                    width: 2.5,
                    decoration: BoxDecoration(
                      color: activeColor,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
              Row(
                mainAxisAlignment: isWide ? MainAxisAlignment.start : MainAxisAlignment.center,
                children: [
                  Icon(
                    selected ? selectedIcon : icon,
                    color: selected ? activeColor : inactiveColor,
                    size: 17,
                  ),
                  if (isWide) ...[
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        label,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
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
    );
  }

  void _navigate(BuildContext context) {
    GoRouter.of(context).go(entry.route);
  }
}

class _LogoutItem extends StatelessWidget {
  final bool isWide;
  const _LogoutItem({required this.isWide});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: InkWell(
        onTap: () async {
          await context.read<AuthService>().signOut();
          if (context.mounted) GoRouter.of(context).go('/login');
        },
        borderRadius: BorderRadius.circular(10),
        child: Container(
          height: 38,
          padding: EdgeInsets.symmetric(horizontal: isWide ? 12 : 0),
          child: Row(
            mainAxisAlignment: isWide ? MainAxisAlignment.start : MainAxisAlignment.center,
            children: [
              Icon(Icons.logout_rounded, color: AminaTheme.textSecondary(context), size: 17),
              if (isWide) ...[
                const SizedBox(width: 10),
                Text(
                  AppLocalizations.of(context)!.logout,
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AminaTheme.textPrimary(context)),
                ),
              ],
            ],
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
  const _UserChip({required this.isWide, required this.initials, required this.name});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Row(
        children: [
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFFE9D3A3), Color(0xFFC78B3A)]),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                initials,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12),
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
                    name.length > 20 ? '${name.substring(0, 18)}…' : name,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                      color: AminaTheme.textPrimary(context),
                    ),
                  ),
                  Builder(builder: (ctx) {
                    final profile = ctx.watch<PatientProfileData?>();
                    final status = _sensorStatusLabel(profile, AppLocalizations.of(ctx)!);
                    return Text(status, style: TextStyle(color: AminaTheme.textSecondary(ctx), fontSize: 11));
                  }),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Bottom Nav (mobile < 700px) ──────────────────────────────────────────────

class _BottomNav extends StatelessWidget {
  final List<_NavEntry> entries;
  final int selectedIndex;
  const _BottomNav({required this.entries, required this.selectedIndex});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final bg = dark ? AminaTheme.darkCard : AminaTheme.cardBg;
    final indicatorColor = dark ? AminaTheme.teal700.withValues(alpha: 0.3) : AminaTheme.teal50;

    return Theme(
      data: Theme.of(context).copyWith(
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: bg,
          indicatorColor: indicatorColor,
          height: 68,
          iconTheme: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return IconThemeData(color: dark ? AminaTheme.teal400 : AminaTheme.teal600, size: 22);
            }
            return IconThemeData(color: dark ? AminaTheme.dark400 : AminaTheme.ink400, size: 22);
          }),
          labelTextStyle: WidgetStateProperty.all(
            TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w600,
              color: dark ? AminaTheme.dark200 : AminaTheme.ink600,
              fontFamily: 'Inter',
            ),
          ),
        ),
      ),
      child: NavigationBar(
        selectedIndex: selectedIndex.clamp(0, entries.length - 1),
        onDestinationSelected: (i) => GoRouter.of(context).go(entries[i].route),
        destinations: [
          for (final e in entries)
            NavigationDestination(
              icon: Icon(e.icon),
              selectedIcon: Icon(e.selectedIcon),
              label: e.label(AppLocalizations.of(context)!),
            ),
        ],
      ),
    );
  }
}

