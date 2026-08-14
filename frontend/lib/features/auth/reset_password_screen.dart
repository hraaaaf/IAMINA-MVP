import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/auth_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../services/auth_service.dart';

class ResetPasswordScreen extends StatefulWidget {
  final String uid;
  final String token;

  const ResetPasswordScreen({
    super.key,
    required this.uid,
    required this.token,
  });

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscure = true;
  bool _submitting = false;
  String? _error;

  bool get _hasValidLink => widget.uid.isNotEmpty && widget.token.isNotEmpty;

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context)!;
    final password = _passwordController.text;
    if (!_hasValidLink) {
      setState(() => _error = l10n.invalidResetLink);
      return;
    }
    if (password.length < 8) {
      setState(() => _error = l10n.passwordMinimumEight);
      return;
    }
    if (password != _confirmController.text) {
      setState(() => _error = l10n.passwordsDoNotMatch);
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await context.read<AuthService>().confirmPasswordReset(
            uid: widget.uid,
            token: widget.token,
            newPassword: password,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(l10n.passwordResetSucceeded),
          behavior: SnackBarBehavior.floating,
        ),
      );
      context.go('/login');
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = l10n.resetLinkExpired;
        });
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(
                      Icons.lock_reset_outlined,
                      size: 44,
                      color: AminaTheme.teal600,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      l10n.newPassword,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AminaTheme.ink900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      l10n.newPasswordIntro,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AminaTheme.ink500),
                    ),
                    const SizedBox(height: 24),
                    TextField(
                      controller: _passwordController,
                      obscureText: _obscure,
                      autocorrect: false,
                      enableSuggestions: false,
                      decoration: InputDecoration(
                        labelText: l10n.newPassword,
                        suffixIcon: IconButton(
                          onPressed: () => setState(() => _obscure = !_obscure),
                          icon: Icon(
                            _obscure
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _confirmController,
                      obscureText: _obscure,
                      autocorrect: false,
                      enableSuggestions: false,
                      onSubmitted: (_) => _submitting ? null : _submit(),
                      decoration: InputDecoration(
                        labelText: l10n.confirmPassword,
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 14),
                      Text(
                        _error!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AminaTheme.dangerFg),
                      ),
                    ],
                    const SizedBox(height: 22),
                    FilledButton(
                      onPressed: _submitting ? null : _submit,
                      child: _submitting
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(l10n.resetPasswordAction),
                    ),
                    const SizedBox(height: 10),
                    TextButton(
                      onPressed: () => context.go('/login'),
                      child: Text(l10n.backToLogin),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
