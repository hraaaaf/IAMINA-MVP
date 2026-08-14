import 'package:flutter/material.dart';

import '../../core/widgets/premium_task_brand_overlay.dart';
import '../dashboard/widgets/add_log_sheet.dart';

class AddLogScreen extends StatelessWidget {
  final AddLogFocus focus;

  const AddLogScreen({super.key, this.focus = AddLogFocus.none});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          AddLogSheet(isPage: true, focus: focus),
          const PremiumTaskBrandOverlay(),
        ],
      ),
    );
  }
}
