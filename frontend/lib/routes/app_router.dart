import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/onboarding_chat_screen.dart';
import '../features/auth/consent_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/navigation/main_shell.dart';
import '../modules/module_registry.dart';
import '../services/consent_service.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> _shellNavigatorKey = GlobalKey<NavigatorState>();

class _AuthNotifier extends ChangeNotifier {
  late final StreamSubscription<User?> _sub;

  _AuthNotifier() {
    _sub = FirebaseAuth.instance.authStateChanges().listen((_) => notifyListeners());
  }

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}

// Holds the notifier alongside the router so both can be disposed together.
class AppRouterHolder {
  final GoRouter router;
  final _AuthNotifier _notifier;

  AppRouterHolder._(this.router, this._notifier);

  void dispose() {
    _notifier.dispose();
    router.dispose();
  }
}

AppRouterHolder createAppRouterHolder({ConsentService? consentService}) {
  final authNotifier = _AuthNotifier();
  final consent = consentService;

  final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: _homeRoute(),
    refreshListenable: consent != null
        ? Listenable.merge([authNotifier, consent])
        : authNotifier,
    redirect: (context, state) {
      final user = FirebaseAuth.instance.currentUser;
      final isLoggedIn = user != null;
      final isAnonymous = user?.isAnonymous ?? false;
      final path = state.uri.path;
      final isLoginPage = path == '/login';
      final isConsentPage = path == '/consent';

      // ── Auth gate ──────────────────────────────────────────────────────────
      if (!isLoggedIn && !isLoginPage) return '/login';
      if (isLoggedIn && isLoginPage) return _homeRoute();

      // ── Consent gate (RGPD Art. 7) ────────────────────────────────────────
      // Skip for anonymous (demo) users — they never gave a real identity.
      // Skip if ConsentService not yet wired (fallback path).
      if (isLoggedIn && !isAnonymous && consent != null) {
        final hasConsent  = consent.hasConsent;
        final hasDeclined = consent.hasDeclinedLocally;

        // If user has not consented AND hasn't declined this session → gate
        if (!hasConsent && !hasDeclined && !isConsentPage) return '/consent';

        // If user now has consent but landed on consent page → move on
        if (hasConsent && isConsentPage) return _homeRoute();
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const LoginScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),
      GoRoute(
        path: '/consent',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const ConsentScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),
      GoRoute(
        path: '/onboarding',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const OnboardingChatScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),

      // ── Full-screen routes (above shell — no bottom nav) ──────────────────
      // Generated from each registered module's full-screen routes (P6).
      for (final m in ModuleRegistry.all())
        for (final r in m.fullScreenRoutes)
          GoRoute(
            path: r.path,
            parentNavigatorKey: _rootNavigatorKey,
            pageBuilder: (context, state) => _createPage(state, r.builder(state)),
          ),

      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          // Chassis shell route (always present, condition-agnostic).
          GoRoute(
            path: '/profile',
            pageBuilder: (context, state) => _createPage(state, const ProfileScreen()),
          ),
          // Module shell routes, generated from the registry (P6).
          for (final m in ModuleRegistry.all())
            for (final r in m.shellRoutes)
              GoRoute(
                path: r.path,
                pageBuilder: (context, state) => _createPage(state, r.builder()),
              ),
        ],
      ),

      GoRoute(
        path: '/',
        redirect: (context, state) => _homeRoute(),
      ),
    ],
  );

  return AppRouterHolder._(router, authNotifier);
}

/// The default landing route — the first nav destination of the first module.
/// Falls back to '/dashboard' if no module declares one.
String _homeRoute() {
  final mods = ModuleRegistry.all();
  if (mods.isNotEmpty && mods.first.navDestinations.isNotEmpty) {
    return mods.first.navDestinations.first.route;
  }
  return '/dashboard';
}

// Kept for backward compat — returns just the GoRouter.
GoRouter createAppRouter([dynamic auth]) => createAppRouterHolder().router;

CustomTransitionPage _createPage(GoRouterState state, Widget child) {
  return CustomTransitionPage(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 300),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return FadeTransition(
        opacity: CurveTween(curve: Curves.easeInOut).animate(animation),
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.05),
            end: Offset.zero,
          ).animate(CurveTween(curve: Curves.easeOutCubic).animate(animation)),
          child: child,
        ),
      );
    },
  );
}

class PlaceholderScreen extends StatelessWidget {
  final String title;
  const PlaceholderScreen({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(child: Text(title)),
    );
  }
}
