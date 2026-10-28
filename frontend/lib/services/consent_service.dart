// ConsentService — local UI gate for externally processed AI features.
// A Drift timestamp alone is never sufficient: it must be paired with current,
// verified notice evidence held in secure storage. Server egress remains the
// authoritative fail-closed boundary.
import 'dart:async';
import 'package:flutter/foundation.dart';
import '../data/drift/database.dart';
import 'd9_first_use_transport.dart';

class ConsentService extends ChangeNotifier {
  bool? _hasConsent;
  bool _hasVerifiedEvidence;
  bool _profileHasTimestamp = false;
  bool _hasCompletedOnboarding = false;
  bool _d9VerifiedRemoteCompletion = false;
  StreamSubscription<PatientProfileData?>? _sub;

  ConsentService({bool hasVerifiedEvidence = false})
    : _hasVerifiedEvidence = hasVerifiedEvidence;

  /// True once the first profile stream event has been processed or seeded.
  bool get isInitialized => _hasConsent != null;

  /// Safe default is false. Both local timestamp and verified evidence required.
  bool get hasConsent => _hasConsent ?? false;

  /// First-use preferences are persisted, not a claim of medical completeness.
  bool get hasCompletedOnboarding => _hasCompletedOnboarding;

  bool _profileCompletesOnboarding(PatientProfileData? profile) {
    // D7: diagnosis and treatment are optional patient declarations. The
    // clinical engine must independently fail closed when they are missing.
    return profile != null || _d9VerifiedRemoteCompletion;
  }

  void _applyProfile(PatientProfileData? profile) {
    final nextCompletedOnboarding = _profileCompletesOnboarding(profile);
    final onboardingChanged =
        nextCompletedOnboarding != _hasCompletedOnboarding;
    _hasCompletedOnboarding = nextCompletedOnboarding;

    _profileHasTimestamp = profile?.aiConsentGivenAt != null;
    final nextConsent = _profileHasTimestamp && _hasVerifiedEvidence;
    final consentChanged = nextConsent != _hasConsent;
    _hasConsent = nextConsent;

    if (onboardingChanged || consentChanged) {
      notifyListeners();
    }
  }

  /// Attach to local profile changes. Legacy timestamps without secure evidence
  /// remain denied after upgrade.
  void attachStream(Stream<PatientProfileData?> profileStream) {
    _sub?.cancel();
    _sub = profileStream.listen(_applyProfile);
  }

  /// Seed synchronously to avoid a redirect flicker on app start.
  void seedInitialProfile(PatientProfileData? profile) {
    _hasCompletedOnboarding = _profileCompletesOnboarding(profile);
    _profileHasTimestamp = profile?.aiConsentGivenAt != null;
    _hasConsent = _profileHasTimestamp && _hasVerifiedEvidence;
  }

  /// D9: accept an explicit server proof for THIS owner only. No PatientProfile
  /// row is fabricated, and AI consent must remain independently verified.
  /// This instance is scoped to one physical vault and disposed on auth switch.
  bool adoptVerifiedD9FirstUseProof(
    D9FirstUseProof? proof, {
    required int activeOwner,
  }) {
    if (proof == null ||
        !proof.completed ||
        activeOwner <= 0 ||
        proof.ownerUserId != activeOwner ||
        proof.completedAt == null) {
      return false;
    }
    _d9VerifiedRemoteCompletion = true;
    if (!_hasCompletedOnboarding) {
      _hasCompletedOnboarding = true;
      notifyListeners();
    }
    return true;
  }

  /// Called only after server acceptance, exact response verification, secure
  /// evidence persistence and local timestamp persistence all succeeded.
  void markVerifiedConsent() {
    _hasVerifiedEvidence = true;
    _profileHasTimestamp = true;
    _hasConsent = true;
    _hasDeclinedLocally = false;
    notifyListeners();
  }

  /// Clear the local gate immediately after withdrawal or evidence invalidation.
  void clearVerifiedConsent() {
    _hasVerifiedEvidence = false;
    _profileHasTimestamp = false;
    _hasConsent = false;
    notifyListeners();
  }

  // ── Decline (session-only) ────────────────────────────────────────────────
  bool _hasDeclinedLocally = false;

  bool get hasDeclinedLocally => _hasDeclinedLocally;

  void declineLocally() {
    _hasDeclinedLocally = true;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
