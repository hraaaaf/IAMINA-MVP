import 'package:amina/l10n/app_localizations.dart';

extension GlobalLocalizedCopy on AppLocalizations {
  String get renderErrorTitle {
    final code = localeName.split(RegExp('[-_]')).first;
    return switch (code) {
      'ar' => 'حدث خطأ في عرض الصفحة',
      'fr' => 'Une erreur de rendu est survenue',
      _ => 'A rendering error occurred',
    };
  }
}
