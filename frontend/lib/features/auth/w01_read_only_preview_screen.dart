import 'package:amina/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/localization/app_lock_localized_copy.dart';
import '../../core/theme/app_theme.dart';
import '../../services/app_lock_service.dart';
import '../../services/auth_service.dart';
import '../../services/consent_service.dart';
import '../../services/preview_api_origin.dart';

/// W01 Web Preview only: public, read-only exploration without a clinical DB.
/// It deliberately never reads AppDatabase, ApiClient or patient providers.
class W01ReadOnlyPreviewScreen extends StatefulWidget {
  const W01ReadOnlyPreviewScreen({
    super.key,
    this.previewEnabled = kIaminaPreviewSameOriginApi,
  });

  final bool previewEnabled;

  @override
  State<W01ReadOnlyPreviewScreen> createState() =>
      _W01ReadOnlyPreviewScreenState();
}

class _W01ReadOnlyPreviewScreenState
    extends State<W01ReadOnlyPreviewScreen> {
  bool _dismissedConsent = false;
  bool _showConsentExplanation = false;

  void _accept() {
    final auth = context.read<AuthService>();
    final lock = context.read<AppLockService>();
    if (!auth.hasRemoteApiCredential || !lock.isUnlocked) {
      setState(() => _showConsentExplanation = true);
      return;
    }
    context.go('/consent');
  }

  void _skip() {
    final lock = context.read<AppLockService>();
    if (lock.isUnlocked) {
      // The full local app is available only after strong unlock.
      // Skipping consent does NOT authorize any external AI provider.
      context.read<ConsentService>().declineLocally();
      context.go('/dashboard');
      return;
    }
    setState(() {
      _dismissedConsent = true;
      _showConsentExplanation = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final lock = context.watch<AppLockService>();

    if (!widget.previewEnabled) {
      return const Scaffold(body: SizedBox.shrink());
    }

    return Scaffold(
      backgroundColor: AminaTheme.bg(context),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 780),
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
              children: [
                if (!_dismissedConsent) ...[
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: Container(
                      key: const Key('w01-preview-consent-card'),
                      constraints: const BoxConstraints(maxWidth: 370),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AminaTheme.surface(context),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AminaTheme.divider(context)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            l10n.w01PreviewConsentTitle,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: AminaTheme.textPrimary(context),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            alignment: WrapAlignment.start,
                            spacing: 8,
                            children: [
                              TextButton(
                                key: const Key('w01-preview-consent-accept'),
                                onPressed: _accept,
                                child: Text(l10n.w01PreviewAccept),
                              ),
                              TextButton(
                                key: const Key('w01-preview-consent-skip'),
                                onPressed: _skip,
                                child: Text(l10n.w01PreviewSkip),
                              ),
                            ],
                          ),
                          if (_showConsentExplanation)
                            Semantics(
                              liveRegion: true,
                              child: Text(
                                l10n.w01PreviewConsentUnavailable,
                                key: const Key('w01-preview-consent-unavailable'),
                                style: TextStyle(
                                  fontSize: 12,
                                  color: AminaTheme.textSecondary(context),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 40),
                Icon(
                  Icons.shield_outlined,
                  size: 52,
                  color: AminaTheme.teal500,
                ),
                const SizedBox(height: 18),
                Text(
                  l10n.w01PreviewTitle,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  l10n.w01PreviewDescription,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  l10n.w01PreviewReadOnlyNotice,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
                const SizedBox(height: 20),
                Center(
                  child: OutlinedButton.icon(
                    key: const Key('w01-preview-open-lock'),
                    onPressed: () => context.go(
                      lock.isConfigured || lock.recoveryRequired
                          ? '/app-lock/unlock'
                          : '/app-lock/setup',
                    ),
                    icon: const Icon(Icons.lock_outline),
                    label: Text(
                      lock.isConfigured || lock.recoveryRequired
                          ? l10n.w01PreviewReturnUnlock
                          : l10n.w01PreviewProtect,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
