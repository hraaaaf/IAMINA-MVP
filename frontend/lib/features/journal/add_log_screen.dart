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
        legacyTopExtent: 82,
        child: AddLogSheet(isPage: true, focus: focus),
      ),
    );
  }
}
