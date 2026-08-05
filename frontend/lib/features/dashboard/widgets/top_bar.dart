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
        padding: EdgeInsetsDirectional.fromSTEB(hPad, top + 10, hPad, 10),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 760;
            return compact ? _buildCompact(context) : _buildDesktop(context);
          },
        ),
      ),
    );
  }

  Widget _buildDesktop(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _breadcrumb(context, detailed: true)),
        _RangeChips(range: range, onChanged: onRangeChanged),
        const SizedBox(width: 12),
        _syncButton(),
        const SizedBox(width: 12),
        _ParlerButton(onTap: onChatTap),
      ],
    );
  }

  Widget _buildCompact(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(child: _breadcrumb(context, detailed: false)),
            const SizedBox(width: 8),
            _syncButton(),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            _RangeChips(range: range, onChanged: onRangeChanged),
            const SizedBox(width: 8),
            Expanded(child: _ParlerButton(onTap: onChatTap, compact: true)),
          ],
        ),
      ],
    );
  }

  Widget _breadcrumb(BuildContext context, {required bool detailed}) {
    return Text(
      detailed
          ? AuditedPageCopy.of(context).breadcrumb
          : AuditedPageCopy.of(context).overview,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: TextStyle(
        fontFamily: 'Inter',
        fontSize: 14,
        color: detailed
            ? AminaTheme.textSecondary(context)
            : AminaTheme.textPrimary(context),
        fontWeight: detailed ? FontWeight.w500 : FontWeight.w700,
      ),
    );
  }

  Widget _syncButton() {
    return ValueListenableBuilder<SyncUiState>(
      valueListenable: syncService.state,
      builder: (_, state, __) => _SyncStatusButton(
        state: state,
        onRetry: state == SyncUiState.syncing
            ? null
            : syncService.syncPendingLogs,
      ),
    );
  }
}

class _ParlerButton extends StatelessWidget {
  final VoidCallback onTap;
  final bool compact;

  const _ParlerButton({required this.onTap, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final label = Text(
      compact ? 'IAmina' : AuditedPageCopy.of(context).talk,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 12,
        fontWeight: FontWeight.w700,
      ),
    );

    return Semantics(
      button: true,
      label: AuditedPageCopy.of(context).talk,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(99),
        child: Container(
          constraints: const BoxConstraints(minHeight: 44),
          padding: EdgeInsets.symmetric(
            horizontal: compact ? 10 : 14,
            vertical: 12,
          ),
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
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: compact ? MainAxisSize.max : MainAxisSize.min,
            children: [
              const Icon(
                Icons.chat_bubble_outline,
                color: Colors.white,
                size: 14,
              ),
              const SizedBox(width: 8),
              if (compact) Expanded(child: label) else label,
            ],
          ),
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
        AuditedPageCopy.of(context).sync('checking'),
        AminaTheme.textSecondary(context),
      ),
      SyncUiState.upToDate => (
        Icons.cloud_done_outlined,
        AuditedPageCopy.of(context).sync('upToDate'),
        AminaTheme.successEmerald,
      ),
      SyncUiState.pending => (
        Icons.cloud_upload_outlined,
        AuditedPageCopy.of(context).sync('pending'),
        AminaTheme.warningOrange,
      ),
      SyncUiState.syncing => (
        Icons.cloud_sync_outlined,
        AuditedPageCopy.of(context).sync('syncing'),
        AminaTheme.teal500,
      ),
      SyncUiState.offline => (
        Icons.cloud_off_outlined,
        AuditedPageCopy.of(context).sync('offline'),
        AminaTheme.ink500,
      ),
      SyncUiState.error => (
        Icons.error_outline,
        AuditedPageCopy.of(context).sync('error'),
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
        mainAxisSize: MainAxisSize.min,
        children: [7, 21, 90].map((r) {
          final selected = r == range;
          return InkWell(
            onTap: () => onChanged(r),
            borderRadius: BorderRadius.circular(6),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: selected
                    ? (dark ? AminaTheme.dark500 : AminaTheme.cardBg)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(6),
                boxShadow: selected ? AminaTheme.shadowClinical : null,
              ),
              child: Text(
                '$r ${AuditedPageCopy.of(context).dayShort}',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  color: selected
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
