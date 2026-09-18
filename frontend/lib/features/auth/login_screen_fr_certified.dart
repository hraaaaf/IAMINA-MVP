import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/api_client.dart';
import '../../services/auth_service.dart';

part 'login_screen_fr_certified_presentation.dart';

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
              style: FilledButton.styleFrom(
                backgroundColor: AminaTheme.teal500,
              ),
              child: Text(dl10n.send),
            ),
          ],
        );
      },
    );
    if (confirmed != true || !mounted) return;
    final email = emailCtrl.text.trim();
    if (email.isEmpty) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
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
                hint: '••••••••  (min. 8 caractères)',
                obscureText: obscure,
                suffix: IconButton(
                  onPressed: () => setDlgState(() => obscure = !obscure),
                  icon: Icon(
                    obscure
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    size: 16,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const _FieldLabel('Confirmer le mot de passe'),
              const SizedBox(height: 6),
              _Field(
                controller: confirmCtrl,
                hint: '••••••••',
                obscureText: obscure,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(l10n.cancel),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AminaTheme.teal500,
              ),
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
                setState(() {
                  _isLoading = true;
                  _error = null;
                });
                try {
                  await context.read<AuthService>().registerWithEmail(
                    email,
                    password,
                  );
                  if (mounted) context.go('/onboarding');
                } catch (error) {
                  if (mounted) {
                    final message = switch (error) {
                      RegistrationFailure(
                        code: RegistrationFailureCode.weakPassword,
                      ) =>
                        'Mot de passe trop faible : utilisez au moins 8 caractères, évitez un mot de passe courant, uniquement numérique ou trop proche de votre e-mail.',
                      RegistrationFailure(
                        code: RegistrationFailureCode.accountExists,
                      ) =>
                        'Un compte existe déjà avec cette adresse e-mail. Connectez-vous ou utilisez « Mot de passe oublié ».',
                      _ =>
                        'Échec de la création du compte — vérifiez votre connexion puis réessayez.',
                    };
                    setState(() => _error = message);
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
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final auth = context.read<AuthService>();
    final db = context.read<AppDatabase>();
    final api = context.read<ApiClient>();
    try {
      if (isDemo) {
        await auth.signInAnonymously();
        if (!kOfflineDemo) {
          await api.seedDemoData(); // best-effort backend mirror
        }
        await db.seedDemoData(); // complete local dataset before navigation
      } else {
        await auth.signInWithEmail(_emailCtrl.text.trim(), _passwordCtrl.text);
      }
      if (mounted) context.go('/dashboard');
    } catch (_) {
      if (mounted)
        setState(() => _error = AppLocalizations.of(context)!.loginError);
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
          const _BottomWave(),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(26, 24, 26, 15),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 390),
                  child: Column(
                    children: [
                      const _Brand(),
                      const SizedBox(height: 64),
                      _LoginCard(
                        emailCtrl: _emailCtrl,
                        passwordCtrl: _passwordCtrl,
                        obscure: _obscure,
                        onToggleObscure: () =>
                            setState(() => _obscure = !_obscure),
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
