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
}
