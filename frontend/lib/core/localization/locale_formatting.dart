import 'package:flutter/widgets.dart';
import 'package:intl/intl.dart';

String formatLocalizedDate(BuildContext context, DateTime value) {
  final locale = Localizations.localeOf(context).toLanguageTag();
  return DateFormat.yMd(locale).format(value);
}

String formatLocalizedDateTime(BuildContext context, DateTime value) {
  final locale = Localizations.localeOf(context).toLanguageTag();
  return DateFormat.yMd(locale).add_Hm().format(value);
}
