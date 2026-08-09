// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appTitle => 'IAmina';

  @override
  String get appSubtitle => 'رفيق داء السكري';

  @override
  String get appTagline => 'توازن سكر الدم، كل يوم';

  @override
  String get brandName => 'Diabetes Log';

  @override
  String get brandTagShort => 'AI · AMINA';

  @override
  String get dataPrivacyNote =>
      'خدمات الذكاء الاصطناعي الخارجية تتطلب موافقتك واعتمادًا صالحًا للمزوّد';

  @override
  String get sensorStatus => 'مستشعر G7 · IAmina';

  @override
  String get login => 'تسجيل الدخول';

  @override
  String get logout => 'تسجيل الخروج';

  @override
  String get signIn => 'الدخول';

  @override
  String get signOut => 'تسجيل الخروج';

  @override
  String get signOutConfirmTitle => 'تسجيل الخروج؟';

  @override
  String get signOutConfirmBody =>
      'تبقى بياناتك محفوظة. يمكنك تسجيل الدخول في أي وقت.';

  @override
  String get confirmSignOut => 'خروج';

  @override
  String get createAccount => 'إنشاء حساب';

  @override
  String get forgotPassword => 'نسيت كلمة المرور؟';

  @override
  String get resetPassword => 'إعادة تعيين كلمة المرور';

  @override
  String get resetPasswordDescription =>
      'أدخل عنوان بريدك الإلكتروني. ستصلك رسالة لإنشاء كلمة مرور جديدة.';

  @override
  String get resetEmailSent =>
      'تم إرسال البريد الإلكتروني — تحقق من صندوق الوارد.';

  @override
  String get emailNotFound =>
      'العنوان غير موجود أو البريد الإلكتروني غير صالح.';

  @override
  String get loginError => 'بريد إلكتروني أو كلمة مرور غير صحيحة.';

  @override
  String get loginSubtitle => 'سجّل دخولك للوصول إلى متابعتك.';

  @override
  String get emailLabel => 'البريد الإلكتروني';

  @override
  String get emailPlaceholder => 'example@mail.com';

  @override
  String get passwordLabel => 'كلمة المرور';

  @override
  String get send => 'إرسال';

  @override
  String get or => 'أو';

  @override
  String get demoAccess => 'وصول تجريبي — 21 يومًا من البيانات';

  @override
  String get dashboard => 'لوحة التحكم';

  @override
  String get addEntry => 'إضافة قياس';

  @override
  String get addMeasurement => 'إضافة قياس';

  @override
  String get summary => 'ملخص IAmina';

  @override
  String get profile => 'الملف الشخصي';

  @override
  String get myProfile => 'ملفي الشخصي';

  @override
  String get profileUpdated => 'تم تحديث الملف الشخصي';

  @override
  String get navSectionMain => 'الرئيسية';

  @override
  String get navSectionAccount => 'الحساب';

  @override
  String get navHome => 'الرئيسية';

  @override
  String get navIamina => 'IAmina';

  @override
  String get navHistory => 'السجل';

  @override
  String get navImport => 'استيراد';

  @override
  String get navSettings => 'الإعدادات';

  @override
  String get navJournal => 'اليومية';

  @override
  String get journalSubtitle => 'السجل الكامل';

  @override
  String get glucose => 'سكر الدم';

  @override
  String get insulin => 'الأنسولين';

  @override
  String get meal => 'الوجبة';

  @override
  String get fatigue => 'الإجهاد';

  @override
  String get sick => 'مريض';

  @override
  String get stressed => 'متوتر';

  @override
  String get freeMeasurement => 'قياس حر';

  @override
  String get enterValue => 'أدخل قيمة';

  @override
  String get diabetesType => 'نوع داء السكري';

  @override
  String get diabetesType1 => 'السكري النوع 1';

  @override
  String get diabetesType2 => 'السكري النوع 2';

  @override
  String get diabetesGestational => 'سكري الحمل';

  @override
  String get diabetesPreDiabetes => 'مقدمات السكري';

  @override
  String get treatment => 'العلاج';

  @override
  String get treatmentInsulin => 'الأنسولين';

  @override
  String get treatmentTablets => 'أقراص';

  @override
  String get treatmentLifestyle => 'نمط الحياة فقط';

  @override
  String get glucoseTarget => 'الهدف الجلوكوزي (mg/dL)';

  @override
  String get measureUnit => 'وحدة القياس';

  @override
  String get dangerZone => 'منطقة حساسة';

  @override
  String get configureWithIamina => 'الإعداد مع IAmina';

  @override
  String get conversationalAssistant => 'استخدام المساعد المحادثاتي';

  @override
  String get journalEmpty => 'يومياتك فارغة';

  @override
  String get journalEmptySubtitle => 'أضف قياسك الأول\nلبدء المتابعة.';

  @override
  String get last7Days => 'آخر 7 أيام';

  @override
  String get last30Days => 'آخر 30 يومًا';

  @override
  String get allHistory => 'كل السجل';

  @override
  String get today => 'اليوم';

  @override
  String get deleteEntryTitle => 'حذف هذا القياس؟';

  @override
  String get actionIrreversible => 'هذا الإجراء لا يمكن التراجع عنه.';

  @override
  String get entryDeleted => 'تم حذف القياس';

  @override
  String get consentTitle => 'الخصوصية والذكاء الاصطناعي';

  @override
  String get consentHeadline =>
      'قد تستخدم IAmina خدمات ذكاء اصطناعي خارجية لبعض الميزات';

  @override
  String get consentBody =>
      'بموافقتك، يمكن لـ IAmina إرسال فئات البيانات المذكورة أعلاه فقط إلى خدمة ذكاء اصطناعي خارجية. لا يتم الإرسال إلا إذا كان المزوّد والمنطقة التي تستضيف البيانات ومدة الاحتفاظ بها معتمدة لبيئة IAmina الخاصة بك. من دون موافقة أو اعتماد صالح للمزوّد، لا تُرسل أي بيانات.\n\nيمكنك سحب موافقتك في أي وقت من ملفك الشخصي.';

  @override
  String get consentDataPoint1 => '📊 قراءات الجلوكوز والاتجاهات';

  @override
  String get consentDataPoint2 => '🍽️ سياق الوجبة وجرعات الأنسولين';

  @override
  String get consentDataPoint3 => '😴 الإجهاد وعلامات أحداث الحياة';

  @override
  String get consentAccept => 'قبول ومتابعة';

  @override
  String get consentDeclineWithoutAI => 'المتابعة بدون ذكاء اصطناعي';

  @override
  String get consentAlreadyGiven => 'تمت الموافقة';

  @override
  String get consentWithdraw => 'سحب موافقة الذكاء الاصطناعي';

  @override
  String get consentWithdrawConfirmTitle => 'سحب موافقة الذكاء الاصطناعي؟';

  @override
  String get consentWithdrawConfirmBody =>
      'سيتم تعطيل ميزات الذكاء الاصطناعي (ملخص IAmina، الدردشة، الصوت) حتى تمنح موافقتك مرة أخرى.';

  @override
  String get consentWithdrawn => 'تم سحب موافقة الذكاء الاصطناعي';

  @override
  String get consentRequired =>
      'مطلوب موافقة الذكاء الاصطناعي لاستخدام هذه الميزة';

  @override
  String get documentPrivacyTitle => 'إرسال خارجي فقط عند السماح به';

  @override
  String get documentPrivacyBody =>
      'لا ترسل IAmina هذا المستند إلى خدمة خارجية إلا إذا منحت موافقتك وكان مزوّد هذه الخدمة معتمدًا لبيئة IAmina الخاصة بك. خلاف ذلك، يُحظر الاستيراد.';

  @override
  String get save => 'حفظ';

  @override
  String get saveProfile => 'حفظ';

  @override
  String get cancel => 'إلغاء';

  @override
  String get delete => 'حذف';

  @override
  String get edit => 'تعديل';

  @override
  String get ok => 'موافق';

  @override
  String get error => 'خطأ';

  @override
  String get loading => 'جارٍ التحميل...';

  @override
  String get noData => 'لا توجد بيانات';

  @override
  String get welcome => 'مرحبًا بك في IAmina';

  @override
  String get overview => 'نظرة عامة';

  @override
  String get breadcrumb => 'الرئيسية · نظرة عامة';

  @override
  String get talk => 'تحدث مع IAmina';

  @override
  String get dayShort => 'يوم';

  @override
  String get syncChecking => 'جارٍ التحقق من المزامنة';

  @override
  String get syncUpToDate => 'البيانات محدّثة';

  @override
  String get syncPending => 'بيانات في انتظار المزامنة';

  @override
  String get syncing => 'جارٍ المزامنة';

  @override
  String get syncOffline => 'غير متصل · البيانات محفوظة على هذا الجهاز';

  @override
  String get syncFailed => 'فشلت المزامنة · اضغط لإعادة المحاولة';

  @override
  String get goodMorning => 'صباح الخير';

  @override
  String get goodAfternoon => 'مساء الخير';

  @override
  String get goodEvening => 'مساء الخير';

  @override
  String greetingWithName(String greeting, String firstName) {
    return '$greeting، $firstName';
  }

  @override
  String greetingWithoutName(String greeting) {
    return '$greeting!';
  }

  @override
  String observation(int range) {
    return 'إليك ما لاحظته IAmina خلال آخر $range يومًا.';
  }

  @override
  String get emptyAnalysis => 'أضف بيانات لعرض تحليل IAmina.';

  @override
  String get latestReading => 'آخر قياس';

  @override
  String get justNow => 'الآن';

  @override
  String minutesAgo(int value) {
    return 'منذ $value دقيقة';
  }

  @override
  String get afterMeal => 'بعد الوجبة';

  @override
  String get fasting => 'صائم';

  @override
  String targetTitle(int range) {
    return 'القياسات ضمن النطاق · $range يومًا';
  }

  @override
  String targetCoverage(int count, int days) {
    return '$count قياسًا خلال $days يومًا · نسبة القراءات المسجلة وليست الوقت ضمن النطاق المحسوب من المراقبة المستمرة للجلوكوز (CGM)';
  }

  @override
  String get targetReference => 'مرجع عام ≥ 70٪ · قد يختلف هدفك الشخصي.';

  @override
  String get viewJournal => 'عرض اليومية';

  @override
  String get readingsInRange => 'القياسات ضمن النطاق';

  @override
  String get rangeReference => 'مرجع 70–180';

  @override
  String get inRange => 'ضمن النطاق';

  @override
  String get high => 'مرتفع';

  @override
  String get low => 'منخفض';

  @override
  String get veryHigh => 'مرتفع جدًا';

  @override
  String get targetExplanation =>
      'مرجع عام: أكثر من 70٪ من القياسات بين 70 و180 mg/dL. قد يختلف هدفك الشخصي.';

  @override
  String get importTitle => 'استيراد';

  @override
  String get importSubtitle => 'اربط مصادر بياناتك';

  @override
  String get directConnections => 'اتصالات مباشرة';

  @override
  String get pulperDescription =>
      'PDF · صورة · Excel · Word — تستخرج IAmina البيانات لمراجعتك.';

  @override
  String get labReport => 'تحاليل مخبرية';

  @override
  String get cgmExport => 'تصدير بيانات المراقبة المستمرة للجلوكوز (CGM)';

  @override
  String get prescription => 'وصفة طبية';

  @override
  String get photo => 'صورة';

  @override
  String get soon => 'قريبًا';

  @override
  String get unavailable => 'غير متاح';

  @override
  String get dexcomDescription =>
      'ربط Dexcom CLARITY مخطط له. يجب تأكيد التواتر والتوفر قبل التفعيل.';

  @override
  String get libreDescription =>
      'استيراد LibreView مخطط له. يجب تأكيد الصيغ والتوفر قبل التفعيل.';

  @override
  String get openDocumentImport => 'فتح استيراد المستند';

  @override
  String get documentTitle => 'استيراد مستند';

  @override
  String get documentIntro =>
      'استورد مستندًا طبيًا. تستخرج IAmina البيانات ثم يجب عليك مراجعتها وتأكيدها.';

  @override
  String get chooseDocument => 'اختيار مستند';

  @override
  String get profileComplete => 'الملف مكتمل';

  @override
  String get profileCompleteChecked => 'الملف مكتمل ✓';

  @override
  String profileCompletionPercent(int percentage) {
    return 'اكتمل الملف بنسبة $percentage٪';
  }

  @override
  String get profileCompletionPrompt => 'أكمل ملفك للحصول على تحليلات أدق.';

  @override
  String get minimum => 'الحد الأدنى';

  @override
  String get maximum => 'الحد الأقصى';

  @override
  String get onboardingWelcome =>
      'مرحبًا! أنا IAmina، رفيقك لمتابعة داء السكري.';

  @override
  String get onboardingChooseLanguage => 'اختر لغة التطبيق.';

  @override
  String get onboardingChooseCountry => 'في أي بلد تستخدم IAmina؟';

  @override
  String get onboardingChooseTone => 'ما الأسلوب الذي تفضله؟';

  @override
  String get onboardingToneNeutral => 'محايد ومهني';

  @override
  String get onboardingToneFriendly => 'بسيط وودود';

  @override
  String get onboardingCountryMorocco => 'المغرب';

  @override
  String get onboardingCountryFrance => 'فرنسا';

  @override
  String get onboardingCountryOther => 'بلد آخر';

  @override
  String get onboardingTypeQuestion => 'ما نوع داء السكري الذي تتابعه؟';

  @override
  String get onboardingTreatmentQuestion => 'ما هو علاجك الرئيسي؟';

  @override
  String get onboardingTreatmentInsulin => 'الأنسولين (حقن أو مضخة)';

  @override
  String get onboardingTreatmentLifestyle => 'نمط الحياة فقط';

  @override
  String get onboardingTargetQuestion =>
      'ما أهداف سكر الدم لديك؟ المرجع العام المعروض هو 70–180 mg/dL ما لم يختلف هدفك الشخصي.';

  @override
  String get onboardingTargetStandard => 'المرجع العام (70–180)';

  @override
  String get onboardingTargetCustom => 'هدف شخصي';

  @override
  String get onboardingUnitQuestion => 'ما وحدة القياس التي تفضلها؟';

  @override
  String get onboardingUnitMg => 'mg/dL';

  @override
  String get onboardingUnitMmol => 'mmol/L';

  @override
  String get onboardingReady =>
      'تم إعداد مساحتك. يمكنك تعديل هذه الاختيارات من ملفك الشخصي.';

  @override
  String get onboardingStart => 'ابدأ';

  @override
  String get onboardingSaving => 'جارٍ الحفظ…';

  @override
  String get onboardingAssistantLabel => 'مساعد الإعداد';

  @override
  String get emptyDashboardTitle => 'أضف بياناتك الأولى';

  @override
  String get emptyDashboardBody =>
      'لا توجد بيانات مسجلة بعد. أضف قياسًا أو استورد مستندًا لبناء لوحة المتابعة انطلاقًا من بياناتك الحقيقية.';

  @override
  String get addFirstMeasurement => 'إضافة أول قياس';

  @override
  String get importDocument => 'استيراد مستند';

  @override
  String get featureRealtimeAgp => 'ملخص اتجاهات المستشعر (AGP)';

  @override
  String get featureAiAnalysis => 'تحليل بالذكاء الاصطناعي';

  @override
  String get featurePrivateData => 'بيانات خاصة';

  @override
  String get analysisLoadError => 'تعذّر استرجاع التحليلات.';

  @override
  String get retry => 'إعادة المحاولة';

  @override
  String get analysisLoading => 'تقوم IAmina بتحليل بياناتك…';

  @override
  String get analysisLoadingWait => 'قد يستغرق ذلك بضع ثوانٍ.';

  @override
  String get dashboardLoadingTitle => 'جارٍ تحميل بياناتك';

  @override
  String get dashboardLoadingBody =>
      'تتحقق IAmina من البيانات المحفوظة على هذا الجهاز قبل عرض لوحة المتابعة.';

  @override
  String get dashboardLoadErrorTitle => 'تعذر عرض بياناتك';

  @override
  String get dashboardLoadErrorBody =>
      'تعذر على لوحة المتابعة قراءة بياناتك المحلية. يمكنك إعادة المحاولة من دون إنشاء أي بيانات افتراضية.';

  @override
  String get firstUseTruthNote =>
      'لن تظهر الاتجاهات والتحليلات إلا عند توفر بيانات حقيقية.';

  @override
  String get profileMedicalSection => 'المتابعة الطبية';

  @override
  String get profileIaminaSection => 'IAmina والتفضيلات';

  @override
  String get profileIaminaSectionHint => 'اللغة والبلد والأسلوب ومساعد الإعداد';

  @override
  String get profileAccountSection => 'الخصوصية والحساب';

  @override
  String get profileAccountSectionHint =>
      'موافقة الذكاء الاصطناعي وإجراءات الحساب';

  @override
  String get profileMedicalSectionHint => 'أكمل المعلومات أو راجعها';

  @override
  String get journalAddTitle => 'قياس جديد';

  @override
  String get journalAddSubtitle => 'سجّل ما حدث للتو.';

  @override
  String get journalGlucose => 'سكر الدم';

  @override
  String get journalNoGlucoseAssumption => 'لن نفترض أي قيمة قبل إدخالك.';

  @override
  String get journalLowGlucoseDetected =>
      'تم رصد قيمة منخفضة — تحقّق من القياس؛ وستظهر رسالة الأمان عند الحفظ.';

  @override
  String get journalTargetNotInferred =>
      'لا يتم استنتاج هدفك الشخصي من هذه القيمة وحدها.';

  @override
  String get journalMeasurementContext => 'سياق القياس';

  @override
  String get journalContextHint => 'اختياري — اختر فقط إذا كنت تعرف السياق.';

  @override
  String get journalContextFasting => 'على الريق';

  @override
  String get journalContextPreMeal => 'قبل الوجبة';

  @override
  String get journalContextPostMeal => 'بعد الوجبة';

  @override
  String get journalContextOther => 'سياق آخر';

  @override
  String get journalAddMeal => 'إضافة وجبة';

  @override
  String get journalMealOptional => 'الوجبة (اختيارية)';

  @override
  String get journalMealBreakfast => 'الفطور';

  @override
  String get journalMealLunch => 'الغداء';

  @override
  String get journalMealDinner => 'العشاء';

  @override
  String get journalMealSnack => 'وجبة خفيفة';

  @override
  String get journalMealNoteLabel => 'ملاحظة اختيارية';

  @override
  String get journalMealNoteHint => 'طريقة التحضير أو تفصيل مفيد…';

  @override
  String get journalRemoveMeal => 'إزالة الوجبة';

  @override
  String get journalDetailsButton =>
      'تفاصيل: الوقت، الإنسولين المأخوذ، السياق…';

  @override
  String get journalToday => 'اليوم';

  @override
  String get journalInsulinTaken => 'الإنسولين المأخوذ';

  @override
  String get journalInsulinExplanation =>
      'أدخل فقط جرعة أخذتها بالفعل. لا يحسب IAmina الجرعة ولا يقيّمها هنا.';

  @override
  String get journalDoseTaken => 'الجرعة التي أخذتها';

  @override
  String get journalOptional => 'اختياري';

  @override
  String get journalAdditionalContext => 'سياق إضافي (اختياري)';

  @override
  String get journalSick => 'مريض';

  @override
  String get journalUnusualStress => 'توتر غير معتاد';

  @override
  String get journalPhysicalActivity => 'نشاط بدني';

  @override
  String get journalPoorSleep => 'نوم سيئ';

  @override
  String get journalSave => 'حفظ القياس';

  @override
  String get journalSaving => 'جارٍ الحفظ…';

  @override
  String get journalVeryLowTitle => 'تم رصد قيمة منخفضة جدًا';

  @override
  String get journalLowTitle => 'تم رصد قيمة منخفضة';

  @override
  String get journalVeryLowSafety =>
      'تفعّل هذه القيمة مسار الأمان ذي الأولوية لانخفاض سكر الدم. تحقّق من القياس واتبع خطة التعامل مع انخفاض السكر المتفق عليها مع فريقك المعالج.';

  @override
  String get journalLowSafety =>
      'تفعّل هذه القيمة مسار الأمان لانخفاض سكر الدم. تحقّق من القياس واتبع خطة التعامل مع انخفاض السكر المتفق عليها مع فريقك المعالج.';

  @override
  String get journalBackToEntry => 'العودة إلى الإدخال';

  @override
  String get journalSaveAnyway => 'الحفظ على أي حال';

  @override
  String get journalEditTitle => 'تعديل القياس';

  @override
  String get journalEditSubtitle => 'صحّح فقط المعلومات التي تم تسجيلها فعلاً.';

  @override
  String get journalEditContextPreserved =>
      'يبقى الطعام وسياق قياس السكر والوقت وباقي التفاصيل دون تغيير في هذه الشاشة.';

  @override
  String get journalNoInsulinTakenHint =>
      'اترك الحقل فارغاً إذا لم يتم أخذ إنسولين لهذا التسجيل.';

  @override
  String get journalUpdated => 'تم تحديث القياس.';

  @override
  String get journalInvalidGlucose => 'أدخل قيمة صحيحة لسكر الدم.';

  @override
  String get journalInvalidInsulin => 'قيمة جرعة الإنسولين المدخلة غير صحيحة.';

  @override
  String get journalSaved => 'تم حفظ القياس.';

  @override
  String get journalDiscardTitle => 'هل تريد إلغاء الإدخال؟';

  @override
  String get journalDiscardBody => 'ستفقد البيانات التي لم تُحفظ.';

  @override
  String get journalContinueEditing => 'متابعة الإدخال';

  @override
  String get journalDiscard => 'إلغاء';

  @override
  String get journalBack => 'رجوع';

  @override
  String get journalDetailsTitle => 'تفاصيل اختيارية';

  @override
  String get journalMealCaptureTitle => 'ما الذي أكلته';

  @override
  String get journalMealCaptureHint =>
      'أضف فقط ما أكلته فعلاً. لا تصنّف IAmina الأطعمة إلى جيدة أو سيئة.';

  @override
  String get journalMealSelected => 'المضاف';

  @override
  String get journalMealRecent => 'الأخيرة';

  @override
  String get journalMealHabitual => 'المعتادة';

  @override
  String get journalMealNoRecent =>
      'ستظهر أطعمتك الأخيرة هنا بعد تسجيل وجباتك القادمة.';

  @override
  String get journalMealNoHabitual =>
      'ستظهر أطعمتك المعتادة هنا مع استخدام اليوميات.';

  @override
  String get journalMealSearch => 'ابحث عن طعام';

  @override
  String get journalMealSearchHint => 'خبز، بيض، كسكس…';

  @override
  String get journalMealSearchEmpty => 'اكتب حرفين على الأقل للبحث.';

  @override
  String get journalMealPhoto => 'التعرّف على الطعام من صورة';

  @override
  String get journalMealPhotoHint =>
      'تُحلَّل الصورة فقط بعد اختيارك وتتطلب موافقتك على معالجة الذكاء الاصطناعي. لن يُضاف أي شيء دون تأكيدك.';

  @override
  String get journalMealPhotoProposal => 'اقتراح يحتاج إلى مراجعة';

  @override
  String get journalMealPhotoProposalHint =>
      'اختر العناصر الصحيحة ثم أكّدها. استخدم البحث للتصحيح أو الإضافة.';

  @override
  String get journalMealPhotoConfirm => 'تأكيد الاختيار';

  @override
  String get journalMealPhotoUnavailable =>
      'لم نتمكن من التعرّف على طعام. أضفه عبر البحث.';

  @override
  String get journalMealPhotoConsent =>
      'يتطلب التعرّف على الصورة موافقتك على معالجة الذكاء الاصطناعي. الإدخال اليدوي متاح دائماً.';

  @override
  String get journalNutritionPortionTitle => 'الكمية';

  @override
  String get journalNutritionPortionHint =>
      'اختر حصة مألوفة أو أدخل الوزن بالغرام إذا كنت تعرفه. لا يعرض IAmina رقماً غذائياً مخمناً.';

  @override
  String get journalNutritionGrams => 'غرام';

  @override
  String get journalNutritionUnavailable =>
      'لا توجد قيمة غذائية رقمية معروضة: الطعام أو الحصة غير موثقين بما يكفي بعد.';

  @override
  String journalNutritionCarbsExact(String value) {
    return '≈ $value غ كربوهيدرات';
  }

  @override
  String journalNutritionCarbsRange(String low, String high) {
    return '≈ $low–$high غ كربوهيدرات';
  }

  @override
  String journalNutritionSource(String source) {
    return 'المصدر: $source';
  }

  @override
  String get ramadanProfileSection => 'فترة رمضان';

  @override
  String get ramadanProfileHint =>
      'اختياري. تُكيّف هذه الفترة أسماء الوجبات في السجل. لا تفترض IAmina أنك صائم.';

  @override
  String get ramadanNotConfigured => 'غير محددة';

  @override
  String get ramadanStartDate => 'البداية';

  @override
  String get ramadanEndDate => 'النهاية';

  @override
  String get ramadanChooseDate => 'اختر تاريخًا';

  @override
  String get ramadanClear => 'مسح الفترة';

  @override
  String get ramadanSave => 'حفظ';

  @override
  String get ramadanSaved => 'تم حفظ فترة رمضان.';

  @override
  String get ramadanSavedLocalOnly =>
      'تم الحفظ على هذا الجهاز. لم يتم تحديث الخادم.';

  @override
  String get ramadanNeedsBothDates =>
      'اختر تاريخ البداية وتاريخ النهاية معًا، أو امسحهما معًا.';

  @override
  String get ramadanDateOrderError =>
      'يجب أن يكون تاريخ البداية قبل تاريخ النهاية أو مساويًا له.';

  @override
  String get journalRamadanMealVocabularyHint =>
      'تتكيف أسماء الوجبات مع الفترة المحفوظة في ملفك. لا يُفترض أنك صائم.';

  @override
  String get journalMealSuhoor => 'السحور';

  @override
  String get journalMealIftar => 'الإفطار';

  @override
  String get journalMealOther => 'أخرى';
}
