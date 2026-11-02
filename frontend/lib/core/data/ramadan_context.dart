// D21 — Web defaults to Ramadan UI OFF. Preserve historical periods and
// native behavior for a separately reviewed reactivation.
const bool kWebRamadanUiEnabled = bool.fromEnvironment(
  'IAMINA_WEB_RAMADAN_UI',
  defaultValue: false,
);

bool shouldApplyRamadanProfileContext({required bool isWeb}) =>
    !isWeb || kWebRamadanUiEnabled;

const List<String> regularMealTypes = <String>[
  'breakfast',
  'lunch',
  'dinner',
  'snack',
];

const List<String> ramadanMealTypes = <String>[
  'suhoor',
  'iftar',
  'snack',
  'other',
];

DateTime _dateOnly(DateTime value) =>
    DateTime(value.year, value.month, value.day);

bool isRamadanProfileDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd,
) {
  if (configuredStart == null || configuredEnd == null) return false;
  final day = _dateOnly(eventDate);
  final start = _dateOnly(configuredStart);
  final end = _dateOnly(configuredEnd);
  return !day.isBefore(start) && !day.isAfter(end);
}

List<String> mealTypesForProfileDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd,
) => isRamadanProfileDate(eventDate, configuredStart, configuredEnd)
    ? ramadanMealTypes
    : regularMealTypes;

// Historical date values remain intact; their meal-label side effects are
// suppressed on Web while the D21 feature flag is disabled.
List<String> mealTypesForSurfaceDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd, {
  required bool isWeb,
}) => shouldApplyRamadanProfileContext(isWeb: isWeb)
    ? mealTypesForProfileDate(eventDate, configuredStart, configuredEnd)
    : regularMealTypes;
