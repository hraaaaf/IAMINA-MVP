import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/api_client.dart';
import '../../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscure = true;
  bool _isLoading = false;
  String? _error;

  Future<void> _handleForgotPassword() async {
    final emailCtrl = TextEditingController(
      text: _emailCtrl.text.trim().isNotEmpty ? _emailCtrl.text.trim() : null,
    );
    final l10n = AppLocalizations.of(context)!;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        final dl10n = AppLocalizations.of(ctx)!;
        return AlertDialog(
          title: Text(dl10n.resetPassword),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(dl10n.resetPasswordDescription,
                  style: const TextStyle(fontSize: 13, height: 1.45)),
              const SizedBox(height: 14),
              _Field(
                controller: emailCtrl,
                hint: dl10n.emailPlaceholder,
                keyboardType: TextInputType.emailAddress,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(dl10n.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: FilledButton.styleFrom(backgroundColor: AminaTheme.teal500),
              child: Text(dl10n.send),
            ),
          ],
        );
      },
    );
    if (confirmed != true || !mounted) return;
    final email = emailCtrl.text.trim();
    if (email.isEmpty) return;
    setState(() { _isLoading = true; _error = null; });
    try {
      await context.read<AuthService>().sendPasswordResetEmail(email);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(l10n.resetEmailSent),
          backgroundColor: AminaTheme.teal600,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (_) {
      if (mounted) setState(() => _error = l10n.emailNotFound);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleSignup() async {
    final l10n = AppLocalizations.of(context)!;
    final emailCtrl = TextEditingController(text: _emailCtrl.text);
    final passwordCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    bool obscure = true;
    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Créer un compte'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _FieldLabel(l10n.emailLabel),
              const SizedBox(height: 6),
              _Field(
                controller: emailCtrl,
                hint: l10n.emailPlaceholder,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              _FieldLabel(l10n.passwordLabel),
              const SizedBox(height: 6),
              _Field(
                controller: passwordCtrl,
                hint: '••••••••  (min. 6 caractères)',
                obscureText: obscure,
                suffix: IconButton(
                  onPressed: () => setDlgState(() => obscure = !obscure),
                  icon: Icon(
                    obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                    size: 16,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const _FieldLabel('Confirmer le mot de passe'),
              const SizedBox(height: 6),
              _Field(controller: confirmCtrl, hint: '••••••••', obscureText: obscure),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.cancel)),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: AminaTheme.teal500),
              onPressed: () async {
                final email = emailCtrl.text.trim();
                final password = passwordCtrl.text;
                final confirm = confirmCtrl.text;
                if (email.isEmpty || password.isEmpty) return;
                if (password != confirm) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Les mots de passe ne correspondent pas'),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                  return;
                }
                Navigator.pop(ctx);
                setState(() { _isLoading = true; _error = null; });
                try {
                  await context.read<AuthService>().registerWithEmail(email, password);
                  if (mounted) context.go('/onboarding');
                } catch (_) {
                  if (mounted) {
                    setState(() => _error =
                        'Échec de la création du compte — vérifiez l\'e-mail et le mot de passe.');
                  }
                } finally {
                  if (mounted) setState(() => _isLoading = false);
                }
              },
              child: const Text('Créer'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogin({bool isDemo = false}) async {
    setState(() { _isLoading = true; _error = null; });
    final auth = context.read<AuthService>();
    final db = context.read<AppDatabase>();
    final api = context.read<ApiClient>();
    try {
      if (isDemo) {
        await auth.signInAnonymously();
        await api.seedDemoData();
        if (await db.countLogs() == 0) await db.seedDemoData();
      } else {
        await auth.signInWithEmail(_emailCtrl.text.trim(), _passwordCtrl.text);
      }
      if (mounted) context.go('/dashboard');
    } catch (_) {
      if (mounted) setState(() => _error = AppLocalizations.of(context)!.loginError);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final fr = Localizations.localeOf(context).languageCode == 'fr';
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _LoginBackdrop(),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(24, 24, 24, 15),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 390),
                  child: Column(
                    children: [
                      const _Brand(),
                      const SizedBox(height: 56),
                      _LoginCard(
                        emailCtrl: _emailCtrl,
                        passwordCtrl: _passwordCtrl,
                        obscure: _obscure,
                        onToggleObscure: () => setState(() => _obscure = !_obscure),
                        error: _error,
                        isLoading: _isLoading,
                        onSubmit: _handleLogin,
                        onForgotPassword: _handleForgotPassword,
                        onDemo: () => _handleLogin(isDemo: true),
                        onSignup: _handleSignup,
                        welcome: fr ? 'Bienvenue' : l10n.welcome,
                        subtitle: fr
                            ? 'Connectez-vous pour accéder à votre compagnon intelligent du diabète'
                            : l10n.loginSubtitle,
                        demoLabel: fr ? 'Accès démo' : l10n.demoAccess,
                      ),
                      const SizedBox(height: 14),
                      _Footer(
                        label: fr
                            ? 'Vos données de santé sont sécurisées et confidentielles.'
                            : l10n.dataPrivacyNote,
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

class _LoginBackdrop extends StatelessWidget {
  const _LoginBackdrop();
  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        painter: _LoginBackdropPainter(isDark: AminaTheme.isDark(context)),
      ),
    );
  }
}

class _LoginBackdropPainter extends CustomPainter {
  final bool isDark;
  const _LoginBackdropPainter({required this.isDark});
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(
      Offset.zero & size,
      Paint()..color = isDark ? AminaTheme.darkPaper : AminaTheme.paper,
    );
    if (isDark) return;
    void glow(Offset center, double radius, Color color) {
      canvas.drawCircle(
        center,
        radius,
        Paint()
          ..shader = RadialGradient(
            colors: [color, color.withValues(alpha: .20), Colors.transparent],
            stops: const [0, .48, 1],
          ).createShader(Rect.fromCircle(center: center, radius: radius)),
      );
    }
    glow(Offset(-size.width * .10, size.height * .18), size.width * .46,
        const Color(0x6628D8C2));
    glow(Offset(size.width * 1.05, size.height * .20), size.width * .30,
        const Color(0x5537E4D0));
    glow(Offset(size.width * .98, size.height * .72), size.width * .32,
        const Color(0x3328D8C2));

    final wave = Path()
      ..moveTo(0, size.height * .93)
      ..cubicTo(size.width * .20, size.height * .95, size.width * .44,
          size.height * 1.02, size.width * .66, size.height * .975)
      ..cubicTo(size.width * .82, size.height * .94, size.width * .94,
          size.height * .90, size.width, size.height * .885)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(
      wave,
      Paint()
        ..shader = const LinearGradient(
          colors: [Color(0xFFD7F8F2), Color(0xFF9DE8DD)],
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
        ).createShader(Rect.fromLTWH(0, size.height * .86, size.width, size.height * .14)),
    );
  }
  @override
  bool shouldRepaint(covariant _LoginBackdropPainter oldDelegate) =>
      oldDelegate.isDark != isDark;
}

class _Brand extends StatelessWidget {
  const _Brand();
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final logo = kIsWeb
        ? Image.network(
            'assets/assets/images/logo_amina.png',
            fit: BoxFit.contain,
            webHtmlElementStrategy: WebHtmlElementStrategy.fallback,
            errorBuilder: (_, __, ___) => const _BrandFallback(),
          )
        : Image.asset(
            'assets/images/logo_amina.png',
            fit: BoxFit.contain,
            filterQuality: FilterQuality.high,
            errorBuilder: (_, __, ___) => const _BrandFallback(),
          );
    return Semantics(
      label: l10n.appTitle,
      image: true,
      child: SizedBox(width: 140, height: 176, child: logo),
    );
  }
}

class _BrandFallback extends StatelessWidget {
  const _BrandFallback();
  @override
  Widget build(BuildContext context) {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text('IA', style: TextStyle(
          fontFamily: 'Georgia', fontSize: 58, height: .92,
          fontWeight: FontWeight.w600, color: Color(0xFF075A45),
        )),
        SizedBox(height: 6),
        Text('آمينة', textDirection: TextDirection.rtl, style: TextStyle(
          fontSize: 35, height: 1, fontWeight: FontWeight.w500,
          color: Color(0xFF075A45),
        )),
      ],
    );
  }
}

class _LoginCard extends StatelessWidget {
  final TextEditingController emailCtrl;
  final TextEditingController passwordCtrl;
  final bool obscure;
  final VoidCallback onToggleObscure;
  final String? error;
  final bool isLoading;
  final void Function({bool isDemo}) onSubmit;
  final VoidCallback onForgotPassword;
  final VoidCallback onDemo;
  final VoidCallback onSignup;
  final String welcome;
  final String subtitle;
  final String demoLabel;
  const _LoginCard({
    required this.emailCtrl,
    required this.passwordCtrl,
    required this.obscure,
    required this.onToggleObscure,
    required this.error,
    required this.isLoading,
    required this.onSubmit,
    required this.onForgotPassword,
    required this.onDemo,
    required this.onSignup,
    required this.welcome,
    required this.subtitle,
    required this.demoLabel,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dark = AminaTheme.isDark(context);
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(20, 20, 20, 20),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context).withValues(alpha: dark ? .98 : .965),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(
          color: dark
              ? AminaTheme.divider(context).withValues(alpha: .58)
              : Colors.white.withValues(alpha: .86),
        ),
        boxShadow: dark ? AminaTheme.shadowDark : const [
          BoxShadow(color: Color(0x1211423A), blurRadius: 36,
              spreadRadius: -12, offset: Offset(0, 18)),
          BoxShadow(color: Color(0x090D1A17), blurRadius: 12,
              spreadRadius: -5, offset: Offset(0, 5)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(welcome, style: TextStyle(
            fontFamily: 'Georgia',
            fontFamilyFallback: const ['Times New Roman', 'serif'],
            fontSize: 30, height: 1.08, fontWeight: FontWeight.w700,
            letterSpacing: -.7,
            color: dark ? AminaTheme.dark100 : const Color(0xFF073D31),
          )),
          const SizedBox(height: 6),
          Text(subtitle, style: TextStyle(
            fontSize: 13, height: 1.35,
            color: dark ? AminaTheme.dark300 : const Color(0xFF566B68),
          )),
          const SizedBox(height: 16),
          _FieldLabel(l10n.emailLabel),
          const SizedBox(height: 5),
          _Field(
            controller: emailCtrl,
            hint: l10n.emailPlaceholder,
            keyboardType: TextInputType.emailAddress,
            prefix: const Icon(Icons.mail_outline_rounded),
          ),
          const SizedBox(height: 12),
          _FieldLabel(l10n.passwordLabel),
          const SizedBox(height: 5),
          _Field(
            controller: passwordCtrl,
            hint: '••••••••••••',
            obscureText: obscure,
            prefix: const Icon(Icons.lock_outline_rounded),
            suffix: IconButton(
              onPressed: onToggleObscure,
              icon: Icon(
                obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                size: 20, color: AminaTheme.ink400,
              ),
            ),
            onSubmit: (_) => onSubmit(),
          ),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: onForgotPassword,
              style: TextButton.styleFrom(
                padding: const EdgeInsetsDirectional.fromSTEB(6, 0, 0, 0),
                minimumSize: const Size(44, 32),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(l10n.forgotPassword, style: const TextStyle(
                fontSize: 12.5, color: Color(0xFF0B735F),
                fontWeight: FontWeight.w500,
              )),
            ),
          ),
          if (error != null) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: BoxDecoration(
                color: AminaTheme.dangerBg,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(children: [
                const Icon(Icons.error_outline, size: 14, color: AminaTheme.dangerFg),
                const SizedBox(width: 8),
                Expanded(child: Text(error!, style: const TextStyle(
                  fontSize: 12, color: AminaTheme.dangerFg,
                ))),
              ]),
            ),
          ],
          const SizedBox(height: 6),
          _PrimaryLoginButton(
            isLoading: isLoading,
            label: l10n.signIn,
            onTap: () => onSubmit(),
          ),
          const SizedBox(height: 10),
          _DividerOr(label: l10n.or),
          const SizedBox(height: 10),
          _DemoButton(isLoading: isLoading, label: demoLabel, onTap: onDemo),
          const SizedBox(height: 8),
          _SignupRow(isLoading: isLoading, onTap: onSignup),
        ],
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String text;
  const _FieldLabel(this.text);
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return Text(text, style: TextStyle(
      fontSize: 13.2, fontWeight: FontWeight.w600,
      color: dark ? AminaTheme.dark200 : const Color(0xFF075A45),
    ));
  }
}

