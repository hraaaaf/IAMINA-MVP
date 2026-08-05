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
  /// **'AI processing subject to approval'**
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
  /// **'IAmina may process some data with approved AI services'**
  String get consentHeadline;

  /// No description provided for @consentBody.
  ///
  /// In en, this message translates to:
  /// **'This consent authorises IAmina to use the data categories listed above for AI features. External processing occurs only when the deployment provider, region and retention policy have been approved. Without consent or a valid provider approval, data is not sent to the AI service.\n\nThe provider and terms may vary by deployment. You can withdraw this consent at any time from your profile settings.'**
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
  /// **'Controlled external processing'**
  String get documentPrivacyTitle;

  /// No description provided for @documentPrivacyBody.
  ///
  /// In en, this message translates to:
  /// **'The document is sent to an external service only when your consent and the deployment provider policy are valid. Otherwise, import is refused.'**
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
