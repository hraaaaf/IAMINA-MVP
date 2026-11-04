import 'dart:js_interop';

@JS('performance.mark')
external JSAny? _markBrowser(JSString name);

void mark(String name) {
  try {
    _markBrowser(name.toJS);
  } catch (_) {
    // Diagnostic hooks never interrupt medical vault or app lock.
  }
}
