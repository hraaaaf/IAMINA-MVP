// IAmina — ConsentScreen
// RGPD Art. 7 — Explicit AI processing consent gate.
//
// Shown once after first login when no consent record exists.
// Routes:
//   Accept  → POST /api/v1/account/consent → local Drift update → /dashboard
//   Decline → /dashboard (AI features unavailable until consent given)
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/api_client.dart';
import '../../services/consent_service.dart';

class ConsentScreen extends StatefulWidget {
  const ConsentScreen({super.key});

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  bool _isLoading = false;

  Future<void> _accept() async {
    setState(() => _isLoading = true);
    // Capture before any async gaps (use_build_context_synchronously)
    final api = context.read<ApiClient>();
    final db  = context.read<AppDatabase>();
    try {
      // Store on backend first (source of truth for audit)
      await api.giveConsent();
      // Mirror locally for offline-first consent check
      await db.setAiConsent(granted: true);
      if (mounted) context.go('/dashboard');
    } catch (_) {
      // Even on network error, store locally — consent was given.
      // The backend will sync when connectivity is restored.
      await db.setAiConsent(granted: true);
      if (mounted) context.go('/dashboard');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _declineWithoutAI() {
    // Mark declined in-memory so the consent gate doesn't re-show this session.
    context.read<ConsentService>().declineLocally();
    context.go('/dashboard');
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dark = AminaTheme.isDark(context);

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // ── Brand header ────────────────────────────────────────
                  Center(
                    child: Container(
                      width: 72, height: 72,
                      decoration: BoxDecoration(
                        gradient: AminaTheme.heroGradient,
                        borderRadius: BorderRadius.circular(22),
                        boxShadow: [
                          BoxShadow(
                            color: AminaTheme.teal500.withValues(alpha: 0.28),
                            blurRadius: 20,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: const Icon(Icons.shield_outlined, color: Colors.white, size: 32),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    l10n.consentTitle,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AminaTheme.teal600,
                      letterSpacing: 0.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.consentHeadline,
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: AminaTheme.textPrimary(context),
                      letterSpacing: -0.4,
                      height: 1.3,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),

                  // ── Data points card ────────────────────────────────────
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: AminaTheme.surface(context),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AminaTheme.divider(context)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _DataPoint(l10n.consentDataPoint1),
                        const SizedBox(height: 12),
                        _DataPoint(l10n.consentDataPoint2),
                        const SizedBox(height: 12),
                        _DataPoint(l10n.consentDataPoint3),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // ── Body text ────────────────────────────────────────────
                  Text(
                    l10n.consentBody,
                    style: TextStyle(
                      fontSize: 13.5,
                      color: AminaTheme.textSecondary(context),
                      height: 1.65,
                    ),
                  ),
                  const SizedBox(height: 36),

                  // ── Accept button ────────────────────────────────────────
                  FilledButton(
                    onPressed: _isLoading ? null : _accept,
                    style: FilledButton.styleFrom(
                      backgroundColor: AminaTheme.teal500,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 20, height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(
                            l10n.consentAccept,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                  const SizedBox(height: 12),

                  // ── Decline (no AI) button ───────────────────────────────
                  TextButton(
                    onPressed: _isLoading ? null : _declineWithoutAI,
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      foregroundColor: dark
                          ? AminaTheme.dark300
                          : AminaTheme.ink400,
                    ),
                    child: Text(
                      l10n.consentDeclineWithoutAI,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ),

                  const SizedBox(height: 24),
                  // ── Legal footnote ───────────────────────────────────────
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.lock_outline, size: 12, color: AminaTheme.ink300),
                      const SizedBox(width: 6),
                      Text(
                        l10n.dataPrivacyNote,
                        style: const TextStyle(fontSize: 11, color: AminaTheme.ink300),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DataPoint extends StatelessWidget {
  final String text;
  const _DataPoint(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: AminaTheme.textPrimary(context),
        height: 1.4,
      ),
    );
  }
}
