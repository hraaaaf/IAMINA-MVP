// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'IAmina';

  @override
  String get appSubtitle => 'Diabetes Companion';

  @override
  String get appTagline => 'Your blood sugar balance, every day';

  @override
  String get brandName => 'Diabetes Log';

  @override
  String get brandTagShort => 'AI · AMINA';

  @override
  String get dataPrivacyNote =>
      'External AI services require your consent and valid provider approval';

  @override
  String get sensorStatus => 'Sensor G7 · IAmina';

  @override
  String get login => 'Log in';

  @override
  String get logout => 'Log out';

  @override
  String get signIn => 'Sign in';

  @override
  String get signOut => 'Sign out';

  @override
  String get signOutConfirmTitle => 'Sign out?';

  @override
  String get signOutConfirmBody =>
      'Your data remains saved. You can sign back in at any time.';

  @override
  String get confirmSignOut => 'Sign out';

  @override
  String get createAccount => 'Create account';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get resetPassword => 'Reset password';

  @override
  String get resetPasswordDescription =>
      'Enter your email address. You will receive a link to create a new password.';

  @override
  String get resetEmailSent => 'Email sent — check your inbox.';

  @override
  String get emailNotFound => 'Address not found or invalid email.';

  @override
  String get loginError => 'Incorrect email or password.';

  @override
  String get loginSubtitle => 'Sign in to access your health log.';

  @override
  String get emailLabel => 'Email address';

  @override
  String get emailPlaceholder => 'you@example.com';

  @override
  String get passwordLabel => 'Password';

  @override
  String get send => 'Send';

  @override
  String get or => 'or';

  @override
  String get demoAccess => 'Demo access — 21 days of data';

  @override
  String get dashboard => 'Dashboard';

  @override
  String get addEntry => 'Add entry';

  @override
  String get addMeasurement => 'Add a reading';

  @override
  String get summary => 'IAmina Summary';

  @override
  String get profile => 'Profile';

  @override
  String get myProfile => 'My Profile';

  @override
  String get profileUpdated => 'Profile updated';

  @override
  String get navSectionMain => 'Main';

  @override
  String get navSectionAccount => 'Account';

  @override
  String get navHome => 'Home';

  @override
  String get navIamina => 'IAmina';

  @override
  String get navHistory => 'History';

  @override
  String get navImport => 'Import';

  @override
  String get navSettings => 'Settings';

  @override
  String get navJournal => 'Journal';

  @override
  String get journalSubtitle => 'Full history';

  @override
  String get glucose => 'Glucose';

  @override
  String get insulin => 'Insulin';

  @override
  String get meal => 'Meal';

  @override
  String get fatigue => 'Fatigue';

  @override
  String get sick => 'Sick';

  @override
  String get stressed => 'Stressed';

  @override
  String get freeMeasurement => 'Free reading';

  @override
  String get enterValue => 'Enter a value';

  @override
  String get diabetesType => 'Diabetes type';

  @override
  String get diabetesType1 => 'Type 1 Diabetes';

  @override
  String get diabetesType2 => 'Type 2 Diabetes';

  @override
  String get diabetesGestational => 'Gestational';

  @override
  String get diabetesPreDiabetes => 'Pre-diabetes';

  @override
  String get treatment => 'Treatment';

  @override
  String get treatmentInsulin => 'Insulin';

  @override
  String get treatmentTablets => 'Tablets';

  @override
  String get treatmentLifestyle => 'Lifestyle only';

  @override
  String get glucoseTarget => 'Glucose target (mg/dL)';

  @override
  String get measureUnit => 'Unit of measure';

  @override
  String get dangerZone => 'Danger zone';

  @override
  String get configureWithIamina => 'Configure with IAmina';

  @override
  String get conversationalAssistant => 'Use the conversational assistant';

  @override
  String get journalEmpty => 'Your journal is empty';

  @override
  String get journalEmptySubtitle =>
      'Add your first reading\nto start tracking.';

  @override
  String get last7Days => 'Last 7 days';

  @override
  String get last30Days => 'Last 30 days';

  @override
  String get allHistory => 'All history';

  @override
  String get today => 'TODAY';

  @override
  String get deleteEntryTitle => 'Delete this reading?';

  @override
  String get actionIrreversible => 'This action cannot be undone.';

  @override
  String get entryDeleted => 'Reading deleted';

  @override
  String get consentTitle => 'Privacy & AI';

  @override
  String get consentHeadline =>
      'IAmina may use external AI services for some features';

  @override
  String get consentBody =>
      'With your consent, IAmina may send only the data categories listed above to an external AI service. Data is sent only when the provider, its hosting region, and its retention period are approved for your IAmina environment. Without consent or valid provider approval, no data is sent.\n\nYou can withdraw your consent at any time from your profile.';

  @override
  String get consentDataPoint1 => '📊 Glucose readings and trends';

  @override
  String get consentDataPoint2 => '🍽️ Meal context and insulin doses';

  @override
  String get consentDataPoint3 => '😴 Fatigue and life event markers';

  @override
  String get consentAccept => 'Accept & continue';

  @override
  String get consentDeclineWithoutAI => 'Continue without AI';

  @override
  String get consentAlreadyGiven => 'Consent given';

  @override
  String get consentWithdraw => 'Withdraw AI consent';

  @override
  String get consentWithdrawConfirmTitle => 'Withdraw AI consent?';

  @override
  String get consentWithdrawConfirmBody =>
      'AI features (IAmina Summary, Chat, Voice) will be disabled until you give consent again.';

  @override
  String get consentWithdrawn => 'AI consent withdrawn';

  @override
  String get consentRequired => 'AI consent required to use this feature';

  @override
  String get documentPrivacyTitle => 'External sending only when authorised';

  @override
  String get documentPrivacyBody =>
      'IAmina sends this document to an external service only if you have given consent and the provider of that service is authorised for your IAmina environment. Otherwise, the import is blocked.';

  @override
  String get save => 'Save';

  @override
  String get saveProfile => 'Save';

  @override
  String get cancel => 'Cancel';

  @override
  String get delete => 'Delete';

  @override
  String get edit => 'Edit';

  @override
  String get ok => 'OK';

  @override
  String get error => 'Error';

  @override
  String get loading => 'Loading...';

  @override
  String get noData => 'No data';

  @override
  String get welcome => 'Welcome to IAmina';

  @override
  String get overview => 'Overview';

  @override
  String get breadcrumb => 'Home · Overview';

  @override
  String get talk => 'Talk to IAmina';

  @override
  String get dayShort => 'd';

  @override
  String get syncChecking => 'Checking synchronization';

  @override
  String get syncUpToDate => 'Data up to date';

  @override
  String get syncPending => 'Data waiting to sync';

  @override
  String get syncing => 'Synchronizing';

  @override
  String get syncOffline => 'Offline · data kept on this device';

  @override
  String get syncFailed => 'Synchronization failed · tap to retry';

  @override
  String get goodMorning => 'Good morning';

  @override
  String get goodAfternoon => 'Good afternoon';

  @override
  String get goodEvening => 'Good evening';

  @override
  String greetingWithName(String greeting, String firstName) {
    return '$greeting, $firstName.';
  }

  @override
  String greetingWithoutName(String greeting) {
    return '$greeting!';
  }

  @override
  String observation(int range) {
    return 'Here is what IAmina observed over your last $range days.';
  }

  @override
  String get emptyAnalysis => 'Add data to view your IAmina analysis.';

  @override
  String get latestReading => 'LATEST READING';

  @override
  String get justNow => 'just now';

  @override
  String minutesAgo(int value) {
    return '$value min ago';
  }

  @override
  String get afterMeal => 'After meal';

  @override
  String get fasting => 'Fasting';

  @override
  String targetTitle(int range) {
    return 'READINGS IN RANGE · $range DAYS';
  }

  @override
  String targetCoverage(int count, int days) {
    return '$count readings over $days days · share of recorded readings, not time in range from continuous glucose monitoring (CGM)';
  }

  @override
  String get targetReference =>
      'General reference ≥ 70% · your personal target may differ.';

  @override
  String get viewJournal => 'View journal';

  @override
  String get readingsInRange => 'Readings in range';

  @override
  String get rangeReference => 'Reference 70–180';

  @override
  String get inRange => 'In range';

  @override
  String get high => 'High';

  @override
  String get low => 'Low';

  @override
  String get veryHigh => 'Very high';

  @override
  String get targetExplanation =>
      'General reference: more than 70% of readings within 70–180 mg/dL. Your personal target may differ.';

  @override
  String get importTitle => 'Import';

  @override
  String get importSubtitle => 'Connect your data sources';

  @override
  String get directConnections => 'Direct connections';

  @override
  String get pulperDescription =>
      'PDF · Photo · Excel · Word — IAmina extracts data for your review.';

  @override
  String get labReport => 'Lab report';

  @override
  String get cgmExport => 'Continuous glucose monitoring (CGM) export';

  @override
  String get prescription => 'Prescription';

  @override
  String get photo => 'Photo';

  @override
  String get soon => 'SOON';

  @override
  String get unavailable => 'Unavailable';

  @override
  String get dexcomDescription =>
      'Dexcom CLARITY connection planned. Frequency and availability must be confirmed before activation.';

  @override
  String get libreDescription =>
      'LibreView import planned. Formats and availability must be confirmed before activation.';

  @override
  String get openDocumentImport => 'Open document import';

  @override
  String get documentTitle => 'Import a document';

  @override
  String get documentIntro =>
      'Import a medical document. IAmina extracts the data, then you must review and confirm it.';

  @override
  String get chooseDocument => 'Choose a document';

  @override
  String get profileComplete => 'Profile complete';

  @override
  String get profileCompleteChecked => 'Profile complete ✓';

  @override
  String profileCompletionPercent(int percentage) {
    return 'Profile $percentage% complete';
  }

  @override
  String get profileCompletionPrompt =>
      'Complete your profile for more precise analyses.';

  @override
  String get minimum => 'Min';

  @override
  String get maximum => 'Max';

  @override
  String get onboardingWelcome =>
      'Hello! I am IAmina, your diabetes tracking companion.';

  @override
  String get onboardingChooseLanguage => 'Choose the app language.';

  @override
  String get onboardingChooseCountry => 'Which country do you use IAmina in?';

  @override
  String get onboardingChooseTone => 'Which tone do you prefer?';

  @override
  String get onboardingToneNeutral => 'Neutral and professional';

  @override
  String get onboardingToneFriendly => 'Simple and warm';

  @override
  String get onboardingCountryMorocco => 'Morocco';

  @override
  String get onboardingCountryFrance => 'France';

  @override
  String get onboardingCountryOther => 'Another country';

  @override
  String get onboardingTypeQuestion => 'What type of diabetes do you manage?';

  @override
  String get onboardingTreatmentQuestion => 'What is your main treatment?';

  @override
  String get onboardingTreatmentInsulin => 'Insulin (injection or pump)';

  @override
  String get onboardingTreatmentLifestyle => 'Lifestyle only';

  @override
  String get onboardingTargetQuestion =>
      'What are your glucose targets? The general reference shown is 70–180 mg/dL unless your personal target differs.';

  @override
  String get onboardingTargetStandard => 'General reference (70–180)';

  @override
  String get onboardingTargetCustom => 'Personal target';

  @override
  String get onboardingUnitQuestion => 'Which measurement unit do you prefer?';

  @override
  String get onboardingUnitMg => 'mg/dL';

  @override
  String get onboardingUnitMmol => 'mmol/L';

  @override
  String get onboardingReady =>
      'Your space is configured. You can change these choices in your profile.';

  @override
  String get onboardingStart => 'Start';

  @override
  String get onboardingSaving => 'Saving…';

  @override
  String get onboardingAssistantLabel => 'Setup assistant';

  @override
  String get emptyDashboardTitle => 'Add your first data';

  @override
  String get emptyDashboardBody =>
      'No data has been recorded yet. Add a reading or import a document to build this dashboard from your real data.';

  @override
  String get addFirstMeasurement => 'Add my first reading';

  @override
  String get importDocument => 'Import a document';

  @override
  String get featureRealtimeAgp => 'Sensor trend summary (AGP)';

  @override
  String get featureAiAnalysis => 'AI analysis';

  @override
  String get featurePrivateData => 'Private data';

  @override
  String get analysisLoadError => 'Unable to retrieve analyses.';

  @override
  String get retry => 'Retry';

  @override
  String get analysisLoading => 'IAmina is analysing your data…';

  @override
  String get analysisLoadingWait => 'This takes a few seconds.';

  @override
  String get dashboardLoadingTitle => 'Loading your data';

  @override
  String get dashboardLoadingBody =>
      'IAmina is checking the data stored on this device before showing your dashboard.';

  @override
  String get dashboardLoadErrorTitle => 'Your data cannot be displayed';

  @override
  String get dashboardLoadErrorBody =>
      'The dashboard could not read your local data. You can retry without creating any placeholder data.';

  @override
  String get firstUseTruthNote =>
      'Trends and analyses will appear only when real data is available.';

  @override
  String get profileMedicalSection => 'Medical tracking';

  @override
  String get profileIaminaSection => 'IAmina & preferences';

  @override
  String get profileIaminaSectionHint =>
      'Language, country, tone and setup assistant';

  @override
  String get profileAccountSection => 'Privacy & account';

  @override
  String get profileAccountSectionHint => 'AI consent and account actions';

  @override
  String get profileMedicalSectionHint => 'Complete or review';

  @override
  String get journalAddTitle => 'New reading';

  @override
  String get journalAddSubtitle => 'Record what just happened.';

  @override
  String get journalGlucose => 'GLUCOSE';

  @override
  String get journalNoGlucoseAssumption =>
      'No value is assumed before you enter one.';

  @override
  String get journalLowGlucoseDetected =>
      'Low value detected — verify the reading; the safety message will appear when you save.';

  @override
  String get journalTargetNotInferred =>
      'Your personal target is not inferred from this value alone.';

  @override
  String get journalMeasurementContext => 'MEASUREMENT CONTEXT';

  @override
  String get journalContextHint =>
      'Optional — choose only if you know the context.';

  @override
  String get journalContextFasting => 'Fasting';

  @override
  String get journalContextPreMeal => 'Before meal';

  @override
  String get journalContextPostMeal => 'After meal';

  @override
  String get journalContextOther => 'Other';

  @override
  String get journalAddMeal => 'Add a meal';

  @override
  String get journalMealOptional => 'MEAL (OPTIONAL)';

  @override
  String get journalMealBreakfast => 'Breakfast';

  @override
  String get journalMealLunch => 'Lunch';

  @override
  String get journalMealDinner => 'Dinner';

  @override
  String get journalMealSnack => 'Snack';

  @override
  String get journalMealNoteLabel => 'Optional note';

  @override
  String get journalMealNoteHint => 'Preparation or another useful detail…';

  @override
  String get journalRemoveMeal => 'Remove meal';

  @override
  String get journalDetailsButton => 'Details: time, insulin taken, context…';

  @override
  String get journalToday => 'Today';

  @override
  String get journalInsulinTaken => 'INSULIN TAKEN';

  @override
  String get journalInsulinExplanation =>
      'Enter only a dose you already took. IAmina does not calculate or judge the dose here.';

  @override
  String get journalDoseTaken => 'Dose actually taken';

  @override
  String get journalOptional => 'Optional';

  @override
  String get journalAdditionalContext => 'ADDITIONAL CONTEXT (OPTIONAL)';

  @override
  String get journalSick => 'Sick';

  @override
  String get journalUnusualStress => 'Unusual stress';

  @override
  String get journalPhysicalActivity => 'Physical activity';

  @override
  String get journalPoorSleep => 'Poor sleep';

  @override
  String get journalSave => 'Save reading';

  @override
  String get journalSaving => 'Saving…';

  @override
  String get journalVeryLowTitle => 'Very low value detected';

  @override
  String get journalLowTitle => 'Low value detected';

  @override
  String get journalVeryLowSafety =>
      'This value triggers the priority low-glucose safety path. Verify the reading and follow the hypoglycaemia plan agreed with your care team.';

  @override
  String get journalLowSafety =>
      'This value triggers the low-glucose safety path. Verify the reading and follow the hypoglycaemia plan agreed with your care team.';

  @override
  String get journalBackToEntry => 'Back to entry';

  @override
  String get journalSaveAnyway => 'Save anyway';

  @override
  String get journalInvalidGlucose => 'Enter a valid glucose value.';

  @override
  String get journalInvalidInsulin => 'The insulin dose entered is not valid.';

  @override
  String get journalSaved => 'Reading saved.';

  @override
  String get journalDiscardTitle => 'Discard this entry?';

  @override
  String get journalDiscardBody => 'Unsaved data will be lost.';

  @override
  String get journalContinueEditing => 'Keep editing';

  @override
  String get journalDiscard => 'Discard';

  @override
  String get journalBack => 'Back';

  @override
  String get journalDetailsTitle => 'Optional details';

  @override
  String get journalMealCaptureTitle => 'WHAT YOU ATE';

  @override
  String get journalMealCaptureHint =>
      'Add only what you actually ate. IAmina does not label foods as good or bad.';

  @override
  String get journalMealSelected => 'Added';

  @override
  String get journalMealRecent => 'Recent';

  @override
  String get journalMealHabitual => 'Frequent';

  @override
  String get journalMealNoRecent =>
      'Your recent foods will appear here after your next meals.';

  @override
  String get journalMealNoHabitual =>
      'Your frequent foods will appear here as you use the journal.';

  @override
  String get journalMealSearch => 'Search for a food';

  @override
  String get journalMealSearchHint => 'Bread, eggs, couscous…';

  @override
  String get journalMealSearchEmpty => 'Type at least 2 characters to search.';

  @override
  String get journalMealPhoto => 'Recognize a meal photo';

  @override
  String get journalMealPhotoHint =>
      'The photo is analyzed only after your action and requires AI-processing consent. Nothing is added without your confirmation.';

  @override
  String get journalMealPhotoProposal => 'Proposal to review';

  @override
  String get journalMealPhotoProposalHint =>
      'Select what is correct, then confirm. Use search to correct or complete the meal.';

  @override
  String get journalMealPhotoConfirm => 'Confirm selection';

  @override
  String get journalMealPhotoUnavailable =>
      'No food could be recognized. Add it with search instead.';

  @override
  String get journalMealPhotoConsent =>
      'Photo recognition requires AI-processing consent. Manual entry remains available.';

  @override
  String get journalNutritionPortionTitle => 'PORTIONS';

  @override
  String get journalNutritionPortionHint =>
      'Choose a natural portion or enter grams if you know them. No nutrition number is invented.';

  @override
  String get journalNutritionGrams => 'Grams';

  @override
  String get journalNutritionUnavailable =>
      'No numeric nutrition shown: the food or portion is not documented well enough yet.';

  @override
  String journalNutritionCarbsExact(String value) {
    return '≈ $value g carbohydrates';
  }

  @override
  String journalNutritionCarbsRange(String low, String high) {
    return '≈ $low–$high g carbohydrates';
  }

  @override
  String journalNutritionSource(String source) {
    return 'Source: $source';
  }
}
