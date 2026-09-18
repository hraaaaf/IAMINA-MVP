part of 'profile_screen.dart';

extension _ProfileScreenPresentation on _ProfileScreenState {
  Widget _buildPresentation(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isMobile = MediaQuery.sizeOf(context).width < 700;
    return Scaffold(
      appBar: isMobile
          ? null
          : AppBar(title: Text(l10n.myProfile), centerTitle: true),
      body: Column(
        children: [
          if (isMobile) AminaMobilePageHeader(title: l10n.myProfile),
          Expanded(
            child: ResponsiveContentSurface(
              maxWidth: 1040,
              child: SingleChildScrollView(
                padding: const EdgeInsetsDirectional.fromSTEB(24, 20, 24, 40),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final sections = Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (!_hasPersistedProfile) ...[
                          AminaFirstUsePanel(
                            key: const ValueKey('profile-first-use'),
                            icon: Icons.tune_rounded,
                            title: l10n.profileMedicalSection,
                            body: AuditedPageCopy.of(
                              context,
                            ).profileCompletionPrompt,
                            compact: true,
                          ),
                          const SizedBox(height: 14),
                        ],
                        _buildMedicalSection(l10n),
                        const SizedBox(height: 14),
                        _buildRamadanSection(l10n),
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
                        borderRadius: BorderRadius.circular(
                          AminaTheme.radius3XL,
                        ),
                        border: Border.all(color: AminaTheme.ink100),
                      ),
                      child: sections,
                    );
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicalSection(AppLocalizations l10n) {
    return _buildProfileSection(
      key: const ValueKey('profile-medical-section'),
      icon: Icons.favorite_border_rounded,
      title: l10n.profileMedicalSection,
      subtitle: _medicalSummary(l10n),
      initiallyExpanded: false,
      children: [
        _buildSectionTitle(Icons.favorite_border, l10n.diabetesType),
        const SizedBox(height: 12),
        _buildChoiceGrid(
          [
            l10n.diabetesType1,
            l10n.diabetesType2,
            l10n.diabetesGestational,
            l10n.diabetesPreDiabetes,
          ],
          ['type1', 'type2', 'gestational', 'pre'],
          _diabetesType,
          (val) => _setPresentationState(() => _diabetesType = val),
        ),
        const SizedBox(height: 28),
        _buildSectionTitle(Icons.science_outlined, l10n.treatment),
        const SizedBox(height: 12),
        _buildChoiceGrid(
          [
            l10n.treatmentInsulin,
            l10n.treatmentTablets,
            l10n.treatmentLifestyle,
          ],
          ['insulin', 'tablets', 'lifestyle'],
          _treatment,
          (val) => _setPresentationState(() => _treatment = val),
        ),
        const SizedBox(height: 28),
        _buildSectionTitle(Icons.show_chart, l10n.glucoseTarget),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 460;
            final low = _buildTextField(
              AuditedPageCopy.of(context).minimum,
              _targetLowController,
              l10n,
            );
            final high = _buildTextField(
              AuditedPageCopy.of(context).maximum,
              _targetHighController,
              l10n,
            );
            if (compact) {
              return Column(children: [low, const SizedBox(height: 12), high]);
            }
            return Row(
              children: [
                Expanded(child: low),
                const SizedBox(width: 16),
                Expanded(child: high),
              ],
            );
          },
        ),
        const SizedBox(height: 28),
        _buildSectionTitle(Icons.straighten, l10n.measureUnit),
        const SizedBox(height: 12),
        _buildChoiceGrid(
          ['mg/dL', 'mmol/L'],
          ['mg/dL', 'mmol/L'],
          _unit,
          (val) => _setPresentationState(() => _unit = val),
        ),
        const SizedBox(height: 28),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _saveProfile,
            style: ElevatedButton.styleFrom(
              backgroundColor: AminaTheme.primaryTeal,
              foregroundColor: Colors.white,
              minimumSize: const Size.fromHeight(48),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
              ),
              elevation: 0,
            ),
            child: Text(
              l10n.saveProfile,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRamadanSection(AppLocalizations l10n) {
    final configured = _ramadanStartDate != null && _ramadanEndDate != null;
    return _buildProfileSection(
      key: const ValueKey('profile-ramadan-section'),
      icon: Icons.nightlight_round,
      title: l10n.ramadanProfileSection,
      subtitle: configured
          ? '${_dateLabel(_ramadanStartDate!)} → ${_dateLabel(_ramadanEndDate!)}'
          : l10n.ramadanNotConfigured,
      initiallyExpanded: false,
      children: [
        Text(
          l10n.ramadanProfileHint,
          style: const TextStyle(
            color: AminaTheme.ink500,
            fontSize: 13,
            height: 1.45,
          ),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 460;
            final start = _ramadanDateButton(
              key: const Key('ramadan-start-date'),
              label: l10n.ramadanStartDate,
              value: _ramadanStartDate,
              onTap: () => _pickRamadanDate(start: true),
            );
            final end = _ramadanDateButton(
              key: const Key('ramadan-end-date'),
              label: l10n.ramadanEndDate,
              value: _ramadanEndDate,
              onTap: () => _pickRamadanDate(start: false),
            );
            if (compact) {
              return Column(children: [start, const SizedBox(height: 10), end]);
            }
            return Row(
              children: [
                Expanded(child: start),
                const SizedBox(width: 12),
                Expanded(child: end),
              ],
            );
          },
        ),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            final clearButton = configured
                ? TextButton(
                    key: const Key('ramadan-clear-period'),
                    onPressed: _savingRamadan
                        ? null
                        : () => setState(() {
                            _ramadanStartDate = null;
                            _ramadanEndDate = null;
                          }),
                    child: Text(l10n.ramadanClear),
                  )
                : null;
            final saveButton = FilledButton(
              key: const Key('ramadan-save-period'),
              onPressed: _savingRamadan ? null : () => _saveRamadanPeriod(l10n),
              child: Text(
                _savingRamadan ? l10n.journalSaving : l10n.ramadanSave,
              ),
            );

            if (constraints.maxWidth < 300) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (clearButton != null) ...[
                    clearButton,
                    const SizedBox(height: 8),
                  ],
                  saveButton,
                ],
              );
            }

            return Row(
              children: [
                if (clearButton != null) clearButton,
                const Spacer(),
                saveButton,
              ],
            );
          },
        ),
      ],
    );
  }

