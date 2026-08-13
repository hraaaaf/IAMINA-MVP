import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../services/api_client.dart';
import '../../data/drift/database.dart';
import '../../core/theme/app_theme.dart';
import 'login_logo_asset.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl    = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscure   = true;
  bool _isLoading = false;
  String? _error;

  Future<void> _handleForgotPassword() async {
    final emailForReset = _emailCtrl.text.trim().isNotEmpty
        ? _emailCtrl.text.trim()
        : null;
    final emailCtrl = TextEditingController(text: emailForReset);
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
              Text(dl10n.resetPasswordDescription, style: const TextStyle(fontSize: 13, height: 1.45)),
              const SizedBox(height: 14),
              _Field(controller: emailCtrl, hint: dl10n.emailPlaceholder, keyboardType: TextInputType.emailAddress),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(dl10n.cancel)),
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
      final auth = context.read<AuthService>();
      await auth.sendPasswordResetEmail(email);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.resetEmailSent), backgroundColor: AminaTheme.teal600, behavior: SnackBarBehavior.floating),
      );
    } catch (_) {
      if (mounted) setState(() => _error = l10n.emailNotFound);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleSignup() async {
    final l10n = AppLocalizations.of(context)!;
    final emailCtrl    = TextEditingController(text: _emailCtrl.text);
    final passwordCtrl = TextEditingController();
    final confirmCtrl  = TextEditingController();
    bool obscure = true;
    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) {
          return AlertDialog(
            title: const Text('Créer un compte'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _FieldLabel(l10n.emailLabel),
                const SizedBox(height: 6),
                _Field(controller: emailCtrl, hint: l10n.emailPlaceholder, keyboardType: TextInputType.emailAddress),
                const SizedBox(height: 12),
                _FieldLabel(l10n.passwordLabel),
                const SizedBox(height: 6),
                _Field(
                  controller: passwordCtrl,
                  hint: '••••••••  (min. 6 caractères)',
                  obscureText: obscure,
                  suffix: IconButton(
                    onPressed: () => setDlgState(() => obscure = !obscure),
                    icon: Icon(obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 16),
                  ),
                ),
                const SizedBox(height: 12),
                _FieldLabel('Confirmer le mot de passe'),
                const SizedBox(height: 6),
                _Field(controller: confirmCtrl, hint: '••••••••', obscureText: obscure),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.cancel)),
              FilledButton(
                style: FilledButton.styleFrom(backgroundColor: AminaTheme.teal500),
                onPressed: () async {
                  final email    = emailCtrl.text.trim();
                  final password = passwordCtrl.text;
                  final confirm  = confirmCtrl.text;
                  if (email.isEmpty || password.isEmpty) return;
                  if (password != confirm) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Les mots de passe ne correspondent pas'), behavior: SnackBarBehavior.floating),
                    );
                    return;
                  }
                  Navigator.pop(ctx);
                  setState(() { _isLoading = true; _error = null; });
                  try {
                    final auth = context.read<AuthService>();
                    await auth.registerWithEmail(email, password);
                    if (mounted) context.go('/onboarding');
                  } catch (e) {
                    if (mounted) setState(() => _error = 'Échec de la création du compte — vérifiez l\'e-mail et le mot de passe.');
                  } finally {
                    if (mounted) setState(() => _isLoading = false);
                  }
                },
                child: const Text('Créer'),
              ),
            ],
          );
        },
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
        final count = await db.countLogs();
        if (count == 0) await db.seedDemoData();
      } else {
        await auth.signInWithEmail(_emailCtrl.text.trim(), _passwordCtrl.text);
      }
      if (mounted) context.go('/dashboard');
    } catch (e) {
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
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _LoginBackdrop(),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(24, 14, 24, 28),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 400),
                  child: Column(
                    children: [
                      _Brand(),
                      const SizedBox(height: 18),
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
                      ),
                      const SizedBox(height: 22),
                      _Footer(),
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
    final isDark = AminaTheme.isDark(context);
    return IgnorePointer(child: CustomPaint(painter: _LoginBackdropPainter(isDark: isDark)));
  }
}

