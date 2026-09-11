from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, new: str, label: str) -> str:
    start_i = text.find(start)
    if start_i < 0:
        raise SystemExit(f'{label}: start marker missing')
    end_i = text.find(end, start_i)
    if end_i < 0:
        raise SystemExit(f'{label}: end marker missing')
    return text[:start_i] + new + text[end_i:]


# Pulper: desktop gets an intentional focal card and compact primary action.
path = 'frontend/lib/features/documents/document_import_screen.dart'
text = read(path)
new_pick = '''  Widget _buildPick() {
    final size = MediaQuery.sizeOf(context);
    final compactHeight = size.height <= 600;
    final desktop = size.width >= 900;
    final verticalPadding = compactHeight ? 12.0 : 24.0;
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        key: const ValueKey('document-import-pick-scroll'),
        padding: EdgeInsets.symmetric(
          horizontal: compactHeight ? 20 : 24,
          vertical: verticalPadding,
        ),
        child: ConstrainedBox(
          constraints: BoxConstraints(
            minHeight: constraints.maxHeight > verticalPadding * 2
                ? constraints.maxHeight - verticalPadding * 2
                : 0,
          ),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 720),
              child: Container(
                padding: EdgeInsetsDirectional.fromSTEB(
                  desktop ? 36 : 0,
                  desktop ? 34 : 0,
                  desktop ? 36 : 0,
                  desktop ? 34 : 0,
                ),
                decoration: desktop
                    ? BoxDecoration(
                        color: AminaTheme.surface(context),
                        borderRadius: BorderRadius.circular(28),
                        border: Border.all(color: AminaTheme.divider(context)),
                        boxShadow: AminaTheme.shadowClinical,
                      )
                    : null,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const _DocumentImportIcon(),
                    SizedBox(height: compactHeight ? 14 : 20),
                    Text(
                      AuditedPageCopy.of(context).documentIntro,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: compactHeight ? 13 : 14,
                        color: AminaTheme.textSecondary(context),
                        height: compactHeight ? 1.4 : 1.5,
                      ),
                    ),
                    SizedBox(height: compactHeight ? 20 : 28),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      alignment: WrapAlignment.center,
                      children: [
                        const _FormatChip(icon: Icons.picture_as_pdf, label: 'PDF'),
                        _FormatChip(
                          icon: Icons.image,
                          label: AuditedPageCopy.of(context).photo,
                        ),
                        const _FormatChip(
                          icon: Icons.table_chart,
                          label: 'Excel / CSV',
                        ),
                        const _FormatChip(icon: Icons.description, label: 'Word'),
                      ],
                    ),
                    SizedBox(height: compactHeight ? 12 : 20),
                    const _PrivacyGateNotice(),
                    SizedBox(height: compactHeight ? 14 : 24),
                    SizedBox(
                      width: desktop ? 260 : double.infinity,
                      child: ElevatedButton.icon(
                        key: const ValueKey('choose-document-button'),
                        onPressed: _pickFile,
                        icon: const Icon(Icons.folder_open),
                        label: Text(AuditedPageCopy.of(context).chooseDocument),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AminaTheme.teal600,
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.symmetric(
                            vertical: compactHeight ? 13 : 16,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      _ErrorCard(message: _error!),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

'''
text = replace_between(text, '  Widget _buildPick() {', '  Widget _buildPreview() {', new_pick, 'pulper pick surface')
write(path, text)

# New reading: preserve desktop 6/4 workspace, compact only the primary action.
path = 'frontend/lib/features/dashboard/widgets/add_log_sheet.dart'
text = read(path)
new_save = '''  Widget _saveBar(AppDatabase db, String unit, AppLocalizations l10n) {
    final desktop = MediaQuery.sizeOf(context).width >= 1000;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 14),
      decoration: BoxDecoration(
        color: AminaTheme.bg(context),
        border: Border(top: BorderSide(color: AminaTheme.divider(context))),
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1080),
          child: Align(
            alignment: desktop
                ? AlignmentDirectional.centerEnd
                : AlignmentDirectional.center,
            child: SizedBox(
              width: desktop ? 280 : double.infinity,
              child: FilledButton.icon(
                key: const Key('save-log-button'),
                onPressed: _saving || !_hasValidGlucose
                    ? null
                    : () => _saveLog(db, unit, l10n),
                icon: _saving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check_rounded),
                label: Text(
                  _saving ? l10n.journalSaving : l10n.journalSave,
                ),
                style: FilledButton.styleFrom(
                  minimumSize: const Size.fromHeight(54),
                  backgroundColor: AminaTheme.teal600,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

'''
text = replace_between(text, '  Widget _saveBar(', '  Future<bool> _confirmLowGlucose', new_save, 'add-log save bar')
write(path, text)

# Companion premium: focal failure/loading rail, compact retry and governed overview width.
path = 'frontend/lib/features/companion/companion_premium_screen.dart'
text = read(path)
text = replace_once(
    text,
    '                return _Overview(overview: overview);',
    '''                return Center(\n                  child: ConstrainedBox(\n                    constraints: const BoxConstraints(maxWidth: 1080),\n                    child: _Overview(overview: overview),\n                  ),\n                );''',
    'companion overview rail',
)
new_shell = '''class _Shell extends StatelessWidget {
  final Widget child;
  const _Shell({required this.child});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: CustomScrollView(
          physics: const BouncingScrollPhysics(),
          slivers: [
            SliverPadding(
              padding: const EdgeInsetsDirectional.fromSTEB(24, 24, 24, 40),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  const _BrandHeader(),
                  const SizedBox(height: 28),
                  child,
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

'''
text = replace_between(text, 'class _Shell extends StatelessWidget {', 'class _Overview extends StatelessWidget {', new_shell, 'companion state shell')
state_start = text.find('class _StateCard extends StatelessWidget {')
state_end = text.find('class _AmbientBackground extends StatelessWidget {', state_start)
if state_start < 0 or state_end < 0:
    raise SystemExit('companion state card markers missing')