class _Field extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final bool obscureText;
  final TextInputType? keyboardType;
  final Widget? prefix;
  final Widget? suffix;
  final void Function(String)? onSubmit;
  const _Field({
    required this.controller,
    required this.hint,
    this.obscureText = false,
    this.keyboardType,
    this.prefix,
    this.suffix,
    this.onSubmit,
  });
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final iconColor = dark ? AminaTheme.dark300 : const Color(0xFF0B735F);
    return SizedBox(
      height: 46,
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onSubmitted: onSubmit,
        style: TextStyle(
          fontSize: 14,
          color: dark ? AminaTheme.dark100 : AminaTheme.ink900,
        ),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(color: AminaTheme.textSecondary(context), fontSize: 14),
          filled: true,
          fillColor: dark ? AminaTheme.darkCard : Colors.white.withValues(alpha: .90),
          contentPadding: const EdgeInsetsDirectional.fromSTEB(14, 11, 14, 11),
          prefixIcon: prefix == null ? null : IconTheme(
            data: IconThemeData(size: 20, color: iconColor),
            child: prefix!,
          ),
          suffixIcon: suffix,
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFC5CECC), width: 1.15),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AminaTheme.teal500, width: 1.5),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AminaTheme.dangerFg, width: 1.2),
          ),
        ),
      ),
    );
  }
}