class _LoginBackdropPainter extends CustomPainter {
  final bool isDark;
  const _LoginBackdropPainter({required this.isDark});
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = isDark ? AminaTheme.darkPaper : AminaTheme.paper);
    if (isDark) return;
    void drawGlow(Offset center, double radius, double opacity) {
      final rect = Rect.fromCircle(center: center, radius: radius);
      canvas.drawCircle(
        center,
        radius,
        Paint()..shader = RadialGradient(
          colors: [AminaTheme.teal100.withValues(alpha: opacity), AminaTheme.teal50.withValues(alpha: opacity * 0.42), Colors.transparent],
          stops: const [0, 0.48, 1],
        ).createShader(rect),
      );
    }
    drawGlow(Offset(-size.width * 0.07, size.height * 0.17), size.width * 0.43, 0.58);
    drawGlow(Offset(size.width * 1.02, size.height * 0.20), size.width * 0.30, 0.46);
    drawGlow(Offset(size.width * 0.92, size.height * 0.73), size.width * 0.34, 0.22);
    final wave = Path()
      ..moveTo(0, size.height * 0.93)
      ..cubicTo(size.width * 0.20, size.height * 0.95, size.width * 0.45, size.height * 1.02, size.width * 0.68, size.height * 0.975)
      ..cubicTo(size.width * 0.84, size.height * 0.94, size.width * 0.94, size.height * 0.90, size.width, size.height * 0.89)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(
      wave,
      Paint()..shader = const LinearGradient(
        colors: [Color(0xFFDDF8F1), Color(0xFFB9F0E5)],
        begin: AlignmentDirectional.topStart,
        end: AlignmentDirectional.bottomEnd,
      ).createShader(Rect.fromLTWH(0, size.height * 0.86, size.width, size.height * 0.14)),
    );
    final highlight = Path()
      ..moveTo(0, size.height * 0.928)
      ..cubicTo(size.width * 0.20, size.height * 0.95, size.width * 0.45, size.height * 1.01, size.width * 0.68, size.height * 0.968)
      ..cubicTo(size.width * 0.84, size.height * 0.935, size.width * 0.94, size.height * 0.897, size.width, size.height * 0.885);
    canvas.drawPath(highlight, Paint()..color = Colors.white.withValues(alpha: 0.86)..style = PaintingStyle.stroke..strokeWidth = 1.2);
  }
  @override
  bool shouldRepaint(covariant _LoginBackdropPainter oldDelegate) => oldDelegate.isDark != isDark;
}