state = text[state_start:state_end]
state = replace_once(
    state,
    '              width: double.infinity,\n              height: 46,',
    '''              width: MediaQuery.sizeOf(context).width >= 900\n                  ? 220\n                  : double.infinity,\n              height: 46,''',
    'companion retry width',
)
text = text[:state_start] + state + text[state_end:]
write(path, text)

# Onboarding: vertically balance the desktop workspace instead of pinning it to the top.
path = 'frontend/lib/features/auth/onboarding_chat_screen.dart'
text = read(path)
old = '''            return SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(28, 28, 28, 40),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 980),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        flex: 4,
                        child: _DesktopWelcomePanel(
                          title: 'IAmina',
                          subtitle: l10n.onboardingAssistantLabel,
                          body: l10n.onboardingWelcome,
                        ),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        flex: 6,
                        child: Container(
                          padding: const EdgeInsetsDirectional.fromSTEB(
                            28,
                            26,
                            28,
                            28,
                          ),
                          decoration: BoxDecoration(
                            color: Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: AminaTheme.ink100),
                            boxShadow: AminaTheme.shadowClinicalLg,
                          ),
                          child: questions,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );'''
new = '''            return SingleChildScrollView(
              padding: const EdgeInsetsDirectional.fromSTEB(28, 28, 28, 40),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight > 68
                      ? constraints.maxHeight - 68
                      : 0,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1040),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          flex: 4,
                          child: _DesktopWelcomePanel(
                            title: 'IAmina',
                            subtitle: l10n.onboardingAssistantLabel,
                            body: l10n.onboardingWelcome,
                          ),
                        ),
                        const SizedBox(width: 28),
                        Expanded(
                          flex: 6,
                          child: Container(
                            padding: const EdgeInsetsDirectional.fromSTEB(
                              30,
                              28,
                              30,
                              30,
                            ),
                            decoration: BoxDecoration(
                              color: Theme.of(context).cardColor,
                              borderRadius: BorderRadius.circular(26),
                              border: Border.all(color: AminaTheme.ink100),
                              boxShadow: AminaTheme.shadowClinicalLg,
                            ),
                            child: questions,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );'''
text = replace_once(text, old, new, 'onboarding desktop balance')
write(path, text)

# Companion chat: present the desktop conversation as an intentional application panel.
path = 'frontend/lib/features/companion/companion_conversation_screen.dart'
text = read(path)
old = '''      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 960),
            child: Column(
              children: ['''
new = '''      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final desktop = constraints.maxWidth >= 900;
            final conversation = Column(
              children: ['''
text = replace_once(text, old, new, 'companion chat opening')
old_tail = '''                _Composer(
                  controller: _controller,
                  sending: _sending,
                  onSend: _send,
                ),
              ],
            ),
          ),
        ),
      ),'''
new_tail = '''                _Composer(
                  controller: _controller,
                  sending: _sending,
                  onSend: _send,
                ),
              ],
            );

            if (!desktop) return conversation;
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: SizedBox(
                  width: 960,
                  height: constraints.maxHeight > 48
                      ? constraints.maxHeight - 48
                      : constraints.maxHeight,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(26),
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: AminaVisualLanguage.controlSurface(context),
                        borderRadius: BorderRadius.circular(26),
                        border: Border.all(
                          color: AminaVisualLanguage.controlBorder(context),
                        ),
                        boxShadow: AminaVisualLanguage.cardShadowLight,
                      ),
                      child: conversation,
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),'''
text = replace_once(text, old_tail, new_tail, 'companion chat closing')
write(path, text)

# Edit log: use desktop width and pair the two primary measurement cards.
path = 'frontend/lib/features/journal/edit_log_screen.dart'
text = read(path)
text = replace_once(
    text,
    "    final unit = profile?.unitPreference ?? 'mg/dL';\n",
    "    final unit = profile?.unitPreference ?? 'mg/dL';\n    final desktop = MediaQuery.sizeOf(context).width >= 900;\n",
    'edit log desktop flag',
)
text = replace_once(
    text,
    '                    constraints: const BoxConstraints(maxWidth: 680),',
    '                    constraints: BoxConstraints(maxWidth: desktop ? 920 : 680),',
    'edit log desktop width',
)
old_cards = '''                        _glucoseCard(l10n, unit),
                        const SizedBox(height: 18),
                        _insulinCard(l10n),
                        const SizedBox(height: 14),'''
new_cards = '''                        if (desktop)
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(child: _glucoseCard(l10n, unit)),
                              const SizedBox(width: 18),
                              Expanded(child: _insulinCard(l10n)),
                            ],
                          )
                        else ...[
                          _glucoseCard(l10n, unit),
                          const SizedBox(height: 18),
                          _insulinCard(l10n),
                        ],
                        const SizedBox(height: 14),'''
text = replace_once(text, old_cards, new_cards, 'edit log desktop cards')
write(path, text)

print('Applied deterministic desktop 9.5 polish batch')
