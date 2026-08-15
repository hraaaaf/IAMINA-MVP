import 'package:flutter/material.dart';

import '../../core/widgets/legacy_page_header_bridge.dart';
import 'document_import_screen.dart';

String _documentImportCopy(BuildContext context, String fr, String en, String ar) {
  final code = Localizations.localeOf(context).languageCode;
  if (code == 'ar') return ar;
  if (code == 'en') return en;
  return fr;
}

class DocumentImportPremiumScreen extends StatelessWidget {
  const DocumentImportPremiumScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AminaLegacyPageHeaderBridge(
      title: _documentImportCopy(
        context,
        'Importer',
        'Import',
        'استيراد',
      ),
      subtitle: _documentImportCopy(
        context,
        'Ajoutez un document, puis vérifiez ce qu’IAmina a lu.',
        'Add a document, then review what IAmina read.',
        'أضف مستنداً ثم راجع ما قرأته IAmina.',
      ),
      legacyTopExtent: 82,
      child: const DocumentImportScreen(),
    );
  }
}
