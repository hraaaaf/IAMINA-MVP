import 'package:flutter/material.dart';
import '../dashboard/widgets/add_log_sheet.dart';

class AddLogScreen extends StatelessWidget {
  const AddLogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: AddLogSheet(isPage: true));
  }
}