class _PrimaryLoginButton extends StatelessWidget {
  final bool isLoading;
  final String label;
  final VoidCallback onTap;
  const _PrimaryLoginButton({
    required this.isLoading,
    required this.label,
    required this.onTap,
  });
  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF075F4A), Color(0xFF027260)],
          begin: AlignmentDirectional.centerStart,
          end: AlignmentDirectional.centerEnd,
        ),
        borderRadius: BorderRadius.circular(14),
        boxShadow: const [
          BoxShadow(color: Color(0x2A075F4A), blurRadius: 18,
              spreadRadius: -8, offset: Offset(0, 10)),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          onTap: isLoading ? null : onTap,
          borderRadius: BorderRadius.circular(14),
          child: SizedBox(
            height: 48,
            child: Center(
              child: isLoading
                  ? const SizedBox(
                      width: 19, height: 19,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : Row(mainAxisSize: MainAxisSize.min, children: [
                      const Icon(Icons.lock_outline_rounded, size: 18, color: Colors.white),
                      const SizedBox(width: 10),
                      Text(label, style: const TextStyle(
                        fontSize: 15, fontWeight: FontWeight.w700, color: Colors.white,
                      )),
                    ]),
            ),
          ),
        ),
      ),
    );
  }
}

class _DividerOr extends StatelessWidget {
  final String label;
  const _DividerOr({required this.label});
  @override
  Widget build(BuildContext context) {
    final divider = AminaTheme.divider(context);
    return Row(children: [
      Expanded(child: Divider(color: divider, height: 1)),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10),
        child: Container(
          width: 28, height: 28, alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AminaTheme.surface(context),
            shape: BoxShape.circle,
            border: Border.all(color: divider),
          ),
          child: Text(label, style: TextStyle(
            fontSize: 11.5, color: AminaTheme.textSecondary(context),
          )),
        ),
      ),
      Expanded(child: Divider(color: divider, height: 1)),
    ]);
  }
}

