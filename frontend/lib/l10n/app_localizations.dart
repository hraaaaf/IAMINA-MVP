import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';
import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en'),
    Locale('fr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'IAmina'**
  String get appTitle;

  /// No description provided for @appSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Diabetes Companion'**
  String get appSubtitle;

  /// No description provided for @appTagline.
  ///
  /// In en, this message translates to:
  /// **'Your blood sugar balance, every day'**
  String get appTagline;

  /// No description provided for @brandName.
  ///
  /// In en, this message translates to:
  /// **'Diabetes Log'**
  String get brandName;

  /// No description provided for @brandTagShort.
  ///
  /// In en, this message translates to:
  /// **'AI · AMINA'**
  String get brandTagShort;

  /// No description provided for @dataPrivacyNote.
  ///
  /// In en, this message translates to:
  /// **'External AI services require your consent and valid provider approval'**
  String get dataPrivacyNote;

  /// No description provided for @sensorStatus.
  ///
  /// In en, this message translates to:
  /// **'Sensor G7 · IAmina'**
  String get sensorStatus;

  /// No description provided for @login.
  ///
  /// In en, this message translates to:
  /// **'Log in'**
  String get login;

  /// No description provided for @logout.
  ///
  /// In en, this message translates to:
  /// **'Log out'**
  String get logout;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;

  /// No description provided for @signOutConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign out?'**
  String get signOutConfirmTitle;

  /// No description provided for @signOutConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'Your data remains saved. You can sign back in at any time.'**
  String get signOutConfirmBody;

  /// No description provided for @confirmSignOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get confirmSignOut;

  /// No description provided for @createAccount.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get createAccount;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @resetPassword.
  ///
  /// In en, this message translates to:
  /// **'Reset password'**
  String get resetPassword;

  /// No description provided for @resetPasswordDescription.
  ///
  /// In en, this message translates to:
  /// **'Enter your email address. You will receive a link to create a new password.'**
  String get resetPasswordDescription;

  /// No description provided for @resetEmailSent.
  ///
  /// In en, this message translates to:
  /// **'Email sent — check your inbox.'**
  String get resetEmailSent;

  /// No description provided for @emailNotFound.
  ///
  /// In en, this message translates to:
  /// **'Address not found or invalid email.'**
  String get emailNotFound;

  /// No description provided for @loginError.
  ///
  /// In en, this message translates to:
  /// **'Incorrect email or password.'**
  String get loginError;

  /// No description provided for @loginSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to access your health log.'**
  String get loginSubtitle;

  /// No description provided for @emailLabel.
  ///
  /// In en, this message translates to:
  /// **'Email address'**
  String get emailLabel;

  /// No description provided for @emailPlaceholder.
  ///
  /// In en, this message translates to:
  /// **'you@example.com'**
  String get emailPlaceholder;

  /// No description provided for @passwordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get passwordLabel;

  /// No description provided for @send.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get send;

  /// No description provided for @or.
  ///
  /// In en, this message translates to:
  /// **'or'**
  String get or;

  /// No description provided for @demoAccess.
  ///
  /// In en, this message translates to:
  /// **'Demo access — 21 days of data'**
  String get demoAccess;

  /// No description provided for @dashboard.
  ///
  /// In en, this message translates to:
  /// **'Dashboard'**
  String get dashboard;

  /// No description provided for @addEntry.
  ///
  /// In en, this message translates to:
  /// **'Add entry'**
  String get addEntry;

  /// No description provided for @addMeasurement.
  ///
  /// In en, this message translates to:
  /// **'Add a reading'**
  String get addMeasurement;

  /// No description provided for @summary.
  ///
  /// In en, this message translates to:
  /// **'IAmina Summary'**
  String get summary;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @myProfile.
  ///
  /// In en, this message translates to:
  /// **'My Profile'**
  String get myProfile;

  /// No description provided for @profileUpdated.
  ///
  /// In en, this message translates to:
  /// **'Profile updated'**
  String get profileUpdated;

  /// No description provided for @navSectionMain.
  ///
  /// In en, this message translates to:
  /// **'Main'**
  String get navSectionMain;

  /// No description provided for @navSectionAccount.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get navSectionAccount;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navIamina.
  ///
  /// In en, this message translates to:
  /// **'IAmina'**
  String get navIamina;

  /// No description provided for @navHistory.
  ///
  /// In en, this message translates to:
  /// **'History'**
  String get navHistory;

  /// No description provided for @navImport.
  ///
  /// In en, this message translates to:
  /// **'Import'**
  String get navImport;

  /// No description provided for @navSettings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get navSettings;

  /// No description provided for @navJournal.
  ///
  /// In en, this message translates to:
  /// **'Journal'**
  String get navJournal;

  /// No description provided for @journalSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Full history'**
  String get journalSubtitle;

  /// No description provided for @glucose.
  ///
  /// In en, this message translates to:
  /// **'Glucose'**
  String get glucose;

  /// No description provided for @insulin.
  ///
  /// In en, this message translates to:
  /// **'Insulin'**
  String get insulin;

  /// No description provided for @meal.
  ///
  /// In en, this message translates to:
  /// **'Meal'**
  String get meal;

  /// No description provided for @fatigue.
  ///
  /// In en, this message translates to:
  /// **'Fatigue'**
  String get fatigue;

  /// No description provided for @sick.
  ///
  /// In en, this message translates to:
  /// **'Sick'**
  String get sick;

  /// No description provided for @stressed.
  ///
  /// In en, this message translates to:
  /// **'Stressed'**
  String get stressed;

  /// No description provided for @freeMeasurement.
  ///
  /// In en, this message translates to:
  /// **'Free reading'**
  String get freeMeasurement;

  /// No description provided for @enterValue.
  ///
  /// In en, this message translates to:
  /// **'Enter a value'**
  String get enterValue;

  /// No description provided for @diabetesType.
  ///
  /// In en, this message translates to:
  /// **'Diabetes type'**
  String get diabetesType;

  /// No description provided for @diabetesType1.
  ///
  /// In en, this message translates to:
  /// **'Type 1 Diabetes'**
  String get diabetesType1;

  /// No description provided for @diabetesType2.
  ///
  /// In en, this message translates to:
  /// **'Type 2 Diabetes'**
  String get diabetesType2;

  /// No description provided for @diabetesGestational.
  ///
  /// In en, this message translates to:
  /// **'Gestational'**
  String get diabetesGestational;

  /// No description provided for @diabetesPreDiabetes.
  ///
  /// In en, this message translates to:
  /// **'Pre-diabetes'**
  String get diabetesPreDiabetes;

  /// No description provided for @treatment.
  ///
  /// In en, this message translates to:
  /// **'Treatment'**
  String get treatment;

  /// No description provided for @treatmentInsulin.
  ///
  /// In en, this message translates to:
  /// **'Insulin'**
  String get treatmentInsulin;

  /// No description provided for @treatmentTablets.
  ///
  /// In en, this message translates to:
  /// **'Tablets'**
  String get treatmentTablets;

  /// No description provided for @treatmentLifestyle.
  ///
  /// In en, this message translates to:
  /// **'Lifestyle only'**
  String get treatmentLifestyle;

  /// No description provided for @glucoseTarget.
  ///
  /// In en, this message translates to:
  /// **'Glucose target (mg/dL)'**
  String get glucoseTarget;

  /// No description provided for @measureUnit.
  ///
  /// In en, this message translates to:
  /// **'Unit of measure'**
  String get measureUnit;

  /// No description provided for @dangerZone.
  ///
  /// In en, this message translates to:
  /// **'Danger zone'**
  String get dangerZone;

  /// No description provided for @configureWithIamina.
  ///
  /// In en, this message translates to:
  /// **'Configure with IAmina'**
  String get configureWithIamina;

  /// No description provided for @conversationalAssistant.
  ///
  /// In en, this message translates to:
  /// **'Use the conversational assistant'**
  String get conversationalAssistant;

  /// No description provided for @journalEmpty.
  ///
  /// In en, this message translates to:
  /// **'Your journal is empty'**
  String get journalEmpty;

  /// No description provided for @journalEmptySubtitle.
  ///
  /// In en, this message translates to:
  /// **'Add your first reading\nto start tracking.'**
  String get journalEmptySubtitle;

  /// No description provided for @last7Days.
  ///
  /// In en, this message translates to:
  /// **'Last 7 days'**
  String get last7Days;

  /// No description provided for @last30Days.
  ///
  /// In en, this message translates to:
  /// **'Last 30 days'**
  String get last30Days;

  /// No description provided for @allHistory.
  ///
  /// In en, this message translates to:
  /// **'All history'**
  String get allHistory;

  /// No description provided for @today.
  ///
  /// In en, this message translates to:
  /// **'TODAY'**
  String get today;

  /// No description provided for @deleteEntryTitle.
  ///
  /// In en, this message translates to:
  /// **'Delete this reading?'**
  String get deleteEntryTitle;

  /// No description provided for @actionIrreversible.
  ///
  /// In en, this message translates to:
  /// **'This action cannot be undone.'**
  String get actionIrreversible;

  /// No description provided for @entryDeleted.
  ///
  /// In en, this message translates to:
  /// **'Reading deleted'**
  String get entryDeleted;

  /// No description provided for @consentTitle.
  ///
  /// In en, this message translates to:
  /// **'Privacy & AI'**
  String get consentTitle;

  /// No description provided for @consentHeadline.
  ///
  /// In en, this message translates to:
  /// **'IAmina may use external AI services for some features'**
  String get consentHeadline;

  /// No description provided for @consentBody.
  ///
  /// In en, this message translates to:
  /// **'With your consent, IAmina may send only the data categories listed above to an external AI service. Data is sent only when the provider, its hosting region, and its retention period are approved for your IAmina environment. Without consent or valid provider approval, no data is sent.\n\nYou can withdraw your consent at any time from your profile.'**
  String get consentBody;

  /// No description provided for @consentDataPoint1.
  ///
  /// In en, this message translates to:
  /// **'📊 Glucose readings and trends'**
  String get consentDataPoint1;

  /// No description provided for @consentDataPoint2.
  ///
  /// In en, this message translates to:
  /// **'🍽️ Meal context and insulin doses'**
  String get consentDataPoint2;

  /// No description provided for @consentDataPoint3.
  ///
  /// In en, this message translates to:
  /// **'😴 Fatigue and life event markers'**
  String get consentDataPoint3;

  /// No description provided for @consentAccept.
  ///
  /// In en, this message translates to:
  /// **'Accept & continue'**
  String get consentAccept;

  /// No description provided for @consentDeclineWithoutAI.
  ///
  /// In en, this message translates to:
  /// **'Continue without AI'**
  String get consentDeclineWithoutAI;

  /// No description provided for @consentAlreadyGiven.
  ///
  /// In en, this message translates to:
  /// **'Consent given'**
  String get consentAlreadyGiven;

  /// No description provided for @consentWithdraw.
  ///
  /// In en, this message translates to:
  /// **'Withdraw AI consent'**
  String get consentWithdraw;

  /// No description provided for @consentWithdrawConfirmTitle.
  ///
  /// In en, this message translates to:
  /// **'Withdraw AI consent?'**
  String get consentWithdrawConfirmTitle;

  /// No description provided for @consentWithdrawConfirmBody.
  ///
  /// In en, this message translates to:
  /// **'AI features (IAmina Summary, Chat, Voice) will be disabled until you give consent again.'**
  String get consentWithdrawConfirmBody;

  /// No description provided for @consentWithdrawn.
  ///
  /// In en, this message translates to:
  /// **'AI consent withdrawn'**
  String get consentWithdrawn;

  /// No description provided for @consentRequired.
  ///
  /// In en, this message translates to:
  /// **'AI consent required to use this feature'**
  String get consentRequired;

  /// No description provided for @documentPrivacyTitle.
  ///
  /// In en, this message translates to:
  /// **'External sending only when authorised'**
  String get documentPrivacyTitle;

  /// No description provided for @documentPrivacyBody.
  ///
  /// In en, this message translates to:
  /// **'IAmina sends this document to an external service only if you have given consent and the provider of that service is authorised for your IAmina environment. Otherwise, the import is blocked.'**
  String get documentPrivacyBody;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @saveProfile.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveProfile;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @ok.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get ok;

  /// No description provided for @error.
  ///
  /// In en, this message translates to:
  /// **'Error'**
  String get error;

  /// No description provided for @loading.
  ///
  /// In en, this message translates to:
  /// **'Loading...'**
  String get loading;

  /// No description provided for @noData.
  ///
  /// In en, this message translates to:
  /// **'No data'**
  String get noData;

  /// No description provided for @welcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome to IAmina'**
  String get welcome;

  /// No description provided for @overview.
  ///
  /// In en, this message translates to:
  /// **'Overview'**
  String get overview;

  /// No description provided for @breadcrumb.
  ///
  /// In en, this message translates to:
  /// **'Home · Overview'**
  String get breadcrumb;

  /// No description provided for @talk.
  ///
  /// In en, this message translates to:
  /// **'Talk to IAmina'**
  String get talk;

  /// No description provided for @dayShort.
  ///
  /// In en, this message translates to:
  /// **'d'**
  String get dayShort;

  /// No description provided for @syncChecking.
  ///
  /// In en, this message translates to:
  /// **'Checking synchronization'**
  String get syncChecking;

  /// No description provided for @syncUpToDate.
  ///
  /// In en, this message translates to:
  /// **'Data up to date'**
  String get syncUpToDate;

  /// No description provided for @syncPending.
  ///
  /// In en, this message translates to:
  /// **'Data waiting to sync'**
  String get syncPending;

  /// No description provided for @syncing.
  ///
  /// In en, this message translates to:
  /// **'Synchronizing'**
  String get syncing;

  /// No description provided for @syncOffline.
  ///
  /// In en, this message translates to:
  /// **'Offline · data kept on this device'**
  String get syncOffline;

  /// No description provided for @syncFailed.
  ///
  /// In en, this message translates to:
  /// **'Synchronization failed · tap to retry'**
  String get syncFailed;

  /// No description provided for @goodMorning.
  ///
  /// In en, this message translates to:
  /// **'Good morning'**
  String get goodMorning;

  /// No description provided for @goodAfternoon.
  ///
  /// In en, this message translates to:
  /// **'Good afternoon'**
  String get goodAfternoon;

  /// No description provided for @goodEvening.
  ///
  /// In en, this message translates to:
  /// **'Good evening'**
  String get goodEvening;

  /// No description provided for @greetingWithName.
  ///
  /// In en, this message translates to:
  /// **'{greeting}, {firstName}.'**
  String greetingWithName(String greeting, String firstName);

  /// No description provided for @greetingWithoutName.
  ///
  /// In en, this message translates to:
  /// **'{greeting}!'**
  String greetingWithoutName(String greeting);

  /// No description provided for @observation.
  ///
  /// In en, this message translates to:
  /// **'Here is what IAmina observed over your last {range} days.'**
  String observation(int range);

  /// No description provided for @emptyAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Add data to view your IAmina analysis.'**
  String get emptyAnalysis;

  /// No description provided for @latestReading.
  ///
  /// In en, this message translates to:
  /// **'LATEST READING'**
  String get latestReading;

  /// No description provided for @justNow.
  ///
  /// In en, this message translates to:
  /// **'just now'**
  String get justNow;

  /// No description provided for @minutesAgo.
  ///
  /// In en, this message translates to:
  /// **'{value} min ago'**
  String minutesAgo(int value);

  /// No description provided for @afterMeal.
  ///
  /// In en, this message translates to:
  /// **'After meal'**
  String get afterMeal;

  /// No description provided for @fasting.
  ///
  /// In en, this message translates to:
  /// **'Fasting'**
  String get fasting;

  /// No description provided for @targetTitle.
  ///
  /// In en, this message translates to:
  /// **'READINGS IN RANGE · {range} DAYS'**
  String targetTitle(int range);

  /// No description provided for @targetCoverage.
  ///
  /// In en, this message translates to:
  /// **'{count} readings over {days} days · share of recorded readings, not time in range from continuous glucose monitoring (CGM)'**
  String targetCoverage(int count, int days);

  /// No description provided for @targetReference.
  ///
  /// In en, this message translates to:
  /// **'General reference ≥ 70% · your personal target may differ.'**
  String get targetReference;

  /// No description provided for @viewJournal.
  ///
  /// In en, this message translates to:
  /// **'View journal'**
  String get viewJournal;

  /// No description provided for @readingsInRange.
  ///
  /// In en, this message translates to:
  /// **'Readings in range'**
  String get readingsInRange;

  /// No description provided for @rangeReference.
  ///
  /// In en, this message translates to:
  /// **'Reference 70–180'**
  String get rangeReference;

  /// No description provided for @inRange.
  ///
  /// In en, this message translates to:
  /// **'In range'**
  String get inRange;

  /// No description provided for @high.
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get high;

  /// No description provided for @low.
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get low;

  /// No description provided for @veryHigh.
  ///
  /// In en, this message translates to:
  /// **'Very high'**
  String get veryHigh;

  /// No description provided for @targetExplanation.
  ///
  /// In en, this message translates to:
  /// **'General reference: more than 70% of readings within 70–180 mg/dL. Your personal target may differ.'**
  String get targetExplanation;

  /// No description provided for @importTitle.
  ///
  /// In en, this message translates to:
  /// **'Import'**
  String get importTitle;

  /// No description provided for @importSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Connect your data sources'**
  String get importSubtitle;

  /// No description provided for @directConnections.
  ///
  /// In en, this message translates to:
  /// **'Direct connections'**
  String get directConnections;

  /// No description provided for @pulperDescription.
  ///
  /// In en, this message translates to:
  /// **'PDF · Photo · Excel · Word — IAmina extracts data for your review.'**
  String get pulperDescription;

  /// No description provided for @labReport.
  ///
  /// In en, this message translates to:
  /// **'Lab report'**
  String get labReport;

  /// No description provided for @cgmExport.
  ///
  /// In en, this message translates to:
  /// **'Continuous glucose monitoring (CGM) export'**
  String get cgmExport;

  /// No description provided for @prescription.
  ///
  /// In en, this message translates to:
  /// **'Prescription'**
  String get prescription;

  /// No description provided for @photo.
  ///
  /// In en, this message translates to:
  /// **'Photo'**
  String get photo;

  /// No description provided for @soon.
  ///
  /// In en, this message translates to:
  /// **'SOON'**
  String get soon;

  /// No description provided for @unavailable.
  ///
  /// In en, this message translates to:
  /// **'Unavailable'**
  String get unavailable;

  /// No description provided for @dexcomDescription.
  ///
  /// In en, this message translates to:
  /// **'Dexcom CLARITY connection planned. Frequency and availability must be confirmed before activation.'**
  String get dexcomDescription;

  /// No description provided for @libreDescription.
  ///
  /// In en, this message translates to:
  /// **'LibreView import planned. Formats and availability must be confirmed before activation.'**
  String get libreDescription;

  /// No description provided for @openDocumentImport.
  ///
  /// In en, this message translates to:
  /// **'Open document import'**
  String get openDocumentImport;

  /// No description provided for @documentTitle.
  ///
  /// In en, this message translates to:
  /// **'Import a document'**
  String get documentTitle;

  /// No description provided for @documentIntro.
  ///
  /// In en, this message translates to:
  /// **'Import a medical document. IAmina extracts the data, then you must review and confirm it.'**
  String get documentIntro;

  /// No description provided for @chooseDocument.
  ///
  /// In en, this message translates to:
  /// **'Choose a document'**
  String get chooseDocument;

  /// No description provided for @profileComplete.
  ///
  /// In en, this message translates to:
  /// **'Profile complete'**
  String get profileComplete;

  /// No description provided for @profileCompleteChecked.
  ///
  /// In en, this message translates to:
  /// **'Profile complete ✓'**
  String get profileCompleteChecked;

  /// No description provided for @profileCompletionPercent.
  ///
  /// In en, this message translates to:
  /// **'Profile {percentage}% complete'**
  String profileCompletionPercent(int percentage);

  /// No description provided for @profileCompletionPrompt.
  ///
  /// In en, this message translates to:
  /// **'Complete your profile for more precise analyses.'**
  String get profileCompletionPrompt;

  /// No description provided for @minimum.
  ///
  /// In en, this message translates to:
  /// **'Min'**
  String get minimum;

  /// No description provided for @maximum.
  ///
  /// In en, this message translates to:
  /// **'Max'**
  String get maximum;

  /// No description provided for @onboardingWelcome.
  ///
  /// In en, this message translates to:
  /// **'Hello! I am IAmina, your diabetes tracking companion.'**
  String get onboardingWelcome;

  /// No description provided for @onboardingChooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose the app language.'**
  String get onboardingChooseLanguage;

  /// No description provided for @onboardingChooseCountry.
  ///
  /// In en, this message translates to:
  /// **'Which country do you use IAmina in?'**
  String get onboardingChooseCountry;

  /// No description provided for @onboardingChooseTone.
  ///
  /// In en, this message translates to:
  /// **'Which tone do you prefer?'**
  String get onboardingChooseTone;

  /// No description provided for @onboardingToneNeutral.
  ///
  /// In en, this message translates to:
  /// **'Neutral and professional'**
  String get onboardingToneNeutral;

  /// No description provided for @onboardingToneFriendly.
  ///
  /// In en, this message translates to:
  /// **'Simple and warm'**
  String get onboardingToneFriendly;

  /// No description provided for @onboardingCountryMorocco.
  ///
  /// In en, this message translates to:
  /// **'Morocco'**
  String get onboardingCountryMorocco;

  /// No description provided for @onboardingCountryFrance.
  ///
  /// In en, this message translates to:
  /// **'France'**
  String get onboardingCountryFrance;

  /// No description provided for @onboardingCountryOther.
  ///
  /// In en, this message translates to:
  /// **'Another country'**
  String get onboardingCountryOther;

  /// No description provided for @onboardingTypeQuestion.
  ///
  /// In en, this message translates to:
  /// **'What type of diabetes do you manage?'**
  String get onboardingTypeQuestion;

  /// No description provided for @onboardingTreatmentQuestion.
  ///
  /// In en, this message translates to:
  /// **'What is your main treatment?'**
  String get onboardingTreatmentQuestion;

  /// No description provided for @onboardingTreatmentInsulin.
  ///
  /// In en, this message translates to:
  /// **'Insulin (injection or pump)'**
  String get onboardingTreatmentInsulin;

  /// No description provided for @onboardingTreatmentLifestyle.
  ///
  /// In en, this message translates to:
  /// **'Lifestyle only'**
  String get onboardingTreatmentLifestyle;

  /// No description provided for @onboardingTargetQuestion.
  ///
  /// In en, this message translates to:
  /// **'What are your glucose targets? The general reference shown is 70–180 mg/dL unless your personal target differs.'**
  String get onboardingTargetQuestion;

  /// No description provided for @onboardingTargetStandard.
  ///
  /// In en, this message translates to:
  /// **'General reference (70–180)'**
  String get onboardingTargetStandard;

  /// No description provided for @onboardingTargetCustom.
  ///
  /// In en, this message translates to:
  /// **'Personal target'**
  String get onboardingTargetCustom;

  /// No description provided for @onboardingUnitQuestion.
  ///
  /// In en, this message translates to:
  /// **'Which measurement unit do you prefer?'**
  String get onboardingUnitQuestion;

  /// No description provided for @onboardingUnitMg.
  ///
  /// In en, this message translates to:
  /// **'mg/dL'**
  String get onboardingUnitMg;

  /// No description provided for @onboardingUnitMmol.
  ///
  /// In en, this message translates to:
  /// **'mmol/L'**
  String get onboardingUnitMmol;

  /// No description provided for @onboardingReady.
  ///
  /// In en, this message translates to:
  /// **'Your space is configured. You can change these choices in your profile.'**
  String get onboardingReady;

  /// No description provided for @onboardingStart.
  ///
  /// In en, this message translates to:
  /// **'Start'**
  String get onboardingStart;

  /// No description provided for @onboardingSaving.
  ///
  /// In en, this message translates to:
  /// **'Saving…'**
  String get onboardingSaving;

  /// No description provided for @onboardingAssistantLabel.
  ///
  /// In en, this message translates to:
  /// **'Setup assistant'**
  String get onboardingAssistantLabel;

  /// No description provided for @emptyDashboardTitle.
  ///
  /// In en, this message translates to:
  /// **'Add your first data'**
  String get emptyDashboardTitle;

  /// No description provided for @emptyDashboardBody.
  ///
  /// In en, this message translates to:
  /// **'No data has been recorded yet. Add a reading or import a document to build this dashboard from your real data.'**
  String get emptyDashboardBody;

  /// No description provided for @addFirstMeasurement.
  ///
  /// In en, this message translates to:
  /// **'Add my first reading'**
  String get addFirstMeasurement;

  /// No description provided for @importDocument.
  ///
  /// In en, this message translates to:
  /// **'Import a document'**
  String get importDocument;

  /// No description provided for @featureRealtimeAgp.
  ///
  /// In en, this message translates to:
  /// **'Sensor trend summary (AGP)'**
  String get featureRealtimeAgp;

  /// No description provided for @featureAiAnalysis.
  ///
  /// In en, this message translates to:
  /// **'AI analysis'**
  String get featureAiAnalysis;

  /// No description provided for @featurePrivateData.
  ///
  /// In en, this message translates to:
  /// **'Private data'**
  String get featurePrivateData;

  /// No description provided for @analysisLoadError.
  ///
  /// In en, this message translates to:
  /// **'Unable to retrieve analyses.'**
  String get analysisLoadError;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @analysisLoading.
  ///
  /// In en, this message translates to:
  /// **'IAmina is analysing your data…'**
  String get analysisLoading;

  /// No description provided for @analysisLoadingWait.
  ///
  /// In en, this message translates to:
  /// **'This takes a few seconds.'**
  String get analysisLoadingWait;

  /// No description provided for @dashboardLoadingTitle.
  ///
  /// In en, this message translates to:
  /// **'Loading your data'**
  String get dashboardLoadingTitle;

  /// No description provided for @dashboardLoadingBody.
  ///
  /// In en, this message translates to:
  /// **'IAmina is checking the data stored on this device before showing your dashboard.'**
  String get dashboardLoadingBody;

  /// No description provided for @dashboardLoadErrorTitle.
  ///
  /// In en, this message translates to:
  /// **'Your data cannot be displayed'**
  String get dashboardLoadErrorTitle;

  /// No description provided for @dashboardLoadErrorBody.
  ///
  /// In en, this message translates to:
  /// **'The dashboard could not read your local data. You can retry without creating any placeholder data.'**
  String get dashboardLoadErrorBody;

  /// No description provided for @firstUseTruthNote.
  ///
  /// In en, this message translates to:
  /// **'Trends and analyses will appear only when real data is available.'**
  String get firstUseTruthNote;

  /// No description provided for @profileMedicalSection.
  ///
  /// In en, this message translates to:
  /// **'Medical tracking'**
  String get profileMedicalSection;

  /// No description provided for @profileIaminaSection.
  ///
  /// In en, this message translates to:
  /// **'IAmina & preferences'**
  String get profileIaminaSection;

  /// No description provided for @profileIaminaSectionHint.
  ///
  /// In en, this message translates to:
  /// **'Language, country, tone and setup assistant'**
  String get profileIaminaSectionHint;

  /// No description provided for @profileAccountSection.
  ///
  /// In en, this message translates to:
  /// **'Privacy & account'**
  String get profileAccountSection;

  /// No description provided for @profileAccountSectionHint.
  ///
  /// In en, this message translates to:
  /// **'AI consent and account actions'**
  String get profileAccountSectionHint;

  /// No description provided for @profileMedicalSectionHint.
  ///
  /// In en, this message translates to:
  /// **'Complete or review'**
  String get profileMedicalSectionHint;

  /// No description provided for @journalAddTitle.
  ///
  /// In en, this message translates to:
  /// **'New reading'**
  String get journalAddTitle;

  /// No description provided for @journalAddSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Record what just happened.'**
  String get journalAddSubtitle;

  /// No description provided for @journalGlucose.
  ///
  /// In en, this message translates to:
  /// **'GLUCOSE'**
  String get journalGlucose;

  /// No description provided for @journalNoGlucoseAssumption.
  ///
  /// In en, this message translates to:
  /// **'No value is assumed before you enter one.'**
  String get journalNoGlucoseAssumption;

  /// No description provided for @journalLowGlucoseDetected.
  ///
  /// In en, this message translates to:
  /// **'Low value detected — verify the reading; the safety message will appear when you save.'**
  String get journalLowGlucoseDetected;

  /// No description provided for @journalTargetNotInferred.
  ///
  /// In en, this message translates to:
  /// **'Your personal target is not inferred from this value alone.'**
  String get journalTargetNotInferred;

  /// No description provided for @journalMeasurementContext.
  ///
  /// In en, this message translates to:
  /// **'MEASUREMENT CONTEXT'**
  String get journalMeasurementContext;

  /// No description provided for @journalContextHint.
  ///
  /// In en, this message translates to:
  /// **'Optional — choose only if you know the context.'**
  String get journalContextHint;

  /// No description provided for @journalContextFasting.
  ///
  /// In en, this message translates to:
  /// **'Fasting'**
  String get journalContextFasting;

  /// No description provided for @journalContextPreMeal.
  ///
  /// In en, this message translates to:
  /// **'Before meal'**
  String get journalContextPreMeal;

  /// No description provided for @journalContextPostMeal.
  ///
  /// In en, this message translates to:
  /// **'After meal'**
  String get journalContextPostMeal;

  /// No description provided for @journalContextOther.
  ///
  /// In en, this message translates to:
  /// **'Other'**
  String get journalContextOther;

  /// No description provided for @journalAddMeal.
  ///
  /// In en, this message translates to:
  /// **'Add a meal'**
  String get journalAddMeal;

  /// No description provided for @journalMealOptional.
  ///
  /// In en, this message translates to:
  /// **'MEAL (OPTIONAL)'**
  String get journalMealOptional;

  /// No description provided for @journalMealBreakfast.
  ///
  /// In en, this message translates to:
  /// **'Breakfast'**
  String get journalMealBreakfast;

  /// No description provided for @journalMealLunch.
  ///
  /// In en, this message translates to:
  /// **'Lunch'**
  String get journalMealLunch;

  /// No description provided for @journalMealDinner.
  ///
  /// In en, this message translates to:
  /// **'Dinner'**
  String get journalMealDinner;

  /// No description provided for @journalMealSnack.
  ///
  /// In en, this message translates to:
  /// **'Snack'**
  String get journalMealSnack;

  /// No description provided for @journalMealNoteLabel.
  ///
  /// In en, this message translates to:
  /// **'Optional note'**
  String get journalMealNoteLabel;

  /// No description provided for @journalMealNoteHint.
  ///
  /// In en, this message translates to:
  /// **'Preparation or another useful detail…'**
  String get journalMealNoteHint;

  /// No description provided for @journalRemoveMeal.
  ///
  /// In en, this message translates to:
  /// **'Remove meal'**
  String get journalRemoveMeal;

  /// No description provided for @journalDetailsButton.
  ///
  /// In en, this message translates to:
  /// **'Details: time, insulin taken, context…'**
  String get journalDetailsButton;

  /// No description provided for @journalToday.
  ///
  /// In en, this message translates to:
  /// **'Today'**
  String get journalToday;

  /// No description provided for @journalInsulinTaken.
  ///
  /// In en, this message translates to:
  /// **'INSULIN TAKEN'**
  String get journalInsulinTaken;

  /// No description provided for @journalInsulinExplanation.
  ///
  /// In en, this message translates to:
  /// **'Enter only a dose you already took. IAmina does not calculate or judge the dose here.'**
  String get journalInsulinExplanation;

  /// No description provided for @journalDoseTaken.
  ///
  /// In en, this message translates to:
  /// **'Dose actually taken'**
  String get journalDoseTaken;

  /// No description provided for @journalOptional.
  ///
  /// In en, this message translates to:
  /// **'Optional'**
  String get journalOptional;

  /// No description provided for @journalAdditionalContext.
  ///
  /// In en, this message translates to:
  /// **'ADDITIONAL CONTEXT (OPTIONAL)'**
  String get journalAdditionalContext;

  /// No description provided for @journalSick.
  ///
  /// In en, this message translates to:
  /// **'Sick'**
  String get journalSick;

  /// No description provided for @journalUnusualStress.
  ///
  /// In en, this message translates to:
  /// **'Unusual stress'**
  String get journalUnusualStress;

  /// No description provided for @journalPhysicalActivity.
  ///
  /// In en, this message translates to:
  /// **'Physical activity'**
  String get journalPhysicalActivity;

  /// No description provided for @journalPoorSleep.
  ///
  /// In en, this message translates to:
  /// **'Poor sleep'**
  String get journalPoorSleep;

  /// No description provided for @journalSave.
  ///
  /// In en, this message translates to:
  /// **'Save reading'**
  String get journalSave;

  /// No description provided for @journalSaving.
  ///
  /// In en, this message translates to:
  /// **'Saving…'**
  String get journalSaving;

  /// No description provided for @journalVeryLowTitle.
  ///
  /// In en, this message translates to:
  /// **'Very low value detected'**
  String get journalVeryLowTitle;

  /// No description provided for @journalLowTitle.
  ///
  /// In en, this message translates to:
  /// **'Low value detected'**
  String get journalLowTitle;

  /// No description provided for @journalVeryLowSafety.
  ///
  /// In en, this message translates to:
  /// **'This value triggers the priority low-glucose safety path. Verify the reading and follow the hypoglycaemia plan agreed with your care team.'**
  String get journalVeryLowSafety;

  /// No description provided for @journalLowSafety.
  ///
  /// In en, this message translates to:
  /// **'This value triggers the low-glucose safety path. Verify the reading and follow the hypoglycaemia plan agreed with your care team.'**
  String get journalLowSafety;

  /// No description provided for @journalBackToEntry.
  ///
  /// In en, this message translates to:
  /// **'Back to entry'**
  String get journalBackToEntry;

  /// No description provided for @journalSaveAnyway.
  ///
  /// In en, this message translates to:
  /// **'Save anyway'**
  String get journalSaveAnyway;

  /// No description provided for @journalEditTitle.
  ///
  /// In en, this message translates to:
  /// **'Edit measurement'**
  String get journalEditTitle;

  /// No description provided for @journalEditSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Correct only the facts that were actually recorded.'**
  String get journalEditSubtitle;

  /// No description provided for @journalEditContextPreserved.
  ///
  /// In en, this message translates to:
  /// **'Meal, glucose context, time and other details stay unchanged on this screen.'**
  String get journalEditContextPreserved;

  /// No description provided for @journalNoInsulinTakenHint.
  ///
  /// In en, this message translates to:
  /// **'Leave blank if no insulin was taken for this entry.'**
  String get journalNoInsulinTakenHint;

  /// No description provided for @journalUpdated.
  ///
  /// In en, this message translates to:
  /// **'Measurement updated.'**
  String get journalUpdated;

  /// No description provided for @journalInvalidGlucose.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid glucose value.'**
  String get journalInvalidGlucose;

  /// No description provided for @journalInvalidInsulin.
  ///
  /// In en, this message translates to:
  /// **'The insulin dose entered is not valid.'**
  String get journalInvalidInsulin;

  /// No description provided for @journalSaved.
  ///
  /// In en, this message translates to:
  /// **'Reading saved.'**
  String get journalSaved;

  /// No description provided for @journalDiscardTitle.
  ///
  /// In en, this message translates to:
  /// **'Discard this entry?'**
  String get journalDiscardTitle;

  /// No description provided for @journalDiscardBody.
  ///
  /// In en, this message translates to:
  /// **'Unsaved data will be lost.'**
  String get journalDiscardBody;

  /// No description provided for @journalContinueEditing.
  ///
  /// In en, this message translates to:
  /// **'Keep editing'**
  String get journalContinueEditing;

  /// No description provided for @journalDiscard.
  ///
  /// In en, this message translates to:
  /// **'Discard'**
  String get journalDiscard;

  /// No description provided for @journalBack.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get journalBack;

  /// No description provided for @journalDetailsTitle.
  ///
  /// In en, this message translates to:
  /// **'Optional details'**
  String get journalDetailsTitle;

  /// No description provided for @journalMealCaptureTitle.
  ///
  /// In en, this message translates to:
  /// **'WHAT YOU ATE'**
  String get journalMealCaptureTitle;

  /// No description provided for @journalMealCaptureHint.
  ///
  /// In en, this message translates to:
  /// **'Add only what you actually ate. IAmina does not label foods as good or bad.'**
  String get journalMealCaptureHint;

  /// No description provided for @journalMealSelected.
  ///
  /// In en, this message translates to:
  /// **'Added'**
  String get journalMealSelected;

  /// No description provided for @journalMealRecent.
  ///
  /// In en, this message translates to:
  /// **'Recent'**
  String get journalMealRecent;

  /// No description provided for @journalMealHabitual.
  ///
  /// In en, this message translates to:
  /// **'Frequent'**
  String get journalMealHabitual;

  /// No description provided for @journalMealNoRecent.
  ///
  /// In en, this message translates to:
  /// **'Your recent foods will appear here after your next meals.'**
  String get journalMealNoRecent;

  /// No description provided for @journalMealNoHabitual.
  ///
  /// In en, this message translates to:
  /// **'Your frequent foods will appear here as you use the journal.'**
  String get journalMealNoHabitual;

  /// No description provided for @journalMealSearch.
  ///
  /// In en, this message translates to:
  /// **'Search for a food'**
  String get journalMealSearch;

  /// No description provided for @journalMealSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Bread, eggs, couscous…'**
  String get journalMealSearchHint;

  /// No description provided for @journalMealSearchEmpty.
  ///
  /// In en, this message translates to:
  /// **'Type at least 2 characters to search.'**
  String get journalMealSearchEmpty;

  /// No description provided for @journalMealPhoto.
  ///
  /// In en, this message translates to:
  /// **'Recognize a meal photo'**
  String get journalMealPhoto;

  /// No description provided for @journalMealPhotoHint.
  ///
  /// In en, this message translates to:
  /// **'The photo is analyzed only after your action and requires AI-processing consent. Nothing is added without your confirmation.'**
  String get journalMealPhotoHint;

  /// No description provided for @journalMealPhotoProposal.
  ///
  /// In en, this message translates to:
  /// **'Proposal to review'**
  String get journalMealPhotoProposal;

  /// No description provided for @journalMealPhotoProposalHint.
  ///
  /// In en, this message translates to:
  /// **'Select what is correct, then confirm. Use search to correct or complete the meal.'**
  String get journalMealPhotoProposalHint;

  /// No description provided for @journalMealPhotoConfirm.
  ///
  /// In en, this message translates to:
  /// **'Confirm selection'**
  String get journalMealPhotoConfirm;

  /// No description provided for @journalMealPhotoUnavailable.
  ///
  /// In en, this message translates to:
  /// **'No food could be recognized. Add it with search instead.'**
  String get journalMealPhotoUnavailable;

  /// No description provided for @journalMealPhotoConsent.
  ///
  /// In en, this message translates to:
  /// **'Photo recognition requires AI-processing consent. Manual entry remains available.'**
  String get journalMealPhotoConsent;

  /// No description provided for @journalNutritionPortionTitle.
  ///
  /// In en, this message translates to:
  /// **'PORTIONS'**
  String get journalNutritionPortionTitle;

  /// No description provided for @journalNutritionPortionHint.
  ///
  /// In en, this message translates to:
  /// **'Choose a natural portion or enter grams if you know them. No nutrition number is invented.'**
  String get journalNutritionPortionHint;

  /// No description provided for @journalNutritionGrams.
  ///
  /// In en, this message translates to:
  /// **'Grams'**
  String get journalNutritionGrams;

  /// No description provided for @journalNutritionUnavailable.
  ///
  /// In en, this message translates to:
  /// **'No numeric nutrition shown: the food or portion is not documented well enough yet.'**
  String get journalNutritionUnavailable;

  /// No description provided for @journalNutritionCarbsExact.
  ///
  /// In en, this message translates to:
  /// **'≈ {value} g carbohydrates'**
  String journalNutritionCarbsExact(String value);

  /// No description provided for @journalNutritionCarbsRange.
  ///
  /// In en, this message translates to:
  /// **'≈ {low}–{high} g carbohydrates'**
  String journalNutritionCarbsRange(String low, String high);

  /// No description provided for @journalNutritionSource.
  ///
  /// In en, this message translates to:
  /// **'Source: {source}'**
  String journalNutritionSource(String source);
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en', 'fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
