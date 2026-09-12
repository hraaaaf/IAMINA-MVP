import 'package:flutter/material.dart';

import '../../core/widgets/legacy_page_header_bridge.dart';
import '../dashboard/widgets/add_log_sheet.dart';

String _addLogCopy(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class AddLogScreen extends StatelessWidget {
  final AddLogFocus focus;

  const AddLogScreen({super.key, this.focus = AddLogFocus.none});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final tablet = width >= 600 && width < 1000;
    final desktop = width >= 1000;
    final effectiveFocus = desktop && focus == AddLogFocus.none
        ? AddLogFocus.activity
        : focus;
    final legacyTopExtent = desktop
        ? 310.0
        : tablet
        ? 360.0
        : 270.0;

    return Scaffold(
      body: AminaLegacyPageHeaderBridge(
        title: _addLogCopy(
          context,
          'Nouvelle mesure',
          'New reading',
          'قراءة جديدة',
        ),
        subtitle: _addLogCopy(
          context,
          'Notez simplement ce qui vient de se passer.',
          'Simply record what just happened.',
          'سجّل ببساطة ما حدث للتو.',
        ),
        legacyTopExtent: legacyTopExtent,
        contentTopInset: 12,
        child: Center(
          child: ConstrainedBox(
            key: const Key('add-log-responsive-column'),
            constraints: BoxConstraints(
              maxWidth: tablet ? 640 : double.infinity,
            ),
            child: AddLogSheet(isPage: true, focus: effectiveFocus),
          ),
        ),
      ),
    );
  }
}
