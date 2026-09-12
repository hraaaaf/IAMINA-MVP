// IAmina — ConsentScreen
// Explicit AI processing consent gate bound to one exact notice version/hash/locale.
//
// Routes:
//   Accept  → exact server receipt → secure local evidence → Drift gate → dashboard
//   Decline → dashboard (external AI features remain unavailable)
import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../data/drift/database.dart';
import '../../services/api_client.dart';
import '../../services/consent_api_extension.dart';
import '../../services/consent_evidence_store.dart';
import '../../services/consent_notice_contract.dart';
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
    final api = context.read<ApiClient>();
    final db = context.read<AppDatabase>();
    final evidenceStore = context.read<ConsentEvidenceStore>();
    final consent = context.read<ConsentService>();
    final claim = ConsentNoticeContract.forLocale(
      Localizations.localeOf(context).toLanguageTag(),
    );
    try {
      final accepted = await api.giveVersionedConsent(claim);
      if (!accepted) return;

      // The UI gate only opens after the exact server response is verified and
      // the same evidence is durably persisted locally.
      await evidenceStore.write(claim);
      await db.setAiConsent(granted: true);
      consent.markVerifiedConsent();
      if (mounted) context.go('/dashboard');
    } catch (_) {
      // Fail closed. The explicit "Continue without AI" route remains usable.
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _declineWithoutAI() {
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
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compactHeight = constraints.maxHeight <= 600;
            final desktop = constraints.maxWidth >= 900;
            final iconSize = compactHeight ? 48.0 : 72.0;

            return Center(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: compactHeight ? 14 : 40,
                ),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 480),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Center(
                        child: Container(
                          width: iconSize,
                          height: iconSize,
                          decoration: BoxDecoration(
                            gradient: AminaTheme.heroGradient,
                            borderRadius: BorderRadius.circular(
                              compactHeight ? 16 : 22,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: AminaTheme.teal500.withValues(
                                  alpha: 0.28,
                                ),
                                blurRadius: compactHeight ? 12 : 20,
                                offset: Offset(0, compactHeight ? 4 : 8),
                              ),
                            ],
                          ),
                          child: Icon(
                            Icons.shield_outlined,
                            color: Colors.white,
                            size: compactHeight ? 24 : 32,
                          ),
                        ),
                      ),
                      SizedBox(height: compactHeight ? 10 : 24),
                      Text(
                        l10n.consentTitle,
                        style: TextStyle(
                          fontSize: compactHeight ? 11.5 : 13,
                          fontWeight: FontWeight.w700,
                          color: AminaTheme.teal600,
                          letterSpacing: 0.5,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      SizedBox(height: compactHeight ? 4 : 8),
                      Text(
                        l10n.consentHeadline,
                        style: TextStyle(
                          fontSize: compactHeight ? 18 : 22,
                          fontWeight: FontWeight.w800,
                          color: AminaTheme.textPrimary(context),
                          letterSpacing: -0.4,
                          height: compactHeight ? 1.18 : 1.3,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      SizedBox(height: compactHeight ? 14 : 32),
                      Container(
                        padding: EdgeInsets.all(compactHeight ? 12 : 20),
                        decoration: BoxDecoration(
                          color: AminaTheme.surface(context),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: AminaTheme.divider(context),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _DataPoint(
                              l10n.consentDataPoint1,
                              compact: compactHeight,
                            ),
                            SizedBox(height: compactHeight ? 6 : 12),
                            _DataPoint(
                              l10n.consentDataPoint2,
                              compact: compactHeight,
                            ),
                            SizedBox(height: compactHeight ? 6 : 12),
                            _DataPoint(
                              l10n.consentDataPoint3,
                              compact: compactHeight,
                            ),
                          ],
                        ),
                      ),
                      SizedBox(height: compactHeight ? 12 : 20),
                      Text(
                        l10n.consentBody,
                        style: TextStyle(
                          fontSize: compactHeight ? 11.5 : 13.5,
                          color: AminaTheme.textSecondary(context),
                          height: compactHeight ? 1.38 : 1.65,
                        ),
                      ),
                      SizedBox(height: compactHeight ? 14 : 36),
                      Align(
                        alignment: Alignment.center,
                        child: SizedBox(
                          width: desktop ? 300 : double.infinity,
                          child: FilledButton(
                            onPressed: _isLoading ? null : _accept,
                            style: FilledButton.styleFrom(
                              backgroundColor: AminaTheme.teal500,
                              padding: EdgeInsets.symmetric(
                                vertical: compactHeight ? 12 : 16,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(
                                  AminaTheme.radiusXL,
                                ),
                              ),
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : Text(
                                    l10n.consentAccept,
                                    style: TextStyle(
                                      fontSize: compactHeight ? 13.5 : 15,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                          ),
                        ),
                      ),
                      SizedBox(height: compactHeight ? 4 : 12),
                      TextButton(
                        onPressed: _isLoading ? null : _declineWithoutAI,
                        style: TextButton.styleFrom(
                          padding: EdgeInsets.symmetric(
                            vertical: compactHeight ? 8 : 14,
                          ),
                          foregroundColor: dark
                              ? AminaTheme.dark300
                              : AminaTheme.ink400,
                        ),
                        child: Text(
                          l10n.consentDeclineWithoutAI,
                          style: TextStyle(
                            fontSize: compactHeight ? 12 : 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      SizedBox(height: compactHeight ? 10 : 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.lock_outline,
                            size: 12,
                            color: AminaTheme.ink300,
                          ),
                          const SizedBox(width: 6),
                          Flexible(
                            child: Text(
                              l10n.dataPrivacyNote,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: compactHeight ? 9.5 : 11,
                                color: AminaTheme.ink300,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _DataPoint extends StatelessWidget {
  final String text;
  final bool compact;

  const _DataPoint(this.text, {this.compact = false});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: compact ? 12 : 14,
        fontWeight: FontWeight.w600,
        color: AminaTheme.textPrimary(context),
        height: compact ? 1.28 : 1.4,
      ),
    );
  }
}