class _Brand extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Semantics(
      label: l10n.appTitle,
      image: true,
      child: SizedBox(
        width: 138,
        height: 124,
        child: Image.memory(
          loginLogoBytes,
          fit: BoxFit.contain,
          filterQuality: FilterQuality.high,
          gaplessPlayback: true,
        ),
      ),
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
  const _LoginCard({required this.emailCtrl, required this.passwordCtrl, required this.obscure, required this.onToggleObscure, required this.error, required this.isLoading, required this.onSubmit, required this.onForgotPassword, required this.onDemo, required this.onSignup});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isDark = AminaTheme.isDark(context);
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(22, 24, 22, 22),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context).withValues(alpha: isDark ? 0.98 : 0.96),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: AminaTheme.divider(context).withValues(alpha: isDark ? 0.72 : 0.58)),
        boxShadow: isDark ? AminaTheme.shadowDark : const [
          BoxShadow(color: Color(0x0F0D1A17), blurRadius: 34, spreadRadius: -10, offset: Offset(0, 18)),
          BoxShadow(color: Color(0x080D1A17), blurRadius: 10, spreadRadius: -4, offset: Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(l10n.welcome, style: TextStyle(fontSize: 25, height: 1.08, fontWeight: FontWeight.w700, letterSpacing: -0.6, color: isDark ? AminaTheme.dark100 : AminaTheme.ink900)),
          const SizedBox(height: 6),
          Text(l10n.loginSubtitle, style: TextStyle(fontSize: 13.5, height: 1.4, color: isDark ? AminaTheme.dark300 : AminaTheme.ink500)),
          const SizedBox(height: 20),
          _FieldLabel(l10n.emailLabel),
          const SizedBox(height: 6),
          _Field(controller: emailCtrl, hint: l10n.emailPlaceholder, keyboardType: TextInputType.emailAddress, prefix: const Icon(Icons.mail_outline_rounded)),
          const SizedBox(height: 14),
          _FieldLabel(l10n.passwordLabel),
          const SizedBox(height: 6),
          _Field(
            controller: passwordCtrl,
            hint: '••••••••',
            obscureText: obscure,
            prefix: const Icon(Icons.lock_outline_rounded),
            suffix: IconButton(
              onPressed: onToggleObscure,
              icon: Icon(obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 19, color: AminaTheme.ink400),
            ),
            onSubmit: (_) => onSubmit(),
          ),
          const SizedBox(height: 4),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: onForgotPassword,
              style: TextButton.styleFrom(padding: const EdgeInsetsDirectional.fromSTEB(6, 2, 6, 2), minimumSize: const Size(44, 40), tapTargetSize: MaterialTapTargetSize.shrinkWrap),
              child: Text(l10n.forgotPassword, style: const TextStyle(fontSize: 12.5, color: AminaTheme.teal700, fontWeight: FontWeight.w600)),
            ),
          ),
          if (error != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(color: AminaTheme.dangerBg, borderRadius: BorderRadius.circular(10)),
              child: Row(children: [
                const Icon(Icons.error_outline, size: 14, color: AminaTheme.dangerFg),
                const SizedBox(width: 8),
                Expanded(child: Text(error!, style: const TextStyle(fontSize: 12, color: AminaTheme.dangerFg))),
              ]),
            ),
          ],
          const SizedBox(height: 12),
          _PrimaryLoginButton(isLoading: isLoading, label: l10n.signIn, onTap: () => onSubmit()),
          const SizedBox(height: 16),
          _DemoButton(isLoading: isLoading, onTap: onDemo),
          const SizedBox(height: 14),
          _SignupRow(isLoading: isLoading, onTap: onSignup),
        ],
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String text;
  _FieldLabel(this.text);
  @override
  Widget build(BuildContext context) {
    final isDark = AminaTheme.isDark(context);
    return Text(text, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: isDark ? AminaTheme.dark200 : AminaTheme.ink700));
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
  const _Field({required this.controller, required this.hint, this.obscureText = false, this.keyboardType, this.prefix, this.suffix, this.onSubmit});

  @override
  Widget build(BuildContext context) {
    final isDark = AminaTheme.isDark(context);
    final iconColor = isDark ? AminaTheme.dark300 : AminaTheme.ink400;
    return SizedBox(
      height: 52,
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onSubmitted: onSubmit,
        style: TextStyle(fontSize: 14, color: isDark ? AminaTheme.dark100 : AminaTheme.ink900),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(color: AminaTheme.textSecondary(context), fontSize: 14),
          filled: true,
          fillColor: isDark ? AminaTheme.darkCard : Colors.white.withValues(alpha: 0.86),
          contentPadding: const EdgeInsetsDirectional.fromSTEB(15, 14, 15, 14),
          prefixIcon: prefix == null ? null : IconTheme(data: IconThemeData(size: 20, color: iconColor), child: prefix!),
          suffixIcon: suffix,
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: AminaTheme.divider(context))),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AminaTheme.teal500, width: 1.4)),
          errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AminaTheme.dangerFg)),
        ),
      ),
    );
  }
}

