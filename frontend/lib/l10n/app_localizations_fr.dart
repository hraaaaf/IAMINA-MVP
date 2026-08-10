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
  String get dataPrivacyNote =>
      'Services IA externes : votre consentement et une autorisation valide du fournisseur sont requis';

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
      'IAmina peut utiliser des services d’IA externes pour certaines fonctionnalités';

  @override
  String get consentBody =>
      'Avec votre consentement, IAmina peut envoyer uniquement les catégories de données indiquées ci-dessus à un service d’IA externe. L’envoi n’a lieu que si le fournisseur, sa région d’hébergement et sa durée de conservation sont autorisés pour votre environnement IAmina. Sans consentement ou sans autorisation valide du fournisseur, aucune donnée n’est envoyée.\n\nVous pouvez retirer votre consentement à tout moment depuis votre profil.';

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
  String get documentPrivacyTitle => 'Envoi externe uniquement si autorisé';

  @override
  String get documentPrivacyBody =>
      'IAmina n’envoie ce document à un service externe que si vous avez donné votre consentement et si le fournisseur de ce service est autorisé pour votre environnement IAmina. Sinon, l’import est bloqué.';

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
    return '$count mesures sur $days jours · proportion des mesures enregistrées, pas temps dans la cible d’un capteur de glucose en continu (CGM)';
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
  String get cgmExport => 'Export de mesure continue du glucose (CGM)';

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

  @override
  String get onboardingWelcome =>
      'Bonjour ! Je suis IAmina, votre compagnon de suivi du diabète.';

  @override
  String get onboardingChooseLanguage =>
      'Choisissez la langue de l’application.';

  @override
  String get onboardingChooseCountry => 'Dans quel pays utilisez-vous IAmina ?';

  @override
  String get onboardingChooseTone => 'Quel ton préférez-vous ?';

  @override
  String get onboardingToneNeutral => 'Neutre et professionnel';

  @override
  String get onboardingToneFriendly => 'Simple et chaleureux';

  @override
  String get onboardingCountryMorocco => 'Maroc';

  @override
  String get onboardingCountryFrance => 'France';

  @override
  String get onboardingCountryOther => 'Autre pays';

  @override
  String get onboardingTypeQuestion =>
      'Quel type de diabète gérez-vous au quotidien ?';

  @override
  String get onboardingTreatmentQuestion =>
      'Quel est votre mode de traitement principal ?';

  @override
  String get onboardingTreatmentInsulin => 'Insuline (injection ou pompe)';

  @override
  String get onboardingTreatmentLifestyle => 'Hygiène de vie seule';

  @override
  String get onboardingTargetQuestion =>
      'Quels sont vos objectifs glycémiques ? Le repère général affiché est 70–180 mg/dL, sauf cible personnelle différente.';

  @override
  String get onboardingTargetStandard => 'Repère général (70–180)';

  @override
  String get onboardingTargetCustom => 'Cible personnelle';

  @override
  String get onboardingUnitQuestion =>
      'Quelle unité préférez-vous pour les mesures ?';

  @override
  String get onboardingUnitMg => 'mg/dL';

  @override
  String get onboardingUnitMmol => 'mmol/L';

  @override
  String get onboardingReady =>
      'Votre espace est configuré. Vous pourrez modifier ces choix dans votre profil.';

  @override
  String get onboardingStart => 'Commencer';

  @override
  String get onboardingSaving => 'Enregistrement…';

  @override
  String get onboardingAssistantLabel => 'Assistant de configuration';

  @override
  String get emptyDashboardTitle => 'Ajoutez votre première donnée';

  @override
  String get emptyDashboardBody =>
      'Aucune donnée n’est encore enregistrée. Ajoutez une mesure ou importez un document pour construire ce tableau de bord à partir de vos données réelles.';

  @override
  String get addFirstMeasurement => 'Ajouter ma première mesure';

  @override
  String get importDocument => 'Importer un document';

  @override
  String get featureRealtimeAgp => 'Résumé des tendances du capteur (AGP)';

  @override
  String get featureAiAnalysis => 'Analyse IA';

  @override
  String get featurePrivateData => 'Données privées';

  @override
  String get analysisLoadError => 'Impossible de récupérer les analyses.';

  @override
  String get retry => 'Réessayer';

  @override
  String get analysisLoading => 'IAmina analyse vos données…';

  @override
  String get analysisLoadingWait => 'Cela prend quelques secondes.';

  @override
  String get dashboardLoadingTitle => 'Chargement de vos données';

  @override
  String get dashboardLoadingBody =>
      'IAmina vérifie les données enregistrées sur cet appareil avant d’afficher votre tableau de bord.';

  @override
  String get dashboardLoadErrorTitle =>
      'Vos données ne peuvent pas être affichées';

  @override
  String get dashboardLoadErrorBody =>
      'Le tableau de bord n’a pas pu lire vos données locales. Vous pouvez réessayer sans créer de données fictives.';

  @override
  String get firstUseTruthNote =>
      'Les tendances et analyses apparaîtront uniquement quand des données réelles seront disponibles.';

  @override
  String get profileMedicalSection => 'Suivi médical';

  @override
  String get profileIaminaSection => 'IAmina & préférences';

  @override
  String get profileIaminaSectionHint =>
      'Langue, pays, ton et assistant de configuration';

  @override
  String get profileAccountSection => 'Confidentialité & compte';

  @override
  String get profileAccountSectionHint =>
      'Consentement IA et actions du compte';

  @override
  String get profileMedicalSectionHint => 'À compléter ou vérifier';

  @override
  String get journalAddTitle => 'Nouvelle mesure';

  @override
  String get journalAddSubtitle => 'Enregistre ce qui vient de se passer.';

  @override
  String get journalGlucose => 'GLYCÉMIE';

  @override
  String get journalNoGlucoseAssumption =>
      'Aucune valeur n’est supposée avant ta saisie.';

  @override
  String get journalLowGlucoseDetected =>
      'Valeur basse détectée — vérifie la mesure ; le message de sécurité apparaîtra à l’enregistrement.';

  @override
  String get journalTargetNotInferred =>
      'Ta cible personnelle n’est pas déduite de cette valeur seule.';

  @override
  String get journalMeasurementContext => 'CONTEXTE DE LA MESURE';

  @override
  String get journalContextHint =>
      'Facultatif — choisis seulement si tu connais le contexte.';

  @override
  String get journalContextFasting => 'À jeun';

  @override
  String get journalContextPreMeal => 'Avant repas';

  @override
  String get journalContextPostMeal => 'Après repas';

  @override
  String get journalContextOther => 'Autre';

  @override
  String get journalAddMeal => 'Ajouter un repas';

  @override
  String get journalMealOptional => 'REPAS (FACULTATIF)';

  @override
  String get journalMealBreakfast => 'Petit-déjeuner';

  @override
  String get journalMealLunch => 'Déjeuner';

  @override
  String get journalMealDinner => 'Dîner';

  @override
  String get journalMealSnack => 'Collation';

  @override
  String get journalMealNoteLabel => 'Note facultative';

  @override
  String get journalMealNoteHint => 'Préparation, détail utile…';

  @override
  String get journalRemoveMeal => 'Retirer le repas';

  @override
  String get journalDetailsButton =>
      'Détails : heure, insuline prise, contexte…';

  @override
  String get journalToday => 'Aujourd’hui';

  @override
  String get journalInsulinTaken => 'INSULINE PRISE';

  @override
  String get journalInsulinExplanation =>
      'Renseigne uniquement une dose déjà administrée. IAmina ne calcule ni ne juge la dose ici.';

  @override
  String get journalDoseTaken => 'Dose réellement prise';

  @override
  String get journalOptional => 'Facultatif';

  @override
  String get journalAdditionalContext => 'CONTEXTE COMPLÉMENTAIRE (FACULTATIF)';

  @override
  String get journalSick => 'Malade';

  @override
  String get journalUnusualStress => 'Stress inhabituel';

  @override
  String get journalPhysicalActivity => 'Activité physique';

  @override
  String get journalPoorSleep => 'Mauvais sommeil';

  @override
  String get journalSave => 'Enregistrer la mesure';

  @override
  String get journalSaving => 'Enregistrement…';

  @override
  String get journalVeryLowTitle => 'Valeur très basse détectée';

  @override
  String get journalLowTitle => 'Valeur basse détectée';

  @override
  String get journalVeryLowSafety =>
      'Cette valeur déclenche le niveau de sécurité prioritaire pour une glycémie basse. Vérifie la mesure et suis le plan d’hypoglycémie établi avec ton équipe soignante.';

  @override
  String get journalLowSafety =>
      'Cette valeur déclenche le parcours de sécurité pour une glycémie basse. Vérifie la mesure et suis le plan d’hypoglycémie établi avec ton équipe soignante.';

  @override
  String get journalBackToEntry => 'Revenir à la saisie';

  @override
  String get journalSaveAnyway => 'Enregistrer quand même';

  @override
  String get journalEditTitle => 'Modifier la mesure';

  @override
  String get journalEditSubtitle =>
      'Corrige uniquement les faits réellement enregistrés.';

  @override
  String get journalEditContextPreserved =>
      'Le repas, le contexte glycémique, l’heure et les autres détails restent inchangés dans cet écran.';

  @override
  String get journalNoInsulinTakenHint =>
      'Laisse vide si aucune insuline n’a été prise pour cette entrée.';

  @override
  String get journalUpdated => 'Mesure mise à jour.';

  @override
  String get journalInvalidGlucose => 'Saisis une glycémie valide.';

  @override
  String get journalInvalidInsulin =>
      'La dose d’insuline saisie n’est pas valide.';

  @override
  String get journalSaved => 'Mesure enregistrée.';

  @override
  String get journalDiscardTitle => 'Abandonner la saisie ?';

  @override
  String get journalDiscardBody =>
      'Les données non enregistrées seront perdues.';

  @override
  String get journalContinueEditing => 'Continuer';

  @override
  String get journalDiscard => 'Abandonner';

  @override
  String get journalBack => 'Retour';

  @override
  String get journalDetailsTitle => 'Détails facultatifs';

  @override
  String get journalMealCaptureTitle => 'CE QUE TU AS MANGÉ';

  @override
  String get journalMealCaptureHint =>
      'Ajoute uniquement ce que tu as réellement mangé. IAmina ne classe pas les aliments comme bons ou mauvais.';

  @override
  String get journalMealSelected => 'Ajoutés';

  @override
  String get journalMealRecent => 'Récents';

  @override
  String get journalMealHabitual => 'Habituels';

  @override
  String get journalMealNoRecent =>
      'Tes aliments récents apparaîtront ici après tes prochains repas.';

  @override
  String get journalMealNoHabitual =>
      'Tes aliments habituels apparaîtront ici avec l’usage.';

  @override
  String get journalMealSearch => 'Rechercher un aliment';

  @override
  String get journalMealSearchHint => 'Pain, œufs, couscous…';

  @override
  String get journalMealSearchEmpty =>
      'Tape au moins 2 caractères pour rechercher.';

  @override
  String get journalMealPhoto => 'Reconnaître une photo';

  @override
  String get journalMealPhotoHint =>
      'La photo est analysée uniquement après ton action et nécessite le consentement IA. Rien n’est ajouté sans ta confirmation.';

  @override
  String get journalMealPhotoProposal => 'Proposition à vérifier';

  @override
  String get journalMealPhotoProposalHint =>
      'Sélectionne ce qui est correct, puis confirme. Utilise la recherche pour corriger ou compléter.';

  @override
  String get journalMealPhotoConfirm => 'Confirmer la sélection';

  @override
  String get journalMealPhotoUnavailable =>
      'Aucun aliment n’a pu être reconnu. Ajoute-les avec la recherche.';

  @override
  String get journalMealPhotoConsent =>
      'La reconnaissance photo nécessite le consentement IA. La saisie manuelle reste disponible.';

  @override
  String get journalNutritionPortionTitle => 'PORTIONS';

  @override
  String get journalNutritionPortionHint =>
      'Choisis une portion naturelle ou indique les grammes si tu les connais. Aucun chiffre nutritionnel n’est inventé.';

  @override
  String get journalNutritionGrams => 'Grammes';

  @override
  String get journalNutritionUnavailable =>
      'Nutrition non chiffrée : donnée ou portion pas encore assez documentée.';

  @override
  String journalNutritionCarbsExact(String value) {
    return '≈ $value g de glucides';
  }

  @override
  String journalNutritionCarbsRange(String low, String high) {
    return '≈ $low–$high g de glucides';
  }

  @override
  String journalNutritionSource(String source) {
    return 'Source : $source';
  }

  @override
  String get ramadanProfileSection => 'Période de Ramadan';

  @override
  String get ramadanProfileHint =>
      'Optionnel. Cette période adapte les noms de repas dans le journal. IAmina n’en déduit pas que tu jeûnes.';

  @override
  String get ramadanNotConfigured => 'Non configurée';

  @override
  String get ramadanStartDate => 'Début';

  @override
  String get ramadanEndDate => 'Fin';

  @override
  String get ramadanChooseDate => 'Choisir une date';

  @override
  String get ramadanClear => 'Effacer la période';

  @override
  String get ramadanSave => 'Enregistrer';

  @override
  String get ramadanSaved => 'Période de Ramadan enregistrée.';

  @override
  String get ramadanSavedLocalOnly =>
      'Enregistrée sur cet appareil. Le serveur n’a pas été mis à jour.';

  @override
  String get ramadanSavedServerOnly =>
      'Enregistrée sur ton compte. Aucun profil local n’était disponible sur cet appareil.';

  @override
  String get ramadanSaveFailed =>
      'Impossible d’enregistrer la période. Réessaie lorsque ton profil est disponible ou que la connexion est rétablie.';

  @override
  String get ramadanNeedsBothDates =>
      'Choisis une date de début et une date de fin, ou efface les deux.';

  @override
  String get ramadanDateOrderError =>
      'La date de début doit précéder ou être égale à la date de fin.';

  @override
  String get journalRamadanMealVocabularyHint =>
      'Repas adaptés à la période enregistrée dans ton profil. Aucun jeûne n’est supposé.';

  @override
  String get journalMealSuhoor => 'Suhoor';

  @override
  String get journalMealIftar => 'Iftar';

  @override
  String get journalMealOther => 'Autre';

  @override
  String get personalResponseTitle => 'Réponses personnelles';

  @override
  String get personalResponseSubtitle =>
      'Répétitions observées dans vos données synchronisées.';

  @override
  String get personalResponseUnavailable =>
      'Analyse indisponible pour le moment';

  @override
  String get personalResponseUnavailableBody =>
      'Le journal reste utilisable. Les motifs réapparaîtront quand les données synchronisées seront accessibles.';

  @override
  String get personalResponseInsufficient => 'Pas encore assez de répétitions';

  @override
  String personalResponseMinimumBasis(int observations, int days) {
    return 'Seuil produit : au moins $observations observations sur $days jours différents.';
  }

  @override
  String personalResponseEvidenceBasis(int observations, int days) {
    return 'Observations : $observations · Jours : $days';
  }

  @override
  String get personalResponsePatternMedian => 'Médiane de ces observations';

  @override
  String personalResponseWindowMedian(int days) {
    return 'Médiane de tous les relevés synchronisés ($days j)';
  }

  @override
  String get personalResponseCausalityNotice =>
      'Association observée dans votre journal. Elle ne prouve pas une cause et ne doit pas guider un traitement ou une dose.';

  @override
  String get personalResponseConfidenceNotice =>
      'Le niveau de répétition décrit seulement la quantité et la répartition de vos données ; ce n’est ni une probabilité ni une confiance clinique.';

  @override
  String get personalResponseSyncedScope =>
      'Basé uniquement sur vos glycémies synchronisées avec votre compte ; les données de démonstration sont exclues.';

  @override
  String get personalResponseEvidenceLimited => 'Répétition limitée';

  @override
  String get personalResponseEvidenceModerate => 'Répétition modérée';

  @override
  String get personalResponseEvidenceStrong => 'Répétition forte';

  @override
  String get personalResponseStress => 'Stress signalé';

  @override
  String get personalResponseActivity => 'Activité physique signalée';

  @override
  String get personalResponseIllness => 'Maladie signalée';

  @override
  String get personalResponsePoorSleep => 'Mauvais sommeil signalé';

  @override
  String get personalResponseFatigue => 'Fatigue signalée';

  @override
  String get personalResponseBreakfast => 'Après petit-déjeuner';

  @override
  String get personalResponseLunch => 'Après déjeuner';

  @override
  String get personalResponseDinner => 'Après dîner';

  @override
  String get personalResponseSnack => 'Après collation';

  @override
  String get personalResponseSuhoor => 'Après Suhoor';

  @override
  String get personalResponseIftar => 'Après Iftar';

  @override
  String get personalResponseObservedPattern => 'Motif observé';

  @override
  String personalResponseShowMore(int count) {
    return 'Afficher $count autres motifs';
  }

  @override
  String get personalResponseShowLess => 'Réduire les motifs';
}
