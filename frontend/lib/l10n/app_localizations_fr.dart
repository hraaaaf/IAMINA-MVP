// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appTitle => 'IAmina';

  @override
  String get appSubtitle => 'Compagnon Diabète';

  @override
  String get appTagline => 'Votre équilibre glycémique, chaque jour';

  @override
  String get brandName => 'Diabetes Log';

  @override
  String get brandTagShort => 'IA · AMINA';

  @override
  String get dataPrivacyNote => 'Traitement IA soumis à autorisation';

  @override
  String get sensorStatus => 'Capteur G7 · IAmina';

  @override
  String get login => 'Connexion';

  @override
  String get logout => 'Déconnexion';

  @override
  String get signIn => 'Se connecter';

  @override
  String get signOut => 'Se déconnecter';

  @override
  String get signOutConfirmTitle => 'Se déconnecter ?';

  @override
  String get signOutConfirmBody =>
      'Vos données restent sauvegardées. Vous pourrez vous reconnecter à tout moment.';

  @override
  String get confirmSignOut => 'Déconnecter';

  @override
  String get createAccount => 'Créer un compte';

  @override
  String get forgotPassword => 'Mot de passe oublié ?';

  @override
  String get resetPassword => 'Réinitialiser le mot de passe';

  @override
  String get resetPasswordDescription =>
      'Entrez votre adresse e-mail. Vous recevrez un lien pour créer un nouveau mot de passe.';

  @override
  String get resetEmailSent =>
      'Email envoyé — vérifiez votre boîte de réception.';

  @override
  String get emailNotFound => 'Adresse introuvable ou email invalide.';

  @override
  String get loginError => 'Identifiant ou mot de passe incorrect.';

  @override
  String get loginSubtitle => 'Connectez-vous pour accéder à votre suivi.';

  @override
  String get emailLabel => 'Adresse e-mail';

  @override
  String get emailPlaceholder => 'vous@exemple.com';

  @override
  String get passwordLabel => 'Mot de passe';

  @override
  String get send => 'Envoyer';

  @override
  String get or => 'ou';

  @override
  String get demoAccess => 'Accès démo — 21 jours de données';

  @override
  String get dashboard => 'Tableau de bord';

  @override
  String get addEntry => 'Ajouter une entrée';

  @override
  String get addMeasurement => 'Ajouter une mesure';

  @override
  String get summary => 'Résumé IAmina';

  @override
  String get profile => 'Profil';

  @override
  String get myProfile => 'Mon Profil';

  @override
  String get profileUpdated => 'Profil mis à jour';

  @override
  String get navSectionMain => 'Principal';

  @override
  String get navSectionAccount => 'Compte';

  @override
  String get navHome => 'Accueil';

  @override
  String get navIamina => 'IAmina';

  @override
  String get navHistory => 'Historique';

  @override
  String get navImport => 'Importer';

  @override
  String get navSettings => 'Paramètres';

  @override
  String get navJournal => 'Journal';

  @override
  String get journalSubtitle => 'Historique complet';

  @override
  String get glucose => 'Glycémie';

  @override
  String get insulin => 'Insuline';

  @override
  String get meal => 'Repas';

  @override
  String get fatigue => 'Fatigue';

  @override
  String get sick => 'Malade';

  @override
  String get stressed => 'Stressé';

  @override
  String get freeMeasurement => 'Mesure libre';

  @override
  String get enterValue => 'Entrez une valeur';

  @override
  String get diabetesType => 'Type de diabète';

  @override
  String get diabetesType1 => 'Diabète Type 1';

  @override
  String get diabetesType2 => 'Diabète Type 2';

  @override
  String get diabetesGestational => 'Gestationnel';

  @override
  String get diabetesPreDiabetes => 'Pré-diabète';

  @override
  String get treatment => 'Traitement';

  @override
  String get treatmentInsulin => 'Insuline';

  @override
  String get treatmentTablets => 'Comprimés';

  @override
  String get treatmentLifestyle => 'Hygiène seule';

  @override
  String get glucoseTarget => 'Cible glycémique (mg/dL)';

  @override
  String get measureUnit => 'Unité de mesure';

  @override
  String get dangerZone => 'Zone sensible';

  @override
  String get configureWithIamina => 'Configurer avec IAmina';

  @override
  String get conversationalAssistant => 'Utiliser l\'assistant conversationnel';

  @override
  String get journalEmpty => 'Votre journal est vide';

  @override
  String get journalEmptySubtitle =>
      'Ajoutez votre première mesure\npour commencer votre suivi.';

  @override
  String get last7Days => '7 derniers jours';

  @override
  String get last30Days => '30 derniers jours';

  @override
  String get allHistory => 'Tout l\'historique';

  @override
  String get today => 'AUJOURD\'HUI';

  @override
  String get deleteEntryTitle => 'Supprimer cette mesure ?';

  @override
  String get actionIrreversible => 'Cette action est irréversible.';

  @override
  String get entryDeleted => 'Mesure supprimée';

  @override
  String get consentTitle => 'Confidentialité & IA';

  @override
  String get consentHeadline =>
      'IAmina peut traiter certaines données avec des services IA approuvés';

  @override
  String get consentBody =>
      'Ce consentement autorise IAmina à utiliser les catégories de données listées ci-dessus pour les fonctionnalités IA. Un traitement externe n\'est effectué que si le fournisseur, la région et la politique de conservation du déploiement ont été approuvés. Sans consentement ou approbation fournisseur valide, les données ne sont pas envoyées au service IA.\n\nLe fournisseur et les conditions peuvent varier selon le déploiement. Vous pouvez retirer ce consentement à tout moment depuis vos paramètres de profil.';

  @override
  String get consentDataPoint1 => '📊 Mesures glycémiques et tendances';

  @override
  String get consentDataPoint2 => '🍽️ Contexte repas et doses d\'insuline';

  @override
  String get consentDataPoint3 =>
      '😴 Fatigue et marqueurs d\'événements de vie';

  @override
  String get consentAccept => 'Accepter et continuer';

  @override
  String get consentDeclineWithoutAI => 'Continuer sans IA';

  @override
  String get consentAlreadyGiven => 'Consentement accordé';

  @override
  String get consentWithdraw => 'Retirer le consentement IA';

  @override
  String get consentWithdrawConfirmTitle => 'Retirer le consentement IA ?';

  @override
  String get consentWithdrawConfirmBody =>
      'Les fonctionnalités IA (Résumé IAmina, Chat, Vocal) seront désactivées jusqu\'à ce que vous donniez à nouveau votre consentement.';

  @override
  String get consentWithdrawn => 'Consentement IA retiré';

  @override
  String get consentRequired =>
      'Consentement IA requis pour utiliser cette fonctionnalité';

  @override
  String get documentPrivacyTitle => 'Traitement externe contrôlé';

  @override
  String get documentPrivacyBody =>
      'Le document n’est transmis à un service externe que si votre consentement et la politique fournisseur du déploiement sont valides. Sinon, l’import est refusé.';

  @override
  String get save => 'Sauvegarder';

  @override
  String get saveProfile => 'Enregistrer';

  @override
  String get cancel => 'Annuler';

  @override
  String get delete => 'Supprimer';

  @override
  String get edit => 'Modifier';

  @override
  String get ok => 'OK';

  @override
  String get error => 'Erreur';

  @override
  String get loading => 'Chargement...';

  @override
  String get noData => 'Aucune donnée';

  @override
  String get welcome => 'Bienvenue dans IAmina';

  @override
  String get overview => 'Vue d\'ensemble';

  @override
  String get breadcrumb => 'Accueil · Vue d\'ensemble';

  @override
  String get talk => 'Parler à IAmina';

  @override
  String get dayShort => 'j';

  @override
  String get syncChecking => 'Vérification de la synchronisation';

  @override
  String get syncUpToDate => 'Données à jour';

  @override
  String get syncPending => 'Données en attente de synchronisation';

  @override
  String get syncing => 'Synchronisation en cours';

  @override
  String get syncOffline => 'Hors ligne · données conservées sur cet appareil';

  @override
  String get syncFailed => 'Échec de synchronisation · appuyer pour réessayer';

  @override
  String get goodMorning => 'Bonjour';

  @override
  String get goodAfternoon => 'Bon après-midi';

  @override
  String get goodEvening => 'Bonsoir';

  @override
  String greetingWithName(String greeting, String firstName) {
    return '$greeting, $firstName.';
  }

  @override
  String greetingWithoutName(String greeting) {
    return '$greeting !';
  }

  @override
  String observation(int range) {
    return 'Voici ce qu\'IAmina a observé sur vos $range derniers jours.';
  }

  @override
  String get emptyAnalysis =>
      'Chargez des données pour voir votre analyse IAmina.';

  @override
  String get latestReading => 'DERNIÈRE MESURE';

  @override
  String get justNow => 'à l\'instant';

  @override
  String minutesAgo(int value) {
    return 'il y a $value min';
  }

  @override
  String get afterMeal => 'Après repas';

  @override
  String get fasting => 'À jeun';

  @override
  String targetTitle(int range) {
    return 'MESURES DANS LA CIBLE · $range JOURS';
  }

  @override
  String targetCoverage(int count, int days) {
    return '$count mesures sur $days jours · proportion de mesures, pas durée CGM';
  }

  @override
  String get targetReference =>
      'Repère général ≥ 70 % · votre cible personnelle peut être différente.';

  @override
  String get viewJournal => 'Voir le journal';

  @override
  String get readingsInRange => 'Mesures dans la cible';

  @override
  String get rangeReference => 'Repère 70–180';

  @override
  String get inRange => 'Dans la cible';

  @override
  String get high => 'Élevé';

  @override
  String get low => 'Bas';

  @override
  String get veryHigh => 'Très élevé';

  @override
  String get targetExplanation =>
      'Repère général : plus de 70 % des mesures dans 70–180 mg/dL. Votre cible personnelle peut être différente.';

  @override
  String get importTitle => 'Importer';

  @override
  String get importSubtitle => 'Connectez vos sources de données';

  @override
  String get directConnections => 'Connexions directes';

  @override
  String get pulperDescription =>
      'PDF · Photo · Excel · Word — IAmina extrait les données pour votre relecture.';

  @override
  String get labReport => 'Bilan labo';

  @override
  String get cgmExport => 'Export CGM';

  @override
  String get prescription => 'Ordonnance';

  @override
  String get photo => 'Photo';

  @override
  String get soon => 'BIENTÔT';

  @override
  String get unavailable => 'Non disponible';

  @override
  String get dexcomDescription =>
      'Connexion Dexcom CLARITY prévue. Fréquence et disponibilité à confirmer avant activation.';

  @override
  String get libreDescription =>
      'Import LibreView prévu. Formats et disponibilité à confirmer avant activation.';

  @override
  String get openDocumentImport => 'Ouvrir l\'import de document';

  @override
  String get documentTitle => 'Importer un document';

  @override
  String get documentIntro =>
      'Importez un document médical. IAmina extrait les données, puis vous devez les relire et les confirmer.';

  @override
  String get chooseDocument => 'Choisir un document';

  @override
  String get profileComplete => 'Profil complet';

  @override
  String get profileCompleteChecked => 'Profil complet ✓';

  @override
  String profileCompletionPercent(int percentage) {
    return 'Profil complété à $percentage%';
  }

  @override
  String get profileCompletionPrompt =>
      'Complétez votre profil pour des analyses plus précises.';

  @override
  String get minimum => 'Min';

  @override
  String get maximum => 'Max';
}