class _PrimaryLoginButton extends StatelessWidget {
  final bool isLoading;
  final String label;
  final VoidCallback onTap;
  const _PrimaryLoginButton({required this.isLoading, required this.label, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF176B5D), Color(0xFF22877A)], begin: AlignmentDirectional.centerStart, end: AlignmentDirectional.centerEnd),
        borderRadius: BorderRadius.circular(15),
        boxShadow: const [BoxShadow(color: Color(0x24176B5D), blurRadius: 18, spreadRadius: -8, offset: Offset(0, 10))],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(15),
        child: InkWell(
          onTap: isLoading ? null : onTap,
          borderRadius: BorderRadius.circular(15),
          child: SizedBox(
            height: 52,
            child: Center(
              child: isLoading
                  ? const SizedBox(width: 19, height: 19, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : Row(mainAxisSize: MainAxisSize.min, children: [
                      const Icon(Icons.lock_outline_rounded, size: 18, color: Colors.white),
                      const SizedBox(width: 9),
                      Text(label, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w700, color: Colors.white)),
                    ]),
            ),
          ),
        ),
      ),
    );
  }
}

class _DemoButton extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;
  const _DemoButton({required this.isLoading, required this.onTap});
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isDark = AminaTheme.isDark(context);
    return Column(children: [
      Row(children: [
        Expanded(child: Divider(color: AminaTheme.divider(context))),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Container(
            width: 30,
            height: 30,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: AminaTheme.surface(context), shape: BoxShape.circle, border: Border.all(color: AminaTheme.divider(context))),
            child: Text(l10n.or, style: TextStyle(fontSize: 11.5, color: isDark ? AminaTheme.dark300 : AminaTheme.ink400)),
          ),
        ),
        Expanded(child: Divider(color: AminaTheme.divider(context))),
      ]),
      const SizedBox(height: 13),
      SizedBox(
        width: double.infinity,
        height: 52,
        child: OutlinedButton.icon(
          onPressed: isLoading ? null : onTap,
          icon: const Icon(Icons.eco_outlined, size: 18, color: AminaTheme.teal700),
          label: Text(l10n.demoAccess, style: const TextStyle(color: AminaTheme.teal700, fontWeight: FontWeight.w700, fontSize: 13.5)),
          style: OutlinedButton.styleFrom(
            side: BorderSide(color: isDark ? AminaTheme.teal600 : AminaTheme.teal200),
            backgroundColor: AminaTheme.surface(context).withValues(alpha: isDark ? 0.54 : 0.78),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          ),
        ),
      ),
    ]);
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
        Text('Pas encore de compte ?', style: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context))),
        TextButton(
          onPressed: isLoading ? null : onTap,
          style: TextButton.styleFrom(minimumSize: const Size(44, 40), padding: const EdgeInsetsDirectional.fromSTEB(6, 2, 6, 2), tapTargetSize: MaterialTapTargetSize.shrinkWrap),
          child: const Text('Créer un compte', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AminaTheme.teal700, decoration: TextDecoration.underline, decorationThickness: 1.2)),
        ),
      ],
    );
  }
}

class _Footer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final isDark = AminaTheme.isDark(context);
    final foreground = isDark ? AminaTheme.dark300 : AminaTheme.ink500;
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 300),
      child: Column(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AminaTheme.teal50.withValues(alpha: isDark ? 0.10 : 0.92),
              shape: BoxShape.circle,
              border: Border.all(color: AminaTheme.teal200.withValues(alpha: isDark ? 0.38 : 0.72)),
            ),
            child: Icon(Icons.shield_outlined, size: 20, color: isDark ? AminaTheme.teal400 : AminaTheme.teal700),
          ),
          const SizedBox(height: 8),
          Text(
            AppLocalizations.of(context)!.dataPrivacyNote,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11.5, height: 1.35, color: foreground),
          ),
        ],
      ),
    );
  }
}