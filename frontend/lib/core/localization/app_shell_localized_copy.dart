import 'package:amina/l10n/app_localizations.dart';

extension AppShellLocalizedCopy on AppLocalizations {
  String get _languageCode => localeName.split(RegExp('[-_]')).first;

  String _pick({required String en, required String fr, required String ar}) {
    return switch (_languageCode) {
      'ar' => ar,
      'fr' => fr,
      _ => en,
    };
  }

  String get renderError => _pick(
        en: 'A rendering error occurred',
        fr: 'Une erreur de rendu est survenue',
        ar: 'حدث خطأ أثناء عرض الواجهة',
      );
}
