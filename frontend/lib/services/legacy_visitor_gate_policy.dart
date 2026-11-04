/// L01/D18 policy only. No DB handle, I/O, patient identity or runtime wiring.
library;

/// Absence of the legacy IndexedDB name is NOT proof that no old OPFS/SQLite
/// vault exists. A trusted, separately certified full inventory is required.
enum LegacyPresence { present, absent, unknown }

enum LegacyVisitorGate { recoveryRequired, notCertified }

/// Conservative until D18's multi-storage legacy inventory is certified.
///
/// In particular, this never returns a public/clinical-ready state. It exists
/// to make the fail-closed decision independently testable without touching
/// production app-lock or opening/migrating the legacy database.
LegacyVisitorGate decideLegacyVisitorGate({
  required LegacyPresence indexedDbPresence,
  required bool fullLegacyInventoryCertified,
}) {
  if (indexedDbPresence != LegacyPresence.absent ||
      !fullLegacyInventoryCertified) {
    return LegacyVisitorGate.recoveryRequired;
  }
  // Even when all legacy stores are proven absent, clinical onboarding still
  // needs its own authorization; this gate does not grant access.
  return LegacyVisitorGate.notCertified;
}
