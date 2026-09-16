import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/auth_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../services/auth_service.dart';

class LocalDeviceEnrollmentScreen extends StatefulWidget {
  const LocalDeviceEnrollmentScreen({super.key});

  @override
  State<LocalDeviceEnrollmentScreen> createState() =>
      _LocalDeviceEnrollmentScreenState();
}

class _LocalDeviceEnrollmentScreenState
    extends State<LocalDeviceEnrollmentScreen> {
  bool _isLoading = false;
  String? _error;

  Future<void> _configureDevice() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await context.read<AuthService>().enrollLocalDevice();
      if (mounted) context.go('/onboarding');
    } catch (_) {
      if (mounted) {
        setState(
          () => _error = AppLocalizations.of(context)!.localEnrollmentFailed,
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dark = AminaTheme.isDark(context);

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        fit: StackFit.expand,
        children: [
          _LocalFirstBackdrop(isDark: dark),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(24, 22, 24, 26),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Column(
                    children: [
                      Semantics(
                        label: l10n.appTitle,
                        image: true,
                        child: SizedBox(
                          width: 132,
                          height: 132,
                          child: Image.asset(
                            'assets/images/logo_amina.png',
                            fit: BoxFit.contain,
                            filterQuality: FilterQuality.high,
                            errorBuilder: (_, __, ___) => const _LogoFallback(),
                          ),
                        ),
                      ),
                      const SizedBox(height: 28),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsetsDirectional.fromSTEB(
                          24,
                          25,
                          24,
                          23,
                        ),
                        decoration: BoxDecoration(
                          color: AminaTheme.surface(context)
                              .withValues(alpha: dark ? .98 : .97),
                          borderRadius: BorderRadius.circular(26),
                          border: Border.all(
                            color: AminaTheme.divider(context)
                                .withValues(alpha: dark ? .70 : .56),
                          ),
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
                                padding: const EdgeInsetsDirectional.fromSTEB(
                                  10,
                                  6,
                                  10,
                                  6,
                                ),
                                decoration: BoxDecoration(
                                  color: AminaTheme.teal50.withValues(
                                    alpha: dark ? .10 : .92,
                                  ),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(
                                    color: AminaTheme.teal200.withValues(
                                      alpha: dark ? .30 : .72,
                                    ),
                                  ),
                                ),
                                child: Text(
                                  l10n.localEnrollmentEyebrow,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: .7,
                                    color: dark
                                        ? AminaTheme.teal400
                                        : AminaTheme.teal700,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 18),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 46,
                                  height: 46,
                                  decoration: BoxDecoration(
                                    color: AminaTheme.teal50.withValues(
                                      alpha: dark ? .12 : 1,
                                    ),
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    Icons.phonelink_lock_outlined,
                                    color: dark
                                        ? AminaTheme.teal400
                                        : AminaTheme.teal700,
                                    size: 23,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        l10n.localEnrollmentTitle,
                                        style: TextStyle(
                                          fontFamily: 'Georgia',
                                          fontFamilyFallback: const [
                                            'Times New Roman',
                                            'serif',
                                          ],
                                          fontSize: 27,
                                          height: 1.08,
                                          fontWeight: FontWeight.w700,
                                          letterSpacing: -.5,
                                          color: dark
                                              ? AminaTheme.dark100
                                              : const Color(0xFF073D31),
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        l10n.localEnrollmentSubtitle,
                                        style: TextStyle(
                                          fontSize: 13.5,
                                          height: 1.45,
                                          color: dark
                                              ? AminaTheme.dark300
                                              : AminaTheme.ink500,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 22),
                            _TruthRow(
                              icon: Icons.wifi_off_rounded,
                              text: l10n.localEnrollmentOffline,
                            ),
                            const SizedBox(height: 10),
                            _TruthRow(
                              icon: Icons.shield_outlined,
                              text: l10n.localEnrollmentSecurity,
                            ),
                            if (_error != null) ...[
                              const SizedBox(height: 16),
                              Container(
                                padding: const EdgeInsets.all(11),
                                decoration: BoxDecoration(
                                  color: AminaTheme.dangerBg,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _error!,
                                  style: const TextStyle(
                                    fontSize: 12.5,
                                    color: AminaTheme.dangerFg,
                                  ),
                                ),
                              ),
                            ],
                            const SizedBox(height: 22),
                            FilledButton.icon(
                              onPressed: _isLoading ? null : _configureDevice,
                              icon: _isLoading
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: Colors.white,
                                      ),
                                    )
                                  : const Icon(Icons.arrow_forward_rounded),
                              label: Text(l10n.localEnrollmentAction),
                              style: FilledButton.styleFrom(
                                minimumSize: const Size.fromHeight(52),
                                backgroundColor: AminaTheme.teal700,
                                foregroundColor: Colors.white,
                                textStyle: const TextStyle(
                                  fontSize: 14.5,
                                  fontWeight: FontWeight.w700,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(15),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        l10n.localEnrollmentFooter,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 11.5,
                          height: 1.4,
                          color: AminaTheme.textSecondary(context),
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

class _TruthRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _TruthRow({required this.icon, required this.text});

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
          Icon(
            icon,
            size: 18,
            color: dark ? AminaTheme.teal400 : AminaTheme.teal700,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 12.5,
                height: 1.4,
                color: dark ? AminaTheme.dark200 : AminaTheme.ink700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LocalFirstBackdrop extends StatelessWidget {
  final bool isDark;

  const _LocalFirstBackdrop({required this.isDark});

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
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
}

class _LogoFallback extends StatelessWidget {
  const _LogoFallback();

  @override
  Widget build(BuildContext context) {
    return const Center(
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
}
