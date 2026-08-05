part of '../dashboard_screen.dart';

// ── Top Bar ───────────────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  final int range;
  final ValueChanged<int> onRangeChanged;
  final SyncService syncService;
  final VoidCallback onChatTap;
  final double hPad;

  const _TopBar({
    required this.range,
    required this.onRangeChanged,
    required this.syncService,
    required this.onChatTap,
    this.hPad = 16,
  });

  @override
  Widget build(BuildContext context) {
    final top = MediaQuery.of(context).padding.top;
    return Container(
      decoration: BoxDecoration(
        color: AminaTheme.surface(context),
        border: Border(bottom: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Padding(
        padding: EdgeInsets.fromLTRB(hPad, top + 10, hPad, 10),
        child: Row(
          children: [
            Expanded(
              child: RichText(
                text: TextSpan(
                  style: TextStyle(
                    fontFamily: 'Inter',
                    fontSize: 14,
                    color: AminaTheme.textSecondary(context),
                  ),
                  children: [
                    const TextSpan(text: 'Accueil · '),
                    TextSpan(
                      text: 'Vue d\'ensemble',
                      style: TextStyle(
                        color: AminaTheme.textPrimary(context),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            _RangeChips(range: range, onChanged: onRangeChanged),
            const SizedBox(width: 12),
            ValueListenableBuilder<SyncUiState>(
              valueListenable: syncService.state,
              builder: (_, state, __) => _SyncStatusButton(
                state: state,
                onRetry: state == SyncUiState.syncing
                    ? null
                    : syncService.syncPendingLogs,
              ),
            ),
            const SizedBox(width: 12),
            _ParlerButton(onTap: onChatTap),
          ],
        ),
      ),
    );
  }
}

class _ParlerButton extends StatelessWidget {
  final VoidCallback onTap;
  const _ParlerButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 44),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          gradient: AminaTheme.heroGradient,
          borderRadius: BorderRadius.circular(99),
          boxShadow: [
            BoxShadow(
              color: AminaTheme.teal500.withValues(alpha: 0.3),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline, color: Colors.white, size: 14),
            SizedBox(width: 8),
            Text(
              'Parler à IAmina',
              style: TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SyncStatusButton extends StatelessWidget {
  final SyncUiState state;
  final VoidCallback? onRetry;

  const _SyncStatusButton({required this.state, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final (icon, label, color) = switch (state) {
      SyncUiState.checking => (
        Icons.cloud_queue_outlined,
        'Vérification de la synchronisation',
        AminaTheme.textSecondary(context),
      ),
      SyncUiState.upToDate => (
        Icons.cloud_done_outlined,
        'Données à jour',
        AminaTheme.successEmerald,
      ),
      SyncUiState.pending => (
        Icons.cloud_upload_outlined,
        'Données en attente de synchronisation',
        AminaTheme.warningOrange,
      ),
      SyncUiState.syncing => (
        Icons.cloud_sync_outlined,
        'Synchronisation en cours',
        AminaTheme.teal500,
      ),
      SyncUiState.offline => (
        Icons.cloud_off_outlined,
        'Hors ligne · données conservées sur cet appareil',
        AminaTheme.ink500,
      ),
      SyncUiState.error => (
        Icons.error_outline,
        'Échec de synchronisation · appuyer pour réessayer',
        AminaTheme.dangerFg,
      ),
    };

    return Tooltip(
      message: label,
      child: Semantics(
        button: onRetry != null,
        label: label,
        child: InkWell(
          onTap: onRetry,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.08),
              border: Border.all(color: color.withValues(alpha: 0.25)),
              borderRadius: BorderRadius.circular(10),
            ),
            child: state == SyncUiState.syncing
                ? Center(
                    child: SizedBox(
                      width: 17,
                      height: 17,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: color,
                      ),
                    ),
                  )
                : Icon(icon, size: 18, color: color),
          ),
        ),
      ),
    );
  }
}

class _RangeChips extends StatelessWidget {
  final int range;
  final ValueChanged<int> onChanged;
  const _RangeChips({required this.range, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return Container(
      decoration: BoxDecoration(
        color: dark ? AminaTheme.dark700 : AminaTheme.ink50,
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(2),
      child: Row(
        children: [7, 21, 90].map((r) {
          final sel = r == range;
          return GestureDetector(
            onTap: () => onChanged(r),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: sel
                    ? (dark ? AminaTheme.dark500 : AminaTheme.cardBg)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(6),
                boxShadow: sel ? AminaTheme.shadowClinical : null,
              ),
              child: Text(
                '$r j',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                  color: sel
                      ? AminaTheme.textPrimary(context)
                      : AminaTheme.textSecondary(context),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
