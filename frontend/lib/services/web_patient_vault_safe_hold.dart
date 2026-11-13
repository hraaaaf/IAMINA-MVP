import 'package:flutter/material.dart';

/// D1-P0: render a public, data-free hold when patient Web storage is denied.
/// No database, API, consent, profile or sync dependency may enter this widget.
/// This screen is NOT an encrypted-vault unlock or a recovery mechanism.
class WebPatientVaultSafeHold extends StatelessWidget {
  final Locale locale;
  final VoidCallback onSignOut;

  const WebPatientVaultSafeHold({
    super.key,
    required this.locale,
    required this.onSignOut,
  });

  @override
  Widget build(BuildContext context) {
    final language = locale.languageCode;
    final title = switch (language) {
      'fr' => 'Coffre patient indisponible',
      'ar' => 'ملف المريض غير متاح',
      _ => 'Patient vault unavailable',
    };
    final explanation = switch (language) {
      'fr' => 'Le stockage chiffré du coffre patient Web n’est pas encore '
          'validé. Par sécurité, l’accès aux données médicales est suspendu. '
          'Aucune migration ni suppression de vos données n’a été lancée.',
      'ar' => 'لم يتم اعتماد التخزين المشفر لملف المريض على الويب بعد. '
          'لأسباب أمنية، تم تعليق الوصول إلى البيانات الطبية. '
          'لم تبدأ أي عملية نقل أو حذف للبيانات.',
      _ => 'Encrypted Web patient storage has not yet been verified. '
          'Access to medical data is suspended for safety. '
          'No migration or deletion of your data has been started.',
    };
    final action = switch (language) {
      'fr' => 'Se déconnecter',
      'ar' => 'تسجيل الخروج',
      _ => 'Sign out',
    };

    return Directionality(
      textDirection: language == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        key: const Key('d1-web-patient-vault-safe-hold'),
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: Semantics(
                  liveRegion: true,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.shield_outlined, size: 48),
                      const SizedBox(height: 18),
                      Text(
                        title,
                        key: const Key('d1-web-safe-hold-heading'),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        explanation,
                        key: const Key('d1-web-safe-hold-explanation'),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 22),
                      OutlinedButton.icon(
                        key: const Key('d1-web-safe-hold-signout'),
                        onPressed: onSignOut,
                        icon: const Icon(Icons.logout_outlined),
                        label: Text(action),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
