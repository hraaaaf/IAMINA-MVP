import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/amina_visual_language.dart';

/// Same companion destination for both Dashboard states; no patient analysis
/// is implied by the label, including before the first recorded reading.
class DashboardCompanionCallout extends StatelessWidget {
  final bool compact;

  const DashboardCompanionCallout({super.key, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final locale = Localizations.localeOf(context).languageCode;
    final title = switch (locale) {
      'ar' => 'IAmina · رفيقك',
      'en' => 'IAMINA · Your companion',
      _ => 'IAMINA · Votre compagnon',
    };
    final action = switch (locale) {
      'ar' => 'اطرح سؤالاً',
      'en' => 'Ask a question',
      _ => 'Poser une question',
    };

    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        key: ValueKey(compact
            ? 'dashboard-empty-companion-secondary'
            : 'dashboard-secondary-companion'),
        onPressed: () => context.go('/companion/chat'),
        style: OutlinedButton.styleFrom(
          minimumSize: Size.fromHeight(compact ? 58 : 66),
          padding: const EdgeInsetsDirectional.fromSTEB(14, 10, 14, 10),
          backgroundColor: AminaVisualLanguage.controlSurface(context),
          foregroundColor: AminaVisualLanguage.forestDeep,
          side: BorderSide(
            color: AminaVisualLanguage.controlBorder(context),
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.chat_bubble_outline_rounded,
              color: AminaVisualLanguage.actionGreen,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: AminaVisualLanguage.secondary(context),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    action,
                    style: TextStyle(
                      color: AminaVisualLanguage.primaryText(context),
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              Directionality.of(context) == TextDirection.rtl
                  ? Icons.arrow_back_ios_new_rounded
                  : Icons.arrow_forward_ios_rounded,
              size: 14,
              color: AminaVisualLanguage.actionGreen,
            ),
          ],
        ),
      ),
    );
  }
}
