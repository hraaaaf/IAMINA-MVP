import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../core/motion/amina_motion.dart';
import '../features/auth/consent_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/onboarding_chat_screen.dart';
import '../features/auth/reset_password_screen.dart';
import '../features/navigation/main_shell.dart';
import '../features/profile/profile_screen.dart';
import '../modules/module_registry.dart';
import '../services/auth_service.dart';
import '../services/consent_service.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> _shellNavigatorKey =
    GlobalKey<NavigatorState>();

class AppRouterHolder {
  final GoRouter router;

  AppRouterHolder._(this.router);

  void dispose() => router.dispose();
}

AppRouterHolder createAppRouterHolder({
  required AuthService authService,
  ConsentService? consentService,
}) {
  final consent = consentService;

  final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: _homeRoute(),
    refreshListenable: consent != null
        ? Listenable.merge([authService, consent])
        : authService,
    redirect: (context, state) {
      final isLoggedIn = authService.isAuthenticated;
      final isAnonymous = authService.isAnonymous;
      final path = state.uri.path;
      final isLoginPage = path == '/login';
      final isPasswordResetPage = path == '/reset-password';
      final isConsentPage = path == '/consent';

      if (!authService.isInitialized) return null;

      // Password-reset links must remain reachable without a session.
      if (isPasswordResetPage) return null;

      // ── Auth gate ──────────────────────────────────────────────────────────
      if (!isLoggedIn && !isLoginPage) return '/login';
      if (isLoggedIn && isLoginPage) return _homeRoute();

      // ── Consent gate (RGPD Art. 7) ────────────────────────────────────────
      // Skip for anonymous demo users and when ConsentService is not wired.
      if (isLoggedIn && !isAnonymous && consent != null) {
        final hasConsent = consent.hasConsent;
        final hasDeclined = consent.hasDeclinedLocally;

        if (!hasConsent && !hasDeclined && !isConsentPage) return '/consent';
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
          transitionDuration: AminaMotion.standard,
          reverseTransitionDuration: AminaMotion.fast,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            if (AminaMotion.reduce(context)) return child;
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: AminaMotion.enter,
              ),
              child: child,
            );
          },
        ),
      ),
      GoRoute(
        path: '/reset-password',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: ResetPasswordScreen(
            uid: state.uri.queryParameters['uid'] ?? '',
            token: state.uri.queryParameters['token'] ?? '',
          ),
          transitionDuration: AminaMotion.standard,
          reverseTransitionDuration: AminaMotion.fast,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            if (AminaMotion.reduce(context)) return child;
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: AminaMotion.enter,
              ),
              child: child,
            );
          },
        ),
      ),
      GoRoute(
        path: '/consent',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const ConsentScreen(),
          transitionDuration: AminaMotion.standard,
          reverseTransitionDuration: AminaMotion.fast,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            if (AminaMotion.reduce(context)) return child;
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: AminaMotion.enter,
              ),
              child: child,
            );
          },
        ),
      ),
      GoRoute(
        path: '/onboarding',
        parentNavigatorKey: _rootNavigatorKey,
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const OnboardingChatScreen(),
          transitionDuration: AminaMotion.standard,
          reverseTransitionDuration: AminaMotion.fast,
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            if (AminaMotion.reduce(context)) return child;
            return FadeTransition(
              opacity: CurvedAnimation(
                parent: animation,
                curve: AminaMotion.enter,
              ),
              child: child,
            );
          },
        ),
      ),

      for (final m in ModuleRegistry.all())
        for (final r in m.fullScreenRoutes)
          GoRoute(
            path: r.path,
            parentNavigatorKey: _rootNavigatorKey,
            pageBuilder: (context, state) =>
                _createPage(state, r.builder(state)),
          ),

      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/profile',
            pageBuilder: (context, state) =>
                _createPage(state, const ProfileScreen()),
          ),
          for (final m in ModuleRegistry.all())
            for (final r in m.shellRoutes)
              GoRoute(
                path: r.path,
                pageBuilder: (context, state) =>
                    _createPage(state, r.builder()),
              ),
        ],
      ),

      GoRoute(path: '/', redirect: (context, state) => _homeRoute()),
    ],
  );

  return AppRouterHolder._(router);
}

String _homeRoute() {
  final mods = ModuleRegistry.all();
  if (mods.isNotEmpty && mods.first.navDestinations.isNotEmpty) {
    return mods.first.navDestinations.first.route;
  }
  return '/dashboard';
}

GoRouter createAppRouter([dynamic auth]) {
  final service = auth is AuthService ? auth : AuthService();
  return createAppRouterHolder(authService: service).router;
}

CustomTransitionPage _createPage(GoRouterState state, Widget child) {
  return CustomTransitionPage(
    key: state.pageKey,
    child: child,
    transitionDuration: AminaMotion.standard,
    reverseTransitionDuration: AminaMotion.fast,
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      if (AminaMotion.reduce(context)) return child;
      final entrance = CurvedAnimation(
        parent: animation,
        curve: AminaMotion.enter,
      );
      return FadeTransition(
        opacity: entrance,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.018),
            end: Offset.zero,
          ).animate(entrance),
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
