import 'package:flutter/material.dart';
import '../dashboard/widgets/add_log_sheet.dart';

class AddLogScreen extends StatelessWidget {
  final AddLogFocus focus;

  const AddLogScreen({super.key, this.focus = AddLogFocus.none});

  @override
  Widget build(BuildContext context) {
    return Scaffold(body: AddLogSheet(isPage: true, focus: focus));
  }
}
