import 'dart:js_interop';
import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;

/// Web: a different browser tab changed IAMINA secure storage.
VoidCallback watchAuthStorageChanges(VoidCallback onChanged) {
  final handler = ((web.Event event) {
    final key = (event as web.StorageEvent).key;
    if (key == null || key.contains('iamina_')) {
      onChanged();
    }
  }).toJS;
  web.window.addEventListener('storage', handler);
  return () => web.window.removeEventListener('storage', handler);
}
