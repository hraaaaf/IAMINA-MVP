from pathlib import Path

root = Path('frontend')

# Summary: replace only _buildError.
p = root / 'lib/features/journal/ai_summary_screen.dart'
s = p.read_text()
start = s.index('  Widget _buildError() {')
end = s.index('\n\n  Widget _buildContent() {', start)
new = r'''  Widget _buildError() {
    final l10n = AppLocalizations.of(context)!;
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 720;
        final icon = Container(
          width: isWide ? 56 : 48,
          height: isWide ? 56 : 48,
          decoration: BoxDecoration(
            color: AminaTheme.dangerBg,
            borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
          ),
          child: Icon(
            Icons.cloud_off_outlined,
            color: AminaTheme.dangerFg,
            size: isWide ? 28 : 24,
          ),
        );
        final message = Text(
          l10n.analysisLoadError,
          textAlign: isWide ? TextAlign.start : TextAlign.center,
          style: TextStyle(
            fontSize: isWide ? 16 : 15,
            height: 1.35,
            fontWeight: FontWeight.w800,
            color: AminaTheme.textPrimary(context),
          ),
        );
        final retry = FilledButton.icon(
          onPressed: _fetchData,
          icon: const Icon(Icons.refresh, size: 17),
          label: Text(l10n.retry),
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
            ),
          ),
        );
        return Align(
          alignment: Alignment.topCenter,
          child: Padding(
            padding: EdgeInsetsDirectional.fromSTEB(20, isWide ? 48 : 32, 20, 24),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: isWide ? 680 : 420),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.all(isWide ? 28 : 24),
                decoration: BoxDecoration(
                  color: AminaTheme.surface(context),
                  borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
                  border: Border.all(color: AminaTheme.divider(context)),
                  boxShadow: AminaTheme.shadowClinical,
                ),
                child: isWide
                    ? Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          icon,
                          const SizedBox(width: 20),
                          Expanded(child: message),
                          const SizedBox(width: 24),
                          SizedBox(width: 190, child: retry),
                        ],
                      )
                    : Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          icon,
                          const SizedBox(height: 16),
                          message,
                          const SizedBox(height: 18),
                          SizedBox(width: double.infinity, child: retry),
                        ],
                      ),
              ),
            ),
          ),
        );
      },
    );
  }'''
s = s[:start] + new + s[end:]
p.write_text(s)

# Journal: replace empty branch and add helper without formatting unrelated code.
p = root / 'lib/features/journal/journal_screen.dart'
s = p.read_text()
start = s.index('              if (logs.isEmpty) {')
end = s.index('\n\n              final groupedLogs', start)
s = s[:start] + '''              if (logs.isEmpty) {\n                return _buildEmptyJournalSliver(\n                  context,\n                  viewportWidth,\n                  horizontalPadding,\n                );\n              }''' + s[end:]
insert_at = s.index('\n\n  Widget _buildSliverAppBar(BuildContext context) {')
helper = r'''

  Widget _buildEmptyJournalSliver(
    BuildContext context,
    double viewportWidth,
    double horizontalPadding,
  ) {
    final l10n = AppLocalizations.of(context)!;
    final content = Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 100, height: 100,
          child: CustomPaint(painter: _EmptyJournalPainter()),
        ),
        const SizedBox(height: 24),
        Text(
          l10n.journalEmpty,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AminaTheme.ink900),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          l10n.journalEmptySubtitle,
          style: const TextStyle(fontSize: 14, color: AminaTheme.ink500, height: 1.5),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 28),
        FilledButton.icon(
          onPressed: () => context.go('/ajouter'),
          icon: const Icon(Icons.add, size: 16),
          label: Text(l10n.addMeasurement),
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 48),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AminaTheme.radiusXL)),
          ),
        ),
      ],
    );
    if (viewportWidth < 700) {
      return SliverFillRemaining(
        hasScrollBody: false,
        child: Center(child: Padding(padding: const EdgeInsets.all(40), child: content)),
      );
    }
    return SliverFillRemaining(
      hasScrollBody: false,
      child: Padding(
        padding: EdgeInsetsDirectional.fromSTEB(horizontalPadding, 48, horizontalPadding, 32),
        child: Align(
          alignment: AlignmentDirectional.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ClinicalCard(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 28),
              child: content,
            ),
          ),
        ),
      ),
    );
  }'''
s = s[:insert_at] + helper + s[insert_at:]
p.write_text(s)

# Profile: only root grouping and surface tokens.
p = root / 'lib/features/profile/profile_screen.dart'
s = p.read_text()
old = r'''          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildMedicalSection(l10n),
              const SizedBox(height: 14),
              _buildProfileSection(
                key: const ValueKey('profile-iamina-section'),
                icon: Icons.auto_awesome_outlined,
                title: l10n.profileIaminaSection,
                subtitle: l10n.profileIaminaSectionHint,
                initiallyExpanded: false,
                children: [_buildIASetupCard(l10n)],
              ),
              const SizedBox(height: 14),
              _buildAccountSection(l10n),
            ],
          ),'''
new = r'''          child: LayoutBuilder(
            builder: (context, constraints) {
              final sections = Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _buildMedicalSection(l10n),
                  const SizedBox(height: 14),
                  _buildProfileSection(
                    key: const ValueKey('profile-iamina-section'),
                    icon: Icons.auto_awesome_outlined,
                    title: l10n.profileIaminaSection,
                    subtitle: l10n.profileIaminaSectionHint,
                    initiallyExpanded: false,
                    children: [_buildIASetupCard(l10n)],
                  ),
                  const SizedBox(height: 14),
                  _buildAccountSection(l10n),
                ],
              );
              if (constraints.maxWidth < 900) return sections;
              return Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AminaTheme.ink50,
                  borderRadius: BorderRadius.circular(AminaTheme.radius3XL),
                  border: Border.all(color: AminaTheme.ink100),
                ),
                child: sections,
              );
            },
          ),'''
if old not in s: raise SystemExit('profile root block not found')
s = s.replace(old, new, 1)
s = s.replace('borderRadius: BorderRadius.circular(18),\n        border: Border.all(color: AminaTheme.ink200.withValues(alpha: 0.75)),\n        boxShadow: AminaTheme.shadowCard,', 'borderRadius: BorderRadius.circular(AminaTheme.radius2XL),\n        border: Border.all(color: AminaTheme.ink100),\n        boxShadow: AminaTheme.shadowClinical,', 1)
s = s.replace('borderRadius: BorderRadius.circular(24),\n          border: Border.all(\n            color: AminaTheme.primaryTeal.withValues(alpha: 0.2),\n            width: 2,\n          ),\n          boxShadow: AminaTheme.shadowCard,', 'borderRadius: BorderRadius.circular(AminaTheme.radius2XL),\n          border: Border.all(\n            color: AminaTheme.primaryTeal.withValues(alpha: 0.2),\n          ),\n          boxShadow: AminaTheme.shadowClinical,', 1)
p.write_text(s)
