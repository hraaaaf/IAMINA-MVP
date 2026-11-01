import 'package:flutter/material.dart';

import '../../core/widgets/legacy_page_header_bridge.dart';
import '../../core/widgets/mobile_page_header.dart';
import '../dashboard/widgets/add_log_sheet.dart';

String _addLogCopy(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class AddLogScreen extends StatefulWidget {
  final AddLogFocus focus;

  const AddLogScreen({super.key, this.focus = AddLogFocus.none});

  @override
  State<AddLogScreen> createState() => _AddLogScreenState();
}

class _AddLogScreenState extends State<AddLogScreen> {
  final _sheetKey = GlobalKey<AddLogSheetState>();

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final compact = width < 600;
    final tablet = width >= 600 && width < 1000;
    final desktop = width >= 1000;
    final effectiveFocus = desktop && widget.focus == AddLogFocus.none
        ? AddLogFocus.activity
        : widget.focus;

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
        leading: AminaPageExitButton(
          beforeExit: () async {
            final sheet = _sheetKey.currentState;
            if (sheet == null) return false;
            return sheet.confirmExitRequested();
          },
        ),
        legacyTopExtent: 0,
        contentTopInset: 12,
        child: SizedBox.expand(
          child: Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              key: const Key('add-log-responsive-column'),
              constraints: BoxConstraints(
                maxWidth: tablet ? 640 : (desktop ? 1120 : double.infinity),
              ),
              child: SizedBox(
                width: double.infinity,
                height: compact ? double.infinity : null,
                child: AddLogSheet(key: _sheetKey, isPage: true, focus: effectiveFocus),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
