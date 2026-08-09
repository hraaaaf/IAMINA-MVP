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
