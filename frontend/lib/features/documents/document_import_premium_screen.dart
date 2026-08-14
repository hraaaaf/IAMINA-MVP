import 'package:flutter/material.dart';

import '../../core/widgets/premium_task_brand_overlay.dart';
import 'document_import_screen.dart';

class DocumentImportPremiumScreen extends StatelessWidget {
  const DocumentImportPremiumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Stack(
      fit: StackFit.expand,
      children: [
        DocumentImportScreen(),
        PremiumTaskBrandOverlay(),
      ],
    );
  }
}
