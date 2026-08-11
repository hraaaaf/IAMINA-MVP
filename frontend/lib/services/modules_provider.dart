import 'package:flutter/foundation.dart';
import '../modules/module_registry.dart';
import 'api_client.dart';

/// Holds the patient's active module set and keeps the chassis nav in sync with
/// the backend (`GET /api/v1/account/modules`). Frontend equivalent of reading
/// the backend PatientModule activations.
///
/// Defaults to every registered module (single-module deployment / offline), and
/// never collapses to an empty set — the shell must always render something.
class ModulesProvider extends ChangeNotifier {
  final ApiClient _api;
  ModulesProvider(this._api);

  Set<String> _activeIds = ModuleRegistry.all().map((m) => m.id).toSet();
  Set<String> get activeIds => _activeIds;

  Set<String> get _allRegistered => ModuleRegistry.all().map((m) => m.id).toSet();

  /// Pull active modules from the backend. Keeps the current set on failure.
  Future<void> refresh() async {
    final names = await _api.getActiveModules();
    if (names == null) return; // offline / error → keep current
    final known = names.where((n) => ModuleRegistry.byId(n) != null).toSet();
    final next = known.isEmpty ? _allRegistered : known;
    if (!setEquals(next, _activeIds)) {
      _activeIds = next;
      notifyListeners();
    }
  }

  /// Activate a module on the backend, then refresh.
  Future<bool> activate(String moduleName) async {
    final ok = await _api.activateModule(moduleName);
    if (ok) await refresh();
    return ok;
  }
}
