/// Temporary Firebase migration bridge policy.
///
/// IAMINA native authentication is authoritative. Pilot builds keep this off
/// unless a controlled legacy-account migration window is explicitly requested.
const bool kFirebaseMigrationEnabled = bool.fromEnvironment(
  'ENABLE_FIREBASE_MIGRATION',
  defaultValue: false,
);
