import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../services/api_client.dart';
import '../../data/drift/database.dart';
import '../../core/theme/app_theme.dart';

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
    // Pre-fill with email already typed, or ask for it.
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
              Text(
                dl10n.resetPasswordDescription,
                style: const TextStyle(fontSize: 13, height: 1.45),
              ),
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
      final auth = context.read<AuthService>();
      await auth.sendPasswordResetEmail(email);
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
        // Anonymous sign-in — no Firebase account needed for the demo.
        await auth.signInAnonymously();
        // Seed backend (creates PatientProfile + 30 days of logs) and local Drift DB.
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
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              children: [
                _Brand(),
                const SizedBox(height: 40),
                _LoginCard(
                  emailCtrl: _emailCtrl,
                  passwordCtrl: _passwordCtrl,
                  obscure: _obscure,
                  onToggleObscure: () => setState(() => _obscure = !_obscure),
                  error: _error,
                  isLoading: _isLoading,
                  onSubmit: _handleLogin,
                  onForgotPassword: _handleForgotPassword,
                ),
                const SizedBox(height: 16),
                _SignupRow(isLoading: _isLoading, onTap: _handleSignup),
                const SizedBox(height: 20),
                _DemoButton(isLoading: _isLoading, onTap: () => _handleLogin(isDemo: true)),
                const SizedBox(height: 32),
                _Footer(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── Brand ─────────────────────────────────────────────────────────────────────

class _Brand extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      children: [
        Semantics(
          label: l10n.appTitle,
          image: true,
          child: Image.asset(
            'assets/images/logo_amina.png',
            width: 160,
            height: 160,
            fit: BoxFit.contain,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          l10n.appTitle,
          style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AminaTheme.ink900, letterSpacing: -0.8),
        ),
        const SizedBox(height: 6),
        Text(
          l10n.appTagline,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 13, color: AminaTheme.ink500, height: 1.4),
        ),
      ],
    );
  }
}

// ── Login card ────────────────────────────────────────────────────────────────

class _LoginCard extends StatelessWidget {
  final TextEditingController emailCtrl;
  final TextEditingController passwordCtrl;
  final bool obscure;
  final VoidCallback onToggleObscure;
  final String? error;
  final bool isLoading;
  final void Function({bool isDemo}) onSubmit;
  final VoidCallback onForgotPassword;

  const _LoginCard({
    required this.emailCtrl,
    required this.passwordCtrl,
    required this.obscure,
    required this.onToggleObscure,
    required this.error,
    required this.isLoading,
    required this.onSubmit,
    required this.onForgotPassword,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
        border: Border.all(color: AminaTheme.divider(context)),
        boxShadow: AminaTheme.shadowClinicalLg,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            l10n.welcome,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AminaTheme.ink900),
          ),
          const SizedBox(height: 6),
          Text(
            l10n.loginSubtitle,
            style: const TextStyle(fontSize: 13, color: AminaTheme.ink500),
          ),
          const SizedBox(height: 24),

          // Email
          _FieldLabel(l10n.emailLabel),
          const SizedBox(height: 6),
          _Field(
            controller: emailCtrl,
            hint: l10n.emailPlaceholder,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: 16),

          // Password
          _FieldLabel(l10n.passwordLabel),
          const SizedBox(height: 6),
          _Field(
            controller: passwordCtrl,
            hint: '••••••••',
            obscureText: obscure,
            suffix: IconButton(
              onPressed: onToggleObscure,
              icon: Icon(obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 18, color: AminaTheme.ink400),
            ),
            onSubmit: (_) => onSubmit(),
          ),

          const SizedBox(height: 8),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: onForgotPassword,
              style: TextButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                minimumSize: Size.zero,
              ),
              child: Text(l10n.forgotPassword, style: const TextStyle(fontSize: 12, color: AminaTheme.teal600, fontWeight: FontWeight.w600)),
            ),
          ),

          // Error
          if (error != null) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(color: AminaTheme.dangerBg, borderRadius: BorderRadius.circular(10)),
              child: Row(
                children: [
                  const Icon(Icons.error_outline, size: 14, color: AminaTheme.dangerFg),
                  const SizedBox(width: 8),
                  Expanded(child: Text(error!, style: const TextStyle(fontSize: 12, color: AminaTheme.dangerFg))),
                ],
              ),
            ),
          ],

          const SizedBox(height: 20),

          // Submit
          FilledButton(
            onPressed: isLoading ? null : () => onSubmit(),
            style: FilledButton.styleFrom(
              backgroundColor: AminaTheme.teal500,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AminaTheme.radiusXL)),
            ),
            child: isLoading
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Text(l10n.signIn, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String text;
  // ignore: prefer_const_constructors_in_immutables
  _FieldLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AminaTheme.ink700));
  }
}

class _Field extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final bool obscureText;
  final TextInputType? keyboardType;
  final Widget? suffix;
  final void Function(String)? onSubmit;

  const _Field({
    required this.controller,
    required this.hint,
    this.obscureText = false,
    this.keyboardType,
    this.suffix,
    this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.subtleBg(context),
        borderRadius: BorderRadius.circular(AminaTheme.radiusSm),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onSubmitted: onSubmit,
        style: TextStyle(fontSize: 14, color: AminaTheme.isDark(context) ? AminaTheme.dark100 : AminaTheme.ink900),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(color: AminaTheme.textSecondary(context), fontSize: 14),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          suffixIcon: suffix,
          isDense: true,
        ),
      ),
    );
  }
}

// ── Demo button ───────────────────────────────────────────────────────────────

class _DemoButton extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;

  const _DemoButton({required this.isLoading, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      children: [
        Row(
          children: [
            const Expanded(child: Divider(color: AminaTheme.ink200)),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(l10n.or, style: const TextStyle(fontSize: 12, color: AminaTheme.ink400)),
            ),
            const Expanded(child: Divider(color: AminaTheme.ink200)),
          ],
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: isLoading ? null : onTap,
            icon: const Icon(Icons.auto_awesome, size: 16, color: AminaTheme.teal600),
            label: Text(l10n.demoAccess, style: const TextStyle(color: AminaTheme.teal700, fontWeight: FontWeight.w600, fontSize: 13)),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 13),
              side: const BorderSide(color: AminaTheme.teal100),
              backgroundColor: AminaTheme.teal50,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AminaTheme.radiusXL)),
            ),
          ),
        ),
      ],
    );
  }
}

// ── Sign-up row ───────────────────────────────────────────────────────────────

class _SignupRow extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;
  const _SignupRow({required this.isLoading, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text('Pas encore de compte ?', style: TextStyle(fontSize: 13, color: AminaTheme.textSecondary(context))),
        const SizedBox(width: 6),
        GestureDetector(
          onTap: isLoading ? null : onTap,
          child: const Text(
            'Créer un compte',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AminaTheme.teal600),
          ),
        ),
      ],
    );
  }
}

// ── Footer ────────────────────────────────────────────────────────────────────

class _Footer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.shield_outlined, size: 13, color: AminaTheme.ink300),
        const SizedBox(width: 6),
        Text(AppLocalizations.of(context)!.dataPrivacyNote, style: const TextStyle(fontSize: 11, color: AminaTheme.ink300)),
      ],
    );
  }
}
