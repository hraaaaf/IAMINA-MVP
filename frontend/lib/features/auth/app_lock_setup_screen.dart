import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/app_lock_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../services/app_lock_authenticator.dart';
import '../../services/app_lock_service.dart';
import '../../services/audit_access_policy.dart';

class AppLockSetupScreen extends StatefulWidget {
  const AppLockSetupScreen({super.key});

  @override
  State<AppLockSetupScreen> createState() => _AppLockSetupScreenState();
}

class _AppLockSetupScreenState extends State<AppLockSetupScreen> {
  AppLockCapability? _capability;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkCapability());
  }

  Future<void> _checkCapability() async {
    if (AuditAccessPolicy.isAllowed(Uri.base) &&
        Uri.base.queryParameters['appLockPreview'] == 'supported') {
      if (mounted) setState(() => _capability = AppLockCapability.supported);
      return;
    }
    try {
      final result = await context.read<AppLockService>().capability();
      if (mounted) setState(() => _capability = result);
    } catch (_) {
      if (mounted) setState(() => _capability = AppLockCapability.unavailable);
    }
  }

  Future<void> _activate() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await context.read<AppLockService>().configure();
      if (mounted) context.go('/onboarding');
    } catch (_) {
      if (mounted) setState(() => _error = AppLocalizations.of(context)!.appLockSetupFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dark = AminaTheme.isDark(context);
    final capability = _capability;
    final supported = capability == AppLockCapability.supported;

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        fit: StackFit.expand,
        children: [
          _SecurityBackdrop(isDark: dark),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(24, 22, 24, 26),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 430),
                  child: Column(
                    children: [
                      SizedBox(
                        width: 118,
                        height: 118,
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
                        padding: const EdgeInsetsDirectional.fromSTEB(24, 24, 24, 23),
                        decoration: BoxDecoration(
                          color: AminaTheme.surface(context).withValues(alpha: dark ? .98 : .97),
                          borderRadius: BorderRadius.circular(26),
                          border: Border.all(color: AminaTheme.divider(context).withValues(alpha: dark ? .70 : .56)),
                          boxShadow: dark
                              ? AminaTheme.shadowDark
                              : const [
                                  BoxShadow(
                                    color: Color(0x1411423A),
                                    blurRadius: 34,
                                    spreadRadius: -10,
                                    offset: Offset(0, 18),
                                  ),
                                ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Align(
                              alignment: AlignmentDirectional.centerStart,
                              child: Container(
                                padding: const EdgeInsetsDirectional.fromSTEB(10, 6, 10, 6),
                                decoration: BoxDecoration(
                                  color: AminaTheme.teal50.withValues(alpha: dark ? .10 : .92),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(color: AminaTheme.teal200.withValues(alpha: dark ? .30 : .72)),
                                ),
                                child: Text(
                                  l10n.appLockEyebrow,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: .7,
                                    color: dark ? AminaTheme.teal400 : AminaTheme.teal700,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 18),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 48,
                                  height: 48,
                                  decoration: BoxDecoration(
                                    color: AminaTheme.teal50.withValues(alpha: dark ? .12 : 1),
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    Icons.fingerprint_rounded,
                                    color: dark ? AminaTheme.teal400 : AminaTheme.teal700,
                                    size: 27,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        l10n.appLockSetupTitle,
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
                                      const SizedBox(height: 8),
                                      Text(
                                        l10n.appLockSetupSubtitle,
                                        style: TextStyle(
                                          fontSize: 13.5,
                                          height: 1.45,
                                          color: dark ? AminaTheme.dark300 : AminaTheme.ink500,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 22),
                            _InfoRow(icon: Icons.wifi_off_rounded, text: l10n.appLockOffline),
                            const SizedBox(height: 10),
                            _InfoRow(icon: Icons.verified_user_outlined, text: l10n.appLockDeviceSecurity),
                            if (capability == null) ...[
                              const SizedBox(height: 18),
                              Row(
                                children: [
                                  const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(child: Text(l10n.appLockChecking)),
                                ],
                              ),
                            ] else if (!supported) ...[
                              const SizedBox(height: 18),
                              _WarningBox(
                                text: capability == AppLockCapability.insecureContext
                                    ? l10n.appLockInsecureContext
                                    : l10n.appLockUnavailable,
                              ),
                            ],
                            if (_error != null) ...[
                              const SizedBox(height: 16),
                              _WarningBox(text: _error!),
                            ],
                            const SizedBox(height: 22),
                            FilledButton.icon(
                              key: const Key('app-lock-activate'),
                              onPressed: supported && !_busy ? _activate : null,
                              icon: _busy
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                    )
                                  : const Icon(Icons.lock_rounded),
                              label: Text(l10n.appLockActivate),
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

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _InfoRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(12, 11, 12, 11),
      decoration: BoxDecoration(
        color: dark ? AminaTheme.darkCard : const Color(0xFFF3F9F7),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: dark ? AminaTheme.teal400 : AminaTheme.teal700),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 12.5, height: 1.4, color: dark ? AminaTheme.dark200 : AminaTheme.ink700),
            ),
          ),
        ],
      ),
    );
  }
}

class _WarningBox extends StatelessWidget {
  final String text;

  const _WarningBox({required this.text});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AminaTheme.dangerBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AminaTheme.dangerFg.withValues(alpha: .18)),
        ),
        child: Text(
          text,
          style: const TextStyle(fontSize: 12.5, height: 1.4, color: AminaTheme.dangerFg),
        ),
      );
}

class _SecurityBackdrop extends StatelessWidget {
  final bool isDark;

  const _SecurityBackdrop({required this.isDark});

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: isDark ? AminaTheme.darkPaper : AminaTheme.paper,
          gradient: isDark
              ? null
              : const RadialGradient(
                  center: Alignment(-.75, -.75),
                  radius: 1.25,
                  colors: [Color(0xFFDDF8F1), Color(0xFFF7FBFA)],
                  stops: [0, .70],
                ),
        ),
      );
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