class _DemoButton extends StatelessWidget {
  final bool isLoading;
  final String label;
  final VoidCallback onTap;
  const _DemoButton({required this.isLoading, required this.label, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 46,
      child: OutlinedButton.icon(
        onPressed: isLoading ? null : onTap,
        icon: const Icon(Icons.eco_outlined, size: 18, color: Color(0xFF075F4A)),
        label: Text(label, style: const TextStyle(
          color: Color(0xFF075F4A), fontWeight: FontWeight.w700, fontSize: 14,
        )),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Color(0xFF0B735F), width: 1.2),
          backgroundColor: AminaTheme.surface(context).withValues(alpha: .84),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
    );
  }
}

class _SignupRow extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;
  const _SignupRow({required this.isLoading, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 2,
      children: [
        Text('Pas encore de compte ?', style: TextStyle(
          fontSize: 12.8, color: AminaTheme.textSecondary(context),
        )),
        TextButton(
          onPressed: isLoading ? null : onTap,
          style: TextButton.styleFrom(
            minimumSize: const Size(44, 34),
            padding: const EdgeInsetsDirectional.fromSTEB(5, 0, 5, 0),
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: const Text('Créer un compte', style: TextStyle(
            fontSize: 12.8, fontWeight: FontWeight.w500,
            color: Color(0xFF0B735F), decoration: TextDecoration.underline,
            decorationThickness: 1.1,
          )),
        ),
      ],
    );
  }
}

class _Footer extends StatelessWidget {
  final String label;
  const _Footer({required this.label});
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final foreground = dark ? AminaTheme.dark300 : const Color(0xFF526865);
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 260),
      child: Column(children: [
        Container(
          width: 40, height: 40,
          decoration: BoxDecoration(
            color: const Color(0xFFE4F7F2).withValues(alpha: dark ? .10 : .92),
            shape: BoxShape.circle,
            border: Border.all(
              color: const Color(0xFFB8E9DE).withValues(alpha: dark ? .38 : .78),
            ),
          ),
          child: Icon(
            Icons.shield_outlined, size: 21,
            color: dark ? AminaTheme.teal400 : const Color(0xFF0B735F),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 11.5, height: 1.34, color: foreground),
        ),
      ]),
    );
  }
}
