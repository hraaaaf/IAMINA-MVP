/// D13: protect the page-backed glucose entry route during a real Drift INSERT.
/// GoRouter redirects (unlike PopScope) observe browser history navigation.
/// Authentication, app-lock, onboarding and consent always take precedence.
class GlucoseSaveNavigationGuard {
  GlucoseSaveNavigationGuard._();

  static int _pendingPageSaves = 0;

  static void beginPageSave() => _pendingPageSaves++;

  static void endPageSave() {
    assert(_pendingPageSaves > 0, 'Unbalanced glucose save navigation guard');
    if (_pendingPageSaves > 0) _pendingPageSaves--;
  }

  static String? redirectWhilePending(String destinationPath) =>
      _pendingPageSaves > 0 && destinationPath != '/ajouter'
      ? '/ajouter'
      : null;
}
