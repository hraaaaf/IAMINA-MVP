// IAmina — ConsentService
// Tracks whether the current user has given explicit AI processing consent.
// Backed by the local Drift PatientProfile (synchronous, offline-first).
// Notifies GoRouter's refreshListenable so redirects fire immediately when
// consent status changes.
import 'dart:async';
import 'package:flutter/foundation.dart';
import '../data/drift/database.dart';

class ConsentService extends ChangeNotifier {
  // tri-state: null = not yet initialised (stream hasn't emitted)
  bool? _hasConsent;
  StreamSubscription<PatientProfileData?>? _sub;

  /// True once the first profile stream event has been processed.
  bool get isInitialized => _hasConsent != null;

  /// Whether the user has given explicit AI consent.
  /// Returns false if not yet initialized (safe default — no consent).
  bool get hasConsent => _hasConsent ?? false;

  /// Attach to the profile watcher stream from Drift.
  /// Called once from main() after the AppDatabase is ready.
  void attachStream(Stream<PatientProfileData?> profileStream) {
    _sub?.cancel();
    _sub = profileStream.listen((profile) {
      final newVal = profile?.aiConsentGivenAt != null;
      if (newVal != _hasConsent) {
        _hasConsent = newVal;
        notifyListeners();
      } else if (_hasConsent == null) {
        // First emission — mark as initialized even if value unchanged
        _hasConsent = newVal;
        notifyListeners();
      }
    });
  }

  /// Seed with a synchronously-available initial value (from a one-time DB
  /// query in main) to avoid a redirect flicker on app start.
  void seedInitialProfile(PatientProfileData? profile) {
    _hasConsent = profile?.aiConsentGivenAt != null;
  }

  // ── Decline (session-only) ────────────────────────────────────────────────
  /// True if the user tapped "Continue without AI" during this session.
  /// Resets on app restart. Prevents the consent gate from re-showing after
  /// the user has explicitly chosen not to consent.
  bool _hasDeclinedLocally = false;

  /// Whether the user has declined AI consent in this session (in-memory only).
  bool get hasDeclinedLocally => _hasDeclinedLocally;

  /// Mark that the user explicitly chose "Continue without AI".
  /// Called from ConsentScreen before navigating away.
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
