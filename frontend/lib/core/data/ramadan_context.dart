// D21: hide historical Ramadan-derived behavior on Web unless explicitly
// opted into by a separately reviewed build. Native retains prior behavior.
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


// Always keep historical periods in storage. Suppress their automatic effect
// on the Web meal form when D21 Ramadan UI is disabled.
List<String> mealTypesForSurfaceDate(
  DateTime eventDate,
  DateTime? configuredStart,
  DateTime? configuredEnd, {
  required bool isWeb,
}) => shouldApplyRamadanProfileContext(isWeb: isWeb)
    ? mealTypesForProfileDate(eventDate, configuredStart, configuredEnd)
    : regularMealTypes;
