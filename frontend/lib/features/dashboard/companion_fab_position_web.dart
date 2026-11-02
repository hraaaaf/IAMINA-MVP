// Browser-local, non-clinical UI preference. Never synchronized or sent to AI.
// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;

const _key = 'iamina.d27.fab.position.v1';

String? loadFabPosition() {
  try {
    return html.window.localStorage[_key];
  } catch (_) {
    // Browsers may disable storage; draggable positioning still works.
    return null;
  }
}

void saveFabPosition(String normalizedPosition) {
  try {
    html.window.localStorage[_key] = normalizedPosition;
  } catch (_) {
    // UI preference persistence is best-effort, never a workflow blocker.
  }
}
