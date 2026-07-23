import 'diabetes_module.dart';
import 'module_config.dart';

/// Frontend module registry — the chassis builds nav + routes from this instead
/// of hardcoding diabetes. Add a module here (and the backend manifest) to make
/// it discoverable. The patient's *active* subset comes from
/// GET /api/v1/account/modules (see ModulesProvider); until that lands every
/// registered module is treated as active (single-module deployment).
class ModuleRegistry {
  static final List<ModuleConfig> _modules = [diabetesModule];

  /// All registered modules (everything the app knows how to render).
  static List<ModuleConfig> all() => List.unmodifiable(_modules);

  /// The registered modules whose id is in [activeIds], in registry order.
  static List<ModuleConfig> activeFrom(Set<String> activeIds) =>
      _modules.where((m) => activeIds.contains(m.id)).toList();

  static ModuleConfig? byId(String id) {
    for (final m in _modules) {
      if (m.id == id) return m;
    }
    return null;
  }
}
