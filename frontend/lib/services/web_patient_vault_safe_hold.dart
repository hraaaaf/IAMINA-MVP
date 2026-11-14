import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

/// D1-P0: public, non-clinical hold while the Web patient DB is rejected.
/// This widget contains no DB, API, profile, consent, or sync dependency.
/// It is never a key-recovery or clinical unlock mechanism.
class WebPatientVaultSafeHold extends StatelessWidget {
  final Locale locale;
  final VoidCallback onSignOut;
  final bool guestPreviewSession;

  const WebPatientVaultSafeHold({
    super.key,
    required this.locale,
    required this.onSignOut,
    this.guestPreviewSession = false,
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
    final status = switch (language) {
      'fr' => 'ACCÈS CLINIQUE SUSPENDU',
      'ar' => 'تم تعليق الوصول الطبي',
      _ => 'CLINICAL ACCESS PAUSED',
    };
    final info = switch (language) {
      'fr' => 'Aucune donnée médicale n’est affichée ici.',
      'ar' => 'لا تُعرض أي بيانات طبية هنا.',
      _ => 'No medical data is shown on this screen.',
    };
    final action = guestPreviewSession ? switch (language) {
      'fr' => 'Quitter le mode invité',
      'ar' => 'مغادرة وضع الضيف',
      _ => 'Leave guest mode',
    } : switch (language) {
      'fr' => 'Se déconnecter',
      'ar' => 'تسجيل الخروج',
      _ => 'Sign out',
    };

    return Directionality(
      textDirection: language == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        key: const Key('d1-web-patient-vault-safe-hold'),
        backgroundColor: AminaTheme.ink50,
        body: DecoratedBox(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFFE4F9F2),
                Color(0xFFF6FBF9),
                Color(0xFFF7FAF8),
              ],
            ),
          ),
          child: SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24, vertical: 28,
                ),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 500),
                  child: Semantics(
                    container: true,
                    explicitChildNodes: true,
                    liveRegion: true,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 112,
                          height: 112,
                          child: Image.asset(
                            'assets/images/iamina_logo_vertical.png',
                            fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => const Icon(
                              Icons.shield_outlined,
                              size: 72,
                              color: AminaTheme.teal900,
                            ),
                          ),
                        ),
                        const SizedBox(height: 26),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            color: AminaTheme.cardBg,
                            borderRadius: BorderRadius.circular(25),
                            border: Border.all(
                              color: AminaTheme.ink100,
                            ),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x0D0B6E57),
                                blurRadius: 36,
                                offset: Offset(0, 14),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Align(
                                alignment: AlignmentDirectional.centerStart,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 7,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AminaTheme.teal50,
                                    borderRadius: BorderRadius.circular(30),
                                    border: Border.all(
                                      color: AminaTheme.teal200,
                                    ),
                                  ),
                                  child: Text(
                                    status,
                                    style: const TextStyle(
                                      color: AminaTheme.teal700,
                                      fontWeight: FontWeight.w800,
                                      fontSize: 11,
                                      letterSpacing: 0.45,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 24),
                              const Align(
                                alignment: AlignmentDirectional.centerStart,
                                child: CircleAvatar(
                                  radius: 24,
                                  backgroundColor: AminaTheme.teal50,
                                  child: Icon(
                                    Icons.shield_outlined,
                                    color: AminaTheme.teal700,
                                    size: 26,
                                  ),
                                ),
                              ),
                              const SizedBox(height: 14),
                              Semantics(
                                container: true,
                                header: true,
                                label: title,
                                child: ExcludeSemantics(
                                  child: Text(
                                    title,
                                    key: const Key('d1-web-safe-hold-heading'),
                                    textAlign: TextAlign.start,
                                    style: const TextStyle(
                                      color: AminaTheme.teal900,
                                      fontSize: 25,
                                      height: 1.15,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 14),
                              Semantics(
                                container: true,
                                label: explanation,
                                child: ExcludeSemantics(
                                  child: Text(
                                    explanation,
                                    key: const Key('d1-web-safe-hold-explanation'),
                                    style: const TextStyle(
                                      color: AminaTheme.ink600,
                                      fontSize: 14,
                                      height: 1.5,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 20),
                              Container(
                                padding: const EdgeInsets.all(13),
                                decoration: BoxDecoration(
                                  color: AminaTheme.ink50,
                                  borderRadius: BorderRadius.circular(14),
                                  border: Border.all(
                                    color: AminaTheme.ink100,
                                  ),
                                ),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Icon(
                                      Icons.info_outline_rounded,
                                      color: AminaTheme.teal700,
                                      size: 19,
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Text(
                                        info,
                                        style: const TextStyle(
                                          color: AminaTheme.ink600,
                                          fontSize: 12.5,
                                          height: 1.4,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 21),
                              OutlinedButton.icon(
                                key: const Key('d1-web-safe-hold-signout'),
                                onPressed: onSignOut,
                                icon: const Icon(Icons.logout_outlined, size: 18),
                                label: Text(action),
                                style: OutlinedButton.styleFrom(
                                  minimumSize: const Size.fromHeight(52),
                                  foregroundColor: AminaTheme.teal700,
                                  side: const BorderSide(
                                    color: AminaTheme.teal200,
                                  ),
                                  textStyle: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 14,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(14),
                                  ),
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
          ),
        ),
      ),
    );
  }
}
