import 'package:flutter/material.dart';
import 'package:amina/l10n/app_localizations.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:drift/drift.dart' as drift;
import '../../core/theme/app_theme.dart';
import '../../core/widgets/amina_text_field.dart';
import '../../core/widgets/responsive_content_surface.dart';
import '../../l10n/audited_page_copy.dart';
import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../services/api_client.dart';
import '../../services/consent_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _targetLowController = TextEditingController();
  final _targetHighController = TextEditingController();
  String _diabetesType = 'type1';
  String _treatment = 'insulin';
  String _unit = 'mg/dL';

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  void _loadProfile() async {
    final db = context.read<AppDatabase>();
    final profile = await db.select(db.patientProfiles).getSingleOrNull();
    if (profile != null) {
      setState(() {
        _diabetesType = profile.diabetesType ?? 'type1';
        _treatment = profile.treatment ?? 'insulin';
        _unit = profile.unitPreference;
        _targetLowController.text = profile.targetRangeLow.toStringAsFixed(0);
        _targetHighController.text = profile.targetRangeHigh.toStringAsFixed(0);
      });
    }
  }

  /// Profile completion score: counts non-default field values.
  int get _completionPct {
    int score = 0;
    // Has non-default diabetes type (type1 is default in initState)
    if (_diabetesType.isNotEmpty) score++;
    // Has non-default treatment (insulin is default)
    if (_treatment.isNotEmpty) score++;
    // Has customised target range (non-empty controllers)
    if (_targetLowController.text.isNotEmpty &&
        _targetHighController.text.isNotEmpty)
      score++;
    // Has chosen a unit
    if (_unit.isNotEmpty) score++;
    return ((score / 4) * 100).round();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final pct = _completionPct;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.myProfile), centerTitle: true),
      body: ResponsiveContentSurface(
        maxWidth: 1040,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Profile completion chip ────────────────────────────────────
              _ProfileCompletionHeader(pct: pct),
              const SizedBox(height: 20),

              _buildIASetupCard(l10n),
              const SizedBox(height: 32),

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
                (val) => setState(() => _diabetesType = val),
              ),

              const SizedBox(height: 32),
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
                (val) => setState(() => _treatment = val),
              ),

              const SizedBox(height: 32),
              _buildSectionTitle(Icons.show_chart, l10n.glucoseTarget),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _buildTextField(
                      AuditedPageCopy.of(context).minimum,
                      _targetLowController,
                      l10n,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _buildTextField(
                      AuditedPageCopy.of(context).maximum,
                      _targetHighController,
                      l10n,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 32),
              _buildSectionTitle(Icons.straighten, l10n.measureUnit),
              const SizedBox(height: 12),
              _buildChoiceGrid(
                ['mg/dL', 'mmol/L'],
                ['mg/dL', 'mmol/L'],
                _unit,
                (val) => setState(() => _unit = val),
              ),

              const SizedBox(height: 48),
              ElevatedButton(
                onPressed: _saveProfile,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AminaTheme.primaryTeal,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 2,
                ),
                child: Text(
                  l10n.saveProfile,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                  ),
                ),
              ),
              const SizedBox(height: 40),

              // Danger zone
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
                  crossAxisAlignment: CrossAxisAlignment.start,
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
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
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
                          side: BorderSide(
                            color: AminaTheme.dangerFg.withValues(alpha: 0.4),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                    // ── AI consent withdraw ──────────────────────────────────
                    Consumer<ConsentService>(
                      builder: (context, consent, _) {
                        if (!consent.hasConsent) return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: SizedBox(
                            width: double.infinity,
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
                                side: BorderSide(
                                  color: AminaTheme.dangerFg.withValues(
                                    alpha: 0.4,
                                  ),
                                ),
                                padding: const EdgeInsets.symmetric(
                                  vertical: 12,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIASetupCard(AppLocalizations l10n) {
    return InkWell(
      onTap: () => context.push('/onboarding'),
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AminaTheme.primaryTeal.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: AminaTheme.primaryTeal.withValues(alpha: 0.2),
            width: 2,
          ),
          boxShadow: AminaTheme.shadowCardLG,
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
    String current,
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

  void _confirmSignOut() {
    final l10n = AppLocalizations.of(context)!;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => SingleChildScrollView(
        child: Container(
          padding: const EdgeInsetsDirectional.fromSTEB(24, 20, 24, 40),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: AminaTheme.ink200,
                  borderRadius: BorderRadius.circular(100),
                ),
              ),
              const SizedBox(height: 20),
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: AminaTheme.dangerBg,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.logout,
                  color: AminaTheme.dangerFg,
                  size: 24,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                l10n.signOutConfirmTitle,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: AminaTheme.ink900,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                l10n.signOutConfirmBody,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 13,
                  color: AminaTheme.ink500,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: const BorderSide(color: AminaTheme.ink200),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        l10n.cancel,
                        style: const TextStyle(
                          color: AminaTheme.ink700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: () async {
                        // Capture everything before the async gap
                        final auth = context.read<AuthService>();
                        final router = GoRouter.of(context);
                        Navigator.pop(context);
                        await auth.signOut();
                        router.go('/login');
                      },
                      style: FilledButton.styleFrom(
                        backgroundColor: AminaTheme.dangerFg,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: Text(
                        l10n.confirmSignOut,
                        style: const TextStyle(fontWeight: FontWeight.w600),
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
  }

  void _confirmWithdrawConsent(AppLocalizations l10n) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetCtx) => Container(
        decoration: BoxDecoration(
          color: Theme.of(context).scaffoldBackgroundColor,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsetsDirectional.fromSTEB(24, 16, 24, 36),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AminaTheme.ink200,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: AminaTheme.dangerBg,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.psychology_outlined,
                color: AminaTheme.dangerFg,
                size: 24,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              l10n.consentWithdrawConfirmTitle,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: AminaTheme.ink900,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.consentWithdrawConfirmBody,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                color: AminaTheme.ink500,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(sheetCtx),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: AminaTheme.ink200),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      l10n.cancel,
                      style: const TextStyle(
                        color: AminaTheme.ink700,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: () async {
                      // Capture before async gap
                      final api = context.read<ApiClient>();
                      final db = context.read<AppDatabase>();
                      final consent = context.read<ConsentService>();
                      Navigator.pop(sheetCtx);
                      await api.withdrawConsent().catchError((_) => false);
                      await db.setAiConsent(granted: false);
                      consent.declineLocally();
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              AppLocalizations.of(context)!.consentWithdrawn,
                            ),
                          ),
                        );
                      }
                    },
                    style: FilledButton.styleFrom(
                      backgroundColor: AminaTheme.dangerFg,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      l10n.consentWithdraw,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _saveProfile() async {
    final db = context.read<AppDatabase>();
    final low = double.tryParse(_targetLowController.text) ?? 70.0;
    final high = double.tryParse(_targetHighController.text) ?? 180.0;

    await db
        .into(db.patientProfiles)
        .insertOnConflictUpdate(
          PatientProfilesCompanion.insert(
            userId: const drift.Value(1),
            preferredLanguage: const drift.Value('fr'),
            updatedAt: DateTime.now(),
            diabetesType: drift.Value(_diabetesType),
            treatment: drift.Value(_treatment),
            unitPreference: drift.Value(_unit),
            targetRangeLow: drift.Value(low),
            targetRangeHigh: drift.Value(high),
          ),
        );

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(AppLocalizations.of(context)!.profileUpdated),
          backgroundColor: AminaTheme.successEmerald,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}

// ── Profile completion header ─────────────────────────────────────────────────

class _ProfileCompletionHeader extends StatelessWidget {
  final int pct;
  const _ProfileCompletionHeader({required this.pct});

  Color get _color {
    if (pct >= 100) return const Color(0xFF059669); // emerald — complete
    if (pct >= 75) return AminaTheme.teal500;
    if (pct >= 50) return const Color(0xFFF59E0B); // amber
    return const Color(0xFFDC2626); // red — minimal data
  }

  @override
  Widget build(BuildContext context) {
    final copy = AuditedPageCopy.of(context);
    final label = copy.profileCompletionLabel(pct);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                pct >= 100
                    ? Icons.verified_user_rounded
                    : Icons.person_outline_rounded,
                size: 16,
                color: _color,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: _color,
                  ),
                ),
              ),
              Text(
                '$pct%',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: _color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct / 100,
              minHeight: 5,
              backgroundColor: _color.withValues(alpha: 0.12),
              valueColor: AlwaysStoppedAnimation<Color>(_color),
            ),
          ),
          if (pct < 100) ...[
            const SizedBox(height: 8),
            Text(
              copy.profileCompletionPrompt,
              style: const TextStyle(
                fontSize: 11,
                color: AminaTheme.ink500,
                height: 1.4,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
