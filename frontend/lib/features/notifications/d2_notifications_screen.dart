import 'package:flutter/material.dart';

import '../../core/theme/amina_visual_language.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/mobile_page_header.dart';

String _d2Text(BuildContext context, String fr, String en, String ar) =>
    switch (Localizations.localeOf(context).languageCode) {
      'ar' => ar,
      'en' => en,
      _ => fr,
    };

/// D2 — dedicated in-app notifications surface, distinct from D3 reminders.
///
/// Honest, view-only shell: no source-bound patient inbox has been certified.
/// Do not invent notices, unread counts, opt-in persistence, or push delivery.
class D2NotificationsScreen extends StatelessWidget {
  const D2NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const ValueKey('d2-notifications-screen'),
      backgroundColor: AminaTheme.bg(context),
      body: Column(
        children: [
          AminaMobilePageHeader(
            leading: const AminaPageExitButton(fallbackRoute: '/dashboard'),
            title: _d2Text(context, 'Notifications', 'Notifications', 'الإشعارات'),
            subtitle: _d2Text(
              context,
              'Informations de votre application',
              'Updates from your app',
              'مستجدات التطبيق',
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              child: Align(
                alignment: AlignmentDirectional.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 760),
                  child: Padding(
                    padding: const EdgeInsetsDirectional.fromSTEB(
                      20, 24, 20, 48,
                    ),
                    child: Container(
                      key: const ValueKey('d2-notifications-unavailable'),
                      width: double.infinity,
                      padding: const EdgeInsetsDirectional.fromSTEB(
                        22, 28, 22, 28,
                      ),
                      decoration: AminaVisualLanguage.cardDecoration(
                        context,
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 64,
                            height: 64,
                            decoration: AminaVisualLanguage.mintIconDecoration(
                              context,
                            ),
                            child: const Icon(
                              Icons.notifications_none_rounded,
                              size: 30,
                              color: AminaVisualLanguage.actionGreen,
                            ),
                          ),
                          const SizedBox(height: 22),
                          Semantics(
                            header: true,
                            child: Text(
                              _d2Text(
                                context,
                                'Les notifications arrivent bientôt',
                                'Notifications are coming soon',
                                'الإشعارات ستتوفر قريباً',
                              ),
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AminaVisualLanguage.primaryText(
                                  context,
                                ),
                                fontFamily: 'Georgia',
                                fontSize: 22,
                                height: 1.2,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _d2Text(
                              context,
                              'La réception des notifications n’est pas encore activée. '
                              'IAMINA n’affiche aucun message fictif.',
                              'Notification delivery is not enabled yet. '
                              'IAMINA never displays invented messages.',
                              'لم يتم تفعيل استقبال الإشعارات بعد. '
                              'لا يعرض IAMINA رسائل وهمية.',
                            ),
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 14,
                              height: 1.55,
                              color: AminaVisualLanguage.secondary(context),
                            ),
                          ),
                          const SizedBox(height: 20),
                          Container(
                            key: const ValueKey('d2-notifications-boundary'),
                            width: double.infinity,
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AminaVisualLanguage.mintSurface.withValues(
                                alpha: AminaTheme.isDark(context) ? .08 : .55,
                              ),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(
                                  Icons.info_outline_rounded,
                                  size: 20,
                                  color: AminaVisualLanguage.actionGreen,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    _d2Text(
                                      context,
                                      'Les rappels sont distincts : ils restent '
                                      'en bas de l’accueil. Les notifications '
                                      'proactives nécessiteront votre accord.',
                                      'Reminders are separate and stay at the '
                                      'bottom of Home. Proactive notifications '
                                      'will require your consent.',
                                      'التذكيرات منفصلة وتبقى أسفل الصفحة '
                                      'الرئيسية. الإشعارات الاستباقية '
                                      'ستتطلب موافقتك.',
                                    ),
                                    style: TextStyle(
                                      color: AminaVisualLanguage.primaryText(
                                        context,
                                      ),
                                      fontSize: 13,
                                      height: 1.5,
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
        ],
      ),
    );
  }
}
