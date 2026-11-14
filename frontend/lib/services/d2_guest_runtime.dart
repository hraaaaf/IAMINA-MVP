import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../features/navigation/d2_guest_shell.dart';
import 'auth_service.dart';

/// D2 opt-in Preview-only bootstrap. Never mount a clinical DB, API client,
/// patient Provider, sync service or AI provider from this widget.
const bool kD2GuestNoDatabasePreview = bool.fromEnvironment(
  'IAMINA_D2_GUEST_NO_DB',
  defaultValue: false,
);

/// A visitor must never become an implicit local-only patient session.
/// Only synthetic Preview accounts can attempt the native Django auth path.
/// Even successful authentication remains in a non-clinical safe hold.
class D2GuestRuntime extends StatefulWidget {
  const D2GuestRuntime({super.key, required this.auth, this.locale});

  final AuthService auth;
  final Locale? locale;

  @override
  State<D2GuestRuntime> createState() => _D2GuestRuntimeState();
}

class _D2GuestRuntimeState extends State<D2GuestRuntime> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _pendingRoute;
  String? _error;
  bool _showAuth = false;
  bool _createAccount = false;
  bool _busy = false;
  bool _confirmedRemote = false;

  @override
  void initState() {
    super.initState();
    // Cached offline bearers are not proof of a fresh verified login.
    _confirmedRemote = widget.auth.isRemoteCredentialVerified &&
        widget.auth.hasRemoteApiCredential;
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  String _copy(String fr, String ar, String en) {
    final code = widget.locale?.languageCode ??
        WidgetsBinding.instance.platformDispatcher.locale.languageCode;
    return switch (code) {
      'ar' => ar,
      'en' => en,
      _ => fr,
    };
  }

  void _protect(String route) {
    // Route intention only. Never capture form content or health data.
    setState(() {
      _pendingRoute = route;
      _showAuth = true;
      _error = null;
    });
  }

  void _cancelAuth() {
    if (_busy) return;
    _password.clear();
    setState(() {
      _showAuth = false;
      _createAccount = false;
      _pendingRoute = null;
      _error = null;
    });
  }

  Future<void> _submit() async {
    if (_busy) return;
    // Build-time guard: never send real email/password to a test backend.
    if (!kD1PreviewOnlySyntheticAccounts ||
        !kRemoteAccountSignInEnabled ||
        (_createAccount && !kRemoteAccountEnrollmentEnabled)) {
      setState(() => _error = _copy(
        'Authentification de test non configurée.',
        'تسجيل الدخول التجريبي غير مهيأ.',
        'Test authentication is not configured.',
      ));
      return;
    }
    final email = _email.text.trim().toLowerCase();
    if (!d1PreviewEmailAllowed(email) || _password.text.isEmpty) {
      setState(() => _error = _copy(
        'Utilisez uniquement une adresse @d1-preview.test.',
        'استخدم عنوان @d1-preview.test فقط.',
        'Only @d1-preview.test addresses are allowed.',
      ));
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_createAccount) {
        await widget.auth.registerWithEmail(email, _password.text);
      } else {
        await widget.auth.signInWithEmail(email, _password.text);
      }
      if (!widget.auth.isRemoteCredentialVerified ||
          !widget.auth.hasRemoteApiCredential) {
        throw StateError('D2_REMOTE_AUTH_NOT_VERIFIED');
      }
      if (!mounted) return;
      _password.clear();
      setState(() {
        _confirmedRemote = true;
        _showAuth = false;
        _createAccount = false;
      });
    } on AuthCredentialsRejected {
      if (mounted) {
        setState(() => _error = _copy(
          'Identifiants de test incorrects.',
          'بيانات الدخول التجريبية غير صحيحة.',
          'Invalid test credentials.',
        ));
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = _copy(
          'Authentification indisponible. Aucune donnée n’a été ouverte.',
          'تسجيل الدخول غير متاح. لم تُفتح أي بيانات.',
          'Authentication unavailable. No data was opened.',
        ));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signOut() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await widget.auth.signOut();
    } catch (_) {
      // The native auth service revokes in-memory identity synchronously.
      // In all cases, remain in a DB-free visitor experience.
    } finally {
      if (mounted) {
        _password.clear();
        setState(() {
          _confirmedRemote = false;
          _createAccount = false;
          _pendingRoute = null;
          _showAuth = false;
          _busy = false;
          _error = null;
        });
      }
    }
  }

  Widget _authenticationGate() => Scaffold(
    key: const Key('d2-guest-auth-gate'),
    appBar: AppBar(
      title: Text(_copy(
        'Compte de test requis',
        'حساب تجريبي مطلوب',
        'Test account required',
      )),
      leading: IconButton(
        key: const Key('d2-guest-auth-back'),
        onPressed: _busy ? null : _cancelAuth,
        icon: const Icon(Icons.arrow_back),
      ),
    ),
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  _copy(
                    'Cette action nécessite un compte. Aucun coffre patient '
                    'ne sera ouvert dans cette Preview.',
                    'هذا الإجراء يتطلب حسابًا. لن يُفتح أي ملف طبي في المعاينة.',
                    'This action requires an account. No patient vault '
                    'will be opened in this Preview.',
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  _pendingRoute ?? '',
                  key: const Key('d2-guest-pending-route'),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                TextField(
                  key: const Key('d2-guest-email'),
                  controller: _email,
                  enabled: !_busy,
                  keyboardType: TextInputType.emailAddress,
                  autocorrect: false,
                  decoration: InputDecoration(
                    labelText: _copy('E-mail de test', 'بريد تجريبي', 'Test email'),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  key: const Key('d2-guest-password'),
                  controller: _password,
                  enabled: !_busy,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: _copy('Mot de passe', 'كلمة المرور', 'Password'),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    key: const Key('d2-guest-auth-error'),
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ],
                const SizedBox(height: 16),
                FilledButton(
                  key: const Key('d2-guest-auth-submit'),
                  onPressed: _busy ? null : _submit,
                  child: Text(_createAccount
                      ? _copy('Créer un compte', 'إنشاء حساب', 'Create account')
                      : _copy('Se connecter', 'تسجيل الدخول', 'Sign in')),
                ),
                TextButton(
                  key: const Key('d2-guest-auth-switch'),
                  onPressed: _busy
                      ? null
                      : () => setState(() => _createAccount = !_createAccount),
                  child: Text(_createAccount
                      ? _copy('Déjà un compte ? Se connecter',
                          'لديك حساب؟ تسجيل الدخول', 'Already have an account? Sign in')
                      : _copy('Créer un compte de test',
                          'إنشاء حساب تجريبي', 'Create a test account')),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );

  Widget _authenticatedSafeHold() => Scaffold(
    key: const Key('d2-guest-authenticated-safe-hold'),
    appBar: AppBar(
      title: Text(_copy('Compte connecté', 'حساب متصل', 'Account connected')),
    ),
    body: SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.shield_outlined, size: 48),
                const SizedBox(height: 12),
                Text(
                  _copy(
                    'Connexion confirmée. Le coffre Web n’est pas certifié : '
                    'l’action reste en attente, sans lecture ni écriture médicale.',
                    'تم تسجيل الدخول. الخزنة غير معتمدة ولا يتم الوصول إلى البيانات الطبية.',
                    'Signed in. The Web vault is not certified, so the requested '
                    'action remains pending with no medical data access.',
                  ),
                  key: const Key('d2-guest-action-paused'),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Text(_pendingRoute ?? '', key: const Key('d2-guest-saved-route')),
                const SizedBox(height: 20),
                OutlinedButton(
                  key: const Key('d2-guest-signout'),
                  onPressed: _busy ? null : _signOut,
                  child: Text(_copy(
                    'Se déconnecter', 'تسجيل الخروج', 'Sign out',
                  )),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'IAMINA · D2',
    locale: widget.locale,
    supportedLocales: const [Locale('fr'), Locale('ar'), Locale('en')],
    localizationsDelegates: const [
      GlobalMaterialLocalizations.delegate,
      GlobalWidgetsLocalizations.delegate,
      GlobalCupertinoLocalizations.delegate,
    ],
    home: _confirmedRemote && widget.auth.isRemoteCredentialVerified &&
            widget.auth.hasRemoteApiCredential
        ? _authenticatedSafeHold()
        : _showAuth
            ? _authenticationGate()
            : D2GuestShell(onProtectedAction: _protect),
  );
}