  Widget _ramadanDateButton({
    required Key key,
    required String label,
    required DateTime? value,
    required VoidCallback onTap,
  }) {
    return OutlinedButton(
      key: key,
      onPressed: _savingRamadan ? null : onTap,
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        alignment: AlignmentDirectional.centerStart,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AminaTheme.ink500),
          ),
          const SizedBox(height: 3),
          Text(
            value == null
                ? AppLocalizations.of(context)!.ramadanChooseDate
                : _dateLabel(value),
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: AminaTheme.ink900,
            ),
          ),
        ],
      ),
    );
  }

  String _dateLabel(DateTime value) {
    final dd = value.day.toString().padLeft(2, '0');
    final mm = value.month.toString().padLeft(2, '0');
    return '$dd/$mm/${value.year}';
  }

  Widget _buildAccountSection(AppLocalizations l10n) {
    return _buildProfileSection(
      key: const ValueKey('profile-account-section'),
      icon: Icons.shield_outlined,
      title: l10n.profileAccountSection,
      subtitle: l10n.profileAccountSectionHint,
      initiallyExpanded: false,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AminaTheme.dangerBg,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AminaTheme.dangerFg.withValues(alpha: 0.2),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                l10n.dangerZone,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AminaTheme.dangerFg,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _confirmSignOut,
                icon: const Icon(
                  Icons.logout,
                  size: 16,
                  color: AminaTheme.dangerFg,
                ),
                label: Text(
                  l10n.signOut,
                  style: const TextStyle(
                    color: AminaTheme.dangerFg,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(48),
                  side: BorderSide(
                    color: AminaTheme.dangerFg.withValues(alpha: 0.4),
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              Consumer<ConsentService>(
                builder: (context, consent, _) {
                  if (!consent.hasConsent) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: OutlinedButton.icon(
                      onPressed: () => _confirmWithdrawConsent(l10n),
                      icon: const Icon(
                        Icons.psychology_outlined,
                        size: 16,
                        color: AminaTheme.dangerFg,
                      ),
                      label: Text(
                        l10n.consentWithdraw,
                        style: const TextStyle(
                          color: AminaTheme.dangerFg,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(48),
                        side: BorderSide(
                          color: AminaTheme.dangerFg.withValues(alpha: 0.4),
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildProfileSection({
    required Key key,
    required IconData icon,
    required String title,
    required String subtitle,
    required bool initiallyExpanded,
    required List<Widget> children,
  }) {
    return Container(
      key: key,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
        border: Border.all(color: AminaTheme.ink100),
        boxShadow: AminaTheme.shadowClinical,
      ),
      clipBehavior: Clip.antiAlias,
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          maintainState: true,
          initiallyExpanded: initiallyExpanded,
          tilePadding: const EdgeInsetsDirectional.fromSTEB(18, 10, 14, 10),
          childrenPadding: const EdgeInsetsDirectional.fromSTEB(18, 0, 18, 20),
          leading: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AminaTheme.primaryTeal.withValues(alpha: 0.09),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: AminaTheme.primaryTeal, size: 21),
          ),
          title: Text(
            title,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: AminaTheme.ink900,
            ),
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Text(
              subtitle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12,
                height: 1.35,
                color: AminaTheme.ink500,
              ),
            ),
          ),
          children: children,
        ),
      ),
    );
  }

  String _medicalSummary(AppLocalizations l10n) {
    if (!_hasPersistedProfile) return l10n.profileMedicalSectionHint;

    final diabetes = switch (_diabetesType) {
      'type1' => l10n.diabetesType1,
      'type2' => l10n.diabetesType2,
      'gestational' => l10n.diabetesGestational,
      'pre' => l10n.diabetesPreDiabetes,
      _ => null,
    };
    final treatment = switch (_treatment) {
      'insulin' => l10n.treatmentInsulin,
      'tablets' => l10n.treatmentTablets,
      'lifestyle' => l10n.treatmentLifestyle,
      _ => null,
    };
    final parts = <String>[
      if (diabetes != null) diabetes,
      if (treatment != null) treatment,
      _unit,
    ];
    return parts.join(' · ');
  }

  Widget _buildIASetupCard(AppLocalizations l10n) {
    return InkWell(
      onTap: () => context.push('/onboarding'),
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AminaTheme.primaryTeal.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
          border: Border.all(
            color: AminaTheme.primaryTeal.withValues(alpha: 0.2),
          ),
          boxShadow: AminaTheme.shadowClinical,
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                gradient: AminaTheme.heroGradient,
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: Colors.white,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.configureWithIamina,
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    l10n.conversationalAssistant,
                    style: const TextStyle(
                      color: AminaTheme.textMuted,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AminaTheme.primaryTeal),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(IconData icon, String title) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AminaTheme.textDark),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
      ],
    );
  }

  Widget _buildChoiceGrid(
    List<String> labels,
    List<String> values,
    String? current,
    Function(String) onSelect,
  ) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: List.generate(labels.length, (index) {
        final isSelected = current == values[index];
        return InkWell(
          onTap: () => onSelect(values[index]),
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isSelected
                  ? AminaTheme.primaryTeal
                  : Colors.grey.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isSelected ? AminaTheme.primaryTeal : Colors.transparent,
              ),
            ),
            child: Text(
              labels[index],
              style: TextStyle(
                fontWeight: FontWeight.w700,
                color: isSelected ? Colors.white : AminaTheme.textDark,
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildTextField(
    String label,
    TextEditingController controller,
    AppLocalizations l10n,
  ) {
    return AminaTextField(
      label: label,
      hint: l10n.enterValue,
      controller: controller,
      keyboardType: TextInputType.number,
    );
  }
}
