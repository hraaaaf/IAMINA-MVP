import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/app_lock_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../services/app_lock_service.dart';

class AppLockUnlockScreen extends StatefulWidget {
  const AppLockUnlockScreen({super.key});

  @override
  State<AppLockUnlockScreen> createState() => _AppLockUnlockScreenState();
}

class _AppLockUnlockScreenState extends State<AppLockUnlockScreen> {
  bool _busy = false;
  String? _error;

  Future<void> _unlock() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await context.read<AppLockService>().unlock();
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) setState(() => _error = AppLocalizations.of(context)!.appLockUnlockFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final lock = context.watch<AppLockService>();
    final dark = AminaTheme.isDark(context);
    final recovery = lock.recoveryRequired;

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        fit: StackFit.expand,
        children: [
          DecoratedBox(
            decoration: BoxDecoration(
              color: dark ? AminaTheme.darkPaper : AminaTheme.paper,
              gradient: dark
                  ? null
                  : const RadialGradient(
                      center: Alignment(-.72, -.78),
                      radius: 1.3,
                      colors: [Color(0xFFDDF8F1), Color(0xFFF7FBFA)],
                      stops: [0, .72],
                    ),
            ),
          ),
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsetsDirectional.fromSTEB(24, 28, 24, 28),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Column(
                    children: [
                      SizedBox(
                        width: 116,
                        height: 116,
                        child: Image.asset(
                          'assets/images/logo_amina.png',
                          fit: BoxFit.contain,
                          filterQuality: FilterQuality.high,
                          errorBuilder: (_, __, ___) => const _LogoFallback(),
                        ),
                      ),
                      const SizedBox(height: 24),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsetsDirectional.fromSTEB(26, 28, 26, 25),
                        decoration: BoxDecoration(
                          color: AminaTheme.surface(context).withValues(alpha: dark ? .98 : .98),
                          borderRadius: BorderRadius.circular(28),
                          border: Border.all(color: AminaTheme.divider(context).withValues(alpha: dark ? .70 : .56)),
                          boxShadow: dark
                              ? AminaTheme.shadowDark
                              : const [
                                  BoxShadow(
                                    color: Color(0x1411423A),
                                    blurRadius: 36,
                                    spreadRadius: -10,
                                    offset: Offset(0, 18),
                                  ),
                                ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Center(
                              child: Container(
                                width: 72,
                                height: 72,
                                decoration: BoxDecoration(
                                  color: recovery
                                      ? AminaTheme.dangerBg
                                      : AminaTheme.teal50.withValues(alpha: dark ? .12 : 1),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  recovery ? Icons.gpp_bad_outlined : Icons.fingerprint_rounded,
                                  size: 38,
                                  color: recovery
                                      ? AminaTheme.dangerFg
                                      : (dark ? AminaTheme.teal400 : AminaTheme.teal700),
                                ),
                              ),
                            ),
                            const SizedBox(height: 20),
                            Text(
                              recovery ? l10n.appLockRecoveryTitle : l10n.appLockLockedTitle,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontFamily: 'Georgia',
                                fontFamilyFallback: const ['Times New Roman', 'serif'],
                                fontSize: 27,
                                height: 1.08,
                                fontWeight: FontWeight.w700,
                                letterSpacing: -.5,
                                color: dark ? AminaTheme.dark100 : const Color(0xFF073D31),
                              ),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              recovery ? l10n.appLockRecoveryBody : l10n.appLockLockedSubtitle,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 13.5,
                                height: 1.5,
                                color: dark ? AminaTheme.dark300 : AminaTheme.ink500,
                              ),
                            ),
                            if (_error != null) ...[
                              const SizedBox(height: 18),
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AminaTheme.dangerBg,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _error!,
                                  style: const TextStyle(fontSize: 12.5, height: 1.4, color: AminaTheme.dangerFg),
                                ),
                              ),
                            ],
                            const SizedBox(height: 24),
                            if (!recovery)
                              FilledButton.icon(
                                key: const Key('app-lock-unlock'),
                                onPressed: _busy ? null : _unlock,
                                icon: _busy
                                    ? const SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                      )
                                    : const Icon(Icons.lock_open_rounded),
                                label: Text(_error == null ? l10n.appLockUnlock : l10n.appLockRetry),
                                style: FilledButton.styleFrom(
                                  minimumSize: const Size.fromHeight(52),
                                  backgroundColor: AminaTheme.teal700,
                                  foregroundColor: Colors.white,
                                  textStyle: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
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
        ],
      ),
    );
  }
}

class _LogoFallback extends StatelessWidget {
  const _LogoFallback();

  @override
  Widget build(BuildContext context) => const Center(
        child: Text(
          'IAmina',
          style: TextStyle(
            fontFamily: 'Georgia',
            fontSize: 28,
            fontWeight: FontWeight.w700,
            color: Color(0xFF075A45),
          ),
        ),
      );
}
