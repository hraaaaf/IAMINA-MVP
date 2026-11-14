import 'package:flutter/material.dart';

import '../../services/auth_service.dart';
import '../../services/w01_revocation_probe.dart';
import 'local_device_enrollment_screen.dart' as local;
import 'login_screen_fr_certified.dart' as certified_fr;
import 'login_screen_mena.dart' as mena;

/// Both journeys remain available when remote account sign-in is enabled.
/// Selecting a local vault must never create a synthetic remote identity.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

// The three ordinary entry choices are exposed ONLY on an isolated D1
// Preview. Patient clinical vault access remains fail-closed in main.dart.
const bool kD1PreviewAuthChoices = bool.fromEnvironment(
  'IAMINA_D1_PREVIEW_AUTH_CHOICES', defaultValue: false,
);

class _LoginScreenState extends State<LoginScreen> {
  bool _accountMode = false;
  bool _openSignupOnEntry = false;

  void _chooseAccount({bool signup = false}) {
    setState(() {
      _openSignupOnEntry = signup;
      _accountMode = true;
    });
  }

  Widget _w01ResultBanner(BuildContext context) {
    return ValueListenableBuilder<W01RevocationProbeResult?>(
      valueListenable: w01RevocationProbeNotice,
      builder: (context, result, _) {
        if (result == null) return const SizedBox.shrink();
        final success = result.passed;
        final locale = Localizations.localeOf(context).languageCode;
        final headline = switch (locale) {
          'fr' => success
              ? 'PASS · ancien jeton refusé par le serveur'
              : 'NON VALIDÉ · vérifiez les codes HTTP',
          'ar' => success
              ? 'نجاح · رفض الخادم الرمز القديم'
              : 'غير مؤكد · تحقق من رموز HTTP',
          _ => success
              ? 'PASS · server rejected old token'
              : 'NOT VERIFIED · review HTTP statuses',
        };
        String code(int? value) => value?.toString() ?? '—';
        final line = 'GET /logs ${code(result.beforeStatus)}  ·  '
            'POST /logout ${code(result.logoutStatus)}  ·  '
            'ancien GET /logs ${code(result.afterStatus)}';
        return Semantics(
          liveRegion: true,
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 0),
              child: Card(
                key: const Key('w01-revocation-result-banner'),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        success
                            ? Icons.verified_user_outlined
                            : Icons.warning_amber_rounded,
                        color: success ? Colors.green.shade700
                            : Colors.orange.shade800,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(headline,
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(line,
                              style: const TextStyle(fontSize: 12),
                            ),
                            if (result.cleanupFailed)
                              const Text(
                                'Local sign-out cleanup could not be confirmed.',
                                style: TextStyle(fontSize: 12),
                              ),
                          ],
                        ),
                      ),
                      IconButton(
                        key: const Key('w01-revocation-dismiss'),
                        tooltip: locale == 'fr' ? 'Fermer'
                            : locale == 'ar' ? 'إغلاق' : 'Dismiss',
                        onPressed: () => w01RevocationProbeNotice.value = null,
                        icon: const Icon(Icons.close, size: 18),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }


  @override
  Widget build(BuildContext context) {
    if (!_accountMode || !kRemoteAccountSignInEnabled) {
      final localScreen = local.LocalDeviceEnrollmentScreen(
        onChooseAccount: kRemoteAccountSignInEnabled
            ? () => _chooseAccount()
            : null,
        onCreateAccount: kD1PreviewAuthChoices &&
                kRemoteAccountEnrollmentEnabled
            ? () => _chooseAccount(signup: true)
            : null,
      );
      if (!kW01RevocationProbeEnabled) return localScreen;
      return Column(
        children: [
          _w01ResultBanner(context),
          Expanded(child: localScreen),
        ],
      );
    }

    final locale = Localizations.localeOf(context).languageCode;
    final backText = switch (locale) {
      'fr' => 'Continuer sans compte',
      'ar' => 'المتابعة بدون حساب',
      _ => 'Continue without an account',
    };
    return Column(
      children: [
        if (kW01RevocationProbeEnabled) _w01ResultBanner(context),
        Material(
          color: Theme.of(context).scaffoldBackgroundColor,
          child: SafeArea(
            bottom: false,
            child: Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton.icon(
                key: const Key('d30-return-local'),
                onPressed: () => setState(() {
                  _accountMode = false;
                  _openSignupOnEntry = false;
                }),
                icon: const Icon(Icons.arrow_back_rounded),
                label: Text(backText),
              ),
            ),
          ),
        ),
        if (kD1PreviewAuthChoices)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: Semantics(
              liveRegion: true,
              child: Text(
                switch (locale) {
                  'fr' => 'Preview D1 · Uniquement les comptes de test @d1-preview.test. Ne saisissez jamais vos identifiants personnels.',
                  'ar' => 'معاينة D1 · حسابات @d1-preview.test التجريبية فقط. لا تستخدم معلوماتك الشخصية.',
                  _ => 'D1 Preview · Use only @d1-preview.test accounts. Never enter your personal credentials.',
                },
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ),
        Expanded(
          child: locale == 'fr'
              ? certified_fr.LoginScreen(
                  syntheticLoginOnly: !kRemoteAccountEnrollmentEnabled,
                  openSignupImmediately: _openSignupOnEntry,
                )
              : mena.LoginScreen(
                  syntheticLoginOnly: !kRemoteAccountEnrollmentEnabled,
                  openSignupImmediately: _openSignupOnEntry,
                ),
        ),
      ],
    );
  }
}
